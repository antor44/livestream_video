// Check if this tab was created during browser startup and should be closed
(function detectStartupTab() {
  // If window already marked as startup tab by the executeScript in background.js
  if (window.isStartupTab) {
    console.log("This is a startup tab detected by background script - closing");
    window.close();
    return;
  }
  
  // Secondary check using storage API
  chrome.storage.local.get(["browserJustStarted", "capturingState"], (result) => {
    const isStartupPeriod = result.browserJustStarted === true;
    const wasCapturing = result.capturingState && result.capturingState.isCapturing === true;
    
    // If browser just started and we weren't in the middle of capturing
    if (isStartupPeriod && !wasCapturing) {
      console.log("This is an unwanted startup tab - closing");
      // Add a small delay to ensure this doesn't interfere with normal operation
      setTimeout(() => {
        window.close();
      }, 500);
    }
  });
})();

/**
 * Captures audio from the active tab in Google Chrome.
 * @returns {Promise<MediaStream>} A promise that resolves with the captured audio stream.
 */
function captureTabAudio() {
  return new Promise((resolve) => {
    chrome.tabCapture.capture(
      {
        audio: true,
        video: false,
      },
      (stream) => {
        resolve(stream);
      }
    );
  });
}


/**
 * Sends a message to a specific tab in Google Chrome.
 * @param {number} tabId - The ID of the tab to send the message to.
 * @param {any} data - The data to be sent as the message.
 * @returns {Promise<any>} A promise that resolves with the response from the tab.
 */
function sendMessageToTab(tabId, data) {
  return new Promise((resolve) => {
    try {
      chrome.tabs.sendMessage(tabId, data, (response) => {
        if (chrome.runtime.lastError) {
          // Silently resolve with null if there's an error
          console.log(`Message error in options.js: ${chrome.runtime.lastError.message}`);
          resolve(null);
          return;
        }
        resolve(response);
      });
    } catch (err) {
      console.log("Error sending message from options.js:", err);
      resolve(null);
    }
  });
}


/**
 * Resamples the audio data to a target sample rate of 16kHz.
 * @param {Array|ArrayBuffer|TypedArray} audioData - The input audio data.
 * @param {number} [origSampleRate=44100] - The original sample rate of the audio data.
 * @returns {Float32Array} The resampled audio data at 16kHz.
 */
function resampleTo16kHZ(audioData, origSampleRate = 44100) {
  // Convert the audio data to a Float32Array
  const data = new Float32Array(audioData);

  // Calculate the desired length of the resampled data
  const targetLength = Math.round(data.length * (16000 / origSampleRate));

  // Create a new Float32Array for the resampled data
  const resampledData = new Float32Array(targetLength);

  // Calculate the spring factor and initialize the first and last values
  const springFactor = (data.length - 1) / (targetLength - 1);
  resampledData[0] = data[0];
  resampledData[targetLength - 1] = data[data.length - 1];

  // Resample the audio data
  for (let i = 1; i < targetLength - 1; i++) {
    const index = i * springFactor;
    const leftIndex = Math.floor(index).toFixed();
    const rightIndex = Math.ceil(index).toFixed();
    const fraction = index - leftIndex;
    resampledData[i] = data[leftIndex] + (data[rightIndex] - data[leftIndex]) * fraction;
  }

  // Return the resampled data
  return resampledData;
}

/**
 * Generates a universally unique identifier (UUID).
 *
 * @returns {string} The generated UUID.
 */
function generateUUID() {
  let dt = new Date().getTime();
  const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = (dt + Math.random() * 16) % 16 | 0;
    dt = Math.floor(dt / 16);
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
  return uuid;
}


/**
 * Starts recording audio from the captured tab.
 * @param {Object} option - The options object containing the currentTabId, host, port, language, task, modelSize, and useVad.
 */
async function startRecord(option) {
  const stream = await captureTabAudio();
  const uuid = generateUUID();

  if (stream) {
    // call when the stream inactive
    stream.oninactive = () => {
      cleanupAndClose();
    };
    
    // Declare variables at function scope so they're available to all code in the function
    let isServerReady = false;
    let language = option.language;
    let socket;
    
    // Create WebSocket and store in global variable for cleanup access
    try {
      window.socket = new WebSocket(`ws://${option.host}:${option.port}/`);
      socket = window.socket;
      
      // Handle WebSocket lifecycle errors
      window.socketErrorHandled = false;
      
      socket.onopen = function(e) {
        try { 
          socket.send(
            JSON.stringify({
              uid: uuid,
              language: option.language,
              task: option.task,
              model: option.modelSize,
              use_vad: option.useVad
            })
          );
        } catch (err) {
          console.log("Error sending initial socket message:", err);
        }
      };
      
      // Add error handler
      socket.onerror = function(error) {
        console.log("WebSocket error:", error);
        window.socketErrorHandled = true;
        cleanupAndClose();
      };
      
      // Add close handler
      socket.onclose = function(event) {
        console.log("WebSocket closed:", event.code, event.reason);
        window.socketErrorHandled = true;
        try {
          chrome.runtime.sendMessage({ action: "toggleCaptureButtons" }, () => {
            if (chrome.runtime.lastError) {
              console.log("Error notifying socket close:", chrome.runtime.lastError.message);
            }
          });
        } catch (e) {
          console.log("Error sending socket close message:", e);
        }
      };
    } catch (err) {
      console.log("Error creating WebSocket:", err);
      window.close();
      return;
    }
    
    // WebSocket handlers already defined above

    socket.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      if (data["uid"] !== uuid)
        return;
      
      if (data["status"] === "WAIT"){
        await sendMessageToTab(option.currentTabId, {
          type: "showWaitPopup",
          data: data["message"],
        });
        chrome.runtime.sendMessage({ action: "toggleCaptureButtons", data: false }) 
        chrome.runtime.sendMessage({ action: "stopCapture" })
        return;
      }
        
      if (isServerReady === false){
        isServerReady = true;
        return;
      }

      if (data["message"] === "DISCONNECT"){
        try {
          chrome.runtime.sendMessage({ action: "toggleCaptureButtons", data: false });
        } catch (e) {
          console.error("Error sending message:", e);
        }       
        return;
      }

      try {
        await sendMessageToTab(option.currentTabId, {
          type: "transcript",
          data: event.data,
        });
      } catch (e) {
        console.error("Error sending transcript to tab:", e);
      }
    };

    // Store context and other elements in window for cleanup access
    const context = new AudioContext();
    window.audioContext = context;
    window.audioDataCache = [];
    window.stream = stream;
    
    const mediaStream = context.createMediaStreamSource(stream);
    
    // Note: ScriptProcessorNode is deprecated, but AudioWorkletNode requires more complex setup
    // and isn't fully supported in all browsers. We'll continue using ScriptProcessorNode for now.
    const recorder = context.createScriptProcessor(4096, 1, 1);
    
    // Store for cleanup
    window.mediaStream = mediaStream;
    window.recorder = recorder;

    recorder.onaudioprocess = (event) => {
      // Use a regular function, not async, to avoid promise rejections
      if (!context || !isServerReady) return;
      
      try {
        const inputData = event.inputBuffer.getChannelData(0);
        const audioData16kHz = resampleTo16kHZ(inputData, context.sampleRate);
  
        // Update cache (used for debugging)
        if (window.audioDataCache) {
          window.audioDataCache.push(inputData);
        }
  
        // Only send if socket still exists and is open
        if (socket && socket.readyState === WebSocket.OPEN) {
          try {
            socket.send(audioData16kHz);
          } catch (e) {
            console.log("Error sending audio data:", e);
            // Don't rethrow, just continue
          }
        }
      } catch (e) {
        console.log("Error processing audio:", e);
        // Don't rethrow, just continue
      }
    };

    // Prevent page mute
    mediaStream.connect(recorder);
    recorder.connect(context.destination);
    mediaStream.connect(context.destination);
    
    // Add event listeners for tab/window closing
    window.addEventListener('beforeunload', cleanupAndClose);
    window.addEventListener('unload', cleanupAndClose);
    
  } else {
    window.close();
  }
}

/**
 * Cleans up resources and closes connections before the page unloads
 */
function cleanupAndClose() {
  try {
    // Close WebSocket connection if it exists
    if (window.socket) {
      if (window.socket.readyState === WebSocket.OPEN || 
          window.socket.readyState === WebSocket.CONNECTING) {
        window.socket.close(1000, "Client disconnected");
      }
      window.socket = null;
    }
    
    // Clean up audio resources
    if (window.recorder && window.mediaStream) {
      window.recorder.disconnect();
      window.mediaStream.disconnect();
    }
    
    // Close AudioContext if it's not already closed
    if (window.audioContext && window.audioContext.state !== 'closed') {
      window.audioContext.close();
    }
    
    // Stop the media stream if it exists
    if (window.stream) {
      window.stream.getTracks().forEach(track => track.stop());
    }
    
    // Reset capturing state
    try {
      chrome.runtime.sendMessage({ action: "toggleCaptureButtons" }, (response) => {
        // Just check for errors and ignore them
        if (chrome.runtime.lastError) {
          console.log("Error in cleanup message:", chrome.runtime.lastError.message);
        }
      });
    } catch (e) {
      console.log("Error sending cleanup message:", e);
    }
  } catch (e) {
    console.error("Error during cleanup:", e);
  }
}

/**
 * Listener for incoming messages from the extension's background script.
 * @param {Object} request - The message request object.
 * @param {Object} sender - The sender object containing information about the message sender.  (Unused in this implementation, but kept for completeness)
 * @param {Function} sendResponse - The function to send a response back to the message sender.
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  try {
    const { type, data } = request;
  
    switch (type) {
      case "start_capture":
        startRecord(data);
        break;
      default:
        break;
    }
  
    // Always send a response, even if empty
    try {
      sendResponse({ success: true });
    } catch (e) {
      console.log("Error sending response:", e);
    }
  } catch (e) {
    console.log("Error handling message:", e);
    try {
      sendResponse({ success: false, error: e.message });
    } catch (responseError) {
      console.log("Error sending error response:", responseError);
    }
  }
  
  return true;
});
