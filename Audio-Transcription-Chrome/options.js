(function detectStartupTab() {
  if (window.isStartupTab) {
    window.close();
    return;
  }

  chrome.storage.local.get(["browserJustStarted", "capturingState"], (result) => {
    const isStartupPeriod = result.browserJustStarted === true;
    const wasCapturing =
      result.capturingState && result.capturingState.isCapturing === true;

    if (isStartupPeriod && !wasCapturing) {
      setTimeout(() => {
        window.close();
      }, 500);
    }
  });
})();

let cleanupDone = false;
let isServerReady = false;
let lastForwardedText = "";
let currentUuid = "";
let socketOpenHandled = false;

window.socket = null;
window.stream = null;
window.audioContext = null;
window.mediaStream = null;
window.recorder = null;
window.audioDataCache = [];
window.currentCaptureTargetId = null;
window.socketErrorHandled = false;

function captureTabAudio() {
  return new Promise((resolve) => {
    try {
      chrome.tabCapture.capture(
        {
          audio: true,
          video: false
        },
        (stream) => {
          if (chrome.runtime.lastError) {
            resolve(null);
            return;
          }
          resolve(stream || null);
        }
      );
    } catch (e) {
      resolve(null);
    }
  });
}

function sendMessageToTab(tabId, data) {
  return new Promise((resolve) => {
    if (!tabId) {
      resolve({ ok: false, error: "Missing tab id", response: null });
      return;
    }

    try {
      chrome.tabs.sendMessage(tabId, data, (response) => {
        const err = chrome.runtime.lastError?.message || "";
        if (err) {
          resolve({ ok: false, error: err, response: null });
          return;
        }
        resolve({ ok: true, error: "", response: response ?? null });
      });
    } catch (err) {
      resolve({ ok: false, error: err?.message || String(err), response: null });
    }
  });
}

function getTabSafe(tabId) {
  return new Promise((resolve) => {
    if (!tabId) {
      resolve(null);
      return;
    }

    try {
      chrome.tabs.get(tabId, (tab) => {
        if (chrome.runtime.lastError) {
          resolve(null);
          return;
        }
        resolve(tab || null);
      });
    } catch (e) {
      resolve(null);
    }
  });
}

async function resolveValidTargetId(preferredId, fallbackId = null) {
  const preferred = await getTabSafe(preferredId);
  if (preferred?.id) return preferred.id;

  const fallback = await getTabSafe(fallbackId);
  if (fallback?.id) return fallback.id;

  return null;
}

function normalizeWhitespace(text) {
  // Normalize horizontal whitespace only, preserving newlines
  return String(text || "").replace(/[ \t\r]+/g, " ").trim();
}

function resampleTo16kHZ(audioData, origSampleRate = 44100) {
  const data = new Float32Array(audioData);
  const targetLength = Math.round(data.length * (16000 / origSampleRate));

  if (targetLength <= 1 || data.length <= 1) {
    return new Float32Array(data);
  }

  const resampledData = new Float32Array(targetLength);
  const springFactor = (data.length - 1) / (targetLength - 1);

  resampledData[0] = data[0];
  resampledData[targetLength - 1] = data[data.length - 1];

  for (let i = 1; i < targetLength - 1; i++) {
    const index = i * springFactor;
    const leftIndex = Math.floor(index);
    const rightIndex = Math.ceil(index);
    const fraction = index - leftIndex;
    resampledData[i] =
      data[leftIndex] + (data[rightIndex] - data[leftIndex]) * fraction;
  }

  return resampledData;
}

function generateUUID() {
  let dt = new Date().getTime();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    const r = (dt + Math.random() * 16) % 16 | 0;
    dt = Math.floor(dt / 16);
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

function extractTranscriptText(payload) {
  let data = payload;

  try {
    if (typeof payload === "string") {
      data = JSON.parse(payload);
    }
  } catch (e) {
    return "";
  }

  if (Array.isArray(data?.segments)) {
    return normalizeWhitespace(
      data.segments
        .map((seg) => (typeof seg?.text === "string" ? seg.text : ""))
        .join("\n")
    );
  }

  if (typeof data?.text === "string") {
    return normalizeWhitespace(data.text);
  }

  return "";
}

function safeRuntimeMessage(message) {
  try {
    chrome.runtime.sendMessage(message, () => {
      void chrome.runtime.lastError;
    });
  } catch (e) {}
}

async function notifyStopCapture() {
  safeRuntimeMessage({ action: "toggleCaptureButtons", data: false });
  safeRuntimeMessage({ action: "stopCapture" });
}

function closeSocketQuietly() {
  try {
    if (
      window.socket &&
      (window.socket.readyState === WebSocket.OPEN ||
        window.socket.readyState === WebSocket.CONNECTING)
    ) {
      window.socket.close(1000, "Client disconnected");
    }
  } catch (e) {}

  window.socket = null;
}

function cleanupAudioResources() {
  try {
    if (window.recorder) {
      try {
        window.recorder.disconnect();
      } catch (e) {}
      window.recorder.onaudioprocess = null;
    }
  } catch (e) {}

  try {
    if (window.mediaStream) {
      try {
        window.mediaStream.disconnect();
      } catch (e) {}
    }
  } catch (e) {}

  try {
    if (window.audioContext && window.audioContext.state !== "closed") {
      window.audioContext.close().catch(() => {});
    }
  } catch (e) {}

  try {
    if (window.stream) {
      window.stream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (e) {}
      });
    }
  } catch (e) {}

  window.recorder = null;
  window.mediaStream = null;
  window.audioContext = null;
  window.stream = null;
}

function cleanupAndClose(shouldNotifyBackground = true) {
  if (cleanupDone) return;
  cleanupDone = true;

  closeSocketQuietly();
  cleanupAudioResources();

  isServerReady = false;
  lastForwardedText = "";
  currentUuid = "";

  if (shouldNotifyBackground) {
    notifyStopCapture();
  }
}

async function forwardTranscriptIfNeeded(option, rawPayload) {
  const text = extractTranscriptText(rawPayload);
  if (!text) return;

  if (text === lastForwardedText) return;
  lastForwardedText = text;

  const targetId = await resolveValidTargetId(
    window.currentCaptureTargetId,
    option.currentTabId
  );
  if (!targetId) return;

  window.currentCaptureTargetId = targetId;

  const sent = await sendMessageToTab(targetId, {
    type: "transcript",
    data: rawPayload
  });

  if (!sent?.ok && targetId !== option.currentTabId) {
    const fallbackId = await resolveValidTargetId(option.currentTabId, null);
    if (!fallbackId) return;

    window.currentCaptureTargetId = fallbackId;
    await sendMessageToTab(fallbackId, {
      type: "transcript",
      data: rawPayload
    });
  }
}

async function startRecord(option) {
  cleanupDone = false;
  isServerReady = false;
  lastForwardedText = "";
  currentUuid = generateUUID();
  window.currentCaptureTargetId = option.currentTabId;
  window.socketErrorHandled = false;

  const stream = await captureTabAudio();
  if (!stream) {
    window.close();
    return;
  }

  window.stream = stream;

  stream.oninactive = () => {
    cleanupAndClose(true);
  };

  let socket;

  try {
    socket = new WebSocket(`ws://${option.host}:${option.port}/`);
    window.socket = socket;
  } catch (err) {
    cleanupAndClose(true);
    window.close();
    return;
  }

  socket.onopen = function () {
    socketOpenHandled = true;

    try {
      socket.send(
        JSON.stringify({
          uid: currentUuid,
          language: option.language,
          task: option.task,
          model: option.modelSize,
          use_vad: option.useVad
        })
      );
    } catch (err) {
      cleanupAndClose(true);
    }
  };

  socket.onerror = function () {
    window.socketErrorHandled = true;
    cleanupAndClose(true);
  };

  socket.onclose = function () {
    if (!cleanupDone) {
      window.socketErrorHandled = true;
      cleanupAndClose(true);
    }
  };

  socket.onmessage = async (event) => {
    if (cleanupDone) return;

    let data;
    try {
      data = JSON.parse(event.data);
    } catch (e) {
      return;
    }

    if (data.uid !== currentUuid) return;

    if (data.status === "WAIT") {
      const targetId = await resolveValidTargetId(
        window.currentCaptureTargetId,
        option.currentTabId
      );
      if (targetId) {
        window.currentCaptureTargetId = targetId;
        await sendMessageToTab(targetId, {
          type: "showWaitPopup",
          data: data.message
        });
      }
      notifyStopCapture();
      return;
    }

    if (data.message === "DISCONNECT") {
      notifyStopCapture();
      return;
    }

    const transcriptText = extractTranscriptText(data);

    if (!isServerReady) {
      isServerReady = true;
      if (!transcriptText) return;
    }

    if (!transcriptText) return;

    await forwardTranscriptIfNeeded(option, event.data);
  };

  const context = new AudioContext();
  window.audioContext = context;
  window.audioDataCache = [];

  const mediaStream = context.createMediaStreamSource(stream);
  const recorder = context.createScriptProcessor(4096, 1, 1);

  window.mediaStream = mediaStream;
  window.recorder = recorder;

  recorder.onaudioprocess = (event) => {
    if (cleanupDone || !context || !isServerReady) return;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;

    try {
      const inputData = event.inputBuffer.getChannelData(0);
      const audioData16kHz = resampleTo16kHZ(inputData, context.sampleRate);

      if (window.audioDataCache) {
        window.audioDataCache.push(inputData);
        if (window.audioDataCache.length > 20) {
          window.audioDataCache.shift();
        }
      }

      socket.send(audioData16kHz);
    } catch (e) {}
  };

  mediaStream.connect(recorder);
  recorder.connect(context.destination);
  mediaStream.connect(context.destination);

  window.addEventListener("beforeunload", () => cleanupAndClose(false), {
    once: true
  });
  window.addEventListener("unload", () => cleanupAndClose(false), {
    once: true
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  try {
    if (request?.action) {
      return false;
    }

    const { type, data } = request || {};
    if (!type) {
      return false;
    }

    switch (type) {
      case "start_capture":
        startRecord(data);
        sendResponse({ success: true });
        return true;

      case "update_target":
        if (data && data.currentTabId) {
          window.currentCaptureTargetId = data.currentTabId;
        }
        sendResponse({ success: true });
        return true;

      case "STOP":
        cleanupAndClose(false);
        window.close();
        sendResponse({ success: true });
        return true;

      default:
        return false;
    }
  } catch (e) {
    try {
      sendResponse({ success: false, error: e.message });
    } catch (responseError) {}
    return true;
  }
});
