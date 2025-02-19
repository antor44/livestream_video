var containerElement = null;
var segments = [];
var previousSegments = []; // Stores the last received window
var historySegments = [];  // Stores the old texts that have been saved
var windowStartTime = null; // Timestamp when the current transcription window started

// Save the current window geometry (top, left, width, height) in chrome.storage
function saveWindowGeometry() {
  if (!containerElement) return;
  const geometry = {
    top: containerElement.style.top,
    left: containerElement.style.left,
    width: containerElement.offsetWidth + 'px',
    height: containerElement.offsetHeight + 'px'
  };
  chrome.storage.local.set({ windowGeometry: geometry });
}

// Load the saved window geometry from chrome.storage and apply it
function loadWindowGeometry() {
  chrome.storage.local.get('windowGeometry', (data) => {
    if (data.windowGeometry && containerElement) {
      const geometry = data.windowGeometry;
      containerElement.style.top = geometry.top;
      containerElement.style.left = geometry.left;
      containerElement.style.width = geometry.width;
      containerElement.style.height = geometry.height;
      containerElement.style.transform = '';
    }
  });
}

function initPopupElement() {
  if (document.getElementById('popupElement')) {
    return;
  }
  const popupContainer = document.createElement('div');
  popupContainer.id = 'popupElement';
  popupContainer.style.cssText =
    'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; color: black; padding: 16px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 1); display: none; text-align: center;';
  const popupText = document.createElement('span');
  popupText.textContent = 'Default Text';
  popupText.className = 'popupText';
  popupText.style.fontSize = '24px';
  popupContainer.appendChild(popupText);
  const buttonContainer = document.createElement('div');
  buttonContainer.style.marginTop = '8px';
  const closePopupButton = document.createElement('button');
  closePopupButton.textContent = 'Close';
  closePopupButton.style.cssText =
    'background-color: #65428A; color: white; border: none; padding: 8px 16px; cursor: pointer;';
  closePopupButton.addEventListener('click', async () => {
    popupContainer.style.display = 'none';
    await browser.runtime.sendMessage({ action: 'toggleCaptureButtons', data: false });
  });
  buttonContainer.appendChild(closePopupButton);
  popupContainer.appendChild(buttonContainer);
  document.body.appendChild(popupContainer);
}

function showPopup(customText) {
  const popup = document.getElementById('popupElement');
  const popupText = popup.querySelector('.popupText');
  if (popup && popupText) {
    popupText.textContent = customText || 'Default Text';
    popup.style.display = 'block';
  }
}

function init_element() {
  if (document.getElementById('transcription')) {
    return;
  }
  // Create main container with native resizing (removed fixed line-height)
  containerElement = document.createElement('div');
  containerElement.id = 'transcription';
  containerElement.style.cssText =
    'font-size:20px; position: absolute; top: 92%; left: 38%; transform: translate(-50%, -50%); width:1000px; height:110px; opacity:1; z-index:2147483647; background:black; border-radius:10px; color:white; overflow: auto; resize: both;';
  
  // Content area occupying the full container
  const content = document.createElement('div');
  content.id = 'transcription-content';
  content.style.cssText =
    'width: 100%; height: 100%; padding: 10px; box-sizing: border-box; overflow-y: auto; position: relative;';
  
  // Container for history (text that has already disappeared)
  const transcriptionHistory = document.createElement('div');
  transcriptionHistory.id = 'transcription-history';
  transcriptionHistory.style.cssText = 'display: block;';
  
  // Container for the current text window
  const transcriptionCurrent = document.createElement('div');
  transcriptionCurrent.id = 'transcription-current';
  transcriptionCurrent.style.cssText = 'display: block;';
  
  content.appendChild(transcriptionHistory);
  content.appendChild(transcriptionCurrent);
  containerElement.appendChild(content);
  
  // Font size adjustment "buttons" as text characters, positioned in the upper right corner
  const fontSizeControls = document.createElement('div');
  fontSizeControls.style.cssText = 'position: absolute; top: 4px; right: 40px; z-index: 10;';
  const decreaseBtn = document.createElement('button');
  decreaseBtn.textContent = '–';
  decreaseBtn.style.cssText =
    'margin-right: 4px; padding: 2px 8px; cursor: pointer; background: transparent; border: none; outline: none; font: inherit; color: inherit;';
  const increaseBtn = document.createElement('button');
  increaseBtn.textContent = '+';
  increaseBtn.style.cssText =
    'padding: 2px 8px; cursor: pointer; background: transparent; border: none; outline: none; font: inherit; color: inherit;';
  decreaseBtn.addEventListener('click', () => adjustFontSize(-2));
  increaseBtn.addEventListener('click', () => adjustFontSize(2));
  fontSizeControls.appendChild(decreaseBtn);
  fontSizeControls.appendChild(increaseBtn);
  containerElement.appendChild(fontSizeControls);
  
  document.body.appendChild(containerElement);
  
  // Load saved font size and apply it to both current and history text areas, including line-height
  chrome.storage.local.get('fontSize', (data) => {
    let fontSize = data.fontSize || 20;
    const lineHeight = Math.round(fontSize * 1.2) + 'px';
    const transcriptionCurrent = document.getElementById('transcription-current');
    const transcriptionHistory = document.getElementById('transcription-history');
    transcriptionCurrent.style.fontSize = `${fontSize}px`;
    transcriptionHistory.style.fontSize = `${fontSize}px`;
    transcriptionCurrent.style.lineHeight = lineHeight;
    transcriptionHistory.style.lineHeight = lineHeight;
  });
  
  // Load saved window geometry (position and size)
  loadWindowGeometry();
  
  let x = 0;
  let y = 0;
  const ele = containerElement;
  
  // Logic to move the window
  const mouseDownHandler = function (e) {
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
  
  const mouseMoveHandler = function (e) {
    const dx = e.clientX - x;
    const dy = e.clientY - y;
    const newTop = Math.max(0, ele.offsetTop + dy);
    const newLeft = Math.max(0, ele.offsetLeft + dx);
    ele.style.top = `${newTop}px`;
    ele.style.left = `${newLeft}px`;
    x = e.clientX;
    y = e.clientY;
  };
  
  const mouseUpHandler = function () {
    document.removeEventListener('mousemove', mouseMoveHandler);
    document.removeEventListener('mouseup', mouseUpHandler);
    saveWindowGeometry();
  };
  
  ele.addEventListener('mousedown', mouseDownHandler);
}

// Adjust font size and line-height for both current and history text areas
function adjustFontSize(delta) {
  const transcriptionCurrent = document.getElementById('transcription-current');
  const transcriptionHistory = document.getElementById('transcription-history');
  if (!transcriptionCurrent || !transcriptionHistory) return;
  const currentSize = parseInt(transcriptionCurrent.style.fontSize || 20);
  const newSize = Math.max(10, currentSize + delta);
  const newLineHeight = Math.round(newSize * 1.2) + 'px';
  transcriptionCurrent.style.fontSize = `${newSize}px`;
  transcriptionHistory.style.fontSize = `${newSize}px`;
  transcriptionCurrent.style.lineHeight = newLineHeight;
  transcriptionHistory.style.lineHeight = newLineHeight;
  chrome.storage.local.set({ fontSize: newSize });
  saveWindowGeometry();
}

// This function compares the previous window with the new one and saves in history the lines that are no longer present.
// It waits until either at least 3 lines have been written or 30 seconds have passed since the current window started.
function updateHistory(newSegments) {
  if (!previousSegments.length) {
    previousSegments = newSegments.slice();
    windowStartTime = Date.now();
    return;
  }
  const isStable = newSegments.length >= 3 || (Date.now() - windowStartTime) >= 30000;
  if (!isStable) {
    previousSegments = newSegments.slice();
    return;
  }
  let index = previousSegments.findIndex(seg => seg.text === newSegments[0].text);
  if (index === -1) {
    index = previousSegments.length;
  }
  const transcriptionHistory = document.getElementById('transcription-history');
  for (let i = 0; i < index; i++) {
    const text = previousSegments[i].text;
    if (!historySegments.includes(text)) {
      historySegments.push(text);
      const spanElem = document.createElement('span');
      spanElem.style.cssText = 'padding-left:16px; padding-right:16px; display: block;';
      spanElem.textContent = text;
      transcriptionHistory.appendChild(spanElem);
    }
  }
  windowStartTime = Date.now();
  previousSegments = newSegments.slice();
}

function displaySegments() {
  const transcriptionCurrent = document.getElementById('transcription-current');
  if (!transcriptionCurrent) return;
  updateHistory(segments);
  transcriptionCurrent.innerHTML = '';
  for (let i = 0; i < segments.length; i++) {
    let elemText = document.createElement('span');
    elemText.style.cssText = 'padding-left:16px; padding-right:16px; display: block;';
    elemText.id = 't' + i;
    elemText.innerHTML = segments[i].text;
    transcriptionCurrent.appendChild(elemText);
  }
  const content = document.getElementById('transcription-content');
  content.scrollTop = content.scrollHeight;
}

function remove_element() {
  const elem = document.getElementById('transcription');
  if (elem) {
    elem.remove();
  }
}

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
  }
  init_element();
  segments = JSON.parse(data).segments;
  displaySegments();
  sendResponse({});
  return true;
});

// Global listener to save geometry on any mouseup (useful for resize events)
document.addEventListener('mouseup', () => {
  if (containerElement) {
    saveWindowGeometry();
  }
});
