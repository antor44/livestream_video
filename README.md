# livestream_video.sh

Transcribe video livestream by feeding ffmpeg output to whisper.cpp at regular intervals, based on livestream.sh from whisper.cpp

This Linux script adds some new features:

-Language command-line option: auto (for autodetection), en, es, fr, de, iw, ar, etc.
-Translate to English when auto is selected


Usage: ./livestream_video.sh stream_url [step_s] [model] [language]

  Example (defaults if no options are specified):
  
    ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 3 tiny.en en


# Step:
Size of the parts into which videos are divided for inference, size in seconds.

# Whisper models:
tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large

# Whisper languages:

auto , autodetected
en , english
zh , chinese
de , german
es , spanish
ru , russian
ko , korean
fr , french
ja , japanese
pt , portuguese
ca , catalan
nl , dutch
ar , arabic
it , italian
iw , hebrew
uk , ukrainian
ro , romanian
fa , persian
sv , swedish
id , indonesian
hi , hindi
fi , finnish
vi , vietnamese
iw , hebrew
uk , ukrainian
el , greek
ms , malay
cs , czech
ro , romanian
da , danish
hu , hungarian
ta , tamil
no , norwegian
th , thai
ur , urdu
hr , croatian
bg , bulgarian
lt , lithuanian
la , latin
mi , maori
ml , malayalam
cy , welsh
sk , slovak
te , telugu
fa , persian
lv , latvian
bn , bengali
sr , serbian
az , azerbaijani
sl , slovenian
kn , kannada
et , estonian
mk , macedonian
br , breton
eu , basque
is , icelandic
hy , armenian
ne , nepali
mn , mongolian
bs , bosnian
kk , kazakh
sq , albanian
sw , swahili
gl , galician
mr , marathi
pa , punjabi
si , sinhala
km , khmer
sn , shona
yo , yoruba
so , somali
af , afrikaans
oc , occitan
ka , georgian
be , belarusian
tg , tajik
sd , sindhi
gu , gujarati
am , amharic
yi , yiddish
lo , lao
uz , uzbek
fo , faroese
ht , haitian creole
ps , pashto
tk , turkmen
nn , nynorsk
mt , maltese
sa , sanskrit
lb , luxembourgish
my , myanmar
br , breton
eu , basque
is , icelandic
hy , armenian
ne , nepali
mn , mongolian
bs , bosnian
kk , kazakh
sq , albanian
sw , swahili
gl , galician
mr , marathi
pa , punjabi
si , sinhala
km , khmer
sn , shona
yo , yoruba
so , somali
af , afrikaans
oc , occitan
ka , georgian
be , belarusian
tg , tajik
sd , sindhi
gu , gujarati
am , amharic
yi , yiddish
lo , lao
uz , uzbek
fo , faroese
ht , haitian creole
ps , pashto
tk , turkmen
nn , nynorsk
mt , maltese
sa , sanskrit
lb , luxembourgish
my , myanmar
bo , tibetan
tl , tagalog
mg , malagasy
as , assamese
tt , tatar
haw , hawaiian
ln , lingala
ha , hausa
ba , bashkir
jw , javanese
su , sundanese

#

Most video streams should work.

Recommended Linux video player: SMPlayer based on mvp, or any other video player based on mplayer, due to its capabilities to timeshift online streams for synchronized live video with the transcription.

## Screenshot:

![Screenshot](https://github.com/antor44/livestream_video/blob/main/whisper_TV.jpg)
