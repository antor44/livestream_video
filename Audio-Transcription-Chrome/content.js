var elem_container = null;
var elem_text = null;
var segments = [];

function initPopupElement() {
  if (document.getElementById('popupElement')) {
    return;
  }

  const popupContainer = document.createElement('div');
  popupContainer.id = 'popupElement';
  popupContainer.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; color: black; padding: 16px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 1); display: none; text-align: center;';

  const popupText = document.createElement('span');
  popupText.textContent = 'Default Text';
  popupText.className = 'popupText';
  popupText.style.fontSize = '24px';
  popupContainer.appendChild(popupText);

  const buttonContainer = document.createElement('div');
  buttonContainer.style.marginTop = '8px';
  const closePopupButton = document.createElement('button');
  closePopupButton.textContent = 'Close';
  closePopupButton.style.backgroundColor = '#65428A';
  closePopupButton.style.color = 'white';
  closePopupButton.style.border = 'none';
  closePopupButton.style.padding = '8px 16px';
  closePopupButton.style.cursor = 'pointer';
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

    elem_container = document.createElement('div');
    elem_container.id = "transcription";
    elem_container.style.cssText = 'padding-top:4px;font-size:20px;position: absolute; top: 92%; left: 38%; transform: translate(-50%, -50%);line-height:18px;width:1000px;height:110px;opacity:1;z-index: 2147483647;background:black;border-radius:10px;color:white;overflow-y: auto; resize: both;'; // Changed to position: absolute

    document.body.appendChild(elem_container);

    let x = 0;
    let y = 0;

    // Query the element
    const ele = elem_container;

    // --- Drag Logic (Move) ---
    const mouseDownHandler = function (e) {

      // Only allow dragging from the top of the container, not the resize handle
      if (e.offsetY < 30) { // Check if click is within the top 30px (adjust as needed)
        x = e.clientX;
        y = e.clientY;
        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
      }

    };

    const mouseMoveHandler = function (e) {
        const dx = e.clientX - x;
        const dy = e.clientY - y;
          // Use offsetWidth and offsetHeight to get the actual dimensions
        const newTop = Math.max(0, ele.offsetTop + dy); // Prevent going off-screen top
        const newLeft = Math.max(0, ele.offsetLeft + dx); // Prevent going off-screen left

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


function remove_element() {
    var elem = document.getElementById('transcription')
    if (elem) {
        elem.remove();
    }
}

function displaySegments() {
    if (!elem_container) return;

    // Clear existing spans
    while (elem_container.firstChild) {
        elem_container.removeChild(elem_container.firstChild);
    }

    for (let i = 0; i < segments.length; i++) {
        let elem_text = document.createElement('span');
        elem_text.style.cssText = 'padding-left:16px;padding-right:16px;display: block;';
        elem_text.id = "t" + i;
        elem_text.innerHTML = segments[i].text;
        elem_container.appendChild(elem_text);
    }

    // Scroll to the bottom after adding new segments
    elem_container.scrollTop = elem_container.scrollHeight;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const { type, data } = request;

    if (type === "STOP") {
        remove_element();
        sendResponse({ data: "STOPPED" });
        return true;
    } else if (type === "showWaitPopup") {
        initPopupElement();
        showPopup(`Estimated wait time ~ ${Math.round(data)} minutes`);
        sendResponse({ data: "popup" });
        return true;
    }

    init_element();

    segments = JSON.parse(data).segments;
    displaySegments();

    sendResponse({});
    return true;
});
