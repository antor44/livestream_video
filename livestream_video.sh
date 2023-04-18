#!/bin/bash
#
# livestream_video.sh v. 1.14
#
#Transcribe video livestream by feeding ffmpeg output to whisper.cpp at regular intervals, based on livestream.sh from whisper.cpp
#
# This Linux script adds some new features:
#
# -Language command-line option: auto (for autodetection), en, es, fr, de, iw, ar, etc.
#
# -Translate to English
#
#
# Usage: ./livestream_video.sh stream_url [step_s] [model] [language] [translate]
#
#   Example (defaults if no options are specified):
#  
#    ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 3 tiny.en en
#
#
# Script and Whisper executable (main), and models directory with at least one archive model, must reside in the same directory.
#


set -eo pipefail

url_default="https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8"
fmt=mp3 # the audio format
step_s=4
model="base"
language="auto"
translate=""

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

# Whisper languages:

# Autodetected (auto), English (en), Chinese (zh), German (de), Spanish (es), Russian (ru), Korean (ko), French (fr), Japanese (ja), Portuguese (pt), Catalan (ca), Dutch (nl), Arabic (ar), Italian (it), Hebrew (iw), Ukrainian (uk), Romanian (ro), Swedish (sv), Indonesian (id), Hindi (hi), Finnish (fi), Vietnamese (vi), Hebrew (iw), Ukrainian (uk), Greek (el), Malay (ms), Czech (cs), Romanian (ro), Danish (da), Hungarian (hu), Tamil (ta), Norwegian (no), Thai (th), Urdu (ur), Croatian (hr), Bulgarian (bg), Lithuanian (lt), Latin (la), Maori (mi), Malayalam (ml), Welsh (cy), Slovak (sk), Telugu (te), Persian (fa), Latvian (lv), Bengali (bn), Serbian (sr), Azerbaijani (az), Slovenian (sl), Kannada (kn), Estonian (et), Macedonian (mk), Breton (br), Basque (eu), Icelandic (is), Armenian (hy), Nepali (ne), Mongolian (mn), Bosnian (bs), Kazakh (kk), Albanian (sq), Swahili (sw), Galician (gl), Marathi (mr), Punjabi (pa), Sinhala (si), Khmer (km), Shona (sn), Yoruba (yo), Somali (so), Afrikaans (af), Occitan (oc), Georgian (ka), Belarusian (be), Tajik (tg), Sindhi (sd), Gujarati (gu), Amharic (am), Yiddish (yi), Lao (lo), Uzbek (uz), Faroese (fo), Haitian Creole (ht), Pashto (ps), Turkmen (tk), Nynorsk (nn), Maltese (mt), Sanskrit (sa), Luxembourgish (lb), Myanmar (my), Tibetan (bo), Tagalog (tl), Malagasy (mg), Assamese (as), Tatar (tt), Hawaiian (haw), Lingala (ln), Hausa (ha), Bashkir (ba), Javanese (jw), Sundanese (su).


languages=( "auto" "en" "zh" "de" "es" "ru" "ko" "fr" "ja" "pt" "tr" "pl" "ca" "nl" "ar" "sv" "it" "id" "hi" "fi" "vi" "iw" "uk" "el" "ms" "cs" "ro" "da" "hu" "ta" "no" "th" "ur" "hr" "bg" "lt" "la" "mi" "ml" "cy" "sk" "te" "fa" "lv" "bn" "sr" "az" "sl" "kn" "et" "mk" "br" "eu" "is" "hy" "ne" "mn" "bs" "kk" "sq" "sw" "gl" "mr" "pa" "si" "km" "sn" "yo" "so" "af" "oc" "ka" "be" "tg" "sd" "gu" "am" "yi" "lo" "uz" "fo" "ht" "ps" "tk" "nn" "mt" "sa" "lb" "my" "bo" "tl" "mg" "as" "tt" "haw" "ln" "ha" "ba" "jw" "su" )

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
    
    # Whisper models
    models=( "tiny.en" "tiny" "base.en" "base" "small.en" "small" "medium.en" "medium" "large-v1" "large" )

    # list available models
    function list_models {
        printf "\n"
        printf "  Available models:"
        for model in "${models[@]}"; do
            printf " $model"
        done
        printf "\n\n"
    }

    list_languages

}


check_requirements


while (( "$#" )); do
    case $1 in
        *://* ) url=$1;;
        [2-9]|[1-5][0-9]|60 ) step_s=$1;;
        tiny.en|tiny|base.en|base|small.en|small|medium.en|medium|large-v1|large ) model=$1;;
        auto|[a-z][a-z]|haw ) language=$1;;
        translate ) translate=$1;;
        * ) echo ""; echo "*** Wrong option $1"; echo ""; usage; exit 1;;
    esac
    shift
done


# Whisper languages:

# Autodetected (auto), English (en), Chinese (zh), German (de), Spanish (es), Russian (ru), Korean (ko), French (fr), Japanese (ja), Portuguese (pt), Catalan (ca), Dutch (nl), Arabic (ar), Italian (it), Hebrew (iw), Ukrainian (uk), Romanian (ro), Swedish (sv), Indonesian (id), Hindi (hi), Finnish (fi), Vietnamese (vi), Hebrew (iw), Ukrainian (uk), Greek (el), Malay (ms), Czech (cs), Romanian (ro), Danish (da), Hungarian (hu), Tamil (ta), Norwegian (no), Thai (th), Urdu (ur), Croatian (hr), Bulgarian (bg), Lithuanian (lt), Latin (la), Maori (mi), Malayalam (ml), Welsh (cy), Slovak (sk), Telugu (te), Persian (fa), Latvian (lv), Bengali (bn), Serbian (sr), Azerbaijani (az), Slovenian (sl), Kannada (kn), Estonian (et), Macedonian (mk), Breton (br), Basque (eu), Icelandic (is), Armenian (hy), Nepali (ne), Mongolian (mn), Bosnian (bs), Kazakh (kk), Albanian (sq), Swahili (sw), Galician (gl), Marathi (mr), Punjabi (pa), Sinhala (si), Khmer (km), Shona (sn), Yoruba (yo), Somali (so), Afrikaans (af), Occitan (oc), Georgian (ka), Belarusian (be), Tajik (tg), Sindhi (sd), Gujarati (gu), Amharic (am), Yiddish (yi), Lao (lo), Uzbek (uz), Faroese (fo), Haitian Creole (ht), Pashto (ps), Turkmen (tk), Nynorsk (nn), Maltese (mt), Sanskrit (sa), Luxembourgish (lb), Myanmar (my), Tibetan (bo), Tagalog (tl), Malagasy (mg), Assamese (as), Tatar (tt), Hawaiian (haw), Lingala (ln), Hausa (ha), Bashkir (ba), Javanese (jw), Sundanese (su).


if [[ ! " ${languages[@]} " =~ " ${language} " ]]; then
    echo ""
    printf "*** Invalid language: $language\n"
    echo ""
    usage

    exit 1
fi

if [ ! -f ./models/ggml-${model}.bin ]; then
    echo ""
    echo "*** No file /models/ggml-${model}.bin for model ${model}"
    echo ""
    usage

    exit 1
fi




if [ $url == "" ]; then
    url=$url_default
    echo ""
    echo "*** No url specified, using default: $url"
    echo ""
else
    echo ""
    echo "*** url specified by user: $url"
    echo ""
fi

running=1

trap "running=0" SIGINT SIGTERM

if [ -f /tmp/whisper-live.wav ]; then
    rm /tmp/whisper* &>/dev/null
fi

# if translate then translate to english

if [[ $translate == "translate" ]]; then
    translate="-tr"
    printf "[+] Transcribing stream with model '$model', step_s $step_s, language '$language', translate to english (press Ctrl+C to stop):\n\n"
else
    translate=""
    printf "[+] Transcribing stream with model '$model', step_s $step_s, language '$language', NO translate to english (press Ctrl+C to stop):\n\n"
fi    
    

# continuous stream in native fmt (this file will grow forever!)
ffmpeg -loglevel quiet -y -probesize 32 -i $url -map 0:a:0 /tmp/whisper-live0.${fmt} &
if [ $? -ne 0 ]; then
    printf "Error: ffmpeg failed to capture audio stream\n"
    exit 1
fi

printf "Buffering audio. Please wait...\n\n"
sleep $(($step_s))

# do not stop script on error
set +e

i=0
SECONDS=0
while [ $running -eq 1 ]; do
    # extract the next piece from the main file above and transcode to wav. -ss sets start time, -0.x seconds adjust
    err=1
    while [ $err -ne 0 ]; do
        if [ $i -gt 0 ]; then
            ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live0.${fmt} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss $(echo "$i * $step_s - 0.8" | bc) -t $(echo "$step_s + 0.1" | bc) /tmp/whisper-live.wav 2> /tmp/whisper-live.err
        else
            ffmpeg -loglevel quiet -v error -noaccurate_seek -i /tmp/whisper-live0.${fmt} -y -ar 16000 -ac 1 -c:a pcm_s16le -ss 0 -t $step_s /tmp/whisper-live.wav 2> /tmp/whisper-live.err
        fi
        err=$(cat /tmp/whisper-live.err | wc -l)
    done

    ./main -l ${language} ${translate} -t 8 -m ./models/ggml-${model}.bin -f /tmp/whisper-live.wav --no-timestamps -otxt 2> /tmp/whispererr | tail -n 1

    while [ $SECONDS -lt $((($i+1)*$step_s)) ]; do
        sleep 0.5
    done
    ((i=i+1))
done

killall -v ffmpeg
killall -v main
