if (window.__audioTranscriptionOverlayApi) {
  window.__audioTranscriptionOverlayApi.reactivate();
} else {
  window.__audioTranscriptionOverlayApi = (function () {
    const TEXT_BLOCK_STYLE =
      "padding:0 16px 10px 16px;display:block;white-space:pre-wrap !important;word-break:break-word !important;";
    const BUTTON_STYLE =
      "padding:2px 8px;cursor:pointer;background:rgba(255,255,255,0.16);border:1px solid rgba(255,255,255,0.22);color:#fff;border-radius:6px;font-size:12px;font-weight:700;";

    const MANIFEST_VERSION = chrome.runtime.getManifest?.()?.version || "";
    const CONTAINER_STYLE = (style) => `
      position:fixed;
      top:${style.top};
      left:${style.left};
      width:${style.width};
      height:${style.height};
      z-index:2147483647;
      background:rgba(2,6,23,0.96);
      color:#f8fafc;
      border:1px solid #334155;
      border-radius:12px;
      overflow:hidden;
      resize:both;
      display:flex;
      flex-direction:column;
      box-shadow:0 12px 28px rgba(0,0,0,0.45);
      backdrop-filter:blur(6px);
    `;

    let containerElement = null;
    let transcriptionHeaderEl = null;
    let transcriptionOriginalEl = null;
    let transcriptionTranslatedEl = null;
    let dividerEl = null;
    let mainWrapperEl = null;
    let waitPopupEl = null;
    let resizeObserver = null;

    let segments = [];
    let previousSegments = [];
    let historyChunks = [];
    let historyChunksRaw = [];
    let translatedChunks = [];
    let pendingStableText = "";
    let windowStartTime = Date.now();
    let currentFormatting = "advanced";
    let currentDisplayMode = "both";
    let currentFontSize = 20;
    let lastReceivedTime = Date.now();
    let silenceFlushTimer = null;
    let isDraggingDivider = false;
    let translationQueue = [];
    let isTranslatingLocal = false;
    let listenerBound = false;
    let statusClearTimer = null;

    let enableGeminiTranslation = false;
    let enableTts = false;
    let dedupTail = [];
    let hideLiveText = false;

    // --- Transcription Profile Configs ---
    const PROFILES = {
      accurate: {
        stableWordCount: 15,
        stableElapsed: 4000,
        stableSegments: 7,
        safeCommitKeep: 3,
        safeCommitMinSeg: 5,
        safeCommitElapsed: 5000,
        fallbackElapsed: 6000,
        silenceFlushMs: 2000,
        silenceCheckMs: 1000,
        translationMinWords: 20,
        translationSentenceWords: 14,
        translationSilenceMs: 2500,
        alignmentSamples: 4
      },
      balanced: {
        stableWordCount: 10,
        stableElapsed: 2500,
        stableSegments: 5,
        safeCommitKeep: 2,
        safeCommitMinSeg: 4,
        safeCommitElapsed: 3500,
        fallbackElapsed: 4000,
        silenceFlushMs: 1200,
        silenceCheckMs: 800,
        translationMinWords: 16,
        translationSentenceWords: 10,
        translationSilenceMs: 1500,
        alignmentSamples: 6
      },
      lowlag: {
        stableWordCount: 5,
        stableElapsed: 1200,
        stableSegments: 3,
        safeCommitKeep: 1,
        safeCommitMinSeg: 2,
        safeCommitElapsed: 1500,
        fallbackElapsed: 2000,
        silenceFlushMs: 600,
        silenceCheckMs: 400,
        translationMinWords: 8,
        translationSentenceWords: 5,
        translationSilenceMs: 800,
        alignmentSamples: 8
      }
    };
    let activeProfile = PROFILES.balanced;

    function getProfile(name) {
      return PROFILES[name] || PROFILES.balanced;
    }

    function normalizeText(text) { return String(text || "").replace(/[ \t\r]+/g, " ").trim(); }
    function stripPunctuation(text) {
      return String(text || "").toLowerCase().replace(/[^\p{L}\p{N}\s']/gu, " ").replace(/\s+/g, " ").trim();
    }
    function splitWords(text) { return stripPunctuation(text).split(" ").filter(Boolean); }
    function escapeHtml(value) {
      return String(value || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    }
    function setSetting(key, value) { chrome.storage.local.set({ [key]: value }); }
    function debounce(fn, delay) {
      let timer = null;
      return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
    }
    const debouncedSaveWindowStyle = debounce(saveWindowStyle, 200);

    function calculateTextSimilarity(a, b) {
      const wa = splitWords(a);
      const wb = splitWords(b);
      if (!wa.length || !wb.length) return 0;
      const setA = new Set(wa);
      let matches = 0;
      for (const word of wb) { if (setA.has(word)) matches++; }
      return matches / Math.max(wa.length, wb.length);
    }

    function trimPrefixOverlap(baseText, candidateText, maxWords = 80, minWords = 3) {
      const baseWords = splitWords(baseText);
      const candidateWords = splitWords(candidateText);
      const max = Math.min(maxWords, baseWords.length, candidateWords.length);
      for (let size = max; size >= minWords; size--) {
        let ok = true;
        for (let i = 0; i < size; i++) {
          if (baseWords[baseWords.length - size + i] !== candidateWords[i]) { ok = false; break; }
        }
        if (ok) {
          let strippedText = normalizeText(candidateText);
          let matchCount = 0;
          let removeUpTo = 0;
          const wordRegex = /[^\s]+/g;
          let match;
          while ((match = wordRegex.exec(strippedText)) !== null) {
            matchCount++;
            if (matchCount === size) { removeUpTo = wordRegex.lastIndex; break; }
          }
          return normalizeText(strippedText.slice(removeUpTo));
        }
      }
      return normalizeText(candidateText);
    }

    function trimPrefixOverlapRaw(baseText, rawCandidateText, maxWords = 80, minWords = 3) {
      const baseWords = splitWords(baseText);
      const candidateWords = splitWords(rawCandidateText);
      const max = Math.min(maxWords, baseWords.length, candidateWords.length);
      for (let size = max; size >= minWords; size--) {
        let ok = true;
        for (let i = 0; i < size; i++) {
          if (baseWords[baseWords.length - size + i] !== candidateWords[i]) { ok = false; break; }
        }
        if (ok) {
          let matchCount = 0;
          let removeUpTo = 0;
          const wordRegex = /\S+/g;
          let m;
          while ((m = wordRegex.exec(rawCandidateText)) !== null) {
            matchCount++;
            if (matchCount === size) { removeUpTo = wordRegex.lastIndex; break; }
          }
          return rawCandidateText.slice(removeUpTo).replace(/^[ \t\r\n]+/, "");
        }
      }
      return rawCandidateText;
    }

    function removeInternalRepetitions(text, minMatchWords = 6) {
      const words = normalizeText(text).split(/\s+/).filter(Boolean);
      if (words.length < minMatchWords * 2) return text;
      const low = words.map(w => stripPunctuation(w));
      for (let i = minMatchWords; i < words.length; i++) {
        const maxLen = Math.min(25, words.length - i);
        for (let len = maxLen; len >= minMatchWords; len--) {
          for (let j = 0; j <= i - len; j++) {
            let match = true;
            for (let k = 0; k < len; k++) {
              if (low[j + k] !== low[i + k]) { match = false; break; }
            }
            if (match) {
              return normalizeText(
                words.slice(0, i).join(" ") + " " + words.slice(i + len).join(" ")
              );
            }
          }
        }
      }
      return text;
    }

    function formatText(text, formatting) {
      if (!text) return "";
      const clean = normalizeText(text);
      if (!clean) return "";

      if (formatting === "none") {
        if (clean.includes("\n")) return clean;
        return clean.replace(/([.!?\u2026\u3002\uFF01\uFF1F\u061F])\s+/g, "$1\n");
      }

      let flat = clean.replace(/\n+/g, " ");
      if (formatting === "join") {
        return flat;
      }

      return flat.replace(
        /(?<!\b\p{L})(?<!\b(?:EE|UU|Sr|Sra|Dr|Dra|Mr|Mrs|Ms|Prof|St|Mt|etc|vs|cf|ie|eg|al|Ud|Vd|vd|ud|av|Av))([.!?\u2026\u061F\u3002\uFF01\uFF1F]+["')\]»"]*)\s+(?=[\p{Lu}\p{Lo}\p{N}¿¡«"(\['"])/gu,
        "$1\n"
      );
    }

    function splitIntoFlushableChunks(text, forceFlush = false) {
      let rest = normalizeText(text);
      const chunks = [];
      if (!rest) return { chunks, remainder: "" };

      const sentenceRegex = /[^.!?\u2026]+[.!?\u2026]+(?:["')\]]+)?/g;
      let consumedLength = 0;
      let match;

      while ((match = sentenceRegex.exec(rest)) !== null) {
        const sentence = normalizeText(match[0]);
        if (sentence) chunks.push(sentence);
        consumedLength = sentenceRegex.lastIndex;
      }

      rest = normalizeText(rest.slice(consumedLength));
      const words = rest.split(/\s+/).filter(Boolean);

      while (words.length >= 10) {
        const piece = normalizeText(words.splice(0, 10).join(" "));
        if (piece) chunks.push(piece);
      }

      if (forceFlush && words.length) {
        chunks.push(normalizeText(words.join(" ")));
        return { chunks, remainder: "" };
      }

      return { chunks, remainder: normalizeText(words.join(" ")) };
    }

    function getCurrentWindowText(segArray) {
      if (!Array.isArray(segArray)) return "";
      return normalizeText(segArray.map((s) => s?.text || "").join(" "));
    }

    function saveWindowStyle() {
      if (!containerElement) return;
      setSetting("windowStyle", {
        top: containerElement.style.top,
        left: containerElement.style.left,
        width: containerElement.style.width,
        height: containerElement.style.height
      });
    }

    function clearSilenceMonitor() {
      if (silenceFlushTimer) { clearInterval(silenceFlushTimer); silenceFlushTimer = null; }
    }

    function stopTtsNow() {
      try { chrome.tts?.stop(); } catch (e) {}
      try { window.speechSynthesis?.cancel(); } catch (e) {}
      try { chrome.runtime.sendMessage({ action: "stopTts" }); } catch (e) {}
    }

    function resetTranslationContext() {
      try { chrome.runtime.sendMessage({ action: "resetTranslationContext" }); } catch (e) {}
    }

    function resetRuntimeState() {
      segments = [];
      previousSegments = [];
      dedupTail = historyChunks.slice(-40);
      historyChunks = [];
      historyChunksRaw = [];
      translatedChunks = [];
      pendingStableText = "";
      windowStartTime = Date.now();
      currentFormatting = currentFormatting || "advanced";
      currentDisplayMode = currentDisplayMode || "both";
      currentFontSize = currentFontSize || 20;
      lastReceivedTime = Date.now();
      translationQueue = [];
      isTranslatingLocal = false;
      if (statusClearTimer) { clearTimeout(statusClearTimer); statusClearTimer = null; }
      window.__transcriptionStatusText = "";
      resetTranslationContext();
    }

    function queueTranslation(text) {
      if (!enableGeminiTranslation) return;
    
      const cleanText = removeInternalRepetitions(normalizeText(text));
      if (!cleanText || cleanText.split(/\s+/).length < 2) return;
    
      if (translationQueue.length === 0) {
        translationQueue.push(cleanText);
      } else {
        const lastInQueue = translationQueue[translationQueue.length - 1];
        const newPart = trimPrefixOverlap(lastInQueue, cleanText, 60, 3);
        
        if (stripPunctuation(newPart).length < stripPunctuation(cleanText).length * 0.95) {
          translationQueue[translationQueue.length - 1] = cleanText;
        } else {
          translationQueue.push(cleanText);
        }
      }
    
      const queued = translationQueue.join(" ");
      const wordCount = queued.split(/\s+/).filter(Boolean).length;
      const hasSentenceBoundary = /[.!?\u2026]/.test(queued);
    
      if (!isTranslatingLocal && (wordCount >= activeProfile.translationMinWords || (wordCount >= activeProfile.translationSentenceWords && hasSentenceBoundary))) {
        processTranslationQueue();
      }
    }
    
    function processTranslationQueue() {
      if (isTranslatingLocal || translationQueue.length === 0) return;
      
      const text = translationQueue.join(" ");
      translationQueue = []; // Clear queue now
      isTranslatingLocal = true;

      const shownTail = translatedChunks.slice(-3).join(" ")
        .split(/\s+/).filter(Boolean).slice(-8).join(" ");

      chrome.runtime.sendMessage({ action: "processTranslation", text, shownTail }, (response) => {
        const runtimeErr = chrome.runtime.lastError?.message || "";
        isTranslatingLocal = false;

        if (!runtimeErr && response?.success) {
          if (response.data) {
            addTranslatedChunk(response.data);
            updateHeaderStatusText("Translation Active");
          }
        } else {
          const errMsg = response?.error || runtimeErr || "Translation failed";
          updateHeaderStatusText(`Translation Error: ${errMsg}`);
          console.error("Translation failed:", errMsg, response || null);
          translationQueue.unshift(text); // Re-queue text on failure
        }

        if (translationQueue.length > 0) {
          setTimeout(processTranslationQueue, 100);
        }
      });
    }

    function addTranslatedChunk(text) {
      const clean = normalizeText(removeInternalRepetitions(normalizeText(text), 4));
      if (!clean) { renderText(); return; }

      const recentHistory = translatedChunks.slice(-15).join(" ");
      let deduped = clean;

      if (recentHistory) {
        deduped = trimPrefixOverlap(recentHistory, clean, 60, 2);
      }

      if (!deduped) { renderText(); return; }

      const isDuplicate = translatedChunks.slice(-10).some(
        chunk => calculateTextSimilarity(chunk, deduped) > 0.85
      );
      if (isDuplicate) { renderText(); return; }

      const recentFull = stripPunctuation(translatedChunks.slice(-20).join(" "));
      const dedupStripped = stripPunctuation(deduped);
      if (dedupStripped.length > 15 && recentFull.includes(dedupStripped)) {
        renderText(); return;
      }

      translatedChunks.push(deduped);
      if (translatedChunks.length > 5000) translatedChunks.shift();
      renderText();
    }

    function appendCommittedChunk(text) {
      const originalText = String(text || "");
      const incoming = normalizeText(text);
      if (!incoming) return;

      const allHistory = [...dedupTail, ...historyChunks];
      let deduped = trimPrefixOverlap(allHistory.slice(-12).join(" "), incoming);
      deduped = normalizeText(deduped);
      if (!deduped) return;

      const lastChunks = allHistory.slice(-6).join(" ");
      if (calculateTextSimilarity(lastChunks, deduped) > 0.80) return;

      const dedupedWords = deduped.split(/\s+/).filter(Boolean);
      if (dedupedWords.length <= 5) {
        const dedupedStripped = stripPunctuation(deduped);
        const recentHistoryStripped = stripPunctuation(allHistory.slice(-50).join(" "));
        if (dedupedStripped && recentHistoryStripped.includes(dedupedStripped)) return;
      }

      const startAnchor = stripPunctuation(normalizeText(deduped).split(/\s+/).slice(0, 7).join(" "));
      if (startAnchor.split(" ").length >= 5) {
        const historySearchable = stripPunctuation(allHistory.slice(-30).join(" "));
        if (historySearchable.includes(startAnchor)) return;
      }

      const rawDeduped = trimPrefixOverlapRaw(allHistory.slice(-12).join(" "), originalText);

      historyChunks.push(deduped);
      historyChunksRaw.push(rawDeduped);
      if (historyChunks.length > 5000) { historyChunks.shift(); historyChunksRaw.shift(); }

      if (enableGeminiTranslation) {
        queueTranslation(deduped);
      } else if (enableTts) {
        chrome.runtime.sendMessage({ action: "speakOriginalText", text: deduped });
      }
    }

    function absorbStableText(text, forceFlush = false) {
      pendingStableText = normalizeText(`${pendingStableText ? `${pendingStableText} ` : ""}${text || ""}`);
      if (!pendingStableText) return;

      const { chunks, remainder } = splitIntoFlushableChunks(pendingStableText, forceFlush);
      for (const chunk of chunks) appendCommittedChunk(chunk);
      pendingStableText = remainder;
    }

    function updateHistory(newSegments) {
      if (!Array.isArray(newSegments) || newSegments.length === 0) return;
      lastReceivedTime = Date.now();

      if (!previousSegments.length) {
        previousSegments = newSegments.slice();
        windowStartTime = Date.now();
        return;
      }

      const transferFlags = () => {
        for (let i = 0; i < newSegments.length; i++) {
          const rawNew = stripPunctuation(newSegments[i]?.text || "");
          const foundIdx = previousSegments.findIndex(s => stripPunctuation(s?.text || "") === rawNew);
          if (foundIdx !== -1) {
            newSegments[i]._committed = previousSegments[foundIdx]._committed;
          }
        }
      };

      const P = activeProfile;
      const currentWindowText = getCurrentWindowText(newSegments);
      const wordCount = splitWords(currentWindowText).length;
      const elapsed = Date.now() - windowStartTime;
      const isStable = wordCount >= P.stableWordCount || elapsed >= P.stableElapsed || newSegments.length >= P.stableSegments;

      if (!isStable) {
        transferFlags();
        previousSegments = newSegments.slice();
        return;
      }

      let alignmentShift = -1;
      const samplesToTry = Math.min(P.alignmentSamples, newSegments.length);

      for (let i = 0; i < samplesToTry; i++) {
        const newSegText = stripPunctuation(newSegments[i]?.text || "");
        if (!newSegText) continue;
        const foundIdx = previousSegments.findIndex(s => stripPunctuation(s?.text || "") === newSegText);
        if (foundIdx !== -1) {
          alignmentShift = foundIdx - i;
          break;
        }
      }

      if (alignmentShift >= 0) {
        for (let i = 0; i < alignmentShift; i++) {
          const seg = previousSegments[i];
          if (seg && !seg._committed && seg.text && seg.text.trim()) {
            appendCommittedChunk(seg.text.trim());
            seg._committed = true;
          }
        }

        for (let i = 0; i < newSegments.length; i++) {
          const prevIdx = i + alignmentShift;
          if (prevIdx < previousSegments.length) {
            newSegments[i]._committed = previousSegments[prevIdx]._committed;
          } else {
            const rawNew = stripPunctuation(newSegments[i]?.text || "");
            const fallbackIdx = previousSegments.findIndex(s => stripPunctuation(s?.text || "") === rawNew);
            if (fallbackIdx !== -1) newSegments[i]._committed = previousSegments[fallbackIdx]._committed;
          }
        }

        if (newSegments.length >= P.safeCommitMinSeg || elapsed > P.safeCommitElapsed) {
          const safeToCommit = Math.max(0, newSegments.length - P.safeCommitKeep);
          for (let i = 0; i < safeToCommit; i++) {
            const seg = newSegments[i];
            if (!seg._committed && seg.text && seg.text.trim()) {
              appendCommittedChunk(seg.text.trim());
              seg._committed = true;
            }
          }
          windowStartTime = Date.now();
        }

        previousSegments = newSegments.slice();

      } else {
        if (elapsed > P.fallbackElapsed) {
          previousSegments.forEach(seg => {
            if (seg && !seg._committed && seg.text && seg.text.trim()) {
              appendCommittedChunk(seg.text.trim());
              seg._committed = true;
            }
          });
          transferFlags();
          previousSegments = newSegments.slice();
          windowStartTime = Date.now();
        } else {
          transferFlags();
          previousSegments = newSegments.slice();
        }
      }
    }

    function getVisibleOriginalText() {
      if (currentFormatting === "none") {
        const recentRaw = historyChunksRaw.join("\n").replace(/\n{3,}/g, "\n\n").trim();
        return recentRaw + (pendingStableText ? "\n" + pendingStableText : "");
      }
      const fullText = historyChunks.join(" ");
      return normalizeText(`${fullText}${pendingStableText ? ` ${pendingStableText}` : ""}`);
    }

    function applyDisplayMode() {
      if (!transcriptionOriginalEl || !transcriptionTranslatedEl || !dividerEl) return;

      if (mainWrapperEl) {
        mainWrapperEl.style.display       = "flex";
        mainWrapperEl.style.flexDirection = "column";
        mainWrapperEl.style.flex          = "1 1 0%";
        mainWrapperEl.style.overflow      = "hidden";
      }

      const hasTranslation = translatedChunks.length > 0;
      const showTranslation = (enableGeminiTranslation || hasTranslation) &&
        (currentDisplayMode === "translation" || currentDisplayMode === "both");
      const showOriginal = currentDisplayMode === "original" || currentDisplayMode === "both" || !showTranslation;

      if (showOriginal && !showTranslation) {
        transcriptionOriginalEl.style.display = "flex";
        transcriptionOriginalEl.style.flex = "1 1 0%";
        transcriptionTranslatedEl.style.display = "none";
        dividerEl.style.display = "none";
      } else if (!showOriginal && showTranslation) {
        transcriptionOriginalEl.style.display = "none";
        dividerEl.style.display = "none";
        transcriptionTranslatedEl.style.display = "flex";
        transcriptionTranslatedEl.style.flex = "1 1 0%";
      } else {
        transcriptionOriginalEl.style.display = "block";
        transcriptionTranslatedEl.style.display = "block";
        dividerEl.style.display = "block";
        if (!transcriptionOriginalEl.style.flex || transcriptionOriginalEl.style.flex === "0 1 0%") {
          transcriptionOriginalEl.style.flex = "1 1 0%";
        }
        if (!transcriptionTranslatedEl.style.flex || transcriptionTranslatedEl.style.flex === "0 1 0%") {
          transcriptionTranslatedEl.style.flex = "1 1 0%";
        }
      }
    }

    function renderBlock(el, text, extraStyle = "") {
      if (!el) return;
      el.innerHTML = `<span style="${TEXT_BLOCK_STYLE}${extraStyle}">${escapeHtml(text).replace(/\n/g, "<br>")}</span>`;
    }

    function renderText() {
      if (!transcriptionOriginalEl || !transcriptionTranslatedEl) return;
      updateHistory(segments);

      const committedText = getVisibleOriginalText();
      const originalFormatted = formatText(committedText, currentFormatting);

      let livePreviewHtml = "";
      if (!hideLiveText && segments.length > 0) {
        const liveRaw = normalizeText(getCurrentWindowText(segments));
        if (liveRaw) {
          const historyTail = normalizeText(committedText).split(/\s+/).slice(-60).join(" ");
          const trimmed = normalizeText(trimPrefixOverlap(historyTail, liveRaw, 80, 2));
          if (trimmed) {
            const liveFormatted = formatText(trimmed, currentFormatting);
            const liveLines = liveFormatted.split("\n");
            const liveCapped = liveLines.slice(-3).join("\n");
            livePreviewHtml = `<span style="opacity:0.35;font-style:italic;">${escapeHtml(liveCapped)}</span>`;
          }
        }
      }

      if (transcriptionOriginalEl) {
        transcriptionOriginalEl.innerHTML =
          `<span style="${TEXT_BLOCK_STYLE}">${escapeHtml(originalFormatted).replace(/\n/g, "<br>")}${livePreviewHtml ? "<br>" + livePreviewHtml.replace(/\n/g, "<br>") : ""}</span>`;
      }

      const translatedFull = formatText(normalizeText(translatedChunks.join(" ")), currentFormatting);
      renderBlock(transcriptionTranslatedEl, translatedFull, "color:#a7f3d0;font-style:italic;");

      applyDisplayMode();

      transcriptionOriginalEl.scrollTop = transcriptionOriginalEl.scrollHeight;
      transcriptionTranslatedEl.scrollTop = transcriptionTranslatedEl.scrollHeight;
    }

    function startSilenceMonitor() {
      clearSilenceMonitor();
      const P = activeProfile;
      silenceFlushTimer = setInterval(() => {
        const now = Date.now();
        if (now - lastReceivedTime > P.silenceFlushMs) {
          if (previousSegments.length > 0) {
            previousSegments.forEach(seg => {
              if (seg && !seg._committed && seg.text && seg.text.trim()) {
                appendCommittedChunk(seg.text.trim());
                seg._committed = true;
              }
            });
            previousSegments = [];
            segments = [];
            renderText();
          } else if (pendingStableText) {
            absorbStableText("", true);
            renderText();
          }
          if (translationQueue.length > 0 && !isTranslatingLocal && now - lastReceivedTime > P.translationSilenceMs) {
            processTranslationQueue();
          }
        }
      }, P.silenceCheckMs);
    }

    function updateHeaderAndStatus(settings) {
      if (!transcriptionHeaderEl) return;
      const model = (settings.selectedModelSize || "small").toLowerCase();
      const lang = (settings.selectedLanguage || "AUTO").toUpperCase();
      const task = settings.selectedTask === "translate" ? "TRANSLATE" : "TRANSCRIBE";
      const geminiModel = settings.geminiModel || "";
      const target = (settings.targetLanguage || "ES").toUpperCase();
      const vad = settings.useVad ? "ON" : "OFF";
      const tts = settings.enableTts ? "ON" : "OFF";
      const geminiOn = enableGeminiTranslation;
      const statusText = window.__transcriptionStatusText || "";
      const isError = statusText && statusText.toLowerCase().includes("error");
      const statusBg = isError ? "rgba(220,38,38,0.25)" : "rgba(34,197,94,0.18)";
      const statusBorder = isError ? "rgba(248,113,113,0.4)" : "rgba(74,222,128,0.35)";
      const statusColor = isError ? "#fca5a5" : "#86efac";
      const versionText = MANIFEST_VERSION ? ` · v${MANIFEST_VERSION}` : "";
      const G = "#4ade80";
      const Mu = "#94a3b8";

      const pill = (label, value) =>
        `<span style="color:${Mu};">${label}</span> <span style="color:${G};">${escapeHtml(value)}</span>`;
      const sep = `&nbsp;&nbsp;`;

      const statsHtml =
        pill("Model", model) + sep +
        pill("Language", lang) + sep +
        pill("Task", task) + sep +
        pill("Gemini", geminiOn ? "ON" : "OFF") + sep +
        (geminiOn && geminiModel ? pill("Model", geminiModel) + sep : "") +
        pill("Target", target) + sep +
        pill("VAD", vad) + sep +
        pill("TTS", tts) +
        `<span style="color:#475569;">${escapeHtml(versionText)}</span>`;

      transcriptionHeaderEl.innerHTML = `
        <div style="padding:8px 16px 10px 16px;border-bottom:1px solid rgba(255,255,255,0.08);background:rgba(30,41,59,0.45);width:100%;box-sizing:border-box;">
          <div style="display:flex;align-items:center;min-height:22px;margin-bottom:3px;padding-right:10px;">
            <div style="font-size:13px;font-weight:700;color:#f8fafc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;">
              ${escapeHtml(document.title || "Live Transcription")}
            </div>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:10px;color:#94a3b8;letter-spacing:0.03em;line-height:1.5;min-height:18px;width:100%;">
            <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;">${statsHtml}</span>
            ${statusText ? `<span style="flex-shrink:0;padding:2px 8px;border-radius:999px;background:${statusBg};border:1px solid ${statusBorder};color:${statusColor};font-weight:700;font-size:10px;white-space:nowrap;display:inline-flex;align-items:center;max-width:200px;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(statusText)}</span>` : ""}
          </div>
        </div>
      `;
    }

    function updateHeaderStatusText(text) {
      window.__transcriptionStatusText = text;
      if (statusClearTimer) clearTimeout(statusClearTimer);
      const keys = ["selectedModelSize", "selectedLanguage", "selectedTask", "targetLanguage", "useVad", "enableTts", "geminiModel"];
      statusClearTimer = setTimeout(() => {
        window.__transcriptionStatusText = "";
        chrome.storage.local.get(keys, (res) => updateHeaderAndStatus(res || {}));
      }, 5000);
      chrome.storage.local.get(keys, (res) => updateHeaderAndStatus(res || {}));
    }

    function adjustFontSize(delta) {
      currentFontSize = Math.max(12, currentFontSize + delta);
      const lineHeight = `${Math.round(currentFontSize * 1.25)}px`;
      if (transcriptionOriginalEl) {
        transcriptionOriginalEl.style.fontSize = `${currentFontSize}px`;
        transcriptionOriginalEl.style.lineHeight = lineHeight;
      }
      if (transcriptionTranslatedEl) {
        transcriptionTranslatedEl.style.fontSize = `${Math.max(12, Math.round(currentFontSize * 0.92))}px`;
        transcriptionTranslatedEl.style.lineHeight = lineHeight;
      }
      setSetting("fontSize", currentFontSize);
    }

    function showWaitPopup(text) {
      if (!waitPopupEl) {
        waitPopupEl = document.createElement("div");
        waitPopupEl.id = "transcription-wait-popup";
        waitPopupEl.style.cssText = `
          position:fixed; z-index:2147483647; left:50%; top:50%; transform:translate(-50%, -50%);
          background:rgba(15,23,42,0.96); color:#f8fafc; border:1px solid #334155; border-radius:12px;
          padding:16px 20px; min-width:260px; max-width:420px; box-shadow:0 16px 40px rgba(0,0,0,0.45);
          text-align:center; font-size:16px; line-height:1.4;
        `;
        document.body.appendChild(waitPopupEl);
      }
      waitPopupEl.textContent = String(text || "").trim() || "Please wait...";
      waitPopupEl.style.display = "block";
      setTimeout(() => { if (waitPopupEl) waitPopupEl.style.display = "none"; }, 3500);
    }

    function createContainer() {
      containerElement = document.createElement("div");
      containerElement.id = "transcription";
      const defaultWidth = Math.min(820, Math.floor(window.innerWidth * 0.78));
      const defaultHeight = Math.min(320, Math.floor(window.innerHeight * 0.55));
      const defaultStyle = {
        top: `${Math.max(16, Math.floor(window.innerHeight - defaultHeight - 48))}px`,
        left: `${Math.max(16, Math.floor((window.innerWidth - defaultWidth) / 2))}px`,
        width: `${defaultWidth}px`,
        height: `${defaultHeight}px`
      };
      containerElement.style.cssText = CONTAINER_STYLE(defaultStyle);
      chrome.storage.local.get(["windowStyle"], (data) => {
        const s = data.windowStyle;
        if (s?.top && s?.left && s?.width && s?.height) {
          containerElement.style.top = s.top; containerElement.style.left = s.left;
          containerElement.style.width = s.width; containerElement.style.height = s.height;
        }
      });
    }

    function createContentArea() {
      transcriptionHeaderEl = document.createElement("div");
      transcriptionHeaderEl.id = "transcription-header";
      containerElement.appendChild(transcriptionHeaderEl);

      mainWrapperEl = document.createElement("div");
      mainWrapperEl.style.cssText = "display:flex;flex-direction:column;flex:1;overflow:hidden;position:relative;";

      transcriptionOriginalEl = document.createElement("div");
      transcriptionOriginalEl.id = "transcription-original";
      transcriptionOriginalEl.style.cssText = "flex:1 1 0%;overflow-y:auto;padding-top:8px;";

      dividerEl = document.createElement("div");
      dividerEl.id = "transcription-divider";
      dividerEl.style.cssText = "height:4px;background:rgba(255,255,255,0.1);cursor:row-resize;border-top:1px solid rgba(255,255,255,0.16);border-bottom:1px solid rgba(0,0,0,0.4);transition:background 0.2s;";

      transcriptionTranslatedEl = document.createElement("div");
      transcriptionTranslatedEl.id = "transcription-translated";
      transcriptionTranslatedEl.style.cssText = "flex:1 1 0%;overflow-y:auto;background:rgba(255,255,255,0.03);padding-top:8px;";

      dividerEl.addEventListener("mouseover", () => { dividerEl.style.background = "rgba(59,130,246,0.45)"; });
      dividerEl.addEventListener("mouseout", () => { if (!isDraggingDivider) dividerEl.style.background = "rgba(255,255,255,0.1)"; });

      dividerEl.addEventListener("mousedown", (e) => {
        isDraggingDivider = true;
        document.body.style.cursor = "row-resize";
        const startY = e.clientY;
        const startH = transcriptionOriginalEl.offsetHeight;
        const totalH = mainWrapperEl.offsetHeight;

        const onMouseMove = (ev) => {
          const delta = ev.clientY - startY;
          const newH = Math.max(40, Math.min(totalH - 40, startH + delta));
          const ratio = newH / totalH;
          transcriptionOriginalEl.style.flex = `${ratio} 1 0%`;
          transcriptionTranslatedEl.style.flex = `${1 - ratio} 1 0%`;
        };

        const onMouseUp = () => {
          isDraggingDivider = false;
          document.body.style.cursor = "default";
          dividerEl.style.background = "rgba(255,255,255,0.1)";
          document.removeEventListener("mousemove", onMouseMove);
          document.removeEventListener("mouseup", onMouseUp);
          const ratio = transcriptionOriginalEl.offsetHeight / mainWrapperEl.offsetHeight;
          setSetting("dividerPos", ratio);
        };

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
      });

      mainWrapperEl.appendChild(transcriptionOriginalEl);
      mainWrapperEl.appendChild(dividerEl);
      mainWrapperEl.appendChild(transcriptionTranslatedEl);
      containerElement.appendChild(mainWrapperEl);
    }

    function configureControls() {
      const controls = document.createElement("div");
      controls.style.cssText = "position:absolute;top:6px;right:6px;z-index:100;display:flex;gap:6px;";
      const makeButton = (label, onClick) => {
        const btn = document.createElement("button");
        btn.type = "button"; btn.textContent = label; btn.style.cssText = BUTTON_STYLE;
        btn.addEventListener("click", onClick);
        return btn;
      };
      controls.appendChild(makeButton("A-", () => adjustFontSize(-2)));
      controls.appendChild(makeButton("A+", () => adjustFontSize(2)));
      controls.appendChild(makeButton("Copy", async () => {
        const text = `Original:\n${transcriptionOriginalEl?.innerText || ""}\n\nTranslation:\n${transcriptionTranslatedEl?.innerText || ""}`;
        try { await navigator.clipboard.writeText(text); } catch (e) {}
      }));
      containerElement.appendChild(controls);
    }

    function configureMovement() {
      let x = 0; let y = 0;
      containerElement.addEventListener("mousedown", (e) => {
        const tag = e.target?.tagName?.toLowerCase?.() || "";
        if (tag === "button" || e.target === dividerEl) return;
        const rect = containerElement.getBoundingClientRect();
        const nearResizeCorner = rect.width - (e.clientX - rect.left) < 18 && rect.height - (e.clientY - rect.top) < 18;
        if (nearResizeCorner) return;

        x = e.clientX; y = e.clientY;
        const onMove = (ev) => {
          containerElement.style.top = `${Math.max(0, containerElement.offsetTop + (ev.clientY - y))}px`;
          containerElement.style.left = `${Math.max(0, containerElement.offsetLeft + (ev.clientX - x))}px`;
          x = ev.clientX; y = ev.clientY;
        };
        const onUp = () => {
          document.removeEventListener("mousemove", onMove); document.removeEventListener("mouseup", onUp);
          debouncedSaveWindowStyle();
        };
        document.addEventListener("mousemove", onMove); document.addEventListener("mouseup", onUp);
      });

      if (window.ResizeObserver) {
        resizeObserver = new ResizeObserver(() => debouncedSaveWindowStyle());
        resizeObserver.observe(containerElement);
      }
    }

    function applySavedUiSettings() {
      chrome.storage.local.get(
        ["textFormatting", "fontSize", "displayMode", "dividerPos", "selectedModelSize",
         "selectedLanguage", "selectedTask", "targetLanguage", "useVad", "enableTts",
         "enableGeminiTranslation", "geminiModel", "transcriptionProfile", "hideLiveText"],
        (res) => {
          currentFormatting = res.textFormatting || "advanced";
          currentDisplayMode = res.displayMode || "both";
          currentFontSize = res.fontSize || 20;
          enableGeminiTranslation = !!res.enableGeminiTranslation;
          enableTts = !!res.enableTts;
          hideLiveText = !!res.hideLiveText;
          activeProfile = getProfile(res.transcriptionProfile || "balanced");

          if (res.dividerPos) {
            const pos = parseFloat(res.dividerPos);
            if (Number.isFinite(pos) && pos > 0.1 && pos < 0.9) {
              if (transcriptionOriginalEl) transcriptionOriginalEl.style.flex = `${pos} 1 0%`;
              if (transcriptionTranslatedEl) transcriptionTranslatedEl.style.flex = `${1 - pos} 1 0%`;
            }
          }

          adjustFontSize(0);
          updateHeaderAndStatus(res || {});
          applyDisplayMode();
          renderText();
        }
      );
    }

    function ensureOverlay() {
      let existing = document.getElementById("transcription");
      if (existing) {
        containerElement = existing;
        transcriptionHeaderEl = document.getElementById("transcription-header");
        transcriptionOriginalEl = document.getElementById("transcription-original");
        transcriptionTranslatedEl = document.getElementById("transcription-translated");
        dividerEl = document.getElementById("transcription-divider");
        mainWrapperEl = transcriptionOriginalEl?.parentElement || null;
        return;
      }
      createContainer();
      createContentArea();
      configureControls();
      configureMovement();
      document.body.appendChild(containerElement);
      applySavedUiSettings();
    }

    function hardRemoveOverlay() {
      clearSilenceMonitor();
      if (resizeObserver) { try { resizeObserver.disconnect(); } catch (e) {} resizeObserver = null; }
      if (containerElement?.parentNode) containerElement.parentNode.removeChild(containerElement);
      if (waitPopupEl?.parentNode) waitPopupEl.parentNode.removeChild(waitPopupEl);
      containerElement = null; transcriptionHeaderEl = null; transcriptionOriginalEl = null;
      transcriptionTranslatedEl = null; dividerEl = null; mainWrapperEl = null; waitPopupEl = null;
    }

    function stopAndCloseOverlay() { stopTtsNow(); resetRuntimeState(); hardRemoveOverlay(); }
    function resetSessionView() { ensureOverlay(); resetRuntimeState(); startSilenceMonitor(); applySavedUiSettings(); renderText(); }

    function handleTranscriptPayload(raw) {
      ensureOverlay();
      let parsed;
      try { parsed = typeof raw === "string" ? JSON.parse(raw) : raw; } catch (e) { parsed = null; }
      segments = Array.isArray(parsed?.segments) ? parsed.segments : [];
      lastReceivedTime = Date.now();

      chrome.storage.local.get(
        ["displayMode", "textFormatting", "fontSize", "selectedModelSize", "selectedLanguage",
         "selectedTask", "targetLanguage", "useVad", "enableTts", "enableGeminiTranslation", "geminiModel",
         "transcriptionProfile", "hideLiveText"],
        (res) => {
          currentDisplayMode = res.displayMode || "both";
          currentFormatting = res.textFormatting || "advanced";
          currentFontSize = res.fontSize || 20;
          enableGeminiTranslation = !!res.enableGeminiTranslation;
          enableTts = !!res.enableTts;
          hideLiveText = !!res.hideLiveText;
          const newProfile = getProfile(res.transcriptionProfile || "balanced");
          if (newProfile !== activeProfile) {
            activeProfile = newProfile;
            startSilenceMonitor();
          }
          adjustFontSize(0);
          updateHeaderAndStatus(res || {});
          renderText();
        }
      );
    }

    function onMessage(request, sender, sendResponse) {
      try {
        if (request.type === "resetSession") { resetSessionView(); sendResponse({ success: true }); return true; }
        if (request.type === "showWaitPopup") { ensureOverlay(); showWaitPopup(request.data); sendResponse({ success: true }); return true; }
        if (request.type === "transcript") { handleTranscriptPayload(request.data); sendResponse({ success: true }); return true; }
        if (request.type === "translationResult") { addTranslatedChunk(request.data); sendResponse({ success: true }); return true; }
        if (request.type === "STOP") { stopAndCloseOverlay(); sendResponse({ success: true }); return true; }
        sendResponse({ success: false });
      } catch (e) {
        sendResponse({ success: false, error: e.message });
      }
      return true;
    }

    function bindMessageListenerOnce() {
      if (listenerBound) return;
      chrome.runtime.onMessage.addListener(onMessage);
      listenerBound = true;
    }

    function bindStorageListener() {
      chrome.storage.onChanged.addListener((changes, area) => {
        if (area !== "local") return;
        let needsRender = false;

        if ("enableGeminiTranslation" in changes) {
          enableGeminiTranslation = !!changes.enableGeminiTranslation.newValue;
          if (!enableGeminiTranslation) { translatedChunks = []; translationQueue = []; isTranslatingLocal = false; }
          needsRender = true;
        }
        if ("enableTts" in changes) {
          enableTts = !!changes.enableTts.newValue;
          needsRender = true;
        }
        if ("displayMode" in changes) { currentDisplayMode = changes.displayMode.newValue || "both"; needsRender = true; }
        if ("textFormatting" in changes) { currentFormatting = changes.textFormatting.newValue || "advanced"; needsRender = true; }
        if ("hideLiveText" in changes) { hideLiveText = !!changes.hideLiveText.newValue; needsRender = true; }
        if ("transcriptionProfile" in changes) {
          activeProfile = getProfile(changes.transcriptionProfile.newValue || "balanced");
          startSilenceMonitor();
          needsRender = true;
        }

        if (needsRender && transcriptionOriginalEl) renderText();
      });
    }

    function reactivate() { ensureOverlay(); startSilenceMonitor(); applySavedUiSettings(); renderText(); }
    function init() { bindMessageListenerOnce(); bindStorageListener(); ensureOverlay(); startSilenceMonitor(); applySavedUiSettings(); }

    init();
    return { reactivate, stopAndCloseOverlay };
  })();
}
