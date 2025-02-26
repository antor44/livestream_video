/**
 * Removes a tab with the specified tab ID in Google Chrome.
 * @param {number} tabId - The ID of the tab to be removed.
 * @returns {Promise<void>} A promise that resolves when the tab is successfully removed or fails to remove.
 */
function removeChromeTab(tabId) {
  return new Promise((resolve) => {
    chrome.tabs.remove(tabId)
      .then(resolve)
      .catch(resolve);
  });
}


/**
 * Executes a script file in a specific tab in Google Chrome.
 * @param {number} tabId - The ID of the tab where the script should be executed.
 * @param {string} file - The file path or URL of the script to be executed.
 * @returns {Promise<void>} A promise that resolves when the script is successfully executed or fails to execute.
 */
function executeScriptInTab(tabId, file) {
  return new Promise((resolve) => {
    chrome.scripting.executeScript(
      {
        target: { tabId },
        files: [file],
      }, () => {
        resolve();
      }
    );
  });
}


/**
 * Opens the options page of the Chrome extension in a new pinned tab.
 * @returns {Promise<chrome.tabs.Tab>} A promise that resolves with the created tab object.
 */
function openExtensionOptions() {
  return new Promise((resolve) => {
    chrome.tabs.create(
      {
        pinned: true,
        active: false,
        url: `chrome-extension://${chrome.runtime.id}/options.html`,
        // Removed ephemeral parameter as it was causing issues with WebSocket connections
      },
      (tab) => {
        resolve(tab);
      }
    );
  });
}


/**
 * Retrieves the value associated with the specified key from the local storage in Google Chrome.
 * @param {string} key - The key of the value to retrieve from the local storage.
 * @returns {Promise<any>} A promise that resolves with the retrieved value from the local storage.
 */
function getLocalStorageValue(key) {
  return new Promise((resolve) => {
    chrome.storage.local.get([key], (result) => {
      resolve(result[key]);
    });
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
    if (!tabId) {
      resolve(null);
      return;
    }
    
    // First check if the tab exists
    chrome.tabs.get(tabId, (tab) => {
      if (chrome.runtime.lastError) {
        // Tab doesn't exist - silently resolve
        resolve(null);
        return;
      }
      
      // Tab exists, try to send message
      try {
        chrome.tabs.sendMessage(tabId, data, (response) => {
          if (chrome.runtime.lastError) {
            // Silently resolve with null, as the tab might have navigated 
            // or been closed between our check and message send
            resolve(null);
            return;
          }
          resolve(response);
        });
      } catch (err) {
        // Silently resolve with null
        resolve(null);
      }
    });
  });
}


/**
 * Delays the execution for a specified duration.
 * @param {number} ms - The duration to sleep in milliseconds (default: 0).
 * @returns {Promise<void>} A promise that resolves after the specified duration.
 */
function delayExecution(ms = 0) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


/**
 * Sets a value associated with the specified key in the local storage of Google Chrome.
 * @param {string} key - The key to set in the local storage.
 * @param {any} value - The value to associate with the key in the local storage.
 * @returns {Promise<any>} A promise that resolves with the value that was set in the local storage.
 */
function setLocalStorageValue(key, value) {
  return new Promise((resolve) => {
    chrome.storage.local.set(
      {
        [key]: value,
      }, () => {
        resolve(value);
      }
    );
  });
}


/**
 * Retrieves the tab object with the specified tabId.
 * @param {number} tabId - The ID of the tab to retrieve.
 * @returns {Promise<object|null>} - A Promise that resolves to the tab object or null if tab doesn't exist.
 */
async function getTab(tabId) {
  return new Promise((resolve) => {
    chrome.tabs.get(tabId, (tab) => {
      if (chrome.runtime.lastError) {
        resolve(null);
      } else {
        resolve(tab);
      }
    });
  });
}


/**
 * Starts the capture process for the specified tab.
 * @param {number} tabId - The ID of the tab to start capturing.
 * @returns {Promise<void>} - A Promise that resolves when the capture process is started successfully.
 */
function startCapture(options) {
  // Use a non-async function to avoid unhandled promise rejections
  const { tabId } = options;
  
  // Create a wrapper function to handle all the async operations with proper error handling
  const doStartCapture = async () => {
    try {
      // Close any existing option tab
      const optionTabId = await getLocalStorageValue("optionTabId");
      if (optionTabId) {
        await removeChromeTab(optionTabId);
      }
  
      // Get the current tab
      const currentTab = await getTab(tabId);
      if (!currentTab) {
        return;
      }
      
      if (currentTab.audible) {
        // Inject content script
        await setLocalStorageValue("currentTabId", currentTab.id);
        await executeScriptInTab(currentTab.id, "content.js");
        await delayExecution(300);
  
        // Open the options page
        const optionTab = await openExtensionOptions();
        await setLocalStorageValue("optionTabId", optionTab.id);
        await delayExecution(300);
  
        // Send message to start capture
        await sendMessageToTab(optionTab.id, {
          type: "start_capture",
          data: { 
            currentTabId: currentTab.id, 
            host: options.host, 
            port: options.port, 
            multilingual: options.useMultilingual,
            language: options.language,
            task: options.task,
            modelSize: options.modelSize,
            useVad: options.useVad,
          },
        });
      } else {
        console.log("No Audio");
        try {
          chrome.runtime.sendMessage({ action: "toggleCaptureButtons" });
        } catch (e) {
          // Ignore error if popup is closed
        }
      }
    } catch (error) {
      console.log("Error in startCapture:", error);
      // Try to send message but don't throw if it fails
      try {
        chrome.runtime.sendMessage({ action: "toggleCaptureButtons" });
      } catch (e) {
        // Ignore error if popup is closed
      }
    }
  };
  
  // Execute the async function with explicit error catching to prevent unhandled rejections
  void Promise.resolve().then(() => doStartCapture()).catch(err => {
    console.log("Start capture error (suppressed):", err);
  });
}


/**
 * Stops the capture process and performs cleanup.
 * @returns {void}
 */
function stopCapture() {
  // Use a non-async function to avoid unhandled promise rejections
  
  // Create a wrapper function to handle all the async operations with proper error handling
  const doStopCapture = async () => {
    try {
      const optionTabId = await getLocalStorageValue("optionTabId");
      const currentTabId = await getLocalStorageValue("currentTabId");
  
      if (optionTabId) {
        if (currentTabId) {
          // Try to stop the content script - don't wait for response
          try {
            await sendMessageToTab(currentTabId, {
              type: "STOP",
              data: { currentTabId: currentTabId },
            });
          } catch (e) {
            // Tab might be closed already, which is fine
          }
        }
        
        // Always attempt to close the option tab
        try {
          await removeChromeTab(optionTabId);
        } catch (e) {
          // Tab might be closed already, which is fine
        }
      }
    } catch (error) {
      // Log error but don't throw - just cleanup as best we can
      console.log("Error in stopCapture:", error);
    }
  };
  
  // Execute the async function with explicit error catching to prevent unhandled rejections
  void Promise.resolve().then(() => doStopCapture()).catch(err => {
    console.log("Stop capture error (suppressed):", err);
  });
}


// =============================================================================
// Turn on verbose error listening globally
// =============================================================================

// Add a global unhandledrejection handler to catch ONLY connection errors
self.addEventListener('unhandledrejection', function(event) {
  // Only suppress "Could not establish connection" errors
  if (event && event.reason && event.reason.message && 
      event.reason.message.includes("Could not establish connection")) {
    console.log('Suppressing connection error:', event.reason.message);
    event.preventDefault();
    return true;
  }
  // Let all other errors pass through to the console
});

/**
 * A super-safe wrapper for chrome.runtime.sendMessage that handles all possible errors
 */
function safeSendMessage(message, callback) {
  setTimeout(() => {
    try {
      chrome.runtime.sendMessage(message, (response) => {
        // Always check for lastError to prevent unchecked runtime.lastError warnings
        if (chrome.runtime.lastError) {
          // Just log and suppress - expected when receiving end doesn't exist
          console.log("Message error handled:", chrome.runtime.lastError.message);
          // Still call the callback with null to indicate failure
          if (callback) callback(null);
          return;
        }
        
        // Call the callback with the response if there was no error
        if (callback) callback(response);
      });
    } catch (err) {
      // Catch any synchronous errors (should be rare)
      console.log("Synchronous send error:", err);
      if (callback) callback(null);
    }
  }, 0); // Use setTimeout to ensure this runs asynchronously
}

/**
 * Listens for messages from the runtime and performs corresponding actions.
 * @param {Object} message - The message received from the runtime.
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Safely handle the message
  const handleMessage = () => {
    try {
      if (message.action === "startCapture") {
        startCapture(message);
        return { success: true };
      } 
      else if (message.action === "stopCapture") {
        stopCapture();
        return { success: true };
      } 
      else if (message.action === "updateSelectedLanguage") {
        const detectedLanguage = message.detectedLanguage;
        safeSendMessage({ action: "updateSelectedLanguage", detectedLanguage });
        chrome.storage.local.set({ selectedLanguage: detectedLanguage });
        return { success: true };
      } 
      else if (message.action === "toggleCaptureButtons") {
        safeSendMessage({ action: "toggleCaptureButtons" });
        chrome.storage.local.set({ capturingState: { isCapturing: false } });
        stopCapture();
        return { success: true };
      }
      else if (message.action === "pageUnloading") {
        // Handle the combined message from page unload event
        if (message.toggleButtons) {
          safeSendMessage({ action: "toggleCaptureButtons" });
          chrome.storage.local.set({ capturingState: { isCapturing: false } });
        }
        if (message.stopCapture) {
          stopCapture();
        }
        return { success: true };
      }
      return { success: false, error: "Unknown action" };
    } catch (e) {
      console.log("Error handling message:", e);
      return { success: false, error: e.message };
    }
  };
  
  // Execute immediately for synchronous response
  try {
    const response = handleMessage();
    sendResponse(response);
  } catch (err) {
    console.log("Message handler error (suppressed):", err);
    sendResponse({ success: false, error: "Internal error" });
  }
  
  // Return false to indicate we've already sent the response
  return false;
});

/**
 * Handle Chrome startup/install to clean up any orphaned tabs from previous sessions
 * Also handle browser shutdown to clean up resources
 */

// Define a key to mark browser startup state
const BROWSER_JUST_STARTED_KEY = "browserJustStarted";

// Handle browser shutdown - only log the event but preserve state
chrome.runtime.onSuspend.addListener(() => {
  console.log("Browser suspending - preserving extension state for possible restart");
  // We no longer reset the state here to allow proper session restoration
});

// Track tabs created during the startup period
chrome.tabs.onCreated.addListener((tab) => {
  chrome.storage.local.get([BROWSER_JUST_STARTED_KEY, "capturingState"], (result) => {
    // Check if this is during browser startup and wasn't an active capture
    if (result[BROWSER_JUST_STARTED_KEY] && 
        (!result.capturingState || !result.capturingState.isCapturing)) {
      
      // If this is our options page, mark it for closing
      if (tab.url && tab.url.includes('chrome-extension://') && 
          tab.url.includes('/options.html')) {
        console.log("New options tab detected during startup - marking for removal");
        
        // Wait a moment for the tab to initialize
        setTimeout(() => {
          try {
            chrome.tabs.executeScript(tab.id, {
              code: 'window.isStartupTab = true;'
            }).catch(() => {
              // If we can't execute the script, just try to close it directly
              chrome.tabs.remove(tab.id).catch(() => {});
            });
          } catch (e) {
            // If anything fails, try direct removal
            chrome.tabs.remove(tab.id).catch(() => {});
          }
        }, 200);
      }
    }
  });
});
chrome.runtime.onStartup.addListener(() => {
  console.log("Browser starting up - setting startup flag");
  
  // Set a flag indicating browser just started
  chrome.storage.local.set({ [BROWSER_JUST_STARTED_KEY]: true });
  
  // Remove the flag after 10 seconds
  setTimeout(() => {
    chrome.storage.local.remove(BROWSER_JUST_STARTED_KEY);
    console.log("Browser startup period ended - cleared startup flag");
  }, 10000);

  // Also track any tabs created during this startup period
  chrome.tabs.query({
    url: `chrome-extension://${chrome.runtime.id}/options.html`
  }, (tabs) => {
    // Mark these tabs as startup tabs
    if (tabs && tabs.length > 0) {
      console.log(`Found ${tabs.length} options tabs during startup`);
      tabs.forEach(tab => {
        // Set a tab-specific flag to identify it as a startup tab
        chrome.tabs.executeScript(tab.id, {
          code: 'window.isStartupTab = true;'
        }).catch(() => {
          // Ignore errors - tab might not be ready yet
        });
      });
    }
  });
});

/**
 * Listen for tab close events to properly clean up resources.
 * This ensures that when a user closes the tab being captured or the options tab,
 * all resources are properly cleaned up.
 */
chrome.tabs.onRemoved.addListener((tabId) => {
  // Use callback-based approach to avoid promise rejections entirely
  
  chrome.storage.local.get(["currentTabId", "optionTabId"], (result) => {
    const currentTabId = result.currentTabId;
    const optionTabId = result.optionTabId;
    
    // If the closed tab is either the captured tab or the options tab
    if (tabId === currentTabId || tabId === optionTabId) {
      // Reset the capturing state
      chrome.storage.local.set({ capturingState: { isCapturing: false } });
      
      // Try to notify the popup - but don't wait for response or handle errors
      safeSendMessage({ action: "toggleCaptureButtons" });
      
      // If the options tab was closed but not by our stopCapture function
      if (tabId === optionTabId && currentTabId) {
        // Safely check if the tab exists first
        chrome.tabs.get(currentTabId, (tab) => {
          // Ignore lastError - if the tab doesn't exist, that's fine
          if (!chrome.runtime.lastError) {
            // Tab exists, try to send STOP message
            try {
              chrome.tabs.sendMessage(currentTabId, {
                type: "STOP",
                data: { currentTabId: currentTabId }
              }, (response) => {
                // Must check for lastError to prevent unchecked runtime.lastError
                if (chrome.runtime.lastError) {
                  console.log("Tab message error handled:", chrome.runtime.lastError.message);
                  return;
                }
              });
            } catch (err) {
              console.log("Tab message error caught:", err);
            }
          }
        });
      }
      
      // Clean up tab IDs in storage
      const updates = {};
      if (tabId === currentTabId) {
        updates.currentTabId = null;
      }
      if (tabId === optionTabId) {
        updates.optionTabId = null;
      }
      
      if (Object.keys(updates).length > 0) {
        chrome.storage.local.set(updates);
      }
    }
  });
});

