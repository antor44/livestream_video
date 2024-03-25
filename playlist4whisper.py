"""

play4whisper - displays a playlist for "livestream_video.sh". AI technology to transcribe the audio from the livestream.

Copyright (c) 2023 Antonio R.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

https://github.com/antor44/livestream_video


---------------------------------


"Playlist4Whisper" is an application that displays a playlist for "livestream_video.sh". It plays an online video
 and uses AI technology to transcribe the audio into text. It supports multi-instance and multi-user execution,
 and allows for changing options per channel and global options.


Author: Antonio R. Version: 2.08 License: GPL 3.0


Usage:
python playlist4whisper.py

-Support for multi-instance and multi-user execution
-Support for IPTV, YouTube, Twitch and many others

The program will load the default playlists playlist_iptv.m3u, playlist_youtube.m3u, and playlist_twitch.m3u,
 and will store options in config_xxx.json.


To ensure proper functioning of this GUI, all whisper.cpp files (from the official releases),
 as well as the script livestream_video.sh, should be copied to the same location as playlist4whisper.py.
 The main executable of whisper.cpp, which is the primary example, should be in the same directory with
 the default executable name 'main'. Additionally, the Whisper model file from OpenAI should be placed
 in the "models" subdirectory with the correct format and name, as specified in the Whisper.cpp repository.
 This can be done using terminal commands such as the following examples:

make tiny.en

make small

playlist4whisper.py depends on (smplayer or mpv) video player and (gnome-terminal or konsole or
xfce4-terminal).

For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp)
For Twitch streamlink is required (https://streamlink.github.io)

Options for script:

Usage:
./livestream_video.sh stream_url [step_s] [model] [language] [translate] [quality] [ [player executable + player options] ] [timeshift] [sync s] [segments n] [segment_time m]

Example (defaults if no options are specified):
./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 8 base auto raw [smplayer]

 [streamlink] option forces the url to be processed by streamlink
 [yt-dlp] option forces the url to be processed by yt-dlp

Quality: The valid options are "raw," "upper," and "lower". "Raw" is used to download another video stream without
 any modifications for the player. "Upper" and "lower" download only one stream, which might correspond to the best
 or worst stream quality, re-encoded for the player.


"[player executable + player options]", valid players: smplayer, mpv, mplayer, vlc, etc... or "[none]" for no player.

Step: Size of the parts into which videos are divided for inference, size in seconds.

Whisper models: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2. large-v3

    ... with suffixes each too: -q4_0, -q4_1, -q4_2, -q5_0, -q5_1, -q8_0

Whisper languages:

auto (Autodetect), af (Afrikaans), am (Amharic), ar (Arabic), as (Assamese), az (Azerbaijani), be (Belarusian),
bg (Bulgarian), bn (Bengali), br (Breton), bs (Bosnian), ca (Catalan), cs (Czech), cy (Welsh), da (Danish),
de (German), el (Greek), en (English), eo (Esperanto), es (Spanish), et (Estonian), eu (Basque), fa (Persian),
fi (Finnish), fo (Faroese), fr (French), ga (Irish), gl (Galician), gu (Gujarati), ha (Bantu), haw (Hawaiian),
he (Hebrew), hi (Hindi), hr (Croatian), ht (Haitian Creole), hu (Hungarian), hy (Armenian), id (Indonesian),
is (Icelandic), it (Italian), iw (<Hebrew>), ja (Japanese), jw (Javanese), ka (Georgian), kk (Kazakh), km (Khmer),
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

sync: Transcription/video synchronization time in seconds (0 <= seconds <= (Step - 3))

segments: Number of segment files for timeshift (2 =< n <= 99).

segment_time: Time for each segment file(1 <= minutes <= 99).


Script and Whisper executable (main), and models directory with at least one archive model, must reside in the same directory.

"""

import json
import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, PhotoImage


def check_terminal_installed(terminal):
   try:
       if terminal == "mlterm":
           result = subprocess.run(["mlterm", "--version"], capture_output=True, text=True)
           mlterm_output = result.stdout
           if "mlterm" in mlterm_output:
               return True
           else:
               return False
       elif terminal in ["lxterm", "xterm"]:
           process = subprocess.run([terminal, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
           return process.returncode == 0
       else:
           process = subprocess.run([terminal, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
           return process.returncode == 0
   except OSError:
       return False

def check_player_installed(player):
   try:
       if player == "smplayer" and subprocess.call(["smplayer", "--help"], stdout=subprocess.DEVNULL,
                                                   stderr=subprocess.DEVNULL) == 0:
           return True
       elif player == "mpv" and subprocess.call(["mpv", "--version"], stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL) == 0:
           return True
       elif player == "none":
           return True
   except OSError:
       return False


# Default options
rPadChars = 100 * " "
default_terminal_option = "gnome-terminal"
default_bash_options = "8 base auto raw"
default_timeshiftactive_option = False
default_timeshift_options = "3 4 10"
default_playeronly_option = False
default_player_option = "mpv"
default_mpv_options = ""
default_override_option = False
terminal = ["gnome-terminal", "konsole", "lxterm", "mate-terminal", "mlterm", "xfce4-terminal", "xterm"]
player = ["none", "smplayer", "mpv"]
models = ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large-v1", "large-v2", "large-v3"]
suffixes = ["-q4_0", "-q4_1", "-q4_2", "-q5_0", "-q5_1", "-q8_0"]

lang_codes = {'auto': 'Autodetect', 'af': 'Afrikaans', 'am': 'Amharic', 'ar': 'Arabic', 'as': 'Assamese',
           'az': 'Azerbaijani', 'be': 'Belarusian', 'bg': 'Bulgarian', 'bn': 'Bengali', 'br': 'Breton',
           'bs': 'Bosnian', 'ca': 'Catalan', 'cs': 'Czech', 'cy': 'Welsh', 'da': 'Danish',
           'de': 'German', 'el': 'Greek', 'en': 'English', 'eo': 'Esperanto', 'es': 'Spanish',
           'et': 'Estonian', 'eu': 'Basque', 'fa': 'Persian', 'fi': 'Finnish', 'fo': 'Faroese',
           'fr': 'French', 'ga': 'Irish', 'gl': 'Galician', 'gu': 'Gujarati', 'ha': 'Bantu',
           'haw': 'Hawaiian', 'he': '[Hebrew]', 'hi': 'Hindi', 'hr': 'Croatian', 'ht': 'Haitian Creole',
           'hu': 'Hungarian', 'hy': 'Armenian', 'id': 'Indonesian', 'is': 'Icelandic', 'it': 'Italian',
           'iw': 'Hebrew', 'ja': 'Japanese', 'jv': 'Javanese', 'ka': 'Georgian', 'kk': 'Kazakh',
           'km': 'Khmer', 'kn': 'Kannada', 'ko': 'Korean', 'ku': 'Kurdish', 'ky': 'Kyrgyz',
           'la': 'Latin', 'lb': 'Luxembourgish', 'lo': 'Lao', 'lt': 'Lithuanian', 'lv': 'Latvian',
           'mg': 'Malagasy', 'mi': 'Maori', 'mk': 'Macedonian', 'ml': 'Malayalam', 'mn': 'Mongolian',
           'mr': 'Marathi', 'ms': 'Malay', 'mt': 'Maltese', 'my': 'Myanmar', 'ne': 'Nepali',
           'nl': 'Dutch', 'nn': 'Nynorsk', 'no': 'Norwegian', 'oc': 'Occitan', 'or': 'Oriya',
           'pa': 'Punjabi', 'pl': 'Polish', 'ps': 'Pashto', 'pt': 'Portuguese', 'ro': 'Romanian',
           'ru': 'Russian', 'sd': 'Sindhi', 'sh': 'Serbo-Croatian', 'si': 'Sinhala', 'sk': 'Slovak',
           'sl': 'Slovenian', 'sn': 'Shona', 'so': 'Somali', 'sq': 'Albanian', 'sr': 'Serbian',
           'su': 'Sundanese', 'sv': 'Swedish', 'sw': 'Swahili', 'ta': 'Tamil', 'te': 'Telugu',
           'tg': 'Tajik', 'th': 'Thai', 'tl': 'Tagalog', 'tr': 'Turkish', 'tt': 'Tatar', 'ug': 'Uighur',
           'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek', 'vi': 'Vietnamese', 'vo': 'Volapuk',
           'wa': 'Walloon', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'zh': 'Chinese',
           'zu': 'Zulu'}

regions = {"Africa": ["af", "am", "ar", "ha", "sn", "so", "sw", "yo", "xh", "zu"],
          "Asia": ["as", "az", "bn", "gu", "hi", "hy", "id", "ja", "jv", "ka", "km", "kn", "ko",
                   "ku", "ky", "lo", "mn", "my", "ne", "or", "pa", "ps", "sd", "si", "ta", "te",
                   "tg", "th", "tl", "tr", "tt", "ug", "ur", "uz", "vi", "zh"],
          "Europe": ["be", "bg", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et",
                     "eu", "fi", "fo", "fr", "ga", "gl", "hr", "hu", "is", "it", "kk", "la", "lb",
                     "lt", "lv", "mk", "mt", "nl", "nn", "no", "oc", "pl", "pt", "ro", "ru", "sh",
                     "sk", "sl", "sq", "sr", "sv", "uk", "wa"],
          "Middle East": ['ar', "fa", "he", 'iw', "yi"],
          "Oceania": ["haw", "mi", "mg"],
          "Americas": ["ht"],
          "World": ["ar", "en", "eo", "es", "de", "fr", "pt", "ru", "zh"]}

terminal_installed = []
for term in terminal:
  if check_terminal_installed(term):
      terminal_installed.append(term)

player_installed = []
for play in player:
  if check_player_installed(play):
      player_installed.append(play)

model_list = models + [model + suffix for model in models for suffix in suffixes]

model_path = "./models/ggml-{}.bin"
models_installed = []
for model in models:
  if os.path.exists(model_path.format(model)):
      models_installed.append(model)

  for suffix in suffixes:
      full_model_name = f"{model}{suffix}"
      if os.path.exists(model_path.format(full_model_name)):
          models_installed.append(full_model_name)


class M3uPlaylistPlayer(tk.Frame):
    def __init__(self, parent, spec, bash):
        super().__init__(parent)
        self.spec = spec
        self.bash_script = bash
        self.current_options = {}
        self.list_number = 0
        self.playlist = []
        self.create_widgets()
        self.populate_playlist()
        self.load_options()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("list_number", "name", "url"), show="headings")
        self.tree.heading("list_number", text="#")
        self.tree.heading("name", text="Channel")
        self.tree.heading("url", text="URL")
        self.tree.column("list_number", width=35, stretch=False, minwidth=15)
        self.tree.column("name", width=200, stretch=True, minwidth=50)
        self.tree.column("url", width=400, stretch=True, minwidth=50)
        self.tree.bind('<Double-Button-1>', self.play_channel)
        self.tree.pack(fill=tk.BOTH, expand=True)

        yscrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=yscrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.load_options)

        self.container_frame = tk.Frame(self)
        self.container_frame.pack(side=tk.LEFT)

        # First Down Frame
        self.options_frame0 = tk.Frame(self.container_frame)
        self.options_frame0.pack(side=tk.TOP, anchor=tk.W)

        # Terminal

        self.terminal_label = tk.Label(self.options_frame0, text="Terminal", padx=10)
        self.terminal_label.pack(side=tk.LEFT)

        self.terminal_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.terminal_frame.pack(side=tk.LEFT)

        self.terminal = tk.StringVar(value="gnome-terminal")

        def update_terminal_button():
            selected_option = self.terminal.get()
            self.terminal_option_menu.configure(text=selected_option)
            self.save_options()

        self.terminal_option_menu = tk.Menubutton(self.terminal_frame, textvariable=self.terminal, indicatoron=True,
                                                  relief="raised")
        self.terminal_option_menu.pack(side=tk.LEFT)

        terminal_menu = tk.Menu(self.terminal_option_menu, tearoff=0)
        self.terminal_option_menu.configure(menu=terminal_menu)

        for term in terminal:
            if term in terminal_installed:
                terminal_menu.add_radiobutton(label=term, value=term, variable=self.terminal,
                                              command=update_terminal_button)
                default_terminal_option = term
            else:
                terminal_menu.add_radiobutton(label=term, value=term, variable=self.terminal,
                                              command=update_terminal_button, state="disabled")

        self.terminal_option_menu.bind("<<MenuSelect>>", lambda e: update_terminal_button())

        # Step_s
        self.step_s_label = tk.Label(self.options_frame0, text="Step(sec)", padx=4)
        self.step_s_label.pack(side=tk.LEFT)

        self.step_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.step_frame.pack(side=tk.LEFT)

        self.save_options_id = None
        self.step_s = tk.StringVar(value="4")
        self.step_s_spinner = tk.Spinbox(self.step_frame, from_=3, to=60, width=2, textvariable=self.step_s,
                                         command=self.schedule_save_options)
        self.step_s_spinner.pack(side=tk.LEFT)

        self.step_s_spinner.bind("<KeyRelease>", self.schedule_save_options)

        # Whisper models
        self.model_label = tk.Label(self.options_frame0, text="Model", padx=4)
        self.model_label.pack(side=tk.LEFT)

        self.model_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.model_frame.pack(side=tk.LEFT)

        self.model = tk.StringVar(value="base")

        def update_model_button():
            selected_option = self.model.get()
            self.model_option_menu.configure(text=selected_option)
            self.save_options()

        self.model_option_menu = tk.Menubutton(self.model_frame, textvariable=self.model, indicatoron=True,
                                               relief="raised")
        self.model_option_menu.pack(side=tk.LEFT)

        model_menu = tk.Menu(self.model_option_menu, tearoff=0)
        self.model_option_menu.configure(menu=model_menu)

        for model in models:
            suffix_menu = tk.Menu(model_menu, tearoff=0)

            if model in models_installed:
                suffix_menu.add_radiobutton(label=model, value=model, variable=self.model, command=update_model_button)
            else:
                suffix_menu.add_radiobutton(label=model, value=model, variable=self.model, command=update_model_button,
                                            state="disabled")

            for suffix in suffixes:
                full_model_name = f"{model}{suffix}"
                if full_model_name in models_installed:
                    suffix_menu.add_radiobutton(label=full_model_name, value=full_model_name, variable=self.model,
                                                command=update_model_button)
                else:
                    suffix_menu.add_radiobutton(label=full_model_name, value=full_model_name, variable=self.model,
                                                command=update_model_button, state="disabled")

            model_menu.add_cascade(label=model, menu=suffix_menu)
        # Regions and their languages
        self.language_label = tk.Label(self.options_frame0, text="Language", padx=4)
        self.language_label.pack(side=tk.LEFT)

        self.language_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.language_frame.pack(side=tk.LEFT)

        self.language = tk.StringVar(value="auto (Autodetect)")

        def update_language_button():
            selected_option = self.language.get()
            self.language_option_menu.configure(text=selected_option)
            self.save_options()

        self.language_option_menu = tk.Menubutton(self.language_frame, textvariable=self.language, indicatoron=True,
                                                  relief="raised")
        self.language_option_menu.pack(side=tk.LEFT)

        language_menu = tk.Menu(self.language_option_menu, tearoff=0)
        self.language_option_menu.configure(menu=language_menu)

        language_menu.add_radiobutton(label="auto (Autodetect)", value="auto (Autodetect)", variable=self.language,
                                      command=update_language_button)

        for region, langs in regions.items():
            sublanguage_menu = tk.Menu(language_menu, tearoff=0)
            for lang in langs:
                lang_name = lang_codes.get(lang)
                full_language_name = f"{lang} ({lang_name})"
                sublanguage_menu.add_radiobutton(label=full_language_name, value=full_language_name,
                                                 variable=self.language, command=update_language_button)
            language_menu.add_cascade(label=region, menu=sublanguage_menu)

        self.language_option_menu["menu"] = language_menu

        self.language_option_menu.bind("<<MenuSelect>>", lambda e: update_language_button())

        # Translate
        self.translate_label = tk.Label(self.options_frame0, text="Translate", padx=4)
        self.translate_label.pack(side=tk.LEFT)

        self.translate_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.translate_frame.pack(side=tk.LEFT)

        self.translate = tk.BooleanVar(value=False)
        self.translate_checkbox = tk.Checkbutton(self.translate_frame, variable=self.translate, onvalue=True,
                                                 offvalue=False, command=self.save_options)
        self.translate_checkbox.pack(side=tk.LEFT)

        # Override
        self.space_label = tk.Label(self.options_frame0, text="", padx=8)
        self.space_label.pack(side=tk.LEFT)

        self.override_label = tk.Label(self.options_frame0, text="Override options")
        self.override_label.pack(side=tk.LEFT)

        self.override_options = tk.BooleanVar()
        self.override_checkbox = tk.Checkbutton(self.options_frame0, variable=self.override_options,
                                                command=self.change_override)
        self.override_checkbox.pack(side=tk.LEFT)

        # Second Down Frame
        self.options_frame1 = tk.Frame(self.container_frame)
        self.options_frame1.pack(side=tk.TOP, anchor=tk.W)

        # Quality
        quality = ["raw", "upper", "lower"]

        self.quality_label = tk.Label(self.options_frame1, text="Video Quality", padx=10)
        self.quality_label.pack(side=tk.LEFT)

        self.quality_frame = tk.Frame(self.options_frame1, highlightthickness=1, highlightbackground="black")
        self.quality_frame.pack(side=tk.LEFT)

        self.quality = tk.StringVar(value="raw")

        def update_quality_button():
            selected_option = self.quality.get()
            self.quality_option_menu.configure(text=selected_option)
            self.save_options()

        self.quality_option_menu = tk.Menubutton(self.quality_frame, textvariable=self.quality, indicatoron=True,
                                                 relief="raised")
        self.quality_option_menu.pack(side=tk.LEFT)

        quality_menu = tk.Menu(self.quality_option_menu, tearoff=0)
        self.quality_option_menu.configure(menu=quality_menu)

        for qua in quality:
            quality_menu.add_radiobutton(label=qua, value=qua, variable=self.quality, command=update_quality_button)

        self.quality_option_menu.bind("<<MenuSelect>>", lambda e: update_quality_button())

        # Player Only
        self.playeronly_label = tk.Label(self.options_frame1, text="Player Only", padx=4)
        self.playeronly_label.pack(side=tk.LEFT)

        self.playeronly_frame = tk.Frame(self.options_frame1, highlightthickness=1, highlightbackground="black")
        self.playeronly_frame.pack(side=tk.LEFT)

        self.playeronly = tk.BooleanVar(value=False)
        self.playeronly_checkbox = tk.Checkbutton(self.playeronly_frame, variable=self.playeronly, onvalue=True,
                                                  offvalue=False, command=self.save_options)
        self.playeronly_checkbox.pack(side=tk.LEFT)

        # Players
        self.player_label = tk.Label(self.options_frame1, text="Player", padx=4)
        self.player_label.pack(side=tk.LEFT)

        self.player_frame = tk.Frame(self.options_frame1, highlightthickness=1, highlightbackground="black")
        self.player_frame.pack(side=tk.LEFT)

        self.player = tk.StringVar(value="smplayer")

        def update_player_button():
            selected_option = self.player.get()
            self.player_option_menu.configure(text=selected_option)
            self.save_options()

        self.player_option_menu = tk.Menubutton(self.player_frame, textvariable=self.player, indicatoron=True,
                                                relief="raised")
        self.player_option_menu.pack(side=tk.LEFT)

        player_menu = tk.Menu(self.player_option_menu, tearoff=0)
        self.player_option_menu.configure(menu=player_menu)

        for play in player:
            if play in player_installed:
                player_menu.add_radiobutton(label=play, value=play, variable=self.player, command=update_player_button)
                default_player_option = play
            else:
                player_menu.add_radiobutton(label=play, value=play, variable=self.player, command=update_player_button,
                                            state="disabled")

        self.player_option_menu.bind("<<MenuSelect>>", lambda e: update_player_button())

        # Player Options
        self.mpv_options_label = tk.Label(self.options_frame1, text="Player Options", padx=4)
        self.mpv_options_label.pack(side=tk.LEFT)

        self.mpv_options_entry = tk.Entry(self.options_frame1, width=50)
        self.mpv_options_entry.insert(0, self.current_options.get("mpv_options", ""))
        self.mpv_options_entry.pack(side=tk.LEFT)

        self.mpv_options_entry.bind("<KeyRelease>", self.schedule_save_options)

        self.mpv_fg = self.mpv_options_entry.cget("fg")
        self.mpv_bg = self.mpv_options_entry.cget("bg")


        # Third Down Frame

        if subprocess.call(["vlc", "--version"], stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL) == 0:
            self.options_frame2 = tk.LabelFrame(self.container_frame, text="Only Raw + VLC player - Large files will be stored in temp directory!!!", padx=10, pady=2)
        else:
            self.options_frame2 = tk.LabelFrame(self.container_frame, text="VLC player not installed for Timeshift!!!", padx=10, pady=2)

        self.options_frame2.pack(fill="both", expand=True, padx=10, pady=2)

        # Timeshift
        self.timeshiftactive_label = tk.Label(self.options_frame2, text="Timeshift", padx=10)
        self.timeshiftactive_label.pack(side=tk.LEFT)

        self.timeshiftactive_frame = tk.Frame(self.options_frame2, highlightthickness=1, highlightbackground="black")
        self.timeshiftactive_frame.pack(side=tk.LEFT)

        self.timeshiftactive = tk.BooleanVar(value=False)
        self.timeshiftactive_checkbox = tk.Checkbutton(self.timeshiftactive_frame, variable=self.timeshiftactive, onvalue=True,
                                                 offvalue=False, command=self.save_options)
        self.timeshiftactive_checkbox.pack(side=tk.LEFT)

        # Synchronization
        self.sync_label = tk.Label(self.options_frame2, text="Synchronization(sec)", padx=4)
        self.sync_label.pack(side=tk.LEFT)

        self.sync_frame = tk.Frame(self.options_frame2, highlightthickness=1, highlightbackground="black")
        self.sync_frame.pack(side=tk.LEFT)

        self.sync_options_id = None
        self.sync = tk.StringVar(value="3")
        self.sync_spinner = tk.Spinbox(self.sync_frame, from_=0, to=57, width=2, textvariable=self.sync,
                                         command=self.schedule_save_options)
        self.sync_spinner.pack(side=tk.LEFT)

        self.sync_spinner.bind("<KeyRelease>", self.schedule_save_options)

        # Segments
        self.segments_label = tk.Label(self.options_frame2, text="Segments", padx=4)
        self.segments_label.pack(side=tk.LEFT)

        self.segments_frame = tk.Frame(self.options_frame2, highlightthickness=1, highlightbackground="black")
        self.segments_frame.pack(side=tk.LEFT)

        self.save_options_id = None
        self.segments = tk.StringVar(value="4")
        self.segments_spinner = tk.Spinbox(self.segments_frame, from_=2, to=99, width=2, textvariable=self.segments,
                                         command=self.schedule_save_options)
        self.segments_spinner.pack(side=tk.LEFT)

        self.segments_spinner.bind("<KeyRelease>", self.schedule_save_options)

        # Segment time
        self.segment_time_label = tk.Label(self.options_frame2, text="Segment Time(minutes)", padx=4)
        self.segment_time_label.pack(side=tk.LEFT)

        self.segment_time_frame = tk.Frame(self.options_frame2, highlightthickness=1, highlightbackground="black")
        self.segment_time_frame.pack(side=tk.LEFT)

        self.segment_time_options_id = None
        self.segment_time = tk.StringVar(value="10")
        self.segment_time_spinner = tk.Spinbox(self.segment_time_frame, from_=1, to=99, width=2, textvariable=self.segment_time,
                                         command=self.schedule_save_options)
        self.segment_time_spinner.pack(side=tk.LEFT)

        self.segment_time_spinner.bind("<KeyRelease>", self.schedule_save_options)


        # Buttons
        self.options_frame3 = tk.Frame(self.container_frame)
        self.options_frame3.pack(side=tk.TOP, anchor=tk.W)

        self.options_frame3 = tk.Frame(self.container_frame)
        self.options_frame3.pack(side=tk.TOP, anchor=tk.W)

        self.add_label = tk.Label(self.options_frame3, text="Channel", padx=10)
        self.add_label.pack(side=tk.LEFT)

        self.add_button = tk.Button(self.options_frame3, text="Add", command=self.add_channel)
        self.add_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(self.options_frame3, text="Delete", command=self.delete_channel)
        self.delete_button.pack(side=tk.LEFT)

        self.edit_button = tk.Button(self.options_frame3, text="Edit", command=self.edit_channel)
        self.edit_button.pack(side=tk.LEFT)

        self.load_label = tk.Label(self.options_frame3, text="Playlist", padx=10)
        self.load_label.pack(side=tk.LEFT)

        self.load_button = tk.Button(self.options_frame3, text="Load", command=self.load_playlist)
        self.load_button.pack(side=tk.LEFT)

        self.append_button = tk.Button(self.options_frame3, text="Append", command=self.append_playlist)
        self.append_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(self.options_frame3, text="Save", command=self.save_playlist)
        self.save_button.pack(side=tk.LEFT)

        self.about_label = tk.Label(self.options_frame3, text="", padx=20)
        self.about_label.pack(side=tk.LEFT)

        self.about_button = tk.Button(self.options_frame3, text="About", command=self.show_about_window)
        self.about_button.pack(side=tk.LEFT)


    def populate_playlist(self, filename=None):
        if filename is None:
            filename = f'playlist_{self.spec}.m3u'
        try:
            with open(filename, "r", encoding='utf-8') as file:
                lines = file.readlines()

            for i, line in enumerate(lines):
                if line.startswith("#EXTINF"):
                    name = line[line.rfind(",") + 1:].strip()
                    url = None

                    for j in range(i + 1, len(lines)):
                        url_line = lines[j].strip()
                        if url_line and not url_line.startswith("#"):
                            url = url_line
                            break

                    if url:
                        list_number = len(self.playlist) + 1
                        self.tree.insert("", "end", values=(list_number, name, url))
                        self.playlist.append((name, url))
        except FileNotFoundError:
            simpledialog.messagebox.showerror("File Not Found",
                                              f"The default playlist_{self.spec}.m3u file was not found.")

    def widgets_updates(self):
        terminal_option = self.current_options["terminal_option"]
        bash_options = self.current_options["bash_options"]
        playeronly_option = self.current_options["playeronly_option"]
        player_option = self.current_options["player_option"]
        mpv_options = self.current_options["mpv_options"]
        timeshiftactive_option = self.current_options["timeshiftactive_option"]
        timeshift_options = self.current_options["timeshift_options"]

        self.terminal_frame.config(highlightthickness=1, highlightbackground="black")
        self.step_frame.config(highlightthickness=1, highlightbackground="black")
        self.model_frame.config(highlightthickness=1, highlightbackground="black")
        self.language_frame.config(highlightthickness=1, highlightbackground="black")
        self.translate_frame.config(highlightthickness=1, highlightbackground="black")
        self.quality_frame.config(highlightthickness=1, highlightbackground="black")
        self.playeronly_frame.config(highlightthickness=1, highlightbackground="black")
        self.player_frame.config(highlightthickness=1, highlightbackground="black")
        self.mpv_options_entry.config(highlightthickness=1, highlightbackground="black")
        self.timeshiftactive_frame.config(highlightthickness=1, highlightbackground="black")
        self.sync_frame.config(highlightthickness=1, highlightbackground="black")
        self.segments_frame.config(highlightthickness=1, highlightbackground="black")
        self.segment_time_frame.config(highlightthickness=1, highlightbackground="black")

        if not self.override_options.get():
            self.mpv_options_entry.config(fg=self.mpv_fg, bg=self.mpv_bg, insertbackground=self.mpv_fg)
            selection = self.tree.focus()
            if selection:
                url = self.tree.item(selection, "values")[2]
                if url in self.current_options:
                    terminal_option = self.current_options[url].get("terminal_option", "")
                    bash_options = self.current_options[url].get("bash_options", "")
                    playeronly_option = self.current_options[url].get("playeronly_option", "")
                    player_option = self.current_options[url].get("player_option", "")
                    mpv_options = self.current_options[url].get("mpv_options", "")
                    timeshiftactive_option = self.current_options[url].get("timeshiftactive_option", "")
                    timeshift_options = self.current_options[url].get("timeshift_options", "")

                    self.terminal_frame.config(highlightthickness=1, highlightbackground="red")
                    self.step_frame.config(highlightthickness=1, highlightbackground="red")
                    self.model_frame.config(highlightthickness=1, highlightbackground="red")
                    self.language_frame.config(highlightthickness=1, highlightbackground="red")
                    self.translate_frame.config(highlightthickness=1, highlightbackground="red")
                    self.quality_frame.config(highlightthickness=1, highlightbackground="red")
                    self.playeronly_frame.config(highlightthickness=1, highlightbackground="red")
                    self.player_frame.config(highlightthickness=1, highlightbackground="red")
                    self.mpv_options_entry.config(highlightthickness=1, highlightbackground="red")
                    self.timeshiftactive_frame.config(highlightthickness=1, highlightbackground="red")
                    self.sync_frame.config(highlightthickness=1, highlightbackground="red")
                    self.segments_frame.config(highlightthickness=1, highlightbackground="red")
                    self.segment_time_frame.config(highlightthickness=1, highlightbackground="red")
        else:
            self.mpv_options_entry.config(fg=self.mpv_bg, bg=self.mpv_fg, insertbackground=self.mpv_bg)

        self.terminal_option_menu.unbind("<<MenuSelect>>")
        self.terminal.set(terminal_option)
        self.terminal_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())

        if not terminal_option in terminal_installed:
            err_message = f"Warning: Terminal {terminal_option} was not found. Please install it" \
                          f" or choose other terminal."
            simpledialog.messagebox.showerror("Terminal Not Installed", err_message)

        self.translate.set(False)

        options_list = bash_options.split()
        while options_list:
            option = options_list.pop(0)
            if option.isdigit() and (3 <= int(option) <= 60):
                self.step_s.set(option)
                self.step_s_spinner.update()
            elif option == "translate":
                self.translate.set(True)
            elif option in ["raw", "upper", "lower"]:
                self.quality_option_menu.unbind("<<MenuSelect>>")
                self.quality.set(option)
                self.quality_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
            elif option in model_list:
                self.model_option_menu.unbind("<<MenuSelect>>")
                self.model.set(option)
                self.model_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
                if not option in models_installed:
                    model_path = "./models/ggml-{}.bin".format(option)
                    err_message = f"Warning: File for model {option} was not found. " \
                                  f"Please install it in {model_path} or choose other model."
                    simpledialog.messagebox.showerror("Model Not Installed", err_message)
            elif option in lang_codes:
                self.language_option_menu.unbind("<<MenuSelect>>")
                lang_name = lang_codes.get(option)
                full_language_name = f"{option} ({lang_name})"
                self.language.set(full_language_name)
                self.language_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
            else:
                simpledialog.messagebox.showerror("Wrong option",
                                                  f"Wrong option {option} found, try again after deleting"
                                                  f" config_{self.spec}.json file")

        options_list = timeshift_options.split()
        option = options_list.pop(0)

        step_s_str = self.step_s.get()
        if step_s_str.isdigit():
            step_s_value = int(step_s_str)
        else:
            step_s_value = 0

        if option.isdigit() and (0 <= int(option) <= step_s_value - 3) and (step_s_value >= 3):
            self.sync.set(option)
            self.sync_spinner.update()
        else:
                simpledialog.messagebox.showerror("Wrong option",
                                                  f"Wrong option {option} found, try again after deleting"
                                                  f" config_{self.spec}.json file")
        option = options_list.pop(0)
        if option.isdigit() and (2 <= int(option) <= 99):
            self.segments.set(option)
            self.segments_spinner.update()
        else:
                simpledialog.messagebox.showerror("Wrong option",
                                                  f"Wrong option {option} found, try again after deleting"
                                                  f" config_{self.spec}.json file")
        option = options_list.pop(0)
        if option.isdigit() and (1 <= int(option) <= 99):
            self.segment_time.set(option)
            self.segment_time_spinner.update()
        else:
                simpledialog.messagebox.showerror("Wrong option",
                                                  f"Wrong option {option} found, try again after deleting"
                                                  f" config_{self.spec}.json file")


        self.playeronly.set(playeronly_option)
        self.player_option_menu.unbind("<<MenuSelect>>")
        self.player.set(player_option)
        self.player_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
        if not player_option in player_installed:
            err_message = f"Warning: Video player {player_option} was not found. Please install it " \
                          f"or choose other video player."
            simpledialog.messagebox.showerror("Video Player Not Installed", err_message)

        self.mpv_options_entry.delete(0, tk.END)
        self.mpv_options_entry.insert(0, mpv_options)
        self.timeshiftactive.set(timeshiftactive_option)
        if not subprocess.call(["vlc", "--version"], stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL) == 0:
            err_message = f"Warning: Video player {player_option} was not found. Please install it."
            simpledialog.messagebox.showerror("Timeshift Player Not Installed", err_message)

    def play_channel(self, event):
        region = self.tree.identify_region(event.x, event.y)

        if region == "cell":
            item = self.tree.selection()[0]
            url = self.tree.item(item, "values")[2]
            mpv_options = self.mpv_options_entry.get()

            language_text = self.language.get()
            language_cleaned = language_text.split('(')[0].strip()

            if self.translate.get():
                translate_value = " translate"
            else:
                translate_value = ""

            print("Playing channel:", url)

            videoplayer = self.player.get()
            quality = self.quality.get()

            if self.timeshiftactive.get():
                if subprocess.call(["vlc", "--version"], stdout=subprocess.DEVNULL,
                                                     stderr=subprocess.DEVNULL) == 0:
                    mpv_options = f"[vlc {mpv_options}]"
                else:
                    err_message = f"Warning: Video player {player_option} was not found. Please install it."
                    simpledialog.messagebox.showerror("Timeshift Player Not Installed", err_message)

            # Try launching smplayer, mpv, or mplayer
            elif self.playeronly.get() or quality == "raw":
                if videoplayer == "smplayer" and videoplayer in player_installed:
                    subprocess.Popen(["smplayer", url, mpv_options])
                elif videoplayer == "mpv" and videoplayer in player_installed:
                    subprocess.Popen(["mpv", url, mpv_options])
                elif videoplayer == "none":
                    if self.playeronly.get():
                        mpv_options = ""
                        print("None video player selected.")
                        simpledialog.messagebox.showerror("Error", "None video player selected.")
                else:
                    mpv_options = ""
                    print(f"No {videoplayer} video player found.")
                    simpledialog.messagebox.showerror("Error", f"No {videoplayer} video player found.")

            if quality == "raw":
                videoplayer = "none"

            # Try launching gnome-terminal, konsole, lxterm, mlterm, xfce4-terminal, xterm
            terminal = self.terminal.get()
            bash_options = self.step_s.get() + " " + self.model.get() + " " + language_cleaned + \
                           translate_value + " " + quality
            if self.timeshiftactive.get():
                bash_options = bash_options + " timeshift sync " + self.sync.get() + " segments " + self.segments.get() + " segment_time " + self.segment_time.get()
            if self.spec == "streamlink":
                bash_options = bash_options + " streamlink"
            if self.spec == "yt-dlp":
                bash_options = bash_options + " yt-dlp"
            print("Script Options:", bash_options)

            if not self.playeronly.get():
                url = '"' + url + '"'
                if self.timeshiftactive.get():
                    if subprocess.call(["vlc", "--version"], stdout=subprocess.DEVNULL,
                                                         stderr=subprocess.DEVNULL) == 0:
                        mpv_options = f"[vlc {mpv_options}]"
                    else:
                        err_message = f"Warning: Video player {player_option} was not found. Please install it."
                        simpledialog.messagebox.showerror("Timeshift Player Not Installed", err_message)
                elif videoplayer == "smplayer" and videoplayer in player_installed:
                    mpv_options = f"[smplayer {mpv_options}]"
                elif videoplayer == "mpv" and videoplayer in player_installed:
                    mpv_options = f"[mpv {mpv_options}]"
                elif videoplayer == "none":
                    mpv_options = f"[none]"
                else:
                    mpv_options = ""
                    print(f"No {videoplayer} video player found.")
                    simpledialog.messagebox.showerror("Error", f"No {videoplayer} video player found.")

                if os.path.exists(self.bash_script):
                    try:
                        if terminal == "gnome-terminal" and subprocess.run(
                                ["gnome-terminal", "--version"]).returncode == 0:
                            subprocess.Popen(["gnome-terminal", "--tab", "--", "/bin/bash", "-c",
                                              f"{self.bash_script} {url} {bash_options} {mpv_options}; exec /bin/bash -i"])
                        elif terminal == "konsole" and subprocess.run(["konsole", "--version"]).returncode == 0:
                            subprocess.Popen(["konsole", "--noclose", "-e", f"{self.bash_script} {url} {bash_options} "
                                                                            f"{mpv_options}"])
                        elif terminal == "lxterm" and subprocess.run(["lxterm", "-version"]).returncode == 0:
                            subprocess.Popen(["lxterm", "-hold", "-e", f"{self.bash_script} {url} {bash_options} "
                                                                       f"{mpv_options}"])
                        elif terminal == "mate-terminal" and subprocess.run(
                                ["mate-terminal", "--version"]).returncode == 0:
                            subprocess.Popen(["mate-terminal", "-e", f"{self.bash_script} {url} {bash_options} "
                                                                     f"{mpv_options}"])
                        elif terminal == "mlterm":
                            result = subprocess.run(["mlterm", "--version"], capture_output=True, text=True)
                            mlterm_output = result.stdout
                            if "mlterm" in mlterm_output:
                                subprocess.Popen(["bash", "-c", f"mlterm -e {self.bash_script} {url} {bash_options} "
                                                                f"{mpv_options} & sleep 2 ; disown"])
                        elif terminal == "xfce4-terminal" and subprocess.run(
                                ["xfce4-terminal", "--version"]).returncode == 0:
                            subprocess.Popen(["xfce4-terminal", "--hold", "-e", f"{self.bash_script} {url} "
                                                                                f"{bash_options} {mpv_options}"])
                        elif terminal == "xterm" and subprocess.run(["xterm", "-version"]).returncode == 0:
                            subprocess.Popen(["xterm", "-e", f"{self.bash_script} {url} {bash_options}"
                                                                      f" {mpv_options}"])
                        else:
                            print("No compatible terminal found.")
                            simpledialog.messagebox.showerror("Error", "No compatible terminal found.")
                    except OSError as e:
                        print("Error executing command:", e)
                        simpledialog.messagebox.showerror("Error", "Error executing command.")
                else:
                    print("Script does not exist.")
                    simpledialog.messagebox.showerror("Error", "Script does not exist.")

    # Function to add a channel
    def add_channel(self):
        name = simpledialog.askstring("Add Channel", "Channel Name:" + rPadChars)
        url = simpledialog.askstring("Add Channel", "Channel URL:" + rPadChars)
        if name and url:
            selection = self.tree.selection()
            # Update list number for new item
            if selection:
                index = self.tree.index(selection[0])
                index += 1
            else:
                index = len(self.tree.get_children()) + 1

            # Add the channel to the list
            self.tree.insert("", index, values=(index, name, url))

            # iterate over all items and update their list_number
            for i, item in enumerate(self.tree.get_children()):
                self.tree.item(item, values=(i + 1,) + tuple(self.tree.item(item)['values'][1:]))

            # Show a success message
            simpledialog.messagebox.showinfo("Success", "Channel added successfully. Don't forget to save the playlist.")
        else:
            # Show an error message if either name or URL is not provided
            simpledialog.messagebox.showerror("Error", "Both name and URL are required.")



    # Function to delete a channel
    def delete_channel(self):
        selection = self.tree.selection()
        if selection:
            self.tree.delete(selection[0])
            # iterate over all items and update their list_number
            for i, item in enumerate(self.tree.get_children()):
                self.tree.item(item, values=(i + 1,) + tuple(self.tree.item(item)['values'][1:]))

            # Show a success message
            simpledialog.messagebox.showinfo("Success", "Channel deleted successfully. Don't forget to save the playlist.")
        else:
            simpledialog.messagebox.showerror("Error", "Select a channel to delete")

    # Function to edit a channel
    def edit_channel(self):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            list_number, name, url = self.tree.item(item, "values")
            name = simpledialog.askstring("Edit Channel", "Channel Name:" + rPadChars,
                                          initialvalue=self.tree.item(item, "values")[1])
            url = simpledialog.askstring("Edit Channel", "Channel URL:" + rPadChars,
                                         initialvalue=self.tree.item(item, "values")[2])
            if name and url:
                self.tree.item(item, values=(list_number, name, url))

                # Show a success message
                simpledialog.messagebox.showinfo("Success", "Channel edited successfully. Don't forget to save the playlist.")
            else:
                # Show an error message if either name or URL is not provided
                simpledialog.messagebox.showerror("Error", "Both name and URL are required.")
        else:
            simpledialog.messagebox.showerror("Error", "Select a channel to edit")

    # Function to load a playlist
    def load_playlist(self):
        filename = filedialog.askopenfilename(filetypes=[("Playlist Files", "*.m3u")])
        if filename:
            self.tree.delete(*self.tree.get_children())
            self.playlist = []
            self.populate_playlist(filename)

    # Function to append a playlist
    def append_playlist(self):
        filename = filedialog.askopenfilename(filetypes=[("Playlist Files", "*.m3u")])
        if filename:
            self.populate_playlist(filename)
            # iterate over all items and update their list_number
            for i, item in enumerate(self.tree.get_children()):
                self.tree.item(item, values=(i + 1,) + tuple(self.tree.item(item)['values'][1:]))

    # Function to save a playlist
    def save_playlist(self):
        filename = filedialog.asksaveasfilename(filetypes=[("Playlist Files", "*.m3u")])
        if filename:
            with open(filename, "w") as file:
                for item in self.tree.get_children():
                    list_number, name, url = self.tree.item(item, "values")
                    file.write(f"#EXTINF:-1,{name}\n{url}\n")

    # Functions to load and save config.json
    def load_options(self, event=None):
        self.load_config()
        override_option = self.current_options["override_option"]
        self.override_options.set(override_option)

        self.widgets_updates()

    def load_config(self):
        try:
            config_file = f'config_{self.spec}.json'
            self.current_options["terminal_option"] = default_terminal_option
            self.current_options["bash_options"] = default_bash_options
            self.current_options["playeronly_option"] = default_playeronly_option
            self.current_options["player_option"] = default_player_option
            self.current_options["mpv_options"] = default_mpv_options
            self.current_options["override_option"] = default_override_option
            self.current_options["timeshiftactive_option"] = default_timeshiftactive_option
            self.current_options["timeshift_options"] = default_timeshift_options

            if os.path.exists(config_file):
                with open(config_file, "r") as file:
                    self.current_options = json.load(file)
        except:
            simpledialog.messagebox.showerror("Wrong option",
                                              f"Wrong option found, try again after deleting"
                                              f" config_{self.spec}.json file")

    def schedule_save_options(self, event=None):
        if self.save_options_id:
            self.after_cancel(self.save_options_id)
        self.save_options_id = self.after(1000, self.save_options)

    def save_options(self, event=None):
        self.terminal_frame.config(highlightthickness=1, highlightbackground="black")
        self.step_frame.config(highlightthickness=1, highlightbackground="black")
        self.model_frame.config(highlightthickness=1, highlightbackground="black")
        self.language_frame.config(highlightthickness=1, highlightbackground="black")
        self.translate_frame.config(highlightthickness=1, highlightbackground="black")
        self.quality_frame.config(highlightthickness=1, highlightbackground="black")
        self.playeronly_frame.config(highlightthickness=1, highlightbackground="black")
        self.player_frame.config(highlightthickness=1, highlightbackground="black")
        self.mpv_options_entry.config(highlightthickness=1, highlightbackground="black")
        self.timeshiftactive_frame.config(highlightthickness=1, highlightbackground="black")
        self.sync_frame.config(highlightthickness=1, highlightbackground="black")
        self.segments_frame.config(highlightthickness=1, highlightbackground="black")
        self.segment_time_frame.config(highlightthickness=1, highlightbackground="black")

        terminal_option = self.terminal.get()

        language_text = self.language.get()
        language_cleaned = language_text.split('(')[0].strip()
        if self.translate.get():
            translate_value = " translate"
        else:
            translate_value = ""

        bash_options = self.step_s.get() + " " + self.model.get() + " " + language_cleaned + \
                       translate_value + " " + self.quality.get()

        playeronly_option = self.playeronly.get()
        player_option = self.player.get()
        mpv_options = self.mpv_options_entry.get()
        timeshiftactive_option = self.timeshiftactive.get()

        sync_str = self.sync.get()
        step_s_str = self.step_s.get()
        if sync_str.isdigit() and step_s_str.isdigit():
            sync_value = int(sync_str)
            step_s_value = int(step_s_str)
            if sync_value > step_s_value - 3:
                self.sync.set(step_s_value - 3)
        else:
            simpledialog.messagebox.showerror("Invalid Integer", f"The value is not a valid integer.")


        timeshift_options = self.sync.get() + " " + self.segments.get() + " " + self.segment_time.get()

        if self.override_options.get():
            self.current_options["terminal_option"] = terminal_option
            self.current_options["bash_options"] = bash_options
            self.current_options["playeronly_option"] = playeronly_option
            self.current_options["player_option"] = player_option
            self.current_options["mpv_options"] = mpv_options
            self.current_options["timeshiftactive_option"] = timeshiftactive_option
            self.current_options["timeshift_options"] = timeshift_options
            self.current_options["override_option"] = True
        else:
            selection = self.tree.focus()
            if selection:
                self.terminal_frame.config(highlightthickness=1, highlightbackground="red")
                self.step_frame.config(highlightthickness=1, highlightbackground="red")
                self.model_frame.config(highlightthickness=1, highlightbackground="red")
                self.language_frame.config(highlightthickness=1, highlightbackground="red")
                self.translate_frame.config(highlightthickness=1, highlightbackground="red")
                self.quality_frame.config(highlightthickness=1, highlightbackground="red")
                self.playeronly_frame.config(highlightthickness=1, highlightbackground="red")
                self.player_frame.config(highlightthickness=1, highlightbackground="red")
                self.mpv_options_entry.config(highlightthickness=1, highlightbackground="red")
                self.timeshiftactive_frame.config(highlightthickness=1, highlightbackground="red")
                self.sync_frame.config(highlightthickness=1, highlightbackground="red")
                self.segments_frame.config(highlightthickness=1, highlightbackground="red")
                self.segment_time_frame.config(highlightthickness=1, highlightbackground="red")

                url = self.tree.item(selection, "values")[2]
                self.current_options[url] = {}
                self.current_options[url]["terminal_option"] = terminal_option
                self.current_options[url]["bash_options"] = bash_options
                self.current_options[url]["playeronly_option"] = playeronly_option
                self.current_options[url]["player_option"] = player_option
                self.current_options[url]["mpv_options"] = mpv_options
                self.current_options[url]["timeshiftactive_option"] = timeshiftactive_option
                self.current_options[url]["timeshift_options"] = timeshift_options


        self.save_config()

    def save_config(self):
        config_file = f'config_{self.spec}.json'
        with open(config_file, "w") as file:
            json.dump(self.current_options, file)

    # Change override
    def change_override(self):
        self.load_config()
        self.current_options["override_option"] = self.override_options.get()

        self.widgets_updates()

        self.save_config()

    # Function About
    @staticmethod
    def show_about_window():
        simpledialog.messagebox.showinfo("About",
                                         "playlist4whisper Version: 2.08\n\nCopyright (C) 2023 Antonio R.\n\n"
                                         "Playlist for livestream_video.sh, "
                                         "it plays online videos and transcribes them. "
                                         "A simple GUI using Python and Tkinter library. "
                                         "Based on whisper.cpp.\n\n"
                                         "License: GPL 3.0\n\n"
                                         "This program comes with ABSOLUTELY NO WARRANTY."
                                         "This is free software, and you are welcome to redistribute it "
                                         "under certain conditions; see source code for details.")


class MainApplication:
    main_window = tk.Tk()
    main_window.title("playlist4whisper")
    main_window.geometry("900x800")

    icon = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABGdBTUEAALGPC" \
           "/xhBQAAAYRpQ0NQSUNDIHByb2ZpbGUAACiRfZE9SMNAHMVfv1C04mAHEYcM1cmCaBHdtApFqBBqhVYdTC79giYNSYqLo" \
           "+BacPBjserg4qyrg6sgCH6AuLo4KbpIif9LCi1iPDjux7t7j7t3gL9RYaoZHAdUzTLSyYSQza0KXa8IIYhexDEjMVOfE" \
           "8UUPMfXPXx8vYvxLO9zf44+JW8ywCcQzzLdsIg3iKc2LZ3zPnGElSSF+Jx4zKALEj9yXXb5jXPRYT/PjBiZ9DxxhFgod" \
           "rDcwaxkqMRx4qiiapTvz7qscN7irFZqrHVP/sJwXltZ5jrNYSSxiCWIECCjhjIqsBCjVSPFRJr2Ex7+IccvkksmVxmMH" \
           "AuoQoXk+MH/4He3ZmFywk0KJ4DQi21/jABdu0Czbtvfx7bdPAECz8CV1vZXG8D0J+n1thY9Avq3gYvrtibvAZc7wOCTL" \
           "hmSIwVo+gsF4P2MvikHDNwCPWtub619nD4AGeoqdQMcHAKjRcpe93h3d2dv/55p9fcDs4VywQjulqoAAAAGYktHRAAAA" \
           "AAAAPlDu38AAAAJcEhZcwAADdcAAA3XAUIom3gAAAAHdElNRQfnBQQLNjFUgOcTAAAD0klEQVR42u2b229MURTGf0ZbL" \
           "Ykqo3VphXqgIqkmXlwiLkGJS73wQhBFIuJFhEcSiVtCSjzwD/DWJsgglAckDU2lCYKKS2ijcal2OqaqUw9nT3Ls7nNme" \
           "mbmzJ4zXclOMz1r7z3fd9Y6a+111kCWy6gE5hZphqUbGEgVAaVADbARmAeUALmaETAAdAJtwC2gHniT6KIlwGXgDzCYY" \
           "SMCXAPKnYJfDfzIQODyCAM7h+sCu4GrQI7F9UGgSzMXGA+Mtrl+HDgRz0KrgH4Fk6+AQ8BsDf0fAb4MqAWaLKxhV6xF/" \
           "MB3aVI/cNjGGnSNbjuAoMIdKuwmXpAm/BVP/kyVhUCPhKnBSrlYMGRWPuqBXGerwhWqVIp7JKU2IM8jCd9DCdtJlVKDp" \
           "HTMQxnvNgnbc5XSS0mp0kMEFErYQiqlLkmp0MFGU4FFmpIgJ3VFquTGPJzIAjH3EbBcMwLeSfjKAXwp2mwJ8EBTIv4TX" \
           "4rXjxJxW1fX8Lm0z1rgibCIFdlIgNkiGoE7wOJsICBi8f81wGMdiEg1Aa3AUuBmDCK0cI1khsHoaJHM/0aM4kUqiVCGQ" \
           "TcJSDcR2hCQLiK0I8BtIrQlICrLRIi0I+JuAlFDewLMRDTFQURlMghwOxGKJX5gJTDXRqcTuE8SXnroZAHFwFmGFjHN4" \
           "wtGVTrfSy7gx6jX/7IB/hWjNlngpYegm8C1IiAdwLUgIJ3A00rAWxcebloTMJjGOx4XAel439cOnMF4+xxOd+LhJgGdw" \
           "HngIvBbl8wrJ9vuuJsEaHnH7QiISGcDn01NLxOBy+eeIR1lHdJTssTBJuNcCGdOJSThK5BZ6ZAmVDjYpFdHPwdmSuH2Z" \
           "9Q6zQQ0S5O24B2pkT43q5Q2SCbSA0zxAPh84KOE7aCVYrukWE9i7bQ6iNz3FMJ4ja+UfYqU9RL2/Xc6yxEFnlOxwqKqH" \
           "ncPo0c4U6QMuK7A8R6p8UNl3tOAp+KvHDcbgYA4WIRsvkALRr9hvJKLUR7PSdDXZ2C0+FYrwnFQ7NEaz2LzBVtO+3Or4" \
           "/zSecDeBPeKZ3zDQaPGZIzycyoIyAP2Ax9IfbP0M4z2XseyXrhEMggYAxwAPrkA/DWwnRil/+GEuFkYbbNzMH5AMdZ0r" \
           "QqYZPq8DqMtxuyftaIAUmqxfh/Gq/KIwxsVFtls9AcTL9x86gYsLCBPhNbPNneqD7hiQ0xGiEzApjiAhwXw6V7ItQMKc" \
           "FbAe8Vx2QtptiUBqhEEzjk8Zmc0AUGgzi7/9ioB3SLv9pMFEpCO0XVeNXU7ArqB08BEslA2AxMYkREZkUyTf3yN/Z4aq" \
           "slDAAAAAElFTkSuQmCC"

    main_window.iconphoto(True, PhotoImage(data=icon))

    script = "./livestream_video.sh"

    tab_control = ttk.Notebook(main_window)

    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)
    tab3 = ttk.Frame(tab_control)
    tab4 = ttk.Frame(tab_control)
    tab5 = ttk.Frame(tab_control)

    tab_control.add(tab1, text="IPTV", compound="left")
    tab_control.add(tab2, text="YouTube", compound="left")
    tab_control.add(tab3, text="Twitch", compound="left")
    tab_control.add(tab4, text="streamlink", compound="left")
    tab_control.add(tab5, text="yt-dlp", compound="left")

    canvas1 = tk.Canvas(tab1, width=25, height=80, bg='black', highlightthickness=0)
    canvas1.pack(side=tk.LEFT, fill=tk.Y)
    canvas1.create_text(15, 40, text='IPTV', angle=90, fill='white', anchor='center')

    canvas2 = tk.Canvas(tab2, width=25, height=80, bg='#ff0000', highlightthickness=0)
    canvas2.pack(side=tk.LEFT, fill=tk.Y)
    canvas2.create_text(15, 40, text='YouTube', angle=90, fill='white', anchor='center')

    canvas3 = tk.Canvas(tab3, width=25, height=80, bg='#9146ff', highlightthickness=0)
    canvas3.pack(side=tk.LEFT, fill=tk.Y)
    canvas3.create_text(15, 40, text='Twitch', angle=90, fill='white', anchor='center')

    canvas4 = tk.Canvas(tab4, width=25, height=80, bg='#2c7ef2', highlightthickness=0)
    canvas4.pack(side=tk.LEFT, fill=tk.Y)
    canvas4.create_text(15, 40, text='streamlink', angle=90, fill='white', anchor='center')

    canvas5 = tk.Canvas(tab5, width=25, height=80, bg='#ff7e00', highlightthickness=0)
    canvas5.pack(side=tk.LEFT, fill=tk.Y)
    canvas5.create_text(15, 40, text='yt-dlp', angle=90, fill='white', anchor='center')

    spec1 = "iptv"
    spec2 = "youtube"
    spec3 = "twitch"
    spec4 = "streamlink"
    spec5 = "yt-dlp"

    tab_control.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

    playlist_player1 = M3uPlaylistPlayer(tab1, spec1, script)
    playlist_player1.pack(fill=tk.BOTH, expand=True)

    playlist_player2 = M3uPlaylistPlayer(tab2, spec2, script)
    playlist_player2.pack(fill=tk.BOTH, expand=True)

    playlist_player3 = M3uPlaylistPlayer(tab3, spec3, script)
    playlist_player3.pack(fill=tk.BOTH, expand=True)

    playlist_player4 = M3uPlaylistPlayer(tab4, spec4, script)
    playlist_player4.pack(fill=tk.BOTH, expand=True)

    playlist_player5 = M3uPlaylistPlayer(tab5, spec5, script)
    playlist_player5.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = MainApplication()
    app.main_window.mainloop()
