(function () {
  const TEXT_BLOCK_STYLE =
    "padding:0 16px 10px 16px;display:block;white-space:pre-wrap;word-break:break-word;";

  const MANIFEST_VERSION = chrome.runtime.getManifest?.()?.version || "";

  const transcriptionOriginalEl = document.getElementById("transcription-original");
  const transcriptionTranslatedEl = document.getElementById("transcription-translated");
  const transcriptionHeaderEl = document.getElementById("transcription-header");
  const statusLineEl = document.getElementById("status-line");
  const dividerEl = document.getElementById("transcription-divider");
  const contentWrapper = document.getElementById("transcription-content");
  const btnDecrease = document.getElementById("btn-decrease");
  const btnIncrease = document.getElementById("btn-increase");
  const btnCopy = document.getElementById("btn-copy");

  if (transcriptionHeaderEl) transcriptionHeaderEl.style.display = "none";

  let segments = [];
  let previousSegments = [];
  let historyChunks = [];
  let translatedChunks = [];
  let pendingStableText = "";
  let windowStartTime = Date.now();
  let currentFormatting = "advanced";
  let currentDisplayMode = "both";
  let currentFontSize = 20;
  let lastReceivedTime = Date.now();
  let silenceFlushTimer = null;
  let statusClearTimer = null;
  let isDraggingDivider = false;
  let translationQueue = [];
  let isTranslatingLocal = false;
  let enableGeminiTranslation = false;
  let dedupTail = [];

  function normalizeText(text) { return String(text || "").replace(/\s+/g, " ").trim(); }
  function splitWords(text) { return normalizeText(text).toLowerCase().split(" ").filter(Boolean); }
  function escapeHtml(value) {
    return String(value || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  }
  function stripPunctuation(text) {
    return String(text || "").toLowerCase().replace(/[^\w\s']/g, " ").replace(/\s+/g, " ").trim();
  }

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
    const rawCandidateWords = normalizeText(candidateText).split(/\s+/).filter(Boolean);
    const candidateWords = splitWords(candidateText);
    const max = Math.min(maxWords, baseWords.length, candidateWords.length);

    for (let size = max; size >= minWords; size--) {
      let ok = true;
      for (let i = 0; i < size; i++) {
        if (baseWords[baseWords.length - size + i] !== candidateWords[i]) { ok = false; break; }
      }
      if (ok) return rawCandidateWords.slice(size).join(" ").trim();
    }
    return normalizeText(candidateText);
  }

  function formatText(text, formatting) {
    const clean = normalizeText(text);
    if (!clean) return "";
    if (formatting === "none") return clean.replace(/([.!?\u2026])\s+/g, "$1\n");
    if (formatting === "join") return clean;
    return clean.replace(/([.!?\u2026])\s+(?=[A-Za-z¿¡])/g, "$1\n").replace(/([.!?\u2026])\s*(¿|¡)/g, "$1\n$2");
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

  function queueTranslation(text) {
    if (!enableGeminiTranslation) return;
    const clean = normalizeText(text);
    if (!clean) return;
    if (translationQueue.length > 0) {
      translationQueue[0] = normalizeText(translationQueue[0] + " " + clean);
    } else {
      translationQueue.push(clean);
    }
    processTranslationQueue();
  }

  function processTranslationQueue() {
    if (isTranslatingLocal || translationQueue.length === 0) return;
    const text = translationQueue.shift();
    isTranslatingLocal = true;
    
    chrome.runtime.sendMessage({ action: "processTranslation", text }, (response) => {
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
      }
      
      if (translationQueue.length > 0) processTranslationQueue();
    });
  }

  function addTranslatedChunk(text) {
    const clean = normalizeText(text);
    if (clean) {
      const last = translatedChunks[translatedChunks.length - 1] || "";
      if (!last || calculateTextSimilarity(last, clean) <= 0.90) {
        translatedChunks.push(clean);
        if (translatedChunks.length > 140) translatedChunks.shift();
      }
    }
    renderText();
  }

  function appendCommittedChunk(text) {
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
      const historySearchable = stripPunctuation(allHistory.join(" "));
      if (historySearchable.includes(startAnchor)) return;
    }

    historyChunks.push(deduped);
    if (historyChunks.length > 200) historyChunks.shift();

    queueTranslation(deduped);
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

    const currentWindowText = getCurrentWindowText(newSegments);
    const wordCount = splitWords(currentWindowText).length;
    const elapsed = Date.now() - windowStartTime;
    const isStable = wordCount >= 10 || elapsed >= 1500 || newSegments.length >= 5;

    if (!isStable) {
      previousSegments = newSegments.slice();
      return;
    }

    let alignmentShift = -1;
    const samplesToTry = Math.min(4, newSegments.length);
    
    for (let i = 0; i < samplesToTry; i++) {
      const newSegText = newSegments[i].text.trim();
      if (!newSegText) continue;
      const idx = previousSegments.findIndex(s => s.text.trim() === newSegText);
      if (idx !== -1) { alignmentShift = idx - i; break; }
    }

    if (alignmentShift > 0) {
      for (let i = 0; i < alignmentShift; i++) {
        const txt = previousSegments[i]?.text;
        if (txt && txt.trim()) appendCommittedChunk(txt.trim());
      }
      previousSegments = newSegments.slice();
      windowStartTime = Date.now();
    } else if (alignmentShift === 0) {
      previousSegments = newSegments.slice();
    } else if (alignmentShift === -1) {
      if (elapsed > 6000) {
        previousSegments.forEach(seg => {
          if (seg.text && seg.text.trim()) appendCommittedChunk(seg.text.trim());
        });
        previousSegments = newSegments.slice();
        windowStartTime = Date.now();
      } else {
        previousSegments = newSegments.slice();
      }
    }
  }

  function getVisibleOriginalText() {
    const allHistoryWords = splitWords(historyChunks.join(" "));
    const historyText = normalizeText(allHistoryWords.slice(-400).join(" "));
    return normalizeText(`${historyText ? `${historyText} ` : ""}${pendingStableText || ""}`);
  }

  function applyDisplayMode() {
    if (!transcriptionOriginalEl || !transcriptionTranslatedEl || !dividerEl) return;
    
    if (contentWrapper) {
      contentWrapper.style.display = "flex";
      contentWrapper.style.flexDirection = "column";
      contentWrapper.style.overflow = "hidden";
      contentWrapper.style.flex = "1 1 0%";
    }
    
    transcriptionOriginalEl.style.overflowY = "auto";
    transcriptionTranslatedEl.style.overflowY = "auto";
    
    const hasTranslation = translatedChunks.length > 0;
    const showTranslation = (enableGeminiTranslation || hasTranslation) &&
      (currentDisplayMode === "translation" || currentDisplayMode === "both");
    const showOriginal = currentDisplayMode === "original" || currentDisplayMode === "both" || !showTranslation;

    if (showOriginal && !showTranslation) {
      transcriptionOriginalEl.style.display = "block";
      transcriptionOriginalEl.style.flex = "1 1 0%";
      transcriptionTranslatedEl.style.display = "none";
      dividerEl.style.display = "none";
    } else if (!showOriginal && showTranslation) {
      transcriptionOriginalEl.style.display = "none";
      dividerEl.style.display = "none";
      transcriptionTranslatedEl.style.display = "block";
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

  function clearSilenceMonitor() {
    if (silenceFlushTimer) { clearInterval(silenceFlushTimer); silenceFlushTimer = null; }
  }

  function stopTtsNow() {
    try { chrome.tts?.stop(); } catch (e) {}
    try { window.speechSynthesis?.cancel(); } catch (e) {}
    try { chrome.runtime.sendMessage({ action: "stopTts" }); } catch (e) {}
  }

  function startSilenceMonitor() {
    clearSilenceMonitor();
    silenceFlushTimer = setInterval(() => {
      const now = Date.now();
      if (now - lastReceivedTime > 1200) {
        if (previousSegments.length > 0) {
          previousSegments.forEach(seg => {
            if (seg.text && seg.text.trim()) appendCommittedChunk(seg.text.trim());
          });
          previousSegments = [];
          segments = [];
          renderText();
        } else if (pendingStableText) {
          absorbStableText("", true);
          renderText();
        }
      }
    }, 800);
  }

  function updateStatusBar(settings) {
    if (!statusLineEl) return;
    
    statusLineEl.style.cssText =
      "display:flex;align-items:center;justify-content:space-between;gap:8px;overflow:hidden;white-space:nowrap;" +
      "min-width:0;padding:2px 8px;min-height:22px;width:100%;box-sizing:border-box;";
      
    const model = (settings.selectedModelSize || "small").toLowerCase();
    const lang = (settings.selectedLanguage || "AUTO").toUpperCase();
    const task = settings.selectedTask === "translate" ? "TRANSLATE" : "TRANSCRIBE";
    const geminiModel = settings.geminiModel || "";
    const target = (settings.targetLanguage || "ES").toUpperCase();
    const vad = settings.useVad ? "ON" : "OFF";
    const tts = settings.enableTts ? "ON" : "OFF";
    const geminiOn = enableGeminiTranslation;
    const G = "#4ade80"; 
    const M = "#94a3b8"; 
    const statusText = window.__transcriptionStatusText || "";
    const isError = statusText && statusText.toLowerCase().includes("error");
    const statusBg = isError ? "rgba(220,38,38,0.25)" : "rgba(34,197,94,0.18)";
    const statusBorder = isError ? "rgba(248,113,113,0.4)" : "rgba(74,222,128,0.35)";
    const statusColor = isError ? "#fca5a5" : "#86efac";
    const versionText = MANIFEST_VERSION ? ` · v${MANIFEST_VERSION}` : "";

    const pill = (label, value, active = true) =>
      `<span style="white-space:nowrap;"><span style="color:${M};">${label}&nbsp;</span><span style="color:${active ? G : M};">${escapeHtml(value)}</span></span>`;

    const sep = `<span style="color:#475569;padding:0 4px;font-size:10px;">·</span>`;

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

    statusLineEl.innerHTML =
      `<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${statsHtml}</span>` +
      (statusText ? `<span style="flex-shrink:0;padding:2px 8px;border-radius:999px;background:${statusBg};border:1px solid ${statusBorder};color:${statusColor};font-weight:700;font-size:10px;white-space:nowrap;">${escapeHtml(statusText)}</span>` : "");
  }

  function updateHeaderStatusText(text) {
    window.__transcriptionStatusText = text;
    if (statusClearTimer) clearTimeout(statusClearTimer);
    const keys = ["selectedModelSize", "selectedLanguage", "selectedTask", "targetLanguage", "useVad", "enableTts", "geminiModel"];
    statusClearTimer = setTimeout(() => {
      window.__transcriptionStatusText = "";
      chrome.storage.local.get(keys, (res) => updateStatusBar(res || {}));
    }, 5000);
    chrome.storage.local.get(keys, (res) => updateStatusBar(res || {}));
  }

  function applyFontSize(size) {
    currentFontSize = Math.max(12, size);
    const lineHeight = `${Math.round(currentFontSize * 1.25)}px`;
    if(transcriptionOriginalEl) {
      transcriptionOriginalEl.style.fontSize = `${currentFontSize}px`;
      transcriptionOriginalEl.style.lineHeight = lineHeight;
    }
    if(transcriptionTranslatedEl) {
      transcriptionTranslatedEl.style.fontSize = `${Math.max(12, Math.round(currentFontSize * 0.92))}px`;
      transcriptionTranslatedEl.style.lineHeight = lineHeight;
    }
    chrome.storage.local.set({ fontSize: currentFontSize });
  }

  function resetGlobalState() {
    segments = [];
    previousSegments = [];
    dedupTail = historyChunks.slice(-40);
    historyChunks = [];
    translatedChunks = [];
    pendingStableText = "";
    windowStartTime = Date.now();
    lastReceivedTime = Date.now();
    translationQueue = [];
    isTranslatingLocal = false;
    if (statusClearTimer) { clearTimeout(statusClearTimer); statusClearTimer = null; }
    window.__transcriptionStatusText = "";
    try { chrome.runtime.sendMessage({ action: "resetTranslationContext" }); } catch (e) {}
  }

  function handleTranscriptPayload(raw) {
    let parsed;
    try { parsed = typeof raw === "string" ? JSON.parse(raw) : raw; } catch (e) { parsed = null; }
    segments = Array.isArray(parsed?.segments) ? parsed.segments : [];
    lastReceivedTime = Date.now();

    chrome.storage.local.get(
      ["displayMode", "textFormatting", "fontSize", "selectedModelSize", "selectedLanguage",
       "selectedTask", "targetLanguage", "useVad", "enableTts", "enableGeminiTranslation", "geminiModel"],
      (res) => {
        currentDisplayMode = res.displayMode || "both";
        currentFormatting = res.textFormatting || "advanced";
        enableGeminiTranslation = !!res.enableGeminiTranslation;
        applyFontSize(res.fontSize || currentFontSize || 20);
        updateStatusBar(res || {});
        renderText();
      }
    );
  }

  dividerEl.addEventListener("mousedown", (e) => {
    if (currentDisplayMode !== "both" || !enableGeminiTranslation) return;
    isDraggingDivider = true;
    document.body.style.cursor = "row-resize";

    const headerHeight = transcriptionHeaderEl.offsetHeight || 0;
    const startY = e.clientY;
    const startH = transcriptionOriginalEl.offsetHeight;
    const totalH = contentWrapper.offsetHeight - headerHeight;

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
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);

      const headerHeightNow = transcriptionHeaderEl.offsetHeight || 0;
      const ratio = transcriptionOriginalEl.offsetHeight / Math.max(1, contentWrapper.offsetHeight - headerHeightNow);
      chrome.storage.local.set({ dividerPos: ratio });
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  });

  btnDecrease.addEventListener("click", () => { applyFontSize(currentFontSize - 2); renderText(); });
  btnIncrease.addEventListener("click", () => { applyFontSize(currentFontSize + 2); renderText(); });
  btnCopy.addEventListener("click", async () => {
    const text = `Original:\n${transcriptionOriginalEl?.innerText || ""}\n\nTranslation:\n${transcriptionTranslatedEl?.innerText || ""}`;
    try { await navigator.clipboard.writeText(text); } catch (e) {}
  });

  function renderBlock(el, text, extraStyle = "") {
    if (!el) return;
    el.innerHTML = `<span style="${TEXT_BLOCK_STYLE}${extraStyle}">${escapeHtml(text)}</span>`;
  }

  function renderText() {
    updateHistory(segments);

    const committedText = getVisibleOriginalText();
    const originalFormatted = formatText(committedText, currentFormatting);

    let livePreviewHtml = "";
    if (segments.length > 0) {
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
        `<span style="${TEXT_BLOCK_STYLE}">${escapeHtml(originalFormatted)}${livePreviewHtml ? "\n" + livePreviewHtml : ""}</span>`;
    }

    const translatedFull = formatText(normalizeText(translatedChunks.join(" ")), currentFormatting);
    renderBlock(transcriptionTranslatedEl, translatedFull, "color:#a7f3d0;font-style:italic;");

    applyDisplayMode();

    if (transcriptionOriginalEl) transcriptionOriginalEl.scrollTop = transcriptionOriginalEl.scrollHeight;
    if (transcriptionTranslatedEl) transcriptionTranslatedEl.scrollTop = transcriptionTranslatedEl.scrollHeight;
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    try {
      if (request.type === "resetSession") {
        resetGlobalState();
        startSilenceMonitor();
        renderText();
        sendResponse({ success: true });
        return true;
      }
      if (request.type === "transcript") {
        handleTranscriptPayload(request.data);
        sendResponse({ success: true });
        return true;
      }
      if (request.type === "translationResult") {
        addTranslatedChunk(request.data);
        sendResponse({ success: true });
        return true;
      }
      if (request.type === "STOP") {
        stopTtsNow();
        resetGlobalState();
        clearSilenceMonitor();
        sendResponse({ success: true });
        window.close();
        return true;
      }
      sendResponse({ success: false });
    } catch (e) {
      sendResponse({ success: false, error: e.message });
    }
    return true;
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    let needsRender = false;
    if ("enableGeminiTranslation" in changes) {
      enableGeminiTranslation = !!changes.enableGeminiTranslation.newValue;
      if (!enableGeminiTranslation) {
        translatedChunks = [];
        translationQueue = [];
        isTranslatingLocal = false;
      }
      needsRender = true;
    }
    if ("displayMode" in changes) { currentDisplayMode = changes.displayMode.newValue || "both"; needsRender = true; }
    if ("textFormatting" in changes) { currentFormatting = changes.textFormatting.newValue || "advanced"; needsRender = true; }
    if (needsRender) renderText();
  });

  window.addEventListener("beforeunload", () => { stopTtsNow(); });

  chrome.storage.local.get(
    ["textFormatting", "displayMode", "fontSize", "dividerPos", "selectedModelSize",
     "selectedLanguage", "selectedTask", "targetLanguage", "useVad", "enableTts",
     "enableGeminiTranslation", "geminiModel"],
    (res) => {
      currentFormatting = res.textFormatting || "advanced";
      currentDisplayMode = res.displayMode || "both";
      enableGeminiTranslation = !!res.enableGeminiTranslation;
      applyFontSize(res.fontSize || 20);

      const pos = parseFloat(res.dividerPos);
      if (Number.isFinite(pos) && pos > 0.1 && pos < 0.9) {
        if (transcriptionOriginalEl) transcriptionOriginalEl.style.flex = `${pos} 1 0%`;
        if (transcriptionTranslatedEl) transcriptionTranslatedEl.style.flex = `${1 - pos} 1 0%`;
      }

      updateStatusBar(res || {});
      applyDisplayMode();
      renderText();
      startSilenceMonitor();
    }
  );
})();