// Wait for the DOM content to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
  const startButton = document.getElementById("startCapture");
  const stopButton = document.getElementById("stopCapture");

  const useVadCheckbox = document.getElementById("useVadCheckbox");
  const languageDropdown = document.getElementById('languageDropdown');
  const taskDropdown = document.getElementById('taskDropdown');
  const modelSizeDropdown = document.getElementById('modelSizeDropdown');
  const ipAddressInput = document.getElementById('ipAddress');
  const portInput = document.getElementById('port');
  const textFormattingDropdown = document.getElementById("textFormattingDropdown");
  const defaultIpButton = document.getElementById('defaultIpButton');
  const defaultPortButton = document.getElementById('defaultPortButton');

  
  let selectedLanguage = null;
  let selectedTask = taskDropdown.value;
  let selectedModelSize = modelSizeDropdown.value;
  let ipAddress = ipAddressInput.value;
  let port = portInput.value;

  // Add click event listeners to the buttons
  startButton.addEventListener("click", startCapture);
  stopButton.addEventListener("click", stopCapture);
  defaultIpButton.addEventListener("click", setDefaultIp);
  defaultPortButton.addEventListener("click", setDefaultPort);

  // Retrieve capturing state from storage on popup open
  chrome.storage.local.get("capturingState", ({ capturingState }) => {
    if (capturingState && capturingState.isCapturing) {
      toggleCaptureButtons(true);
    } else {
      toggleCaptureButtons(false);
    }
  });

  // Retrieve checkbox state from storage on popup open
  chrome.storage.local.get("useVadState", ({ useVadState }) => {
    if (useVadState !== undefined) {
      useVadCheckbox.checked = useVadState;
    }
  });

  // Retrieve selected language from storage on popup open, or default to ""
  chrome.storage.local.get("selectedLanguage", ({ selectedLanguage: storedLanguage }) => {
    if (storedLanguage !== undefined && storedLanguage !== null) {
      languageDropdown.value = storedLanguage;
      selectedLanguage = storedLanguage;
    } else {
      languageDropdown.value = ""; // Set to empty string for "Automatically detect"
    }      
  });

  // Retrieve IP address from storage on popup open
  chrome.storage.local.get("ipAddress", ({ ipAddress: storedIpAddress }) => {
    if (storedIpAddress !== undefined) {
      ipAddressInput.value = storedIpAddress;
      ipAddress = storedIpAddress;
    }
  });

  // Retrieve port from storage on popup open
  chrome.storage.local.get("port", ({ port: storedPort }) => {
    if (storedPort !== undefined) {
      portInput.value = storedPort;
      port = storedPort;
    }
  });

  // Retrieve selected task from storage on popup open
  chrome.storage.local.get("selectedTask", ({ selectedTask: storedTask }) => {
    if (storedTask !== undefined) {
      taskDropdown.value = storedTask;
      selectedTask = storedTask;
    }
  });

    // Retrieve selected model size from storage on popup open
  chrome.storage.local.get("selectedModelSize", ({ selectedModelSize: storedModelSize }) => {
    if (storedModelSize !== undefined) {
      modelSizeDropdown.value = storedModelSize;
      selectedModelSize = storedModelSize;
    }
  });

  // Load text formatting option and update dropdown (default to "advanced")
  chrome.storage.local.get("textFormatting", ({ textFormatting }) => {
    textFormattingDropdown.value = textFormatting || "advanced";
  });

  // Common function to restart capture if active
  function restartCaptureIfActive() {
    chrome.storage.local.get("capturingState", ({ capturingState }) => {
      if (capturingState && capturingState.isCapturing) {
        stopCapture();
        setTimeout(() => startCapture(), 500);
      }
    });
  }

  // Function to request resetting transcription window in the current tab
  function resetSession() {
    getCurrentTab().then((tab) => {
      if (tab) {
        chrome.tabs.sendMessage(tab.id, { type: "resetSession" });
      }
    });
  }

  // Function to handle the start capture button click event
  async function startCapture() {
    // Ignore click if the button is disabled
    if (startButton.disabled) {
      return;
    }

    // Get the current active tab
    const currentTab = await getCurrentTab();
    if (!currentTab) {
      return;
    }

    // First toggle the button state
    toggleCaptureButtons(true);
    chrome.storage.local.set({ capturingState: { isCapturing: true } });
    
    // Send a message to the background script to start capturing
    chrome.runtime.sendMessage({
      action: "startCapture",
      tabId: currentTab.id,
      host: ipAddress,
      port: port,
      language: selectedLanguage,
      task: selectedTask,
      modelSize: selectedModelSize,
      useVad: useVadCheckbox.checked,
    });
  }

  // Function to handle the stop capture button click event
  function stopCapture() {
    // Ignore click if the button is disabled
    if (stopButton.disabled) {
      return;
    }

    // Update capturing state and toggle buttons
    chrome.storage.local.set({ capturingState: { isCapturing: false } });
    toggleCaptureButtons(false);
    
    // Send a message to the background script to stop capturing
    chrome.runtime.sendMessage({ action: "stopCapture" });
  }

  // Function to get the current active tab
  async function getCurrentTab() {
    return new Promise((resolve) => {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        resolve(tabs[0]);
      });
    });
  }

  // Function to toggle the capture buttons based on the capturing state
  function toggleCaptureButtons(isCapturing) {
    startButton.disabled = isCapturing;
    stopButton.disabled = !isCapturing;
    useVadCheckbox.disabled = isCapturing;
    modelSizeDropdown.disabled = isCapturing;
    languageDropdown.disabled = isCapturing;
    ipAddressInput.disabled = isCapturing;
    portInput.disabled = isCapturing;
    taskDropdown.disabled = isCapturing;
    startButton.classList.toggle("disabled", isCapturing);
    stopButton.classList.toggle("disabled", !isCapturing);
    ipAddressInput.classList.toggle("disabled", isCapturing);
    portInput.classList.toggle("disabled", isCapturing);
  }

  // Save the checkbox state when it's toggled
  useVadCheckbox.addEventListener("change", () => {
    const useVadState = useVadCheckbox.checked;
    chrome.storage.local.set({ useVadState });
  });

  // Event listener for language dropdown change
  languageDropdown.addEventListener('change', function() {
    const selectedLanguage = languageDropdown.value || null; // Store null for "Automatically detect"
    chrome.storage.local.set({ selectedLanguage });
    restartCaptureIfActive();
    resetSession();
  });

  // Event listener for task dropdown change
  taskDropdown.addEventListener('change', function() {
    const selectedTask = taskDropdown.value;
    chrome.storage.local.set({ selectedTask });
    restartCaptureIfActive();
    resetSession();
  });

  // Event listener for model size dropdown change
  modelSizeDropdown.addEventListener('change', function() {
    const selectedModelSize = modelSizeDropdown.value;
    chrome.storage.local.set({ selectedModelSize });
    restartCaptureIfActive();
    resetSession();
  });

  // Event listener for default IP button click
  defaultIpButton.addEventListener('click', function() {
    setDefaultIp();
    restartCaptureIfActive();
  });

  // Event listener for default Port button click
  defaultPortButton.addEventListener('click', function() {
    setDefaultPort();
    restartCaptureIfActive();
  });

  // Function to set the IP address to the default value (localhost)
  function setDefaultIp() {
    ipAddressInput.value = "localhost";
    ipAddress = ipAddressInput.value;
    chrome.storage.local.set({ ipAddress: "localhost" });
  }

  // Function to set the port to the default value (9090)
  function setDefaultPort() {
    portInput.value = "9090";
    port = portInput.value;
    chrome.storage.local.set({ port: "9090" });
  }

  // Event listener for IP address input change
  ipAddressInput.addEventListener('change', function() {
    const ipAddress = ipAddressInput.value;
    chrome.storage.local.set({ ipAddress });
    restartCaptureIfActive();
    resetSession();
  });

  // Event listener for port input change
  portInput.addEventListener('change', function() {
    const port = portInput.value;
    chrome.storage.local.set({ port });
    restartCaptureIfActive();
    resetSession();
  });

  // Event listener for text formatting dropdown change
  textFormattingDropdown.addEventListener("change", function() {
    chrome.storage.local.set({ textFormatting: textFormattingDropdown.value });
    resetSession();
  });

  // Single listener for all message types
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    try {
      // Handle different action types
      if (request.action === "toggleCaptureButtons") {
        console.log("Received toggleCaptureButtons message");
        toggleCaptureButtons(false);
        chrome.storage.local.set({ capturingState: { isCapturing: false } });
        sendResponse({ success: true });
      }
      else {
        // Unknown action type
        sendResponse({ success: false, error: "Unknown action type" });
      }
    } catch (error) {
      console.error("Error processing message:", error);
      sendResponse({ success: false, error: error.message });
    }
    
    // Return true to indicate we want to send a response asynchronously
    return true;
  });

});
