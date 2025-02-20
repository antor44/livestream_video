var containerElement = null;
var segments = [];
var previousSegments = []; // Stores the last received window
var historySegments = [];  // Stores the old texts that have been saved
var windowStartTime = null; // Timestamp when the current transcription window started

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

  // Add informative text when the transcription window is initialized
  chrome.storage.local.get(['selectedLanguage', 'selectedTask', 'selectedModelSize'], (data) => {
    // Determine the language display: use selected language or "auto-detect" if null
    const language = data.selectedLanguage ? data.selectedLanguage : 'auto-detect';
    // Determine translation status: "translate to English" if task is "translate", else "NO translate"
    const task = data.selectedTask === 'translate' ? 'translate to English' : 'NO translate to English';
    // Use the selected model size, default to "unknown" if not set
    const model = data.selectedModelSize || 'unknown';
    // Get the current webpage title
    const webpageTitle = document.title;

    // Create first line of informative text
    const spanElem1 = document.createElement('span');
    spanElem1.style.cssText = 'padding-left:16px; padding-right:16px; display: block;';
    spanElem1.textContent = `Transcription of ${webpageTitle}`;
    transcriptionHistory.appendChild(spanElem1);

    // Create second line of informative text
    const spanElem2 = document.createElement('span');
    spanElem2.style.cssText = 'padding-left:16px; padding-right:16px; display: block;';
    spanElem2.textContent = `Transcribing stream with model ${model}, language ${language}, ${task}`;
    transcriptionHistory.appendChild(spanElem2);

    // Create third line of informative text
    const spanElem3 = document.createElement('span');
    spanElem3.style.cssText = 'padding-left:16px; padding-right:16px; display: block;';
    spanElem3.textContent = `...`;
    transcriptionHistory.appendChild(spanElem3);
  });

  // Container for the current text window
  const transcriptionCurrent = document.createElement('div');
  transcriptionCurrent.id = 'transcription-current';
  transcriptionCurrent.style.cssText = 'display: block;';

  content.appendChild(transcriptionHistory);
  content.appendChild(transcriptionCurrent);
  containerElement.appendChild(content);

  // Font size adjustment "buttons" and copy button, positioned in the upper right corner
  const controls = document.createElement('div');
  controls.style.cssText = 'position: absolute; top: 4px; right: 4px; z-index: 10; display: flex; align-items: center;'; // Use flexbox

  const decreaseBtn = document.createElement('button');
  decreaseBtn.textContent = '–';
  decreaseBtn.style.cssText =
    'margin-right: 4px; padding: 2px 8px; cursor: pointer; background: transparent; border: none; outline: none; font: inherit; color: inherit;';
  const increaseBtn = document.createElement('button');
  increaseBtn.textContent = '+';
  increaseBtn.style.cssText =
    'margin-right: 4px; padding: 2px 8px; cursor: pointer; background: transparent; border: none; outline: none; font: inherit; color: inherit;';
  const copyBtn = document.createElement('button');
  copyBtn.textContent = 'Copy';
  copyBtn.style.cssText =
    'margin-right: 10px; padding: 2px 8px; cursor: pointer; background: transparent; border: none; outline: none; font: inherit; color: inherit;';

  decreaseBtn.addEventListener('click', () => adjustFontSize(-2));
  increaseBtn.addEventListener('click', () => adjustFontSize(2));
  copyBtn.addEventListener('click', copyAllTextToClipboard);

  controls.appendChild(decreaseBtn);
  controls.appendChild(increaseBtn);
  controls.appendChild(copyBtn); // Add the copy button
  containerElement.appendChild(controls);


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
}

// This function compares the previous window with the new one and saves in history the lines that are no longer present.
// It waits until either at least 5 lines have been written or 15 seconds have passed since the current window started.
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

// New function to copy all text to the clipboard
function copyAllTextToClipboard() {
    const transcriptionContent = document.getElementById('transcription-content');
    if (!transcriptionContent) return;

    const textToCopy = transcriptionContent.innerText; // Use innerText to get all text, including history

    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            // Optional: Show a success message (you could use your popup for this)
            initPopupElement(); // Make sure the popup element exists
            showPopup("Text copied to clipboard!");
            setTimeout(() => {
                const popup = document.getElementById('popupElement');
                if (popup) popup.style.display = 'none';
            }, 2000); // Hide popup after 2 seconds
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
            // Optional: Show an error message
            showPopup("Failed to copy text!"); // Indicate copy failure
        });
}



init_element();

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
  segments = JSON.parse(data).segments;
  displaySegments();
  sendResponse({});
  return true;
});
