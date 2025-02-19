# Audio Transcription for Chrome v.1.04 (fork)

Audio Transcription is a Chrome extension that allows users to capture any audio playing on the current tab and transcribe it using OpenAI-whisper in real time. Users will have the option to do voice activity detection as well to not send audio to server when there is no speech.

This is a forked version with some aesthetic changes and enhancements, designed specifically for use with a local server running WhisperLive. You need to install [WhisperLive](https://github.com/collabora/WhisperLive). It supports Linux, Windows through WSL2, and macOS ARM (Intel versions do not seem to work).

Before installing WhisperLive on Ubuntu 22.04 on Windows WSL2, you need to install portaudio:
```
apt-get install portaudio19-dev python-all-dev
```
You can run the server in a Linux virtualized environment and use the extension in the Google Chrome Windows version. To do this, copy or download this repository or the extension directory to a Windows directory and install it in Google Chrome on Windows. Make sure to run the server script and play some audio in Chrome before activating the 'Start capture' button on the extension.

## Loading and running the extension
- Install WhisperLive:
```
pip3 install whisper-live
```
- Run a local WhisperLive server:
```
./WhisperLive_server.sh
```
- Open the Google Chrome browser.
- Type chrome://extensions in the address bar and press Enter.
- Enable the Developer mode toggle switch located in the top right corner.
- Clone this repository
- Click the Load unpacked button.
- Browse to the location where you cloned the repository files and select the ```Audio Transcription``` folder.
- The extension should now be loaded and visible on the extensions page.
- Play any audio or video on a webpage, then click the ```Start Capture``` button on the extension.


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


## Note
The extension relies on a properly running transcription server.
