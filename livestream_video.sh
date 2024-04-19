#!/bin/bash
#
# livestream_video.sh v. 2.40 - plays audio/video files or video streams, transcribing the audio using AI technology.
# The application supports a fully configurable timeshift feature, multi-instance and multi-user execution, allows
# for changing options per channel and global options, online translation, and Text-to-Speech with translate-shell.
# All of these tasks can be performed efficiently even with low-level processors. Additionally,
# it generates subtitles from audio/video files.
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
# livestream_video.sh is based on whisper.cpp
#
# For installing whisper-cpp, follow the instructions provided at https://github.com/ggerganov/whisper.cpp"
#
# This Linux script adds some new features:
#
# -Support for multi-instance and multi-user execution
# -Support for IPTV, YouTube, Twitch, and many others
# -Language command-line option "auto" (for autodetection), "en", "es", "fr", "de", "he", "ar", etc., and "translate" for translation to English.
# -Quantized models support
# -Online translation and Text-to-Speech with translate-shell (https://github.com/soimort/translate-shell)
# -Generates subtitles from audio/video files.
#
#  Usage: ./livestream_video.sh stream_url [step_s] [model] [language] [translate] [subtitles] [timeshift] [segments #n (2<n<99)] [segment_time m (1<minutes<99)] [[trans trans_language] [output_text] [speak]]"
#
# Example:"
# ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 8 base auto raw [smplayer] timeshift segments 4 segment_time 10 [trans es both speak]"
#
# Local audio/video file must be enclosed in double quotation marks, with full path or if the file is in the same directory preceded with './'
#
# [streamlink] option forces the url to be processed by streamlink
# [yt-dlp] option forces the url to be processed by yt-dlp
#
# Quality: The valid options are "raw," "upper," and "lower". "Raw" is used to download another video stream without any modifications for the player.
# "Upper" and "lower" download only one stream, which might correspond to the best or worst stream quality, re-encoded for the player.
#
# "[player executable + player options]", valid players: smplayer, mpv, mplayer, vlc, etc... "[none]" or "[true]" for no player.
#
# Step: Size of the parts into which videos are divided for inference, size in seconds.
#
# Whisper models: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2", large-v3
#
# ... with suffixes each too: -q2_k, -q3_k, -q4_0, -q4_1, -q4_k, -q5_0, -q5_1, -q5_k, -q6_k, -q8_0
#
# translate: The "translate" feature offers automatic English translation using Whisper AI (English only).
#
# subtitles: Generate Subtitles from an Audio/Video File, with support for language selection, translation feature of Whisper IA, and online translation to any language.
#            A .srt file will be saved with the same filename and in the same directory as the source audio/video file.
#
# [trans + options]: Online translation and Text-to-Speech with translate-shell (https://github.com/soimort/translate-shell)
#
# trans_language: Translation language for translate-shell.
#
# output_text: Choose the output text during translation with translate-shell: original, translation, both, none.
#
# speak: Online Text-to-Speech using translate-shell.
#
# playeronly: Play the video stream without transcriptions.
#
# timeshift: Timeshift feature, only VLC player is supported.
#
# sync: Transcription/video synchronization time in seconds (0 <= seconds <= (Step - 3)).
#
# segments: Number of segment files for timeshift (2 =< n <= 99).
#
# segment_time: Time for each segment file(1 <= minutes <= 99).
#
# This script and whisper-cpp's executable 'main', and models directory with at least one archive model, must reside in the same directory.
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
local=0
step_s=8
model="base"
language="auto"
translate=""
playeronly=""
mpv_options="mpv"
quality="raw"
streamlink_force=""
ytdlp_force=""
segment_time=10
segments=4
sync=4
speak=""
trans=""
output_text="both"
trans_language="en"
subtitles=""

# Temporary file to store used port numbers
temp_file="/tmp/used_ports.txt"

# Whisper languages:
# auto (Autodetect), af (Afrikaans), am (Amharic), ar (Arabic), as (Assamese), az (Azerbaijani), be (Belarusian), bg (Bulgarian), bn (Bengali), br (Breton), bs (Bosnian), ca (Catalan), cs (Czech), cy (Welsh), da (Danish), de (German), el (Greek), en (English), eo (Esperanto), et (Estonian), eu (Basque), fa (Persian), fi (Finnish), fo (Faroese), fr (French), ga (Irish), gl (Galician), gu (Gujarati), haw (Hawaiian), he (Hebrew), hi (Hindi), hr (Croatian), ht (Haitian Creole), hu (Hungarian), hy (Armenian), id (Indonesian), is (Icelandic), it (Italian), ja (Japanese), jw (Javanese), ka (Georgian), kk (Kazakh), km (Khmer), kn (Kannada), ko (Korean), ku (Kurdish), ky (Kyrgyz), la (Latin), lb (Luxembourgish), lo (Lao), lt (Lithuanian), lv (Latvian), mg (Malagasy), mi (Maori), mk (Macedonian), ml (Malayalam), mn (Mongolian), mr (Marathi), ms (Malay), mt (Maltese), my (Myanmar), ne (Nepali), nl (Dutch), nn (Nynorsk), no (Norwegian), oc (Occitan), or (Oriya), pa (Punjabi), pl (Polish), ps (Pashto), pt (Portuguese), ro (Romanian), ru (Russian), sd (Sindhi), sh (Serbo-Croatian), si (Sinhala), sk (Slovak), sl (Slovenian), sn (Shona), so (Somali), sq (Albanian), sr (Serbian), su (Sundanese), sv (Swedish), sw (Swahili), ta (Tamil), te (Telugu), tg (Tajik), th (Thai), tl (Tagalog), tr (Turkish), tt (Tatar), ug (Uighur), uk (Ukrainian), ur (Urdu), uz (Uzbek), vi (Vietnamese), vo (Volapuk), wa (Walloon), xh (Xhosa), yi (Yiddish), yo (Yoruba), zh (Chinese), zu (Zulu)
languages=( "auto" "af" "am" "ar" "as" "az" "ba" "be" "bg" "bn" "bo" "br" "bs" "ca" "cs" "cy" "da" "de" "el" "en" "es" "et" "eo" "eu" "fa" "fi" "fo" "fr" "ga" "gl" "gu" "ha" "haw" "he" "hi" "hr" "ht" "hu" "hy" "id" "is" "it" "ja" "jw" "ka" "kk" "km" "kn" "ko" "ku" "ky" "la" "lb" "ln" "lo" "lt" "lv" "mg" "mi" "mk" "ml" "mn" "mr" "ms" "mt" "my" "ne" "nl" "nn" "no" "oc" "or" "pa" "pl" "ps" "pt" "ro" "ru" "sa" "sd" "sh" "si" "sk" "sl" "sn" "so" "sq" "sr" "su" "sv" "sw" "ta" "te" "tg" "th" "tl" "tk" "tr" "tt" "ug" "uk" "ur" "uz" "vi" "vo" "wa" "xh" "yi" "yo" "zh" "zu")

# Whisper models
models=( "tiny.en" "tiny" "base.en" "base" "small.en" "small" "medium.en" "medium" "large-v1" "large-v2" "large-v3" )
suffixes=( "-q2_k" "-q3_k" "-q4_0" "-q4_1" "-q4_k" "-q5_0" "-q5_1" "-q5_k" "-q6_k" "-q8_0" )

model_list=()

for modele in "${models[@]}"; do
 model_list+=("$modele")
 for suffix in "${suffixes[@]}"; do
   model_list+=("${modele}${suffix}")
 done
done

output_text_list=( "original" "translation" "both" "none" )

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
    echo "Usage: $0 stream_url [step_s] [model] [language] [translate] [subtitles] [timeshift] [segments #n (2<n<99)] [segment_time m (1<minutes<99)] [[trans trans_language] [output_text] [speak]]"
    echo ""
    echo "  Example:"
    echo "    ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 8 base auto raw [smplayer] timeshift segments 4 segment_time 10 [trans es both speak]"
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

# check VLC when Timeshift
function vlc_check()
{
  check_pid=$(ps -p $vlc_pid) # check pidof player

  if [[ $check_pid != *vlc* ]] && [[ $check_pid != *VLC* ]]; then # timeshift exit
    echo
    pkill -e -f "^ffmpeg.*${mypid}.*$"
    pkill -e -f "^./main.*${mypid}.*$"
    # Remove the used port from the temporary file
    awk -v myport="$myport" '$0 !~ myport' "$temp_file" > temp_file.tmp && mv temp_file.tmp "$temp_file"
    echo
    echo "*** VLC closed. Timeshift finished."
    echo
    exit 0
  fi
}

# Function to get a unique random port number
get_unique_port() {
    local min=1024
    local max=65535
    local random_port

    # Create the temporary file if it doesn't exist
    if ! [ -f "$temp_file" ]; then
        touch "$temp_file"
    fi

    while true; do
        # Generate a random port number between 1024 and 65535
        random_port=$((RANDOM % (max - min + 1) + min))

        # Check if the random port is already in use
        if ! grep -q "$random_port" "$temp_file"; then
            echo "$random_port" >> "$temp_file"
            break
        fi
    done

    # Return the generated unique port
    echo "$random_port"
}


# main
check_requirements

while [[ $# -gt 0 ]]; do
    case $1 in
        *://* | /* | ./* )
            url=$1
            if [[ $url == /* ]] || [[ $url == ./* ]]; then
                local=1
            fi
            if [[ $url == ./* ]]; then
                url=${1#./}
                url="$(pwd)/$url"
            fi
            ;;
        [3-9]|[1-5][0-9]|60 ) step_s=$1;;
        translate ) translate=$1;;
        subtitles ) subtitles=$1;;
        playeronly ) playeronly=$1;;
        timeshift ) timeshift=$1;;
        segment_time ) segment_time=$2
            if ! [[ "$segment_time" =~ ^[0-9]+$ ]]; then
                echo "Error: Segment Time must be a numeric value."
                usage
                exit 1
            fi
            shift;;
        segments ) segments=$2
            if ! [[ "$segments" =~ ^[0-9]+$ ]]; then
                echo "Error: Segments must be a numeric value."
                usage
                exit 1
            fi
            shift;;
        sync ) sync=$2
            if ! [[ "$sync" =~ ^[0-9]+$ ]]; then
                echo "Error: Sync must be a numeric value."
                usage
                exit 1
            fi
            shift;;
        raw | upper | lower ) quality=$1;;
        streamlink ) streamlink_force=$1;;
        yt-dlp ) ytdlp_force=$1;;
        \[trans* )
            trans="trans"
            if ! command -v trans &>/dev/null; then
                echo "translate-shell is required (https://github.com/soimort/translate-shell)"
                exit 1
            fi
            if [[ $1 == *\]* ]]; then
                echo "Warning: Missing language option in the trans options. Default is ${trans_language}."
                trans_option="${trans_language}]"
            else
                shift
                while [[ $1 != *\]* ]]; do
                    if [[ $1 == "" ]]; then
                        echo "Error: Missing closing bracket ']' in the trans options."
                        exit 1
                    elif [[ " ${output_text_list[@]} " =~ " $1 " ]]; then
                        output_text=$1
                    elif [[ " ${languages[@]} " =~ " $1 " ]]; then
                        trans_language=$1
                    elif [[ " speak " == " $1 " ]]; then
                        speak="speak"
                    else
                        echo ""; echo "*** Wrong option $1"; echo ""; usage; exit 1
                    fi
                    shift
                done
                trans_option=$1
                trans_option=${trans_option%\]}
                if [[ $trans_option == "speak" ]]; then
                    speak="speak"
                elif [[ " ${output_text_list[@]} " =~ " $trans_option " ]]; then
                    output_text=$trans_option
                elif [[ " ${languages[@]} " =~ " $trans_option " ]]; then
                    trans_language=$trans_option
                else
                    echo ""; echo "*** Wrong option $trans_option"; echo ""; usage; exit 1
                fi
            fi
            ;;
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


if [ "$timeshift" = "timeshift" ]; then
    if [ "$segments" -lt 2 ] || [ "$segments" -gt 99 ]; then
        echo "Error: Segments should be between 2 and 99."
        usage
        exit 1
    fi

    if [ "$segment_time" -lt 1 ] || [ "$segment_time" -gt 99 ]; then
        echo "Error: Segment Time should be between 2 and 99."
        usage
        exit 1
    fi

    if [ $sync -lt 0 ] || [ $sync -gt $((step_s - 3)) ]; then
        echo "Error: Sync should be between 0 and $((step_s - 3))."
        usage
        exit 1
    fi
fi

mypid=$(ps aux | awk '/livestream_video\.sh/ {pid=$2} END {print pid}')

if [ -n "$mypid" ]; then
    if [ -e "/tmp/whisper-live_${mypid}.wav" ] && ! [ -w "/tmp/whisper-live_${mypid}.wav" ]; then
      echo ""
      echo "Error: Permission denied to access files /tmp/whisper-live_${mypid}.*"
      echo ""
      exit 1
    else
      echo ""
      if [[ "$timeshift" = "timeshift" ]] || ( [ $local -eq 0 ] && [[ "$playeronly" == "" ]] && ([[ $quality == "upper" ]] || [[ $quality == "lower" ]])); then
          myport=$(get_unique_port "$mypid")
          echo "New script PID: $mypid - Loopback port: $myport"
      else
          echo "New script PID: $mypid"
      fi
    fi
else
  echo ""
  echo "An unknown error has occurred."
  echo ""
fi

echo ""
if [ -z "$url" ]; then
    url="$url_default"
    echo " * No url specified, using default: $url"
else
    echo " * url specified by user: $url"
fi
echo ""

if [ "$playeronly" == "" ] || [[ $subtitles == "subtitles" ]] ; then
    # if "translate" then translate to english
    if [[ $translate == "translate" ]]; then
        translate="-tr"
        printf "[+] Transcribing stream with model '$model', '$step_s' seconds steps, language '$language', translate to English (press Ctrl+C to stop).\n\n"
    else
        translate=""
        printf "[+] Transcribing stream with model '$model', '$step_s' seconds steps, language '$language', NO translate to English (press Ctrl+C to stop).\n\n"
    fi
fi

# if online translate"
if [ "$trans" == "trans" ]; then
    if [ "$speak" == "speak" ]; then
        printf "[+] Online translation into language '$trans_language', output text: '$output_text', Text-to-speech.\n\n"
    else
        printf "[+] Online translation into language '$trans_language', output text: '$output_text'.\n\n"
    fi
fi


if [[ $subtitles == "subtitles" ]] && [[ $local -eq 0 ]]; then
    echo ""
    echo "Error: Generate Subtitles only available for local Audio/Video Files."
    echo ""
    # Remove the used port from the temporary file
    awk -v myport="$myport" '$0 !~ myport' "$temp_file" > temp_file.tmp && mv temp_file.tmp "$temp_file"
    exit 1
fi


# Generate Subtitles from Audio/Video File.
if [[ $subtitles == "subtitles" ]] && [[ $local -eq 1 ]]; then

    echo ""
    echo "Generating Subtitles..."
    echo ""
    # do not stop script on error
    set +e

    ffmpeg -i "${url}" -y -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper-live_${mypid}.wav
    err=$?

    if [ $err -eq 0 ]; then

        ./main -l ${language} ${translate} -t 4 -m ./models/ggml-${model}.bin -f /tmp/whisper-live_${mypid}.wav -osrt 2> /tmp/whisper-live_${mypid}-err.err
        err=$?

        url_no_ext="${url%.*}"
        if [[ $trans == "trans" ]] && [ $err -eq 0 ]; then
            trans -b :${trans_language} -i /tmp/whisper-live_${mypid}.wav.srt -o /tmp/whisper-live_${mypid}.wav.${trans_language}.srt
            err=$?
            destination="${url_no_ext}.${trans_language}.srt"
            mv /tmp/whisper-live_${mypid}.wav.${trans_language}.srt /tmp/whisper-live_${mypid}.wav.srt
        elif [ $err -eq 0 ]; then
            if [[ $translate == "" ]]; then
                destination="${url_no_ext}.${language}.srt"
            else
                destination="${url_no_ext}.en.srt"
            fi
        fi

        # Check if destination file already exists
        if [ -e "$destination" ] && [ $err -eq 0 ]; then
            echo ""
            read -p "The file '$destination' already exists. Do you want to overwrite it? (y/n): " response
            if [ "$response" = "y" ]; then
                mv /tmp/whisper-live_${mypid}.wav.srt "$destination"
                err=$?
            elif [ "$response" = "n" ]; then
                read -p "Enter a new name with full path for the destination file [${destination}]: " new_destination
                mv -i /tmp/whisper-live_${mypid}.wav.srt "$new_destination"
                err=$?
            else
                echo "Invalid response. Aborting. You can find the temporary Subtitles File in: /tmp/whisper-live_${mypid}.wav.srt"
                err=1
            fi
        else
            mv -i /tmp/whisper-live_${mypid}.wav.srt "$destination"
            err=$?
        fi
    fi

		if [ $err -eq 0 ]; then
        echo ""
        echo "Subtitles generated successfully."
        echo ""
        exit 0
    else
        echo ""
        echo "An error occurred while generating subtitles."
        echo ""
        pkill -e -f "^ffmpeg.*${mypid}.*$"
        pkill -e -f "^./main.*${mypid}.*$"
        pkill -e -f "^trans.*${mypid}.*$"
        # Remove the used port from the temporary file
        awk -v myport="$myport" '$0 !~ myport' "$temp_file" > temp_file.tmp && mv temp_file.tmp "$temp_file"
        exit 1
    fi

fi


running=1
trap "running=0" SIGINT SIGTERM

# if "timeshift" then timeshift
if [[ $timeshift == "timeshift" ]] && [[ $local -eq 0 ]]; then
    printf "[+] Timeshift active: '$segments' segments of '$segment_time' minutes and a synchronization of '$sync' seconds.\n\n"

    segment_time=$((segment_time * 60))

    case $url in
        *youtube* | *youtu.be* )
            if ! command -v yt-dlp &>/dev/null; then
                echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                exit 1
            fi
            ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f b -g $url) -bufsize 44M -acodec ${fmt} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $segment_time -reset_timestamps 1 /tmp/whisper-live_${mypid}_buf%03d.avi &
            ffmpeg_pid=$!
            ;;
        * )
            if [[ "$streamlink_force" = "streamlink" || "$url" = *twitch* ]]; then
                if ! command -v streamlink >/dev/null 2>&1; then
                    echo "streamlink is required (https://streamlink.github.io)"
                    exit 1
                fi
                streamlink $url best -O 2>/dev/null | ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i - -bufsize 44M -acodec ${fmt} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $segment_time -reset_timestamps 1 /tmp/whisper-live_${mypid}_buf%03d.avi &
                ffmpeg_pid=$!
            elif [[ "$ytdlp_force" = "yt-dlp" ]]; then
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f b -g $url) -bufsize 44M -acodec ${fmt} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $segment_time -reset_timestamps 1 /tmp/whisper-live_${mypid}_buf%03d.avi &
                ffmpeg_pid=$!
            else
                ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $url -bufsize 44M -map_metadata 0 -map 0:v:9? -map 0:v:8? -map 0:v:7? -map 0:v:6? -map 0:v:5? -map 0:v:4? -map 0:v:3? -map 0:v:2? -map 0:v:1? -map 0:v:0? -map 0:a:9? -map 0:a:8? -map 0:a:7? -map 0:a:6? -map 0:a:5? -map 0:a:4? -map 0:a:3? -map 0:a:2? -map 0:a:1? -map 0:a:0? -acodec ${fmt} -vcodec libx264 -threads 2 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $segment_time -reset_timestamps 1 /tmp/whisper-live_${mypid}_buf%03d.avi &
                ffmpeg_pid=$!
            fi
            ;;
    esac


    # build m3u playlist
    arg='#EXTM3U'
		x=0
		while [ $x -lt $segments ]; do
			arg="$arg"'\n/tmp/whisper-live_'"${mypid}"'_'"$x"'.avi'
			x=$((x+1))
		done
		echo -e $arg > /tmp/playlist_whisper-live_${mypid}.m3u

    # launch player
    ln -f -s /tmp/whisper-live_${mypid}_buf000.avi /tmp/whisper-live_${mypid}_0.avi # symlink first buffer at start

    if [ "$playeronly" == "" ]; then
        printf "Buffering audio. Please wait...\n\n"
    fi
    sleep 15

    if ! ps -p $ffmpeg_pid > /dev/null; then
        printf "Error: ffmpeg failed to capture the stream\n"
        exit 1
    fi
    sleep $(($step_s+5))
    if [[ $mpv_options == "true" ]]; then
        vlc -I http --http-host 127.0.0.1 --http-port "$myport" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${mypid}.m3u >/dev/null 2>&1 &
    else
        vlc --extraintf=http --http-host 127.0.0.1 --http-port "$myport" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${mypid}.m3u >/dev/null 2>&1 &
    fi

    if [ $? -ne 0 ]; then
        printf "Error: The player could not play the stream. Please check your input or try again later\n"
        exit 1
    fi

    vlc_pid=$(ps -ax -o etime,pid,command -c | grep -i '[Vv][Ll][Cc]' | tail -n 1 | awk '{print $2}') # check pidof vlc
    if [ -z "$vlc_pid" ]; then
        vlc_pid=0
        printf "Error: The player could not be executed.\n"
        exit 1
    fi

    # do not stop script on error
    set +e

    # handle buffers, repeat until player closes

    n=0
    tbuf=0
  	abuf="000"
    xbuf=1
    nbuf="001"

    i=-1
    SECONDS=0
    FILEPLAYED=""
    TIMEPLAYED=0
    acceleration_factor="1.5"

    if [ "$playeronly" != "" ]; then
      echo "Now recording video buffer /tmp/whisper-live_${mypid}_$n.avi"
    fi

    while [ $running -eq 1 ]; do

  		if [ -f /tmp/whisper-live_${mypid}_buf$nbuf.avi ]; then # check split
  			mv -f /tmp/whisper-live_${mypid}_buf$abuf.avi /tmp/whisper-live_${mypid}_$n.avi
  			if [ $n -eq $((segments-1)) ]; then # restart buffer value when last buffer reached
  				n=-1
  			fi
  			tbuf=$((tbuf+1))
  			if [ $tbuf -lt 10 ]; then # split number, character value
  				abuf="00"$tbuf""
  			elif [ $tbuf -lt 100 ]; then
  				abuf="0"$tbuf""
  			else
  				abuf="$tbuf"
  			fi
        xbuf=$((xbuf+1))
        if [ $xbuf -lt 10 ]; then # split number, character value
          nbuf="00"$xbuf""
        elif [ $xbuf -lt 100 ]; then
          nbuf="0"$xbuf""
        else
  				nbuf="$xbuf"
  			fi
        n=$((n+1))
  			ln -f -s /tmp/whisper-live_${mypid}_buf$abuf.avi /tmp/whisper-live_${mypid}_$n.avi
        if [ "$playeronly" != "" ]; then
          echo "Now recording video buffer /tmp/whisper-live_${mypid}_$n.avi"
        fi
  		fi

      while [ $SECONDS -lt $((($i+1)*$step_s)) ]; do
          sleep 0.1
      done

      vlc_check

      curl_output=$(curl -s -N -u :playlist4whisper http://127.0.0.1:${myport}/requests/status.xml)

            FILEPLAY=$(echo "$curl_output" | sed -n 's/.*<info name='"'"'filename'"'"'>\([^<]*\).*$/\1/p')

            POSITION=$(echo "$curl_output" | sed -n 's/.*<time>\([^<]*\).*$/\1/p')


      if [[ "$POSITION" =~ ^[0-9]+$ ]] && [ "$playeronly" == "" ]; then

          if [ $POSITION -ge 2 ]; then

              if [ "$FILEPLAY" != "$FILEPLAYED" ]; then
                  FILEPLAYED="$FILEPLAY"
                  TIMEPLAYED=$(date -r /tmp/"$FILEPLAY" +%s)
                  if [ $(echo "$POSITION < $step_s" | bc -l) -eq 1 ]; then
                      in=0
                  else
                      in=2
                      ((SECONDS=SECONDS+step_s))
                  fi
                  tin=0
              elif [ "$(date -r /tmp/"$FILEPLAY" +%s)" -gt "$((TIMEPLAYED + segment_time))" ] && [ $tin -eq 0 ]; then
                  tin=1
              fi

              if [ $tin -eq 0 ]; then
                  err=1

                  segment_played=$(echo ffprobe -i /tmp/"$FILEPLAY" -show_format -v quiet | sed -n 's/duration=//p')

                  if ! [[ "$segment_played" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                      segment_played="$segment_time"
                  fi

                  rest=$(echo "$segment_played - $POSITION - $sync" | bc -l)
                  tryed=0
                  if [ $(echo "$rest < $step_s" | bc -l) -eq 1 ] && [ $(echo "$rest > 0" | bc -l) -eq 1 ]; then

                      while [ $err -ne 0 ] && [ $tryed -lt 10 ]; do
                          sleep 0.4
                          ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $sync - 0.8" | bc -l) -t $(echo "$rest + 0.8" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
                          ((tryed=tryed+1))
                          err=$(cat /tmp/whisper-live_${mypid}.err | wc -l)
                      done
                      in=3

                  else

                      while [ $err -ne 0 ] && [ $tryed -lt 5 ]; do
                          if [ $in -eq 0 ]; then
                              if [ $(echo "$((POSITION)) < $(((step_s+sync)*2))" | bc -l) -eq 1 ]; then
                                  ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -to $(echo "$POSITION + $sync - 0.8" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
                                  in=1
                              else
                                  in=1
                              fi
                          else
                              ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $sync - 0.8" | bc -l) -t $(echo "$step_s + 0.0" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
                              in=2
                          fi
                          err=$(cat /tmp/whisper-live_${mypid}.err | wc -l)
                          ((tryed=tryed+1))
                      done

                      if [ $in -eq 1 ]; then
                          ((SECONDS=SECONDS+step_s))
                      fi

                  fi


                  ./main -l ${language} ${translate} -t 4 -m ./models/ggml-${model}.bin -f /tmp/whisper-live_${mypid}.wav --no-timestamps -otxt 2> /tmp/whisper-live_${mypid}-err.err | tail -n 1 | tr -d '<>^*_' | tee /tmp/output-whisper-live_${mypid}.txt >/dev/null

                  if [[ $output_text == "original" ]] || [[ $output_text == "both" ]] || [[ $trans == "" ]]; then
                      cat /tmp/output-whisper-live_${mypid}.txt | tee -a /tmp/transcription-whisper-live_${mypid}.txt
                  else
                      cat /tmp/output-whisper-live_${mypid}.txt >> /tmp/transcription-whisper-live_${mypid}.txt
                  fi

                  if [[ $trans == "trans" ]]; then
                      if [[ $speak == "speak" ]]; then

                          if [ $(wc -m < /tmp/output-whisper-live_${mypid}.txt) -ge 3 ] && [[ $speak == "speak" ]]; then
                              if [[ $output_text == "translation" ]]; then
                                  trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt
                              elif [[ $output_text == "both" ]]; then
                                  tput rev
                                  trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt
                                  tput sgr0
                              else
                                  trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt >/dev/null
                              fi
                              if [ -f /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 ]; then

                                  # Get duration of input audio file in seconds
                                  duration=$(ffprobe -i /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 -show_entries format=duration -v quiet -of csv="p=0")

                                  # Check if duration exceeds maximum time
                                  if [ -n "$duration" ]; then

                                      if [[ $(echo "$duration > ($step_s - ( $step_s / 8 ))" | bc -l) == 1 ]]; then
                                          acceleration_factor=$(echo "scale=2; $duration / ($step_s - ( $step_s / 8 ))" | bc -l)
                                      fi
                                      if [[ $(echo "$acceleration_factor < 1.5" | bc -l) == 1 ]]; then
                                          acceleration_factor="1.5"
                                      fi
                                      # Use FFmpeg to speed up the audio file
                                      mv -f "/tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3" "/tmp/whisper-live_${mypid}_$(((i+1)%2)).mp3"
                                      ffmpeg -i /tmp/whisper-live_${mypid}_$(((i+1)%2)).mp3 -filter:a "atempo=$acceleration_factor" /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 >/dev/null 2>&1

                                      # Play the modified audio
                                      mpv /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 &>/dev/null &
                                  fi
                              fi
                          fi

                      elif [[ $output_text == "translation" ]]; then
                          trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} | tee -a /tmp/translation-whisper-live_${mypid}.txt
                      elif [[ $output_text == "both" ]]; then
                          tput rev
                          trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} | tee -a /tmp/translation-whisper-live_${mypid}.txt
                          tput sgr0
                      fi
                  fi




              elif [ $tin -eq 1 ]; then
                  echo
                  echo "*** You have reached the configured timeshift window time. The version of the video file $FILEPLAY you are watching has been overwritten. You can still watch it, but without transcriptions. Please note that subsequent video files may also be overwritten. To avoid this limitation in the future, consider configuring Timeshift with more segments and/or longer segment times."
                  echo
                  tin=2
              fi

          else
            in=0
          fi
      fi
      ((i=i+1))

    done

    pkill -e -f "^ffmpeg.*${mypid}.*$"
    pkill -e -f "^./main.*${mypid}.*$"
    # Remove the used port from the temporary file
    awk -v myport="$myport" '$0 !~ myport' "$temp_file" > temp_file.tmp && mv temp_file.tmp "$temp_file"

elif [[ $timeshift == "timeshift" ]] && [[ $local -eq 1 ]]; then # local video file with vlc

    if [ "$playeronly" == "" ]; then
        arg="#EXTM3U\n${url}"
        echo -e $arg > /tmp/playlist_whisper-live_${mypid}.m3u

        if [[ $mpv_options == "true" ]]; then
            vlc -I http --http-host 127.0.0.1 --http-port "$myport" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${mypid}.m3u >/dev/null 2>&1 &
        else
            vlc --extraintf=http --http-host 127.0.0.1 --http-port "$myport" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${mypid}.m3u >/dev/null 2>&1 &
        fi

        if [ $? -ne 0 ]; then
            printf "Error: The player could not play the file. Please check your input.\n"
            exit 1
        fi

        vlc_pid=$(ps -ax -o etime,pid,command -c | grep -i '[Vv][Ll][Cc]' | tail -n 1 | awk '{print $2}') # check pidof vlc
        if [ -z "$vlc_pid" ]; then
            vlc_pid=0
            printf "Error: The player could not be executed.\n"
            exit 1
        fi

        # do not stop script on error
        set +e

        FILEPLAYED=""
        TIMEPLAYED=0
        SECONDS=0
        i=-1
        acceleration_factor="1.5"

        # repeat until player closes
        while [ $running -eq 1 ]; do


            while [ $SECONDS -lt $((($i+1)*$step_s)) ]; do
                sleep 0.1
            done

            vlc_check

            curl_output=$(curl -s -N -u :playlist4whisper http://127.0.0.1:${myport}/requests/status.xml)

                  FILEPLAY=$(echo "$curl_output" | sed -n 's/.*<info name='"'"'filename'"'"'>\([^<]*\).*$/\1/p')

                  POSITION=$(echo "$curl_output" | sed -n 's/.*<time>\([^<]*\).*$/\1/p')


            if [[ "$POSITION" =~ ^[0-9]+$ ]]; then

                if [ $POSITION -ge 2 ]; then

                    if [ "$FILEPLAY" != "$FILEPLAYED" ]; then
                        FILEPLAYED="$FILEPLAY"
                        if [ $(echo "$POSITION < $step_s" | bc -l) -eq 1 ]; then
                            in=0
                        else
                            in=2
                            ((SECONDS=SECONDS+step_s))
                        fi
                    fi

                    err=1

                    segment_played=$(echo ffprobe -i "${url}" -show_format -v quiet | sed -n 's/duration=//p')

                    if ! [[ "$segment_played" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then

                        rest=$(echo "$segment_played - $POSITION - $sync" | bc -l)
                        tryed=0
                        if [ $(echo "$rest < $step_s" | bc -l) -eq 1 ] && [ $(echo "$rest > 0" | bc -l) -eq 1 ]; then

                            while [ $err -ne 0 ] && [ $tryed -lt 10 ]; do
                                sleep 0.4
                                ffmpeg -loglevel quiet -v error -noaccurate_seek -i "${url}" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $sync - 1" | bc -l) -t $(echo "$rest + 0.5" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
                                ((tryed=tryed+1))
                                err=$(cat /tmp/whisper-live_${mypid}.err | wc -l)
                            done
                            in=3

                        else

                            while [ $err -ne 0 ] && [ $tryed -lt 5 ]; do
                                if [ $in -eq 0 ]; then
                                    if [ $(echo "$((POSITION)) < $(((step_s+sync)*2))" | bc -l) -eq 1 ]; then
                                        ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -to $(echo "$POSITION + $sync - 0.8" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
                                        in=1
                                    else
                                        in=1
                                    fi
                                else
                                    ffmpeg -loglevel quiet -v error -noaccurate_seek -i "${url}" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $sync - 1" | bc -l) -t $(echo "$step_s + 0.0" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
                                    in=2
                                fi
                                err=$(cat /tmp/whisper-live_${mypid}.err | wc -l)
                                ((tryed=tryed+1))
                            done

                            if [ $in -eq 1 ]; then
                                ((SECONDS=SECONDS+step_s))
                            fi

                        fi

                        ./main -l ${language} ${translate} -t 4 -m ./models/ggml-${model}.bin -f /tmp/whisper-live_${mypid}.wav --no-timestamps -otxt 2> /tmp/whisper-live_${mypid}-err.err | tail -n 1 | tr -d '<>^*_' | tee /tmp/output-whisper-live_${mypid}.txt >/dev/null

                        if [[ $output_text == "original" ]] || [[ $output_text == "both" ]] || [[ $trans == "" ]]; then
                            cat /tmp/output-whisper-live_${mypid}.txt | tee -a /tmp/transcription-whisper-live_${mypid}.txt
                        else
                            cat /tmp/output-whisper-live_${mypid}.txt >> /tmp/transcription-whisper-live_${mypid}.txt
                        fi

                        if [[ $trans == "trans" ]]; then
                            if [[ $speak == "speak" ]]; then

                                if [ $(wc -m < /tmp/output-whisper-live_${mypid}.txt) -ge 3 ] && [[ $speak == "speak" ]]; then
                                    if [[ $output_text == "translation" ]]; then
                                        trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt
                                    elif [[ $output_text == "both" ]]; then
                                        tput rev
                                        trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt
                                        tput sgr0
                                    else
                                        trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt >/dev/null
                                    fi
                                    if [ -f /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 ]; then

                                        # Get duration of input audio file in seconds
                                        duration=$(ffprobe -i /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 -show_entries format=duration -v quiet -of csv="p=0")

                                        # Check if duration exceeds maximum time
                                        if [ -n "$duration" ]; then

                                            if [[ $(echo "$duration > ($step_s - ( $step_s / 8 ))" | bc -l) == 1 ]]; then
                                                acceleration_factor=$(echo "scale=2; $duration / ($step_s - ( $step_s / 8 ))" | bc -l)
                                            fi
                                            if [[ $(echo "$acceleration_factor < 1.5" | bc -l) == 1 ]]; then
                                                acceleration_factor="1.5"
                                            fi
                                            # Use FFmpeg to speed up the audio file
                                            mv -f /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 /tmp/whisper-live_${mypid}_$(((i+1)%2)).mp3
                                            ffmpeg -i /tmp/whisper-live_${mypid}_$(((i+1)%2)).mp3 -filter:a "atempo=$acceleration_factor" /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 >/dev/null 2>&1

                                            # Play the modified audio
                                            mpv /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 &>/dev/null &
                                        fi
                                    fi
                                fi

                            elif [[ $output_text == "translation" ]]; then
                                trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} | tee -a /tmp/translation-whisper-live_${mypid}.txt
                            elif [[ $output_text == "both" ]]; then
                                tput rev
                                trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} | tee -a /tmp/translation-whisper-live_${mypid}.txt
                                tput sgr0
                            fi
                        fi

                    fi
                else
                  in=0
                fi
            fi
            ((i=i+1))

        done

    pkill -e -f "^ffmpeg.*${mypid}.*$"
    pkill -e -f "^./main.*${mypid}.*$"
    # Remove the used port from the temporary file
    awk -v myport="$myport" '$0 !~ myport' "$temp_file" > temp_file.tmp && mv temp_file.tmp "$temp_file"

    else

      $mpv_options "${url}" &>/dev/null &

    fi

elif [ "$playeronly" == "" ]; then # No timeshift

    if [[ $local -eq 1 ]]; then
          ffmpeg -loglevel quiet -y -probesize 32 -i "${url}" -bufsize 44M -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} &
          ffmpeg_pid=$!
          $mpv_options "${url}" &>/dev/null &
    # continuous stream in native fmt (this file will grow forever!)
    elif [[ $quality == "upper" ]]; then
        case $url in
            *youtube* | *youtu.be* )
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f b -g "$url")" \
                    -bufsize 44M -acodec ${fmt} -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} \
                    -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${myport} &
                ffmpeg_pid=$!
                ;;
            * )
                if [[ "$streamlink_force" = "streamlink" || "$url" = *twitch* ]]; then
                    if ! command -v streamlink >/dev/null 2>&1; then
                        echo "streamlink is required (https://streamlink.github.io)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -re -i "$(streamlink $url best --stream-url)" \
                        -bufsize 44M -acodec ${fmt} -map 0:a:0  /tmp/whisper-live_${mypid}.${fmt} \
                        -bufsize 4M -acodec ${fmt} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${myport} &
                    ffmpeg_pid=$!
                elif [[ "$ytdlp_force" = "yt-dlp" ]]; then
                    if ! command -v yt-dlp &>/dev/null; then
                        echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f b -g "$url")" \
                        -bufsize 44M -acodec ${fmt} -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} \
                        -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${myport} &
                    ffmpeg_pid=$!
                else
                    ffmpeg -loglevel quiet -y -probesize 32 -i $url \
                        -bufsize 44M -acodec ${fmt} -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} \
                        -bufsize 4M -map_metadata 0 -map 0:v:9? -map 0:v:8? -map 0:v:7? -map 0:v:6? -map 0:v:5? -map 0:v:4? -map 0:v:3? -map 0:v:2? -map 0:v:1? -map 0:v:0? -map 0:a:0 -acodec ${fmt} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${myport} &
                    ffmpeg_pid=$!
                fi
                ;;
        esac
        sleep 2
        nohup $mpv_options udp://127.0.0.1:${myport} >/dev/null 2>&1 &

    elif [[ $quality == "lower" ]]; then
        case $url in
            *youtube* | *youtu.be* )
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'worst' -g "$url")" \
                    -bufsize 44M -acodec ${fmt} -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} \
                    -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${myport} &
                ffmpeg_pid=$!
                ;;
            * )
                if [[ "$streamlink_force" = "streamlink" || "$url" = *twitch* ]]; then
                    if ! command -v streamlink >/dev/null 2>&1; then
                        echo "streamlink is required (https://streamlink.github.io)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -y -probesize 32 -re -i "$(streamlink $url worst --stream-url)" \
                        -bufsize 44M -acodec ${fmt} -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} \
                        -bufsize 4M -map_metadata 0 -map 0:v:0 -map 0:a:0 -acodec ${fmt} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${myport} &
                    ffmpeg_pid=$!
                elif [[ "$ytdlp_force" = "yt-dlp" ]]; then
                    if ! command -v yt-dlp &>/dev/null; then
                        echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'worst' -g "$url")" \
                        -bufsize 44M -acodec ${fmt} -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} \
                        -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${myport} &
                    ffmpeg_pid=$!
                else
                    ffmpeg -loglevel quiet -y -probesize 32 -i $url \
                        -bufsize 44M -acodec ${fmt} -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} \
                        -bufsize 4M -map_metadata 0 -map 0:v:0? -map 0:v:1? -map 0:v:2? -map 0:v:3? -map 0:v:4? -map 0:v:5? -map 0:v:6? -map 0:v:7? -map 0:v:8? -map 0:v:9? -map 0:a:0 -acodec ${fmt} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${myport} &
                    ffmpeg_pid=$!
                fi
                ;;
        esac
        sleep 2
        nohup $mpv_options udp://127.0.0.1:${myport} >/dev/null 2>&1 &

    elif [[ $quality == "raw" ]]; then
        case $url in
            *youtube* | *youtu.be* )
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f 'worst' -g $url) -bufsize 44M -acodec ${fmt} -threads 2 -map 0:a:0 -vsync 2 -reset_timestamps 1 /tmp/whisper-live_${mypid}.${fmt} &
                ffmpeg_pid=$!
                ;;
            * )
                if [[ "$streamlink_force" = "streamlink" || "$url" = *twitch* ]]; then
                    if ! command -v streamlink >/dev/null 2>&1; then
                        echo "streamlink is required (https://streamlink.github.io)"
                        exit 1
                    fi
                    streamlink $url worst -O 2>/dev/null | ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i - -bufsize 44M -acodec ${fmt} -threads 2 -map 0:a:0 -vsync 2 -reset_timestamps 1 /tmp/whisper-live_${mypid}.${fmt} &
                    ffmpeg_pid=$!
                elif [[ "$ytdlp_force" = "yt-dlp" ]]; then
                    if ! command -v yt-dlp &>/dev/null; then
                        echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f 'worst' -g $url) -bufsize 44M -acodec ${fmt} -threads 2 -map 0:a:0 -vsync 2 -reset_timestamps 1 /tmp/whisper-live_${mypid}.${fmt} &
                    ffmpeg_pid=$!
                else
                    ffmpeg -loglevel quiet -y -probesize 32 -i $url -bufsize 44M -map 0:a:0 /tmp/whisper-live_${mypid}.${fmt} &
                    ffmpeg_pid=$!
                fi
                ;;
        esac
        $mpv_options $url &>/dev/null &
    fi

    if [ $? -ne 0 ]; then
        printf "Error: The player could not play the stream. Please check your input or try again later\n"
        exit 1
    fi

    printf "Buffering audio. Please wait...\n\n"
    sleep $(($step_s+3))

    # do not stop script on error
    set +e

    i=0
    SECONDS=0
    acceleration_factor="1.5"

    while [ $running -eq 1 ]; do
        # extract the next piece from the main file above and transcode to wav. -ss sets start time, -0.x seconds adjust
        err=1
        while [ $err -ne 0 ]; do
            if [ $i -gt 0 ]; then
                ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live_${mypid}.${fmt} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$i * $step_s - 1" | bc -l) -t $(echo "$step_s" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
            else
                ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live_${mypid}.${fmt} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -to $(echo "$step_s - 1" | bc -l) /tmp/whisper-live_${mypid}.wav 2> /tmp/whisper-live_${mypid}.err
            fi
            err=$(cat /tmp/whisper-live_${mypid}.err | wc -l)
        done

        ./main -l ${language} ${translate} -t 4 -m ./models/ggml-${model}.bin -f /tmp/whisper-live_${mypid}.wav --no-timestamps -otxt 2> /tmp/whisper-live_${mypid}-err.err | tail -n 1 | tr -d '<>^*_' | tee /tmp/output-whisper-live_${mypid}.txt >/dev/null

        if [[ $output_text == "original" ]] || [[ $output_text == "both" ]] || [[ $trans == "" ]]; then
            cat /tmp/output-whisper-live_${mypid}.txt | tee -a /tmp/transcription-whisper-live_${mypid}.txt
        else
            cat /tmp/output-whisper-live_${mypid}.txt >> /tmp/transcription-whisper-live_${mypid}.txt
        fi

        if [[ $trans == "trans" ]]; then
            if [ $(wc -m < /tmp/output-whisper-live_${mypid}.txt) -ge 3 ] && [[ $speak == "speak" ]]; then
                if [[ $output_text == "translation" ]]; then
                    trans -i "/tmp/output-whisper-live_${mypid}.txt" -no-warn -b ":${trans_language}" -download-audio-as "/tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3" | tee -a /tmp/translation-whisper-live_${mypid}.txt
                elif [[ $output_text == "both" ]]; then
                    tput rev
                    trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt
                    tput sgr0
                else
                    trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} -download-audio-as /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${mypid}.txt >/dev/null
                fi
                if [ -f /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 ]; then

                    # Get duration of input audio file in seconds
                    duration=$(ffprobe -i /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 -show_entries format=duration -v quiet -of csv="p=0")

                    # Check if duration exceeds maximum time
                    if [ -n "$duration" ]; then
                        if [[ $(echo "$duration > ($step_s - ( $step_s / 8 ))" | bc -l) == 1 ]]; then
                            acceleration_factor=$(echo "scale=2; $duration / ($step_s - ( $step_s / 8 ))" | bc -l)
                        fi
                        if [[ $(echo "$acceleration_factor < 1.5" | bc -l) == 1 ]]; then
                            acceleration_factor="1.5"
                        fi
                        # Use FFmpeg to speed up the audio file
                        mv -f /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 /tmp/whisper-live_${mypid}_$(((i+1)%2)).mp3
                        ffmpeg -i /tmp/whisper-live_${mypid}_$(((i+1)%2)).mp3 -filter:a "atempo=$acceleration_factor" /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 >/dev/null 2>&1

                        # Play the modified audio
                        mpv /tmp/whisper-live_${mypid}_$(((i+2)%2)).mp3 &>/dev/null &
                    fi
                fi
            elif [[ $output_text == "translation" ]]; then
                trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} | tee -a /tmp/translation-whisper-live_${mypid}.txt
            elif [[ $output_text == "both" ]]; then
                tput rev
                trans -i /tmp/output-whisper-live_${mypid}.txt -no-warn -b :${trans_language} | tee -a /tmp/translation-whisper-live_${mypid}.txt
                tput sgr0
            fi
        fi
        while [ $SECONDS -lt $((($i+1)*$step_s)) ]; do
            sleep 0.1
        done
        ((i=i+1))
    done

    pkill -e -f "^ffmpeg.*${mypid}.*$"
    pkill -e -f "^./main.*${mypid}.*$"
    # Remove the used port from the temporary file
    awk -v myport="$myport" '$0 !~ myport' "$temp_file" > temp_file.tmp && mv temp_file.tmp "$temp_file"

else
    if [[ $local -eq 0 ]] ; then
        $mpv_options $url &>/dev/null &
    else
        $mpv_options "${url}" &>/dev/null &
    fi
fi
