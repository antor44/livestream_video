"""

"Playlist4Whisper" is an application that displays a playlist for "livestream_video.sh". It plays an online video
 and uses AI technology to transcribe the audio into text. It supports multi-instance and multi-user execution,
 and allows for changing options per channel and global options.


Author: Antonio R. Version: 1.32 License: MIT



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

    ./livestream_video.sh stream_url [step_s] [model] [language] [translate]

    Example (defaults if no options are specified):

    ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 4 base auto


Step: Size of the parts into which videos are divided for inference, size in seconds.

Whisper models: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large

Whisper languages:

Autodetected (auto), English (en), Chinese (zh), German (de), Spanish (es), Russian (ru), Korean (ko), French (fr),
Japanese (ja), Portuguese (pt), Catalan (ca), Dutch (nl), Arabic (ar), Italian (it), Hebrew (iw), Ukrainian (uk),
Romanian (ro), Persian (fa), Swedish (sv), Indonesian (id), Hindi (hi), Finnish (fi), Vietnamese (vi), Hebrew (iw),
Ukrainian (uk), Greek (el), Malay (ms), Czech (cs), Romanian (ro), Danish (da), Hungarian (hu), Tamil (ta),
Norwegian (no), Thai (th), Urdu (ur), Croatian (hr), Bulgarian (bg), Lithuanian (lt), Latin (la), Maori (mi),
Malayalam (ml), Welsh (cy), Slovak (sk), Telugu (te), Persian (fa), Latvian (lv), Bengali (bn), Serbian (sr),
Azerbaijani (az), Slovenian (sl), Kannada (kn), Estonian (et), Macedonian (mk), Breton (br), Basque (eu), Icelandic (
is), Armenian (hy), Nepali (ne), Mongolian (mn), Bosnian (bs), Kazakh (kk), Albanian (sq), Swahili (sw),
Galician (gl), Marathi (mr), Punjabi (pa), Sinhala (si), Khmer (km), Shona (sn), Yoruba (yo), Somali (so),
Afrikaans (af), Occitan (oc), Georgian (ka), Belarusian (be), Tajik (tg), Sindhi (sd), Gujarati (gu), Amharic (am),
Yiddish (yi), Lao (lo), Uzbek (uz), Faroese (fo), Haitian Creole (ht), Pashto (ps), Turkmen (tk), Nynorsk (nn),
Maltese (mt), Sanskrit (sa), Luxembourgish (lb), Myanmar (my), Tibetan (bo), Tagalog (tl), Malagasy (mg),
Assamese (as), Tatar (tt), Hawaiian (haw), Lingala (ln), Hausa (ha), Bashkir (ba), Javanese (jw), Sundanese (su).

translate: The "translate" option provides automatic English translation (only English is available).




MIT License

Copyright (c) 2023 Antonio R.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import re
import json
import urllib.parse
import tkinter as tk
from tkinter import Tk, ttk, filedialog, simpledialog, PhotoImage


# Default options
rPadChars = 100 * " "


class M3uPlaylistPlayer(tk.Frame):
    def __init__(self, parent, spec, bash):
        super().__init__(parent)
        self.spec = spec
        self.bash_script = bash
        self.default_mpv_options = "-geometry 1100"
        self.default_bash_options = "4 base auto"
        self.playlist = []

        self.load_button = None
        self.load_label = None
        self.save_button = None
        self.edit_button = None
        self.delete_button = None
        self.add_button = None
        self.add_label = None
        self.override_checkbox = None
        self.save_options_id = None
        self.bash_options_entry = None
        self.bash_options_label = None
        self.mpv_options_entry = None
        self.mpv_options_label = None
        self.options_frame = None
        self.tree = None

        self.current_options = {}
        self.list_number = 0
        self.override_options = tk.BooleanVar()
        self.create_widgets()
        self.mpv_fg = self.mpv_options_entry.cget("fg")
        self.mpv_bg = self.mpv_options_entry.cget("bg")
        self.bash_fg = self.bash_options_entry.cget("fg")
        self.bash_bg = self.bash_options_entry.cget("bg")
        self.load_config()
        self.populate_playlist()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("list_number", "name", "url"), show="headings")
        self.tree.heading("list_number", text="#")
        self.tree.heading("name", text="Channel")
        self.tree.heading("url", text="URL")
        self.tree.column("list_number", width=35, stretch=False, minwidth=15)
        self.tree.column("name", width=250, stretch=True, minwidth=50)
        self.tree.column("url", width=400, stretch=True, minwidth=50)
        self.tree.bind('<Double-Button-1>', self.play_channel)
        self.tree.pack(fill=tk.BOTH, expand=True)

        yscrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=yscrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.load_options)

        self.options_frame = tk.Frame(self)
        self.options_frame.pack(side=tk.TOP)

        self.mpv_options_label = tk.Label(self.options_frame, text="Player Options:")
        self.mpv_options_label.pack(side=tk.LEFT)

        self.mpv_options_entry = tk.Entry(self.options_frame)
        self.mpv_options_entry.insert(0, self.current_options.get("mpv_options", ""))
        self.mpv_options_entry.pack(side=tk.LEFT)

        self.bash_options_label = tk.Label(self.options_frame, text="Script Options:", padx=10)
        self.bash_options_label.pack(side=tk.LEFT)

        self.bash_options_entry = tk.Entry(self.options_frame)
        self.bash_options_entry.insert(0, self.current_options.get("bash_options", ""))
        self.bash_options_entry.pack(side=tk.LEFT)

        self.mpv_options_entry.bind("<KeyRelease>", self.schedule_save_options)
        self.bash_options_entry.bind("<KeyRelease>", self.schedule_save_options)
        self.save_options_id = None

        self.override_options = tk.BooleanVar()
        self.override_checkbox = tk.Checkbutton(self.options_frame, text='Override options', variable=self.override_options, command=self.change_override)
        self.override_checkbox.pack(side=tk.LEFT, padx=10)

        self.add_label = tk.Label(self, text="Channel:", padx=10)
        self.add_label.pack(side=tk.LEFT)

        self.add_button = tk.Button(self, text="Add", command=self.add_channel)
        self.add_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(self, text="Delete", command=self.delete_channel)
        self.delete_button.pack(side=tk.LEFT)

        self.edit_button = tk.Button(self, text="Edit", command=self.edit_channel)
        self.edit_button.pack(side=tk.LEFT)

        self.load_label = tk.Label(self, text="Playlist:", padx=10)
        self.load_label.pack(side=tk.LEFT)

        self.load_button = tk.Button(self, text="Load", command=self.load_playlist)
        self.load_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(self, text="Append", command=self.append_playlist)
        self.save_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(self, text="Save", command=self.save_playlist)
        self.save_button.pack(side=tk.LEFT)

        self.load_label = tk.Label(self, text="", padx=20)
        self.load_label.pack(side=tk.LEFT)

        self.load_button = tk.Button(self, text="About", command=self.show_about_window)
        self.load_button.pack(side=tk.LEFT)


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
            simpledialog.messagebox.showerror("File Not Found", f"The default playlist_{self.spec}.m3u file was not found.")

    def play_channel(self, event):
        region = self.tree.identify_region(event.x, event.y)

        if region == "cell":
            item = self.tree.selection()[0]
            url = self.tree.item(item, "values")[2]
            url = '"' + url + '"'
            mpv_options = self.mpv_options_entry.get()
            bash_options = self.bash_options_entry.get()
            print("Playing channel:", url)

            # Try launching gnome-terminal, konsole or xfce4-terminal
            if os.path.exists(self.bash_script):
                if os.system("gnome-terminal --version") == 0:
                    os.system(f"gnome-terminal --tab -- /bin/bash -c '{self.bash_script} {url} {bash_options}; exec /bin/bash -i' &")
                elif os.system("konsole --version") == 0:
                    os.system(f"konsole --noclose -e '{self.bash_script} {url} {bash_options}' &")
                elif os.system("xfce4-terminal --version") == 0:
                    os.system(f"xfce4-terminal --hold -e '{self.bash_script} {url} {bash_options}' &")
                else:
                    print("No compatible terminal found.")
                    simpledialog.messagebox.showerror("Error", "No compatible terminal found.")
            else:
                print("Script does not exist.")
                simpledialog.messagebox.showerror("Error", "Script does not exist.")

            # Try launching smplayer, mpv or mplayer
            if os.system("smplayer --help") == 0:
                os.system(f"smplayer {url} {mpv_options} &")
            elif os.system("mpv --version") == 0:
                os.system(f"mpv {url} {mpv_options} &")
            elif os.system("mplayer -v") == 0:
                os.system(f"mplayer {url} {mpv_options} &")
            else:
                print("No compatible video player found.")
                simpledialog.messagebox.showerror("Error", "No compatible video player found.")

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
    def load_options(self, event):
        self.load_config()
        mpv_options = self.current_options["mpv_options"]
        bash_options = self.current_options["bash_options"]
        self.mpv_options_entry.config(highlightthickness=1, highlightbackground="black")
        self.bash_options_entry.config(highlightthickness=1, highlightbackground="black")

        if not self.override_options.get():
            selection = self.tree.focus()
            if selection:
                url = self.tree.item(selection, "values")[2]
                if url in self.current_options:
                    mpv_options = self.current_options[url].get("mpv_options", "")
                    bash_options = self.current_options[url].get("bash_options", "")
                    self.mpv_options_entry.config(highlightthickness=1, highlightbackground="red")
                    self.bash_options_entry.config(highlightthickness=1, highlightbackground="red")
                self.mpv_options_entry.delete(0, tk.END)
                self.mpv_options_entry.insert(0, mpv_options)
                self.bash_options_entry.delete(0, tk.END)
                self.bash_options_entry.insert(0, bash_options)

    def load_config(self):
        config_file = f'config_{self.spec}.json'
        self.current_options["mpv_options"] = self.default_mpv_options
        self.current_options["bash_options"] = self.default_bash_options
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                self.current_options = json.load(file)

    def schedule_save_options(self, event):
        if self.save_options_id:
            self.after_cancel(self.save_options_id)
        self.save_options_id = self.after(1000, self.save_options)

    def save_options(self):
        mpv_options = self.mpv_options_entry.get()
        bash_options = self.bash_options_entry.get()
        self.mpv_options_entry.config(highlightthickness=1, highlightbackground="black")
        self.bash_options_entry.config(highlightthickness=1, highlightbackground="black")
        if self.override_options.get():
            self.current_options["mpv_options"] = mpv_options
            self.current_options["bash_options"] = bash_options
        else:
            selection = self.tree.focus()
            if selection:
                self.mpv_options_entry.config(highlightthickness=1, highlightbackground="red")
                self.bash_options_entry.config(highlightthickness=1, highlightbackground="red")
                url = self.tree.item(selection, "values")[2]
                self.current_options[url] = {}
                self.current_options[url]["mpv_options"] = mpv_options
                self.current_options[url]["bash_options"] = bash_options
        self.save_config()

    def save_config(self):
        config_file = f'config_{self.spec}.json'
        with open(config_file, "w") as file:
            json.dump(self.current_options, file)

    # Change override
    def change_override(self):
        self.load_config()
        mpv_options = self.current_options["mpv_options"]
        bash_options = self.current_options["bash_options"]
        self.mpv_options_entry.config(highlightthickness=1, highlightbackground="black")
        self.bash_options_entry.config(highlightthickness=1, highlightbackground="black")
        if self.override_options.get():
            self.mpv_options_entry.config(fg=self.mpv_bg, bg=self.mpv_fg, insertbackground=self.mpv_bg)
            self.bash_options_entry.config(fg=self.bash_bg, bg=self.bash_fg, insertbackground=self.bash_bg)
        else:
            self.mpv_options_entry.config(fg=self.mpv_fg, bg=self.mpv_bg, insertbackground=self.mpv_fg)
            self.bash_options_entry.config(fg=self.bash_fg, bg=self.bash_bg, insertbackground=self.bash_fg)
            selection = self.tree.focus()
            if selection:
                url = self.tree.item(selection, "values")[2]
                if url in self.current_options:
                    self.mpv_options_entry.config(highlightthickness=1, highlightbackground="red")
                    self.bash_options_entry.config(highlightthickness=1, highlightbackground="red")
                    mpv_options = self.current_options[url].get("mpv_options", "")
                    bash_options = self.current_options[url].get("bash_options", "")
        self.mpv_options_entry.delete(0, tk.END)
        self.mpv_options_entry.insert(0, mpv_options)
        self.bash_options_entry.delete(0, tk.END)
        self.bash_options_entry.insert(0, bash_options)
        self.save_config()

    # Function About
    @staticmethod
    def show_about_window():
        simpledialog.messagebox.showinfo("About",
                                         "playlist4whisper\n"
                                         "Playlist for livestream_video.sh, "
                                         "it plays online videos and transcribes them. "
                                         "A simple GUI using Python and Tkinter library. "
                                         "Based on whisper.cpp.\n\n"
                                         "Author: Antonio R.\nVersion: 1.32\nLicense: MIT")


class MainApplication():
    main_window =tk.Tk()
    main_window.title("playlist4whisper")
    main_window.geometry("800x800")

    icon = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABGdBTUEAALGPC/xhBQAAAYRpQ0NQSUNDIHByb2ZpbGUAACiRfZE9SMNAHMVfv1C04mAHEYcM1cmCaBHdtApFqBBqhVYdTC79giYNSYqLo+BacPBjserg4qyrg6sgCH6AuLo4KbpIif9LCi1iPDjux7t7j7t3gL9RYaoZHAdUzTLSyYSQza0KXa8IIYhexDEjMVOfE8UUPMfXPXx8vYvxLO9zf44+JW8ywCcQzzLdsIg3iKc2LZ3zPnGElSSF+Jx4zKALEj9yXXb5jXPRYT/PjBiZ9DxxhFgodrDcwaxkqMRx4qiiapTvz7qscN7irFZqrHVP/sJwXltZ5jrNYSSxiCWIECCjhjIqsBCjVSPFRJr2Ex7+IccvkksmVxmMHAuoQoXk+MH/4He3ZmFywk0KJ4DQi21/jABdu0Czbtvfx7bdPAECz8CV1vZXG8D0J+n1thY9Avq3gYvrtibvAZc7wOCTLhmSIwVo+gsF4P2MvikHDNwCPWtub619nD4AGeoqdQMcHAKjRcpe93h3d2dv/55p9fcDs4VywQjulqoAAAAGYktHRAAAAAAAAPlDu38AAAAJcEhZcwAADdcAAA3XAUIom3gAAAAHdElNRQfnBQQLNjFUgOcTAAAD0klEQVR42u2b229MURTGf0ZbLYkqo3VphXqgIqkmXlwiLkGJS73wQhBFIuJFhEcSiVtCSjzwD/DWJsgglAckDU2lCYKKS2ijcal2OqaqUw9nT3Ls7nNmembmzJ4zXclOMz1r7z3fd9Y6a+111kCWy6gE5hZphqUbGEgVAaVADbARmAeUALmaETAAdAJtwC2gHniT6KIlwGXgDzCYYSMCXAPKnYJfDfzIQODyCAM7h+sCu4GrQI7F9UGgSzMXGA+Mtrl+HDgRz0KrgH4Fk6+AQ8BsDf0fAb4MqAWaLKxhV6xF/MB3aVI/cNjGGnSNbjuAoMIdKuwmXpAm/BVP/kyVhUCPhKnBSrlYMGRWPuqBXGerwhWqVIp7JKU2IM8jCd9DCdtJlVKDpHTMQxnvNgnbc5XSS0mp0kMEFErYQiqlLkmp0MFGU4FFmpIgJ3VFquTGPJzIAjH3EbBcMwLeSfjKAXwp2mwJ8EBTIv4TX4rXjxJxW1fX8Lm0z1rgibCIFdlIgNkiGoE7wOJsICBi8f81wGMdiEg1Aa3AUuBmDCK0cI1khsHoaJHM/0aM4kUqiVCGQTcJSDcR2hCQLiK0I8BtIrQlICrLRIi0I+JuAlFDewLMRDTFQURlMghwOxGKJX5gJTDXRqcTuE8SXnroZAHFwFmGFjHN4wtGVTrfSy7gx6jX/7IB/hWjNlngpYegm8C1IiAdwLUgIJ3A00rAWxcebloTMJjGOx4XAel439cOnMF4+xxOd+LhJgGdwHngIvBbl8wrJ9vuuJsEaHnH7QiISGcDn01NLxOBy+eeIR1lHdJTssTBJuNcCGdOJSThK5BZ6ZAmVDjYpFdHPwdmSuH2Z9Q6zQQ0S5O24B2pkT43q5Q2SCbSA0zxAPh84KOE7aCVYrukWE9i7bQ6iNz3FMJ4ja+UfYqU9RL2/Xc6yxEFnlOxwqKqHncPo0c4U6QMuK7A8R6p8UNl3tOAp+KvHDcbgYA4WIRsvkALRr9hvJKLUR7PSdDXZ2C0+FYrwnFQ7NEaz2LzBVtO+3Or4/zSecDeBPeKZ3zDQaPGZIzycyoIyAP2Ax9IfbP0M4z2XseyXrhEMggYAxwAPrkA/DWwnRil/+GEuFkYbbNzMH5AMdZ0rQqYZPq8DqMtxuyftaIAUmqxfh/Gq/KIwxsVFtls9AcTL9x86gYsLCBPhNbPNneqD7hiQ0xGiEzApjiAhwXw6V7ItQMKcFbAe8Vx2QtptiUBqhEEzjk8Zmc0AUGgzi7/9ioB3SLv9pMFEpCO0XVeNXU7ArqB08BEslA2AxMYkREZkUyTf3yN/Z4aqslDAAAAAElFTkSuQmCC"

    main_window.iconphoto(True, PhotoImage(data=icon))

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

    canvas2 = tk.Canvas(tab2, width=25, height=80, bg='black', highlightthickness=0)
    canvas2.pack(side=tk.LEFT, fill=tk.Y)
    canvas2.create_text(15, 40, text='YouTube', angle=90, fill='white', anchor='center')

    canvas3 = tk.Canvas(tab3, width=25, height=80, bg='black', highlightthickness=0)
    canvas3.pack(side=tk.LEFT, fill=tk.Y)
    canvas3.create_text(15, 40, text='Twitch', angle=90, fill='white', anchor='center')

    spec1 = "iptv"
    spec2 = "youtube"
    spec3 = "twitch"

    tab_control.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

    playlist_player1 = M3uPlaylistPlayer(tab1, spec1, "./livestream_video.sh")
    playlist_player1.pack(fill=tk.BOTH, expand=True)

    playlist_player2 = M3uPlaylistPlayer(tab2, spec2, "./livestream_video.sh")
    playlist_player2.pack(fill=tk.BOTH, expand=True)

    playlist_player3 = M3uPlaylistPlayer(tab3, spec3, "./livestream_video.sh")
    playlist_player3.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = MainApplication()
    app.main_window.mainloop()
