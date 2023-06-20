#!/bin/bash
#
# livestream_video.sh v. 1.70 - plays a video stream and transcribes the audio using AI technology.
#
# Copyright (c) 2023 Antonio R.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#   https://github.com/antor44/livestream_video
#
#--------------------------------------------------------------------------------------------------------
#
#
#livestream_video.sh transcribes a video livestream by regularly feeding the output of ffmpeg to whisper.cpp,
# based on the implementation in livestream.sh from whisper.cpp
#
#This Linux script adds some new features:
#
#-Support for multi-instance and multi-user execution
#-Support for IPTV, YouTube, Twitch, and many others
#-Language command-line option "auto" (for autodetection), "en", "es", "fr", "de", "he", "ar", etc., and "translate" for translation to English.
#-Quantized models support
#-VAD (voice activity detection)
#
# Usage: ./livestream_video.sh stream_url [step_s] [model] [language] [translate] [quality] [ [player executable + player options] ]
#
# [streamlink] option forces the url to be processed by streamlink
# [yt-dlp] option forces the url to be processed by yt-dlp
#
#   Example (defaults if no options are specified):
#
#    ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 4 base auto raw [smplayer]
#
# Quality: The valid options are "raw," "upper," and "lower". "Raw" is used to download another video stream without any modifications for the player.
# "Upper" and "lower" download only one stream, which might correspond to the best or worst stream quality, re-encoded for the player.
#
#"[player executable + player options]", valid players: smplayer, mpv, mplayer, vlc, etc... "[none]" or "[true]" for no player.
#
#Step: Size of the parts into which videos are divided for inference, size in seconds.
#
#Whisper models: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large
#
#    ... with suffixes each too: -q4_0, -q4_1, -q4_2, -q5_0, -q5_1, -q8_0
#
#translate: The "translate" option provides automatic English translation (only English is available).
#
#
# Script and Whisper executable (main), and models directory with at least one archive model, must reside in the same directory.
#


if [[ "$(uname)" == "Darwin" ]]; then
    # macOS
    true
else
    # Linux
    set -eo pipefail
fi

url_default="https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8"
fmt=mp3 # the audio format
step_s=4
model="base"
language="auto"
translate=""
mpv_options="mpv"
quality="raw"
streamlink_force=""
ytdlp_force=""


# Whisper languages:
# auto (Autodetect), af (Afrikaans), am (Amharic), ar (Arabic), as (Assamese), az (Azerbaijani), be (Belarusian), bg (Bulgarian), bn (Bengali), br (Breton), bs (Bosnian), ca (Catalan), cs (Czech), cy (Welsh), da (Danish), de (German), el (Greek), en (English), eo (Esperanto), et (Estonian), eu (Basque), fa (Persian), fi (Finnish), fo (Faroese), fr (French), ga (Irish), gl (Galician), gu (Gujarati), haw (Hawaiian), he (<Hebrew>), hi (Hindi), hr (Croatian), ht (Haitian Creole), hu (Hungarian), hy (Armenian), id (Indonesian), is (Icelandic), it (Italian), iw (<Hebrew>), ja (Japanese), jw (Javanese), ka (Georgian), kk (Kazakh), km (Khmer), kn (Kannada), ko (Korean), ku (Kurdish), ky (Kyrgyz), la (Latin), lb (Luxembourgish), lo (Lao), lt (Lithuanian), lv (Latvian), mg (Malagasy), mi (Maori), mk (Macedonian), ml (Malayalam), mn (Mongolian), mr (Marathi), ms (Malay), mt (Maltese), my (Myanmar), ne (Nepali), nl (Dutch), nn (Nynorsk), no (Norwegian), oc (Occitan), or (Oriya), pa (Punjabi), pl (Polish), ps (Pashto), pt (Portuguese), ro (Romanian), ru (Russian), sd (Sindhi), sh (Serbo-Croatian), si (Sinhala), sk (Slovak), sl (Slovenian), sn (Shona), so (Somali), sq (Albanian), sr (Serbian), su (Sundanese), sv (Swedish), sw (Swahili), ta (Tamil), te (Telugu), tg (Tajik), th (Thai), tl (Tagalog), tr (Turkish), tt (Tatar), ug (Uighur), uk (Ukrainian), ur (Urdu), uz (Uzbek), vi (Vietnamese), vo (Volapuk), wa (Walloon), xh (Xhosa), yi (Yiddish), yo (Yoruba), zh (Chinese), zu (Zulu)
languages=( "auto" "af" "am" "ar" "as" "az" "ba" "be" "bg" "bn" "bo" "br" "bs" "ca" "cs" "cy" "da" "de" "el" "en" "es" "et" "eo" "eu" "fa" "fi" "fo" "fr" "ga" "gl" "gu" "ha" "haw" "he" "hi" "hr" "ht" "hu" "hy" "id" "is" "it" "iw" "ja" "jw" "ka" "kk" "km" "kn" "ko" "ku" "ky" "la" "lb" "ln" "lo" "lt" "lv" "mg" "mi" "mk" "ml" "mn" "mr" "ms" "mt" "my" "ne" "nl" "nn" "no" "oc" "pa" "pl" "ps" "pt" "ro" "ru" "sa" "sd" "sh" "si" "sk" "sl" "sn" "so" "sq" "sr" "su" "sv" "sw" "ta" "te" "tg" "th" "tl" "tk" "tr" "tt" "ug" "uk" "ur" "uz" "vi" "vo" "wa" "xh" "yi" "yo" "zh" "zu")

# Whisper models
models=( "tiny.en" "tiny" "base.en" "base" "small.en" "small" "medium.en" "medium" "large-v1" "large" )
suffixes=( "-q4_0" "-q4_1" "-q4_2" "-q5_0" "-q5_1" "-q8_0" )

model_list=()

for modele in "${models[@]}"; do
 model_list+=("$modele")
 for suffix in "${suffixes[@]}"; do
   model_list+=("${modele}${suffix}")
 done
done

# functions

check_requirements()
{
    if ! command -v ./main &>/dev/null; then
        echo "whisper.cpp main executable is required (make)"
        exit 1
    fi

    if ! command -v ffmpeg &>/dev/null; then
        echo "ffmpeg is required (https://ffmpeg.org)"
        exit 1
    fi
}


# list available languages
function list_languages {
    printf "\n"
    printf "  Available languages:"
    for language in "${languages[@]}"; do
        printf " $language"
    done
    printf "\n\n"
}

usage()
{
    echo "Usage: $0 stream_url [step_s] [model] [language] [translate]"
    echo ""
    echo "  Example:"
    echo "    $0 $url $step_s $model $language $translate"
    echo ""

    # list available models

    printf "\n"
    printf "  Available models:"
    for modele in "${model_list[@]}"; do
        printf " $modele"
    done
    printf "\n\n"

    list_languages

}

# main
check_requirements

while [[ $# -gt 0 ]]; do
    case $1 in
        *://* ) url=$1;;
        [2-9]|[1-5][0-9]|60 ) step_s=$1;;
        translate ) translate=$1;;
        raw | upper | lower ) quality=$1;;
        streamlink ) streamlink_force=$1;;
        yt-dlp ) ytdlp_force=$1;;
        \[* )
            mpv_options=${1#\[}
            if [[ $mpv_options == none*\]* ]]; then
                mpv_options="true"
            fi
            if [[ $mpv_options == *\]* ]]; then
                mpv_options=${mpv_options%\]}
            else
                while [[ $1 != *\]* ]]; do
                    shift
                    if [[ $1 == "" ]]; then
                        echo "Error: Missing closing bracket ']' in the player parameter."
                        exit 1
                    fi
                    mpv_options+=" $1"
                done
                mpv_options=${mpv_options%\]}
            fi
            ;;
        * )
            if [[ " ${model_list[@]} " =~ " $1 " ]]; then
                model=$1
            elif [[ " ${languages[@]} " =~ " $1 " ]]; then
                language=$1
            else
                echo ""; echo "*** Wrong option $1"; echo ""; usage; exit 1
            fi
            ;;
    esac
    shift
done

if [ ! -f ./models/ggml-${model}.bin ]; then
    echo ""
    echo "*** No file /models/ggml-${model}.bin for model ${model}"
    echo ""
    usage

    exit 1
fi

mypid=$(ps aux | awk '/[l]ivestream_video\.sh/ {pid=$2} END {print pid}')

if [ -n "$mypid" ]; then
    if [ -e "/tmp/whisper-live_${mypid}.wav" ] && ! [ -w "/tmp/whisper-live_${mypid}.wav" ]; then
      echo ""
      echo "Error: Permission denied to access files /tmp/whisper-live_${mypid}.*"
      echo ""
      exit 1
    else
      echo ""
      echo "New script PID: $mypid"
    fi
else
  echo ""
  echo "An unknown error has occurred."
  echo ""
  exit 1
fi

if [ -z "$url" ]; then
    url="$url_default"
    echo " *** No url specified, using default: $url"
    echo ""
else
    echo " *** url specified by user: $url"
    echo ""
fi

running=1

trap "running=0" SIGINT SIGTERM

# if "translate" then translate to english
if [[ $translate == "translate" ]]; then
    translate="-tr"
    printf "[+] Transcribing stream with model '$model', step_s $step_s, language '$language', translate to english (press Ctrl+C to stop):\n\n"
else
    translate=""
    printf "[+] Transcribing stream with model '$model', step_s $step_s, language '$language', NO translate to english (press Ctrl+C to stop):\n\n"
fi

# continuous stream in native fmt (this file will grow forever!)
if [[ $quality == "upper" ]]; then
    case $url in
        *youtube* | *youtu.be* )
            if ! command -v yt-dlp &>/dev/null; then
                echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                exit 1
            fi
            ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'bestaudio/best[height<=1080]' -g "$url")" \
                -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                -bufsize 44M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:56789 &
            ffmpeg_pid=$!

            nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            ;;
        * )
            if [[ "$streamlink_force" = "streamlink" || "$url" = *twitch* ]]; then
                if ! command -v streamlink >/dev/null 2>&1; then
                    echo "streamlink is required (https://streamlink.github.io)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -re -i "$(streamlink $url best --stream-url)" -bufsize 440M \
                    -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                    -map 0:v:0 -map 0:a:0 -acodec ${fmt}  -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -f mpegts udp://127.0.0.1:56789 &
                ffmpeg_pid=$!

                nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            elif [[ "$ytdlp_force" = "yt-dlp" ]]; then
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'bestaudio/best[height<=1080]' -g "$url")" \
                    -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                    -bufsize 44M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:56789 &
                ffmpeg_pid=$!

                nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            else
                ffmpeg -loglevel quiet -y -probesize 32 -i $url \
                    -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                    -bufsize 44M -map_metadata 0 -map 0:v:9? -map 0:v:8? -map 0:v:7? -map 0:v:6? -map 0:v:5? -map 0:v:4? -map 0:v:3? -map 0:v:2? -map 0:v:1? -map 0:v:0? -map 0:a:0 -acodec ${fmt} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -f mpegts udp://127.0.0.1:56789 &
                ffmpeg_pid=$!

                nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            fi
            ;;
    esac
fi

if [[ $quality == "lower" ]]; then
    case $url in
        *youtube* | *youtu.be* )
            if ! command -v yt-dlp &>/dev/null; then
                echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                exit 1
            fi
            ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'bestaudio/worst' -g "$url")" \
                -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                -bufsize 44M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:56789 &
            ffmpeg_pid=$!

            nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            ;;
        * )
            if [[ "$streamlink_force" = "streamlink" || "$url" = *twitch* ]]; then
                if ! command -v streamlink >/dev/null 2>&1; then
                    echo "streamlink is required (https://streamlink.github.io)"
                    exit 1
                fi
                    ffmpeg -loglevel quiet -y -probesize 32 -re -i "$(streamlink $url worst --stream-url)" -bufsize 440M \
                    -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                    -map 0:v:0 -map 0:a:0 -acodec ${fmt} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -f mpegts udp://127.0.0.1:56789 &
                ffmpeg_pid=$!

                nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            elif [[ "$ytdlp_force" = "yt-dlp" ]]; then
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'bestaudio/worst' -g "$url")" \
                    -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                    -bufsize 44M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:56789 &
                ffmpeg_pid=$!

                nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            else
                ffmpeg -loglevel quiet -y -probesize 32 -i $url \
                    -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} \
                    -bufsize 44M -map_metadata 0 -map 0:v:0? -map 0:v:1? -map 0:v:2? -map 0:v:3? -map 0:v:4? -map 0:v:5? -map 0:v:6? -map 0:v:7? -map 0:v:8? -map 0:v:9? -map 0:a:0 -acodec ${fmt} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -f mpegts udp://127.0.0.1:56789 &
                ffmpeg_pid=$!

                nohup $mpv_options udp://127.0.0.1:56789 >/dev/null 2>&1 &
            fi
            ;;
    esac
fi

if [[ $quality == "raw" ]]; then
    case $url in
        *youtube* | *youtu.be* )
            if ! command -v yt-dlp &>/dev/null; then
                echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                exit 1
            fi
            ffmpeg -loglevel quiet -y -probesize 32 -i $(yt-dlp -i -f 'bestaudio/worst' -g $url) -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} &
            ffmpeg_pid=$!
            ;;
        * )
            if [[ "$streamlink_force" = "streamlink" || "$url" = *twitch* ]]; then
                if ! command -v streamlink >/dev/null 2>&1; then
                    echo "streamlink is required (https://streamlink.github.io)"
                    exit 1
                fi
                streamlink $url worst -O 2>/dev/null | ffmpeg -loglevel quiet -i - -y -probesize 32 -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} &
                ffmpeg_pid=$!
            elif [[ "$ytdlp_force" = "yt-dlp" ]]; then
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -i $(yt-dlp -i -f 'bestaudio/worst' -g $url) -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} &
                ffmpeg_pid=$!
            else
                ffmpeg -loglevel quiet -y -probesize 32 -i $url -bufsize 44M -map 0:a:0 /tmp/whisper-live0_${mypid}.${fmt} &
                ffmpeg_pid=$!
            fi
            ;;
    esac

    $mpv_options $url &>/dev/null &

    if [ $? -ne 0 ]; then
        printf "Error: The player could not play the stream. Please check your input or try again later\n"
        exit 1
    fi
fi

printf "Buffering audio. Please wait...\n\n"
sleep $(($step_s+1))

if ! ps -p $ffmpeg_pid > /dev/null; then
    printf "Error: ffmpeg failed to capture the stream\n"
    exit 1
fi

# do not stop script on error
set +e

i=0
SECONDS=0
while [ $running -eq 1 ]; do
    # extract the next piece from the main file above and transcode to wav. -ss sets start time, -0.x seconds adjust
    err=1
    while [ $err -ne 0 ]; do
        if [ $i -gt 0 ]; then
            ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live0_${mypid}.${fmt} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$i * $step_s - 0.8" | bc) -t $(echo "$step_s + 0.0" | bc) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
        else
            ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live0_${mypid}.${fmt} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -t $(echo "$step_s - 0.8" | bc) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
        fi
        err=$(cat /tmp/whisper-live_${mypid}.err | wc -l)
    done

    ./main -l ${language} ${translate} -t 4 -m ./models/ggml-${model}.bin -f /tmp/whisper-live_${mypid}.wav --no-timestamps -otxt 2> /tmp/whispererr_${mypid} | tail -n 1

    while [ $SECONDS -lt $((($i+1)*$step_s)) ]; do
        sleep 0.5
    done
    ((i=i+1))
done

killall -v ffmpeg
killall -v main
