"""

"playlist4whisper" is an application that displays a playlist for livestream_video.sh, a simple GUI using Python and the tkinter library. It plays online videos and transcribes livestreams by feeding the output of ffmpeg to whisper.cpp, based on livestream.sh from whisper.cpp.


Author: Antonio R. Version: 1.16 License: MIT



Usage: 

python playlist4whisper.py 

The program will load default playlist.m3u, and will store options in config.json


This program depends on other Linux programs and their libraries, such as whisper.cpp and mpv. The script livestream_video.sh should be in the same directory as the compiled executable of whisper.cpp, which should have the default name "main". Additionally, it is necessary to download the Whisper model file from OpenAI and place it in the "models" directory with the correct format and name, as specified in the Whisper.cpp repository. This can be done using terminal commands like one of the following examples:

make tiny.en

make small


playlist4whisper.py dependes on (smplayer, mpv or mplayer) video player and (gnome-terminal or konsole or xfce4-terminal).


Options for script:

    ./livestream_video.sh stream_url [step_s] [model] [language] [translate]

    Example (defaults if no options are specified):
 
    ./livestream_video.sh https://cbsnews.akamaized.net/hls/live/2020607/cbsnlineup_8/master.m3u8 3 tiny.en en


Step: Size of the parts into which videos are divided for inference, size in seconds.

Whisper models: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large

Whisper languages:

Autodetected (auto), English (en), Chinese (zh), German (de), Spanish (es), Russian (ru), Korean (ko), French (fr), Japanese (ja), Portuguese (pt), Catalan (ca), Dutch (nl), Arabic (ar), Italian (it), Hebrew (iw), Ukrainian (uk), Romanian (ro), Persian (fa), Swedish (sv), Indonesian (id), Hindi (hi), Finnish (fi), Vietnamese (vi), Hebrew (iw), Ukrainian (uk), Greek (el), Malay (ms), Czech (cs), Romanian (ro), Danish (da), Hungarian (hu), Tamil (ta), Norwegian (no), Thai (th), Urdu (ur), Croatian (hr), Bulgarian (bg), Lithuanian (lt), Latin (la), Maori (mi), Malayalam (ml), Welsh (cy), Slovak (sk), Telugu (te), Persian (fa), Latvian (lv), Bengali (bn), Serbian (sr), Azerbaijani (az), Slovenian (sl), Kannada (kn), Estonian (et), Macedonian (mk), Breton (br), Basque (eu), Icelandic (is), Armenian (hy), Nepali (ne), Mongolian (mn), Bosnian (bs), Kazakh (kk), Albanian (sq), Swahili (sw), Galician (gl), Marathi (mr), Punjabi (pa), Sinhala (si), Khmer (km), Shona (sn), Yoruba (yo), Somali (so), Afrikaans (af), Occitan (oc), Georgian (ka), Belarusian (be), Tajik (tg), Sindhi (sd), Gujarati (gu), Amharic (am), Yiddish (yi), Lao (lo), Uzbek (uz), Faroese (fo), Haitian Creole (ht), Pashto (ps), Turkmen (tk), Nynorsk (nn), Maltese (mt), Sanskrit (sa), Luxembourgish (lb), Myanmar (my), Tibetan (bo), Tagalog (tl), Malagasy (mg), Assamese (as), Tatar (tt), Hawaiian (haw), Lingala (ln), Hausa (ha), Bashkir (ba), Javanese (jw), Sundanese (su).

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
from tkinter import filedialog, ttk, simpledialog

# Default options
default_mpv_options = "-geometry 1280"
default_bash_options = "4 base auto translate"
bash_script = "./livestream_video.sh"
config_file = "config.json"


class M3uPlaylistPlayer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("playlist4whisper")
        self.geometry("800x800")

        self.playlist = []
        self.current_options = {} 
        self.load_config()

        self.create_widgets()
        self.populate_playlist()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("name", "url"), show="headings")
        self.tree.heading("name", text="Channel")
        self.tree.heading("url", text="URL")
        self.tree.column("name", width=250, stretch=True, minwidth=50)
        self.tree.column("url", width=400, stretch=True, minwidth=50)
        self.tree.bind('<Double-Button-1>', self.play_channel)
        self.tree.pack(fill=tk.BOTH, expand=True)

        yscrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=yscrollbar.set)

        self.options_frame = tk.Frame(self)
        self.options_frame.pack(side=tk.TOP)

        self.mpv_options_label = tk.Label(self.options_frame, text="Player Options:")
        self.mpv_options_label.pack(side=tk.LEFT)

        self.mpv_options_entry = tk.Entry(self.options_frame)
        self.mpv_options_entry.insert(0, self.current_options.get("mpv_options", ""))
        self.mpv_options_entry.pack(side=tk.LEFT)
        self.mpv_options_entry.bind("<FocusOut>", self.save_options)

        self.bash_options_label = tk.Label(self.options_frame, text="Script Options:", padx=10)
        self.bash_options_label.pack(side=tk.LEFT)

        self.bash_options_entry = tk.Entry(self.options_frame)
        self.bash_options_entry.insert(0, self.current_options.get("bash_options", ""))
        self.bash_options_entry.pack(side=tk.LEFT)
        self.bash_options_entry.bind("<FocusOut>", self.save_options)

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

        self.load_label = tk.Label(self, text="", padx=10)
        self.load_label.pack(side=tk.LEFT)

        self.load_button = tk.Button(self, text="About", command=self.show_about_window)
        self.load_button.pack(side=tk.LEFT)


    def populate_playlist(self, filename="playlist.m3u"):
        try:
            with open(filename, "r", encoding='utf-8') as file:
                lines = file.readlines()

            for i, line in enumerate(lines):
                if line.startswith("#EXTINF"):
                    name = line[line.rfind(",")+1:].strip()
                    url = None

                    for j in range(i+1, len(lines)):
                        url_line = lines[j].strip()
                        if url_line and not url_line.startswith("#"):
                            url = url_line
                            break

                    if url:
                        self.tree.insert("", "end", values=(name, url))
        except FileNotFoundError:
            simpledialog.messagebox.showerror("File Not Found", "The default playlist.m3u file was not found.")





    def play_channel(self, event):
        region = self.tree.identify_region(event.x, event.y)

        if region == "cell":
            item = self.tree.selection()[0]
            url = self.tree.item(item, "values")[1]
            url =  '"' + url + '"'
            mpv_options = self.mpv_options_entry.get()
            bash_options = self.bash_options_entry.get()
            print("Playing channel:", url)

            # Try launching gnome-terminal, konsole or xfce4-terminal
            if os.path.exists(bash_script):
                if os.system("gnome-terminal --version") == 0:
                    os.system(f"gnome-terminal --tab -- /bin/bash -c '{bash_script} {url} {bash_options}; exec /bin/bash -i' &")
                elif os.system("konsole --version") == 0:
                    os.system(f"konsole --noclose -e '{bash_script} {url} {bash_options}' &")
                elif os.system("xfce4-terminal --version") == 0:
                    os.system(f"xfce4-terminal --hold -e '{bash_script} {url} {bash_options}' &")
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
        name = simpledialog.askstring("Add Channel", "Channel Name:")
        url = simpledialog.askstring("Add Channel", "Channel URL:")
        if name and url:
            self.tree.insert("", "end", values=(name, url))

    # Function to delete a channel
    def delete_channel(self):
        selection = self.tree.selection()
        if selection:
            self.tree.delete(selection[0])
        else:
            simpledialog.messagebox.showerror("Error", "Select a channel to delete")

    # Function to edit a channel
    def edit_channel(self):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            name = simpledialog.askstring("Edit Channel", "Channel Name:", initialvalue=self.tree.item(item, "values")[0])
            url = simpledialog.askstring("Edit Channel", "Channel URL:", initialvalue=self.tree.item(item, "values")[1])
            if name and url:
                self.tree.item(item, values=(name, url))
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

    # Function to save a playlist
    def save_playlist(self):
        filename = filedialog.asksaveasfilename(filetypes=[("Playlist Files", "*.m3u")])
        if filename:
            with open(filename, "w") as file:
                for item in self.tree.get_children():
                    name, url = self.tree.item(item, "values")
                    file.write(f"#EXTINF:-1,{name}\n{url}\n")

    # Function to load and save config.json
    def load_config(self):
        self.current_options["mpv_options"] = default_mpv_options
        self.current_options["bash_options"] = default_bash_options
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                self.current_options = json.load(file)

    def save_options(self, event):
        mpv_options = self.mpv_options_entry.get()
        self.current_options["mpv_options"] = mpv_options
        bash_options = self.bash_options_entry.get()
        self.current_options["bash_options"] = bash_options
        self.save_config()

    def save_config(self):
        with open(config_file, "w") as file:
            json.dump(self.current_options, file) 

    # Function About
    def show_about_window(self):
        simpledialog.messagebox.showinfo("About", "playlist4whisper\n\nPlaylist for livestream_video.sh, a simple GUI using Python and tkinter library. It plays online videos and transcribe livestreams by feeding ffmpeg output to whisper.cpp, based on livestream.sh from whisper.cpp.\n\nAuthor: Antonio R.\nVersion: 1.16\nLicense: MIT")


if __name__ == "__main__":
    app = M3uPlaylistPlayer()
    app.mainloop()
