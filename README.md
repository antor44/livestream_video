# livestream_video.sh

Transcribe video livestream by feeding ffmpeg output to whisper.cpp at regular intervals, based on livestream.sh from whisper.cpp

This Linux script adds some new features:

-Language command-line option: auto (for autodetection), en, es, fr, de, iw, ar, etc.
-Translate to English when auto is selected

Most video streams should work.

Recommended Linux video player: SMPlayer based on mvp, or any other video player based on mplayer, due to its capabilities to timeshift online streams for synchronized live video with the transcription.

## Screenshot:

![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV.jpg)
