# Audio Transcription for Chrome/Chromium/Microsoft Edge 1.6.0

Audio Transcription is a Chrome/Chromium/Microsoft Edge extension that allows users to capture any audio playing in the current tab and transcribe it in real time using OpenAI Whisper, with a local server running on the user's computer. The user has the option to choose from all languages supported by OpenAI’s Whisper transcription AI, translate any language into English, and enable voice activity detection to avoid sending audio to the server when there is no speech.

This is a forked version with some aesthetic changes and enhancements, designed specifically for use with a local server running WhisperLive. You need to install [WhisperLive](https://github.com/collabora/WhisperLive). It supports Linux, Windows through WSL2, and macOS ARM (Intel versions do not work).

Also in this release, we've added enhanced server configuration options that let you customize the server IP and port.

---

## New Features

- **Custom Server Configuration:**
  - **IP and Port Textboxes:** You can now enter a custom server IP address and port directly in the extension.
  - **Default Buttons:** Two handy buttons allow you to quickly reset the values:
    - **Default IP:** Resets the server IP to `localhost`.
    - **Default Port:** Resets the port to `9090`.

---

## Installing the WhisperLive Server

- Depending on your operating system configuration, you may need to create a Python virtual environment using either Anaconda or virtualenv (not pipx, which is not intended for libraries), and you need to activate this environment to run the WhisperLive server. For virtualenv:
```
sudo apt install virtualenv
```
Or for macOS:
```
brew install virtualenv
```
Then:
```
mkdir ~/python-environments
virtualenv ~/python-environments/whisper-live
source ~/python-environments/whisper-live/bin/activate
```

- Install WhisperLive (at least version 0.6.2):
```
pip3 install "whisper-live>=0.6.2"
```
If an error occurs, i.e. with Python 3.12, because "Could not find a version that satisfies the requirement onnxruntime==1.16.0 (from whisper-live)", then you have to
try the alternative installation by downloading the WhisperLive GitHub repository:


Clone WhisperLive repository:
```
git clone https://github.com/collabora/WhisperLive.git

```
```
cd WhisperLive
```
```
pip3 install .
```
This may take several minutes.

- Download this repository, you can use the following command:
```
git clone https://github.com/antor44/livestream_video.git
```
---

## Running the WhisperLive Server

Before using the extension, make sure you run the local WhisperLive server:

- Change to the directory Audio-Transcription-Chrome (our version inside the subdirectory livestream_video):
```
cd livestream_video/Audio-Transcription-Chrome
```
- Run a local WhisperLive server:
```
./WhisperLive_server.sh
```
Or, if you use a Python virtual environment:
```
source ~/python-environments/whisper-live/bin/activate && ./WhisperLive_server.sh
```
If a "numpy version 2" error occurs:
```
pip3 install "numpy<2"
```

*You can edit the bash script WhisperLive_server.sh for modify the default Server IP and Port.

---

## Installing the Extension

1. Open Google Chrome, Chromium, or Microsoft Edge.
2. In the address bar, type `chrome://extensions` and press Enter.
3. Enable **Developer mode** (toggle switch in the top right corner).
4. Click the **Load unpacked** button.
5. Browse to the folder where you cloned this repository and select the `Audio-Transcription-Chrome` folder (our version inside the subdirectory livestream_video).
6. The extension should now appear on the extensions page.
7. (Optional) Disable **Developer mode** for normal usage.

---

## Using the Extension

1. **Prepare the Server:**
   - Ensure that the WhisperLive server is running.
2. **Play Audio:**
   - Play any audio or video on a webpage.
3. **Open the Extension:**
   - Click the extension icon to open the options popup.
4. **Configure Your Options:**
   - **Language:** Select the target language for transcription or translation.
   - **Task:** Choose between "transcribe" for transcription or "translate" to convert audio to English.
   - **Model Size:** Pick the model size that suits your system’s performance.
   - **Server Configuration:**
     - Enter a custom server IP and port using the provided textboxes.
     - Click **Default IP** to revert the IP to `localhost`.
     - Click **Default Port** to revert the port to `9090`.
5. **Start Transcription:**
   - Click the **Start Capture** button to begin capturing audio and sending it to the server.
   - The first time a model is selected, the necessary files will be downloaded automatically.
6. **Stop Transcription:**
   - Click the **Stop Capture** button to end the session.

---

## Windows Installation (WSL2)

For Windows users, the local server runs through Windows Subsystem for Linux (WSL2):

1. Install PortAudio inside WSL2 by running in the linux terminal:
   ```
   sudo apt-get install portaudio19-dev python3-all-dev
   ```
2. Install WhisperLive and run `./WhisperLive_server.sh` within your Linux environment.
3. Use the extension in the Windows version of Chrome/Chromium/Microsoft Edge by copying or downloading this repository (or just the extension directory) to a Windows folder and loading it via the **Load unpacked** option.

---
## Screenshot

![Screenshot](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/Chrome_extension1.jpg)

---


## Real-Time Transcription with OpenAI-Whisper

We use the OpenAI-Whisper model to process audio continuously and send transcriptions back to the client in real time. By integrating optimizations via [faster-whisper](https://github.com/guillaumekln/faster-whisper), we achieve transcription speeds up to 4x faster than the standard implementation.

---

## Implementation Details

### Capturing Audio

The extension captures audio from the current tab using Chrome’s `tabCapture` API, which provides a `MediaStream` object that is then sent to the server for transcription.

### Options Summary

- **Language:** Choose from multiple languages supported by OpenAI-Whisper.
- **Task:** Select either "transcribe" for transcription or "translate" to convert audio to English.
- **Model Size:** Choose the model size appropriate for your system.
- **Server Configuration:** Customize the server connection by entering a custom IP and port, or use the default buttons to set `localhost` and `9090`.

---


## Summary

This extension simplifies real-time audio transcription by combining advanced transcription technology with flexible server configuration. Whether you stick with the default settings or customize the server IP and port, Audio Transcription is designed to provide a seamless, real-time experience for transcribing audio directly in your browser.
