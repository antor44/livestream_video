# Audio Transcription for Chrome/Chromium/Microsoft Edge 2.3.0

## Using the Extension

### Prepare the Server:

Ensure that the WhisperLive server is running.

### Play Audio:

Play any audio or video on a webpage.

### Open the Extension:

Click the extension icon to open the options popup.

### Configure Your Options:

The UI is divided into several sections to give you full control over transcription and translation:

- **General Settings:**
  - **Speech (TTS) Speed & Enable TTS:** Enable Text-to-Speech to have the extension read the translated text aloud in real time. You can adjust the reading speed.
  - **Show in Standalone Window:** Choose between displaying the text in a floating overlay inside the webpage, or in a dedicated, resizable standalone popup window.
  - **Voice Activity Detection (VAD):** Enable this to stop processing audio during silent periods, saving CPU/GPU resources.

- **Audio Server:**
  - Enter a custom server IP address and port (default is `localhost` and `9090`).
  - Click **Reset Default** to easily revert to local settings.

- **Transcription Settings:**
  - **Audio Language:** Select the source language of the audio, or leave it on "Auto Detect".
  - **Whisper Task:** Choose between "Transcribe" (text in the original language) or "Translate" (direct Whisper translation to English).
  - **Model Size:** Pick the model size that suits your system’s hardware (from Base to Large-v3).
  - **Text Formatting:** Choose from "Raw Segments", "Joined Text", or "Advanced Paragraphs" to make the output more readable.

- **Gemini Translation (New in v2.3.0):**
  - **Enable Gemini Translation:** Check this to activate real-time translation powered by Google Gemini.
  - **Gemini API Key:** Paste your Google Gemini API key (you can get one for free from Google AI Studio).
  - **Gemini Model:** Select the desired model (e.g., `gemini-3-flash-preview`, `gemini-2.5-pro`).
  - **Target Language:** Select the language you want to translate the text into.
  - **Display Mode:** Choose how to view the text ("Original Only", "Translation Only", or "Side by Side").

### Start Transcription:

Click **Start Capture** to begin capturing audio and sending it to the server. The first time a model is selected, necessary files will be downloaded automatically. You can monitor the active settings and connection status in the real-time status bar at the top of the transcription window.

### Stop Transcription:

Click **Stop Capture** to end the session.

## Windows Installation (WSL2)

For Windows users, the local server runs through Windows Subsystem for Linux (WSL2):

1. Install PortAudio inside WSL2:
   ```sh
   sudo apt-get install portaudio19-dev python3-all-dev
   ```
2. Install WhisperLive and run `./WhisperLive_server.sh` within your Linux environment.
3. Use the extension in the Windows version of Chrome/Chromium/Microsoft Edge by copying or downloading this repository (or just the extension directory) to a Windows folder and loading it via the **Load unpacked** option.

---
## Screenshot

![Screenshot](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/Chrome_extension1.jpg)

---

## FAQ

**Q: What is a localhost server? Could I use the extension from the internet to connect to my server?**

A: A localhost server is one running on your own PC. The Chrome extension uses one port to communicate with this server, which transcribes the audio played on a webpage. Alternatively, the server can transcribe multiple audio streams from different web browsers running on your PC simultaneously.

The loopback interface is a virtual network interface for each user that, by default, is not accessible from outside your computer. However, you can configure the server and the extension to connect from different PCs on your LAN. It is also possible to connect the Chrome extension to the server via the Internet, although this requires additional network settings for your operating system and router.

**Q: Are connections to the server secure? Is it safe to use the extension from the Internet to connect to my server?**

A: The WhisperLive server uses WebSockets without secure connections, so both audio clips and transcribed texts are transmitted unencrypted. This is not a problem on a local server or when used on a LAN. If security is required, you can connect clients to the server via SSH tunnels, which provide sufficient security.

**Q: Can the server run with GPU acceleration?**

A: WhisperLive Server supports the faster‑whisper backend accelerated by a GPU, which should be automatically detected as long as the system has a compatible version of the Nvidia CUDA libraries installed. It also supports the TensorRT backend for Nvidia graphics cards, which is generally more efficient than faster‑whisper. See the WhisperLive documentation for detailed configuration instructions.

Keep in mind that although WhisperLive supports multiple concurrent clients on a single GPU, there are limitations due to the limited amount of available VRAM and compute capacity. Primarily, the ability to handle multiple clients depends on the available VRAM. Notably, the server can be configured in single‑model mode to optimize VRAM usage, but in that case all clients must use the same model size.

Additionally, WhisperLive does not include a built-in load balancing system; there are no mechanisms to distribute the load among multiple server instances, so an external load balancing solution must be implemented.

**Q: What quality of transcription can I expect when using only a low-level processor?**

A: This Chrome extension program is based on WhisperLive, which is based on faster-whisper, a highly optimized implementation of OpenAI's Whisper AI. The performance of the transcription largely depends on this software. For English, you can expect very good transcriptions of video or audio streams even on low-end or older PCs, including those that are at least 10 years old. You can easily configure the application with models such as small.en or base.en, which offer excellent transcriptions for English. Even the tiny.en model, despite its small size, provides great results. However, transcriptions of other major languages are not as good with small models, and minority languages do not perform well at all. For these, you will need a better CPU or a supported GPU.

**Q: Some transcribed texts are difficult to read when words keep changing, and some phrases disappear or appear to be cut off. Why is that?**

A: The extension relies on the output texts from the WhisperLive server, which uses a special technique to achieve real-time transcriptions. It first rapidly transcribes the most recent chunk of audio, and then re-transcribes them with better context. This causes frequent changes in the transcribed words. This is inherent to Whisper AI, which is not designed for real-time transcriptions. Processing online videos is very challenging due to the somewhat random nature of this transcription algorithm. Moreover, the output format and length of the transcribed texts from the WhisperLive server are even more unpredictable.

Currently, the extension uses a very simple algorithm to handle the phrases that are being displayed and stored. In the near future, we plan to address these stability issues in the visualization of transcriptions. However, it needs to be a solution that does not consume too many resources in order to maintain the philosophy of this application being able to run on as many computers as possible. The solutions include:

- **Managing the Dynamics of Transcriptions to Reduce Instability:**  
  A sliding window or buffer with a look-ahead time of 1–2 seconds can be used before considering a phrase as final, allowing additional context to refine the transcription. This introduces some latency, but it may be acceptable depending on the user's needs.  
  Alternatively, a system of "interim and final results" can be implemented, where only the final results are shown to the user after they have stabilized.

- **Improving the Text Format:**  
  The current solution in WhisperLive's own extension version is to join all sentences with only spaces between words, resulting in difficult-to-read texts. Simple formatting rules could be applied: inserting line breaks and adding basic punctuation based on common patterns. A post-processing step can be implemented using algorithms or lightweight correction models to correct common errors. Heuristic rules could be used to predict the most likely sequence of words, for example, correcting repeated or incoherent words using local context, although this must be efficient for real-time processing.
