let isCaptureStarting = false;
let isStoppingCapture = false;
let isTranslating = false;

let translatedContextWindow = [];
let recentOriginalFragments = [];

const MAX_CONTEXT_SIZE = 2;
const MAX_RECENT_ORIGINALS = 20;
const STARTUP_FLAG_KEY = "browserJustStarted";

function delay(ms = 0) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getStorage(keys) {
  return new Promise((resolve) => {
    chrome.storage.local.get(keys, (result) => resolve(result || {}));
  });
}

function getStorageValue(key) {
  return new Promise((resolve) => {
    chrome.storage.local.get([key], (result) => resolve(result ? result[key] : undefined));
  });
}

function setStorage(obj) {
  return new Promise((resolve) => {
    chrome.storage.local.set(obj, () => resolve());
  });
}

function getTab(tabId) {
  return new Promise((resolve) => {
    if (!tabId) {
      resolve(null);
      return;
    }

    chrome.tabs.get(tabId, (tab) => {
      if (chrome.runtime.lastError) {
        resolve(null);
        return;
      }
      resolve(tab || null);
    });
  });
}

function sendMessageToTab(tabId, message) {
  return new Promise((resolve) => {
    if (!tabId) {
      resolve(null);
      return;
    }

    try {
      chrome.tabs.sendMessage(tabId, message, (response) => {
        if (chrome.runtime.lastError) {
          resolve(null);
          return;
        }
        resolve(response || null);
      });
    } catch (e) {
      resolve(null);
    }
  });
}

function executeScriptInTab(tabId, file) {
  return new Promise((resolve) => {
    if (!tabId) {
      resolve(false);
      return;
    }

    try {
      chrome.scripting.executeScript(
        {
          target: { tabId },
          files: [file]
        },
        () => {
          if (chrome.runtime.lastError) {
            resolve(false);
            return;
          }
          resolve(true);
        }
      );
    } catch (e) {
      resolve(false);
    }
  });
}

function removeChromeTab(tabId) {
  return new Promise((resolve) => {
    if (!tabId) {
      resolve();
      return;
    }

    try {
      chrome.tabs.remove(tabId, () => {
        void chrome.runtime.lastError; 
        resolve();
      });
    } catch (e) {
      resolve();
    }
  });
}

function safeSendRuntimeMessage(message) {
  try {
    chrome.runtime.sendMessage(message, () => {
      void chrome.runtime.lastError;
    });
  } catch (e) {}
}

function normalizeText(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

function splitWords(text) {
  return normalizeText(text).toLowerCase().split(" ").filter(Boolean);
}

function textSimilarity(a, b) {
  const wa = splitWords(a);
  const wb = splitWords(b);

  if (!wa.length || !wb.length) return 0;

  const setA = new Set(wa);
  let matches = 0;
  for (const word of wb) {
    if (setA.has(word)) matches++;
  }

  return matches / Math.max(wa.length, wb.length);
}

function overlapSuffixPrefix(baseText, nextText, maxWords = 40, minWords = 3) {
  const a = splitWords(baseText);
  const b = splitWords(nextText);
  const max = Math.min(maxWords, a.length, b.length);

  for (let size = max; size >= minWords; size--) {
    let ok = true;
    for (let i = 0; i < size; i++) {
      if (a[a.length - size + i] !== b[i]) {
        ok = false;
        break;
      }
    }
    if (ok) return size;
  }

  return 0;
}

function trimTranslatedPrefixOverlap(previousText, newText) {
  const prev = splitWords(previousText);
  const rawNew = normalizeText(newText).split(/\s+/).filter(Boolean);
  const normNew = splitWords(newText);
  const max = Math.min(30, prev.length, normNew.length);

  for (let size = max; size >= 3; size--) {
    let ok = true;
    for (let i = 0; i < size; i++) {
      if (prev[prev.length - size + i] !== normNew[i]) {
        ok = false;
        break;
      }
    }
    if (ok) {
      return rawNew.slice(size).join(" ").trim();
    }
  }

  return normalizeText(newText);
}

function resetTranslationContext() {
  translatedContextWindow = [];
  recentOriginalFragments = [];
  try {
    chrome.tts.stop();
  } catch (e) {}
}


// --- Google Translate via unofficial endpoint (no API key needed) ---
async function translateWithGoogle(text, targetLangCode) {
  const input = normalizeText(text);
  if (input.length < 3) return "";

  try {
    const url = new URL("https://clients5.google.com/translate_a/t");
    url.searchParams.set("client", "dict-chrome-ex");
    url.searchParams.set("sl", "auto");
    url.searchParams.set("tl", targetLangCode);
    url.searchParams.set("q", input);

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 4000);
    try {
      const response = await fetch(url.toString(), { signal: controller.signal });
      if (!response.ok) return "";
      const data = await response.json();
      // Response structure: [["translated", "original"]] or {sentences:[{trans,orig}]}
      let result = "";
      if (Array.isArray(data) && Array.isArray(data[0])) {
        result = data.map(item => (Array.isArray(item) ? item[0] : "")).join("");
      } else if (data?.sentences) {
        result = data.sentences.map(s => s.trans || "").join("");
      }
      return normalizeText(result);
    } finally {
      clearTimeout(timer);
    }
  } catch (e) {
    console.warn("Google Translate fallback failed:", e);
    return "";
  }
}

// --- Build thinking config and generation config based on model name ---
// Mirrors the bash script's per-model thinking logic
function _buildGenerationConfig(model) {
  let thinkingConfig = null;

  if (model.match(/gemini-3(\.\d+)?.*pro/i)) {
    // Gemini 3.x Pro: low thinking for speed
    thinkingConfig = { thinkingLevel: "low" };
  } else if (model.match(/gemini-3(\.\d+)?.*flash.*lite/i)) {
    // Gemini 3.x Flash Lite: minimal thinking
    thinkingConfig = { thinkingLevel: "minimal" };
  } else if (model.match(/gemini-3(\.\d+)?.*flash/i)) {
    // Gemini 3.x Flash: minimal thinking
    thinkingConfig = { thinkingLevel: "minimal" };
  } else if (model.match(/gemini-2\.5.*pro/i)) {
    // Gemini 2.5 Pro: small budget
    thinkingConfig = { thinkingBudget: 128 };
  } else if (model.match(/gemini-2\.5.*flash/i)) {
    // Gemini 2.5 Flash: disable thinking
    thinkingConfig = { thinkingBudget: 0 };
  }

  const generationConfig = { temperature: 0.1, maxOutputTokens: 256 };
  if (thinkingConfig) generationConfig.thinkingConfig = thinkingConfig;
  return generationConfig;
}

// All safety filters disabled — same as bash BLOCK_NONE
const SAFETY_SETTINGS_OFF = [
  { category: "HARM_CATEGORY_HARASSMENT",       threshold: "BLOCK_NONE" },
  { category: "HARM_CATEGORY_HATE_SPEECH",       threshold: "BLOCK_NONE" },
  { category: "HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold: "BLOCK_NONE" },
  { category: "HARM_CATEGORY_DANGEROUS_CONTENT", threshold: "BLOCK_NONE" }
];

// --- Single Gemini API attempt with AbortController timeout ---
async function _geminiAttempt(prompt, model, apiKey, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const isGemma = model.includes("gemma");
    const body = {
      contents: [{ parts: [{ text: prompt }] }],
      safetySettings: SAFETY_SETTINGS_OFF
    };
    if (!isGemma) {
      body.generationConfig = _buildGenerationConfig(model);
    }

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMsg = errorData?.error?.message || response.statusText || "Fetch error";
      throw new Error(`Gemini HTTP ${response.status}: ${errorMsg}`);
    }

    const data = await response.json();
    return normalizeText(data?.candidates?.[0]?.content?.parts?.[0]?.text || "");
  } finally {
    clearTimeout(timer);
  }
}

// --- Build prompt: correction mode when source==target, translation otherwise ---
function _buildPrompt(input, langName, isCorrection) {
  const context = translatedContextWindow.join(" ");
  const contextPart = context ? `\nContext: ${context}` : "";

  if (isCorrection) {
    // Same source and target: fix grammar/broken words, do NOT translate
    return `Fix grammar and broken words in ${langName}. Output ONLY the corrected text.${contextPart}\nText: ${input}`;
  } else {
    return `Translate to ${langName}. Output ONLY the translation.${contextPart}\nText: ${input}`;
  }
}

// sourceLangCode is passed so we can detect correction mode (source == target)
async function translateWithGemini(originalText, targetLangCode, model, apiKey, sourceLangCode) {
  const input = normalizeText(originalText);
  if (!apiKey || input.length < 3) return "";

  let langName = targetLangCode;
  try {
    const displayNames = new Intl.DisplayNames(["en"], { type: "language" });
    langName = displayNames.of(targetLangCode) || targetLangCode;
  } catch (e) {}

  // Correction mode: source and target are the same non-auto language
  const isCorrection = !!(sourceLangCode &&
    sourceLangCode !== "auto" && sourceLangCode !== "" &&
    sourceLangCode === targetLangCode);

  const prompt = _buildPrompt(input, langName, isCorrection);

  // --- Gemini attempt 1 (2.5s timeout) ---
  let translated = "";
  try {
    translated = await _geminiAttempt(prompt, model, apiKey, 2500);
  } catch (e) {
    console.warn("Gemini attempt 1 failed:", e.message);
  }

  // --- Gemini attempt 2 / retry (2.5s timeout) ---
  if (!translated) {
    try {
      translated = await _geminiAttempt(prompt, model, apiKey, 2500);
    } catch (e) {
      console.warn("Gemini attempt 2 failed:", e.message);
    }
  }

  // --- Emergency fallback: Google Translate ---
  // ⁺ = U+207A SUPERSCRIPT PLUS SIGN — silent in every TTS engine
  let usedFallback = false;
  if (!translated) {
    console.warn("Gemini unavailable, trying Google Translate fallback...");
    translated = await translateWithGoogle(input, targetLangCode);
    if (translated) usedFallback = true;
  }

  if (!translated) return "";  // All methods failed, discard silently

  translatedContextWindow.push(translated);
  if (translatedContextWindow.length > MAX_CONTEXT_SIZE) {
    translatedContextWindow.shift();
  }

  return usedFallback ? `\u207A ${translated}` : translated;
}

function speakText(text, lang) {
  const clean = normalizeText(text);
  if (!clean) return;

  chrome.storage.local.get(["ttsSpeed"], (res) => {
    const rate = Number.parseFloat(res?.ttsSpeed || "1.0");
    const options = {
      rate: Number.isFinite(rate) ? rate : 1.0,
      pitch: 1.0,
      volume: 1.0,
      enqueue: true
    };

    // Force language accent if valid
    if (lang && lang.trim() !== "" && lang.trim() !== "AUTO") {
      options.lang = lang;
    }

    try {
      chrome.tts.speak(clean, options);
    } catch (e) {
      console.error("TTS error:", e);
    }
  });
}

function setCapturingState(isCapturing) {
  chrome.storage.local.set({
    capturingState: { isCapturing: !!isCapturing },
    isCapturing: !!isCapturing
  });
  safeSendRuntimeMessage({ action: "toggleCaptureButtons", isCapturing: !!isCapturing });
}

function notifyLanguage(detectedLanguage) {
  safeSendRuntimeMessage({
    action: "updateSelectedLanguage",
    detectedLanguage: detectedLanguage || null
  });
}

function openOptionsTab() {
  return new Promise((resolve) => {
    chrome.tabs.create(
      {
        pinned: true,
        active: false,
        url: `chrome-extension://${chrome.runtime.id}/options.html`
      },
      (tab) => resolve(tab || null)
    );
  });
}

function openStandaloneWindow() {
  return new Promise((resolve) => {
    chrome.windows.create(
      {
        url: chrome.runtime.getURL("standalone.html"),
        type: "popup",
        width: 920,
        height: 360
      },
      (win) => {
        const tabId = win?.tabs?.[0]?.id || null;
        resolve(tabId);
      }
    );
  });
}

async function stopCaptureInternal() {
  if (isStoppingCapture) return;
  isStoppingCapture = true;

  try { chrome.tts.stop(); } catch (e) {}

  try {
    const storageKeys = [
      "optionTabId",
      "currentTabId",
      "standaloneTabId",
      "captureSourceTabId"
    ];
    const storage = await getStorage(storageKeys);

    const idsToStop = Array.from(
      new Set(
        [
          storage.captureSourceTabId,
          storage.currentTabId,
          storage.standaloneTabId,
          storage.optionTabId
        ].filter(Boolean)
      )
    );

    await Promise.all(
      idsToStop.map((id) =>
        sendMessageToTab(id, { type: "STOP" }).catch((err) =>
          console.log(`Stop message failed for tab ${id}:`, err)
        )
      )
    );

    await delay(100);

    const closePromises = [];
    if (storage.standaloneTabId) {
      closePromises.push(removeChromeTab(storage.standaloneTabId).catch(() => {}));
    }
    if (storage.optionTabId) {
      closePromises.push(removeChromeTab(storage.optionTabId).catch(() => {}));
    }
    await Promise.all(closePromises);

    resetTranslationContext();

    await setStorage({
      optionTabId: null,
      currentTabId: null,
      standaloneTabId: null,
      captureSourceTabId: null
    });

    setCapturingState(false);
  } catch (error) {
    console.error("stopCaptureInternal error:", error);
    setCapturingState(false);
  } finally {
    isStoppingCapture = false;
  }
}

function stopCapture() {
  void Promise.resolve().then(() => stopCaptureInternal());
}

async function startCaptureInternal(options) {
  if (isCaptureStarting) return;
  isCaptureStarting = true;

  try {
    const currentState = await getStorageValue("capturingState");
    if (currentState?.isCapturing) {
      await stopCaptureInternal();
      await delay(250);
    }

    const sourceTab = await getTab(options.tabId);
    if (!sourceTab) {
      setCapturingState(false);
      return;
    }

    const oldOptionTabId = await getStorageValue("optionTabId");
    if (oldOptionTabId) {
      await removeChromeTab(oldOptionTabId);
      await setStorage({ optionTabId: null });
    }

    const oldStandaloneTabId = await getStorageValue("standaloneTabId");
    if (oldStandaloneTabId) {
      await removeChromeTab(oldStandaloneTabId);
      await setStorage({ standaloneTabId: null });
    }

    if (!options.useStandalone) {
      const injected = await executeScriptInTab(sourceTab.id, "content.js");
      if (!injected) {
        throw new Error("No se pudo inyectar content.js");
      }

      await delay(120);
      await sendMessageToTab(sourceTab.id, { type: "resetSession" });
      await setStorage({
        currentTabId: sourceTab.id,
        captureSourceTabId: sourceTab.id
      });
    } else {
      await setStorage({
        captureSourceTabId: sourceTab.id
      });
    }

    const optionTab = await openOptionsTab();
    if (!optionTab?.id) {
      throw new Error("No se pudo abrir options.html");
    }

    await setStorage({ optionTabId: optionTab.id });
    await delay(300);

    const {
      selectedLanguage,
      selectedTask,
      selectedModelSize
    } = await getStorage([
      "selectedLanguage",
      "selectedTask",
      "selectedModelSize"
    ]);

    const startMessage = {
      type: "start_capture",
      data: {
        currentTabId: sourceTab.id,
        host: options.host || "localhost",
        port: options.port || "9090",
        multilingual: !!options.useMultilingual,
        language: selectedLanguage || null,
        task: selectedTask || "transcribe",
        modelSize: selectedModelSize || "small",
        useVad: !!options.useVad,
        useStandalone: !!options.useStandalone
      }
    };

    const started = await sendMessageToTab(optionTab.id, startMessage);
    if (!started || started.success === false) {
      throw new Error("No se pudo iniciar la captura en options.js");
    }

    if (options.useStandalone) {
      setCapturingState(true);

      const standaloneTabId = await openStandaloneWindow();
      if (!standaloneTabId) {
        throw new Error("No se pudo abrir la ventana standalone");
      }

      await setStorage({
        standaloneTabId,
        currentTabId: standaloneTabId
      });

      await delay(500);
      await sendMessageToTab(standaloneTabId, { type: "resetSession" });

      await sendMessageToTab(optionTab.id, {
        type: "update_target",
        data: { currentTabId: standaloneTabId }
      });
    } else {
      setCapturingState(true);
    }
  } catch (error) {
    console.error("startCaptureInternal error:", error);
    await stopCaptureInternal();
    setCapturingState(false);
  } finally {
    isCaptureStarting = false;
  }
}

function startCapture(options) {
  void Promise.resolve().then(() => startCaptureInternal(options));
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  try {
    if (message.action === "startCapture") {
      startCapture(message);
      sendResponse({ success: true });
      return false;
    }

    if (message.action === "stopCapture") {
      stopCapture();
      sendResponse({ success: true });
      return false;
    }

    if (message.action === "toggleCaptureButtons") {
      const isCapturing =
        typeof message.isCapturing === "boolean"
          ? message.isCapturing
          : typeof message.data === "boolean"
          ? message.data
          : false;

      setCapturingState(isCapturing);
      sendResponse({ success: true });
      return false;
    }

    if (message.action === "updateSelectedLanguage") {
      const detectedLanguage = message.detectedLanguage || null;
      chrome.storage.local.set({ selectedLanguage: detectedLanguage });
      notifyLanguage(detectedLanguage);
      sendResponse({ success: true });
      return false;
    }

    if (message.action === "resetTranslationContext") {
      resetTranslationContext();
      sendResponse({ success: true });
      return false;
    }

    if (message.action === "stopTts") {
      try { chrome.tts.stop(); } catch (e) {}
      sendResponse({ success: true });
      return false;
    }

    if (message.action === "pageUnloading") {
      sendResponse({ success: true });
      return false;
    }
    
    // Reproducción TTS del texto original (Cuando Gemini está apagado)
    if (message.action === "speakOriginalText") {
      getStorage(["enableTts", "selectedTask", "selectedLanguage"]).then((res) => {
        if (!res.enableTts) {
          sendResponse({ success: true });
          return;
        }
        
        let ttsLang = ""; 
        if (res.selectedTask === "translate") {
          ttsLang = "en"; // Whisper nativo traduce siempre al inglés
        } else if (res.selectedLanguage && res.selectedLanguage !== "AUTO") {
          ttsLang = res.selectedLanguage; 
        }
        
        speakText(message.text, ttsLang);
        sendResponse({ success: true });
      });
      return true;
    }

    if (message.action === "processTranslation") {
      getStorage(["geminiApiKey", "geminiModel", "targetLanguage", "enableTts", "selectedLanguage"])
        .then(async (res) => {
          const targetLang = res.targetLanguage || "es";
          const apiKey = res.geminiApiKey || "";
          const model = res.geminiModel || "gemini-3.1-flash-lite-preview";
          const sourceLang = res.selectedLanguage || "";

          let translated = "";

          if (model === "google-translate") {
            // --- Primary engine: Google Translate (no API key needed) ---
            translated = await translateWithGoogle(message.text, targetLang);
          } else {
            // --- Primary engine: Gemini (with Google Translate as fallback) ---
            if (!apiKey) {
              sendResponse({ success: false, error: "API Key missing" });
              return;
            }
            try {
              translated = await translateWithGemini(message.text, targetLang, model, apiKey, sourceLang);
            } catch (e) {
              console.error("translateWithGemini caught:", e);
              sendResponse({ success: false, error: e.message });
              return;
            }
          }

          if (res.enableTts && translated) {
            // Strip the ⁺ fallback marker before TTS — it's visual only
            const ttsText = translated.replace(/^\u207A\s*/, "");
            speakText(ttsText, targetLang);
          }
          sendResponse({ success: true, data: translated || "" });
        })
        .catch((err) => {
          sendResponse({ success: false, error: err.message });
        });

      return true;
    }


    sendResponse({ success: false, error: "Unknown action" });
    return false;
  } catch (e) {
    console.error("runtime message error:", e);
    sendResponse({ success: false, error: e.message });
    return false;
  }
});

chrome.runtime.onStartup.addListener(() => {
  chrome.storage.local.set({ [STARTUP_FLAG_KEY]: true });
  setTimeout(() => {
    chrome.storage.local.remove(STARTUP_FLAG_KEY);
  }, 10000);
});

chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.local.get(
    ["optionTabId", "currentTabId", "standaloneTabId", "captureSourceTabId", "capturingState"],
    (result) => {
      if (!result?.capturingState?.isCapturing) return;

      const tracked = [
        result.optionTabId,
        result.currentTabId,
        result.standaloneTabId,
        result.captureSourceTabId
      ].filter(Boolean);

      if (tracked.includes(tabId)) {
        try { chrome.tts.stop(); } catch (e) {}
        stopCapture();
      }
    }
  );
});

// Stop capture when the source tab navigates to a new URL (embedded mode only).
// In standalone mode the capture window is separate — URL changes don't affect it.
chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  // Only react to completed navigations (URL change fully done)
  if (changeInfo.status !== "loading" || !changeInfo.url) return;

  chrome.storage.local.get(
    ["captureSourceTabId", "standaloneTabId", "capturingState"],
    (result) => {
      if (!result?.capturingState?.isCapturing) return;

      // If standalone mode is active, the source tab URL change is irrelevant
      if (result.standaloneTabId) return;

      // Embedded mode: if the source tab (where the overlay lives) navigates away, stop
      if (tabId === result.captureSourceTabId) {
        console.log("Embedded mode: source tab navigated, stopping capture.");
        try { chrome.tts.stop(); } catch (e) {}
        stopCapture();
      }
    }
  );
});

self.addEventListener("unhandledrejection", (event) => {
  const message = event?.reason?.message || "";
  if (message.includes("Could not establish connection")) {
    event.preventDefault();
    return true;
  }
});
