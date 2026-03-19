const DEFAULTS = {
  serverHost: "localhost",
  serverPort: "9090",
  selectedLanguage: "",
  selectedTask: "transcribe",
  selectedModelSize: "small",
  textFormatting: "advanced",
  transcriptionProfile: "balanced",
  hideLiveText: false,
  geminiApiKey: "",
  geminiModel: "gemini-3.1-flash-lite-preview",
  targetLanguage: "es",
  displayMode: "both",
  useVad: true,
  useStandalone: false,
  enableTts: false,
  ttsSpeed: "1.2",
  enableGeminiTranslation: false
};

const el = {};

let fullApiKey = "";

function $(id) {
  return document.getElementById(id);
}

function maskApiKey(key) {
  if (!key) return "";
  if (key.length <= 6) return "•".repeat(key.length);
  return key.slice(0, 3) + "•".repeat(Math.min(key.length - 6, 24)) + key.slice(-3);
}

function initElements() {
  el.startButton = $("startCapture");
  el.stopButton = $("stopCapture");
  el.ttsSpeed = $("ttsSpeed");
  el.ttsSpeedValue = $("ttsSpeedValue");
  el.enableTtsCheckbox = $("enableTtsCheckbox");
  el.useStandaloneCheckbox = $("useStandaloneCheckbox");
  el.useVadCheckbox = $("useVadCheckbox");
  el.ipAddress = $("ipAddress");
  el.port = $("port");
  el.defaultIpButton = $("defaultIpButton");
  el.languageDropdown = $("languageDropdown");
  el.taskDropdown = $("taskDropdown");
  el.modelSizeDropdown = $("modelSizeDropdown");
  el.textFormattingDropdown = $("textFormattingDropdown");
  el.transcriptionProfileDropdown = $("transcriptionProfileDropdown");
  el.hideLiveTextCheckbox = $("hideLiveTextCheckbox");
  el.geminiApiKey = $("geminiApiKey");
  el.enableGeminiTranslationCheckbox = $("enableGeminiTranslationCheckbox");
  el.geminiModelDropdown = $("geminiModelDropdown");
  el.geminiApiKeyRow = $("geminiApiKeyRow");
  el.targetLanguageDropdown = $("targetLanguageDropdown");
  el.displayModeDropdown = $("displayModeDropdown");
  el.connectionStatus = $("connectionStatus");
}

function normalizeHost(value) {
  const clean = String(value || "").trim();
  return clean || DEFAULTS.serverHost;
}

function normalizePort(value) {
  const clean = String(value || "").replace(/[^\d]/g, "");
  return clean || DEFAULTS.serverPort;
}

function normalizeSpeed(value) {
  const n = Number.parseFloat(value);
  if (!Number.isFinite(n)) return DEFAULTS.ttsSpeed;
  return Math.min(2.0, Math.max(0.5, n)).toFixed(1);
}

function setStatus(text) {
  if (!el.connectionStatus) return;
  el.connectionStatus.textContent = text;
}

function setButtonsFromState(isCapturing) {
  if (el.startButton) el.startButton.disabled = !!isCapturing;
  if (el.stopButton) el.stopButton.disabled = !isCapturing;
  setStatus(isCapturing ? "Capturing..." : "Idle");
}

function updateApiKeyVisibility() {
  if (!el.geminiApiKeyRow || !el.geminiModelDropdown) return;
  const isGoogleTranslate = el.geminiModelDropdown.value === "google-translate";
  el.geminiApiKeyRow.style.display = isGoogleTranslate ? "none" : "";
}

function updateTtsSpeedLabel() {
  if (!el.ttsSpeed) return;
  const speed = normalizeSpeed(el.ttsSpeed.value);
  el.ttsSpeed.value = speed;
  if (el.ttsSpeedValue) {
    el.ttsSpeedValue.textContent = `${speed}x`;
  }
}

function collectSettings() {
  return {
    serverHost: normalizeHost(el.ipAddress?.value),
    serverPort: normalizePort(el.port?.value),
    selectedLanguage: el.languageDropdown?.value || "",
    selectedTask: el.taskDropdown?.value || DEFAULTS.selectedTask,
    selectedModelSize: el.modelSizeDropdown?.value || DEFAULTS.selectedModelSize,
    textFormatting: el.textFormattingDropdown?.value || DEFAULTS.textFormatting,
    transcriptionProfile: el.transcriptionProfileDropdown?.value || DEFAULTS.transcriptionProfile,
    hideLiveText: !!el.hideLiveTextCheckbox?.checked,
    geminiApiKey: fullApiKey,
    geminiModel: el.geminiModelDropdown?.value || DEFAULTS.geminiModel,
    targetLanguage: el.targetLanguageDropdown?.value || DEFAULTS.targetLanguage,
    displayMode: el.displayModeDropdown?.value || DEFAULTS.displayMode,
    useVad: !!el.useVadCheckbox?.checked,
    useStandalone: !!el.useStandaloneCheckbox?.checked,
    enableTts: !!el.enableTtsCheckbox?.checked,
    ttsSpeed: normalizeSpeed(el.ttsSpeed?.value),
    enableGeminiTranslation: !!el.enableGeminiTranslationCheckbox?.checked
  };
}

async function saveSettings() {
  const settings = collectSettings();

  await chrome.storage.local.set({
    serverHost: settings.serverHost,
    serverPort: settings.serverPort,
    ipAddress: settings.serverHost,
    port: settings.serverPort,
    selectedLanguage: settings.selectedLanguage || null,
    selectedTask: settings.selectedTask,
    selectedModelSize: settings.selectedModelSize,
    textFormatting: settings.textFormatting,
    transcriptionProfile: settings.transcriptionProfile,
    hideLiveText: settings.hideLiveText,
    geminiApiKey: settings.geminiApiKey,
    geminiModel: settings.geminiModel,
    targetLanguage: settings.targetLanguage,
    displayMode: settings.displayMode,
    useVad: settings.useVad,
    useStandalone: settings.useStandalone,
    enableTts: settings.enableTts,
    ttsSpeed: settings.ttsSpeed,
    enableGeminiTranslation: settings.enableGeminiTranslation
  });

  return settings;
}

function applySettingsToUI(settings) {
  if (el.ipAddress) el.ipAddress.value = settings.serverHost ?? DEFAULTS.serverHost;
  if (el.port) el.port.value = settings.serverPort ?? DEFAULTS.serverPort;
  if (el.languageDropdown) el.languageDropdown.value = settings.selectedLanguage ?? "";
  if (el.taskDropdown) el.taskDropdown.value = settings.selectedTask ?? DEFAULTS.selectedTask;
  if (el.modelSizeDropdown) el.modelSizeDropdown.value = settings.selectedModelSize ?? DEFAULTS.selectedModelSize;
  if (el.textFormattingDropdown) el.textFormattingDropdown.value = settings.textFormatting ?? DEFAULTS.textFormatting;
  if (el.transcriptionProfileDropdown) el.transcriptionProfileDropdown.value = settings.transcriptionProfile ?? DEFAULTS.transcriptionProfile;
  if (el.hideLiveTextCheckbox) el.hideLiveTextCheckbox.checked = settings.hideLiveText ?? DEFAULTS.hideLiveText;

  fullApiKey = String(settings.geminiApiKey ?? DEFAULTS.geminiApiKey);
  if (el.geminiApiKey) el.geminiApiKey.value = maskApiKey(fullApiKey);

  if (el.geminiModelDropdown) el.geminiModelDropdown.value = settings.geminiModel ?? DEFAULTS.geminiModel;
  if (el.targetLanguageDropdown) el.targetLanguageDropdown.value = settings.targetLanguage ?? DEFAULTS.targetLanguage;
  if (el.displayModeDropdown) el.displayModeDropdown.value = settings.displayMode ?? DEFAULTS.displayMode;
  if (el.useVadCheckbox) el.useVadCheckbox.checked = settings.useVad ?? DEFAULTS.useVad;
  if (el.useStandaloneCheckbox) el.useStandaloneCheckbox.checked = settings.useStandalone ?? DEFAULTS.useStandalone;
  if (el.enableTtsCheckbox) el.enableTtsCheckbox.checked = settings.enableTts ?? DEFAULTS.enableTts;
  if (el.ttsSpeed) el.ttsSpeed.value = normalizeSpeed(settings.ttsSpeed ?? DEFAULTS.ttsSpeed);
  if (el.enableGeminiTranslationCheckbox) {
    el.enableGeminiTranslationCheckbox.checked = settings.enableGeminiTranslation ?? DEFAULTS.enableGeminiTranslation;
  }
  updateTtsSpeedLabel();
  updateApiKeyVisibility();
}

async function loadSettings() {
  const stored = await chrome.storage.local.get(null);

  const settings = {
    ...DEFAULTS,
    ...stored,
    serverHost: stored.serverHost || stored.ipAddress || DEFAULTS.serverHost,
    serverPort: stored.serverPort || stored.port || DEFAULTS.serverPort,
    selectedLanguage:
      stored.selectedLanguage === undefined || stored.selectedLanguage === null
        ? ""
        : stored.selectedLanguage
  };

  applySettingsToUI(settings);

  const isCapturing =
    !!stored?.capturingState?.isCapturing || !!stored?.isCapturing;

  setButtonsFromState(isCapturing);
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs && tabs.length ? tabs[0] : null;
}

async function startCapture() {
  const settings = await saveSettings();
  const activeTab = await getActiveTab();

  if (!activeTab?.id) {
    setButtonsFromState(false);
    setStatus("No active tab");
    return;
  }

  setStatus("Starting...");

  chrome.runtime.sendMessage(
    {
      action: "startCapture",
      tabId: activeTab.id,
      host: settings.serverHost,
      port: settings.serverPort,
      useMultilingual: !settings.selectedLanguage,
      useVad: settings.useVad,
      useStandalone: settings.useStandalone
    },
    (response) => {
      if (chrome.runtime.lastError || !response?.success) {
        setButtonsFromState(false);
        setStatus("Start failed");
        return;
      }
    }
  );
}

function stopCapture() {
  setStatus("Stopping...");

  chrome.runtime.sendMessage({ action: "stopCapture" }, (response) => {
    if (chrome.runtime.lastError || !response?.success) {
      setStatus("Stop failed");
      return;
    }
  });
}

async function resetDefaults() {
  // Only reset IP and port to defaults, leave all other settings untouched
  await chrome.storage.local.set({
    serverHost: DEFAULTS.serverHost,
    serverPort: DEFAULTS.serverPort,
    ipAddress: DEFAULTS.serverHost,
    port: DEFAULTS.serverPort
  });

  if (el.ipAddress) el.ipAddress.value = DEFAULTS.serverHost;
  if (el.port) el.port.value = DEFAULTS.serverPort;
}

function bindAutosave() {
  const controls = [
    el.enableTtsCheckbox,
    el.enableGeminiTranslationCheckbox,
    el.useStandaloneCheckbox,
    el.useVadCheckbox,
    el.hideLiveTextCheckbox,
    el.ipAddress,
    el.port,
    el.languageDropdown,
    el.taskDropdown,
    el.modelSizeDropdown,
    el.textFormattingDropdown,
    el.transcriptionProfileDropdown,
    el.geminiModelDropdown,
    el.targetLanguageDropdown,
    el.displayModeDropdown
  ].filter(Boolean);

  for (const control of controls) {
    const eventName =
      control.tagName === "INPUT" &&
      (control.type === "text" || control.type === "number")
        ? "input"
        : "change";

    control.addEventListener(eventName, async () => {
      await saveSettings();
    });

    if (eventName !== "change") {
      control.addEventListener("change", async () => {
        await saveSettings();
      });
    }
  }

  if (el.ttsSpeed) {
    el.ttsSpeed.addEventListener("input", async () => {
      updateTtsSpeedLabel();
      await saveSettings();
    });

    el.ttsSpeed.addEventListener("change", async () => {
      updateTtsSpeedLabel();
      await saveSettings();
    });
  }

  if (el.geminiApiKey) {
    el.geminiApiKey.addEventListener("focus", () => {
      el.geminiApiKey.value = fullApiKey;
    });

    el.geminiApiKey.addEventListener("input", () => {
      fullApiKey = el.geminiApiKey.value;
    });

    el.geminiApiKey.addEventListener("blur", async () => {
      fullApiKey = String(el.geminiApiKey.value || "").trim();
      el.geminiApiKey.value = maskApiKey(fullApiKey);
      await saveSettings();
    });
  }

  if (el.languageDropdown) {
    el.languageDropdown.addEventListener("change", () => {
      chrome.runtime.sendMessage(
        {
          action: "updateSelectedLanguage",
          detectedLanguage: el.languageDropdown.value || null
        },
        () => {
          void chrome.runtime.lastError;
        }
      );
    });
  }

  if (el.geminiModelDropdown) {
    el.geminiModelDropdown.addEventListener("change", () => {
      updateApiKeyVisibility();
    });
  }
}


function bindButtons() {
  if (el.startButton) {
    el.startButton.addEventListener("click", startCapture);
  }

  if (el.stopButton) {
    el.stopButton.addEventListener("click", stopCapture);
  }

  if (el.defaultIpButton) {
    el.defaultIpButton.addEventListener("click", resetDefaults);
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  try {
    // THIS IS THE MAIN FIX
    // The popup ONLY processes messages intended for it.
    // It completely ignores "processTranslation" so that it is handled by background.js
    if (message.action === "toggleCaptureButtons") {
      const isCapturing = typeof message.isCapturing === "boolean" ? message.isCapturing : false;
      setButtonsFromState(isCapturing);
      sendResponse({ success: true });
      return false;
    }

    if (message.action === "updateSelectedLanguage" && el.languageDropdown) {
      el.languageDropdown.value = message.detectedLanguage || "";
      sendResponse({ success: true });
      return false;
    }

    // Ignore everything else
    return false;
  } catch (e) {
    return false;
  }
});

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "local") return;

  if (changes.capturingState || changes.isCapturing) {
    chrome.storage.local.get(["capturingState", "isCapturing"], (res) => {
      const isCapturing =
        !!res?.capturingState?.isCapturing || !!res?.isCapturing;
      setButtonsFromState(isCapturing);
    });
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  initElements();

  const versionEl = document.getElementById("extensionVersion");
  if (versionEl) {
    const v = chrome.runtime.getManifest?.()?.version || "";
    if (v) versionEl.textContent = `v. ${v}`;
  }

  await loadSettings();
  bindAutosave();
  bindButtons();
  updateTtsSpeedLabel();
});
