# playlist4whisper/livestream_video.sh and Audio Transcription for Chrome/Chromium/Microsoft Edge

## playlist4whisper & livestream_video.sh

`playlist4whisper` is a graphical application that allows you to easily manage and launch `livestream_video.sh`. It provides a user-friendly interface to configure all transcription and translation options, manage TV channel playlists, and store settings.

### Some Notable Features:

-   **Online Translation:** Translate transcriptions in real-time using either Google Translate or the high-quality Google Gemini API.
-   **Context Control for AI:** Fine-tune Gemini translations with context levels (0-3) to balance between literal accuracy and creative, context-aware fluency.
-   **Text-to-Speech (TTS):** Read translated text aloud for a more immersive experience.
-   **Save Session Transcripts:** Save the complete transcription and translation logs from the current session with a single click.
-   **Subtitle Generation:** Automatically create `.srt` subtitle files from local media files.
-   **Subtitle Video Editor:** Integrated tool to cut and merge video segments, ideal for creating multilingual subtitles or refining timing.
-   **Timeshift:** A fully configurable timeshift feature, exclusive to the VLC player.
-   **Timeshift Recording:** Save and merge selected video segments directly from the timeshift buffer.
-   **Broad Service Support:** Access a wide range of video services through `streamlink` or `yt-dlp`.
-   **Multi-Platform:** Compatible with Linux, macOS, and Windows (via WSL2).

### Online Translation with Google Gemini API

The latest version introduces high-quality online translation using Google's Gemini AI models. This feature serves as a powerful alternative to the standard translation provided by `translate-shell`.

**Key Features:**

*   **Superior Quality:** Gemini models often provide more accurate and context-aware translations than traditional services.
*   **Model Selection:** You can choose from several available Gemini models, such as `gemini-2.5-flash-lite` (default) or the more powerful `gemini-2.5-pro`, directly from the application's UI.
*   **API Key Integration:** The system securely manages your Google Gemini API key.

#### Context Level Control

To further enhance translation quality, you can now control the amount of context the Gemini AI uses. This is crucial for achieving translations that are not only accurate but also fluent and coherent.

*   **Level 0 (Literal):** No context is used. Translates each segment independently. Best for simple, disconnected phrases.
*   **Level 1 (Minimal):** Uses the immediately preceding and succeeding segments for context. Good for general use.
*   **Level 2 (Standard - Default):** Uses a wider "window" of several surrounding segments. Excellent for understanding the flow of conversation.
*   **Level 3 (Creative):** Uses the same wide context as Level 2 but gives the AI permission to intelligently fix or complete fragmented sentences, which is ideal for live streams where words might be cut off.

You can select your preferred context level from the new dropdown menu in the "Online translation" section of the UI.

#### How to Enable Gemini Translation

##### 1. Obtain a Google Gemini API Key

*   Go to **[Google AI Studio](https://aistudio.google.com/)**.
*   Sign in with your Google account.
*   Click on **"Get API key"** and then **"Create API key"**.
*   Copy the generated key immediately.

##### 2. Provide the API Key to the Application

1.  In `playlist4whisper`, click the **"API Key"** button located in the "Online translation" section.
2.  Paste your key into the dialog box and click "OK". The key is saved in your configuration file.

##### 3. Configure and Run

1.  Check the **"Online"** box to enable online translation.
2.  Use the **"Engine"** dropdown menu to select your desired Gemini model.
3.  Use the **"Level"** dropdown menu to select your desired context level.

The script will now use the Gemini API for translations. If the API key is not found, it will automatically fall back to the standard `translate-shell` engine.

**Note:** Using the Gemini API is subject to Google’s pricing and usage policies. Please consult the [Google AI Platform pricing page](https://ai.google.dev/pricing) for details.

The Gemini API **free tier** is available with lower rate limits for testing purposes. Google AI Studio usage is completely free in all supported countries. The Gemini API **paid tier** provides higher rate limits, additional features, and different data handling.

</br>
Author: Antonio R. Version: 4.30 License: GPL 3.0
</br>
</br>

#

# Audio Transcription

Chrome/Chromium/Microsoft Edge extension (Firefox version not supported) that allows users to capture any audio playing in the current tab and transcribe it in real time using an implementation of OpenAI Whisper, with a local server running on the user's computer. The user has the option to choose from all languages supported by OpenAI’s Whisper transcription AI, translate any language into English, and enable voice activity detection to avoid sending audio to the server when there is no speech.

This is an application totally independent of playlist4whisper and livestream_video.sh, based on WhiperLive, an implementation of OpenAI Whisper different from whisper.cpp. This browser extension is a fork of a [WhisperLive extension](https://github.com/collabora/WhisperLive) with some aesthetic changes and enhancements, designed specifically for use with a local server running WhisperLive. You need to install WhisperLive and run a bash script to launch a local server. It supports Linux, Windows through WSL2 (Chrome/Chromium/Microsoft Edge on Windows is supported for the extension part), and macOS ARM (Intel versions do not work). For help and installation instructions, see the [README](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/README.md) file in its directory.

In this release, we have added various options for text output manipulation and improved the server configuration options that allow you to customize the server IP address and port.

</br>
</br>

![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV6.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV1.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV10.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/Audio-Transcription-Chrome/Chrome_extension1.jpg)
#

#
## playlist4whisper Quick start

playlist4whisper and livestream_video.sh is based on whisper.cpp and also supports OpenAI's Whisper. It depends on other executables and libraries. Please ensure that mpv, smplayer, translate-shell, ffmpeg, vlc, python3-tk, python3-pip, imageio, imageio-ffmpeg, Pillow, jq, curl, bc, and xterm are installed. 

To install whisper.cpp, choose one of these options (you can install all and choose any, or Whisper executables are prioritized, with ./build/bin/whisper-cli executable being the first choice):
```
pip3 install pywhispercpp
```
For macOS and linux with brew repository:
```
brew install whisper-cpp
```
or for OpenAI's Whisper (not fully supported, except for generating subtitles for local audio/video files):
```
pip3 install openai-whisper
```
For the latest version of whisper.cpp or to compile an accelerated version, follow the instructions provided at https://github.com/ggerganov/whisper.cpp

Finally, launch the app by entering the following command in the terminal. Make sure you are inside the whisper.cpp directory (cd ~/whisper.cpp) and that your Python environment is activated (source ~/python-environments/whisper/bin/activate), if required.
```
python3 playlist4whisper.py
```
*Before using VLC go to Tools->Preferences and Show setting: All. Then Interface->Main Interfaces-> Qt-> Uncheck: 'Resize interface to the native video size', and 'When to raise the interface'-> Never. Ensure that VLC is configured to repeat the playlist infinitely, not just the current file, and save the configurations.

*The required model files must be stored in the subdirectory ./models. They can be automatically downloaded using playlist4whisper (this feature is only supported for the compiled version of whisper.cpp), or you can follow the instructions provided at https://github.com/ggerganov/whisper.cpp/blob/master/models/README.md

*Please note that the model installed by playlist4whisper may not be optimized for an accelerated version of Whisper.cpp.

*OpenAI's Whisper automatically downloads the required model if it does not exist. Keep in mind that its format is different from the whisper.cpp model.


#
## Detailed installation for linux


1. Download and build whisper.cpp to a new directory following the instructions provided in the documentation at https://github.com/ggerganov/whisper.cpp

Download the source code of whisper.cpp from your home directory:

```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Change the default directory to the whisper.cpp directory, which is whisper.cpp:
```
cd whisper.cpp
```
Compile whisper.cpp for CPU mode:
```
make
```
Download some models:
```
make tiny.en
```
```
make base.en
```
```
make base
```
2. Download playlist4whisper and livestream_video.sh, you can use the following command:
```
git clone https://github.com/antor44/livestream_video.git
```
Stay where you executed the command, move all to whisper.cpp directory:
```
mv livestream_video/* ~/whisper.cpp
```
playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper.cpp.

This program depends on other Linux programs and their libraries, such as Python, whisper.cpp and mpv. For example, Ubuntu Linux users can install the following packages:
```
sudo apt-get install mpv smplayer translate-shell vlc ffmpeg make cmake python3-tk python3-pip jq curl bc xterm
```

You need to install some libraries via pip. One option is to install a python virtualenv:
```
sudo apt install virtualenv
```
Then:
```
mkdir ~/python-environments
virtualenv ~/python-environments/whisper
source ~/python-environments/whisper/bin/activate
```
And finally:
```
pip3 install imageio imageio-ffmpeg Pillow
```
Remember, in every session you need to run command 'source ~/python-environments/whisper/bin/activate' before executing playlist4whisper.py

For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp), for Twitch and Others streamlink is required (https://streamlink.github.io).

The easy way to install yt-dlp and streamlink:
```
pip3 install yt-dlp
pip3 install streamlink
```
or to create a Python virtual environment alongside Python applications, install pipx:
```
sudo apt-get install pipx
pipx install yt-dlp
pipx install streamlink
```

And to upgrade them:
```
pip3 install --upgrade yt-dlp
pip3 install --upgrade streamlink
```
or 
```
pipx upgrade yt-dlp
pipx upgrade streamlink
```

3. Finally, launch the app by entering the following command in the terminal. Make sure you are inside the whisper.cpp directory (cd ~/whisper.cpp) and that your Python environment is activated (source ~/python-environments/whisper/bin/activate), if required.
```
python3 playlist4whisper.py
```
Before using VLC go to Tools->Preferences and Show setting: All. Then Interface->Main Interfaces-> Qt-> Uncheck: 'Resize interface to the native video size', and 'When to raise the interface'-> Never. Ensure that VLC is configured to repeat the playlist infinitely, not just the current file, and save the configurations.

For multi-instances with SMPlayer: Go to Preferences - Interface - Instances, and turn off the option to use only one instance.
#
## Detailed Installation for macOS

You can run playlist4whisper.py on macOS by following these steps:

1. Install Homebrew by visiting https://brew.sh/ and following the installation instructions.

2. Once Homebrew is installed, open a terminal and install the required dependencies. Run the following commands:

```
brew install make
brew install cmake
brew install python3
brew install python-tk
brew install ffmpeg
brew install xquartz
brew install xterm
brew install vlc
brew install mpv
brew install smplayer
brew install translate-shell
brew install yt-dlp
brew install streamlink
brew install jq
```
You need to install some libraries via pip. One option is to install a python virtualenv:
```
brew install virtualenv
```
Then:
```
mkdir ~/python-environments
virtualenv ~/python-environments/whisper
source ~/python-environments/whisper/bin/activate
```
Finally:
```
pip3 install imageio imageio-ffmpeg Pillow
```
Remember, in every session you need to run command 'source ~/python-environments/whisper/bin/activate' before executing playlist4whisper.py


3. playlist4whisper has been successfully tested on the macOS Ventura Intel version, also macOS versions for Mx or ARM should work without issues, and can also run on older versions such as Big Sur with some extra adjustments.

For all versions of macOS, Homebrew has introduced significant changes in recent versions of the applications needed by playlist4whisper. First of all, there have been changes in the behavior of installing Python applications, likely to improve stability or security. Depending on how Python was installed or updated, you may need to adjust your system settings to begin using a Python environment and to detect the new Python version. Please follow the instructions provided in the terminal when installing Python3.

Additionally, for older macOS versions like Big Sur, you may encounter issues when installing Homebrew applications and compiling whisper.cpp due to outdated default libraries or conflicts between Homebrew and macOS. Alternatively, you can install an older version of whisper.cpp, and older versions of applications such as FFmpeg (separately from FFplay and FFprobe, which are also necessary), VLC, SMPlayer, and MPV from other sources, downloading them individually. If you trust the source, just copy the executable packaged as a .app file to the Applications folder and then link the path to /usr/local/bin/[executable]. Make sure to use the executable name in lowercase for the /usr/local/bin/ part:
```
ln -s /Applications/[executable].app/Contents/MacOS/[executable] /usr/local/bin/[executable]
```
or
```
ln -s /Users/[user]/[directory]/[executable] /usr/local/bin/[executable]
```
For example, if you installed VLC individually, if the app isn't signed you'll need to grant it permission in your system, and to make it compatible with bash scripts or default commandline:
```
ln -s /Applications/VLC.app/Contents/MacOS/VLC.app /usr/local/bin/vlc
```


4. If you encounter an xterm error that says "Failed to open input method," it could be because the xterm executable in the "/opt/X11/bin" directory isn't the first one in your $PATH variable. You can try:
```
rm /usr/local/bin/xterm
ln -s /opt/X11/bin/xterm /usr/local/bin/xterm
```
To display the correct local characters you can create a file named ".Xresources" in your user's home directory (/Users/[user]). Inside the file, you can define specific settings to customize the appearance of the transcription text. For example:

```
.xterm*background: black
.xterm*foreground: yellow
.xterm*font: 10x20
.xterm*vt100*geometry: 80x10
.xterm*saveLines: 10000
.xterm*locale: true 
```
In this example, the settings modify the background color to black, the foreground color to yellow, the font size to 10x20, the terminal's geometry to 80x10, and the number of lines to save to 10,000. After saving these changes in the ".Xresources" file, you need to relaunch XQuartz for the new settings to take effect. Once you launch an xterm terminal, you will see the desired customization of the transcription text.

The final option '.xterm*locale: true' will enable the same language settings in xterm as those in your macOS's default terminal. Although you may need to make changes and/or install additional components to display characters in other languages.


5. Compile whisper.cpp following the instructions provided in the documentation at https://github.com/ggerganov/whisper.cpp, or for CPU mode, just follow these instructions:

From your base user directory (/Users/[user]) download the source code for whisper.cpp:
```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Change the default directory to the whisper.cpp directory:
```
cd whisper.cpp
```
Compile whisper.cpp for CPU mode:
```
make
```
Download some models:
```
make tiny.en
```
```
make base.en
```
```
make base
```

To download playlist4whisper and livestream_video.sh, you can use the following command:
```
git clone https://github.com/antor44/livestream_video.git
```
Stay where you executed the command, move all to whisper.cpp directory:
```
mv livestream_video/* ~/whisper.cpp
```
playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper.cpp and its subdirectory ./build/bin/ with its 'whisper-cli' executable.


6. Finally, launch the app by entering the following command in the terminal. Make sure you are inside the whisper.cpp directory (cd ~/whisper.cpp) and that your Python environment is activated (source ~/python-environments/whisper/bin/activate), if required.
```
python3 playlist4whisper.py
```

Please note that on macOS, only the xterm terminal and the mpv/vlc video player are supported. Additionally, the xterm terminal automatically closes its window when Control+C is used.

#
## Detailed installation for Windows 10/11

playlist4whisper can run on Windows Subsystem for Linux (WSL2), which is the default virtual system on Windows 10/11 for running native Linux software. Keep in mind that WSL2 may not provide the same level of stability and smooth performance as Linux or macOS. When using the VLC player, which is required for one of the main features, you might run into audio issues with the default settings. Nevertheless, you can also compile whisper.cpp with GPU acceleration.

Open PowerShell or Windows Command Prompt in administrator mode by right-clicking and selecting "Run as administrator", and install WSL2:

```
wsl --install
```
This command will enable the features necessary to run WSL and install the Ubuntu distribution of Linux (the default distribution). Once this is done, you will need to restart.

Upon the initial launch of a newly installed Linux distribution, a console window will appear and prompt you to wait while files are decompressed and stored on your machine. Subsequent launches should be completed in less than a second.

After successfully installing WSL and Ubuntu, the next step is to set up a user account and password for your new Linux distribution.

Open the Linux terminal, not the Windows terminal. Then update the packages in your distribution:
```
sudo apt update
```
```
sudo apt upgrade
```
Install Linux programs and their libraries, such as Python, whisper.cpp and mpv. Ubuntu Linux users can install the following packages:
```
sudo apt-get install mpv smplayer translate-shell vlc ffmpeg make cmake python3-tk python3-pip jq curl bc gnome-terminal xterm
```

You need to install some libraries via pip. One option is to install a python virtualenv:
```
sudo apt install virtualenv
```
Then:
```
mkdir ~/python-environments
virtualenv ~/python-environments/whisper
source ~/python-environments/whisper/bin/activate
```
Finally:
```
pip3 install imageio imageio-ffmpeg Pillow
```
Remember, in every session you need to run command 'source ~/python-environments/whisper/bin/activate' before executing playlist4whisper.py

For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp), for Twitch and Others streamlink is required (https://streamlink.github.io).

The easy way to install yt-dlp and streamlink:
```
pip3 install yt-dlp
pip3 install streamlink
```
or to create a Python virtual environment alongside Python applications, install pipx:
```
sudo apt-get install pipx
pipx install yt-dlp
pipx install streamlink
```

And to upgrade them:
```
pip3 install --upgrade yt-dlp
pip3 install --upgrade streamlink
```
or 
```
pipx upgrade yt-dlp
pipx upgrade streamlink
```

Download the source code of whisper.cpp:

```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Change the default directory to the whisper.cpp directory:
```
cd whisper.cpp
```
Compile whisper.cpp for CPU mode:
```
make
```
Download some models:
```
make tiny.en
```
```
make base.en
```
```
make base
```
To download playlist4whisper and livestream_video.sh, you can use the following command:
```
git clone https://github.com/antor44/livestream_video.git
```
Stay where you executed the command, move all to whisper.cpp directory:
```
mv livestream_video/* ~/whisper.cpp
```
playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper.cpp

Finally, launch the app by entering the following command in the terminal. Make sure you are inside the whisper.cpp directory (cd ~/whisper.cpp) and that your Python environment is activated (source ~/python-environments/whisper/bin/activate), if required.
```
python3 playlist4whisper.py
```
MPV player is not working on Windows, potentially due to the need for additional configuration and/or installation of packages.

#
## Usage 

**Warning: To use the Timeshift feature, ensure that VLC is configured to repeat the playlist infinitely, not just the current file.**

Make sure that you are in the same directory as whisper.cpp, playlist4whisper.py, and livestream_video.sh, and also ensure that the Python environment for playlist4whisper is active. Then:

```
python3 playlist4whisper.py
```
Playlist4Whisper accepts optional command-line arguments to add any number of tabs, specifying their names and colors displayed within the application.
 The names provided by the user will be used to create the M3U playlist and JSON configuration files, which will be converted to lowercase.

--tabs: Accepts a list of tab names. If a tab name contains spaces, enclose it in double quotes.

--colors: Accepts a list of tab colors. Colors can be specified as color names (e.g., "red") or hexadecimal RGB values (e.g., "#ff0000").
 If a color is specified in hexadecimal RGB format, enclose it in double quotes.
 
Example:
```
python playlist4whisper.py --tabs Tab1 Tab2 Tab3 --colors red green "#ff7e00"
```
This command will create three tabs with the names "Tab1", "Tab2", "Tab3", and the colors red, green, and orange ("#ff7e00"), respectively.

You can also run different "playlist4whisper" copies in separate directories, each with its own playlist and configuration files.
#
*Check out the section on livestream_video.sh for help with the available options.

Local audio/video files must be referenced with the full file path. Alternatively, if the file is in the same directory, it can be referenced with './' preceding the file name.

The program will load the default playlists playlist_iptv.m3u, playlist_youtube.m3u, playlist_twitch.m3u, ...
 and will store options in config_xxx.json.
 
The majority of online video streams should work. Ensure that your installed yt-dlp and streamlink are up-to-date.

Recommended Linux video player (when playlist4whisper's timeshift with VLC is not active): SMPlayer, based on mpv, due to its capabilities to timeshift online streams for manual synchronization of live video with transcriptions.

Before using VLC go to Tools->Preferences and Show setting: All. Then Interface->Main Interfaces-> Qt-> Uncheck: 'Resize interface to the native video size', and 'When to raise the interface'-> Never. Ensure that VLC is configured to repeat the playlist infinitely, not just the current file, and save the configurations.

For multi-instances with SMPlayer: Go to Preferences - Interface - Instances, and turn off the option to use only one instance.
</br>
</br>
#
# livestream_video.sh


This is a command-line program that includes the same transcription functions as `playlist4whisper` and can be run independently of the GUI. Options are set via parameters in a terminal, or you can create desktop shortcuts for each TV channel.

`livestream_video.sh` is a Linux script that transcribes video livestreams by feeding `ffmpeg` output to `whisper.cpp` at regular intervals. It is based on `livestream.sh` from the `whisper.cpp` project:

https://github.com/ggerganov/whisper.cpp

*The Text-to-Speech (TTS) feature is performed online via the **Translate Shell** app, which utilizes a free Google service. The availability of this service is not guaranteed. Additionally, the TTS feature is designed for short audio segments and is limited to certain languages.

### Some Notable Features:

-   **Online Translation:** Translate transcriptions in real-time using either Google Translate or the high-quality Google Gemini API.
-   **Context Control for AI:** Fine-tune Gemini translations with context levels (0-3) to balance between literal accuracy and creative, context-aware fluency.
-   **Text-to-Speech (TTS):** Read translated text aloud for a more immersive experience with [Translate Shell](https://github.com/soimort/translate-shell).
-   **Subtitle Generation:** Automatically create `.srt` subtitle files from local media files.
-   **Timeshift:** A fully configurable timeshift feature, exclusive to the VLC player (note: not all streams are compatible).
-   **Broad Service Support:**
    -   Native support for IPTV, YouTube, and Twitch.
    -   Extended support for a wide range of video services through `streamlink` or `yt-dlp`, including Dailymotion, Vimeo, and many more.
    -   List of sites supported by `streamlink` (some plugins may be outdated): [streamlink.github.io/plugins.html](https://streamlink.github.io/plugins.html)
    -   List of sites supported by `yt-dlp` (some plugins may be outdated): [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
-   **Multi-Instance Execution:** Run multiple instances of the script simultaneously. To use this feature with SMPlayer, go to `Preferences -> Interface -> Instances` and disable the option "Use only one instance."
-   **Whisper AI Options:** Full control over Whisper parameters, including language autodetection (`auto`), specific languages (`en`, `es`, `fr`, etc.), and direct translation to English (`--translate`).
-   **Quantized Models:** Support for quantized models to improve performance on CPUs.
-   **Multi-Platform:** Compatible with Linux, macOS, and Windows (via WSL2).
-   **Audio Inputs:** Transcribe from any audio input, including loopback devices to capture desktop audio. Supported on Linux (PulseAudio) and macOS (AVFoundation).

### Online Translation with Google Gemini API

The latest version introduces high-quality online translation using Google's Gemini AI models. This feature serves as a powerful alternative to the standard translation provided by `translate-shell`.

**Key Features:**

*   **Superior Quality:** Gemini models often provide more accurate and context-aware translations than traditional services.
*   **Model Selection:** You can choose from several available Gemini models, such as `gemini-2.5-flash-lite` (default) or the more powerful `gemini-2.5-pro`.
*   **Context Control:** Use the `--gemini-level` argument to adjust how much context the AI uses, allowing you to fine-tune the translation style from literal to highly fluent.
*   **API Key Integration:** The system securely manages your Google Gemini API key, which is required to use this feature.

#### How to Enable Gemini Translation

##### 1. Obtain a Google Gemini API Key

*   Go to **[Google AI Studio](https://aistudio.google.com/)**.
*   Sign in with your Google account.
*   Click on **"Get API key"** and then **"Create API key"**.
*   Copy the generated key immediately. It is crucial for the next step.

##### 2. Provide the API Key to the Application

You must make the API key available to the `livestream_video.sh` script. There are three recommended methods:

###### Method A: System-Wide Environment Variable (Recommended for Desktop Users)

This method ensures the key is always available, even when launching the bash script from a desktop icon.

1.  Open the file `~/.profile` with a text editor (e.g., `nano ~/.profile`).
2.  Add the following line at the end, replacing `YOUR_API_KEY_HERE` with your actual key:
    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```
3.  Save the file and log out and log back in for the changes to take effect.

###### Method B: Shell-Specific Environment Variable (Recommended for Terminal Users)

This is ideal if you primarily run the application from a terminal.

1.  Open your shell's configuration file (`~/.bashrc` for Bash, `~/.zshrc` for Zsh).
2.  Add the same line as in Method A:
    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```
3.  Save the file and either restart your terminal or run `source ~/.bashrc` (or `source ~/.zshrc`).

###### Method C: Set in the `playlist4whisper` GUI (Easiest)

The graphical application can store the key for you. This method is the most straightforward, but the key will only be used when launching the script **from the GUI**.

1.  In `playlist4whisper`, click the **"API Key"** button located in the "Online translation" section.
2.  Paste your key into the dialog box and click "OK". The key is saved in your configuration file and will be passed to the script automatically.

##### 3. Use Gemini Translation via Command Line

*   Add the `--trans <language_code>` flag to enable online translation.
*   Add the `--gemini-trans` flag to use the Gemini engine.
*   (Optional) Specify a model: `--gemini-trans gemini-2.5-pro`.
*   (Optional) Specify a context level: `--gemini-level 3`.

The script will now use the Gemini API for translations. If the API key is not found, it will automatically fall back to the standard `translate-shell` engine.

**Note:** Using the Gemini API is subject to Google's pricing and usage policies. Please consult the [Google AI Platform pricing page](https://ai.google.dev/pricing) for details.

---

### Usage

`./livestream_video.sh stream_url [or /path/media_file or pulse:index or avfoundation:index] [--step step_s] [--model model] [--language language] [--executable exe_path] [--translate] [--subtitles] [--timeshift] [--segments segments (2<n<99)] [--segment_time minutes (1<minutes<99)] [--sync seconds (0 <= seconds <= (Step - 3))] [--trans trans_language output_text speak] [--gemini-trans [gemini_model]] [--gemini-level [0-3]] [player player_options]`

Example:
```
./livestream_video.sh https://cbsn-det.cbsnstream.cbsnews.com/out/v1/169f5c001bc74fa7a179b19c20fea069/master.m.m3u8 --lower --step 8 --model base --language auto --translate --timeshift --segments 4 --segment_time 10 --trans es both speak --gemini-trans --gemini-level 3
```

**Only for the bash script and only for local audio/video:** Files must be enclosed in double quotation marks, with the full path. If the file is in the same directory, it should be preceded with './'

**pulse:index or avfoundation:index:** Live transcription from the selected device index. Pulse for PulseAudio for Linux and Windows WSL2, AVFoundation for macOS. The quality of the transcription depends on your computer's capabilities, the chosen model, volume and sound configuration on your operating system, and the noise around you. Please note that this is a preliminary feature. There are several seconds of delay between live sound and transcriptions, with no possibilities for synchronization.

#

### **Argument Options**

#### Stream Handling

`--streamlink`
Forces the URL to be processed by Streamlink.

`--yt-dlp`
Forces the URL to be processed by yt-dlp.

`--[raw, upper, lower]`
Video quality options. Affects timeshift for IPTV.
- **raw:** Downloads another video stream without any modifications for the player.
- **upper/lower:** Downloads only one stream that is re-encoded for the player (best/worst quality). This saves data, but not all streams support it.

#### Player

`--player`
Specify player executable and options. Valid players: `smplayer`, `mpv`, `mplayer`, `vlc`, etc. Use `'none'` or `'true'` for no player.

#### Whisper AI Configuration

`--step`
Size of the sound parts into which audio is divided for AI inference, measured in seconds.

`--model`
Whisper Models available:
- **Base Models:** `tiny.en`, `tiny`, `base.en`, `base`, `small.en`, `small`, `medium.en`, `medium`, `large-v1`, `large-v2`, `large-v3`, `large-v3-turbo`.
- **Quantized Suffixes:** `-q2_k`, `-q3_k`, `-q4_0`, `-q4_1`, `-q4_k`, `-q5_0`, `-q5_1`, `-q5_k`, `-q6_k`, `-q8_0`.

`--executable`
Specify the whisper executable to use (full path or command name).

`--language`
Whisper Languages available (code and name):

```
 auto (Autodetect)      fa (Persian)           kk (Kazakh)            nn (Nynorsk)           ta (Tamil)
 af (Afrikaans)         fi (Finnish)           km (Khmer)             no (Norwegian)         te (Telugu)
 am (Amharic)           fo (Faroese)           kn (Kannada)           oc (Occitan)           tg (Tajik)
 ar (Arabic)            fr (French)            ko (Korean)            or (Oriya)             th (Thai)
 as (Assamese)          ga (Irish)             ku (Kurdish)           pa (Punjabi)           tl (Tagalog)
 az (Azerbaijani)       gl (Galician)          ky (Kyrgyz)            pl (Polish)            tr (Turkish)
 be (Belarusian)        gu (Gujarati)          la (Latin)             ps (Pashto)            tt (Tatar)
 bg (Bulgarian)         ha (Bantu)             lb (Luxembourgish)     pt (Portuguese)        ug (Uighur)
 bn (Bengali)           haw (Hawaiian)         lo (Lao)               ro (Romanian)          uk (Ukrainian)
 br (Breton)            he (Hebrew)            lt (Lithuanian)        ru (Russian)           ur (Urdu)
 bs (Bosnian)           hi (Hindi)             lv (Latvian)           sd (Sindhi)            uz (Uzbek)
 ca (Catalan)           hr (Croatian)          mg (Malagasy)          sh (Serbo-Croatian)    vi (Vietnamese)
 cs (Czech)             ht (Haitian Creole)    mi (Maori)             si (Sinhala)           vo (Volapuk)
 cy (Welsh)             hu (Hungarian)         mk (Macedonian)        sk (Slovak)            wa (Walloon)
 da (Danish)            hy (Armenian)          ml (Malayalam)         sl (Slovenian)         xh (Xhosa)
 de (German)            id (Indonesian)        mn (Mongolian)         sn (Shona)             yi (Yiddish)
 el (Greek)             is (Icelandic)         mr (Marathi)           so (Somali)            yo (Yoruba)
 en (English)           it (Italian)           ms (Malay)             sq (Albanian)          zh (Chinese)
 eo (Esperanto)         iw (Hebrew)            mt (Maltese)           sr (Serbian)           zu (Zulu)
 es (Spanish)           ja (Japanese)          my (Myanmar)           su (Sundanese)
 et (Estonian)          jw (Javanese)          ne (Nepali)            sv (Swedish)
 eu (Basque)            ka (Georgian)          nl (Dutch)             sw (Swahili)                     
```

`--translate`
Automatic English translation using Whisper AI (English only).

`--subtitles`
Generate subtitles (`.srt`) from a local audio/video file.

#### Online Translation

`--trans`
Enables online translation. Must be followed by a language code.
- `trans_language`: Translation language (e.g., `es`, `fr`, `de`).
- `output_text`: (Optional) Output text: `original`, `translation`, `both`, `none`.
- `speak`: (Optional) Online Text-to-Speech.

`--gemini-trans`
Use the Google Gemini API for higher quality translation.
- `gemini_model`: (Optional) Specify a Gemini model. Defaults to `gemini-2.5-flash-lite`.

`--gemini-level`
Set the context level for Gemini translation (0-3). Default is 2.
- `Level 0`: No context, translates literally.
- `Level 1`: Minimal context (surrounding segments).
- `Level 2`: Standard context (sliding window of multiple surrounding segments).
- `Level 3`: Creative context (allows AI to fix/complete phrases based on context).

#### Timeshift Configuration (VLC Player Only)

`--timeshift`
Enables the timeshift feature.

`--sync`
Transcription/video synchronization time in seconds (`0` <= `seconds` <= (`Step` - 3)).

`--segments`
Number of segment files for timeshift (`2` <= `n` <= `99`).

`--segment_time`
Time for each segment file (`1` <= `minutes` <= `99`).

#

## playlist4whisper Screenshots
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV2.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV8.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV7.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV9.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV11.jpg)
#
## livestream_video.sh screenshots:
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV3.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV4.jpg)

#
# To-Do List

- Advanced audio chunk processing to avoid transcriptions out of context.
- Voice activity detection (VAD) for splitting audio into chunks.
- Advanced GUI as a standalone application.
- Support for different AI engines.
- Sound filters.
- ...

#
# FAQ

**Q: What quality of transcription can I expect when using only a low-level processor?**

A: This program is based on whisper.cpp, which is a highly optimized implementation of OpenAI's Whisper AI. The performance of the transcription largely depends on this software. For English language, you can expect very good transcriptions of video streams or media files even on low-end or old PCs, even those that are at least 10 years old. You can easily configure the application with models such as small.en or base.en, which offer excellent transcriptions for the English language. Even the tiny.en model, despite its small size, provides great results. However, transcriptions of other major languages are not as good with small models, and minority languages do not perform well at all. For these, you will need a better CPU or a supported GPU.

**Q: Why isn't there a precompiled and packaged distribution for the program "playlist4whisper"?**

A: First, this is a Linux application, and macOS and Windows are not fully supported. For Linux systems, compiling and distributing packages is the responsibility of each distribution’s maintainers, not the programmer.

Linux prioritizes security, which is best ensured through precompiled packages stored in official repositories—especially in major Linux distributions, on which many others depend.

'whisper.cpp' itself is not available in the repositories of major Linux distributions, despite its reputation for being significantly more efficient than OpenAI's original implementation. It can only be installed via PyPI—a repository for Python software—or Homebrew, a non-traditional package manager.

Additionally, Linux distributions are very different, even Python environments, and it is not easy to support every one, especially with this project that depends on numerous other libraries and programs.

The absence of precompiled ‘playlist4whisper’ packages on the project’s webpage is due to frequent updates and optional hardware-specific optimizations in the underlying ‘whisper.cpp’ program. By providing the source code, users can adapt to these ongoing changes and tailor performance optimizations to their hardware and preferences.

Keep in mind that compiling whisper.cpp with certain hardware accelerations—such as CUDA on any NVIDIA RTX graphics card—can result in a significant performance boost, even compared to the default or CPU-optimized builds of whisper.cpp, even on powerful modern CPUs.

However, compiling whisper.cpp with CUDA is not always a trivial task: the success of the build or executable will depend on factors such as the CUDA version, NVIDIA driver, compiler version, and other libraries installed on the user’s Linux operating system.

Another question is that "playlist4whisper" relies on the included bash script "livestream_video.sh". This script can be executed independently, supporting accessibility technologies. It can also run on Linux terminals without a desktop environment and potentially be used as a server application in multi-instance and multi-user scenarios, making it versatile for various use cases. By providing the source code, advanced users can review or customize the programs to suit their specific requirements and environments.

**Q: In a low-power processor, is it possible to improve transcription in languages other than English?**

A: Yes, several advanced methods can significantly boost performance:

*   **GPU/NPU Acceleration:** Instead of running the AI engine on the CPU, you can compile `whisper.cpp` with hardware acceleration. This can increase execution speed by 2x or more, allowing you to use larger, more accurate models. Supported technologies include:
    *   **NVIDIA GPU:** via [cuBLAS](https://github.com/ggerganov/whisper.cpp#nvidia-gpu-support-via-cublas).
    *   **Cross-Vendor GPU (NVIDIA, AMD, Intel):** via [Vulkan](https://github.com/ggerganov/whisper.cpp#vulkan-gpu-support) or [OpenCL (CLBlast)](https://github.com/ggerganov/whisper.cpp/pull/1037).
    *   **Intel CPU/GPU:** via [OpenVINO](https://github.com/ggerganov/whisper.cpp#openvino-support).
    *   **Apple Silicon (M1/M2/M3/M4):** via [Core ML](https://github.com/ggerganov/whisper.cpp#core-ml-support) to use the Apple Neural Engine (ANE), offering speed-ups of over 3x.
    *   **Ascend NPU:** via [CANN](https://github.com/ggerganov/whisper.cpp#ascend-npu-support).
    *   **Moore Threads GPU:** via [MUSA SDK](https://github.com/ggerganov/whisper.cpp#moore-threads-gpu-support).
   
*   **CPU Acceleration:** For CPU-only systems, you can still get a boost by compiling with [OpenBLAS](https://github.com/ggerganov/whisper.cpp#blas-cpu-support-via-openblas) or [POWER VSX](https://github.com/ggerganov/whisper.cpp#power-vsx-intrinsics).
    
*   **Quantized Models:** You can try using the quantized models option, which can improve execution speed on certain processors with minimal loss in accuracy.
  
*   **Fine-Tuning:** If you have AI programming experience, you can fine-tune a default model by retraining it with a dataset of voices and transcriptions in a specific language. This can also improve recognition of specific accents, slang, or dialects. You can find instructions for converting models to the required `ggml` format on the [whisper.cpp repository](https://github.com/ggerganov/whisper.cpp/blob/master/models/README.md).

Keep in mind that compiling whisper.cpp with certain hardware accelerations—such as CUDA on any NVIDIA RTX graphics card—can result in a significant performance boost, even compared to the default or CPU-optimized builds of whisper.cpp, even on powerful modern CPUs.

*The accelerated versions of whisper.cpp may require specific model versions to achieve better performance.

**Q: How do I configure whisper.cpp for hardware accelerations (e.g., CUDA, Core ML, OpenVINO) and generate the specific models needed? Why don't the models downloaded by `playlist4whisper.py` work with all accelerations?**

A: Whisper.cpp supports various hardware accelerations (CPU, CUDA, Core ML, OpenVINO, Vulkan, BLAS, CANN, MUSA), each requiring specific compilation flags and, for some, custom model formats. The models downloaded by `playlist4whisper.py` are in the standard `ggml` format (`.bin`) and work only with CPU, CUDA, Vulkan, BLAS, CANN, and MUSA backends. **These models do not work with Core ML (Apple M1/M2/M3/M4 NPU) or OpenVINO (Intel CPU/GPU) without conversion to their specific formats.** Core ML or OpenVINO require converted models (`.mlmodelc` for Core ML, `.xml`/`.bin` IR for OpenVINO). Attempting to use a standard `.bin` with these backends will fail, as whisper.cpp expects the optimized format in the `models/` directory. Below are the steps to compile whisper.cpp for each acceleration, generate the required models, and test them with `livestream_video.sh`.

**Commands for Compilation and Model Generation**  

Download the source code of whisper.cpp from your home directory:
```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Change the default directory to the whisper.cpp directory, which is whisper.cpp:
```
cd whisper.cpp
```

#### 1. CPU (Standard, No Acceleration)
- **Compilation**:  
```bash
cmake -B build
cmake --build build -j --config Release
```
- **Model**: Download a standard model:  
```bash
make base.en
```
  - Optional: Quantize for reduced memory/faster processing:  
```bash
./build/bin/quantize models/ggml-base.en.bin models/ggml-base.en-q5_0.bin q5_0
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
- **Note**: Models from `playlist4whisper.py` work directly.

#### 2. CUDA (NVIDIA GPU, e.g., RTX 4060 Ti)
- **Requirements**: Install CUDA toolkit (https://developer.nvidia.com/cuda-downloads).  
- **Compilation**:  
```bash
cmake -B build -DGGML_CUDA=1
cmake --build build -j --config Release
```
  - For newer GPUs (e.g., RTX 5000 series):  
```bash
cmake -B build -DGGML_CUDA=1 -DCMAKE_CUDA_ARCHITECTURES="86"
cmake --build build -j --config Release
```
- **Model**: Use the same `.bin` as for CPU:  
```bash
make base.en
```
  - Optional: Quantize:  
```bash
./build/bin/quantize models/ggml-base.en.bin models/ggml-base.en-q5_0.bin q5_0
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
- **Note**: Models from `playlist4whisper.py` work directly.

#### 3. Core ML (Apple Silicon M1/M2/M3/M4 NPU)
- **Requirements**:  
  - macOS Sonoma (14 or later).  
  - Xcode and command-line tools:  
```bash
xcode-select --install
```
  - Python 3.11 (use Miniconda):  
```bash
conda create -n py311-whisper python=3.11 -y
conda activate py311-whisper
pip install ane_transformers openai-whisper coremltools
```
- **Generate Model**:  
```bash
sh ./models/generate-coreml-model.sh base.en
```
  - Creates `models/ggml-base.en-encoder.mlmodelc` (loaded as `.bin`).  
- **Compilation**:  
```bash
cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
  - **Important**: `--model base.en` loads `ggml-base.en-encoder.mlmodelc` if Core ML is enabled.  
- **Note**: Models from `playlist4whisper.py` **do not work**. You must generate the `.mlmodelc` model.

#### 4. OpenVINO (Intel CPU/GPU)
- **Requirements**:  
  - Python 3.10:  
```bash
cd models
python3 -m venv openvino_conv_env
source openvino_conv_env/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-openvino.txt
```
  - OpenVINO toolkit (version 2024.6.0, from https://www.intel.com/content/www/us/en/developer/tools/openvino-toolkit-download.html).  
  - Set up OpenVINO:  
```bash
source /path/to/openvino/setupvars.sh  # Linux
```
- **Generate Model**:  
```bash
python convert-whisper-to-openvino.py --model base.en
```
  - Creates `models/ggml-base.en-encoder-openvino.xml` and `.bin`. Move to `models/` if needed.  
- **Compilation**:  
```bash
cmake -B build -DWHISPER_OPENVINO=1
cmake --build build -j --config Release
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
  - **Important**: `--model base.en` loads the `.xml`/`.bin` IR files internally.  
- **Note**: Models from `playlist4whisper.py` **do not work**. You must generate the OpenVINO IR model.

#### 5. Vulkan (AMD/Intel/NVIDIA GPUs)
- **Requirements**: Install drivers with Vulkan API support.  
- **Compilation**:  
```bash
cmake -B build -DGGML_VULKAN=1
cmake --build build -j --config Release
```
- **Model**: Use the same `.bin` as for CPU/CUDA:  
```bash
make base.en
```
  - Optional: Quantize:  
```bash
./build/bin/quantize models/ggml-base.en.bin models/ggml-base.en-q5_0.bin q5_0
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
- **Note**: Models from `playlist4whisper.py` work directly.

#### 6. BLAS (CPU with OpenBLAS)
- **Requirements**: Install OpenBLAS (https://www.openblas.net/).  
- **Compilation**:  
```bash
cmake -B build -DGGML_BLAS=1
cmake --build build -j --config Release
```
- **Model**: Use the same `.bin` as for CPU:  
```bash
make base.en
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
- **Note**: Models from `playlist4whisper.py` work directly.

#### 7. Ascend NPU (Huawei Atlas 300T A2)
- **Requirements**: Install CANN toolkit (latest version, check Huawei documentation).  
- **Compilation**:  
```bash
cmake -B build -DGGML_CANN=1
cmake --build build -j --config Release
```
- **Model**: Use the same `.bin` as for CPU:  
```bash
make base.en
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
- **Note**: Models from `playlist4whisper.py` work directly.

#### 8. MUSA (Moore Threads GPU)
- **Requirements**: Install MUSA SDK rc4.2.0 (https://developer.mthreads.com/sdk/download/musa).  
- **Compilation**:  
```bash
cmake -B build -DGGML_MUSA=1
cmake --build build -j --config Release
```
  - For specific GPUs (e.g., MTT S80):  
```bash
cmake -B build -DGGML_MUSA=1 -DMUSA_ARCHITECTURES="21"
cmake --build build -j --config Release
```
- **Model**: Use the same `.bin` as for CPU:  
```bash
make base.en
```
- **Run**:  
```bash
./livestream_video.sh ./samples/jfk.wav --model base.en --subtitles
```
- **Note**: Models from `playlist4whisper.py` work directly.

**Q: How much data is needed to fine-tune a model?**

A: Fine-tuning a Whisper model might be more difficult and costly than expected; you must collect that specific information yourself. Some users report success with a relatively short amount of data, while others couldn't obtain significant improvements. It depends on the quality of the language already supported by Whisper and its similarities with other languages supported by Whisper. It also depends on the quality of the dataset for training. It's clear that having as much data as possible is better; perhaps thousands of hours of short sound chunks with their transcriptions. You might be able to fine-tune with large free datasets like Common Voice. You can find the latest version of the Common Voice dataset by checking the [Mozilla Foundation](https://commonvoice.mozilla.org) page or the [Hugging Face Hub](https://huggingface.co/mozilla-foundation). Keep in mind that OpenAI already utilized Common Voice datasets for the validation task during its training, so it's possible that some datasets or languages may not improve Whisper's models as expected. Nonetheless, some minority languages like Catalan, Esperanto and Basque have a significant number of hours in Common Voice, while one of the major languages like Spanish has a very poor dataset. If you want to fine-tune for a more specific use, then you might need a lot of effort or cost to collect enough data with the needed quality, although the dataset would be smaller for improving technical words, slang, or a specific accent of a local region for an already well-supported language.

**Q: Why do I sometimes get errors or poor-quality translations with Gemini AI?**

A: Online translation issues with the Gemini API can stem from several factors, from API availability to the inherent behavior of AI models. Here are the most common causes:

*   **API Unavailability:** The service may be temporarily unavailable or experiencing high traffic. The script handles this differently depending on the mode:
    *   In **Subtitle Generation**, it will retry a few times before falling back to `translate-shell`.
    *   In **Live Stream** mode, it will immediately fall back to `translate-shell` for a failed block to maintain real-time flow, indicated by a `(*)` prefix.

*   **API Rate Limits:** The primary cause of failures is exceeding the usage limits imposed by Google, which are **particularly strict on the free tier**. While paid tiers have much higher limits, the following applies to free accounts:
    *   **Gemma 3 models** have a very high daily limit on the free tier (**14,400 RPD**) but a very low per-minute limit (**15,000 TPM**). This makes them excellent for **prolonged, low-intensity use** (like long live streams), but they will fail on high-intensity tasks (like subtitle generation) that exceed the TPM limit.
    *   **Gemini 2.5 models** on the free tier have the opposite profile: a low daily limit (e.g., **1,000 RPD for Flash-Lite**) but a high per-minute limit (**250,000 TPM**). This makes them perfect for **short, high-intensity tasks** like generating subtitles, but their daily quota can be exhausted in a long live stream.

*   **Inherent AI Translation Errors:** Even with a stable connection and within rate limits, all Gemini API models can occasionally produce translation errors. Users should be aware that issues like **confusing languages** (especially with multilingual source text), process previous sentences **modifying timestamps** in subtitle files, or **occasionally repeating previous phrases** can occur.

*   **Model Recommendations & Strategies (for Free Tier users):**
    *   **For Subtitle Generation:** Use a **Gemini 2.5 model** (`gemini-2.5-flash` or `gemini-2.5-flash-lite`). Their high TPM can handle the processing burst required for an entire file.
    *   **For Prolonged Live Streams (Hours):** Use a **Gemma 3 model**. Its massive daily request quota is ideal for long-running sessions. To avoid hitting the low TPM limit during dense dialogue, it is highly recommended to use a lower context level. You can do this by selecting "Level 0" or "Level 1" from the "Gemini Level" menu in the `playlist4whisper` application, or if using the `livestream_video.sh` script independently, by adding `--gemini-level 0` or `--gemini-level 1` to your command.
    *   **For Moderate Live Streams (Casual Use):** The **`gemini-2.5-flash-lite`** model is the best all-around choice, offering a great balance of quality, speed, and a reasonable daily quota (1,000 requests) using the default context level.

**Q: Why do subtitles translated via the Gemini API sometimes differ in quality from the web version in Google AI Studio?**

A: While the quality from the API is very high, you may notice that pasting an entire SRT file into a web chat like Google AI Studio can sometimes yield superior results. The primary reason for this is **global context**. When you paste a full SRT file into the web interface, it generally uses a powerful model like Gemini 2.5 Pro and can process the entire document as a single piece of context. This allows the AI to understand overarching themes and the relationships between distant parts of the dialogue, resulting in excellent quality translations in a wide range of languages. However, this manual method is less practical and can fail with very long texts, and occasionally generates other errors as well.

The application, on the other hand, processes the subtitle file in **segmented parts** to handle very large files robustly without failing. To maintain coherence, it provides the AI with a "sliding window" of context, including several phrases before and after the current segment being translated. For most content, the quality difference is barely noticeable. The most significant drop in quality usually occurs due to external factors like API server overload or rate limit errors. You may occasionally see minor errors, such as the repetition of words.

Despite this, the script's approach is highly effective. Even with smaller models like `gemini-2.5-flash-lite`, it does an excellent job with common languages, often correcting misspelled words and accurately identifying well-known entities such as places, acronyms, companies, organizations, political parties, and the names of famous people. However, it's important to note a universal limitation: if a name of an unknown person is transcribed incorrectly (e.g., "Jhon" instead of "John"), the AI has no way of knowing the correct spelling, a challenge that even the web version cannot solve.

**Q: Why doesn't the application use the entire subtitle file for context at once, similar to the web version?**

A: This is a design choice to optimize the script for reliability and performance across all models, especially for users with free tier API keys. While a feature known as **context caching** exists, which allows uploading a full document for global context, its practical application is complex.

The situation is as follows:

- For the powerful **Gemini models**, context caching is primarily a **paid tier feature**.
- For **Gemma models**, context caching is indeed available **free of charge**. However, this option was deliberately not implemented as the default for two key reasons:

    - **Rate Limits:** The free tier for Gemma models has a very low **Tokens Per Minute (TPM) limit**. Attempting to upload a moderately sized subtitle file to the cache would immediately fail by exceeding this limit.
    - **Translation Quality:** While Gemma is highly capable, it is not as powerful as the flagship Gemini models, especially for translating less common or nuanced languages where the larger model's extensive training data makes a significant difference.

Therefore, the current "sliding window" approach was chosen as the best overall solution. It provides high-quality context, works reliably across all models without failing on rate limits, and is optimized for the free tier. Paid account users still benefit from this system as they can use more powerful models with much higher rate limits, leading to a superior result.

**Q: What's the use of the loopback ports? Could I see my videos from the internet?**

A: Loopback ports are needed for features like timeshift, and for upper and lower video quality options. The application uses one port to communicate with VLC for information about the currently playing video, or is used by ffmpeg to stream video to mpv or smplayer. The loopback interface is a virtual network interface per user that by default is not accessible outside your computer, although you can configure your firewall and network interfaces to control VLC and transmit video outside to the internet using VLC's streaming option. However, this would not include live transcriptions, only subtitles. Nevertheless, there are some solutions to stream your entire desktop with decent image quality over the internet, NoMachine (freeware) or Moonlight (open source license) are both great options.

**Q: Some streams don't work, especially with upper and lower qualities, and sometimes timeshift doesn't work?**

A: Streams can often experience interruptions or temporary cuts, and their proper functioning in playlist4whisper can also depend on the ads they insert, and in other cases on whether yt-dlp and streamlink support the frequent changes made by various online video providers.

In general, processing online videos is very difficult due to the nature of different video codecs and network protocols used on servers and their various implementations, or due to incorrect timestamps and metadata information, or because of the difficulty of recording and cutting videos with ffmpeg. To add the somewhat random nature of the artificial intelligence algorithm for transcription.

**Q: How does timeshift work and where are the files stored? Can I save these videos?**

A: Timeshift functions similarly to other applications, but in playlist4whisper, it involves a playlist repeated indefinitely with temporary videos or buffers. You can configure the number of these buffers and their size in minutes. For example, from just a few minutes up to a maximum of 99 videos, each lasting 99 minutes. This allows for a maximum of 163 hours of live streaming for timeshift, although at the cost of requiring a very large amount of disk space. When the chosen maximum size is reached, the oldest video file is deleted, and this process continues indefinitely until the application is stopped or an error occurs.

The videos can be navigated in VLC as if it were a playlist with multiple videos, allowing you to switch between videos or rewind and fast forward within a single video. The transcription will automatically switch to the chosen point. However, you should be cautious not to approach the current live recording moment too closely, as the player may jump to another video. Occasionally, video stream errors and transcription errors could cause the player to jump to another video in this timeshift playlist.

The temporary video buffer files can be saved in another directory, they will have names similar to whisper-live_131263_3.avi, or for the last one being recorded, whisper-live_131263_buf033.avi. The files are stored in the /tmp directory in both Linux and macOS, which typically serves as the temporary directory and is usually cleared upon restarting the computer.

**Q: What can Playlist4Whisper do in terms of transcribing or translating sound card or sound device inputs? Are USB devices supported in Linux?**

The quality of the transcription depends on your computer's capabilities, the chosen model, volume, and sound configuration on your operating system, as well as the ambient noise. Please note that this is a preliminary feature. There is a several-second delay between live sound and transcriptions, with no possibility for synchronization.

The capabilities to transcribe audio inputs or 'what you hear' on the desktop exist in numerous scenarios depending on the capabilities of sound cards, webcams, microphones, and USB-connected headphones. In Linux, USB sound cards and sound integrated into webcams, microphones, and headphones might be problematic, especially for devices that are too old or too new. Sometimes you may need to install device controllers or modules for Linux. Most USB drivers are usually available in one of three ways: within the kernel, as a compilable standalone module, or available as a pre-compiled (packaged) binary driver from your Linux distribution. However, sometimes these devices or their modules are deactivated in the Linux kernel. Although this is a rare situation, it may occur if Windows WSL2 uses a Linux kernel with deactivated device controllers, or requires some configurations. Anyway, you may encounter issues when using these devices in a Linux virtualized environment on WSL2.

Apart from device drivers or Linux modules, operating systems could use different libraries or sound systems. Playlist4Whisper depends on PulseAudio for Linux and Windows WSL2, and AVFoundation for macOS. If you use other libraries, your operating system might require software wrappers to ensure compatibility between different software sound systems.

Sound cards or devices in duplex mode support recording and listening simultaneously; you may need to configure your sound card for duplex mode. Some models allow different mixes or combinations for recording multiple inputs and simultaneous playback, while there is also software available, both free and paid, that enables this functionality. For Linux, devices suffixed with 'monitor' are loopback devices that allow you to record all sounds 'what you hear' on your desktop. Some sound cards or Linux distributions need to activate this feature with PulseAudio commands, or you could add links between inputs and outputs of your sound cards by editing your Linux sound card configuration files. These devices, along with applications, can be configured individually using PulseAudio Volume Control. For macOS, you can only use loopback devices through a virtual device with an Audio Loopback Driver like Blackhole (free license), Loopback (commercial license) or VB-Cable (donationware).

Windows supports loopback sound for native applications through a virtual driver, such as VB-Cable (donationware), which is an additional piece of software similar to those used in macOS. However, Playlist4Whisper is executed in the Linux virtual environment WSL2. Sound capacities depend on each Linux application and on PulseAudio and Microsoft support for virtualized sound in WSL2. Currently, the default virtualized system in WSL2 or WSLg (Windows Subsystem for Linux GUI) can utilize PulseAudio, albeit through an RDP (Remote Desktop Protocol) loopback network connection, which is not the optimal solution.

**Q: Is it possible to achieve speech translation from a microphone without delay?**

A: There are few possibilities to achieve something similar to real-time or live transcriptions or speech translations. Different approaches exist for Speech-to-Speech translation systems: one involves a step-by-step process utilizing various specialized AI models, ranging from two to four steps. Another approach is a multimodal or all-in-one AI that handles all steps using a single model, like the SeamlessM4T free AI from Meta, which is currently in its early development stage. Neither approach can achieve real-time or live translations, nor anything resembling "near-live," due to the necessity of processing the input speech by dividing the recorded sound into small chunks. This is mainly due to contextual challenges or the differing nature of languages, which require the AI to understand the context of phrases or even anticipate what the speaker is going to say, akin to a wizard's alchemy. While it may be possible to introduce some shortcuts to shorten the steps, these tricks may not be suitable for a scientific solution or for accurate translation, as they could lead to reductionism or reinterpretations of what the speaker is saying.

Some applications use a trick to achieve a near-live result during the first transcription step, even with a Whisper AI and low-power computers, which playlist4whisper will support in the near future. This trick involves rapidly transcribing live speech, with one of the smallest models being something similar to a transcript without context or with a lot of errors, and immediately reintroducing the same sound data continuously to correct any possible errors in the last seconds transcribed. With this solution, the last words may frequently change, but it's not a significant issue for the user. However, this reintroduction trick cannot be applied to the speech translation step, as it is not serious to hear a translation of a sentence, and then the AI might repeatedly change the sentence because the initial version was incorrect.

![Live Transcription](https://github.com/antor44/livestream_video/blob/main/live-transcription.jpg)

**Q: Why is the program not working?**

A: There could be various reasons why the script/program is not functioning correctly. It relies on other Linux programs and their libraries, such as whisper.cpp and mpv. To compile the ./build/bin/whisper-cli executable, your operating system must have the necessary tools and development libraries installed, including those related to the chosen acceleration options. If you are not familiar with compilation, errors can often occur due to missing development libraries in your operating system. You will need to install only the necessary development libraries and the specific or compatible versions used by whisper.cpp. The ./build/bin/whisper-cli executable from whisper.cpp needs to be placed in the subdirectory of the directory of playlist4whisper.py and the script livestream_video.sh. Before lauch playlist4whisper.py, make sure that you are in the same directory as whisper.cpp, playlist4whisper.py, and livestream_video.sh, and eventually too the python environment for playlist4whisper is active. Additionally, it is crucial to have the Whisper model files in the "models" directory, following the correct format and name used by Whisper.cpp. 

The whsiper.cpp installation can be accomplished using terminal commands:

First clone the repository:
```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Now change directory to the whisper-ccp folder and build the ./build/bin/whisper-cli example to transcribe an audio file using the following command.

Build the './build/bin/whisper-cli' example:
```
make
```
Download some models:
```
make tiny.en
make base.en
make base
make small
make large-v3
```
Transcribe an audio file (for model base.en):
```
./build/bin/whisper-cli -f samples/jfk.wav
```
For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp). For Twitch streamlink is required (https://streamlink.github.io).

The easy way to install yt-dlp and streamlink:
```
pip3 install yt-dlp
pip3 install streamlink
```
Or to upgrade them:
```
pip3 install --upgrade yt-dlp
pip3 install --upgrade streamlink
```

**Q: When I run the script, I always encounter an error related to the "whisper-cli" or "main" executable.**

A: There could be various reasons for this error. The "whisper-cli" executable, originally named "main" executable, is one of the examples provided in whisper.cpp, a high-level implementation of OpenAI's Whisper AI. The executable's name should remain as the default "whisper-cli" and reside in the subdirectory "./build/bin/" of the directory where playlist4whisper.py and the bash script livestream_video.sh were copied. Ensure that both the whisper-cli executable and livestream_video.sh have executable permissions, at least for the current user. Additionally, the models you use should be stored in the "models" subdirectory, which are created by running terminal commands like "make base.en" or "make tiny.en". It's important to note that quantized models and large-v3 may not be compatible with older versions of whisper.cpp, which could lead to a "whisper-cli error". After building the whisper-cli example using the terminal command "make", you can test an audio file example using the command (for model base.en): ./build/bin/whisper-cli -f samples/jfk.wav

**Q: Can I run playlist4whisper without using the terminal, from a desktop shortcut on Linux?**

A: Yes, you can run it with the command "python" followed by the full path of playlist4whisper.py. In this case, before launching playlist4whisper.py, make sure that the Python environment for playlist4whisper is active. You can alternatively launch a bash script that first includes a command like 'source ~/python-environments/whisper/bin/activate'. If you are using an Anaconda environment, use the command '/home/[user]/anaconda3/bin/conda run python /home/[user]/[app directory]/playlist4whisper.py'. In both cases, provide the working directory where the program is located.

**Q: How can I change the size of the transcribed text snippets?**

A: You can change the size of the text snippets in seconds with the "step_s" option, which determines the duration of each part into which the videos are divided for transcription.

**Q: How can I change the size and colors of the transcription text?**

A: You can change the size and colors of the transcription text in the options of the terminal program you are using.

**Q: How can I position the terminal window for transcriptions in a fixed position?**

A: You can use a program for placing windows in Linux, such as devilspie, and configure a name for the terminal window and another for the main program terminal, such as Konsole or Xterm, to avoid name conflicts. For example, a configuration for the Gnome terminal in devilspie would be:

    ; generated_rule Terminal
    ( if
    ( and
    ( matches (window_name) "Terminal" )
    )
    ( begin
    ( geometry "+644+831" )
    ( println "match" )
    )
    )

**Q: How can I permanently change the size and colors of the transcription text on macOS? How to display the correct local characters?**

To achieve this, you can create a file named ".Xresources" in your user's home directory (/Users/[user]). Inside the file, you can define specific settings to customize the appearance of the transcription text. For example:

```
.xterm*background: black
.xterm*foreground: yellow
.xterm*font: 10x20
.xterm*vt100*geometry: 80x10
.xterm*saveLines: 10000
.xterm*locale: true 
```
In this example, the settings modify the background color to black, the foreground color to yellow, the font size to 10x20, the terminal's geometry to 80x10, and the number of lines to save to 10,000. After saving these changes in the ".Xresources" file, you need to relaunch XQuartz for the new settings to take effect. Once you launch an xterm terminal, you will see the desired customization of the transcription text.

The final option '.xterm*locale: true' will enable the same language settings in xterm as those in your macOS's default terminal. Although you may need to make changes and/or install additional components to display characters in other languages.

**Q: How can I copy the transcribed text on macOS after xterm has been closed?**

The xterm window closes when the bash script stops. The behavior of this terminal differs in playlist4whisper due to macOS's distinct handling of closed windows. However, you can still find text files containing all the transcriptions and translations in your /tmp directory. Recent versions of playlist4whisper now allow you to easily save these files by clicking the 'Save Texts' button. Please note that the operating system clears the /tmp directory upon computer boot.

**Q: How can I synchronize the video and the transcription?**

A: Without the Timeshift option, you can manually synchronize the video and transcription to your desired timing by using the pause and forward/backward buttons of the video player. When Timeshift is activated, the transcription is synchronized with the sync option, which is an automatic but fixed synchronization that cannot be changed during play.

**Q: Why does the video and transcription get desynchronized?**

A: There could be several potential causes. Online video streams may not always provide reliable video synchronization or timestamps. Some versions of the programs used by playlist4whisper, like VLC player or ffmpeg, may not accurately address the timestamps of the video being played. Additionally, video and transcription applications work independently, each with its own stream of video or audio. Over time, desynchronization can fluctuate, and choosing a model that is too large for the processor's capabilities can also impact synchronization.

The timeshift feature alongside with an automatic video/transcription synchronization option may help address the issue, although this may lead to some issues with phrases at the beginning of each segmented video chunk.

**Q: Why does the beginning and end of the transcription often get lost? Is this an AI issue?**

A: Most of the time, this occurs because the application lacks a voice activity detection (VAD) system to split the audio during silent intervals. The current versions of the bash script segment sound files into chunks based on user-selected durations, which may result in the truncation or deletion of words at the beginning and end of each chunk. Additionally, sometimes, there may be cut-offs of a few words at the start or end, either caused by the difficulty in obtaining precise data on video synchronization or timestamps, or this issue could be caused by gaps in the Whisper AI's neural network.

We are working on an advanced audio chunk processing method to avoid transcriptions out of context and resolve most issues related to truncation or deletion of words. However, this is a bit complicated and requires the addition of some processing power, which we have to minimize to maintain the philosophy of this application, which is to maintain low requirements for multiuser use or to run on as many computers as possible for individual use. The first solution is an algorithm similar to that used by the optional Chrome extension based on WhisperLive, which is in turn based on faster-whisper, a highly optimized implementation of OpenAI's Whisper AI. The extension relies on the output texts from the WhisperLive server, which uses a special technique to achieve real-time transcriptions. It first rapidly transcribes the most recent chunk of audio and then re-transcribes it with better context. This is done continuously for an undetermined window of time with the last seconds of video or audio.

Another solution is to implement an algorithm similar to a sliding window algorithm, a well-known algorithm used in digital data transmissions. We could use it in this case as well, with a low processor penalty. For example, with windows where each chunk size is determined by the seconds chosen by the user and a 3-window length, the middle window is transcribed while the other two windows serve as context to avoid the current transcription issues with truncation or deletion of words. In this case, the delay added would be the number of seconds of a window chunk.

These solutions are very efficient, but for apps like playlist4whisper and livestream_video.sh, they come with downsides because of stabilization problems. They'd make things more complex and add a delay before you see the stabilized text. Even worse, trying to use an even more advanced solution, or a whole new AI model just to fix the first AI's mistakes, doesn't make much sense.

It's worth noting that while playlist4whisper and livestream_video.sh currently process audio in isolated chunks —which can lead to word truncation and loss of broader sentence context— this approach also inherently minimizes the impact of hallucinations and other errors common to all Whisper AI model versions and model sizes. Any such errors are typically confined to a single audio/video fragment and occur infrequently, rather than propagating extensively throughout the transcription. The proposed additions to correct these word truncation issues are essentially classic coding workarounds, akin to applying a patch to address these noticeable flaws in OpenAI's Whisper model. Despite this development effort, guaranteed results are not assured. Furthermore, it's highly probable that OpenAI will implement similar or more sophisticated solutions directly within future Whisper model versions, or any other company in another transcription AI; it's almost inevitable they will address such evident and undesirable known errors sooner rather than later. Keep in mind that a very efficient and low power consumption, multilingual transcription AI is more than necessary for a lot of electronic devices and for all robots. This is the most fundamental part of the software to translate voice commands to robot's actions. Consequently, despite the significant programming work, and probably more inefficiently, to try and mitigate these issues externally, it might ultimately be time spent on a temporary fix.

Regarding the low-level development of the AI utilized by playlist4whisper.py or livestream_video.sh, OpenAI states: "The Whisper architecture is a simple end-to-end approach, implemented as an encoder-decoder Transformer. Input audio is split into 30-second chunks, converted into a log-Mel spectrogram, and then passed into an encoder. A decoder is trained to predict the corresponding text caption, intermixed with special tokens that direct the single model to perform tasks such as language identification, phrase-level timestamps, multilingual speech transcription, and English speech translation."

In essence, Whisper is an automatic speech recognition (ASR) system trained on 680,000 hours of multilingual and multitask supervised data collected from the web. The latest and largest model, large-v3, has been trained with over one million hours of labeled audio and over four million hours of audio. The sound is converted into spectrogram images, specifically into log-Mel spectrogram images, similar to other AIs that process input sound directly. These same spectrogram images are used to convert new sound files for inference or speech processing.

Additionally, Whisper utilizes a GPT-2 model, which incorporates a tokenizer responsible for breaking down input text into individual units called tokens. In Whisper’s case, the tokenizer employs the same set of Byte-Pair Encoding (BPE) tokens as the GPT-2 model for English-only models, with additional tokens included for multilingual models. GPT-2 is a Transformer-based language model trained to predict the next word fragment without explicit supervision. Its purpose is to fill in gaps and resolve audio inconsistencies to accurately transcribe coherent words within context, processing up to the last 224 tokens (approximately 168 words).

However, by default, when Whisper AI generates text during inference, the influence of these GPT-2 tokens for English, or the custom tokens introduced for other languages, is minimal. Whisper does not produce context-based predictions or make speculative guesses for incomprehensible words unless a prompt is provided, which may have a slight influence. This effect only becomes more pronounced with specialized fine-tuning or when an additional Large Language Model (LLM), such as GPT-4 or DeepSeek-R1, is applied to the output text.

Despite these limitations, Whisper excels at processing speech even when inaudible or unintelligible. For example, if someone speaks while covering their mouth, Whisper can often transcribe full sentences by supplementing missing information as needed.

Choosing a larger Whisper model improves its accuracy. However, it's important to note that Playlist4Whisper doesn't enhance transcription accuracy by adding tokens from previous chunks processed. This is because smaller models don't see much benefit from the added complexity, and we often encounter the well-known problem of hallucinations and other behaviors. If accuracy is your top priority and your computer has sufficient power, using a larger model and longer step time would be optimal, resulting in fewer audio splits. Nonetheless, hallucinations and other errors could occur with large chunks.

Alternatively, you can generate subtitles for local audio/video files. This feature supports any model size with any processor; the only limitation is the processing time. When generating subtitles, the AI takes into account the maximum tokens supported by this implementation of OpenAI's Whisper AI. It's important to note that while this feature is powerful, users might still occasionally experience minor text inconsistencies or, more rarely, a phenomenon where the transcription appears to loop on a repeated phrase. This latter behavior, along with other types of 'hallucinations' (generating text not present in the audio), are recognized limitations of current AI transcription models like Whisper.

If you wish, you can try the optional Chrome extension for transcribing audio and video solely from web pages; note that its translation capabilities are limited to English. Otherwise, with the exception of subtitle generation for locally stored files, the playlist4whisper and livestream_video.sh applications should be primarily viewed as helpful tools for understanding video and audio content, capable of transcribing or translating a significant portion, though not always with complete coverage. This is still a significant capability, considering Whisper AI's extensive language support and accuracy in a variety of scenarios. However, at least with present versions, users should not expect perfectly exact results; if high precision is critical, exploring alternative solutions might be more appropriate.

**Q: Sometimes the transcriptions are wrong or not appears, what could be the issue?**

A: The AI model is designed to transcribe audio from various situations, but certain factors can affect its accuracy. For instance, challenging accents or voice tones, or changes in voices during conversations can pose difficulties. In the future, the addition of sound filters options aims to minimize these issues. Additionally, the model may occasionally produce incorrect transcriptions due to gaps in its neural network connections. This can happen more frequently with smaller or quantized models, as well as with languages that have not been extensively trained.

**Q: Sometimes when I generate a subtitle, the text is ruined and gets stuck with a repeated phrase.**

A: This is one of the well-known limitations of the current version of OpenAI's Whisper AI, known as hallucinations. This issue persists even with larger models and is even more problematic in the latest and more accurate larger-v3 model. You could try using a different model or attempt to divide the audio/video file into various chunks. The optional OpenAI Whisper executable could help reduce hallucinations when generating subtitles, you could run different executables simultaneously, each with its own 'playlist4whisper' copied into a separate directory, along with its own playlist files. However, many parameters are shared among users, and as of yet, no one has discovered "the magic formula".

**Q: The transcriptions I get are not accurate?**

A: The quality of the transcriptions depends on several factors, especially the size of the model chosen. Larger models generally yield better results, but they also require more processing power. The English models tend to perform better than models for other languages. For languages other than English, you may need to use a larger model. If you choose the option auto for language autodetection or translate for simultaneous translation to English, it may also significantly increase processor consumption.

**Q: smplayer does not work with online TV?**

A: First, check if you have passed a player option that is not compatible with smplayer. smplayer depens of mpv or mplayer, the installed version of mplayer may not support online video streams, depending on how it was compiled or its configurations, or there may be conflicts with video encoding libraries used by mplayer. In general, mpv is a better option, or if you prefer smplayer, make sure it is configured to use mpv.

**Q: Is this program legal to watch TV channels?**

A: Yes, many of the URLs for channels found on the internet are made freely accessible by companies, governments, or public institutions for personal use only. Channels that may be restricted to a specific country or region for copyright reasons cannot be viewed, as the broadcasting company typically blocks viewers with IPs from other countries. However, playlists found on the internet may contain some channels with legality that is not entirely clear. Even if their URLs are publicly known, direct distribution or commercialization of the television channel is likely not allowed.

In the case of YouTube and Twitch, watching channels through standalone applications such as `yt-dlp` or `streamlink` poses a conflict with the companies, as they cannot control the advertisements you see. In other words, they are not interested in this approach and may make it difficult or prevent you from accessing their video streams.




[<img src="https://github.com/antor44/livestream_video/blob/main/Paypal-QR-Button.png">](https://www.paypal.com/donate/?business=D2SKZRE6RVAZG&no_recurring=0&item_name=Your+donation+powers+our+commitment+to+providing+free%2C+efficient+transcription+%26+translation+tools.+Thank+you+for+contributing.&currency_code=EUR)
