# Audio Transcription for Chrome/Chromium/Microsoft Edge 2.7.0

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
  - **Speech (TTS) Speed & Enable TTS:** Enable Text-to-Speech to have the extension read the text aloud in real time. If translation is active, it reads the translated text. If it is disabled, it reads the original Whisper transcription (using the selected Audio Language, or English if Whisper's task is set to "Translate"). You can also adjust the reading speed. **Note: This feature uses the chrome.tts extension API. On Windows, it uses the voices installed via SAPI 5 (configured in your OS). On macOS, it uses the native macOS speech voices. On Linux: Google Chrome bundles its own internal eSpeak-NG engine (fixed quality, limited language support); Microsoft Edge uses Microsoft's online Neural TTS voices (high quality, broad language support, requires internet); Chromium has no built-in engine but works if a TTS engine extension like Piper is installed — without one, no audio will be produced.**
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

Run the server (optionally accepts some arguments):

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
> [!TIP]
> You can edit the **`WhisperLive_server.sh`** bash script to optionally add the environment activation command. For example, add it at the beginning, just below the line `#!/bin/bash`: `source ~/python-environments/whisper-live/bin/activate`.

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

**Q: How do I set up WhisperLive with TensorRT acceleration using Docker, and what should I do if I get CUDA errors?**

Docker is the recommended (and easiest) way to run the TensorRT backend. It bundles the exact versions of CUDA, TensorRT-LLM, and all dependencies that have been tested together — no manual dependency management needed.

#### Step 1 — Prerequisites

- NVIDIA GPU with CUDA support (tested on RTX 30xx/40xx)
- [Docker](https://docs.docker.com/get-docker/) installed
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed
- **~10–12 GB free disk space** during compilation (2.9 GB model weights + ~1.9 GB checkpoint + 3.1 GB engines + build buffers). After compilation you can delete the `.pt` file and the `large-v2-weights/` directory to recover space.

After installing Docker, add your user to the `docker` group so you can run containers without `sudo`:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

> **Note:** `newgrp docker` applies the group change to the current terminal session immediately. For it to apply system-wide to all future sessions (including when you open a new terminal or reboot), you need to **log out and log back in** once.

Verify everything works before starting:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

If you see your GPU listed, you're ready.

#### Step 2 — Download the Whisper model weights

```bash
mkdir -p ~/whisper-engines
wget -O ~/whisper-engines/large-v2.pt \
  https://openaipublic.azureedge.net/main/whisper/models/81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524/large-v2.pt
```

The file is ~2.9 GB. You only need to do this once.

#### Step 3 — Compile the TensorRT engines

Engines are GPU-specific and must be compiled once on your machine. They are saved to `~/whisper-engines/` on your host and reused every time the server starts.

```bash
# Start a temporary build container
docker run -it --gpus all \
  -v ~/whisper-engines:/engines \
  ghcr.io/collabora/whisperlive-tensorrt:latest bash
```

Inside the container, run these commands:

```bash
# Link the downloaded weights and convert the checkpoint
cd /app/TensorRT-LLM-examples/whisper
mkdir -p assets
ln -sf /engines/large-v2.pt assets/large-v2.pt
mkdir -p /engines/tmp && export TMPDIR=/engines/tmp

python3 convert_checkpoint.py \
    --output_dir /engines/large-v2-weights \
    --model_name large-v2

# Compile the encoder
mkdir -p /engines/large-v2/encoder
trtllm-build \
    --checkpoint_dir /engines/large-v2-weights/encoder \
    --output_dir /engines/large-v2/encoder \
    --moe_plugin disable \
    --enable_xqa disable \
    --max_batch_size 1 \
    --gemm_plugin disable \
    --bert_attention_plugin float16 \
    --max_input_len 3000 \
    --max_seq_len 3000

# Compile the decoder
# max_beam_width=1 is required — see CUDA errors section below for details
mkdir -p /engines/large-v2/decoder
trtllm-build \
    --checkpoint_dir /engines/large-v2-weights/decoder \
    --output_dir /engines/large-v2/decoder \
    --moe_plugin disable \
    --enable_xqa disable \
    --max_beam_width 1 \
    --max_batch_size 1 \
    --max_seq_len 200 \
    --max_input_len 14 \
    --max_encoder_input_len 3000 \
    --gemm_plugin float16 \
    --bert_attention_plugin float16 \
    --gpt_attention_plugin float16

# Verify both engines were created successfully
ls -lh /engines/large-v2/encoder/rank0.engine
ls -lh /engines/large-v2/decoder/rank0.engine
exit
```

Compilation time varies by GPU — typically fast on modern GPUs (RTX 30xx/40xx). When done, your host will have:

```
~/whisper-engines/
└── large-v2/
    ├── encoder/rank0.engine   (~1.2 GB)
    └── decoder/rank0.engine   (~1.9 GB)
```

Optional — recover disk space after compilation:

```bash
rm -rf ~/whisper-engines/large-v2-weights
rm -f ~/whisper-engines/large-v2.pt
```

#### Step 4 — Start the server

```bash
./WhisperLive_server.sh docker trt --model large-v2 --multilingual
```

You should see:

```
🚀 INFO  Server ready → host=0.0.0.0  port=9090  backend=tensorrt
```

The server is now accepting WebSocket connections on `ws://localhost:9090`.

> **Why `--host 0.0.0.0` inside Docker?**
> Inside a container, `0.0.0.0` means "listen on all container interfaces" — it does not expose the service to the outside world. Docker's `-p 127.0.0.1:9090:9090` flag (used in the `docker run` command inside WhisperLive_server.sh) controls what is reachable from the host. The server is only accessible from your own machine unless you explicitly open it to the network or use `./WhisperLive_server.sh --host <ip>` (a different argument here), which specifies the Host/IP to bind to (default: 127.0.0.1); i.e., 0.0.0.0 exposes it to the LAN/internet, although this will depend too on your router and other network related stuff.

> **Why `--multilingual`?**
> Without this flag the TensorRT backend defaults to English-only transcription even if the audio is in another language.

---

#### CUDA errors — causes and fixes

If you encounter `CUDA error: an illegal memory access was encountered`, the verified fix is compiling the decoder with `--max_beam_width 1`. Higher values (`2`, `4`) triggered this error consistently during testing with the Collabora TensorRT image (`TensorRT-LLM 0.15.0.dev2024111200`) on Ada Lovelace GPUs (RTX 40xx, sm_89). The root cause may vary by TensorRT-LLM version and GPU architecture — if you experience the error with `beam_width=1`, try adding `CUDA_LAUNCH_BLOCKING=1` to get a detailed trace (see below).

If you need to recompile only the decoder without starting from scratch:

```bash
# Enter the build container with the engines volume mounted
docker run -it --gpus all \
  -v ~/whisper-engines:/engines \
  ghcr.io/collabora/whisperlive-tensorrt:latest bash
```

Inside the container:

```bash
# Note: this requires /engines/large-v2-weights/ to still exist.
# If you deleted it after the initial compilation, you must repeat the
# convert_checkpoint.py step first (re-downloading large-v2.pt if needed).

rm -rf /engines/large-v2/decoder
mkdir -p /engines/large-v2/decoder

trtllm-build \
    --checkpoint_dir /engines/large-v2-weights/decoder \
    --output_dir /engines/large-v2/decoder \
    --moe_plugin disable \
    --enable_xqa disable \
    --max_beam_width 1 \
    --max_batch_size 1 \
    --max_seq_len 200 \
    --max_input_len 14 \
    --max_encoder_input_len 3000 \
    --gemm_plugin float16 \
    --bert_attention_plugin float16 \
    --gpt_attention_plugin float16

exit
```

Then restart the server normally with `./WhisperLive_server.sh docker trt`.

**Note on `--beam-size`:** the `--beam-size` option in `run_server.py` has **no effect** on the TensorRT backend. Beam width is fixed at engine compile time via `--max_beam_width`. Using `1` enables greedy decoding — for live transcription with Whisper large-v2 the accuracy difference versus beam search is negligible, while latency and VRAM usage are lower.

To get a detailed CUDA error trace for debugging (slows down inference — remove afterwards):

```bash
# Add -e CUDA_LAUNCH_BLOCKING=1 to the docker run command in WhisperLive_server.sh
```

**Optional — GPU persistence mode:**
Running `sudo nvidia-smi -pm 1` keeps the NVIDIA driver loaded in memory at all times, which can reduce latency on first inference. This is a general GPU server best practice and is unrelated to the CUDA errors described above.

---

#### Configurable options in `WhisperLive_server.sh`

Edit the `# Configuration` block at the top of the script to change defaults:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `9090` | WebSocket port |
| `MAX_CLIENTS` | `100` | Max simultaneous clients |
| `MAX_CONNECTION_TIME` | `604800` | Max session duration in seconds (7 days) |
| `MODEL` | `large-v2` | Whisper model name |
| `ENGINES_DIR` | `~/whisper-engines` | Host path where compiled engines are stored |

Or pass flags at runtime:

```bash
./WhisperLive_server.sh docker trt --model large-v2 --multilingual --port 9091
```

**Q: What quality of transcription can I expect when using only a low-level processor?**

A: This Chrome extension program is based on WhisperLive, which is based on faster-whisper, a highly optimized implementation of OpenAI's Whisper AI. The performance of the transcription largely depends on this software. For English, you can expect very good transcriptions of video or audio streams even on low-end or older PCs, including those that are at least 10 years old (Intel Haswell). You can easily configure the application with models such as small.en or base.en, which offer excellent transcriptions for English. However, transcriptions of other major languages are not as good with small models, and minority languages do not perform well at all. For these, you will need a better CPU or a supported GPU.

**Q: Some transcribed texts are difficult to read because words keep changing, and some phrases disappear or appear to be cut off. Why does this happen?**

A: The extension displays the transcription output generated by the WhisperLive server, which approximates real-time transcription using incremental decoding. In this approach, the most recent audio chunk is transcribed quickly and then repeatedly reprocessed as additional context becomes available. As a result, previously generated words may be revised or replaced, causing visible changes in the displayed text.

This behavior is inherent to Whisper-based models. Whisper was originally designed for batch transcription rather than low-latency streaming, so when it is adapted for real-time usage the intermediate results can be unstable.

In addition, the output produced by the WhisperLive server is not strictly structured for client-side stabilization. The server emits blocks of text that may change frequently, contain recognition errors, and do not follow a fixed or predictable size. These blocks also lack reliable timestamps that could be used to anchor segments on the client side. From the perspective of the extension, this means the transcription stream behaves like a partially unstable and non-deterministic text sequence.

Currently, the extension uses a relatively simple algorithm to manage the phrases that are displayed and stored. Future versions will aim to improve the stability and readability of the transcription output while keeping the computational overhead low. Maintaining a lightweight implementation is important so the extension can run efficiently on a wide range of computers.

Current and planned approaches include:

- **Managing Transcription Dynamics to Reduce Instability (partially implemented and currently used together with the formatting approach)**  
  A sliding window or buffering mechanism with a short look-ahead delay (for example, 1–2 seconds) could be used before considering a phrase final. This allows additional context to stabilize the transcription.  
  Another option is implementing an *interim vs final results* model, where only stabilized segments are shown as final output.

- **Improving Text Formatting and Post-Processing (partially implemented and currently used together with the transcription dynamics approach)**  
  Basic formatting rules could be applied, such as inserting line breaks or punctuation based on simple patterns.  
  A lightweight post-processing stage could also help correct common transcription artifacts. Heuristic rules may improve local coherence by detecting repeated or inconsistent word sequences and adjusting them using nearby context, provided the processing remains efficient enough for real-time operation.
