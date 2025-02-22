# Audio Transcription for Chrome/Chromium/Microsoft Edge 1.2.8

Audio Transcription is a Chrome/Chromium/Microsoft Edge extension that allows users to capture any audio playing in the current tab and transcribe it in real time using OpenAI Whisper, with a local server running on the user's computer. The user has the option to choose from all languages supported by OpenAI’s Whisper transcription AI, translate any language into English, and enable voice activity detection to avoid sending audio to the server when there is no speech.

This is a forked version with some aesthetic changes and enhancements, designed specifically for use with a local server running WhisperLive. You need to install [WhisperLive](https://github.com/collabora/WhisperLive). It supports Linux, Windows through WSL2, and macOS ARM (Intel versions do not work).


## Loading and running the extension
- Install WhisperLive (at least version 0.6.2):
```
pip3 install "whisper-live>=0.6.2"
```
or the alternative is downloading WhisperLive GitHub repository:
```
git clone https://github.com/collabora/WhisperLive.git

```
```
cd WhiperLive
```
```
pip install .
```
If an error occurs, i.e. with Python 3.12, because "Could not find a version that satisfies the requirement onnxruntime==1.16.0 (from whisper-live)", then you have to manually update the setup.py file, changing "onnxruntime==1.17.0",

- Download this repository, you can use the following command:
```
git clone https://github.com/antor44/livestream_video.git
```
- Change to the directory Audio-Transcription-Chrome:
```
cd livestream_video/Audio-Transcription-Chrome
```
- Run a local WhisperLive server:
```
./WhisperLive_server.sh
```
- Open the Google Chrome/Chromium/Microsoft Edge browser.
- Type chrome://extensions in the address bar and press Enter.
- Enable the Developer mode toggle switch located in the top right corner.
- Click the Load unpacked button.
- Browse to the location where you cloned the repository files and select the ```Audio-Transcription-Chrome``` folder.
- The extension should now be loaded and visible on the extensions page.
- Play any audio or video on a webpage, select a language and a model according to your computer power. There are models for English language and multilingual. Then click the 'Start Capture' button on the extension. When a model is selected for the first time, the file will be downloaded. It will only be downloaded the first time it is used.


For Windows installations only: The local server can only be installed through Windows Subsystem for Linux (WSL2). Before installing WhisperLive on Ubuntu 22.04 within Windows WSL2, you need to install PortAudio by running:
```
apt-get install portaudio19-dev python3-all-dev
```  
Then install WhisperLive and run ./WhisperLive_server.sh within the Linux virtual environment.

Once WhisperLive is installed, you can run the server in the Linux virtualized environment while using the extension in the Windows version of Google Chrome. To do this, copy or download this repository (or the extension directory) to a Windows folder and install it in Google Chrome on Windows.

Make sure the server script is running and that audio is playing in Chrome before activating the "Start Capture" button in the extension.

#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/Chrome_extension1.jpg)
#


## Real time transcription with OpenAI-whisper
We use OpenAI-whisper model to process the audio continuously and send the transcription back to the client. We apply a few optimizations on top of OpenAI's implementation to improve performance and run it faster in a real-time manner. To this end, we used [faster-whisper](https://github.com/guillaumekln/faster-whisper) which is 4x faster than OpenAI's implementation.

This Chrome extension allows you to send audio from your browser to a server for transcribing the audio in real time. It can also incorporate voice activity detection on the client side to detect when speech is present, and it continuously receives transcriptions of the spoken content from the server. You can select from the options menu if you want to run the speech recognition.


## Implementation Details

### Capturing Audio
To capture the audio in the current tab, we used the chrome `tabCapture` API to obtain a `MediaStream` object of the current tab.

### Options
When using the Audio Transcription extension, you have the following options:
 - **Language**: Select the target language for transcription or translation. You can choose from a variety of languages supported by OpenAI-whisper.
 - **Task:** Choose the specific task to perform on the audio. You can select either "transcribe" for transcription or "translate" to translate the audio to English.
 - **Model Size**: Select the whisper model size to run the server with.

### Getting Started
- Make sure the transcription server is running properly.
- Just click on the Chrome Extension which should show 2 options
  - **Start Capture** : Starts capturing the audio in the current tab and sends the captured audio to the server for transcription. This also creates an element to show the transcriptions recieved from the server on the current tab.
  - **Stop Capture** - Stops capturing the audio.

