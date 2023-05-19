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


Author: Antonio R. Version: 1.46 License: GPL 3.0


Usage:

python playlist4whisper.py

-Support for multi-instance and multi-user execution
-Support for IPTV, YouTube and Twitch

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


playlist4whisper.py depends on (smplayer, mpv or mplayer) video player and (gnome-terminal or konsole or
xfce4-terminal).

For YouTube yt-dlp is required (https://github.com/yt-dlp/yt-dlp)
For Twitch streamlink is required (https://streamlink.github.io)

Options for script:

Usage:
./livestream_video.sh stream_url [step_s] [model] [language] [translate] [quality] [ [player executable + options] ]

Example (defaults if no options are specified):
./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 4 base auto raw [smplayer]


Quality: The valid options are "raw," "upper," and "lower". "Raw" is used to download another video stream without
 any modifications for the player. "Upper" and "lower" download only one stream, which might correspond to the best
 or worst stream quality, re-encoded for the player.

"[player executable + player options]", valid players: smplayer, mpv, mplayer, vlc, etc... or "[true]" for no player.

Step: Size of the parts into which videos are divided for inference, size in seconds.

Whisper models: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large

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

"""

import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, PhotoImage

# Default options
rPadChars = 100 * " "


class M3uPlaylistPlayer(tk.Frame):
    def __init__(self, parent, spec, bash):
        super().__init__(parent)
        self.spec = spec
        self.bash_script = bash
        self.default_terminal_option = "genome-terminal"
        self.default_bash_options = "4 base auto raw"
        self.default_playeronly_option = False
        self.default_player_option = "smplayer"
        self.default_mpv_options = "-geometry 1100"
        self.default_override_option = False
        self.playlist = []
        self.lang_codes = {'auto': 'Autodetect', 'af': 'Afrikaans', 'am': 'Amharic', 'ar': 'Arabic', 'as': 'Assamese',
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
        self.load_button = None
        self.load_label = None
        self.save_button = None
        self.edit_button = None
        self.delete_button = None
        self.add_button = None
        self.add_label = None
        self.about_button = None
        self.about_label = None
        self.append_button = None
        self.options_frame2 = None
        self.override_checkbox = None
        self.steps_s_spinner = None
        self.save_options_id = None
        self.mpv_options_entry = None
        self.mpv_options_label = None
        self.options_frame = None
        self.mpv_bg = None
        self.mpv_fg = None
        self.player_option_menu = None
        self.player = None
        self.player_frame = None
        self.player_label = None
        self.playeronly_checkbox = None
        self.playeronly = None
        self.playeronly_frame = None
        self.playeronly_label = None
        self.quality_option_menu = None
        self.quality = None
        self.quality_frame = None
        self.quality_label = None
        self.options_frame1 = None
        self.override_label = None
        self.space_label = None
        self.translate_checkbox = None
        self.translate = None
        self.translate_frame = None
        self.translate_label = None
        self.language_option_menu = None
        self.language = None
        self.language_frame = None
        self.language_label = None
        self.model_option_menu = None
        self.model = None
        self.model_frame = None
        self.model_label = None
        self.step_s_spinner = None
        self.step_s = None
        self.step_frame = None
        self.step_s_label = None
        self.terminal_option_menu = None
        self.terminal = None
        self.terminal_frame = None
        self.terminal_label = None
        self.options_frame0 = None
        self.container_frame = None
        self.termninal = None
        self.tree = None
        self.current_options = {}
        self.list_number = 0
        self.override_options = tk.BooleanVar()
        self.create_widgets()
        self.load_config()
        self.populate_playlist()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("list_number", "name", "url"), show="headings")
        self.tree.heading("list_number", text="#")
        self.tree.heading("name", text="Channel")
        self.tree.heading("url", text="URL")
        self.tree.column("list_number", width=35, stretch=False, minwidth=15)
        self.tree.column("name", width=250, stretch=True, minwidth=50)
        self.tree.column("url", width=250, stretch=True, minwidth=50)
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
        terminal = ["gnome-terminal", "konsole", "lxterm", "mate-terminal", "mlterm", "xfce4-terminal", "xterm"]

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
            terminal_menu.add_radiobutton(label=term, value=term, variable=self.terminal,
                                          command=update_terminal_button)

        self.terminal_option_menu.bind("<<MenuSelect>>", lambda e: update_terminal_button())

        # Step_s
        self.step_s_label = tk.Label(self.options_frame0, text="Step(sec)", padx=4)
        self.step_s_label.pack(side=tk.LEFT)

        self.step_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.step_frame.pack(side=tk.LEFT)

        self.step_s = tk.StringVar(value="4")
        self.step_s_spinner = tk.Spinbox(self.step_frame, from_=2, to=60, width=2, textvariable=self.step_s,
                                         command=self.schedule_save_options)
        self.step_s_spinner.pack(side=tk.LEFT)

        self.step_s_spinner.bind("<KeyRelease>", self.schedule_save_options)

        # Whisper models
        models = ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large-v1", "large"]
        suffixes = ["-q4_0", "-q4_1", "-q4_2", "-q5_0", "-q5_1", "-q8_0"]

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
            suffix_menu.add_radiobutton(label=model, value=model, variable=self.model, command=update_model_button)
            for suffix in suffixes:
                full_model_name = f"{model}{suffix}"
                suffix_menu.add_radiobutton(label=full_model_name, value=full_model_name, variable=self.model,
                                            command=update_model_button)
            model_menu.add_cascade(label=model, menu=suffix_menu)

        self.model_option_menu["menu"] = model_menu

        self.model_option_menu.bind("<<MenuSelect>>", lambda e: update_model_button())

        # Regions and their languages
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
                lang_name = self.lang_codes.get(lang)
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
        player = ["none", "smplayer", "mpv", "mplayer"]

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
            player_menu.add_radiobutton(label=play, value=play, variable=self.player, command=update_player_button)

        self.player_option_menu.bind("<<MenuSelect>>", lambda e: update_player_button())

        # Player Options
        self.mpv_options_label = tk.Label(self.options_frame1, text="Player Options:", padx=4)
        self.mpv_options_label.pack(side=tk.LEFT)

        self.mpv_options_entry = tk.Entry(self.options_frame1, width=50)
        self.mpv_options_entry.insert(0, self.current_options.get("mpv_options", ""))
        self.mpv_options_entry.pack(side=tk.LEFT)

        self.mpv_options_entry.bind("<KeyRelease>", self.schedule_save_options)

        self.mpv_fg = self.mpv_options_entry.cget("fg")
        self.mpv_bg = self.mpv_options_entry.cget("bg")

        # Buttons
        self.options_frame2 = tk.Frame(self.container_frame)
        self.options_frame2.pack(side=tk.TOP, anchor=tk.W)

        self.options_frame2 = tk.Frame(self.container_frame)
        self.options_frame2.pack(side=tk.TOP, anchor=tk.W)

        self.add_label = tk.Label(self.options_frame2, text="Channel:", padx=10)
        self.add_label.pack(side=tk.LEFT)

        self.add_button = tk.Button(self.options_frame2, text="Add", command=self.add_channel)
        self.add_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(self.options_frame2, text="Delete", command=self.delete_channel)
        self.delete_button.pack(side=tk.LEFT)

        self.edit_button = tk.Button(self.options_frame2, text="Edit", command=self.edit_channel)
        self.edit_button.pack(side=tk.LEFT)

        self.load_label = tk.Label(self.options_frame2, text="Playlist:", padx=10)
        self.load_label.pack(side=tk.LEFT)

        self.load_button = tk.Button(self.options_frame2, text="Load", command=self.load_playlist)
        self.load_button.pack(side=tk.LEFT)

        self.append_button = tk.Button(self.options_frame2, text="Append", command=self.append_playlist)
        self.append_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(self.options_frame2, text="Save", command=self.save_playlist)
        self.save_button.pack(side=tk.LEFT)

        self.about_label = tk.Label(self.options_frame2, text="", padx=150)
        self.about_label.pack(side=tk.LEFT)

        self.about_button = tk.Button(self.options_frame2, text="About", command=self.show_about_window)
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

    def play_channel(self, event):
        region = self.tree.identify_region(event.x, event.y)

        if region == "cell":
            item = self.tree.selection()[0]
            url = self.tree.item(item, "values")[2]
            url = '"' + url + '"'
            mpv_options = self.mpv_options_entry.get()

            language_text = self.language.get()
            language_cleaned = language_text.split('(')[0].strip()

            if self.translate.get():
                translate_value = " translate"
            else:
                translate_value = ""

            bash_options = self.step_s.get() + " " + self.model.get() + " " + language_cleaned + \
                           translate_value + " " + self.quality.get()

            print("Playing channel:", url)
            print("Script Options:", bash_options)
            videoplayer = self.player.get()

            # Try launching smplayer, mpv, or mplayer
            if self.playeronly.get():
                if videoplayer == "smplayer" and os.system("smplayer --help > /dev/null 2>&1") == 0:
                    os.system(f"smplayer {url} {mpv_options} &")
                elif videoplayer == "mpv" and os.system("mpv --version > /dev/null 2>&1") == 0:
                    os.system(f"mpv {url} {mpv_options} &")
                elif videoplayer == "mplayer" and os.system("mplayer -v > /dev/null 2>&1") == 0:
                    os.system(f"mplayer {url} {mpv_options} &")
                else:
                    mpv_options = ""
                    print(f"No {videoplayer} video player found.")
                    simpledialog.messagebox.showerror("Error", f"No {videoplayer} video player found.")
            else:
                if videoplayer == "smplayer" and os.system("smplayer --help > /dev/null 2>&1") == 0:
                    mpv_options = f"[smplayer {mpv_options}]"
                elif videoplayer == "mpv" and os.system("mpv --version > /dev/null 2>&1") == 0:
                    mpv_options = f"[mpv {mpv_options}]"
                elif videoplayer == "mplayer" and os.system("mplayer -v > /dev/null 2>&1") == 0:
                    mpv_options = f"[mplayer {mpv_options}]"
                elif videoplayer == "none":
                    mpv_options = f"[true]"
                else:
                    mpv_options = ""
                    print(f"No {videoplayer} video player found.")
                    simpledialog.messagebox.showerror("Error", f"No {videoplayer} video player found.")

            # Try launching gnome-terminal, konsole, lxterm, mlterm, xfce4-terminal, xterm
            if not self.playeronly.get():
                if os.path.exists(self.bash_script):
                    if os.system("gnome-terminal --version") == 0:
                        os.system(
                            f"gnome-terminal --tab -- /bin/bash -c '{self.bash_script} {url} {bash_options}"
                            f" {mpv_options}; exec /bin/bash -i' &")
                    elif os.system("konsole --version") == 0:
                        os.system(f"konsole --noclose -e '{self.bash_script} {url} {bash_options} {mpv_options}' &")
                    elif os.system("lxterm -version") == 0:
                        os.system(f"lxterm -hold -e '{self.bash_script} {url} {bash_options} {mpv_options}' &")
                    elif os.system("mate-terminal --version") == 0:
                        os.system(f"mate-terminal -e '{self.bash_script} {url} {bash_options} {mpv_options}'"
                                  f" & sleep 2 ; disown")
                    elif os.system("mlterm --version") == 0:
                        os.system(f"mlterm -e {self.bash_script} {url} {bash_options} {mpv_options} & sleep 2 ; disown")
                    elif os.system("xfce4-terminal --version") == 0:
                        os.system(f"xfce4-terminal --hold -e '{self.bash_script} {url} {bash_options} {mpv_options}' &")
                    elif os.system("xterm -version") == 0:
                        os.system(f"xterm -hold -e '{self.bash_script} {url} {bash_options} {mpv_options}' &")
                    else:
                        print("No compatible terminal found.")
                        simpledialog.messagebox.showerror("Error", "No compatible terminal found.")
                else:
                    print("Script does not exist.")
                    simpledialog.messagebox.showerror("Error", "Script does not exist.")

    # Function to add a channel
    def add_channel(self):
        name = simpledialog.askstring("Add Channel", "Channel Name:" + rPadChars)
        url = simpledialog.askstring("Add Channel", "Channel URL:" + rPadChars)
        if name and url:
            self.list_number = len(self.tree.get_children()) + 1
            self.tree.insert("", "end", values=(self.list_number, name, url))

    # Function to delete a channel
    def delete_channel(self):
        selection = self.tree.selection()
        if selection:
            self.tree.delete(selection[0])
            # iterate over all items and update their list_number
            for i, item in enumerate(self.tree.get_children()):
                self.tree.item(item, values=(i + 1,) + tuple(self.tree.item(item)['values'][1:]))
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

    # Function to load and save config.json
    def load_options(self, event=None):
        self.load_config()
        terminal_option = self.current_options["terminal_option"]
        bash_options = self.current_options["bash_options"]
        playeronly_option = self.current_options["playeronly_option"]
        player_option = self.current_options["player_option"]
        mpv_options = self.current_options["mpv_options"]
        override_option = self.current_options["override_option"]

        self.terminal_frame.config(highlightthickness=1, highlightbackground="black")
        self.step_frame.config(highlightthickness=1, highlightbackground="black")
        self.model_frame.config(highlightthickness=1, highlightbackground="black")
        self.language_frame.config(highlightthickness=1, highlightbackground="black")
        self.translate_frame.config(highlightthickness=1, highlightbackground="black")
        self.quality_frame.config(highlightthickness=1, highlightbackground="black")
        self.playeronly_frame.config(highlightthickness=1, highlightbackground="black")
        self.player_frame.config(highlightthickness=1, highlightbackground="black")
        self.mpv_options_entry.config(highlightthickness=1, highlightbackground="black")

        self.override_options.set(override_option)

        if not self.override_options.get():
            selection = self.tree.focus()
            if selection:
                url = self.tree.item(selection, "values")[2]
                if url in self.current_options:
                    terminal_option = self.current_options[url].get("terminal_option", "")
                    bash_options = self.current_options[url].get("bash_options", "")
                    playeronly_option = self.current_options[url].get("playeronly_option", "")
                    player_option = self.current_options[url].get("player_option", "")
                    mpv_options = self.current_options[url].get("mpv_options", "")

                    self.terminal_frame.config(highlightthickness=1, highlightbackground="red")
                    self.step_frame.config(highlightthickness=1, highlightbackground="red")
                    self.model_frame.config(highlightthickness=1, highlightbackground="red")
                    self.language_frame.config(highlightthickness=1, highlightbackground="red")
                    self.translate_frame.config(highlightthickness=1, highlightbackground="red")
                    self.quality_frame.config(highlightthickness=1, highlightbackground="red")
                    self.playeronly_frame.config(highlightthickness=1, highlightbackground="red")
                    self.player_frame.config(highlightthickness=1, highlightbackground="red")
                    self.mpv_options_entry.config(highlightthickness=1, highlightbackground="red")

                self.terminal_option_menu.unbind("<<MenuSelect>>")
                self.terminal.set(terminal_option)
                self.terminal_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
                self.translate.set(False)

                models = ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium",
                          "large-v1", "large"]
                suffixes = ["-q4_0", "-q4_1", "-q4_2", "-q5_0", "-q5_1", "-q8_0"]

                model_list = models + [model + suffix for model in models for suffix in suffixes]

                options_list = bash_options.split()
                while options_list:
                    option = options_list.pop(0)
                    if option.isdigit() and (2 <= int(option) <= 60):
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
                    elif option in self.lang_codes:
                        self.language_option_menu.unbind("<<MenuSelect>>")
                        lang_name = self.lang_codes.get(option)
                        full_language_name = f"{option} ({lang_name})"
                        self.language.set(full_language_name)
                        self.language_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
                    else:
                        simpledialog.messagebox.showerror("Wrong option",
                                                          f"Wrong option {option} found, try again after deleting"
                                                          f" config_{self.spec}.json file")

                self.playeronly.set(playeronly_option)
                self.player_option_menu.unbind("<<MenuSelect>>")
                self.player.set(player_option)
                self.player_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
                self.mpv_options_entry.delete(0, tk.END)
                self.mpv_options_entry.insert(0, mpv_options)


    def load_config(self):
        try:
            config_file = f'config_{self.spec}.json'
            self.current_options["terminal_option"] = self.default_terminal_option
            self.current_options["bash_options"] = self.default_bash_options
            self.current_options["playeronly_option"] = self.default_playeronly_option
            self.current_options["player_option"] = self.default_player_option
            self.current_options["mpv_options"] = self.default_mpv_options
            self.current_options["override_option"] = self.default_override_option

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

        if self.override_options.get():
            self.current_options["terminal_option"] = terminal_option
            self.current_options["bash_options"] = bash_options
            self.current_options["playeronly_option"] = playeronly_option
            self.current_options["player_option"] = player_option
            self.current_options["mpv_options"] = mpv_options
            self.current_options["override option"] = True
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

                url = self.tree.item(selection, "values")[2]
                self.current_options[url] = {}
                self.current_options[url]["terminal_option"] = terminal_option
                self.current_options[url]["bash_options"] = bash_options
                self.current_options[url]["playeronly_option"] = playeronly_option
                self.current_options[url]["player_option"] = player_option
                self.current_options[url]["mpv_options"] = mpv_options

        self.save_config()

    def save_config(self):
        config_file = f'config_{self.spec}.json'
        with open(config_file, "w") as file:
            json.dump(self.current_options, file)

    # Change override
    def change_override(self):
        self.load_config()
        terminal_option = self.current_options["terminal_option"]
        bash_options = self.current_options["bash_options"]
        playeronly_option = self.current_options["playeronly_option"]
        player_option = self.current_options["player_option"]
        mpv_options = self.current_options["mpv_options"]

        self.terminal_frame.config(highlightthickness=1, highlightbackground="black")
        self.step_frame.config(highlightthickness=1, highlightbackground="black")
        self.model_frame.config(highlightthickness=1, highlightbackground="black")
        self.language_frame.config(highlightthickness=1, highlightbackground="black")
        self.translate_frame.config(highlightthickness=1, highlightbackground="black")
        self.quality_frame.config(highlightthickness=1, highlightbackground="black")
        self.playeronly_frame.config(highlightthickness=1, highlightbackground="black")
        self.player_frame.config(highlightthickness=1, highlightbackground="black")
        self.mpv_options_entry.config(highlightthickness=1, highlightbackground="black")

        if self.override_options.get():
            self.mpv_options_entry.config(fg=self.mpv_bg, bg=self.mpv_fg, insertbackground=self.mpv_bg)
        else:
            self.mpv_options_entry.config(fg=self.mpv_fg, bg=self.mpv_bg, insertbackground=self.mpv_fg)
            selection = self.tree.focus()
            if selection:
                url = self.tree.item(selection, "values")[2]
                if url in self.current_options:
                    self.terminal_frame.config(highlightthickness=1, highlightbackground="red")
                    self.step_frame.config(highlightthickness=1, highlightbackground="red")
                    self.model_frame.config(highlightthickness=1, highlightbackground="red")
                    self.language_frame.config(highlightthickness=1, highlightbackground="red")
                    self.translate_frame.config(highlightthickness=1, highlightbackground="red")
                    self.quality_frame.config(highlightthickness=1, highlightbackground="red")
                    self.playeronly_frame.config(highlightthickness=1, highlightbackground="red")
                    self.player_frame.config(highlightthickness=1, highlightbackground="red")
                    self.mpv_options_entry.config(highlightthickness=1, highlightbackground="red")

                    terminal_option = self.current_options[url].get("terminal_option", "")
                    bash_options = self.current_options[url].get("bash_options", "")
                    playeronly_option = self.current_options[url].get("playeronly_option", "")
                    player_option = self.current_options[url].get("player_option", "")
                    mpv_options = self.current_options[url].get("mpv_options", "")

        self.terminal_option_menu.unbind("<<MenuSelect>>")
        self.terminal.set(terminal_option)
        self.terminal_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
        self.translate.set(False)

        models = ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large-v1",
                  "large"]
        suffixes = ["-q4_0", "-q4_1", "-q4_2", "-q5_0", "-q5_1", "-q8_0"]

        model_list = models + [model + suffix for model in models for suffix in suffixes]

        options_list = bash_options.split()
        while options_list:
            option = options_list.pop(0)
            if option.isdigit() and (2 <= int(option) <= 60):
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
            elif option in self.lang_codes:
                self.language_option_menu.unbind("<<MenuSelect>>")
                lang_name = self.lang_codes.get(option)
                full_language_name = f"{option} ({lang_name})"
                self.language.set(full_language_name)
                self.language_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
            else:
                simpledialog.messagebox.showerror("Wrong option",
                                                  f"Wrong option {option} found, try again after deleting"
                                                  f" config_{self.spec}.json file")

        self.playeronly.set(playeronly_option)
        self.player_option_menu.unbind("<<MenuSelect>>")
        self.player.set(player_option)
        self.player_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
        self.mpv_options_entry.delete(0, tk.END)
        self.mpv_options_entry.insert(0, mpv_options)

        self.save_config()


    # Function About
    @staticmethod
    def show_about_window():
        simpledialog.messagebox.showinfo("About",
                                         "playlist4whisper Version: 1.46\n\nCopyright (C) 2023 Antonio R.\n\n"
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
    main_window.geometry("1000x800")

    icon = "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" \
           "slDAAAAAElFTkSuQmCC"

    main_window.iconphoto(True, PhotoImage(data=icon))

    script = "./livestream_video.sh"

    tab_control = ttk.Notebook(main_window)

    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)
    tab3 = ttk.Frame(tab_control)

    tab_control.add(tab1, text="IPTV", compound="left")
    tab_control.add(tab2, text="YouTube", compound="left")
    tab_control.add(tab3, text="Twitch", compound="left")

    canvas1 = tk.Canvas(tab1, width=25, height=80, bg='black', highlightthickness=0)
    canvas1.pack(side=tk.LEFT, fill=tk.Y)
    canvas1.create_text(15, 40, text='IPTV', angle=90, fill='white', anchor='center')

    canvas2 = tk.Canvas(tab2, width=25, height=80, bg='#ff0000', highlightthickness=0)
    canvas2.pack(side=tk.LEFT, fill=tk.Y)
    canvas2.create_text(15, 40, text='YouTube', angle=90, fill='white', anchor='center')

    canvas3 = tk.Canvas(tab3, width=25, height=80, bg='#9146ff', highlightthickness=0)
    canvas3.pack(side=tk.LEFT, fill=tk.Y)
    canvas3.create_text(15, 40, text='Twitch', angle=90, fill='white', anchor='center')

    spec1 = "iptv"
    spec2 = "youtube"
    spec3 = "twitch"

    tab_control.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

    playlist_player1 = M3uPlaylistPlayer(tab1, spec1, script)
    playlist_player1.pack(fill=tk.BOTH, expand=True)

    playlist_player2 = M3uPlaylistPlayer(tab2, spec2, script)
    playlist_player2.pack(fill=tk.BOTH, expand=True)

    playlist_player3 = M3uPlaylistPlayer(tab3, spec3, script)
    playlist_player3.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = MainApplication()
    app.main_window.mainloop()
