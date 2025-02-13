# playlist4whisper

playlist4whisper - displays a playlist for 'livestream_video.sh' and plays audio/video files or video streams, transcribing the audio using AI technology. The application supports a fully configurable timeshift feature, multi-instance and multi-user execution, allows for changing options per channel and global options, online translation and Text-to-Speech with translate-shell, and audio device inputs. All of these tasks can be performed efficiently even with low-level processors. Additionally, it generates subtitles from audio/video files.


Author: Antonio R. Version: 2.60 License: GPL 3.0

#
# Quick start

playlist4whisper and livestream_video.sh is based on whisper.cpp and also supports OpenAI's Whisper. It depends on other executables and libraries. Please ensure that mpv, smplayer, translate-shell, vlc, ffmpeg, python3-tk, python3-pip, bc, and xterm are installed.

To install whisper-cpp, choose one of these options (you can install all, Whisper-cpp executables are prioritized, with ./main executable being the first choice):
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
For the latest version of whisper-cpp or to compile an accelerated version, follow the instructions provided at https://github.com/ggerganov/whisper.cpp


The required model files must be stored in the subdirectory ./models. They can be automatically downloaded using playlist4whisper (this feature is only supported for the compiled version of whisper-cpp), or you can follow the instructions provided at https://github.com/ggerganov/whisper.cpp/blob/master/models/README.md

Please note that the model installed by playlist4whisper may not be optimized for an accelerated version of Whisper-cpp.

OpenAI's Whisper automatically downloads the required model if it does not exist. Keep in mind that its format is different from the whisper-cpp model.


#
# Detailed installation for linux


1. Download and build whisper-cpp to a new directory following the instructions provided in the documentation at https://github.com/ggerganov/whisper.cpp

Download the source code of whisper-cpp from your home directory:

```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Change the default directory to the whisper-cpp directory, which is whisper.cpp:
```
cd whisper.cpp
```
Compile whisper-cpp for CPU mode:
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
playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper-cpp.

This program depends on other Linux programs and their libraries, such as Python, whisper.cpp and mpv. For example, Ubuntu Linux users can install the following packages:
```
sudo apt-get install mpv smplayer translate-shell vlc ffmpeg python3-tk python3-pip bc xterm
```
For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp), for Twitch and Others streamlink is required (https://streamlink.github.io).

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

3. Finally, you can launch the app by entering the following command in the terminal:
```
python3 playlist4whisper.py
```
Before using VLC go to Tools->Preferences and Show setting: All. Then Interface->Main Interfaces-> Qt-> Uncheck: 'Resize interface to the native video size', and 'When to raise the interface'-> Never. Ensure that VLC is configured to repeat the playlist infinitely, not just the current file, and save the configurations.

For multi-instances with SMPlayer: Go to Preferences - Interface - Instances, and turn off the option to use only one instance.
#
# Detailed Installation for macOS

You can run playlist4whisper.py on macOS by following these steps:

1. Install Homebrew by visiting https://brew.sh/ and following the installation instructions.

2. Once Homebrew is installed, open a terminal and install the required dependencies. Run the following commands:

```
brew install make
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
```

3. playlist4whisper has been successfully tested on the macOS Ventura Intel version and can also run on Big Sur with some extra adjustments.
  
Homebrew has introduced significant changes and issues in the latest versions of the applications needed by playlist4whisper. First of all, there have been changes in the behavior of installing Python applications, likely to improve stability or security. Depending on how Python was installed or updated, you may need to adjust your system settings to begin using a Python environment and to detect the new Python version. Please follow the instructions provided in the terminal when installing Python3.

Additionally, for older macOS version, like Big Sur, due to misconfigurations, outdated default libraries in older macOS versions, or conflicts between Homebrew and macOS, you might encounter issues when installing Homebrew applications. Alternatively, you can install older version of applications like FFmpeg (separately from FFplay and FFprobe, which are also necessary), VLC, SMPlayer, and MPV from other sources, downloading them individually. If you trust the source, just copy the executable packaged as a .app file to the Applications folder and then link the path to /usr/local/bin/[executable]. Make sure to use the executable name in lowercase for the /usr/local/bin/ part:
```
ln -s /Applications/[executable].app/Contents/MacOS/[executable] /usr/local/bin/[executable]
```
or
```
ln -s /Users/[user]/[directory]/[executable] /usr/local/bin/[executable]
```
If the app isn't signed, you'll need to grant it permission in your system.


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


5. Compile whisper-cpp following the instructions provided in the documentation at https://github.com/ggerganov/whisper.cpp, or for CPU mode, just follow these instructions:

From your base user directory (/Users/[user]) download the source code for whisper-cpp:
```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Change the default directory to the whisper-cpp directory:
```
cd whisper.cpp
```
Compile whisper-cpp for CPU mode:
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
playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper-cpp and its 'main' executable.


6. Finally, you can launch the app by entering the following command in the terminal:
```
python3 playlist4whisper.py
```

Please note that on macOS, only the xterm terminal and the mpv video player are supported. Additionally, the xterm terminal automatically closes its window when Control+C is used.

#
# Detailed installation for Windows 10/11

playlist4whisper can run on Windows Subsystem for Linux (WSL2), which is the default virtual system on Windows 10/11 for running native Linux software. Keep in mind that WSL2 may not provide the same level of stability and smooth performance as Linux or macOS. When using the VLC player, which is required for one of the main features, you might run into audio issues with the default settings. Nevertheless, you can also compile whisper-cpp with GPU acceleration or install a whisper-cpp Docker image, which also supports GPU acceleration.

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
sudo apt-get install mpv smplayer translate-shell vlc ffmpeg python3-tk python3-pip bc gnome-terminal xterm
```
For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp), for Twitch and Others streamlink is required (https://streamlink.github.io).

The easy way to install yt-dlp and streamlink:
```
pip3 install yt-dlp
```
```
pip3 install streamlink
```
Or to upgrade them:
```
pip3 install --upgrade yt-dlp
```
```
pip3 install --upgrade streamlink
```
Download the source code of whisper-cpp:

```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Change the default directory to the whisper-cpp directory:
```
cd whisper.cpp
```
Compile whisper-cpp for CPU mode:
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
playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper-cpp, whisper.cpp

Finally, you can launch the app by entering the following command in the terminal:
```
python3 playlist4whisper.py
```
MPV player is not working on Windows, potentially due to the need for additional configuration and/or installation of packages.

#
# Usage: 

**Warning: When updating, you may need to delete your previous configuration files in the installation directory: config_iptv.json, config_youtube.json, config_twitch.json and others config_xxx.json.**

**To use the Timeshift feature, ensure that VLC is configured to repeat the playlist infinitely, not just the current file.**

**Ensure that your installed yt-dlp and streamlink are up-to-date.**

Make sure that you are in the same directory as whisper-cpp, playlist4whisper.py, and livestream_video.sh:

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

#
# livestream_video.sh

This is a command-line program with the same transcription functions as playlist4whisper and can be run independently of this GUI/frontend, options are set via parameters in a terminal or create a shortcut on your desktop for each TV channel.

livestream_video.sh is a linux script to transcribe video livestream by feeding ffmpeg output to whisper.cpp at regular intervals, based on livestream.sh from whisper.cpp:

https://github.com/ggerganov/whisper.cpp

The text-to-speech feature and translation to languages other than English are performed via the internet, thanks to the Translate-shell app, which utilizes a free Google service. However, the availability of this service is not guaranteed and the text-to-speech feature only works for short segments of a few seconds and is limited to certain languages.
#

Some notable features:

- Supports a fully configurable timeshift feature, exclusive to VLC player (not all streams supported)
- Support for IPTV, YouTube, Twitch. Supports a wide range of video services through streamlink or yt-dlp, including: Dailymotion, Vimeo, Livestream, Ustream, Facebook, and many more
- List of supported sites by streamlink (not all supported or outdated): https://streamlink.github.io/plugins.html
- List of supported sites by yt-dlp (not all supported or outdated): https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
- Online translation and Text-to-Speech with translate-shell (https://github.com/soimort/translate-shell).
- Generates subtitles from audio/video files.
- Support for multi-instance and multi-user execution (To use this feature with SMPlayer: Go to Preferences -> Interface -> Instances, and disable the option to use only one instance)
- Language command-line option "auto" (for autodetection), "en", "es", "fr", "de", "he", "ar", etc., and "translate" for translation to English
- Quantized models support
- MacOS support.
- Audio inputs, including loopback devices, to transcribe what you hear on the desktop. Supported for Linux, macOS, and Windows WSL2.

#
Usage: ./livestream_video.sh stream_url [or /path/media_file or pulse:index or avfoundation:index] [--step step_s] [--model model] [--language language] [--translate] [--subtitles] [--timeshift] [--segments segments (2<n<99)] [--segment_time minutes (1<minutes<99)] [--sync seconds (0 <= seconds <= (Step - 3))] [--trans trans_language output_text speak] [player player_options]

Example:
```
./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 --step 8 --model base --language auto --translate --subtitles --timeshift --segments 4 --segment_time 10 --trans es both speak
```
Only for the bash script and only for local audio/video: Files must be enclosed in double quotation marks, with the full path. If the file is in the same directory, it should be preceded with './'


pulse:index or avfoundation:index: Live transcription from the selected device index. Pulse for PulseAudio for Linux and Windows WSL2, AVFoundation for macOS. The quality of the transcription depends on your computer's capabilities, the chosen model, volume and sound configuration on your operating system, and the noise around you. Please note that this is a preliminary feature. There are several seconds of delay between live sound and transcriptions, with no possibilities for synchronization.

--streamlink:    Forces the URL to be processed by Streamlink.

--yt-dlp:        Forces the URL to be processed by yt-dlp.

--quality:       Video quality options are 'raw,' 'upper,' and 'lower'. Quality also affects when timeshift is active for IPTV.
'Raw' is used to download another video stream without any modifications for the player.
'Upper' and 'lower' download only one stream that is re-encoded for the player, which might correspond to the best or worst stream quality.
This is intended to save downloaded data, although not all streams support it. Additionally, with timeshift, only one stream is downloaded.

--player:        Specify player executable and options. Valid players: smplayer, mpv, mplayer, vlc, etc. Use 'none' or 'true' for no player.

--step:          Size of the sound parts into which videos are divided for AI inference, measured in seconds.

--model:         Whisper Models:

tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3

with suffixes: -q2_k, -q3_k, -q4_0, -q4_1, -q4_k, -q5_0, -q5_1, -q5_k, -q6_k, -q8_0

--language:      Whisper Languages:

auto (Autodetect), af (Afrikaans), am (Amharic), ar (Arabic), as (Assamese), az (Azerbaijani), be (Belarusian), bg (Bulgarian), bn (Bengali), br (Breton), bs (Bosnian), ca (Catalan), cs (Czech), cy (Welsh), da (Danish), de (German), el (Greek), en (English), eo (Esperanto), es (Spanish), et (Estonian), eu (Basque), fa (Persian), fi (Finnish), fo (Faroese), fr (French), ga (Irish), gl (Galician), gu (Gujarati), ha (Bantu), haw (Hawaiian), he ([Hebrew]), hi (Hindi), hr (Croatian), ht (Haitian Creole), hu (Hungarian), hy (Armenian), id (Indonesian), is (Icelandic), it (Italian), iw (Hebrew), ja (Japanese), jw (Javanese), ka (Georgian), kk (Kazakh), km (Khmer), kn (Kannada), ko (Korean), ku (Kurdish), ky (Kyrgyz), la (Latin), lb (Luxembourgish), lo (Lao), lt (Lithuanian), lv (Latvian), mg (Malagasy), mi (Maori), mk (Macedonian), ml (Malayalam), mn (Mongolian), mr (Marathi), ms (Malay), mt (Maltese), my (Myanmar), ne (Nepali), nl (Dutch), nn (Nynorsk), no (Norwegian), oc (Occitan), or (Oriya), pa (Punjabi), pl (Polish), ps (Pashto), pt (Portuguese), ro (Romanian), ru (Russian), sd (Sindhi), sh (Serbo-Croatian), si (Sinhala), sk (Slovak), sl (Slovenian), sn (Shona), so (Somali), sq (Albanian), sr (Serbian), su (Sundanese), sv (Swedish), sw (Swahili), ta (Tamil), te (Telugu), tg (Tajik), th (Thai), tl (Tagalog), tr (Turkish), tt (Tatar), ug (Uighur), uk (Ukrainian), ur (Urdu), uz (Uzbek), vi (Vietnamese), vo (Volapuk), wa (Walloon), xh (Xhosa), yi (Yiddish), yo (Yoruba), zh (Chinese), zu (Zulu)

--translate:      Automatic English translation using Whisper AI (English only).

--subtitles:      Generate subtitles from an audio/video file, with support for language selection, Whisper AI translation, and online translation to any language. A .srt file will be saved with the same filename and in the same directory as the source file.

 --trans:          Online translation and Text-to-Speech with translate-shell (https://github.com/soimort/translate-shell). 
    trans_language: Translation language for translate-shell. 
    output_text: Choose the output text during translation with translate-shell: original, translation, both, none. 
    speak: Online Text-to-Speech using translate-shell.

--timeshift:      Timeshift feature, only VLC player is supported.

--sync:           Transcription/video synchronization time in seconds (0 <= seconds <= (Step - 3)).

--segments:       Number of segment files for timeshift (2 <= n <= 99).

--segment_time:   Time for each segment file (1 <= minutes <= 99).

#

## playlist4whisper Screenshots:
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV6.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV2.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV8.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV7.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV9.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV10.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV11.jpg)
#
## livestream_video.sh screenshots:
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV3.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV4.jpg)

#
# To-Do List

- Voice activity detection (VAD) for splitting audio into chunks
- Advanced GUI as a standalone application
- Support for different AI engines
- Sound filters
- ...

#
# FAQ

**Q: What quality of transcription can I expect when using only a low-level processor?**

A: This program is based on whisper-cpp, which is a highly optimized implementation of OpenAI's Whisper AI. The performance of the transcription largely depends on this software. For English language, you can expect very good transcriptions of video streams or media files even on low-end or old PCs, even those that are at least 10 years old. You can easily configure the application with models such as small.en or base.en, which offer excellent transcriptions for the English language. Even the tiny.en model, despite its small size, provides great results. However, transcriptions of other major languages are not as good with small models, and minority languages do not perform well at all. For these, you will need a better CPU or a supported GPU.

**Q: Why isn't there a precompiled and packaged distribution for the program "playlist4whisper"?**

A: The absence of a precompiled and packaged distribution for "playlist4whisper" is due to the constant changes and optional optimizations in the underlying "whisper-cpp" Linux program. Providing the source code allows users to adapt to these modifications and optimize performance based on their hardware and preferences.

Additionally, "playlist4whisper" relies on the included bash script "livestream_video.sh". This script can be executed independently, supporting accessibility technologies. It can also run on Linux terminals without a desktop environment and potentially be used as a server application in multi-instance and multi-user scenarios, making it versatile for various use cases. By providing the source code, advanced users can review or customize the programs to suit their specific requirements and environments.

**Q: What's the use of the loopback ports? Could I see my videos from the internet?**

A: Loopback ports are needed for features like timeshift, and for upper and lower video quality options. The application uses one port to communicate with VLC for information about the currently playing video, or is used by ffmpeg to stream video to mpv or smplayer. The loopback interface is a virtual network interface per user that by default is not accessible outside your computer, although you can configure your firewall and network interfaces to control VLC and transmit video outside to the internet using VLC's streaming option. However, this would not include live transcriptions, only subtitles. Nevertheless, there are some solutions to stream your entire desktop with decent image quality over the internet, NoMachine (freeware) or Moonlight (open source license) are both great options.

**Q: Some streams don't work, especially with upper and lower qualities, and sometimes timeshift doesn't work?**

A: Streams can often experience interruptions or temporary cuts, and their proper functioning in playlist4whisper can also depend on the ads they insert, and in other cases on whether yt-dlp and streamlink support the frequent changes made by various online video providers.

In general, processing online videos is very difficult due to the nature of different video codecs and network protocols used on servers and their various implementations, or due to incorrect timestamps and metadata information, or because of the difficulty of recording and cutting videos with ffmpeg. To add the somewhat random nature of the artificial intelligence algorithm for transcription.

**Q: How does timeshift work and where are the files stored? Can I save these videos?**

A: Timeshift functions similarly to other applications, but in playlist4whisper, it involves a playlist repeated indefinitely with temporary videos or buffers. You can configure the number of these buffers and their size in minutes. For example, from just a few minutes up to a maximum of 99 videos, each lasting 99 minutes. This allows for a maximum of 163 hours of live streaming for timeshift, although at the cost of requiring a very large amount of disk space. When the chosen maximum size is reached, the oldest video file is deleted, and this process continues indefinitely until the application is stopped or an error occurs.

The videos can be navigated in VLC as if it were a playlist with multiple videos, allowing you to switch between videos or rewind and fast forward within a single video. However, you should be cautious not to approach the current live recording moment too closely, as the player may jump to another video. The transcription will automatically switch to the chosen point.

The temporary video buffer files can be saved in another directory, they will have names similar to whisper-live_131263_3.avi, or for the last one being recorded, whisper-live_131263_buf033.avi. The files are stored in the /tmp directory in both Linux and macOS, which typically serves as the temporary directory and is usually cleared upon restarting the computer.

**Q: What can Playlist4Whisper do in terms of transcribing or translating sound card or sound device inputs? Are USB devices supported in Linux?**

The quality of the transcription depends on your computer's capabilities, the chosen model, volume, and sound configuration on your operating system, as well as the ambient noise. Please note that this is a preliminary feature. There is a several-second delay between live sound and transcriptions, with no possibility for synchronization.

The capabilities to transcribe audio inputs or 'what you hear' on the desktop exist in numerous scenarios depending on the capabilities of sound cards, webcams, microphones, and USB-connected headphones. In Linux, USB sound cards and sound integrated into webcams, microphones, and headphones might be problematic, especially for devices that are too old or too new. Sometimes you may need to install device controllers or modules for Linux. Most USB drivers are usually available in one of three ways: within the kernel, as a compilable standalone module, or available as a pre-compiled (packaged) binary driver from your Linux distribution. However, sometimes these devices or their modules are deactivated in the Linux kernel. Although this is a rare situation, it may occur if Windows WSL2 uses a Linux kernel with deactivated device controllers, or requires some configurations. Anyway, you may encounter issues when using these devices in a Linux virtualized environment on WSL2.

Apart from device drivers or Linux modules, operating systems could use different libraries or sound systems. Playlist4Whisper depends on PulseAudio for Linux and Windows WSL2, and AVFoundation for macOS. If you use other libraries, your operating system might require software wrappers to ensure compatibility between different software sound systems.

Sound cards or devices in duplex mode support recording and listening simultaneously; you may need to configure your sound card for duplex mode. Some models allow different mixes or combinations for recording multiple inputs and simultaneous playback, while there is also software available, both free and paid, that enables this functionality. For Linux, devices suffixed with 'monitor' are loopback devices that allow you to record all sounds 'what you hear' on your desktop. Some sound cards or Linux distributions need to activate this feature with PulseAudio commands, or you could add links between inputs and outputs of your sound cards by editing your Linux sound card configuration files. These devices, along with applications, can be configured individually using PulseAudio Volume Control. For macOS, you can only use loopback devices through a virtual device with an Audio Loopback Driver like Blackhole (free license), Loopback (commercial license) or VB-Cable (donationware).

Windows supports loopback sound for native applications through a virtual driver, such as VB-Cable (donationware), which is an additional piece of software similar to those used in macOS. However, Playlist4Whisper is executed in the Linux virtual environment WSL2. Sound capacities depend on each Linux application and on PulseAudio and Microsoft support for virtualized sound in WSL2. Currently, the default virtualized system in WSL2 or WSLg (Windows Subsystem for Linux GUI) can utilize PulseAudio, albeit through an RDP (Remote Desktop Protocol) loopback network connection, which is not the optimal solution.

**Q: Is it possible to achieve speech translation from a microphone without delay?**

A: There are few possibilities to achieve something similar to real-time or live transcriptions or speech translations. Different approaches exist for Speech-to-Speech translation systems: one involves a step-by-step process utilizing various specialized AI models, ranging from two to four steps. Another approach is a multimodal or all-in-one AI that handles all steps using a single model, like the SeamlessM4T free AI from Meta, which is currently in its early development stage. Neither approach can achieve real-time or live translations, nor anything resembling "near-live," due to the necessity of processing the input speech by dividing the recorded sound into small chunks. This is mainly due to contextual challenges or the differing nature of languages, which require the AI to understand the context of phrases or even anticipate what the speaker is going to say, akin to a wizard's alchemy. While it may be possible to introduce some shortcuts to shorten the steps, these tricks may not be suitable for a scientific solution or for accurate translation, as they could lead to reductionism or reinterpretations of what the speaker is saying. Some applications use a trick to achieve a near-live result during the transcription step, even with a Whisper AI and low-power computers, which playlist4whisper will support in the near future. This trick involves rapidly transcribing live speech without context and immediately reintroducing the same sound data continuously to correct any possible errors in the last seconds transcribed. With this solution, the last words may frequently change, but it's not a significant issue for the user. However, this reintroduction trick cannot be applied to the speech translation step, as it is not serious to hear a translation of a sentence, and then the AI might repeatedly change the sentence because the initial version was incorrect.

![Live Transcription](https://github.com/antor44/livestream_video/blob/main/live-transcription.jpg)

**Q: Why is the program not working?**

A: There could be various reasons why the script/program is not functioning correctly. It relies on other Linux programs and their libraries, such as whisper.cpp and mpv. To compile the main executable, your operating system must have the necessary tools and development libraries installed, including those related to the chosen acceleration options. If you are not familiar with compilation, errors can often occur due to missing development libraries in your operating system. You will need to install only the necessary development libraries and the specific or compatible versions used by whisper-cpp. The main executable from whisper.cpp needs to be placed in the same directory as playlist4whisper.py and the script livestream_video.sh. By default, this executable should be named 'main'. Additionally, it is crucial to have the Whisper model files in the "models" directory, following the correct format and name used by Whisper.cpp. These tasks can be accomplished using terminal commands:

First clone the repository:
```
git clone https://github.com/ggerganov/whisper.cpp.git
```
Now change directory to the whisper-ccp folder and build the main example to transcribe an audio file using the following command.

Build the 'main' example:
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
./main -f samples/jfk.wav
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

**Q: When I run the script, I always encounter an error related to the "main" executable.**

A: There could be various reasons for this error. The "main" executable is one of the examples provided in whisper.cpp, a high-level implementation of OpenAI's Whisper AI. The executable's name should remain as the default "main" and reside in the same directory as playlist4whisper.py and the bash script livestream_video.sh. Ensure that both the main executable and livestream_video.sh have executable permissions, at least for the current user. Additionally, the models you use should be stored in the "models" subdirectory, which are created by running terminal commands like "make base.en" or "make tiny.en". It's important to note that quantized models and large-v3 may not be compatible with older versions of whisper.cpp, which could lead to a "main error". After building the main example using the terminal command "make", you can test an audio file example using the command (for model base.en): ./main -f samples/jfk.wav

**Q: Can I run playlist4whisper without using the terminal, from a desktop shortcut on Linux?**

A: Yes, you can run it with the command "python" followed by the full path of playlist4whisper.py, or if you are using an Anaconda environment: "/home/[user]/anaconda3/bin/conda run python /home/[user]/[app directory]/playlist4whisper.py". In both cases, provide the working directory where the program is located.

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

**Q: Why does the beginning and end of the transcription often get lost?**

A: Most of the time, this occurs because the application lacks a voice activity detection (VAD) system to split the audio during silent intervals. The current versions of the bash script segment sound files into chunks based on user-selected durations, which may result in the truncation or deletion of words at the beginning and end of each chunk. Additionally, sometimes, there may be cut-offs of a few words at the start or end, either caused by the difficulty in obtaining precise data on video synchronization or timestamps, or this issue could be caused by gaps in the Whisper AI's neural network.

Regarding the low-level development of the IA utilized by `playlist4whisper.py` or `livestream_video.sh`, OpenAI states: "The Whisper architecture is a simple end-to-end approach, implemented as an encoder-decoder Transformer. Input audio is split into 30-second chunks, converted into a log-Mel spectrogram, and then passed into an encoder. A decoder is trained to predict the corresponding text caption, intermixed with special tokens that direct the single model to perform tasks such as language identification, phrase-level timestamps, multilingual speech transcription, and English speech translation".

In essence, Whisper is an automatic speech recognition (ASR) system trained on 680,000 hours of multilingual and multitask supervised data collected from the web. The latest and largest model, large-v3, has been trained with over one million hours of labeled audio and over four million hours of audio. The sound is converted into spectrogram images, specifically into log-Mel spectrogram images, similar to other AIs that process input sound directly. These same spectrogram images are used to convert new sound files for inference or speech processing.

Additionally, Whisper utilizes a GPT-2 model, which incorporates a tokenizer responsible for breaking down input text into individual units called tokens. In the case of Whisper, the tokenizer employs the same set of Byte-Pair Encoding (BPE) tokens as the GPT-2 model for English-only models, with additional tokens included for multilingual models. GPT-2 is a Transformer-based language model trained to predict the next wordpiece without explicit supervision. Its purpose is to fill in gaps and address sound issues to accurately transcribe coherent words within context, with a maximum of the last 224 tokens processed (approximately 168 words). Whisper can effectively process speech even when it's inaudible or unintelligible. For instance, if someone speaks while covering their mouth with their hand, Whisper can often transcribe entire speeches, supplementing missing information when necessary.

Choosing a larger Whisper model improves its performance. However, it's important to note that playlist4whisper doesn't enhance transcription accuracy by adding tokens from previous chunks processed. This is because smaller models don't see much benefit from the added complexity, and I often encounter the well-known problem of hallucinations. If accuracy is your top priority and your computer has sufficient power, using a larger model and longer step time would be optimal, resulting in fewer audio splits. Nonetheless, there are many instances where this token system is ineffective for truncated words, so I plan to integrate a VAD system in the near future.

Alternatively, you can generate subtitles for local audio/video files. This feature supports any model size with any processor; the only limitation is the processing time. When generating subtitles, the AI takes into account the maximum tokens supported by this implementation of OpenAI's Whisper AI.

**Q: Sometimes the transcriptions are wrong or not appears, what could be the issue?**

A: The AI model is designed to transcribe audio from various situations, but certain factors can affect its accuracy. For instance, challenging accents or voice tones, or changes in voices during conversations can pose difficulties. In the future, the addition of sound filters options aims to minimize these issues. Additionally, the model may occasionally produce incorrect transcriptions due to gaps in its neural network connections. This can happen more frequently with smaller or quantized models, as well as with languages that have not been extensively trained.

**Q: Sometimes when I generate a subtitle, the text is ruined and gets stuck with a repeated phrase.**

A: This is one of the well-known limitations of the current version of OpenAI's Whisper AI, known as hallucinations. This issue persists even with larger models and is even more problematic in the latest and more accurate larger-v3 model. You could try using a different model or attempt to divide the audio/video file into various chunks. The optional OpenAI Whisper executable could help reduce hallucinations when generating subtitles, you could run different executables simultaneously, each with its own 'playlist4whisper' copied into a separate directory, along with its own playlist files. However, many parameters are shared among users, and as of yet, no one has discovered "the magic formula".

**Q: The transcriptions I get are not accurate?**

A: The quality of the transcriptions depends on several factors, especially the size of the model chosen. Larger models generally yield better results, but they also require more processing power. The English models tend to perform better than models for other languages. For languages other than English, you may need to use a larger model. If you choose the option auto for language autodetection or translate for simultaneous translation to English, it may also significantly increase processor consumption.

**Q: What audio file types are supported? How could I play sound files with subtitles generated by playlist4whisper?**

A: The audio file types supported by playlist4whisper are all those supported by the version of ffmpeg installed in your operating system. You can play audio files with subtitles using players like VLC or MPV. For VLC, you need to configure it to display something while playing sound files, such as a Spectrometer. For MPV, you can either configure its configuration file or add the MPV option '--force-window' in playlist4whisper (without single quotes) and play the file with 'Player Only' set to show a window with the subtitles for audio files.

**Q: In a low-power processor, is it possible to improve transcription in languages other than English?**

A:  Yes, if you have knowledge of AI programming, you will need to fine-tune a default model by retraining it with a dataset of voices along with their transcriptions in a specific language, or to improve an accent, slang or dialect. Some datasets can be found online, as well as sample codes for fine-tuning a Whisper model. Whisper models must be converted to ggml format, to convert Whisper models to ggml format yourself, instructions are at: https://github.com/ggerganov/whisper.cpp/blob/master/models/README.md

You can also try using the quantized models option, which can improve execution speed on certain processors.
 
Alternatively, instead of running the AI engine on the CPU, you can try compiling whisper.cpp with partial GPU support using the cuBLAS library for Nvidia graphics cards or GPUs, or compile it with partial OpenCL GPU support using the CLBlast library for all graphics cards or GPUs, including Nvidia, AMD, and Intel, or compile using OpenVINO for Intel GPUs. By doing so, you can significantly increase the execution speed by at least x2 or even more, depending on the GPU model you have, and this will allow you to run larger whisper models:

https://github.com/ggerganov/whisper.cpp#nvidia-gpu-support-via-cublas

There should be no issues running the program on Apple computers with ARM processors, whisper.cpp can be compiled to be executed on the Apple Neural Engine (ANE) via Core ML. This can result in a significant speed-up, more than x3 faster compared to CPU-only execution:

https://github.com/ggerganov/whisper.cpp#core-ml-support

The accelerated versions of whisper-cpp require specific model versions to achieve better performance.

**Q: How much data is needed to fine-tune a model?**

A: Fine-tuning a Whisper model might be more difficult and costly than expected; you must collect that specific information yourself. Some users report success with a relatively short amount of data, while others couldn't obtain significant improvements. It depends on the quality of the language already supported by Whisper and its similarities with other languages supported by Whisper. It also depends on the quality of the dataset for training. It's clear that having as much data as possible is better; perhaps thousands of hours of short sound chunks with their transcriptions. You might be able to fine-tune with large free datasets like Common Voice. You can find the latest version of the Common Voice dataset by checking the [Mozilla Foundation](https://commonvoice.mozilla.org) page or the [Hugging Face Hub](https://huggingface.co/mozilla-foundation). Keep in mind that OpenAI already utilized Common Voice datasets for the validation task during its training, so it's possible that some datasets or languages may not improve Whisper's models as expected. Nonetheless, some minority languages like Catalan, Esperanto and Basque have a significant number of hours in Common Voice, while one of the major languages like Spanish has a very poor dataset. If you want to fine-tune for a more specific use, then you might need a lot of effort or cost to collect enough data with the needed quality, although the dataset would be smaller for improving technical words, slang, or a specific accent of a local region for an already well-supported language.

**Q: smplayer does not work with online TV?**

A: First, check if you have passed a player option that is not compatible with smplayer. smplayer depens of mpv or mplayer, the installed version of mplayer may not support online video streams, depending on how it was compiled or its configurations, or there may be conflicts with video encoding libraries used by mplayer. In general, mpv is a better option, or if you prefer smplayer, make sure it is configured to use mpv.

**Q: Is this program legal to watch TV channels?**

A: Yes, of course, many of the URLs of channels that you find published on the internet are proactively accessible for free use thanks to companies, governments or public institutions, as long as it is for personal use only. Channels that may be restricted to a country or region for copyright reasons cannot be viewed, and the broadcasting company blocks viewers with IPs from other countries. However, the playlists that are found on the internet may contain some channels with legality that is not entirely clear, even if their URLs are publicly known, it is likely that direct distribution of the signal or commercialization of the television channel is not allowed.
 
In the case of YouTube and Twitch, watching channels through standalone applications such as yt-dlp or streamlink poses a conflict with the companies as they cannot control the advertisements you see. In other words, they are not interested in this approach and may make it difficult or prevent you from accessing their video streams.




[<img src="https://github.com/antor44/livestream_video/blob/main/Paypal-QR-Button.png">](https://www.paypal.com/donate/?business=D2SKZRE6RVAZG&no_recurring=0&item_name=Your+donation+powers+our+commitment+to+providing+free%2C+efficient+transcription+%26+translation+tools.+Thank+you+for+contributing.&currency_code=EUR)
