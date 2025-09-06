#!/bin/bash

# livestream_video.sh v. 4.22 - Plays audio/video files or video streams, transcribing the audio using AI.
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
TRANS_ENGINE="google"   # Default engine for translate-shell ("google", "bing", "yandex")
LOCAL_FILE=0            # Flag for local file (0 = false, 1 = true)
STEP_S=9                # Step size in seconds for audio processing
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
SYNC=6                  # Transcription/video sync time (seconds)
SPEAK=""                # Enable Text-to-Speech
TRANS=""                # Enable online translation
OUTPUT_TEXT="both"      # Output text during translation (original, translation, both, none)
TRANS_LANGUAGE="en"     # Default translation language
GEMINI_TRANS_MODEL=""   # Use Google's Gemini for translation with the specified model
GEMINI_CONTEXT_LEVEL=2  # Context level for Gemini translation (0-3)
SUBTITLES=""            # Generate subtitles flag
AUDIO_SOURCE=""         # Audio source (pulse:index or avfoundation:index)
AUDIO_INDEX="0"         # Default audio index
WHISPER_EXECUTABLE=""   # Path to the Whisper executable

#GEMINI_API_KEY=""      # Optional variable for the Gemni API Key

# Context window for the final translated text
declare -a translated_context_window=()

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

# Available Gemini models for translation
AVAILABLE_GEMINI_MODELS=(
    "gemini-2.5-pro"
    "gemini-2.5-flash"
    "gemini-2.5-flash-lite"
    "gemma-3-27b-it"
    "gemma-3-12b-it"
    "gemma-3-4b-it"
)

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
Usage: $0 stream_url [or /path/media_file or pulse:index or avfoundation:index] [--step step_s] [--model model] [--language language] [--executable exe_path] [--translate] [--subtitles] [--timeshift] [--segments segments (2<n<99)] [--segment_time minutes (1<minutes<99)] [--sync seconds (0 <= seconds <= (Step - 3))] --trans trans_language [output_text speak] [--gemini-trans [gemini_model]] [--gemini-level [0-3]] [player player_options]

Example:
  $0 https://cbsn-det.cbsnstream.cbsnews.com/out/v1/169f5c001bc74fa7a179b19c20fea069/master.m3u8 --step 8 --model base --language auto --translate --timeshift --segments 4 --segment_time 10 --trans es both speak
  $0 ./my_video.mp4 --subtitles --trans es --gemini-trans
  $0 ./my_video.mp4 --subtitles --trans fr --gemini-trans gemini-2.5-pro --gemini-level 3

Help:

  livestream_video.sh v. 4.22 - plays audio/video files or video streams, transcribing the audio using AI technology.
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

  --trans         Enables online translation. Must be followed by a language code.
                  Default engine is translate-shell. Use --gemini-trans to switch to the Gemini API.
    trans_language: Translation language (e.g., es, fr, de).
    output_text: (Optional) Output text: original, translation, both, none.
    speak: (Optional) Online Text-to-Speech.

  --gemini-trans  Use the Google Gemini API for higher quality translation (replaces translate-shell).
                  Requires the '--trans' flag to be set with a language.
                  Requires the 'GEMINI_API_KEY' variable to be set.
    gemini_model: (Optional) Specify a Gemini model. Defaults to 'gemini-2.5-flash-lite'.
                  Available models: ${AVAILABLE_GEMINI_MODELS[@]}

  --gemini-level  Set the context level for Gemini translation (0-3). Default is 2.
                  Level 0: No context, translates literally.
                  Level 1: Minimal context (previous segment).
                  Level 2: Standard context (sliding window of last 2 segments).
                  Level 3: Creative context (allows AI to fix/complete phrases).

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

    # The processing pipe is designed to be robust across whisper.cpp versions
    if [[ "$WHISPER_EXECUTABLE" == "./build/bin/whisper-cli" ]] || [[ "$WHISPER_EXECUTABLE" == "./main" ]] || [[ "$WHISPER_EXECUTABLE" == "whisper-cpp" ]]; then
        "$WHISPER_EXECUTABLE" -l ${LANGUAGE} ${TRANSLATE} -t 4 -m ./models/ggml-${MODEL}.bin -f "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tr '\r' '\n' | grep '^\[' | sed 's/^\[.*\] *//' | paste -s -d ' ' - | tr -d '<>^*_' | tee /tmp/output-whisper-live_${MYPID}.txt >/dev/null
        err=$?
    elif [[ "$WHISPER_EXECUTABLE" == "pwcpp" ]]; then
        if [[ "$TRANSLATE" == "--translate" ]]; then
            pwcpp --language ${LANGUAGE} --translate translate --n_threads 4 -m ./models/ggml-${MODEL}.bin "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tr '\r' '\n' | grep '^\[' | sed 's/^\[.*\] *//' | paste -s -d ' ' - | tr -d '<>^*_' | tee /tmp/output-whisper-live_${MYPID}.txt >/dev/null
            err=$?
        else
            pwcpp --language ${LANGUAGE} --n_threads 4 -m ./models/ggml-${MODEL}.bin "$wav_file" 2> /tmp/whisper-live_${MYPID}-err.err | tr '\r' '\n' | grep '^\[' | sed 's/^\[.*\] *//' | paste -s -d ' ' - | tr -d '<>^*_' | tee /tmp/output-whisper-live_${MYPID}.txt >/dev/null
            err=$?
        fi
    elif [[ "$WHISPER_EXECUTABLE" == "whisper" ]]; then
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

    # --- Translation and Output Logic ---

    # Get the raw transcribed text from whisper.
    local original_text
    original_text=$(< "/tmp/output-whisper-live_${MYPID}.txt")

    # Safety guard: if transcription is empty or too short, do nothing.
    if [[ $(wc -m <<< "$original_text") -lt 3 ]]; then
        return
    fi

    local translated_text=""
    local use_trans_fallback=true
    local fallback_indicator=""

    # Attempt translation with the primary engine (Gemini)
    if [[ -n "$GEMINI_TRANS_MODEL" ]] && [[ -n "$GEMINI_API_KEY" ]]; then
        # --- Gemini Prompt Engineering based on Context Level ---
        local translated_context=""
        local prompt_instructions=""

        case "$GEMINI_CONTEXT_LEVEL" in
            0)
                translated_context=""
                prompt_instructions="You are an expert real-time translator. Your goal is to provide a literal and fluid translation of the 'New source text fragment' into ${TRANS_LANGUAGE}. Your output must be ONLY the new translation."
                ;;
            1)
                if [ "${#translated_context_window[@]}" -gt 0 ]; then
                    translated_context="${translated_context_window[-1]}"
                fi
                prompt_instructions="You are an expert real-time translator. Your goal is to provide a fluid and natural translation of the 'New source text fragment' into ${TRANS_LANGUAGE} that logically continues the 'Translated Context'. Your output must be ONLY the new translation."
                ;;
            3)
                translated_context=$(printf "%s " "${translated_context_window[@]}")
                prompt_instructions="You are an expert real-time translator. Your goal is to provide a fluid and natural translation of the 'New source text fragment' into ${TRANS_LANGUAGE}. Based on the 'Translated Context', you have the creative freedom to rephrase, complete sentences, or fix cut-off words in the 'New source text fragment' to ensure the final output is coherent and flows naturally. Your output must be ONLY the new, improved translation."
                ;;
            *)
                translated_context=$(printf "%s " "${translated_context_window[@]}")
                prompt_instructions="You are an expert real-time translator. Your goal is to provide a fluid and natural translation of the 'New source text fragment' into ${TRANS_LANGUAGE} that logically continues the 'Translated Context'. It is crucial that you translate the full meaning without omitting any information from the original fragment. Your output must be ONLY the new translation."
                ;;
        esac

        local full_prompt="${prompt_instructions}\n\nTranslated Context:\n${translated_context}\n\nNew source text fragment:\n${original_text}"

        local json_payload
        json_payload=$(jq -n \
            --arg prompt_text "$full_prompt" \
            '{
                "contents": [ { "parts": [ { "text": $prompt_text } ] } ],
                "generationConfig": { "temperature": 0.2, "maxOutputTokens": 1024 },
                "safetySettings": [
                    { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
                    { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
                    { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
                    { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" }
                ]
            }')

        # API call
        local api_response_raw
        api_response_raw=$(curl --silent --no-buffer --max-time 2 -X POST \
            -H 'Content-Type: application/json' \
            -d "$json_payload" \
            "https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_TRANS_MODEL}:generateContent?key=$GEMINI_API_KEY")

        if [[ $? -eq 0 ]]; then
            local extracted_translation
            extracted_translation=$(echo "$api_response_raw" | jq -r '.candidates[0].content.parts[0].text // ""' | tr -d '\r\n')

            if [[ -n "$extracted_translation" ]]; then
                translated_text="$extracted_translation"
                use_trans_fallback=false
            fi
        fi
    fi

    # Fallback to the secondary translation engine (trans)
    if [[ "$use_trans_fallback" == true ]]; then
        if [[ $TRANS == "trans" ]]; then
            if [[ -n "$GEMINI_TRANS_MODEL" ]]; then
                fallback_indicator="(*) "
            fi
            translated_text=$(echo "$original_text" | trans -no-warn -b :${TRANS_LANGUAGE} 2>/dev/null)
        fi
    fi

    # --- Display, Context Update, and TTS Logic ---

    # Log the raw, unwrapped original text
    echo "$original_text" >> "/tmp/transcription-whisper-live_${MYPID}.txt"

    # Helper function to print text with smart wrapping.
    # It gets the terminal width on every call to handle window resizing.
    print_wrapped() {
        local text_to_print="$1"
        local terminal_width
        terminal_width=$(tput cols 2>/dev/null || echo 80)
        echo "$text_to_print" | fold -s -w "$terminal_width"
    }

    # Display original text if enabled, using the wrapper
    if [[ $OUTPUT_TEXT == "original" ]] || [[ $OUTPUT_TEXT == "both" ]]; then
         print_wrapped "$original_text"
    fi

    # Display translated text if available and enabled, using the wrapper
    if [[ -n "$translated_text" ]] && ([[ $OUTPUT_TEXT == "translation" ]] || [[ $OUTPUT_TEXT == "both" ]]); then
        if [[ $OUTPUT_TEXT == "both" ]]; then tput rev; fi
        print_wrapped "${fallback_indicator}${translated_text}"
        if [[ $OUTPUT_TEXT == "both" ]]; then tput sgr0; fi

        # Log the raw, unwrapped translated text
        echo "${fallback_indicator}${translated_text}" >> "/tmp/translation-whisper-live_${MYPID}.txt"

        # Sanitize the raw, unwrapped translated text before adding it to the context window
        local clean_translated_text
        clean_translated_text=$(echo "$translated_text" | sed 's/(\([^)]*\))//g; s/\[[^]]*\]//g; s/[$*#]//g')

        # Update the context window ONLY with the cleaned text
        if [[ -n "$clean_translated_text" ]]; then
            translated_context_window+=("$clean_translated_text")
            if [ "${#translated_context_window[@]}" -gt 2 ]; then
                translated_context_window=("${translated_context_window[@]:1}")
            fi
        fi
    fi

    # Handle Text-to-Speech (TTS)
    if [[ $SPEAK == "speak" ]] && [[ -n "$translated_text" ]]; then
        # TTS logic uses the raw, unwrapped text
        echo "$translated_text" | trans -b :${TRANS_LANGUAGE} -download-audio-as /tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3 >/dev/null 2>&1

        local audio_file="/tmp/whisper-live_${MYPID}_$(((i+2)%2)).mp3"
        if [ -f "$audio_file" ]; then
            local duration
            duration=$(ffprobe -i "$audio_file" -show_entries format=duration -v quiet -of csv="p=0")
            if [ -n "$duration" ]; then
                local acceleration_factor="1.5"
                if [[ $(echo "$duration > ($STEP_S - ( $STEP_S / 8 ))" | bc -l) == 1 ]]; then
                    acceleration_factor=$(echo "scale=2; $duration / ($STEP_S - ( $STEP_S / 8 ))" | bc -l)
                fi
                if [[ $(echo "$acceleration_factor < 1.5" | bc -l) == 1 ]]; then
                    acceleration_factor="1.5"
                fi
                local accelerated_audio_file="/tmp/whisper-live_${MYPID}_$(((i+2)%2))_accel.mp3"
                ffmpeg -y -i "$audio_file" -filter:a "atempo=$acceleration_factor" "$accelerated_audio_file" >/dev/null 2>&1
                mpv "$accelerated_audio_file" &>/dev/null &
            fi
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
        --gemini-trans )
            GEMINI_TRANS_MODEL="gemini-2.5-flash-lite" # Set default model

            # Check for an OPTIONAL model name as the next argument
            if [[ -n "$2" ]] && [[ "$2" != --* ]]; then
                shift # Consume optional model argument
                provided_model=$1
                if [[ " ${AVAILABLE_GEMINI_MODELS[*]} " =~ " ${provided_model} " ]]; then
                    GEMINI_TRANS_MODEL=$provided_model
                else
                    echo ""; echo "${ICON_ERROR} Invalid Gemini model: ${provided_model}"; echo "Available models: ${AVAILABLE_GEMINI_MODELS[@]}"; echo ""; usage; exit 1
                fi
            fi
            ;;
        --gemini-level )
            shift
            if [[ "$1" =~ ^[0-3]$ ]]; then
                GEMINI_CONTEXT_LEVEL=$1
            else
                echo ""; echo "${ICON_ERROR} Invalid Gemini level: $1. Must be between 0 and 3."; echo ""; usage; exit 1
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
                        --model | --language | --step | --translate | --subtitles | --playeronly | --timeshift | --segment_time | --segments | --sync | --raw | --upper | --lower | --streamlink | --yt-dlp | --trans | --gemini-trans | --gemini-level )
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

# --- Argument Validation ---
# Ensure that if --gemini-trans is used, --trans has also been used to set a language.
if [[ -n "$GEMINI_TRANS_MODEL" ]] && [[ "$TRANS" != "trans" ]]; then
    echo ""
    echo "${ICON_ERROR} Error: --gemini-trans requires --trans to be set with a language."
    echo "       Example: --trans es --gemini-trans"
    echo ""
    usage
    exit 1
fi

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

# if online translate
if [[ "$TRANS" == "trans" ]] && [[ "$PLAYER_ONLY" == "" ]]; then
    engine_info=""
    if [[ -n "$GEMINI_TRANS_MODEL" ]]; then
        engine_info="via Gemini ('${GEMINI_TRANS_MODEL}'), context level: ${GEMINI_CONTEXT_LEVEL}"
    else
        engine_info="via translate-shell (engine: '${TRANS_ENGINE}')"
    fi

    if [[ "$SPEAK" == "speak" ]]; then
        printf "[+] Online translation to '${TRANS_LANGUAGE}' ${engine_info}, output: '${OUTPUT_TEXT}', Text-to-speech.\n\n"
    else
        printf "[+] Online translation to '${TRANS_LANGUAGE}' ${engine_info}, output: '${OUTPUT_TEXT}'.\n\n"
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

    # Arrays to store information about translation fallbacks
    declare -a emergency_batches=()
    declare -a emergency_gemini_success=()
    declare -a trans_fallback_blocks=()
    declare -a original_fallback_blocks=()

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
    temp_online_trans_srt="/tmp/whisper-live_${MYPID}.wav.${TRANS_LANGUAGE}.srt"

    if [[ "$skip_transcription" == false ]]; then
        echo ""
        echo "---------------------------------------------------------------------------"
        echo "-> Step 1: Converting audio to WAV format..."
        echo "---------------------------------------------------------------------------"
        echo ""
        ffmpeg -i "${URL}" -y -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper-live_${MYPID}.wav
        err=$?

        if [ $err -eq 0 ]; then
            echo ""
            echo "---------------------------------------------------------------------------"
            echo "-> Step 2: Running Whisper AI Transcription/Translation..."
            echo "---------------------------------------------------------------------------"
            echo ""
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

        # 1. Save the Whisper AI subtitle file if it was newly generated

        echo ""
        echo "-> Saving new Whisper AI subtitle to: $whisper_dest_file"
        cp "$temp_whisper_srt" "$whisper_dest_file"
        if [ $? -ne 0 ]; then
            echo ""
            echo "${ICON_ERROR} Failed to create file $whisper_dest_file ${ICON_ERROR}"
            err=1
        fi

        # The source for the next step is the newly generated temporary file.
        source_srt_file="$temp_whisper_srt"
    else
        echo ""
        echo "---------------------------------------------------------------------------"
        echo "-> Skipping Steps 1 & 2 as requested."
        echo "---------------------------------------------------------------------------"
        echo ""
    fi

    # --- ONLINE TRANSLATION LOGIC ---
    # This is the main switch. If --trans was used, we proceed.
    if [[ "$TRANS" == "trans" ]] && [[ $err -eq 0 ]] && [[ -f "$source_srt_file" ]]; then

        # This is the engine selector. If --gemini-trans was used, its model variable will be set.
        if [[ -n "$GEMINI_TRANS_MODEL" ]]; then
            # --- B. Google Gemini API method ---
            echo ""
            echo "---------------------------------------------------------------------------"
            echo "-> Step 3: Starting Online Translation (Gemini AI) to '${TRANS_LANGUAGE}'..."
            echo ""
            echo "   Using model: ${GEMINI_TRANS_MODEL}, context level: ${GEMINI_CONTEXT_LEVEL}"
            echo "   Source: ${source_srt_file}"
            echo ""
            echo "---------------------------------------------------------------------------"
            echo ""

            if [[ -z "$GEMINI_API_KEY" ]]; then
                echo "${ICON_WARN} GEMINI_API_KEY environment variable not set. Skipping Gemini translation."
                err=1
            else
                # -- Deconstruction --
                echo "--> Deconstructing source SRT file..."
                mapfile -t srt_numbers < <(awk 'BEGIN { RS=""; FS="\n" } { gsub(/\r/,""); print $1 }' "$source_srt_file")
                mapfile -t srt_timestamps < <(awk 'BEGIN { RS=""; FS="\n" } { gsub(/\r/,""); print $2 }' "$source_srt_file")
                mapfile -t text_blocks < <(awk 'BEGIN { RS=""; FS="\n" } { gsub(/\r/,""); s=$3; for (i=4; i<=NF; i++) { s = s "_NL_" $i } print s; }' "$source_srt_file")
                echo "Done."

                # -- Batch Processing with Context Window --
                temp_text_only_trans="/tmp/translated_text_only_${MYPID}.txt"
                > "$temp_text_only_trans"

                batch_size=20
                total_blocks=${#text_blocks[@]}

                # Flags to track failure levels for the final message
                any_emergency_fallback=false
                any_trans_fallback=false
                any_original_fallback=false

                for (( i=0; i<total_blocks; i+=batch_size )); do
                    start_index=$i
                    end_index=$((i + batch_size - 1))
                    if (( end_index >= total_blocks )); then end_index=$((total_blocks - 1)); fi

                    # --- Gemini Prompt Engineering for Subtitles based on Context Level ---
                    context_start=0
                    context_end=0
                    prompt_instructions=""

                    case "$GEMINI_CONTEXT_LEVEL" in
                        0) # Level 0: No context, batch only
                            context_start=$start_index
                            context_end=$end_index
                            prompt_instructions="You are an expert subtitle translator. Translate every text block to ${TRANS_LANGUAGE}. Each block is separated by a delimiter. Maintain the separator exactly in your output. Output only the translated blocks, joined by the separator."
                            ;;
                        1) # Level 1: Minimal bidirectional context
                            context_start=$((start_index - 1))
                            context_end=$((end_index + 1))
                            prompt_instructions="You are an expert subtitle translator. Translate every text block to ${TRANS_LANGUAGE}, using the surrounding blocks for context. Each block is separated by a delimiter. Maintain the separator exactly. Output only the translated blocks, joined by the separator."
                            ;;
                        3) # Level 3: Creative context
                            context_start=$((start_index - 3))
                            context_end=$((end_index + 2))
                            prompt_instructions="You are an expert subtitle translator. Translate every text block to ${TRANS_LANGUAGE}. Use surrounding blocks for context. You have creative freedom to slightly rephrase the translations to ensure they are coherent and flow naturally. Each block is separated by a delimiter. Maintain the separator exactly. Output only the improved translated blocks, joined by the separator."
                            ;;
                        *) # Level 2 (Default): Standard context
                            context_start=$((start_index - 3))
                            context_end=$((end_index + 2))
                            prompt_instructions="You are an expert subtitle translator. Translate every text block to ${TRANS_LANGUAGE}. Each block is separated by a delimiter. Maintain the separator exactly in your output. Output only the translated blocks, joined by the separator."
                            ;;
                    esac

                    # Boundary checks for the context window
                    if (( context_start < 0 )); then context_start=0; fi
                    if (( context_end >= total_blocks )); then context_end=$((total_blocks - 1)); fi

                    text_to_translate=""
                    delimiter="|||SUB|||"
                    num_prefix_context_lines=$((start_index - context_start))
                    num_main_lines=$((end_index - start_index + 1))
                    total_blocks_in_request=$((context_end - context_start + 1))

                    for (( k=context_start; k<=context_end; k++ )); do
                        text_to_translate+="${text_blocks[k]}${delimiter}"
                    done

                    echo "--> Translating blocks $((start_index + 1)) to $((end_index + 1)) (with context window)..."

                    full_prompt="${prompt_instructions}\n\n${text_to_translate}"

                    json_payload=$(jq -n \
                        --arg prompt_text "$full_prompt" \
                        '{
                            "contents": [ { "parts": [ { "text": $prompt_text } ] } ],
                            "safetySettings": [
                                { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
                                { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
                                { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
                                { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" }
                            ]
                        }')

                    max_retries=6
                    retry_count=0
                    batch_successful=false

                    while [[ $retry_count -lt $max_retries && "$batch_successful" == false ]]; do
                        ((retry_count++))

                        api_response_raw=$(curl --silent --no-buffer --max-time 30 -X POST -H 'Content-Type: application/json' -d "$json_payload" "https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_TRANS_MODEL}:generateContent?key=$GEMINI_API_KEY")
                        api_error=$(echo "$api_response_raw" | jq -r '.error.message // ""')

                        if [[ -n "$api_error" ]] || [[ -z "$api_response_raw" ]]; then
                            if [[ -z "$api_error" ]]; then api_error="cURL request timed out or returned empty response."; fi
                            echo "${ICON_ERROR} API Error: ${api_error}"
                            if [[ $retry_count -lt $max_retries ]]; then
                                if [[ "$api_error" == *"quota"* ]]; then
                                    echo "    Quota limit hit. Waiting 61s... ($((retry_count))/$((max_retries - 1)))"
                                    sleep 61
                                else
                                    delay=$((retry_count * 10))
                                    echo "    Retrying in ${delay}s... ($((retry_count))/$((max_retries - 1)))"
                                    sleep $delay
                                fi
                            fi
                            continue
                        fi

                        translated_text_block=$(echo "$api_response_raw" | jq -r '.candidates[0].content.parts[0].text // ""')
                        mapfile -t all_translations_in_batch < <(printf "%s" "$translated_text_block" | tr -d '\r' | sed "s/${delimiter}/\n/g" | grep .)

                        if [ "${#all_translations_in_batch[@]}" -ne "$total_blocks_in_request" ]; then
                            echo "${ICON_ERROR} Translation Alignment Error: Expected ${total_blocks_in_request} total blocks, got ${#all_translations_in_batch[@]}."
                            if [[ $retry_count -lt $max_retries ]]; then
                                delay=$((retry_count * 10))
                                echo "    Retrying in ${delay}s... ($((retry_count))/$((max_retries - 1)))"
                                sleep $delay
                            fi
                        else
                            main_translations=("${all_translations_in_batch[@]:$num_prefix_context_lines:$num_main_lines}")
                            batch_successful=true
                        fi
                    done

                    if [[ "$batch_successful" == true ]]; then
                        for (( j=0; j<num_main_lines; j++ )); do
                            current_block_index=$((start_index + j))
                            printf "%s\n" "${main_translations[j]}" >> "$temp_text_only_trans"

                            # Print with timestamps
                            translated_text_nl=$(echo "${main_translations[j]}" | sed 's/_NL_/\n/g')
                            echo -e "${srt_numbers[current_block_index]}\n${srt_timestamps[current_block_index]}\n${translated_text_nl}\n"
                        done
                    else
                        echo ""
                        echo "${ICON_WARN} Main batch failed. Activating emergency translation in smaller sub-batches..."
                        any_emergency_fallback=true
                        emergency_batches+=("Batch from block $((start_index + 1)) to $((end_index + 1))")
                        mini_batch_size=5

                        for (( j=start_index; j<=end_index; j+=mini_batch_size )); do
                            # Wait between each emergency sub-batch to be rate-limit friendly
                            sleep 5

                            mini_start=$j
                            mini_end=$((j + mini_batch_size - 1))
                            if (( mini_end > end_index )); then mini_end=$end_index; fi

                            echo "    --> Translating sub-batch (lines $((mini_start + 1)) to $((mini_end + 1)))..."

                            mini_text_to_translate=""
                            for (( l=mini_start; l<=mini_end; l++ )); do
                                mini_text_to_translate+="${text_blocks[l]}${delimiter}"
                            done

                            mini_prompt="You are an expert subtitle translator. Translate every text block to ${TRANS_LANGUAGE}. Each block is separated by '${delimiter}'. Maintain the separator exactly. Output only the translated blocks.\n\n${mini_text_to_translate}"
                            mini_payload=$(jq -n --arg prompt_text "$mini_prompt" '{ "contents": [ { "parts": [ { "text": $prompt_text } ] } ], "safetySettings": [ { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" }, { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" }, { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" }, { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" } ] }')
                            mini_response_raw=$(curl --silent --no-buffer --max-time 15 -X POST -H 'Content-Type: application/json' -d "$mini_payload" "https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_TRANS_MODEL}:generateContent?key=$GEMINI_API_KEY")

                            translated_mini_block=$(echo "$mini_response_raw" | jq -r '.candidates[0].content.parts[0].text // ""')
                            mapfile -t translated_mini_lines < <(printf "%s" "$translated_mini_block" | tr -d '\r' | sed "s/${delimiter}/\n/g" | grep .)

                            num_lines_in_mini_batch=$((mini_end - mini_start + 1))
                            if [ "${#translated_mini_lines[@]}" -ne "$num_lines_in_mini_batch" ]; then
                                echo "        ${ICON_ERROR} Sub-batch failed. Falling back to translate-shell for these ${num_lines_in_mini_batch} lines:"
                                for (( l=mini_start; l<=mini_end; l++ )); do
                                    original_text_nl=$(echo "${text_blocks[l]}" | sed 's/_NL_/\n/g')
                                    echo "        -> Translating block $((l + 1)) with fallback..."
                                    # Translate using trans, redirecting stderr to /dev/null
                                    translated_text_nl=$(echo "$original_text_nl" | trans -b -no-warn :${TRANS_LANGUAGE} 2>/dev/null)

                                    # Final fallback: if trans fails, use original text
                                    if [[ -z "$translated_text_nl" ]]; then
                                        any_original_fallback=true
                                        original_fallback_blocks+=("Block $((l + 1)) | ${srt_timestamps[l]}")
                                        echo "            -> translate-shell also failed. Using original text as a last resort."
                                        translated_text_nl="$original_text_nl"
                                        echo -e "${srt_numbers[l]}\n${srt_timestamps[l]}\n${translated_text_nl}\n"
                                    else
                                        any_trans_fallback=true
                                        trans_fallback_blocks+=("Block $((l + 1)) | ${srt_timestamps[l]}")
                                        echo -e "${srt_numbers[l]}\n${srt_timestamps[l]}\n${translated_text_nl}\n"
                                    fi

                                    # Convert back to placeholder format
                                    translated_text_placeholder=$(echo "$translated_text_nl" | awk 'ORS="_NL_"' | sed 's/_NL_$//')
                                    printf "%s\n" "$translated_text_placeholder" >> "$temp_text_only_trans"
                                done
                            else
                                # Show the successful translations and store the timestamp range
                                start_ts_full="${srt_timestamps[mini_start]}"
                                end_ts_full="${srt_timestamps[mini_end]}"
                                # Extract start time from the first block and end time from the last block
                                start_time=$(echo "$start_ts_full" | cut -d' ' -f1)
                                end_time=$(echo "$end_ts_full" | cut -d' ' -f3)
                                emergency_gemini_success+=("Blocks $((mini_start + 1)) to $((mini_end + 1)) | ${start_time} --> ${end_time}")

                                for k in "${!translated_mini_lines[@]}"; do
                                    current_block_index=$((mini_start + k))
                                    translated_text_nl=$(echo "${translated_mini_lines[k]}" | sed 's/_NL_/\n/g')
                                    echo -e "${srt_numbers[current_block_index]}\n${srt_timestamps[current_block_index]}\n${translated_text_nl}\n"
                                    printf "%s\n" "${translated_mini_lines[k]}" >> "$temp_text_only_trans"
                                done
                            fi
                        done
                        echo "${ICON_WARN} Finished emergency handling for the problematic block."
                    fi

                    # Wait before processing the next main batch to be rate-limit friendly
                    if [ $i -lt $((total_blocks - batch_size)) ]; then
                        sleep 1
                    fi
                done

                mapfile -t all_translated_lines < "$temp_text_only_trans"
                rm "$temp_text_only_trans"

                echo "--> Reconstructing final SRT file..."
                > "$temp_online_trans_srt"
                for (( k=0; k<total_blocks; k++ )); do
                    line_number="${srt_numbers[k]}"
                    timestamp="${srt_timestamps[k]}"
                    translated_text="${all_translated_lines[k]:-${text_blocks[k]}}" # Fallback to original text_block if line is empty
                    translated_text_final=$(printf "%s" "$translated_text" | sed 's/_NL_/\n/g')
                    echo -e "${line_number}\n${timestamp}\n${translated_text_final}\n" >> "$temp_online_trans_srt"
                done
                echo "Done."
            fi
        else
            # --- A. Translate-shell (trans) method ---
            echo ""
            echo "---------------------------------------------------------------------------"
            echo "-> Step 3: Starting Online Translation (translate-shell / Simple Method)..."
            echo ""
            echo "   Using engine: ${TRANS_ENGINE}"
            echo "   Source: ${source_srt_file}"
            echo ""
            echo "---------------------------------------------------------------------------"
            echo ""

            # Redirect stderr to /dev/null to hide gawk errors
            trans -b -e "${TRANS_ENGINE}" :"${TRANS_LANGUAGE}" -i "$source_srt_file" 2>/dev/null | tee "$temp_online_trans_srt"
            err=${PIPESTATUS[0]}

            if [[ $err -ne 0 ]]; then
                echo "${ICON_ERROR} translate-shell failed."
            fi
            echo ""
        fi
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
                cp "$source_file" "$dest_file"
                if [ $? -ne 0 ]; then
                    echo ""
                    echo "${ICON_ERROR} Failed to copy file to $dest_file. Temp file is at $source_file ${ICON_ERROR}"
                    err=1
                fi
                ;;
            n|no)
                echo ""
                echo "${ICON_WARN} User chose not to overwrite. The temporary file is available at: '$source_file' ${ICON_WARN}"
                err=2
                ;;
            *)
                echo ""
                echo "${ICON_ERROR} Invalid response. The temporary file is available at '$source_file' ${ICON_ERROR}"
                err=1
                ;;
        esac
    }

    if [ $err -eq 0 ]; then
        echo ""
        echo "=========================================="
        echo "-> Finalizing File..."
        echo "=========================================="

        # 1. Save the Whisper AI subtitle file if it was newly generated. No more questions here.
        if [[ "$skip_transcription" == false ]]; then
            if [ ! -e "$whisper_dest_file" ]; then
                echo ""
                echo "${ICON_ERROR} Failed to create file to $whisper_dest_file ${ICON_ERROR}"
                err=1
            fi
        else
            echo ""
             echo "-> Whisper AI subtitle file was not re-generated, so no new version to save."
        fi

        if [[ $err -eq 0 ]] && [[ "$TRANS" == "trans" ]] && [[ -f "$temp_online_trans_srt" ]]; then
             trans_dest_file="${url_no_ext}.${TRANS_LANGUAGE}.srt"
             trans_file_description="Online Translated Subtitle (${TRANS_LANGUAGE})"

             save_online_translation_file "$temp_online_trans_srt" "$trans_dest_file" "$trans_file_description"

             set +x
         fi
     fi

    # --- Final Status ---
    if [ $err -eq 0 ]; then
        success=true
        # Check for any issues and set success to false if any are found
        if [ ${#original_fallback_blocks[@]} -gt 0 ] || [ ${#trans_fallback_blocks[@]} -gt 0 ] || [ ${#emergency_batches[@]} -gt 0 ]; then
            success=false
        fi

        # General summary if emergency mode was triggered
        if [ ${#emergency_batches[@]} -gt 0 ]; then
             echo ""; echo " ${ICON_WARN} SUMMARY: The translation process encountered issues and entered emergency mode for the following main batches: ${ICON_WARN}";
             for item in "${emergency_batches[@]}"; do
                echo "  - $item"
            done
        fi

        # Most severe issue: Using original text
        if [ ${#original_fallback_blocks[@]} -gt 0 ]; then
            echo ""; echo " ${ICON_ERROR} CRITICAL: Some blocks could not be translated by any engine. Original text was used in these instances: ${ICON_ERROR}";
            printf "%-20s | %s\n" "Block Number" "Timestamp"
            printf -- "-%.0s" {1..50}; echo ""
            for item in "${original_fallback_blocks[@]}"; do
                printf "%-20s | %s\n" "$(echo $item | cut -d'|' -f1)" "$(echo $item | cut -d'|' -f2)"
            done
        fi

        # Second most severe: Fallback to translate-shell
        if [ ${#trans_fallback_blocks[@]} -gt 0 ]; then
            echo ""; echo " ${ICON_WARN} WARNING: Some blocks failed with Gemini and fell back to translate-shell in these instances: ${ICON_WARN}";
            printf "%-20s | %s\n" "Block Number" "Timestamp"
            printf -- "-%.0s" {1..50}; echo ""
            for item in "${trans_fallback_blocks[@]}"; do
                printf "%-20s | %s\n" "$(echo $item | cut -d'|' -f1)" "$(echo $item | cut -d'|' -f2)"
            done
        fi

        # Informational: Gemini successes within emergency mode
        if [ ${#emergency_gemini_success[@]} -gt 0 ]; then
             echo ""; echo " ${ICON_OK} INFO: Gemini successfully translated the following sub-batches within emergency mode: ${ICON_OK}";
             printf "%-30s | %s\n" "Sub-Batch Range" "Timestamp Range"
             printf -- "-%.0s" {1..80}; echo ""
             for item in "${emergency_gemini_success[@]}"; do
                printf "%-30s | %s\n" "$(echo $item | cut -d'|' -f1)" "$(echo $item | cut -d'|' -f2)"
            done
        fi

        if [[ "$success" == true ]]; then
            echo ""; echo "${ICON_OK} Subtitles generation process completed successfully! ${ICON_OK}"; echo ""
        else
            # Add a final newline for better separation if there were warnings/errors
            echo ""
        fi

        exit 0
    elif [ $err -eq 2 ]; then
        echo ""; echo " ${ICON_WARN} Operation finished, but final file was not saved as per user request. ${ICON_WARN}"; echo ""
        exit 0
    else
        echo ""; echo "${ICON_ERROR} An error occurred during the subtitle generation process. ${ICON_ERROR}"; echo ""
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
             filter_complex="[0:a]showspectrum=s=854x480:mode=separate:color=intensity:legend=disabled:fps=25,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='PID\: ${MYPID} | %{pts\:gmtime\:$(date +%s)\:%Y-%m-%d %H\\\\\:%M\\\\\:%S}':fontcolor=white:x=10:y=10"
             ffmpeg -loglevel quiet -y -f pulse -i "$AUDIO_INDEX" -filter_complex "$filter_complex" -c:v mjpeg -q:v 2 -c:a pcm_s16le -threads 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 -segment_format avi /tmp/${filename_base}.avi &
             FFMPEG_PID=$!
             ;;
         avfoundation )
             filename_base="whisper-live_${MYPID}_buf%03d"
             filter_complex="[0:a]showspectrum=s=854x480:mode=separate:color=intensity:legend=disabled:fps=25,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='PID\: ${MYPID} | %{pts\:gmtime\:$(date +%s)\:%Y-%m-%d %H\\\\\:%M\\\\\:%S}':fontcolor=white:x=10:y=10"
             ffmpeg -loglevel quiet -y -f avfoundation -i :"${AUDIO_INDEX}" -filter_complex "$filter_complex" -c:v mjpeg -q:v 2 -c:a pcm_s16le -threads 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 -segment_format avi /tmp/${filename_base}.avi &
             FFMPEG_PID=$!
             ;;
        *youtube* | *youtu.be* )
            if ! command -v yt-dlp &>/dev/null; then echo "yt-dlp is required" && exit 1; fi
            ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f b -g $URL) -bufsize 44M -acodec ${FMT} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
            FFMPEG_PID=$!
            ;;
        * )
            if [[ "$STREAMLINK_FORCE" = "streamlink" || "$URL" = *twitch* ]]; then
                if ! command -v streamlink >/dev/null 2>&1; then echo "streamlink is required" && exit 1; fi
                streamlink $URL best -O 2>/dev/null | ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i - -bufsize 44M -acodec ${FMT} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                FFMPEG_PID=$!
            elif [[ "$YTDLP_FORCE" = "yt-dlp" ]]; then
                if ! command -v yt-dlp &>/dev/null; then echo "yt-dlp is required" && exit 1; fi
                ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $(yt-dlp -i -f b -g $URL) -bufsize 44M -acodec ${FMT} -threads 2 -vcodec libx264 -map 0:v:0 -map 0:a:0 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                FFMPEG_PID=$!
            else
                if [[ $QUALITY == "lower" ]]; then
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $URL -bufsize 44M -map_metadata 0 -map 0:v:0? -map 0:v:1? -map 0:v:2? -map 0:v:3? -map 0:v:4? -map 0:v:5? -map 0:v:6? -map 0:v:7? -map 0:v:8? -map 0:v:9? -map 0:a? -acodec ${FMT} -vcodec libx264 -threads 2 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                    FFMPEG_PID=$!
                else
                    ffmpeg -loglevel quiet -accurate_seek -y -probesize 32 -i $URL -bufsize 44M -map_metadata 0 -map 0:v:9? -map 0:v:8? -map 0:v:7? -map 0:v:6? -map 0:v:5? -map 0:v:4? -map 0:v:3? -map 0:v:2? -map 0:v:1? -map 0:v:0? -map 0:a? -acodec ${FMT} -vcodec libx264 -threads 2 -preset ultrafast -movflags +faststart -vsync 2 -f segment -segment_time $SEGMENT_TIME -reset_timestamps 1 /tmp/whisper-live_${MYPID}_buf%03d.avi &
                    FFMPEG_PID=$!
                fi
            fi
            ;;
    esac

    arg='#EXTM3U'
	x=0
	while [ $x -lt $SEGMENTS ]; do
		arg="$arg"'\n/tmp/whisper-live_'"${MYPID}"'_'"$x"'.avi'
		x=$((x+1))
	done
	echo -e $arg > /tmp/playlist_whisper-live_${MYPID}.m3u

    max_wait_time=20
    file_path="/tmp/whisper-live_${MYPID}_buf000.avi"
    start_time=$(date +%s)
    while [ ! -f "$file_path" ]; do
        current_time=$(date +%s)
        elapsed_time=$((current_time - start_time))
        if [ "$elapsed_time" -ge "$max_wait_time" ]; then echo "Maximum wait time exceeded." && break; fi
        sleep 0.1
    done

    if [ -f "$file_path" ]; then
        sleep 10
        ln -f -s /tmp/whisper-live_${MYPID}_buf000.avi /tmp/whisper-live_${MYPID}_0.avi
    else
        printf "${ICON_ERROR} Error: ffmpeg failed to capture the stream\n" && exit 1
    fi

    if [[ "$PLAYER_ONLY" == "" ]]; then printf "Buffering audio. Please wait...\n\n"; fi
    if ! ps -p $FFMPEG_PID > /dev/null; then printf "${ICON_ERROR} Error: ffmpeg failed to capture the stream\n" && exit 1; fi

    sleep 2
    if [[ $MPV_OPTIONS == "true" ]]; then
        vlc -I http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
    else
        vlc --extraintf=http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
    fi

    if [ $? -ne 0 ]; then printf "${ICON_ERROR} Error: The player could not play the stream\n" && exit 1; fi
    VLC_PID=$(ps -ax -o etime,pid,command -c | grep -i '[Vv][Ll][Cc]' | tail -n 1 | awk '{print $2}')
    if [ -z "$VLC_PID" ]; then printf "${ICON_ERROR} Error: The player could not be executed.\n" && exit 1; fi

    set +e
    n=0; tbuf=0; abuf="000"; xbuf=1; nbuf="001"
    FILEPLAYED=""; transcribed_until=0; segment_duration=0; last_pos=0
    TIMEPLAYED=0; tin=0

    while [ $RUNNING -eq 1 ]; do
        if [ -f /tmp/whisper-live_${MYPID}_buf$nbuf.avi ]; then
            mv -f /tmp/whisper-live_${MYPID}_buf$abuf.avi /tmp/whisper-live_${MYPID}_$n.avi
            if [ $n -eq $((SEGMENTS-1)) ]; then n=-1; fi
            tbuf=$((tbuf+1))
            if [ $tbuf -lt 10 ]; then abuf="00"$tbuf""; elif [ $tbuf -lt 100 ]; then abuf="0"$tbuf""; else abuf="$tbuf"; fi
            xbuf=$((xbuf+1))
            if [ $xbuf -lt 10 ]; then nbuf="00"$xbuf""; elif [ $xbuf -lt 100 ]; then nbuf="0"$xbuf""; else nbuf="$xbuf"; fi
            n=$((n+1))
            ln -f -s /tmp/whisper-live_${MYPID}_buf$abuf.avi /tmp/whisper-live_${MYPID}_$n.avi
        fi

        vlc_check
        curl_output=$(curl -s -N -u :playlist4whisper http://127.0.0.1:${MYPORT}/requests/status.xml)
        FILEPLAY=$(echo "$curl_output" | sed -n 's/.*<info name='"'"'filename'"'"'>\([^<]*\).*$/\1/p')
        POSITION=$(echo "$curl_output" | sed -n 's/.*<time>\([^<]*\).*$/\1/p')

        # Safety guard: if VLC is paused or not providing a valid time, skip this iteration.
        if ! [[ "$POSITION" =~ ^[0-9]+$ ]]; then
            sleep 0.1
            continue
        fi

        if [[ "$PLAYER_ONLY" == "" ]] && [[ -f "/tmp/$FILEPLAY" ]]; then

            file_mod_time=0
            if [[ "$(uname)" == "Darwin" ]]; then # macOS compatible command
                file_mod_time=$(stat -f %m "/tmp/$FILEPLAY")
            else # GNU/Linux command
                file_mod_time=$(date +%s -r "/tmp/$FILEPLAY")
            fi

            if [ "$FILEPLAY" != "$FILEPLAYED" ]; then
                FILEPLAYED="$FILEPLAY"
                TIMEPLAYED=$file_mod_time
                translated_context_window=()
                transcribed_until=0; last_pos=0; tin=0

                # This ffprobe check is only for the very first chunk of a new file segment.
                segment_duration=$(ffprobe -i "/tmp/$FILEPLAY" -show_format -v quiet | sed -n 's/duration=//p' 2>/dev/null)
                if ! [[ "$segment_duration" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then segment_duration=$SEGMENT_TIME; fi

                if (( $(echo "$segment_duration > 1" | bc -l) )); then
                    ffmpeg -loglevel quiet -v error -noaccurate_seek -i "/tmp/$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -t $STEP_S /tmp/whisper-live_${MYPID}.wav
                    process_audio_chunk "/tmp/whisper-live_${MYPID}.wav"
                    transcribed_until=$STEP_S
                fi
            elif [ "$file_mod_time" -gt "$((TIMEPLAYED + SEGMENT_TIME + 6))" ] && [ $tin -eq 0 ]; then
                tin=1
            fi

            if [ $tin -eq 0 ]; then
                # This logic correctly handles when the user seeks forward or backward in the video.
                pos_diff=$(echo "$POSITION - $last_pos" | bc)
                seek_threshold=$(echo "2 * $STEP_S" | bc)
                if (( $(echo "$pos_diff > $seek_threshold" | bc -l) )) || (( $(echo "$pos_diff < -$seek_threshold" | bc -l) )); then
                    transcribed_until=$POSITION
                fi
                last_pos=$POSITION

                # Main transcription trigger.
                if (( $(echo "$POSITION + $SYNC > $transcribed_until" | bc -l) )); then
                    # NOTE: 'local' keyword removed for shell compatibility.
                    chunk_start=$transcribed_until
                    chunk_duration=$STEP_S

                    ffmpeg -loglevel quiet -v error -noaccurate_seek -i "/tmp/$FILEPLAY" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss "$chunk_start" -t "$chunk_duration" /tmp/whisper-live_${MYPID}.wav

                    process_audio_chunk "/tmp/whisper-live_${MYPID}.wav"

                    transcribed_until=$((transcribed_until + STEP_S))
                fi
            elif [ $tin -eq 1 ]; then
                echo
                echo "${ICON_WARN} Timeshift window reached. Video $FILEPLAY overwritten. Transcription may be affected. ${ICON_WARN}"
                echo
                tin=2
            fi
        fi

        sleep 0.1
    done

    pkill -f "^ffmpeg.*${MYPID}.*$"
    pkill -f "^${WHISPER_EXECUTABLE}.*${MYPID}.*$"
    if [ -f "$TEMP_FILE" ]; then awk -v myport="$myport" '$0 !~ myport' "$TEMP_FILE" > temp_file.tmp && mv temp_file.tmp "$TEMP_FILE"; fi

elif [[ $TIMESHIFT == "timeshift" ]] && [[ $LOCAL_FILE -eq 1 ]]; then # local video file with vlc
    if [[ "$PLAYER_ONLY" == "" ]]; then
        arg="#EXTM3U\n${URL}"
        echo -e $arg > /tmp/playlist_whisper-live_${MYPID}.m3u

        if [[ $MPV_OPTIONS == "true" ]]; then
            vlc -I http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
        else
            vlc --extraintf=http --http-host 127.0.0.1 --http-port "$MYPORT" --http-password playlist4whisper -L /tmp/playlist_whisper-live_${MYPID}.m3u >/dev/null 2>&1 &
        fi

        if [ $? -ne 0 ]; then printf "${ICON_ERROR} Error: The player could not play the file.\n" && exit 1; fi
        VLC_PID=$(ps -ax -o etime,pid,command -c | grep -i '[Vv][Ll][Cc]' | tail -n 1 | awk '{print $2}')
        if [ -z "$VLC_PID" ]; then printf "${ICON_ERROR} Error: The player could not be executed.\n" && exit 1; fi

        set +e
        FILEPLAYED=""; transcribed_until=0; segment_duration=0; last_pos=0

        while [ $RUNNING -eq 1 ]; do
            vlc_check
            curl_output=$(curl -s -N -u :playlist4whisper http://127.0.0.1:${MYPORT}/requests/status.xml)
            FILEPLAY=$(echo "$curl_output" | sed -n 's/.*<info name='"'"'filename'"'"'>\([^<]*\).*$/\1/p')
            POSITION=$(echo "$curl_output" | sed -n 's/.*<time>\([^<]*\).*$/\1/p')

            if [[ -n "$FILEPLAY" ]]; then
                if [ "$FILEPLAY" != "$FILEPLAYED" ]; then
                    FILEPLAYED="$FILEPLAY"
                    translated_context_window=()
                    transcribed_until=0; last_pos=0
                    segment_duration=$(ffprobe -i "${URL}" -show_format -v quiet | sed -n 's/duration=//p' 2>/dev/null)
                    if ! [[ "$segment_duration" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then segment_duration=999999; fi

                    if (( $(echo "$segment_duration > 1" | bc -l) )); then
                        ffmpeg -loglevel quiet -v error -noaccurate_seek -i "${URL}" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -t $STEP_S /tmp/whisper-live_${MYPID}.wav
                        process_audio_chunk "/tmp/whisper-live_${MYPID}.wav"
                        transcribed_until=$STEP_S
                    fi
                fi

                pos_diff=$(echo "$POSITION - $last_pos" | bc)
                seek_threshold=$(echo "2 * $STEP_S" | bc)
                if (( $(echo "$pos_diff > $seek_threshold" | bc -l) )) || (( $(echo "$pos_diff < -$seek_threshold" | bc -l) )); then
                    transcribed_until=$POSITION
                fi
                last_pos=$POSITION

                if (( $(echo "$POSITION + $SYNC > $transcribed_until" | bc -l) )) && (( $(echo "$transcribed_until < $segment_duration" | bc -l) )); then
                    chunk_start=$transcribed_until
                    chunk_duration=$STEP_S

                    if (( $(echo "$chunk_start + $chunk_duration > $segment_duration" | bc -l) )); then
                        chunk_duration=$(echo "$segment_duration - $chunk_start" | bc)
                    fi

                    if (( $(echo "$chunk_duration > 1" | bc -l) )); then
                        ffmpeg -loglevel quiet -v error -noaccurate_seek -i "${URL}" -y -ar 16000 -ac 1 -c:a pcm_s16le -ss "$chunk_start" -t "$chunk_duration" /tmp/whisper-live_${MYPID}.wav
                        process_audio_chunk "/tmp/whisper-live_${MYPID}.wav"
                    fi

                    transcribed_until=$((transcribed_until + STEP_S))
                fi
            fi
            sleep 0.1
        done

        pkill -f "^ffmpeg.*${MYPID}.*$"
        pkill -f "^${WHISPER_EXECUTABLE}.*${MYPID}.*$"
        if [ -f "$TEMP_FILE" ]; then awk -v myport="$myport" '$0 !~ myport' "$TEMP_FILE" > temp_file.tmp && mv temp_file.tmp "$TEMP_FILE"; fi
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
            sleep 0.1
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
