(function(){
  // Prevent duplicate loading.
  // if (window.__contentJS_loaded) return;
  // window.__contentJS_loaded = true;

  // If there are no multimedia elements on the page (video/audio), remove the overlay.
  if (!document.querySelector('video, audio')) {
    remove_element();
    return;
  }

  // -------------------- Constants for Styles -------------------- //
  const TEXT_SPAN_STYLE = "padding-left:16px; padding-right:16px; display:block;";
  const TITLE_SPAN_STYLE = "padding-left:16px; padding-right:16px; display:block; font-weight: bold; margin-bottom: 8px;";
  const BUTTON_STYLE = "margin-right:4px; padding:2px 8px; cursor:pointer; background:transparent; border:none; outline:none; font:inherit; color:inherit;";
  const COPY_BUTTON_STYLE = "margin-right:10px; padding:2px 8px; cursor:pointer; background:transparent; border:none; outline:none; font:inherit; color:inherit;";
  const POPUP_CONTAINER_STYLE = "position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); background:white; color:black; padding:16px; border-radius:10px; box-shadow:0px 0px 10px rgba(0,0,0,1); display:none; text-align:center;";
  const CONTENT_STYLE = "width:100%; height:100%; padding:10px; box-sizing:border-box; overflow-y:auto; position:relative;";
  const CONTAINER_STYLE = (style) =>
    `font-size:20px; position:absolute; top:${style.top}; left:${style.left}; width:${style.width}; height:${style.height}; opacity:1; z-index:2147483647; background:black; border-radius:10px; color:white; overflow:auto; resize:both;`;

  // -------------------- Global Variables -------------------- //
  let containerElement = null; // Main transcription container.
  let transcriptionCurrentEl = null; // Current transcription area.
  let transcriptionHistoryEl = null; // Transcription history container.
  let transcriptionHeaderEl = null; // Header container.
  let segments = [];  // Current transcription segments.
  let previousSegments = []; // Previously received segments.
  let historySegments = [];  // Stored historical segments (raw, unformatted).
  let windowStartTime = null; // Timestamp when the current transcription window started.
  let currentUrl = window.location.href;  // Track current URL for navigation changes.

  // -------------------- Helper Functions for Storage -------------------- //
  // Retrieves a setting from Chrome's local storage.
  function getSetting(key, callback) {
    chrome.storage.local.get(key, (data) => callback(data[key]));
  }
  // Saves a setting to Chrome's local storage.
  function setSetting(key, value) {
    chrome.storage.local.set({ [key]: value });
  }

  // -------------------- Debounce Function -------------------- //
  // Debounces a function call.
  function debounce(func, delay) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    }
  }
  const debouncedSaveWindowStyle = debounce(saveWindowStyle, 300);

  // -------------------- Popup Functions -------------------- //
  // Initializes the popup element.
  function initPopupElement() {
    if (document.getElementById('popupElement')) return;
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
  // Shows the popup with custom text.
  function showPopup(customText) {
    const popup = document.getElementById('popupElement');
    const popupText = popup && popup.querySelector('.popupText');
    if (popup && popupText) {
      popupText.textContent = customText || 'Default Text';
      popup.style.display = 'block';
    }
  }

  // -------------------- Initialization Subfunctions -------------------- //
  // Creates the main transcription container.
  function createContainer() {
    containerElement = document.createElement('div');
    containerElement.id = 'transcription';
    // Calculate default styles based on the viewport.
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
    containerElement.style.cssText = CONTAINER_STYLE(defaultStyle);

    // Retrieve stored windowStyle; if valid, update; otherwise save default.
    chrome.storage.local.get('windowStyle', (data) => {
      if (data.windowStyle) {
        const stored = data.windowStyle;
        const sWidth = parseInt(stored.width);
        const sHeight = parseInt(stored.height);
        const sTop = parseInt(stored.top);
        const sLeft = parseInt(stored.left);
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

  // Creates the content area within the transcription container.
  function createContentArea() {
    const content = document.createElement('div');
    content.id = 'transcription-content';
    content.style.cssText = CONTENT_STYLE;

    // Create header container for initial information.
    transcriptionHeaderEl = document.createElement('div');
    transcriptionHeaderEl.id = 'transcription-header';
    transcriptionHeaderEl.style.cssText = 'display:block;';

    // Create history container for accumulated transcription text.
    transcriptionHistoryEl = document.createElement('div');
    transcriptionHistoryEl.id = 'transcription-history';
    transcriptionHistoryEl.style.cssText = 'display:block;';

    // Add header information (this will not be overwritten later).
    chrome.storage.local.get(['selectedLanguage', 'selectedTask', 'selectedModelSize'], (data) => {
      const language = data.selectedLanguage || 'auto-detect';
      const task = data.selectedTask === 'translate' ? 'translate to English' : 'NO translate to English';
      const model = data.selectedModelSize || 'unknown';
      const webpageTitle = document.title;
      const spanElem1 = document.createElement('span');
      spanElem1.style.cssText = TITLE_SPAN_STYLE;
      spanElem1.textContent = `Transcription of ${webpageTitle}`;
      transcriptionHeaderEl.appendChild(spanElem1);
      const spanElem2 = document.createElement('span');
      spanElem2.style.cssText = TITLE_SPAN_STYLE;
      spanElem2.textContent = `Transcribing stream with model ${model}, language ${language}, ${task}`;
      transcriptionHeaderEl.appendChild(spanElem2);
    });

    // Create current transcription container.
    transcriptionCurrentEl = document.createElement('div');
    transcriptionCurrentEl.id = 'transcription-current';
    transcriptionCurrentEl.style.cssText = 'display:block;';

    // Append the header, history, and current transcription areas.
    content.appendChild(transcriptionHeaderEl);
    content.appendChild(transcriptionHistoryEl);
    content.appendChild(transcriptionCurrentEl);
    containerElement.appendChild(content);
  }

  // Configures control buttons (adjust font size, copy).
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

  // Configures movement for the transcription window.
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
      debouncedSaveWindowStyle();
    };
    ele.addEventListener('mousedown', mouseDownHandler);
  }

  // -------------------- Functions for Adjusting and Saving Style -------------------- //
  // Adjusts the font size of transcription text.
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

  // Saves the current window style (position and size) to storage.
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

  // Recalculates window style ensuring it fits within the viewport.
  function recalcWindowStyle() {
    if (!containerElement) return;
    let top = parseInt(containerElement.style.top) || 0;
    let left = parseInt(containerElement.style.left) || 0;
    let width = parseInt(containerElement.style.width) || 720;
    let height = parseInt(containerElement.style.height) || 120;
    width = Math.min(width, window.innerWidth);
    height = Math.min(height, window.innerHeight);
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

  // Updates historySegments with new stable segments from newSegments.
  function updateHistory(newSegments) {
    if (!previousSegments.length) {
      previousSegments = newSegments.slice();
      windowStartTime = Date.now();
      return;
    }
    // Consider the window stable if there are at least 3 segments or 8 seconds have passed.
    const isStable = newSegments.length >= 3 || (Date.now() - windowStartTime) >= 8000;
    if (!isStable) {
      previousSegments = newSegments.slice();
      return;
    }
    let index = previousSegments.findIndex(seg => seg.text === newSegments[0].text);
    if (index === -1) {
      index = previousSegments.length;
    }
    
    // Process stable segments for addition to history
    for (let i = 0; i < index; i++) {
      const text = previousSegments[i].text;
      
      // Skip empty segments
      if (!text || text.trim().length === 0) {
        continue;
      }
      
      // Skip hallucination check for very short texts
      if (text.split(/\s+/).length <= 3) {
        if (!historySegments.includes(text)) {
          historySegments.push(text);
        }
        continue;
      }
      
      // Check similarity with existing history segments to detect hallucinations
      let isHallucination = false;
      
      // If history is empty, add the segment
      if (historySegments.length === 0) {
        historySegments.push(text);
        continue;
      }
      
      // Compare with the last few history segments to detect hallucinations
      const similarityThreshold = 0.9; // 90% similarity threshold
      const lastSegmentsToCheck = Math.min(2, historySegments.length);
      
      for (let j = 1; j <= lastSegmentsToCheck; j++) {
        const prevHistorySegment = historySegments[historySegments.length - j];
        const similarity = calculateTextSimilarity(text, prevHistorySegment);
        
        // If too similar to existing content, consider it a hallucination or duplicate
        if (similarity > similarityThreshold) {
          isHallucination = true;
          break;
        }
      }
      
      if (!isHallucination && !historySegments.includes(text)) {
        historySegments.push(text);
      }
    }
    
    windowStartTime = Date.now();
    previousSegments = newSegments.slice();
  }

  // -------------------- Text Similarity Function -------------------- //
  // Calculate similarity between two texts using word comparison
  function calculateTextSimilarity(text1, text2) {
    if (!text1 || !text2) return 0;
    
    // Convert texts to word arrays and filter out empty strings
    const words1 = text1.toLowerCase().split(/\s+/).filter(word => word.length > 0);
    const words2 = text2.toLowerCase().split(/\s+/).filter(word => word.length > 0);
    
    // If either text has very few words, similarity is less relevant
    if (words1.length <= 3 || words2.length <= 3) {
      return words1.length > 0 && words2.length > 0 ? 0.9 : 0; // Consider short non-empty texts as similar
    }
    
    // Count matching words
    const wordSet = new Set(words1);
    const matchingWords = words2.filter(word => wordSet.has(word)).length;
    
    // Calculate similarity as percentage of matching words relative to the longer text
    return matchingWords / Math.max(words1.length, words2.length);
  }
  
  // Advanced formatting function.
  // This simplified approach inserts a newline after a punctuation mark
  // (period, exclamation, question mark, or ellipsis) if it is followed by at least one space.
  // In cases like acronyms or numbers, there is no space after the punctuation.
  function advancedFormat(text) {
    return text.replace(/([.!?…])\s+/g, '$1\n');
  }

  // Displays the current transcription segments and updates the history display.
  function displaySegments() {
    // Basic validation
    if (!transcriptionCurrentEl) return;
    
    // Create backup of current content in case rendering fails
    const currentContent = transcriptionCurrentEl.innerHTML;
    
    try {
      // Update history with current raw segments
      updateHistory(segments);
      
      // Validate segments arrays
      const validHistorySegments = Array.isArray(historySegments) ? historySegments : [];
      const validSegments = Array.isArray(segments) ? segments : [];
      
      // Use a promise to ensure we don't have race conditions with settings retrieval
      new Promise((resolve) => {
        chrome.storage.local.get("textFormatting", resolve);
      })
      .then((result) => {
        const formatType = result.textFormatting || "none";
        
        // Don't clear content until we're ready to actually add new content
        let newContent = document.createDocumentFragment();
        
        if (formatType === "none") {
          // In "none" mode, render each history segment and current segment individually.
          validHistorySegments.forEach((text) => {
            if (text && text.trim()) { // Skip empty segments
              const spanElem = document.createElement('span');
              spanElem.style.cssText = TEXT_SPAN_STYLE;
              spanElem.innerText = text;
              newContent.appendChild(spanElem);
            }
          });
          
          validSegments.forEach((seg, i) => {
            if (seg && seg.text && seg.text.trim()) { // Skip empty segments
              const elemText = document.createElement('span');
              elemText.style.cssText = TEXT_SPAN_STYLE;
              elemText.id = 't' + i;
              elemText.innerText = seg.text; // Use innerText instead of innerHTML for security
              newContent.appendChild(elemText);
            }
          });
        } else {
          // In "join" and "advanced" modes, join history and current segments.
          const historyText = validHistorySegments.filter(text => text && text.trim()).map(text => text.trim()).join(" ");
          const currentText = validSegments.filter(seg => seg && seg.text && seg.text.trim()).map(seg => seg.text.trim()).join(" ");
          let fullText = (historyText + " " + currentText).trim();
          
          if (formatType === "advanced") {
            fullText = advancedFormat(fullText);
            const lines = fullText.split('\n');
            const mergedLines = [];
            
            for (let i = 0; i < lines.length; i++) {
              let currentLine = lines[i];
              while (i + 1 < lines.length && currentLine.trim().length < 8) {
                currentLine += " " + lines[i + 1].trim();
                i++;
              }
              if (currentLine.trim()) { // Skip empty lines
                mergedLines.push(currentLine);
              }
            }
            
            fullText = mergedLines.join('\n');
          }
          
          if (fullText.trim()) { // Only create element if there's actual text
            const elemText = document.createElement('span');
            elemText.style.cssText = TEXT_SPAN_STYLE;
            elemText.innerText = fullText;
            newContent.appendChild(elemText);
          }
        }
        
        // Only replace content if we successfully generated new content
        if (newContent.childNodes.length > 0) {
          transcriptionCurrentEl.innerHTML = '';
          transcriptionCurrentEl.appendChild(newContent);
        } else if (currentContent) {
          // If no new content but we had previous content, restore it
          transcriptionCurrentEl.innerHTML = currentContent;
        }
        
        // Scroll to the bottom of the content area
        const content = document.getElementById('transcription-content');
        if (content) content.scrollTop = content.scrollHeight;
      })
      .catch((error) => {
        console.error("Error displaying segments:", error);
        // Restore previous content if rendering fails
        if (currentContent) {
          transcriptionCurrentEl.innerHTML = currentContent;
        }
      });
    } catch (error) {
      console.error("Error in displaySegments:", error);
      // Restore previous content if processing fails
      if (currentContent) {
        transcriptionCurrentEl.innerHTML = currentContent;
      }
    }
  }

  // Removes the transcription element from the DOM.
  function remove_element() {
    const elem = document.getElementById('transcription');
    if (elem) {
      elem.remove();
    }
    chrome.storage.local.set({ capturingState: { isCapturing: false } });
    chrome.runtime.sendMessage({ action: "toggleCaptureButtons" });
    window.__contentJS_loaded = false;
  }

  // -------------------- Copy-to-Clipboard -------------------- //
  // Copies all transcribed text (including history) to the clipboard.
  function copyAllTextToClipboard() {
    const transcriptionContent = document.getElementById('transcription-content');
    if (!transcriptionContent) return;
    const textToCopy = transcriptionContent.innerText;
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

  // Checks for visible media elements.
  function hasVisibleMediaElements() {
    const mediaElements = document.querySelectorAll('video, audio');
    for (const media of mediaElements) {
      const rect = media.getBoundingClientRect();
      const style = window.getComputedStyle(media);
      if (rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden") {
        return true;
      }
    }
    return false;
  }

  // Stub function for adding an initialization header.
  function addInitializationHeader() {
    return true;
  }

  // Override pushState to detect SPA navigation.
  (function(history){
    const pushState = history.pushState;
    history.pushState = function(state) {
      const result = pushState.apply(history, arguments);
      window.dispatchEvent(new Event('locationchange'));
      return result;
    };
  })(window.history);

  window.addEventListener('popstate', function(){
    window.dispatchEvent(new Event('locationchange'));
  });

  window.addEventListener('hashchange', function(){
    window.dispatchEvent(new Event('locationchange'));
  });

  window.addEventListener('locationchange', function(){
    if (window.location.href !== currentUrl) {
      if (!hasVisibleMediaElements()) {
        remove_element();
      } else {
        addInitializationHeader();
      }
      currentUrl = window.location.href;
    }
  });

  let currentTitle = document.title;
  const titleObserver = new MutationObserver(mutations => {
    if (document.title !== currentTitle) {
      currentTitle = document.title;
      if (hasVisibleMediaElements()) {
        addInitializationHeader();
      } else {
        remove_element();
      }
    }
  });
  const titleElement = document.querySelector('title');
  if (titleElement) {
    titleObserver.observe(titleElement, { childList: true });
  }

  const mediaObserver = new MutationObserver(mutations => {
    if (!hasVisibleMediaElements()) {
      remove_element();
      mediaObserver.disconnect();
    }
  });
  mediaObserver.observe(document.body, { childList: true, subtree: true });

  // -------------------- Initialize and Setup Listeners -------------------- //
  function init_element() {
    if (document.getElementById('transcription')) return;
    createContainer();
    createContentArea();
    configureControls();
    document.body.appendChild(containerElement);
    if (window.ResizeObserver) {
      const resizeObserver = new ResizeObserver(() => {
        debouncedSaveWindowStyle();
      });
      resizeObserver.observe(containerElement);
    }
    getSetting('fontSize', (fontSizeValue) => {
      const fontSize = fontSizeValue || 20;
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

  window.addEventListener('beforeunload', () => {
    try {
      chrome.runtime.sendMessage({
        action: "pageUnloading",
        stopCapture: true,
        toggleButtons: true
      }).catch((e) => { console.error("Error during page unload:", e); });
      remove_element();
    } catch (e) {
      console.error("Ignoring error during page unload:", e);
    }
  });

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const { type, data } = request;
    if (type === 'resetSession') {
      if (transcriptionHistoryEl) {
        addInitializationHeader();
      }
      sendResponse({ success: true });
      return true;
    }
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

  init_element();
})();
