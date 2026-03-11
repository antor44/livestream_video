# Audio Transcription for Chrome/Chromium/Microsoft Edge 2.5.0

## Using the Extension

### Prepare the Server:

Ensure that the [WhisperLive](https://github.com/collabora/WhisperLive) server is running.

### Play Audio:

Play any audio or video on a webpage.

### Open the Extension:

Click the extension icon to open the options popup.

### Configure Your Options:

The UI is divided into several sections to give you full control over transcription and translation:

- **General Settings:**
  - **Speech (TTS) Speed & Enable TTS:** Enable Text-to-Speech to have the extension read the text aloud in real time. If translation is active, it reads the translated text. If it is disabled, it reads the original Whisper transcription (using the selected Audio Language, or English if Whisper's task is set to "Translate"). You can also adjust the reading speed. 
  *Note: The extension uses the default local internal TTS engine of your Chrome browser. For it to work correctly, you must have the corresponding text-to-speech language voices installed and configured in your operating system.*
  - **Show in Standalone Window:** Choose between displaying the text in a floating overlay inside the webpage, or in a dedicated, resizable standalone popup window.
  - **Voice Activity Detection (VAD):** Enable this to stop processing audio during silent periods, saving CPU/GPU resources.

- **WhisperLive Server:**
  - Enter a custom server IP address and port to connect to your transcription server (default is `localhost` and `9090`).
  - Click **Reset Default** to easily revert to local settings.

- **Transcription Settings:**
  - **Audio Language:** Select the source language of the audio, or leave it on "Auto Detect". *Tip: If you select a language different from the one spoken in the audio, larger Whisper models (like large-v2 or large-v3) will often provide a very good direct translation into the selected language natively, without needing to use external translation features.*
  - **Whisper Task:** Choose between "Transcribe" (text in the original language) or "Translate" (direct Whisper translation to English).
  - **Model Size:** Pick the model size that suits your system’s hardware (from Base to Large-v3).
  - **Text Formatting:** Choose from "Raw Segments", "Joined Text", or "Advanced Paragraphs" to make the output more readable.

- **Gemini & Google Translation:**
  - **Enable Translation:** Check this to activate real-time translation.
  - **Gemini API Key:** If you intend to use a Gemini model, paste your Google Gemini API key here (you can get one for free from Google AI Studio).
  - **Translation Model (Free Option Available):** Select your desired engine. You can choose **Google Translate** for completely free translations without an API key, or select a Gemini model (e.g., `gemini-3-flash-preview`).
  - **Automatic Fallback:** If you select a Gemini model and the API fails, times out, or throws an error, the extension will automatically use the free Google Translate as a fallback. Translations produced by this fallback are marked with a `⁺` (U+207A) symbol at the beginning of the text.
  - **Target Language:** Select the language you want to translate the text into.
  - **Display Mode:** Choose how to view the text ("Original Only", "Translation Only", or "Side by Side").

**Important Note on Models:**
While many models such as the `gemini-flash-lite-preview` family offer generous free tiers, advanced models like `gemini-3.1-pro` are typically available only through the paid tier of the Gemini API. The paid API operates on a pay-per-use basis: if you don't use it, you don't pay. Please check your billing status if you plan to use Pro models or expect intensive usage of Flash models. Under normal usage, the cost is typically no more than a few cents per day, even with relatively heavy use.

**Model Recommendations for High-Quality Translate or Corrections in the Same Language:**
*   **Paid API key recommended:** The Free Tier can work reliably for flash-lite models, recommended only when both source and destination are major languages.
*   For reliable, high-quality subtitles or for long sessions, use at least the `gemini-3-flash` model. It provides good results for major-language translations and for improving same-language transcription.
*   Use `gemini-3.1-pro` when either the source or destination language is non-major.
*   *Note: Google plans to discontinue Gemini 2.5 Pro and Flash 2.5 models on June 17, 2026.*

### Start Transcription:

Click **Start Capture** to begin capturing audio and sending it to the server. The first time a model is selected, necessary files will be downloaded automatically. You can monitor the active settings and connection status in the real-time status bar at the top of the transcription window.

### Window Customization & History:
The transcription windows (both in-page overlay and standalone) give you full control:
- You can freely move and resize the windows to fit your layout.
- You can increase or decrease the font size of the text.
- All processed text is saved in a continuous history, and you can easily copy the entire transcript (both original and translated) to your clipboard with a single click.

### Stop Transcription:

Click **Stop Capture** to end the session.

#

## Installing the WhisperLive Server

Depending on your operating system configuration, you may need to create a Python virtual environment using either Anaconda or virtualenv. You must activate this environment to run the WhisperLive server.

For virtualenv:

```sh
sudo apt install virtualenv
```

Or for macOS:

```sh
brew install virtualenv
```

Then:

```sh
mkdir ~/python-environments
virtualenv ~/python-environments/whisper-live
source ~/python-environments/whisper-live/bin/activate
```

Install WhisperLive (at least version 0.6.3):

```sh
pip3 install whisper-live
```

Or install manually by cloning the WhisperLive GitHub repository:

```sh
git clone https://github.com/collabora/WhisperLive.git
cd WhisperLive
pip3 install .
```

This may take several minutes.

Download this repository using:

```sh
git clone https://github.com/antor44/livestream_video.git
```

## Running the WhisperLive Server

Before using the extension, ensure the local WhisperLive server is running.

Change to the directory:

```sh
cd livestream_video/Audio-Transcription-Chrome
```

Run the server:

```sh
./WhisperLive_server.sh
```

Or, if using a Python virtual environment:

```sh
source ~/python-environments/whisper-live/bin/activate && ./WhisperLive_server.sh
```

If a "numpy version 2" error occurs:

```sh
pip3 install "numpy<2"
```

*You can edit the bash script **`WhisperLive_server.sh`** to modify the default Server IP and Port.*

## Installing the Extension

1. Open Google Chrome, Chromium, or Microsoft Edge.
2. In the address bar, type `chrome://extensions` and press Enter.
3. Enable Developer mode (toggle switch in the top right corner). Recent versions of Chrome require this switch enabled for extensions not signed by Google.
4. Click the **Load unpacked** button.
5. Browse to the folder where you cloned this repository and select the `Audio-Transcription-Chrome` folder (inside `livestream_video`).
6. The extension should now appear on the extensions page.

## Windows Installation (WSL2)

For Windows users, the local server runs through Windows Subsystem for Linux (WSL2):

1. Install PortAudio inside WSL2:
   ```sh
   sudo apt-get install portaudio19-dev python3-all-dev
   ```
2. Install WhisperLive and run `./WhisperLive_server.sh` within your Linux environment.
3. Use the extension in the Windows version of Chrome/Chromium/Microsoft Edge by copying or downloading this repository (or just the extension directory) to a Windows folder and loading it via the **Load unpacked** option.

---
## Screenshots

![Screenshot](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/Chrome_extension1.jpg)

![Screenshot](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/Chrome_extension2.jpg)

![Screenshot](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/Chrome_extension3.jpg)
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

A: This Chrome extension program is based on WhisperLive, which is based on faster-whisper, a highly optimized implementation of OpenAI's Whisper AI. The performance of the transcription largely depends on this software. For English, you can expect very good transcriptions of video or audio streams even on low-end or older PCs, including those that are at least 10 years old. You can easily configure the application with models such as small.en or base.en, which offer excellent transcriptions for English. However, transcriptions of other major languages are not as good with small models, and minority languages do not perform well at all. For these, you will need a better CPU or a supported GPU.

**Q: Some transcribed texts are difficult to read when words keep changing, and some phrases disappear or appear to be cut off. Why is that?**

A: The extension relies on the output texts from the WhisperLive server, which uses a special technique to achieve real-time transcriptions. It first rapidly transcribes the most recent chunk of audio, and then re-transcribes them with better context. This causes frequent changes in the transcribed words. This is inherent to Whisper AI, which is not designed for real-time transcriptions. Processing online videos is very challenging due to the somewhat random nature of this transcription algorithm. Moreover, the output format and length of the transcribed texts from the WhisperLive server are even more unpredictable.

Currently, the extension uses a very simple algorithm to handle the phrases that are being displayed and stored. In the near future, we plan to address these stability issues in the visualization of transcriptions. However, it needs to be a solution that does not consume too many resources in order to maintain the philosophy of this application being able to run on as many computers as possible. The solutions include:

- **Managing the Dynamics of Transcriptions to Reduce Instability:**  
  A sliding window or buffer with a look-ahead time of 1–2 seconds can be used before considering a phrase as final, allowing additional context to refine the transcription. This introduces some latency, but it may be acceptable depending on the user's needs.  
  Alternatively, a system of "interim and final results" can be implemented, where only the final results are shown to the user after they have stabilized.

- **Improving the Text Format:**  
  Simple formatting rules could be applied: inserting line breaks and adding basic punctuation based on common patterns. A post-processing step can be implemented using algorithms or lightweight correction models to correct common errors. Heuristic rules could be used to predict the most likely sequence of words, for example, correcting repeated or incoherent words using local context, although this must be efficient for real-time processing.
