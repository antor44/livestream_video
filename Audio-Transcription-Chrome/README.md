# Audio Transcription for Chrome/Chromium/Microsoft Edge 1.6.2

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

- Install WhisperLive (at least version 0.6.3):
```
pip3 install "whisper-live>=0.6.3"
```
Or the alternative installation by downloading the WhisperLive GitHub repository:

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

## FAQ

**Q: What is a localhost server? Could I use the extension from the internet to connect to my server?**

A: A localhost server is one running on your own PC, using loopback ports. The Chrome extension uses one port to communicate with this server, which transcribes the audio played on a webpage. Alternatively, the server can transcribe multiple audio streams from different web browsers running on your PC simultaneously.

The loopback interface is a virtual network interface for each user that, by default, is not accessible from outside your computer. However, you can configure the server and the extension to connect from different PCs on your LAN. It is also possible to connect the Chrome extension to the server via the Internet, although this requires additional network settings for your operating system and router.

**Q: Are connections to the server secure? Is it safe to use the extension from the Internet to connect to my server?**

A: The WhisperLive server uses WebSockets without secure connections, so both audio clips and transcribed texts are transmitted unencrypted. This is not a problem on a local server or when used on a LAN. If security is required, you can connect clients to the server via SSH tunnels, which provide sufficient security.

**Q: Can the server run with GPU acceleration?**

A: WhisperLive Server supports the faster‑whisper backend accelerated by a GPU, which should be automatically detected as long as the system has a compatible version of the Nvidia CUDA libraries installed. It also supports the TensorRT backend for Nvidia graphics cards, which is generally more efficient than faster‑whisper. See the WhisperLive documentation for detailed configuration instructions.

Keep in mind that although WhisperLive supports multiple concurrent clients on a single GPU, there are limitations due to the limited amount of available VRAM and compute capacity. Primarily, the ability to handle multiple clients depends on the available VRAM. Notably, the server can be configured in single‑model mode to optimize VRAM usage, but in that case all clients must use the same model size.

Additionally, WhisperLive does not include a built-in load balancing system; there are no mechanisms to distribute the load among multiple server instances, so an external load balancing solution must be implemented.

**Q: What quality of transcription can I expect when using only a low-level processor?**

A: This Chrome extension program is based on WhisperLive, which is based on faster-whisper, a highly optimized implementation of OpenAI's Whisper AI. The performance of the transcription largely depends on this software. For English, you can expect very good transcriptions of video or audio streams even on low-end or older PCs, including those that are at least 10 years old. You can easily configure the application with models such as small.en or base.en, which offer excellent transcriptions for English. Even the tiny.en model, despite its small size, provides great results. However, transcriptions of other major languages are not as good with small models, and minority languages do not perform well at all. For these, you will need a better CPU or a supported GPU.

**Q: Some transcribed texts are difficult to read when words keep changing, and some phrases appear to be cut off. Why is that?**

A: The extension relies on the output texts from the WhisperLive server, which uses a special technique to achieve real-time transcriptions. It first rapidly transcribes the most recent chunk of audio, and then re-transcribes them with better context. This causes frequent changes in the transcribed words. This is inherent to Whisper AI, which is not designed for real-time transcriptions. Processing online videos is very challenging due to the somewhat random nature of this transcription algorithm. Moreover, the output format and length of the transcribed texts from the WhisperLive server are even more unpredictable.

Currently, the extension uses a very simple algorithm to handle the phrases that are being displayed and stored. In the near future, we plan to address these instability issues in the visualization of the transcriptions. The solutions include:

- **Managing the Dynamics of Transcriptions to Reduce Instability:**  
  A sliding window or buffer with a look-ahead time of 1–2 seconds can be used before considering a phrase as final, allowing additional context to refine the transcription. This introduces some latency, but it may be acceptable depending on the user's needs.  
  Alternatively, a system of "interim and final results" can be implemented, where only the final results are shown to the user after they have stabilized.

- **Improving the Text Format:**  
  The current solution in WhisperLive's own extension version is to join all sentences with only spaces between words, resulting in difficult-to-read texts. Simple formatting rules could be applied: inserting line breaks and adding basic punctuation based on common patterns. A post-processing step can be implemented using algorithms or lightweight correction models to correct common errors. Heuristic rules could be used to predict the most likely sequence of words, although this must be efficient for real-time processing. For example, correcting repeated or incoherent words using local context.
