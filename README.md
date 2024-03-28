# playlist4whisper GUI

**Warning: When updating, you may need to delete your previous configuration files in the installation directory: config_iptv.json, config_youtube.json, config_twitch.json and others config_xxx.json.**

**To use the Timeshift feature, ensure that VLC is configured to repeat the playlist infinitely, not just the current file.**

**Ensure that your installed yt-dlp and streamlink are up-to-date.**

Playlist4Whisper is an application designed to display playlists for 'livestream_video.sh'. It plays online videos and utilizes AI technology to transcribe audio into text. The application supports a fully configurable timeshift feature, multi-instance and multi-user execution, and allows for changing options per channel and global options.


Author: Antonio R. Version: 2.08 License: GPL 3.0


#
# Installation

1. Download and build whisper-cpp to a new directory, then download some models following the instructions provided in the documentation at https://github.com/ggerganov/whisper.cpp

2. Download and unzip the default playlist4whisper.py, livestream_video.sh and playlist_xxx.m3u files, they should all be located in the same directory as whisper-cpp.

3. Finally, you can launch the GUI by entering the following command in the terminal. Make sure that you are in the same directory as whisper-cpp, playlist4whisper.py, and livestream_video.sh.
```
python3 playlist4whisper.py
```

This program depends on other Linux programs and their libraries, such as Python, whisper.cpp and mpv. For example, Ubuntu Linux users can install the following packages:
```
sudo apt-get install mpv smplayer vlc ffmpeg python3-tk
```
For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp)
For Twitch and Others streamlink is required (https://streamlink.github.io)

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

playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper-cpp. The main executable of whisper.cpp, which is the primary example, should be in the same directory with the default executable name 'main'. Additionally, the whisper model files should be placed in the "models" subdirectory with the correct format and name, as specified in the Whisper.cpp repository. This can be done using terminal commands such as the following examples:
```
make tiny.en
```
```
make small
```
#
# Usage: 

python playlist4whisper.py 

*For help with options, see the livestream_video.sh section.

- Supports a fully configurable timeshift feature, exclusive to VLC player (not all streams supported)
- Support for IPTV, YouTube, Twitch. Supports a wide range of video services through streamlink or yt-dlp, including: Dailymotion, Vimeo, Livestream, Ustream, Facebook, and many more
- List of supported sites by streamlink (not all supported or outdated): https://streamlink.github.io/plugins.html
- List of supported sites by yt-dlp (not all supported or outdated): https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

The program will load the default playlists playlist_iptv.m3u, playlist_youtube.m3u, playlist_twitch.m3u, ...
 and will store options in config_xxx.json.
 

The majority of online video streams should work. Ensure that your installed yt-dlp and streamlink are up-to-date.

Recommended Linux video player (when timeshift is not active): SMPlayer, based on mvp, due to its capabilities to timeshift online streams for synchronized live video with transcription.

For multi-instances with SMPlayer: Go to Preferences - Interface - Instances, and turn off the option to use only one instance.

#
# livestream_video.sh

This is a command-line program with the same transcription functions as playlist4whisper GUI and can be run independently of the GUI, options are set via parameters in a terminal or create a shortcut on your desktop for each TV channel.

livestream_video.sh is a linux script to transcribe video livestream by feeding ffmpeg output to whisper.cpp at regular intervals, based on livestream.sh from whisper.cpp:

https://github.com/ggerganov/whisper.cpp

#

Some notable features:

-Supports a fully configurable timeshift feature, exclusive to VLC player (not all streams supported)
  
-Support for IPTV, YouTube, Twitch, and many others

-Support for multi-instance and multi-user execution (To use this feature with SMPlayer: Go to Preferences -> Interface -> Instances, and disable the option to use only one instance)

-Language command-line option "auto" (for autodetection), "en", "es", "fr", "de", "he", "ar", etc., and "translate" for translation to English

-Quantized models support

-MacOS support.

#

Usage: ./livestream_video.sh stream_url [step_s] [model] [language] [translate] [quality] [ [player executable + player options] ] [timeshift] [sync s] [segments n] [segment_time m]

 [streamlink] option forces the url to be processed by streamlink.
 
 [yt-dlp] option forces the url to be processed by yt-dlp.

   Example (defaults if no options are specified):

    ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 8 base auto raw [mpv]


Quality: The valid options are "raw," "upper," and "lower". "Raw" is used to download another video stream without any modifications for the player.
 "Upper" and "lower" download only one stream and re-encoded for the player, which might correspond to the best or worst stream quality, it is intended to save downloaded data, although not all streams support it.

"[player executable + player options]", valid players: smplayer, mpv, mplayer, vlc, etc... "[none]" or "[true]" for no player.

Step: Size of the parts into which videos are divided for inference, size in seconds.

Whisper models: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3

... with suffixes each too: -q4_0, -q4_1, -q4_2, -q5_0, -q5_1, -q8_0 

Whisper languages (not all fully supported):

auto (Autodetect), af (Afrikaans), am (Amharic), ar (Arabic), as (Assamese), az (Azerbaijani), be (Belarusian),
bg (Bulgarian), bn (Bengali), br (Breton), bs (Bosnian), ca (Catalan), cs (Czech), cy (Welsh), da (Danish),
de (German), el (Greek), en (English), eo (Esperanto), es (Spanish), et (Estonian), eu (Basque), fa (Persian),
fi (Finnish), fo (Faroese), fr (French), ga (Irish), gl (Galician), gu (Gujarati), ha (Bantu), haw (Hawaiian),
he ([Hebrew]), hi (Hindi), hr (Croatian), ht (Haitian Creole), hu (Hungarian), hy (Armenian), id (Indonesian),
is (Icelandic), it (Italian), iw (Hebrew), ja (Japanese), jw (Javanese), ka (Georgian), kk (Kazakh), km (Khmer),
kn (Kannada), ko (Korean), ku (Kurdish), ky (Kyrgyz), la (Latin), lb (Luxembourgish), lo (Lao), lt (Lithuanian),
lv (Latvian), mg (Malagasy), mi (Maori), mk (Macedonian), ml (Malayalam), mn (Mongolian), mr (Marathi), ms (Malay),
mt (Maltese), my (Myanmar), ne (Nepali), nl (Dutch), nn (Nynorsk), no (Norwegian), oc (Occitan), or (Oriya),
pa (Punjabi), pl (Polish), ps (Pashto), pt (Portuguese), ro (Romanian), ru (Russian), sd (Sindhi), sh (Serbo-Croatian),
si (Sinhala), sk (Slovak), sl (Slovenian), sn (Shona), so (Somali), sq (Albanian), sr (Serbian), su (Sundanese),
sv (Swedish), sw (Swahili), ta (Tamil), te (Telugu), tg (Tajik), th (Thai), tl (Tagalog), tr (Turkish), tt (Tatar),
ug (Uighur), uk (Ukrainian), ur (Urdu), uz (Uzbek), vi (Vietnamese), vo (Volapuk), wa (Walloon), xh (Xhosa),
yi (Yiddish), yo (Yoruba), zh (Chinese), zu (Zulu)


translate: The "translate" option provides automatic English translation (only English is available).

timeshift: Timeshift feature, only VLC player is supported.

sync: Transcription/video synchronization time in seconds (0 <= seconds <= (Step - 3)).

segments: Number of segment files for timeshift (2 =< n <= 99).

segment_time: Time for each segment file(1 <= minutes <= 99).


#

## playlist4whisper GUI Screenshots:
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV8.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV9.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV6.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV5.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV10.jpg)
#
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV11.jpg)
#
## livestream_video.sh screenshots:
![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV.jpg)
#
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

**Q: Why isn't there a precompiled and packaged distribution for the program "playlist4whisper"?**

A: The absence of a precompiled and packaged distribution for "playlist4whisper" is due to the constant changes and optional optimizations in the underlying "whisper-cpp" Linux program. Providing the source code allows users to adapt to these modifications and optimize performance based on their hardware and preferences.

Additionally, "playlist4whisper" relies on the included bash script "livestream_video.sh". This script can be executed independently, supporting accessibility technologies. It can also run on Linux terminals without a desktop environment and potentially be used as a server application in multi-instance and multi-user scenarios, making it versatile for various use cases. Providing the source code enables expert users to customize and adapt the programs to their specific needs and environments.

**Q: Some streams don't work, especially with upper and lower qualities, and sometimes timeshift doesn't work?**

A: Streams can often experience interruptions or temporary cuts, and their proper functioning in playlist4whisper can also depend on the ads they insert, and in other cases on whether yt-dlp and streamlink support the frequent changes made by various online video providers.

In general, processing online videos is very difficult due to the nature of different video codecs and network protocols used on servers and their various implementations, or due to incorrect metadata information, or because of the difficulty of recording and cutting videos with ffmpeg. To add the somewhat random nature of the artificial intelligence algorithm for transcription.

**Q: How does timeshift work and where are the files stored? Can I save these videos?**

A: Timeshift functions similarly to other applications, but in playlist4whisper, it involves a playlist repeated indefinitely with temporary videos or buffers. You can configure the number of these buffers and their size in minutes. For example, from just a few minutes up to a maximum of 99 videos, each lasting 99 minutes. This allows for a maximum of 163 hours of live streaming for timeshift, although at the cost of requiring a very large amount of disk space. When the chosen maximum size is reached, the oldest video file is deleted, and this process continues indefinitely until the application is stopped or an error occurs.

The videos can be navigated in VLC as if it were a playlist with multiple videos, allowing you to switch between videos or rewind and fast forward within a single video. However, you should be cautious not to approach the current live recording moment too closely, as the player may jump to another video. The transcription will automatically switch to the chosen point.

The temporary video buffer files can be saved in another directory, they will have names similar to whisper-live0_131263_3.avi, or for the last one being recorded, whisper-live0_131263_buf033.avi. These files are typically stored in the temporary directory, which is /tmp on Linux and OS X, and are usually deleted upon each computer restart.

**Q: Why is the program not working?**

A: There could be various reasons why the script/program is not functioning correctly. It relies on other Linux programs and their libraries, such as whisper.cpp and mpv. The main executable of whisper.cpp, the primary example, needs to be compiled and placed in the same directory as playlist4whisper and the script livestream_video.sh. By default, this executable should be named 'main'. Additionally, it is crucial to have the Whisper model file from OpenAI in the "models" directory, following the correct format and name as specified in the Whisper.cpp repository. This task can be accomplished using terminal commands, for example:

make tiny.en

make small

For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp). For Twitch streamlink is required (https://streamlink.github.io).

**Q: Can I run playlist4whisper without using the terminal, from a desktop shortcut on Linux?**

A: Yes, you can run it with the command "python" followed by the full path of playlist4whisper.py, or if you are using an Anaconda environment: "/home/[user]/anaconda3/bin/conda run python /home/[user]/[app directory]/playlist4whisper.py". In both cases, provide the working directory where the program is located. However, even when running it from a desktop shortcut, it is recommended to use the option to run in a terminal to get error information.

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

**Q: How can I run play4whisper.py on macOS?**

You can run play4whisper.py on macOS by following these steps:

1. Install Homebrew by visiting https://brew.sh/ and following the installation instructions.

2. Once Homebrew is installed, open a terminal and install the required dependencies. Run the following commands:

```
brew install python3
brew install python-tk@3.11
brew install make
brew install xquartz
brew install xterm
brew install vlc
brew install mpv
```

3. Next, install the necessary Python packages using pip3. Run the following commands:

```
pip3 install yt-dlp
pip3 install streamlink
```

4. Download some models and compile whisper-cpp following the instructions provided in the documentation at https://github.com/ggerganov/whisper.cpp
. If you encounter an "Illegal instruction: 4" error during compilation, you can resolve it by deleting line 67 "CFLAGS += -mf16c" in the Makefile.

5. playlist4whisper.py, livestream_video.sh, and the default playlist_xxx.m3u files must be located in the same directory as whisper-cpp.

6. Finally, you can launch the GUI by entering the following command in the terminal. Make sure that you are in the same directory as whisper-cpp, playlist4whisper.py, and livestream_video.sh:
```
python3 playlist4whisper.py
```

Please note that on macOS, only the xterm terminal and the mpv video player are supported. Additionally, the xterm terminal automatically closes its window when Control+C is used.

**Q: How can I permanently change the size and colors of the transcription text on macOS?**

To achieve this, you can create a file named ".Xresources" in your user's home directory (/Users/[user]). Inside the file, you can define specific settings to customize the appearance of the transcription text. For example:

```
.xterm*background: black
.xterm*foreground: yellow
.xterm*font: 10x20
.xterm*vt100*geometry: 80x10
.xterm*saveLines: 10000
```
In this example, the settings modify the background color to black, the foreground color to yellow, the font size to 10x20, the terminal's geometry to 80x10, and the number of lines to save to 10,000. After saving these changes in the ".Xresources" file, you need to relaunch XQuartz for the new settings to take effect. Once you launch an xterm terminal, you will see the desired customization of the transcription text.

**Q: How can I synchronize the video and the transcription?**

A: You can use the pause and forward/backward buttons of the video player to manually synchronize the video and transcription to your desired timing.

**Q: Why does the video and transcription get desynchronized?**

A: The video and transcription applications work independently, each with its own stream of video or audio. Over time, the desynchronization can also vary, choosing a model that is too large for the processor's capabilities can also affect the synchronization.

The timeshift feature alongside with an automatic video/transcription synchronization option may help address the issue, albeit potentially resulting in the omission of some phrases.

**Q: Why does the beginning and end of the transcription often get lost?**

A: The current script versions segment sound files into chunks based on user-selected durations. However, this approach may lead to the truncation or deletion of words at the beginning and end of each chunk because it lacks a voice activity detection (VAD) system for splitting the audio. A VAD system is planned to be incorporated in the near future.

**Q: Sometimes the transcriptions are wrong or not appears, what could be the issue?**

A: The AI model is designed to transcribe audio from various situations, but certain factors can affect its accuracy. For instance, challenging accents or voice tones, or changes in voices during conversations can pose difficulties. In the future, the addition of sound filters options aims to minimize these issues. Additionally, the model may occasionally produce incorrect transcriptions due to gaps in its neural network connections. This can happen more frequently with smaller or quantized models, as well as with languages that have not been extensively trained.

**Q: The transcriptions I get are not accurate?**

A: The quality of the transcriptions depends on several factors, especially the size of the model chosen. Larger models generally yield better results, but they also require more processing power. The English models tend to perform better than models for other languages. For languages other than English, you may need to use a larger model. If you choose the option auto for language autodetection or translate for simultaneous translation to English, it may also significantly increase processor consumption.

**Q: In a low-power processor, is it possible to improve transcription in languages other than English?**

A:  Yes, if you have knowledge of AI programming, you will need to fine-tune a default model by retraining it with a dataset of voices along with their transcriptions in a specific language, or to improve an accent, slang or dialect. Some datasets can be found online, as well as sample codes for fine-tuning a Whisper model. Whisper models must be converted to ggml format, to convert Whisper models to ggml format yourself, instructions are at: https://github.com/ggerganov/whisper.cpp/blob/master/models/README.md

You can also try using the quantized models option, which can improve execution speed on certain processors.
 
Alternatively, instead of running the AI engine on the CPU, you can try compiling whisper.cpp with partial GPU support using the cuBLAS library for Nvidia graphics cards or GPUs, or compile it with partial OpenCL GPU support using the CLBlast library for all graphics cards or GPUs, including Nvidia, AMD, and Intel, or compile using OpenVINO for Intel GPUs. By doing so, you can significantly increase the execution speed by at least x2 or even more, depending on the GPU model you have, and this will allow you to run larger whisper models:

https://github.com/ggerganov/whisper.cpp#nvidia-gpu-support-via-cublas

There should be no issues running the program on Apple computers with ARM processors, whisper.cpp can be compiled to be executed on the Apple Neural Engine (ANE) via Core ML. This can result in a significant speed-up, more than x3 faster compared to CPU-only execution:

https://github.com/ggerganov/whisper.cpp#core-ml-support

**Q: smplayer does not work with online TV?**

A: First, check if you have passed a player option that is not compatible with smplayer. smplayer depens of mpv or mplayer, the installed version of mplayer may not support online video streams, depending on how it was compiled or its configurations, or there may be conflicts with video encoding libraries used by mplayer. In general, mpv is a better option than mplayer, or if you prefer smplayer, make sure it is configured to use mpv.


**Q: Is this program legal to watch TV channels?**

A: Yes, of course, many of the URLs of channels that you find published on the internet are proactively accessible for free use thanks to companies, governments or public institutions, as long as it is for personal use only. Channels that may be restricted to a country or region for copyright reasons cannot be viewed, and the broadcasting company blocks viewers with IPs from other countries. However, the playlists that are found on the internet may contain some channels with legality that is not entirely clear, even if their URLs are publicly known, it is likely that direct distribution of the signal or commercialization of the television channel is not allowed.
 
In the case of YouTube and Twitch, watching channels through standalone applications such as yt-dlp or streamlink poses a conflict with the companies as they cannot control the advertisements you see. In other words, they are not interested in this approach and may make it difficult or prevent you from accessing their video streams.


