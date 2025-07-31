#!/bin/bash

# livestream_video.sh v. 3.56 - Plays audio/video files or video streams, transcribing the audio using AI.
# Supports timeshift, multi-instance/user, per-channel/global options, online translation, and TTS.
# Generates subtitles from audio/video files.
#
# Copyright (c) 2023 Antonio R.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# https://github.com/antor44/livestream_video

# --- Configuration and Constants ---

# Default URL to use if none is provided
readonly URL_DEFAULT="https://cbsn-det.cbsnstream.cbsnews.com/out/v1/169f5c001bc74fa7a179b19c20fea069/master.m3u8"
# Temporary file to store used port numbers for multi-instance support
readonly TEMP_FILE="/tmp/used_ports-livestream_video.txt"

# --- Default Parameter Values ---

FMT="mp3"               # Audio format
LOCAL_FILE=0            # Flag for local file (0 = false, 1 = true)
STEP_S=8                # Step size in seconds for audio processing
MODEL="base"            # Default Whisper model
LANGUAGE="auto"         # Default language for Whisper
TRANSLATE=""            # Translate to English flag
PLAYER_ONLY=""          # Only play the video/audio, no transcription
MPV_OPTIONS="mpv"       # Default player and options
QUALITY="raw"           # Video quality (raw, upper, lower)
STREAMLINK_FORCE=""     # Force usage of Streamlink
YTDLP_FORCE=""          # Force usage of yt-dlp
SEGMENT_TIME=10         # Time for each segment file (minutes) in timeshift
SEGMENTS=4              # Number of segment files for timeshift
SYNC=4                  # Transcription/video sync time (seconds)
SPEAK=""                # Enable Text-to-Speech
TRANS=""                # Enable online translation
OUTPUT_TEXT="both"      # Output text during translation (original, translation, both, none)
TRANS_LANGUAGE="en"     # Default translation language
SUBTITLES=""            # Generate subtitles flag
AUDIO_SOURCE=""         # Audio source (pulse:index or avfoundation:index)
AUDIO_INDEX="0"         # Default audio index
WHISPER_EXECUTABLE=""   # Path to the Whisper executable


# --- Style Configuration ---
# Auto-detect terminal capabilities for styled output.
if [[ ($LANG == *.UTF-8 || $LC_ALL == *.UTF-8) && "$TERM" != "xterm" && "$TERM" != "linux" && "$TERM" != "vt100" ]]; then
    USE_EMOJI=true
else
    USE_EMOJI=false
fi

if [ "$USE_EMOJI" = true ]; then
    # Emoji symbols
    ICON_OK="✅"
    ICON_ERROR="❌"
    ICON_WARN="⚠️"
    ICON_ROCKET="🚀"
else
    # ASCII-safe symbols
    ICON_OK="[OK]"
    ICON_ERROR="[ERROR]"
    ICON_WARN="[WARNING]"
    ICON_ROCKET="-->"
fi


# --- Supported Languages and Models ---

# Array of supported languages for Whisper
readonly LANGUAGES=( "auto" "af" "am" "ar" "as" "az" "ba" "be" "bg" "bn" "bo" "br" "bs" "ca" "cs" "cy" "da" "de" "el" "en" "es" "et" "eo" "eu" "fa" "fi" "fo" "fr" "ga" "gl" "gu" "ha" "haw" "he" "hi" "hr" "ht" "hu" "hy" "id" "is" "it" "ja" "jw" "ka" "kk" "km" "kn" "ko" "ku" "ky" "la" "lb" "ln" "lo" "lt" "lv" "mg" "mi" "mk" "ml" "mn" "mr" "ms" "mt" "my" "ne" "nl" "nn" "no" "oc" "or" "pa" "pl" "ps" "pt" "ro" "ru" "sa" "sd" "sh" "si" "sk" "sl" "sn" "so" "sq" "sr" "su" "sv" "sw" "ta" "te" "tg" "th" "tl" "tk" "tr" "tt" "ug" "uk" "ur" "uz" "vi" "vo" "wa" "xh" "yi" "yo" "zh" "zu")

# Array of base Whisper models
readonly MODELS=( "tiny.en" "tiny" "base.en" "base" "small.en" "small" "medium.en" "medium" "large-v1" "large-v2" "large-v3" "large-v3-turbo" )
# Array of Whisper model suffixes
readonly SUFFIXES=( "-q2_k" "-q3_k" "-q4_0" "-q4_1" "-q4_k" "-q5_0" "-q5_1" "-q5_k" "-q6_k" "-q8_0" )

# --- Function Definitions ---
# Build all models list combining base models and suffixes
build_model_list() {
    local model_list=()
    local modele
    local suffix
    for modele in "${MODELS[@]}"; do
        model_list+=("$modele")
        for suffix in "${SUFFIXES[@]}"; do
            model_list+=("${modele}${suffix}")
        done
    done
    echo "${model_list[@]}"  # Output the array as a space-separated string
}

# Get the complete model list.
readonly MODEL_LIST=( $(build_model_list) ) # Populate model list
readonly OUTPUT_TEXT_LIST=( "original" "translation" "both" "none" )

# --- Function Definitions ---

# Checks if required external tools (ffmpeg, whisper, etc.) are available.
check_requirements() {
    # Use specified executable or find and select one

    if [[ -n "$WHISPER_EXECUTABLE" ]]; then
        # Check if the executable exists in the current directory or in the PATH
        if [[ ! -x "$(command -v "$WHISPER_EXECUTABLE")" ]]; then
            echo "${ICON_ERROR} Specified whisper executable '$WHISPER_EXECUTABLE' not found."
            exit 1
        fi
    else
        # Array of executable names in priority order
        local executables=("./build/bin/whisper-cli" "./main" "whisper-cpp" "pwcpp" "whisper")

        # Loop through each executable name
        for exe in "${executables[@]}"; do
            # Check if the executable exists in the current directory or in the PATH
            if [[ -x "$(command -v "$exe")" ]]; then
                # Save the first executable found and exit loop
                WHISPER_EXECUTABLE="$exe"
                break
            fi
        done
    fi

    echo
    if [[ -z "$WHISPER_EXECUTABLE" ]]; then
        echo "${ICON_ERROR} Whisper executable is required."
        exit 1
    elif [[ "$PLAYER_ONLY" == "" ]]; then
        echo -n "Found whisper executable: ${WHISPER_EXECUTABLE} - "
        local current_dir=$(pwd)
        local models_dir="$current_dir/models"
        if [ ! -d "$models_dir" ]; then
            mkdir -p "$models_dir"
        fi
    fi

    if ! command -v ffmpeg &>/dev/null; then
        echo "${ICON_ERROR} ffmpeg is required (https://ffmpeg.org)."
        exit 1
    fi

    if [[ "$WHISPER_EXECUTABLE" == "whisper" && ! -f "./models/${MODEL}.pt" ]]; then
      echo "Please wait until the model file is downloaded for first time."
      whisper --threads 4 --model ${MODEL} --model_dir ./models /tmp/whisper-live_${MYPID}.wav > /dev/null 2> /tmp/whisper-live_${MYPID}-err.err
    fi
}


# Prints usage instructions and exits.
usage() {
    cat <<EOF
Usage: $0 stream_url [or /path/media_file or pulse:index or avfoundation:index] [--step step_s] [--model model] [--language language] [--executable exe_path] [--translate] [--subtitles] [--timeshift] [--segments segments (2<n<99)] [--segment_time minutes (1<minutes<99)] [--sync seconds (0 <= seconds <= (Step - 3))] [--trans trans_language output_text speak] [player player_options]

Example:
  $0 https://cbsn-det.cbsnstream.cbsnews.com/out/v1/169f5c001bc74fa7a179b19c20fea069/master.m3u8 --step 8 --model base --language auto --translate --timeshift --segments 4 --segment_time 10 --trans es both speak

Help:

  livestream_video.sh v. 3.56 - plays audio/video files or video streams, transcribing the audio using AI technology.
  The application supports timeshift, multi-instance/user, per-channel/global options, online translation, and TTS.
  Generates subtitles from audio/video files.

  pulse:index or avfoundation:index
    Live transcription from the selected device index. PulseAudio (Linux/WSL2), AVFoundation (macOS).
    Transcription quality depends on your computer, model, volume, sound configuration, and noise.

  Local audio/video files (bash script only): Enclose in double quotes, with full path.  Use './' if in the same directory.

  Text-to-speech and translation (non-English) use Translate-shell (Google service). Availability not guaranteed. TTS works for short segments and limited languages.

  --streamlink    Forces URL processing by Streamlink.
  --yt-dlp        Forces URL processing by yt-dlp.

  --[raw, upper, lower]: Video quality options. Affects timeshift for IPTV.
                  'raw': Downloads another stream without modification for the player.
                  'upper'/'lower': Downloads one stream, re-encoded for the player (best/worst quality).
                  Saves data; not all streams support it. Timeshift downloads only one stream.

  --player        Specify player and options. Valid: smplayer, mpv, mplayer, vlc, etc. Use '[none]' or '[true]' for no player.

  --step          Size of sound parts for AI inference (seconds).

  --model         Whisper Models: $(echo ${MODELS[@]})
                  with suffixes: $(echo ${SUFFIXES[@]})

  --executable    Specify the whisper executable (full path or command name).

  --language      Whisper Languages: auto (Autodetect), af (Afrikaans), am (Amharic), ar (Arabic), as (Assamese), az (Azerbaijani), be (Belarusian), bg (Bulgarian), bn (Bengali), br (Breton), bs (Bosnian), ca (Catalan), cs (Czech), cy (Welsh), da (Danish), de (German), el (Greek), en (English), eo (Esperanto), es (Spanish), et (Estonian), eu (Basque), fa (Persian), fi (Finnish), fo (Faroese), fr (French), ga (Irish), gl (Galician), gu (Gujarati), ha (Bantu), haw (Hawaiian), he ([Hebrew]), hi (Hindi), hr (Croatian), ht (Haitian Creole), hu (Hungarian), hy (Armenian), id (Indonesian), is (Icelandic), it (Italian), iw (Hebrew), ja (Japanese), jw (Javanese), ka (Georgian), kk (Kazakh), km (Khmer), kn (Kannada), ko (Korean), ku (Kurdish), ky (Kyrgyz), la (Latin), lb (Luxembourgish), lo (Lao), lt (Lithuanian), lv (Latvian), mg (Malagasy), mi (Maori), mk (Macedonian), ml (Malayalam), mn (Mongolian), mr (Marathi), ms (Malay), mt (Maltese), my (Myanmar), ne (Nepali), nl (Dutch), nn (Nynorsk), no (Norwegian), oc (Occitan), or (Oriya), pa (Punjabi), pl (Polish), ps (Pashto), pt (Portuguese), ro (Romanian), ru (Russian), sd (Sindhi), sh (Serbo-Croatian), si (Sinhala), sk (Slovak), sl (Slovenian), sn (Shona), so (Somali), sq (Albanian), sr (Serbian), su (Sundanese), sv (Swedish), sw (Swahili), ta (Tamil), te (Telugu), tg (Tajik), th (Thai), tl (Tagalog), tr (Turkish), tt (Tatar), ug (Uighur), uk (Ukrainian), ur (Urdu), uz (Uzbek), vi (Vietnamese), vo (Volapuk), wa (Walloon), xh (Xhosa), yi (Yiddish), yo (Yoruba), zh (Chinese), zu (Zulu)

  --translate     Automatic English translation using Whisper AI (English only).

  --subtitles     Generate subtitles (.srt) from audio/video, with language, Whisper AI translation, and online translation.

  --trans         Online translation and Text-to-Speech (translate-shell: https://github.com/soimort/translate-shell).
    trans_language: Translation language.
    output_text: Output text: original, translation, both, none.
    speak: Online Text-to-Speech.

  --timeshift     Timeshift feature (VLC player only).

  --sync          Transcription/video synchronization time (seconds, 0 <= seconds <= (Step - 3)).

  --segments      Number of segment files for timeshift (2 <= n <= 99).

  --segment_time  Time for each segment file (1 <= minutes <= 99).

EOF
    exit 1
}

# Checks if VLC is still running (used in timeshift mode).
vlc_check() {
    local check_pid=$(ps -p "$VLC_PID") # check pidof player

    if [[ $check_pid != *vlc* ]] && [[ $check_pid != *VLC* ]]; then # timeshift exit
        echo
        pkill -f "^ffmpeg.*${MYPID}.*$"
        pkill -f "^${WHISPER_EXECUTABLE}.*${MYPID}.*$"
        # Remove the used port from the temporary file
        if [ -f "$TEMP_FILE" ]; then
            awk -v myport="$MYPORT" '$0 !~ myport' "$TEMP_FILE" > temp_file.tmp && mv temp_file.tmp "$TEMP_FILE"
        fi
        echo
        echo "${ICON_OK} VLC closed. Timeshift finished ${ICON_OK}"
        echo
        exit 0
    fi
}

# Gets a unique, unused port number for loopback communication.
get_unique_port() {
  local min=1024
  local max=65535
  local random_port
  local max_ports=$((max - min + 1))

    # Create the temporary file if it doesn't exist
    if ! [ -f "$TEMP_FILE" ]; then
        touch "$TEMP_FILE"
    fi

    # Check if the temporary file exceeds the maximum number of ports
    if [ "$(wc -l < "$TEMP_FILE")" -ge "$max_ports" ]; then
        echo "${ICON_ERROR} Error: Maximum number of ports ($max_ports) reached!"
        exit 1
    fi

    while true; do
        # Generate a random port number between 1024 and 65535
        random_port=$((RANDOM % (max - min + 1) + min))

        # Check if the random port is already in use
        if ! grep -q "$random_port" "$TEMP_FILE"; then
            echo "$random_port" >> "$TEMP_FILE"
            break
        fi
    done

    # Return the generated unique port
    echo "$random_port"
}


# Processes a single audio chunk with Whisper and handles translation/TTS.
# Takes the path to the temporary WAV file as its first argument.
process_audio_chunk() {
    local wav_file="$1"

    # The processing pipe is designed to be robust across whisper.cpp versions:
    # 1. tr '\r' '\n': Converts carriage returns to newlines to normalize output from all versions.
    # 2. grep '^\[': Isolates ALL lines that start with a timestamp.
    # 3. sed 's/^\[.*\] *//': Strips the timestamp from EACH of those lines.
    # 4. paste -s -d ' ': Joins all the cleaned lines back into a single line, separated by spaces.
    # 5. tr -d ...: Cleans up potential garbage characters.
    # 6. tee ...: Prints to screen and saves to a file.

    if [[ "$WHISPER_EXECUTABLE" == "./build/bin/whisper-cli" ]] || [[ "$WHISPER_EXECUTABLE" == "./main" ]] || [[ "$WHISPER_EXECUTABLE" == "whisper-cpp" ]]; then
        "$WHISPER_EXECUTABLE" -l ${LANGUAGE} ${TRANSLATE} -t 4 -m ./models/ggml-${MODEL}.bin -f "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tr '\r' '\n' | grep '^\[' | sed 's/^\[.*\] *//' | paste -s -d ' ' | tr -d '<>^*_' | tee /tmp/output-whisper-live_${MYPID}.txt >/dev/null
        err=$?
    elif [[ "$WHISPER_EXECUTABLE" == "pwcpp" ]]; then
        if [[ "$TRANSLATE" == "--translate" ]]; then
            pwcpp --language ${LANGUAGE} --translate translate --n_threads 4 -m ./models/ggml-${MODEL}.bin "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tr '\r' '\n' | grep '^\[' | sed 's/^\[.*\] *//' | paste -s -d ' ' | tr -d '<>^*_' | tee /tmp/output-whisper-live_${MYPID}.txt >/dev/null
            err=$?
        else
            pwcpp --language ${LANGUAGE} --n_threads 4 -m ./models/ggml-${MODEL}.bin "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tr '\r' '\n' | grep '^\[' | sed 's/^\[.*\] *//' | paste -s -d ' ' | tr -d '<>^*_' | tee /tmp/output-whisper-live_${MYPID}.txt >/dev/null
            err=$?
        fi
    elif [[ "$WHISPER_EXECUTABLE" == "whisper" ]]; then
        # The python version of whisper has a different, more stable output format and is not affected.
        if [[ "$TRANSLATE" == "--translate" ]]; then
            if [[ "$LANGUAGE" == "auto" ]]; then
                whisper --temperature 0 --beam_size 8 --best_of 4 --initial_prompt "" --threads 4 --model ${MODEL} --task translate --model_dir ./models --output_dir /tmp --output_format txt "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tail -n 1 | tr -d '<>^*_' | tee /tmp/aout-whisper-live_${MYPID}.txt >/dev/null
                err=$?
            else
                whisper --temperature 0 --beam_size 8 --best_of 4 --initial_prompt "" --threads 4 --model ${MODEL} --task translate --model_dir ./models --output_dir /tmp --output_format txt "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tail -n 1 | tr -d '<>^*_' | tee /tmp/aout-whisper-live_${MYPID}.txt >/dev/null
                err=$?
            fi
        else
            if [[ "$LANGUAGE" == "auto" ]]; then
                  whisper --temperature 0 --beam_size 8 --best_of 4 --initial_prompt "" --threads 4 --model ${MODEL} --model_dir ./models --output_dir /tmp --output_format txt "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tail -n 1 | tr -d '<>^*_' | tee /tmp/aout-whisper-live_${MYPID}.txt >/dev/null
                  err=$?
            else
                  whisper --temperature 0 --beam_size 8 --best_of 4 --initial_prompt "" --language ${LANGUAGE} --threads 4 --model ${MODEL} --model_dir ./models --output_dir /tmp --output_format txt "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tail -n 1 | tr -d '<>^*_' | tee /tmp/aout-whisper-live_${MYPID}.txt >/dev/null
                  err=$?
            fi
        fi
        sed 's/\[[^][]*\] *//g' /tmp/aout-whisper-live_${MYPID}.txt > /tmp/output-whisper-live_${MYPID}.txt
    fi

    # --- El resto de la función (traducción, etc.) no necesita cambios ---
    # Print original/translated text to console
    if [[ $OUTPUT_TEXT == "original" ]] || [[ $OUTPUT_TEXT == "both" ]] || [[ $TRANS == "" ]]; then
        cat /tmp/output-whisper-live_${MYPID}.txt | tee -a /tmp/transcription-whisper-live_${MYPID}.txt
    else
        cat /tmp/output-whisper-live_${MYPID}.txt >> /tmp/transcription-whisper-live_${MYPID}.txt
    fi

    # Handle online translation and TTS
    if [[ $TRANS == "trans" ]]; then
        if [[ $(wc -m < /tmp/output-whisper-live_${MYPID}.txt) -ge 3 ]] && [[ $SPEAK == "speak" ]]; then
            if [[ $OUTPUT_TEXT == "translation" ]]; then
                trans -i /tmp/output-whisper-live_${MYPID}.txt -no-warn -b :${TRANS_LANGUAGE} -download-audio-as /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${MYPID}.txt
            elif [[ $OUTPUT_TEXT == "both" ]]; then
                tput rev
                trans -i /tmp/output-whisper-live_${MYPID}.txt -no-warn -b :${TRANS_LANGUAGE} -download-audio-as /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${MYPID}.txt
                tput sgr0
            else
                trans -i /tmp/output-whisper-live_${MYPID}.txt -no-warn -b :${TRANS_LANGUAGE} -download-audio-as /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 | tee -a /tmp/translation-whisper-live_${MYPID}.txt >/dev/null
            fi
            if [ -f /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 ]; then
                # ... (TTS logic remains the same)
                duration=$(ffprobe -i /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 -show_entries format=duration -v quiet -of csv="p=0")
                if [ -n "$duration" ]; then
                    if [[ $(echo "$duration > ($STEP_S - ( $STEP_S / 8 ))" | bc -l) == 1 ]]; then
                        acceleration_factor=$(echo "scale=2; $duration / ($STEP_S - ( $STEP_S / 8 ))" | bc -l)
                    fi
                    if [[ $(echo "$acceleration_factor < 1.5" | bc -l) == 1 ]]; then
                        acceleration_factor="1.5"
                    fi
                    mv -f "/tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3" "/tmp/whisper-live_${MYPID}_$(((i+1)%2)).mp3"
                    ffmpeg -i /tmp/whisper-live_${MYPID}_$(((i+1)%2)).mp3 -filter:a "atempo=$acceleration_factor" /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 >/dev/null 2>&1
                    mpv /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 &>/dev/null &
                fi
            fi
        # SYNTAX FIX: The elifs now correctly follow a single if structure
        elif [[ $OUTPUT_TEXT == "translation" ]]; then
            trans -i /tmp/output-whisper-live_${MYPID}.txt -no-warn -b :${TRANS_LANGUAGE} | tee -a /tmp/translation-whisper-live_${MYPID}.txt
        elif [[ $OUTPUT_TEXT == "both" ]]; then
            tput rev
            trans -i /tmp/output-whisper-live_${MYPID}.txt -no-warn -b :${TRANS_LANGUAGE} | tee -a /tmp/translation-whisper-live_${MYPID}.txt
            tput sgr0
        fi
    fi
}


# --- Main Script Execution ---

# Set shell options for error handling (except on macOS, where set -e can be problematic)
if [[ "$(uname)" != "Darwin" ]]; then
    set -eo pipefail
fi

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        *://* | /* | ./* )
            URL=$1
            if [[ $URL == /* ]] || [[ $URL == ./* ]]; then
                LOCAL_FILE=1
            fi
            if [[ $URL == ./* ]]; then
                URL=${1#./}
                URL="$(pwd)/$URL"
            fi
            ;;
        pulse* | avfoundation* )
            AUDIO_SOURCE=$1
            ;;
        --model )
            shift
            if [[ " ${MODEL_LIST[*]} " =~ " $1 " ]]; then
                MODEL=$1
            else
                echo ""; echo "${ICON_ERROR} Invalid model option: $1"; echo ""; usage; exit 1
            fi
            ;;
        --language )
            shift
            if [[ " ${LANGUAGES[*]} " =~ " $1 " ]]; then
                LANGUAGE=$1
            else
                echo ""; echo "${ICON_ERROR} Invalid language option: $1"; echo ""; usage; exit 1
            fi
            ;;
        --step )
            shift
            STEP_S=$1
            if ! [[ "$STEP_S" =~ ^[0-9]+$ ]]; then
                echo "${ICON_ERROR} Error: Step time must be a numeric value."
                usage
                exit 1
            fi
            if [[ "$STEP_S" -gt 60 ]] || [[ "$STEP_S" -lt 0 ]]; then
                echo "${ICON_ERROR} Error: Step time value out of range."
                usage
                exit 1
            fi
            ;;
        --translate ) TRANSLATE=$1;;
        --subtitles ) SUBTITLES=${1#--};;
        --playeronly ) PLAYER_ONLY=${1#--};;
        --timeshift ) TIMESHIFT=${1#--};;
        --segment_time )
            shift
            SEGMENT_TIME=$1
            if ! [[ "$SEGMENT_TIME" =~ ^[0-9]+$ ]]; then
                echo "${ICON_ERROR} Error: Segment Time must be a numeric value."
                usage
                exit 1
            fi
            ;;
        --segments )
            shift
            SEGMENTS=$1
            if ! [[ "$SEGMENTS" =~ ^[0-9]+$ ]]; then
                echo "${ICON_ERROR} Error: Segments must be a numeric value."
                usage
                exit 1
            fi
            ;;
        --sync )
            shift
            SYNC=$1
            if ! [[ "$SYNC" =~ ^[0-9]+$ ]]; then
                echo "${ICON_ERROR} Error: Sync must be a numeric value."
                usage
                exit 1
            fi
            ;;
        --executable )
            shift
            WHISPER_EXECUTABLE=$1
            ;;
        --raw | --upper | --lower ) QUALITY=${1#--};;
        --streamlink ) STREAMLINK_FORCE=${1#--};;
        --yt-dlp ) YTDLP_FORCE=${1#--};;
        --trans )
            TRANS="trans"
            if ! command -v trans &>/dev/null; then
                echo "translate-shell is required (https://github.com/soimort/translate-shell)"
                exit 1
            fi
            if [[ $# -gt 1 ]]; then
                if [[ $2 == --* ]]; then
                    echo "Warning: Missing language option in the trans options. Default is ${TRANS_LANGUAGE}."
                else
                    while [[ $# -gt 1 ]] && [[ $2 != --* ]]; do
                        if [[ " ${LANGUAGES[*]} " =~ " $2 " ]]; then
                            TRANS_LANGUAGE=$2
                        elif [[ " ${OUTPUT_TEXT_LIST[*]} " =~ " $2 " ]]; then
                            OUTPUT_TEXT=$2
                        elif [[ " speak " == " $2 " ]]; then
                            SPEAK="speak"
                        else
                            echo ""; echo "*** Wrong option $2"; echo ""; usage; exit 1
                        fi
                        shift
                    done
                    if [[ $# -gt 0 ]] && [[ $2 != --* ]]; then
                        if [[ " ${LANGUAGES[*]} " =~ " $1 " ]]; then
                            TRANS_LANGUAGE=$1
                        elif [[ " ${OUTPUT_TEXT_LIST[*]} " =~ " $1 " ]]; then
                            OUTPUT_TEXT=$1
                        elif [[ " speak " == " $1 " ]]; then
                            SPEAK="speak"
                        else
                            echo ""; echo "*** Wrong option $1"; echo ""; usage; exit 1
                        fi
                    fi
                fi
            else
                echo "Warning: Missing language option in the trans options. Default is ${TRANS_LANGUAGE}."
            fi
            ;;
        --player )
            shift
            MPV_OPTIONS=$1
            if [[ $MPV_OPTIONS == none ]]; then
                MPV_OPTIONS="true"
            fi
            if [[ $# -gt 1 ]]; then
                while [[ $# -gt 1 ]]; do
                    case $2 in
                        --model | --language | --step | --translate | --subtitles | --playeronly | --timeshift | --segment_time | --segments | --sync | --raw | --upper | --lower | --streamlink | --yt-dlp | --trans )
                            break
                            ;;
                        *)
                            shift
                            MPV_OPTIONS+=" $1"
                            ;;
                    esac
                done
            fi
            ;;
        *)
            echo ""; echo "*** Unknown option $1"; echo ""; usage; exit 1
            ;;
    esac
    shift
done

# Ensure required tools are present
check_requirements

# Validate Timeshift parameters
if [ "$TIMESHIFT" = "timeshift" ]; then
    if [ "$SEGMENTS" -lt 2 ] || [ "$SEGMENTS" -gt 99 ]; then
        echo "${ICON_ERROR} Error: Segments should be between 2 and 99."
        usage
        exit 1
    fi

    if [ "$SEGMENT_TIME" -lt 1 ] || [ "$SEGMENT_TIME" -gt 99 ]; then
        echo "${ICON_ERROR} Error: Segment Time should be between 2 and 99."
        usage
        exit 1
    fi

    if [ $SYNC -lt 0 ] || [ $SYNC -gt $((STEP_S - 3)) ]; then
        echo "${ICON_ERROR} Error: Sync should be between 0 and $((STEP_S - 3))."
        usage
        exit 1
    fi
fi

# Get the script's PID and check for permissions on temporary files.
MYPID=$(ps aux | awk '/livestream_video\.sh/ {pid=$2} END {print pid}')

if [ -n "$MYPID" ]; then
    if [ -e "/tmp/whisper-live_${MYPID}.wav" ] && ! [ -w "/tmp/whisper-live_${MYPID}.wav" ]; then
      echo ""
      echo "${ICON_ERROR} Error: Permission denied to access files /tmp/whisper-live_${MYPID}.*"
      echo ""
      exit 1
    else
      if [[ "$TIMESHIFT" == "timeshift" ]] || ( [ $LOCAL_FILE -eq 0 ] && [[ "$PLAYER_ONLY" == "" ]] && ([[ $QUALITY == "upper" ]] || [[ $QUALITY == "lower" ]])); then
          MYPORT=$(get_unique_port "$MYPID")
          echo "New script PID: $MYPID - Loopback port: $MYPORT"
      else
          echo "New script PID: $MYPID"
      fi
    fi
else
  echo ""
  echo "${ICON_ERROR} An unknown error has occurred. ${ICON_ERROR}"
  echo ""
  exit 1
fi

echo ""


# Set URL and audio index based on input, handle default URL.
if [[ "$AUDIO_SOURCE" == "pulse:"* ]] || [[ "$AUDIO_SOURCE" == "avfoundation:"* ]]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        URL="avfoundation"
        AUDIO_INDEX="${AUDIO_SOURCE##*:}"
    else
        # Linux
        URL="pulse"
        AUDIO_INDEX="${AUDIO_SOURCE##*:}"
    fi
    echo " * Audio source: $AUDIO_SOURCE"
else
    echo -n "[+] Quality: $QUALITY - "
    if [ -z "$URL" ]; then
        URL="$URL_DEFAULT"
        echo "No url specified, using default: $URL"
    else
        echo "url specified by user: $URL"
    fi
fi
echo ""

# Print transcription options.
if [[ "$PLAYER_ONLY" == "" ]] || [[ $SUBTITLES == "subtitles" ]] ; then
    # if "translate" then translate to english
    if [[ $TRANSLATE == "--translate" ]]; then
        printf "[+] Transcribing stream with model '$MODEL', '$STEP_S' seconds steps, language '$LANGUAGE', translate to English (press Ctrl+C to stop).\n\n"
    else
        TRANSLATE=""
        printf "[+] Transcribing stream with model '$MODEL', '$STEP_S' seconds steps, language '$LANGUAGE', NO translate to English (press Ctrl+C to stop).\n\n"
    fi
fi

# if online translate"
if [[ "$TRANS" == "trans" ]] && [[ "$PLAYER_ONLY" == "" ]]; then
    if [[ "$SPEAK" == "speak" ]]; then
        printf "[+] Online translation into language '$TRANS_LANGUAGE', output text: '$OUTPUT_TEXT', Text-to-speech.\n\n"
    else
        printf "[+] Online translation into language '$TRANS_LANGUAGE', output text: '$OUTPUT_TEXT'.\n\n"
    fi
fi


# Error if generating subtitles with remote source.
if [[ $SUBTITLES == "subtitles" ]] && [[ $LOCAL_FILE -eq 0 ]]; then
    echo ""
    echo "${ICON_ERROR} Error: Generate Subtitles only available for local Audio/Video Files."
    echo ""
    # Remove the used port from the temporary file
    if [ -f "$TEMP_FILE" ]; then
        awk -v myport="$MYPORT" '$0 !~ myport' "$TEMP_FILE" > temp_file.tmp && mv temp_file.tmp "$TEMP_FILE"
    fi
    exit 1
fi


# --- Subtitle Generation ---

# Generate Subtitles from a local Audio/Video File.
if [[ $SUBTITLES == "subtitles" ]] && [[ $LOCAL_FILE -eq 1 ]]; then

    echo ""
    echo "=========================================="
    echo "  ${ICON_ROCKET} Starting Subtitle Generation  ${ICON_ROCKET}"
    echo "=========================================="
    echo ""
    # do not stop script on error
    set +e

    url_no_ext="${URL%.*}"
    skip_transcription=false
    source_srt_file="" # This will hold the path to the SRT file to be used by 'trans'

    # --- Pre-flight Check: Ask about re-running the AI to save processing time ---

    # Determine the destination file for Whisper's output
    if [[ "$TRANSLATE" == "--translate" ]]; then
        whisper_dest_file="${url_no_ext}.en.srt"
        whisper_file_description="Whisper AI Translated Subtitle (en)"
    else
        whisper_dest_file="${url_no_ext}.${LANGUAGE}.srt"
        whisper_file_description="Whisper AI Original Subtitle (${LANGUAGE})"
    fi

    if [ -e "$whisper_dest_file" ]; then
        echo "ATTENTION: An AI-generated subtitle file already exists."
        echo "  - File: $whisper_dest_file"
        echo "  - Type: $whisper_file_description"
        echo ""
        read -p "Do you want to re-run the AI and overwrite this file? (Answering 'n' will use the existing file) [y/n]: " response

        # Normalize user input: convert to lowercase and remove leading/trailing whitespace
        response_clean=$(echo "$response" | tr '[:upper:]' '[:lower:]' | xargs)

        case "$response_clean" in
            n|no)
                echo ""
                echo "-> Skipping AI transcription. The existing file will be used for any further steps."
                skip_transcription=true
                source_srt_file="$whisper_dest_file" # Use this existing file for online translation
                ;;
            y|yes)
                echo ""
                echo "-> OK. The existing file will be overwritten upon completion."
                # Let the script proceed with skip_transcription=false
                ;;
            *)
                echo ""
                echo "${ICON_ERROR} Invalid response. Aborting. ${ICON_ERROR}"
                echo ""
                exit 1
                ;;
        esac
    fi

    # --- Main Processing ---

    err=0
    temp_whisper_srt="/tmp/whisper-live_${MYPID}.wav.srt"
    temp_trans_srt="/tmp/whisper-live_${MYPID}.wav.${TRANS_LANGUAGE}.srt"

    if [[ "$skip_transcription" == false ]]; then
        echo ""
        echo "-> Step 1: Converting audio to WAV format..."
        echo ""
        ffmpeg -i "${URL}" -y -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper-live_${MYPID}.wav
        err=$?

        if [ $err -eq 0 ]; then
            echo ""
            echo "-> Step 2: Running Whisper AI Transcription/Translation..."
            echo ""
            echo "----------------------------------------------------"
            # This part remains identical to your original logic.
            if [[ "$WHISPER_EXECUTABLE" == "./build/bin/whisper-cli" ]] || [[ "$WHISPER_EXECUTABLE" == "./main" ]] || [[ "$WHISPER_EXECUTABLE" == "whisper-cpp" ]]; then
                "$WHISPER_EXECUTABLE" -l ${LANGUAGE} ${TRANSLATE} -t 4 -m ./models/ggml-${MODEL}.bin -f /tmp/whisper-live_${MYPID}.wav -osrt 2> /tmp/whisper-live_${MYPID}-err.err
                err=$?
            elif [[ "$WHISPER_EXECUTABLE" == "pwcpp" ]]; then
                if [[ "$TRANSLATE" == "--translate" ]]; then
                    pwcpp --language ${LANGUAGE} --translate translate --n_threads 4 -m ./models/ggml-${MODEL}.bin -osrt /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}-err.err
                    err=$?
                else
                    pwcpp --language ${LANGUAGE} --n_threads 4 -m ./models/ggml-${MODEL}.bin -osrt /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}-err.err
                    err=$?
                fi
            elif [[ "$WHISPER_EXECUTABLE" == "whisper" ]]; then
                if [[ "$TRANSLATE" == "--translate" ]]; then
                    whisper --temperature 0 --beam_size 8 --best_of 4 --initial_prompt "" --threads 4 --model ${MODEL} --task translate --model_dir ./models --output_format srt --output_dir /tmp /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}-err.err
                    err=$?
                else
                    whisper_lang_opt=""
                    if [[ "$LANGUAGE" != "auto" ]]; then
                        whisper_lang_opt="--language ${LANGUAGE}"
                    fi
                    whisper --temperature 0 --beam_size 8 --best_of 4 --initial_prompt "" ${whisper_lang_opt} --threads 4 --model ${MODEL} --model_dir ./models --output_format srt --output_dir /tmp /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}-err.err
                    err=$?
                fi
                mv /tmp/whisper-live_${MYPID}.srt "$temp_whisper_srt"
            fi
        fi

        # The source for the next step is the newly generated temporary file.
        source_srt_file="$temp_whisper_srt"
    else
        echo ""
        echo "-> Skipping Steps 1 & 2 as requested."
    fi

    # Perform online translation if requested and no previous errors occurred
    if [[ $TRANS == "trans" ]] && [[ $err -eq 0 ]]; then
        echo ""
        echo "----------------------------------------------------"
        echo "-> Step 3: Starting Online Translation to '${TRANS_LANGUAGE}'..."
        echo "   (Using source: ${source_srt_file})"
        echo "----------------------------------------------------"
        echo ""
        trans -b :${TRANS_LANGUAGE} -i "$source_srt_file" | tee "$temp_trans_srt" 2>/dev/null
        echo ""
        err=$?
    fi

    # --- Final File Saving Logic ---

    # Helper function to manage saving/overwriting files for the online translation
    save_online_translation_file() {
        local source_file="$1"
        local dest_file="$2"
        local file_desc="$3"
        local overwrite_response="y"

        if [ -e "$dest_file" ]; then
            echo ""
            echo "ATTENTION: The final translated subtitle file already exists."
            echo "  - File: $dest_file"
            echo "  - Type: $file_desc"
            echo ""
            read -p "Do you want to overwrite it? [y/n]: " response

            overwrite_response=$(echo "$response" | tr '[:upper:]' '[:lower:]' | xargs)
        fi

        case "$overwrite_response" in
            y|yes)
                echo ""
                echo "-> Saving $file_desc to: $dest_file"
                mv "$source_file" "$dest_file"
                if [ $? -ne 0 ]; then
                    echo ""
                    echo "${ICON_ERROR} Failed to move file to $dest_file. Temp file is at $source_file ${ICON_ERROR}"
                    err=1 # Set global error state for a real failure
                fi
                ;;
            n|no)
                echo ""
                echo "${ICON_WARN} User chose not to overwrite. The temporary file is available at: '$source_file' ${ICON_WARN}"
                err=2 # Set state to indicate user-aborted save
                ;;
            *)
                echo ""
                echo "${ICON_ERROR} Invalid response. The temporary file is available at '$source_file' ${ICON_ERROR}"
                err=1 # Invalid input is a failure
                ;;
        esac
    }

    if [ $err -eq 0 ]; then
        echo ""
        echo "----------------------------------------------------"
        echo "-> Finalizing Files..."
        echo "----------------------------------------------------"

        # 1. Save the Whisper AI subtitle file if it was newly generated. No more questions here.
        if [[ "$skip_transcription" == false ]]; then
            echo ""
            echo "-> Saving new Whisper AI subtitle to: $whisper_dest_file"
            mv "$temp_whisper_srt" "$whisper_dest_file"
            if [ $? -ne 0 ]; then
                echo ""
                echo "${ICON_ERROR} Failed to move file to $whisper_dest_file. Temp file is at $temp_whisper_srt ${ICON_ERROR}"
                err=1
            fi
        else
            echo ""
             echo "-> Whisper AI subtitle file was not re-generated, so no new version to save."
        fi

        # 2. Save the online translated file (if generated), asking for confirmation if needed.
        # This check is important to only run saving logic if the primary steps were ok.
        if [[ $err -eq 0 ]] && [[ $TRANS == "trans" ]] && [[ -f "$temp_trans_srt" ]]; then
            trans_dest_file="${url_no_ext}.${TRANS_LANGUAGE}.srt"
            trans_file_description="Online Translated Subtitle (${TRANS_LANGUAGE})"
            save_online_translation_file "$temp_trans_srt" "$trans_dest_file" "$trans_file_description"
        fi
    fi

    # --- Final Status ---
    if [ $err -eq 0 ]; then
        echo ""
        echo "${ICON_OK} Subtitles generation process completed successfully! ${ICON_OK}"
        echo ""
        exit 0
    elif [ $err -eq 2 ]; then
        echo ""
        echo " ${ICON_WARN} Operation finished, but final file was not saved as per user request. ${ICON_WARN}"
        echo ""
        exit 0 # Exit cleanly as it was not a script failure
    else
        echo ""
        echo "${ICON_ERROR} An error occurred during the subtitle generation process. ${ICON_ERROR}"
        echo ""
        pkill -f "^ffmpeg.*${MYPID}.*$"
        pkill -f "^${WHISPER_EXECUTABLE}.*${MYPID}.*$"
        pkill -f "^trans.*${MYPID}.*$"
        exit 1
    fi

fi


# --- Timeshift Logic ---

# Set up signal handling to gracefully exit on interrupt.
RUNNING=1
trap "RUNNING=0" SIGINT SIGTERM

# Timeshift with remote stream and VLC.
if [[ $TIMESHIFT == "timeshift" ]] && [[ $LOCAL_FILE -eq 0 ]]; then
    printf "[+] Timeshift active: '$SEGMENTS' segments of '$SEGMENT_TIME' minutes and a synchronization of '$SYNC' seconds.\n\n"

    SEGMENT_TIME=$((SEGMENT_TIME * 60))

    case $URL in
        pulse )
             filename_base="whisper-live_${MYPID}_buf%03d"
             # The dynamic timestamp is handled directly by the ffmpeg filter
             filter_complex="[0:a]showspectrum=s=854x480:mode=separate:color=intensity:legend=disabled:fps=25,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PID\: ${MYPID} | %{pts\:gmtime\:$(date +%s)\:%Y-%m-%d %H\\\\\:%M\\\\\:%S}':fontcolor=white:x=10:y=10"

             ffmpeg -loglevel quiet -y \
             -f pulse -i "$AUDIO_INDEX" \
             -filter_complex "$filter_complex" \
             -c:v mjpeg -q:v 2 -c:a pcm_s16le \
             -threads 2 \
             -f segment \
             -segment_time $SEGMENT_TIME \
             -reset_timestamps 1 \
             -segment_format avi \
             /tmp/${filename_base}.avi &
             FFMPEG_PID=$!
             ;;
         avfoundation )
             filename_base="whisper-live_${MYPID}_buf%03d"
             # The dynamic timestamp is handled directly by the ffmpeg filter
             filter_complex="[0:a]showspectrum=s=854x480:mode=separate:color=intensity:legend=disabled:fps=25,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='PID\: ${MYPID} | %{pts\:gmtime\:$(date +%s)\:%Y-%m-%d %H\\\\\:%M\\\\\:%S}':fontcolor=white:x=10:y=10"

             ffmpeg -loglevel quiet -y \
             -f avfoundation -i :"${AUDIO_INDEX}" \
             -filter_complex "$filter_complex" \
             -c:v mjpeg -q:v 2 -c:a pcm_s16le \
             -threads 2 \
             -f segment \
             -segment_time $SEGMENT_TIME \
             -reset_timestamps 1 \
             -segment_format avi \
             /tmp/${filename_base}.avi &
             FFMPEG_PID=$!
             ;;
        *youtube* | *youtu.be* )
            if ! command -v yt-dlp &>/dev/null; then
                echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                exit 1
            fi
            ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f b -g $URL) -bufsize 44M -acodec ${FMT} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
            FFMPEG_PID=$!
            ;;
        * )
            if [[ "$STREAMLINK_FORCE" = "streamlink" || "$URL" = *twitch* ]]; then
                if ! command -v streamlink >/dev/null 2>&1; then
                    echo "streamlink is required (https://streamlink.github.io)"
                    exit 1
                fi
                streamlink $URL best -O 2>/dev/null | ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i - -bufsize 44M -acodec ${FMT} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                FFMPEG_PID=$!
            elif [[ "$YTDLP_FORCE" = "yt-dlp" ]]; then
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f b -g $URL) -bufsize 44M -acodec ${FMT} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                FFMPEG_PID=$!
            else
                if [[ $QUALITY == "lower" ]]; then
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $URL -bufsize 44M -map_metadata 0 -map 0:v:0? -map 0:v:1? -map 0:v:2? -map 0:v:3? -map 0:v:4? -map 0:v:5? -map 0:v:6? -map 0:v:7? -map 0:v:8? -map 0:v:9? -map 0:a:0? -map 0:a:1? -map 0:a:2? -map 0:a:3? -map 0:a:4? -map 0:a:5? -map 0:a:6? -map 0:a:7? -map 0:a:8? -map 0:a:9? -acodec ${FMT} -vcodec libx264 -threads 2 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                    FFMPEG_PID=$!
                else
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $URL -bufsize 44M -map_metadata 0 -map 0:v:9? -map 0:v:8? -map 0:v:7? -map 0:v:6? -map 0:v:5? -map 0:v:4? -map 0:v:3? -map 0:v:2? -map 0:v:1? -map 0:v:0? -map 0:a:9? -map 0:a:8? -map 0:a:7? -map 0:a:6? -map 0:a:5? -map 0:a:4? -map 0:a:3? -map 0:a:2? -map 0:a:1? -map 0:a:0? -acodec ${FMT} -vcodec libx264 -threads 2 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                    FFMPEG_PID=$!
                fi
            fi
            ;;
    esac


    # build m3u playlist
    arg='#EXTM3U'
		x=0
		while [ $x -lt $SEGMENTS ]; do
			arg="$arg"'\n/tmp/whisper-live_'"${MYPID}"'_'"$x"'.avi'
			x=$((x+1))
		done
		echo -e $arg > /tmp/playlist_whisper-live_${MYPID}.m3u

    # Define the maximum time to wait in seconds
    max_wait_time=20

    # Define the file path pattern
    file_path="/tmp/whisper-live_${MYPID}_buf000.avi"

    # Get the start time
    start_time=$(date +%s)

    # Loop until the file exists or the maximum wait time is reached
    while [ ! -f "$file_path" ]; do
        # Get the current time
        current_time=$(date +%s)

        # Calculate the elapsed time
        elapsed_time=$((current_time - start_time))

        # Check if the maximum wait time is exceeded
        if [ "$elapsed_time" -ge "$max_wait_time" ]; then
            echo "Maximum wait time exceeded."
            break
        fi

        # Wait for a short interval before checking again
        sleep 0.1
    done

    # Check if the file exists after the loop
    if [ -f "$file_path" ]; then
        # launch player
        sleep 10
        ln -f -s /tmp/whisper-live_${MYPID}_buf000.avi /tmp/whisper-live_${MYPID}_0.avi # symlink first buffer at start
    else
        printf "${ICON_ERROR} Error: ffmpeg failed to capture the stream\n"
        exit 1
    fi

    if [[ "$PLAYER_ONLY" == "" ]]; then
        printf "Buffering audio. Please wait...\n\n"
    fi

    if ! ps -p $FFMPEG_PID > /dev/null; then
        printf "${ICON_ERROR} Error: ffmpeg failed to capture the stream\n"
        exit 1
    fi

    sleep $(($STEP_S+$SYNC))
    if [[ $MPV_OPTIONS == "true" ]]; then
        vlc -I http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
    else
        vlc --extraintf=http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
    fi

    if [ $? -ne 0 ]; then
        printf "${ICON_ERROR} Error: The player could not play the stream. Please check your input or try again later\n"
        exit 1
    fi

   VLC_PID=$(ps -ax -o etime,pid,command -c | grep -i '[Vv][Ll][Cc]' | tail -n 1 | awk '{print $2}') # check pidof vlc
    if [ -z "$VLC_PID" ]; then
        VLC_PID=0
        printf "${ICON_ERROR} Error: The player could not be executed.\n"
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

    if [[ "$PLAYER_ONLY" != "" ]]; then
      echo "${ICON_OK} -> Now recording video buffer /tmp/whisper-live_${MYPID}_$n.avi"
    fi

    while [ $RUNNING -eq 1 ]; do

  		if [ -f /tmp/whisper-live_${MYPID}_buf$nbuf.avi ]; then # check split
  			mv -f /tmp/whisper-live_${MYPID}_buf$abuf.avi /tmp/whisper-live_${MYPID}_$n.avi
  			if [ $n -eq $((SEGMENTS-1)) ]; then # restart buffer value when last buffer reached
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
  			ln -f -s /tmp/whisper-live_${MYPID}_buf$abuf.avi /tmp/whisper-live_${MYPID}_$n.avi
        if [ "$PLAYER_ONLY" != "" ]; then
          echo "${ICON_OK} -> Now recording video buffer /tmp/whisper-live_${MYPID}_$n.avi"
        fi
  		fi

      while [ $SECONDS -lt $((($i+1)*$STEP_S)) ]; do
          sleep 0.1
      done

      vlc_check

      curl_output=$(curl -s -N -u :playlist4whisper http://127.0.0.1:${MYPORT}/requests/status.xml)

            FILEPLAY=$(echo "$curl_output" | sed -n 's/.*<info name='"'"'filename'"'"'>\([^<]*\).*$/\1/p')

            POSITION=$(echo "$curl_output" | sed -n 's/.*<time>\([^<]*\).*$/\1/p')


      if [[ "$POSITION" =~ ^[0-9]+$ ]] && [[ "$PLAYER_ONLY" == "" ]]; then

          if [ $POSITION -ge 2 ]; then

              if [ "$FILEPLAY" != "$FILEPLAYED" ]; then
                  FILEPLAYED="$FILEPLAY"
                  TIMEPLAYED=$(date -r /tmp/"$FILEPLAY" +%s)
                  if [ $(echo "$POSITION < $STEP_S" | bc -l) -eq 1 ]; then
                      in=0
                  else
                      in=2
                      ((SECONDS=SECONDS+STEP_S))
                  fi
                  tin=0
              elif [ "$(date -r /tmp/"$FILEPLAY" +%s)" -gt "$((TIMEPLAYED + SEGMENT_TIME + 6))" ] && [ $tin -eq 0 ]; then
                  tin=1
              fi

              if [ $tin -eq 0 ]; then
                  err=1

                  segment_played=$(echo ffprobe -i /tmp/"$FILEPLAY" -show_format -v quiet | sed -n 's/duration=//p')

                  if ! [[ "$segment_played" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                      segment_played="$SEGMENT_TIME"
                  fi

                  rest=$(echo "$segment_played - $POSITION - $SYNC" | bc -l)
                  tryed=0
                  if [ $(echo "$rest < $STEP_S" | bc -l) -eq 1 ] && [ $(echo "$rest > 0" | bc -l) -eq 1 ]; then

                      while [ $err -ne 0 ] && [ $tryed -lt 10 ]; do
                          sleep 0.4
                          ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $SYNC - 0.8" | bc -l) -t $(echo "$rest + 0.8" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
                          ((tryed=tryed+1))
                          err=$(cat /tmp/whisper-live_${MYPID}.err | wc -l)
                      done
                      in=3

                  else

                      while [ $err -ne 0 ] && [ $tryed -lt 5 ]; do
                          if [ $in -eq 0 ]; then
                              if [ $(echo "$((POSITION)) < $(((STEP_S+SYNC)*2))" | bc -l) -eq 1 ]; then
                                  ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -to $(echo "$POSITION + $SYNC - 0.8" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
                                  in=1
                              else
                                  in=1
                              fi
                          else
                              ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $SYNC - 0.8" | bc -l) -t $(echo "$STEP_S + 0.0" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
                              in=2
                          fi
                          err=$(cat /tmp/whisper-live_${MYPID}.err | wc -l)
                          ((tryed=tryed+1))
                          sleep 0.4
                      done

                      if [ $in -eq 1 ]; then
                          ((SECONDS=SECONDS+STEP_S))
                      fi

                  fi

                  # Call the function to process the audio chunk
                  process_audio_chunk "/tmp/whisper-live_${MYPID}.wav"

              elif [ $tin -eq 1 ]; then
                  echo
                  echo "${ICON_WARN} Timeshift window reached. Video $FILEPLAY overwritten. You can still watch it, but without transcriptions. Next files may be affected. Adjust Timeshift for more segments/longer times ${ICON_WARN}"
                  echo
                  tin=2
              fi

          else
            in=0
          fi
      fi
      ((i=i+1))

    done

    pkill -f "^ffmpeg.*${MYPID}.*$"
    pkill -f "^${WHISPER_EXECUTABLE}.*${MYPID}.*$"
    # Remove the used port from the temporary file
    if [ -f "$TEMP_FILE" ]; then
        awk -v myport="$MYPORT" '$0 !~ myport' "$TEMP_FILE" > temp_file.tmp && mv temp_file.tmp "$TEMP_FILE"
    fi

elif [[ $TIMESHIFT == "timeshift" ]] && [[ $LOCAL_FILE -eq 1 ]]; then # local video file with vlc

    if [[ "$PLAYER_ONLY" == "" ]]; then
        arg="#EXTM3U\n${URL}"
        echo -e $arg > /tmp/playlist_whisper-live_${MYPID}.m3u

        if [[ $MPV_OPTIONS == "true" ]]; then
            vlc -I http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
        else
            vlc --extraintf=http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
        fi

        if [ $? -ne 0 ]; then
            printf "${ICON_ERROR} Error: The player could not play the file. Please check your input.\n"
            exit 1
        fi

        VLC_PID=$(ps -ax -o etime,pid,command -c | grep -i '[Vv][Ll][Cc]' | tail -n 1 | awk '{print $2}') # check pidof vlc
        if [ -z "$VLC_PID" ]; then
            VLC_PID=0
            printf "${ICON_ERROR} Error: The player could not be executed.\n"
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
        while [ $RUNNING -eq 1 ]; do


            while [ $SECONDS -lt $((($i+1)*$STEP_S)) ]; do
                sleep 0.1
            done

            vlc_check

            curl_output=$(curl -s -N -u :playlist4whisper http://127.0.0.1:${MYPORT}/requests/status.xml)

                  FILEPLAY=$(echo "$curl_output" | sed -n 's/.*<info name='"'"'filename'"'"'>\([^<]*\).*$/\1/p')

                  POSITION=$(echo "$curl_output" | sed -n 's/.*<time>\([^<]*\).*$/\1/p')


            if [[ "$POSITION" =~ ^[0-9]+$ ]]; then

                if [ $POSITION -ge 2 ]; then

                    if [ "$FILEPLAY" != "$FILEPLAYED" ]; then
                        FILEPLAYED="$FILEPLAY"
                        if [ $(echo "$POSITION < $STEP_S" | bc -l) -eq 1 ]; then
                            in=0
                        else
                            in=2
                            ((SECONDS=SECONDS+STEP_S))
                        fi
                    fi

                    err=1

                    segment_played=$(echo ffprobe -i "${URL}" -show_format -v quiet | sed -n 's/duration=//p')

                    if ! [[ "$segment_played" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then

                        rest=$(echo "$segment_played - $POSITION - $SYNC" | bc -l)
                        tryed=0
                        if [ $(echo "$rest < $STEP_S" | bc -l) -eq 1 ] && [ $(echo "$rest > 0" | bc -l) -eq 1 ]; then

                            while [ $err -ne 0 ] && [ $tryed -lt 10 ]; do
                                sleep 0.4
                                ffmpeg -loglevel quiet -v error -noaccurate_seek -i "${URL}" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $SYNC - 1" | bc -l) -t $(echo "$rest + 0.5" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
                                ((tryed=tryed+1))
                                err=$(cat /tmp/whisper-live_${MYPID}.err | wc -l)
                            done
                            in=3

                        else

                            while [ $err -ne 0 ] && [ $tryed -lt 5 ]; do
                                if [ $in -eq 0 ]; then
                                    if [ $(echo "$((POSITION)) < $(((STEP_S+SYNC)*2))" | bc -l) -eq 1 ]; then
                                        ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/"$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -to $(echo "$POSITION + $SYNC - 0.8" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
                                        in=1
                                    else
                                        in=1
                                    fi
                                else
                                    ffmpeg -loglevel quiet -v error -noaccurate_seek -i "${URL}" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$POSITION + $SYNC - 1" | bc -l) -t $(echo "$STEP_S + 0.0" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
                                    in=2
                                fi
                                err=$(cat /tmp/whisper-live_${MYPID}.err | wc -l)
                                ((tryed=tryed+1))
                                sleep 0.4
                            done

                            if [ $in -eq 1 ]; then
                                ((SECONDS=SECONDS+STEP_S))
                            fi

                        fi

                        # Call the function to process the audio chunk
                        process_audio_chunk "/tmp/whisper-live_${MYPID}.wav"

                    fi
                else
                  in=0
                fi
            fi
            ((i=i+1))

        done

    pkill -f "^ffmpeg.*${MYPID}.*$"
    pkill -f "^${WHISPER_EXECUTABLE}.*${MYPID}.*$"
    # Remove the used port from the temporary file
    if [ -f "$TEMP_FILE" ]; then
        awk -v myport="$MYPORT" '$0 !~ myport' "$TEMP_FILE" > temp_file.tmp && mv temp_file.tmp "$TEMP_FILE"
    fi

    else

      $MPV_OPTIONS "${URL}" &>/dev/null &

    fi

elif [[ "$PLAYER_ONLY" == "" ]]; then # No timeshift

    if [[ $URL == "pulse" ]]; then
          ffmpeg -loglevel quiet -y -f pulse -i "$AUDIO_INDEX" /tmp/whisper-live_${MYPID}.${FMT} &
          FFMPEG_PID=$!
          $MPV_OPTIONS /tmp/whisper-live_${MYPID}.${FMT} &>/dev/null &

    elif [[ $URL == "avfoundation" ]]; then
          ffmpeg -loglevel quiet -y -f avfoundation -i :"${AUDIO_INDEX}" /tmp/whisper-live_${MYPID}.${FMT} &
          FFMPEG_PID=$!
          $MPV_OPTIONS /tmp/whisper-live_${MYPID}.${FMT} &>/dev/null &

    elif [[ $LOCAL_FILE -eq 1 ]]; then
          ffmpeg -loglevel quiet -y -probesize 32 -i "${URL}" -bufsize 44M -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} &
          FFMPEG_PID=$!
          $MPV_OPTIONS "${URL}" &>/dev/null &

    elif [[ $QUALITY == "upper" ]]; then
        case $URL in
            *youtube* | *youtu.be* )
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f b -g "$URL")" \
                    -bufsize 44M -acodec ${FMT} -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} \
                    -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${MYPORT} &
                FFMPEG_PID=$!
                ;;
            * )
                if [[ "$STREAMLINK_FORCE" = "streamlink" || "$URL" = *twitch* ]]; then
                    if ! command -v streamlink >/dev/null 2>&1; then
                        echo "streamlink is required (https://streamlink.github.io)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -re -i "$(streamlink $URL best --stream-url)" \
                        -bufsize 44M -acodec ${FMT} -map 0:a:0  /tmp/whisper-live_${MYPID}.${FMT} \
                        -bufsize 4M -acodec ${FMT} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${MYPORT} &
                    FFMPEG_PID=$!
                elif [[ "$YTDLP_FORCE" = "yt-dlp" ]]; then
                    if ! command -v yt-dlp &>/dev/null; then
                        echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f b -g "$URL")" \
                        -bufsize 44M -acodec ${FMT} -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} \
                        -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${MYPORT} &
                    FFMPEG_PID=$!
                else
                    ffmpeg -loglevel quiet -y -probesize 32 -i $URL \
                        -bufsize 44M -acodec ${FMT} -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} \
                        -bufsize 4M -map_metadata 0 -map 0:v:9? -map 0:v:8? -map 0:v:7? -map 0:v:6? -map 0:v:5? -map 0:v:4? -map 0:v:3? -map 0:v:2? -map 0:v:1? -map 0:v:0? -map 0:a:0 -acodec ${FMT} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${MYPORT} &
                    FFMPEG_PID=$!
                fi
                ;;
        esac
        # Define the maximum time to wait in seconds
        max_wait_time=20

        # Define the file path pattern
        file_path="/tmp/whisper-live_${MYPID}.${FMT}"

        # Get the start time
        start_time=$(date +%s)

        # Loop until the file exists or the maximum wait time is reached
        while [ ! -f "$file_path" ]; do
            # Get the current time
            current_time=$(date +%s)

            # Calculate the elapsed time
            elapsed_time=$((current_time - start_time))

            # Check if the maximum wait time is exceeded
            if [ "$elapsed_time" -ge "$max_wait_time" ]; then
                echo "Maximum wait time exceeded."
                break
            fi

            # Wait for a short interval before checking again
            sleep 0.1
        done

        # Check if the file exists after the loop
        if [ -f "$file_path" ]; then
            # launch player
            nohup $MPV_OPTIONS udp://127.0.0.1:${MYPORT} >/dev/null 2>&1 &
        else
            printf "${ICON_ERROR} Error: ffmpeg failed to capture the stream\n"
            exit 1
        fi

    elif [[ $QUALITY == "lower" ]]; then
        case $URL in
            *youtube* | *youtu.be* )
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'worst' -g "$URL")" \
                    -bufsize 44M -acodec ${FMT} -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} \
                    -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${MYPORT} &
                FFMPEG_PID=$!
                ;;
            * )
                if [[ "$STREAMLINK_FORCE" = "streamlink" || "$URL" = *twitch* ]]; then
                    if ! command -v streamlink >/dev/null 2>&1; then
                        echo "streamlink is required (https://streamlink.github.io)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -y -probesize 32 -re -i "$(streamlink $URL worst --stream-url)" \
                        -bufsize 44M -acodec ${FMT} -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} \
                        -bufsize 4M -map_metadata 0 -map 0:v:0 -map 0:a:0 -acodec ${FMT} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${MYPORT} &
                    FFMPEG_PID=$!
                elif [[ "$YTDLP_FORCE" = "yt-dlp" ]]; then
                    if ! command -v yt-dlp &>/dev/null; then
                        echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -y -probesize 32 -i "$(yt-dlp -i -f 'worst' -g "$URL")" \
                        -bufsize 44M -acodec ${FMT} -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} \
                        -bufsize 4M -map 0:v:0 -map 0:a -c:v copy -c:a copy -f mpegts udp://127.0.0.1:${MYPORT} &
                    FFMPEG_PID=$!
                else
                    ffmpeg -loglevel quiet -y -probesize 32 -i $URL \
                        -bufsize 44M -acodec ${FMT} -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} \
                        -bufsize 4M -map_metadata 0 -map 0:v:0? -map 0:v:1? -map 0:v:2? -map 0:v:3? -map 0:v:4? -map 0:v:5? -map 0:v:6? -map 0:v:7? -map 0:v:8? -map 0:v:9? -map 0:a:0 -acodec ${FMT} -threads 2 -vcodec libx264 -preset ultrafast -movflags +faststart -vsync 2 -reset_timestamps 1 -f mpegts udp://127.0.0.1:${MYPORT} &
                    FFMPEG_PID=$!
                fi
                ;;
        esac
        # Define the maximum time to wait in seconds
        max_wait_time=20

        # Define the file path pattern
        file_path="/tmp/whisper-live_${MYPID}.${FMT}"

        # Get the start time
        start_time=$(date +%s)

        # Loop until the file exists or the maximum wait time is reached
        while [ ! -f "$file_path" ]; do
            # Get the current time
            current_time=$(date +%s)

            # Calculate the elapsed time
            elapsed_time=$((current_time - start_time))

            # Check if the maximum wait time is exceeded
            if [ "$elapsed_time" -ge "$max_wait_time" ]; then
                echo "Maximum wait time exceeded."
                break
            fi

            # Wait for a short interval before checking again
            sleep 0.1
        done

        # Check if the file exists after the loop
        if [ -f "$file_path" ]; then
            # launch player
            nohup $MPV_OPTIONS udp://127.0.0.1:${MYPORT} >/dev/null 2>&1 &
        else
            printf "${ICON_ERROR} Error: ffmpeg failed to capture the stream\n"
            exit 1
        fi

    elif [[ $QUALITY == "raw" ]]; then
        case $URL in
            *youtube* | *youtu.be* )
                if ! command -v yt-dlp &>/dev/null; then
                    echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                    exit 1
                fi
                ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f 'worst' -g $URL) -bufsize 44M -acodec ${FMT} -threads 2 -map 0:a:0 -vsync 2 -reset_timestamps 1 /tmp/whisper-live_${MYPID}.${FMT} &
                FFMPEG_PID=$!
                ;;
            * )
                if [[ "$STREAMLINK_FORCE" = "streamlink" || "$URL" = *twitch* ]]; then
                    if ! command -v streamlink >/dev/null 2>&1; then
                        echo "streamlink is required (https://streamlink.github.io)"
                        exit 1
                    fi
                    streamlink $URL worst -O 2>/dev/null | ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i - -bufsize 44M -acodec ${FMT} -threads 2 -map 0:a:0 -vsync 2 -reset_timestamps 1 /tmp/whisper-live_${MYPID}.${FMT} &
                    FFMPEG_PID=$!
                elif [[ "$YTDLP_FORCE" = "yt-dlp" ]]; then
                    if ! command -v yt-dlp &>/dev/null; then
                        echo "yt-dlp is required (https://github.com/yt-dlp/yt-dlp)"
                        exit 1
                    fi
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f 'worst' -g $URL) -bufsize 44M -acodec ${FMT} -threads 2 -map 0:a:0 -vsync 2 -reset_timestamps 1 /tmp/whisper-live_${MYPID}.${FMT} &
                    FFMPEG_PID=$!
                else
                    ffmpeg -loglevel quiet -y -probesize 32 -i $URL -bufsize 44M -map 0:a:0 /tmp/whisper-live_${MYPID}.${FMT} &
                    FFMPEG_PID=$!
                fi
                ;;
        esac
        # Define the maximum time to wait in seconds
       max_wait_time=20

        # Define the file path pattern
        file_path="/tmp/whisper-live_${MYPID}.${FMT}"

        # Get the start time
        start_time=$(date +%s)

        # Loop until the file exists or the maximum wait time is reached
        while [ ! -f "$file_path" ]; do
            # Get the current time
            current_time=$(date +%s)

            # Calculate the elapsed time
            elapsed_time=$((current_time - start_time))

            # Check if the maximum wait time is exceeded
            if [ "$elapsed_time" -ge "$max_wait_time" ]; then
                echo "Maximum wait time exceeded."
                break
            fi

            # Wait for a short interval before checking again
            sleep 0.1
        done

        # Check if the file exists after the loop
        if [ -f "$file_path" ]; then
            # launch player
            $MPV_OPTIONS $URL &>/dev/null &
        else
            printf "${ICON_ERROR} Error: ffmpeg failed to capture the stream\n"
            exit 1
        fi
    fi

    if [ $? -ne 0 ]; then
        printf "${ICON_ERROR} Error: The player could not play the stream. Please check your input or try again later\n"
        exit 1
    fi

    printf "Buffering audio. Please wait...\n\n"
    sleep $(($STEP_S))

    # do not stop script on error
    set +e

    i=0
    SECONDS=0
    acceleration_factor="1.5"

    while [ $RUNNING -eq 1 ]; do
        # extract the next piece from the main file above and transcode to wav. -ss sets start time, -0.x seconds adjust
        err=1
        tryed=0
        while [ $err -ne 0 ] && [ $tryed -lt $STEP_S ]; do
            if [ $i -gt 0 ]; then
                ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live_${MYPID}.${FMT} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$i * $STEP_S - 1" | bc -l) -t $(echo "$STEP_S" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
            else
                ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live_${MYPID}.${FMT} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -to $(echo "$STEP_S - 1" | bc -l) /tmp/whisper-live_${MYPID}.wav 2> /tmp/whisper-live_${MYPID}.err
            fi
            err=$(cat /tmp/whisper-live_${MYPID}.err | wc -l)
            ((tryed=tryed+1))
            sleep 0.5
        done

        # Call the function to process the audio chunk
        process_audio_chunk "/tmp/whisper-live_${MYPID}.wav"

        while [ $SECONDS -lt $((($i+1)*$STEP_S)) ]; do
            sleep 0.1
        done

        ((i=i+1))

    done

    pkill -f "^ffmpeg.*${MYPID}.*$"
    pkill -f "^${WHISPER_EXECUTABLE}.*${MYPID}.*$"
    # Remove the used port from the temporary file
    if [ -f "$TEMP_FILE" ]; then
        awk -v myport="$MYPORT" '$0 !~ myport' "$TEMP_FILE" > temp_file.tmp && mv temp_file.tmp "$TEMP_FILE"
    fi

else
    if [[ $LOCAL_FILE -eq 0 ]] ; then
        $MPV_OPTIONS $URL &>/dev/null &
    else
        $MPV_OPTIONS "${URL}" &>/dev/null &
    fi
fi
