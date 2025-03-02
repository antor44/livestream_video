(function(){
  // Prevent duplicate loading
  if (window.__contentJS_loaded) return;
  window.__contentJS_loaded = true;

  // -------------------- Constants for styles -------------------- //
  const TEXT_SPAN_STYLE = "padding-left:16px; padding-right:16px; display:block;";
  const BUTTON_STYLE = "margin-right:4px; padding:2px 8px; cursor:pointer; background:transparent; border:none; outline:none; font:inherit; color:inherit;";
  const COPY_BUTTON_STYLE = "margin-right:10px; padding:2px 8px; cursor:pointer; background:transparent; border:none; outline:none; font:inherit; color:inherit;";
  const POPUP_CONTAINER_STYLE = "position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); background:white; color:black; padding:16px; border-radius:10px; box-shadow:0px 0px 10px rgba(0,0,0,1); display:none; text-align:center;";
  const CONTENT_STYLE = "width:100%; height:100%; padding:10px; box-sizing:border-box; overflow-y:auto; position:relative;";
  const CONTAINER_STYLE = (style) => 
    `font-size:20px; position:absolute; top:${style.top}; left:${style.left}; width:${style.width}; height:${style.height}; opacity:1; z-index:2147483647; background:black; border-radius:10px; color:white; overflow:auto; resize:both;`;

  // -------------------- Global Variables -------------------- //
  var containerElement = null;
  var transcriptionCurrentEl = null; // cached reference to transcription-current
  var transcriptionHistoryEl = null; // cached reference to transcription-history
  var segments = [];
  var previousSegments = []; // Stores the last received window
  var historySegments = [];  // Stores the old texts that have been saved
  var windowStartTime = null; // Timestamp when the current transcription window started

  // -------------------- Helper Functions for Storage -------------------- //
  function getSetting(key, callback) {
    chrome.storage.local.get(key, (data) => callback(data[key]));
  }
  function setSetting(key, value) {
    chrome.storage.local.set({ [key]: value });
  }

  // -------------------- Debounce Function -------------------- //
  function debounce(func, delay) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    }
  }
  const debouncedSaveWindowStyle = debounce(saveWindowStyle, 300);

  // -------------------- Popup Functions -------------------- //
  function initPopupElement() {
    if (document.getElementById('popupElement')) {
      return;
    }
    const popupContainer = document.createElement('div');
    popupContainer.id = 'popupElement';
    popupContainer.style.cssText = POPUP_CONTAINER_STYLE;
    const popupText = document.createElement('span');
    popupText.textContent = 'Default Text';
    popupText.className = 'popupText';
    popupText.style.fontSize = '24px';
    popupContainer.appendChild(popupText);
    document.body.appendChild(popupContainer);
  }

  function showPopup(customText) {
    const popup = document.getElementById('popupElement');
    const popupText = popup && popup.querySelector('.popupText');
    if (popup && popupText) {
      popupText.textContent = customText || 'Default Text';
      popup.style.display = 'block';
    }
  }

  // -------------------- Initialization Subfunctions -------------------- //
  function createContainer() {
    containerElement = document.createElement('div');
    containerElement.id = 'transcription';
    // Calculate default styles based on the viewport
    const defaultWidth = Math.min(700, Math.floor(window.innerWidth * 0.8));
    const defaultHeight = Math.min(120, Math.floor(window.innerHeight * 0.5));
    const defaultTop = Math.floor((window.innerHeight - defaultHeight) / 1.1);
    const defaultLeft = Math.floor((window.innerWidth - defaultWidth) / 2.5);
    const defaultStyle = {
      top: defaultTop + 'px',
      left: defaultLeft + 'px',
      width: defaultWidth + 'px',
      height: defaultHeight + 'px'
    };

    // Immediately apply the default style using template strings
    containerElement.style.cssText = CONTAINER_STYLE(defaultStyle);

    // Retrieve stored windowStyle; if valid, update; otherwise store default
    chrome.storage.local.get('windowStyle', (data) => {
      if (data.windowStyle) {
        let stored = data.windowStyle;
        let sWidth = parseInt(stored.width);
        let sHeight = parseInt(stored.height);
        let sTop = parseInt(stored.top);
        let sLeft = parseInt(stored.left);
        const valid = !isNaN(sWidth) && !isNaN(sHeight) && !isNaN(sTop) && !isNaN(sLeft) &&
                      sWidth > 0 && sHeight > 0 &&
                      sWidth <= window.innerWidth && sHeight <= window.innerHeight &&
                      sLeft >= 0 && sTop >= 0 &&
                      (sLeft + sWidth) <= window.innerWidth &&
                      (sTop + sHeight) <= window.innerHeight;
        if (valid) {
          containerElement.style.top = sTop + 'px';
          containerElement.style.left = sLeft + 'px';
          containerElement.style.width = sWidth + 'px';
          containerElement.style.height = sHeight + 'px';
        } else {
          containerElement.style.top = defaultStyle.top;
          containerElement.style.left = defaultStyle.left;
          containerElement.style.width = defaultStyle.width;
          containerElement.style.height = defaultStyle.height;
          setSetting('windowStyle', defaultStyle);
        }
      } else {
        setSetting('windowStyle', defaultStyle);
      }
    });
  }

  function createContentArea() {
    const content = document.createElement('div');
    content.id = 'transcription-content';
    content.style.cssText = CONTENT_STYLE;

    // Create history container
    transcriptionHistoryEl = document.createElement('div');
    transcriptionHistoryEl.id = 'transcription-history';
    transcriptionHistoryEl.style.cssText = 'display:block;';
    
    // Add informative text when transcription window is initialized
    chrome.storage.local.get(['selectedLanguage', 'selectedTask', 'selectedModelSize'], (data) => {
      // Determine the language display: use selected language or auto-detect if null
      const language = data.selectedLanguage || 'auto-detect';
      // Determine translation status
      const task = data.selectedTask === 'translate' ? 'translate to English' : 'NO translate to English';
      // Use selected model size, default to unknown if not set
      const model = data.selectedModelSize || 'unknown';
      const webpageTitle = document.title;
      
      const spanElem1 = document.createElement('span');
      spanElem1.style.cssText = TEXT_SPAN_STYLE;
      spanElem1.textContent = `Transcription of ${webpageTitle}`;
      transcriptionHistoryEl.appendChild(spanElem1);
      
      const spanElem2 = document.createElement('span');
      spanElem2.style.cssText = TEXT_SPAN_STYLE;
      spanElem2.textContent = `Transcribing stream with model ${model}, language ${language}, ${task}`;
      transcriptionHistoryEl.appendChild(spanElem2);
      
      const spanElem3 = document.createElement('span');
      spanElem3.style.cssText = TEXT_SPAN_STYLE;
      spanElem3.textContent = `...`;
      transcriptionHistoryEl.appendChild(spanElem3);
    });
    
    // Create current transcription container
    transcriptionCurrentEl = document.createElement('div');
    transcriptionCurrentEl.id = 'transcription-current';
    transcriptionCurrentEl.style.cssText = 'display:block;';
    
    content.appendChild(transcriptionHistoryEl);
    content.appendChild(transcriptionCurrentEl);
    containerElement.appendChild(content);
  }

  function configureControls() {
    const controls = document.createElement('div');
    controls.style.cssText = "position:absolute; top:4px; right:4px; z-index:10; display:flex; align-items:center;";
    
    const decreaseBtn = document.createElement('button');
    decreaseBtn.textContent = '–';
    decreaseBtn.style.cssText = BUTTON_STYLE;
    const increaseBtn = document.createElement('button');
    increaseBtn.textContent = '+';
    increaseBtn.style.cssText = BUTTON_STYLE;
    const copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy';
    copyBtn.style.cssText = COPY_BUTTON_STYLE;
    
    decreaseBtn.addEventListener('click', () => adjustFontSize(-2));
    increaseBtn.addEventListener('click', () => adjustFontSize(2));
    copyBtn.addEventListener('click', copyAllTextToClipboard);
    
    controls.appendChild(decreaseBtn);
    controls.appendChild(increaseBtn);
    controls.appendChild(copyBtn);
    containerElement.appendChild(controls);
  }

  function configureMovement() {
    let x = 0, y = 0;
    const ele = containerElement;
    
    const mouseDownHandler = function(e) {
      if (e.target.tagName.toLowerCase() === 'button') return;
      const rect = ele.getBoundingClientRect();
      const offsetX = e.clientX - rect.left;
      const offsetY = e.clientY - rect.top;
      if (rect.width - offsetX < 16 && rect.height - offsetY < 16) return;
      x = e.clientX;
      y = e.clientY;
      document.addEventListener('mousemove', mouseMoveHandler);
      document.addEventListener('mouseup', mouseUpHandler);
    };
    
    const mouseMoveHandler = function(e) {
      const dx = e.clientX - x;
      const dy = e.clientY - y;
      const newTop = Math.max(0, ele.offsetTop + dy);
      const newLeft = Math.max(0, ele.offsetLeft + dx);
      ele.style.top = `${newTop}px`;
      ele.style.left = `${newLeft}px`;
      x = e.clientX;
      y = e.clientY;
    };
    
    const mouseUpHandler = function() {
      document.removeEventListener('mousemove', mouseMoveHandler);
      document.removeEventListener('mouseup', mouseUpHandler);
      // Save position and size after finishing the movement using debounced function
      debouncedSaveWindowStyle();
    };
    
    ele.addEventListener('mousedown', mouseDownHandler);
  }

  // -------------------- Main Initialization -------------------- //
  function init_element() {
    if (document.getElementById('transcription')) return;
    createContainer();
    createContentArea();
    configureControls();
    document.body.appendChild(containerElement);
    
    // Install ResizeObserver to save style changes with debounce
    if (window.ResizeObserver) {
      const resizeObserver = new ResizeObserver(() => {
        debouncedSaveWindowStyle();
      });
      resizeObserver.observe(containerElement);
    }
    
    // Load saved font size and apply it to both current and history text areas
    getSetting('fontSize', (fontSizeValue) => {
      let fontSize = fontSizeValue || 20;
      const lineHeight = Math.round(fontSize * 1.2) + 'px';
      if (transcriptionCurrentEl && transcriptionHistoryEl) {
        transcriptionCurrentEl.style.fontSize = `${fontSize}px`;
        transcriptionHistoryEl.style.fontSize = `${fontSize}px`;
        transcriptionCurrentEl.style.lineHeight = lineHeight;
        transcriptionHistoryEl.style.lineHeight = lineHeight;
      }
    });
    
    configureMovement();
  }

  // -------------------- Functions for Adjusting and Saving Style -------------------- //
  function adjustFontSize(delta) {
    if (!transcriptionCurrentEl || !transcriptionHistoryEl) return;
    const currentSize = parseInt(transcriptionCurrentEl.style.fontSize || 20);
    const newSize = Math.max(10, currentSize + delta);
    const newLineHeight = Math.round(newSize * 1.2) + 'px';
    transcriptionCurrentEl.style.fontSize = `${newSize}px`;
    transcriptionHistoryEl.style.fontSize = `${newSize}px`;
    transcriptionCurrentEl.style.lineHeight = newLineHeight;
    transcriptionHistoryEl.style.lineHeight = newLineHeight;
    setSetting('fontSize', newSize);
  }

  function saveWindowStyle() {
    if (!containerElement) return;
    const style = {
      top: containerElement.style.top,
      left: containerElement.style.left,
      width: containerElement.style.width,
      height: containerElement.style.height,
    };
    setSetting('windowStyle', style);
  }

  function recalcWindowStyle() {
    if (!containerElement) return;
    let top = parseInt(containerElement.style.top) || 0;
    let left = parseInt(containerElement.style.left) || 0;
    let width = parseInt(containerElement.style.width) || 720;
    let height = parseInt(containerElement.style.height) || 120;
    
    // Limit size to current viewport dimensions
    width = Math.min(width, window.innerWidth);
    height = Math.min(height, window.innerHeight);
    
    // Adjust top and left to ensure the window is visible
    if (left + width > window.innerWidth) {
      left = Math.max(0, window.innerWidth - width);
    }
    if (top + height > window.innerHeight) {
      top = Math.max(0, window.innerHeight - height);
    }
    
    containerElement.style.top = top + 'px';
    containerElement.style.left = left + 'px';
    containerElement.style.width = width + 'px';
    containerElement.style.height = height + 'px';
    containerElement.style.transform = 'none';
    setSetting('windowStyle', {
      top: containerElement.style.top,
      left: containerElement.style.left,
      width: containerElement.style.width,
      height: containerElement.style.height
    });
  }

  // -------------------- Viewport Resize Listener -------------------- //
  window.addEventListener('resize', recalcWindowStyle);

  // -------------------- History Update and Display Functions -------------------- //
  function updateHistory(newSegments) {
    if (!previousSegments.length) {
      previousSegments = newSegments.slice();
      windowStartTime = Date.now();
      return;
    }
    const isStable = newSegments.length >= 5 || (Date.now() - windowStartTime) >= 15000;
    if (!isStable) {
      previousSegments = newSegments.slice();
      return;
    }
    let index = previousSegments.findIndex(seg => seg.text === newSegments[0].text);
    if (index === -1) {
      index = previousSegments.length;
    }
    if (transcriptionHistoryEl) {
      for (let i = 0; i < index; i++) {
        const text = previousSegments[i].text;
        if (!historySegments.includes(text)) {
          historySegments.push(text);
          const spanElem = document.createElement('span');
          spanElem.style.cssText = TEXT_SPAN_STYLE;
          spanElem.textContent = text;
          transcriptionHistoryEl.appendChild(spanElem);
        }
      }
    }
    windowStartTime = Date.now();
    previousSegments = newSegments.slice();
  }

  function displaySegments() {
    if (!transcriptionCurrentEl) return;
    updateHistory(segments);
    transcriptionCurrentEl.innerHTML = '';
    for (let i = 0; i < segments.length; i++) {
      let elemText = document.createElement('span');
      elemText.style.cssText = TEXT_SPAN_STYLE;
      elemText.id = 't' + i;
      elemText.innerHTML = segments[i].text;
      transcriptionCurrentEl.appendChild(elemText);
    }
    const content = document.getElementById('transcription-content');
    if (content) content.scrollTop = content.scrollHeight;
  }

  function remove_element() {
    const elem = document.getElementById('transcription');
    if (elem) {
      elem.remove();
    }
    // Reset the flag so the extension can reinitialize the UI
    window.__contentJS_loaded = false;
  }

  // -------------------- Copy-to-Clipboard -------------------- //
  function copyAllTextToClipboard() {
    const transcriptionContent = document.getElementById('transcription-content');
    if (!transcriptionContent) return;
    const textToCopy = transcriptionContent.innerText; // Get all text including history
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            initPopupElement();
            showPopup("Text copied to clipboard!");
            setTimeout(() => {
                const popup = document.getElementById('popupElement');
                if (popup) popup.style.display = 'none';
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
            showPopup("Failed to copy text!");
        });
  }

  // -------------------- Initialize and Setup Listeners -------------------- //
  init_element();

  window.addEventListener('beforeunload', () => {
    try {
      chrome.runtime.sendMessage({ 
        action: "pageUnloading", 
        stopCapture: true, 
        toggleButtons: true 
      }).catch(() => { /* silently ignore */ });
      remove_element();
    } catch (e) {
      console.log("Ignoring error during page unload");
    }
  });

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const { type, data } = request;

    if (type === 'STOP') {
      remove_element();
      sendResponse({ data: 'STOPPED' });
      return true;
    } else if (type === 'showWaitPopup') {
      initPopupElement();
      showPopup(`Estimated wait time ~ ${Math.round(data)} minutes`);
      sendResponse({ data: 'popup' });
      return true;
    } else if (type === 'transcript') {
      segments = JSON.parse(data).segments;
      displaySegments();
      sendResponse({});
      return true;
    }
    
    sendResponse({});
    return true;
  });
})();
