"""
play4whisper - displays a playlist for "livestream_video.sh" and plays audio/video files or video streams,
transcribing the audio using AI technology. The application supports a fully configurable timeshift feature,
multi-instance and multi-user execution, allows for changing options per channel and global options,
online translation, and Text-to-Speech with translate-shell. All of these tasks can be performed efficiently
even with low-level processors. Additionally, it generates subtitles from audio/video files.

Author: Antonio R. Version: 3.12 License: GPL 3.0

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

--------------------------------------------------------------------------------
"""

import json
import re
import os
import platform
import shutil
import glob
from pathlib import Path
import time
import argparse
import queue
import threading
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage, scrolledtext
import imageio
from PIL import Image, ImageTk


previous_error_messages = set()
consecutive_same_messages = 0

# Function to display warning messages
def show_error_messages(error_messages, remove_labels_callback=None):
    """
    Displays warning messages if there are no changes in the 'error_messages' for 3 consecutive checks.

    This function tracks the 'error_messages' and displays them using a message box if the same
    'error_messages' are detected for 3 consecutive checks. It uses global variables to keep
    track of previous 'error_messages' and the count of consecutive identical message sets.

    Args:
        error_messages: A list of tuples containing error types and error texts.
        remove_labels_callback (callable, optional): A callback function to remove drag labels.
            This function is called just before printing and showing an error message.
    """

    global previous_error_messages, consecutive_same_messages

    # Check if there are new error messages
    if error_messages:
        consecutive_same_messages = 0
        previous_error_messages.update(error_messages)
    else:
        consecutive_same_messages += 1

    # If there have been no changes for two consecutive checks, show the messages
    if consecutive_same_messages >= 2:
        unique_error_messages = set()

        for error_type, error_text in previous_error_messages:
            unique_error_messages.add((error_type, error_text))

        for error_type, error_text in unique_error_messages:
            err_message = f"{error_type}: {error_text}"
            print(err_message)
            if remove_labels_callback:
                remove_labels_callback()  # remove labels only when message is displayed
            messagebox.showinfo("Warning", err_message)

        previous_error_messages.clear()
        consecutive_same_messages = 0


def wait_and_check_process(process, log_file, url, mpv_options):
    """
    Waits for a brief period and then checks the log file for errors related to a process.

    This function sleeps for 5 seconds, reads the specified log file, and searches for
    error messages indicating issues either with loading the file or with the mpv options.
    If errors are found, it terminates the process and displays an appropriate error message.

    Args:
        process: The subprocess to monitor.
        log_file: A file object for the log file to be checked.
        url: The URL of the file being processed.
        mpv_options: The options used with mpv.

    """

    time.sleep(5)
    with open(log_file.name, "r") as log:
        log_content = log.read()
        error_pattern = re.compile(r"Error.*?option", re.DOTALL)
        if "Errors when loading file" in log_content:
            process.kill()
            error_message = f"Error occurred while playing: {url}"
            print(error_message)
            messagebox.showerror("Error", error_message)
        elif error_pattern.search(log_content):
            process.kill()
            error_message = f"Error in mpv options: {mpv_options}"
            print(error_message)
            messagebox.showerror("Error", error_message)


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
rPadChars = 75
default_executable_option = "./build/bin/whisper-cli"
default_terminal_option = "xterm"
default_bash_options = "8 base auto raw"
default_timeshiftactive_option = False
default_timeshift_options = "4 4 10"
default_playeronly_option = False
default_player_option = "mpv"
default_mpv_options = ""
default_online_translation_option = False
default_trans_options = "en both speak"
default_override_option = False
terminal = ["gnome-terminal", "konsole", "lxterm", "mate-terminal", "mlterm", "xfce4-terminal", "xterm"]
player = ["none", "smplayer", "mpv"]
models = ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large-v1", "large-v2", "large-v3", "large-v3-turbo"]
suffixes = ["-q2_k", "-q3_k", "-q4_0", "-q4_1", "-q4_k", "-q5_0", "-q5_1", "-q5_k", "-q6_k", "-q8_0"]
model_path = "./models/ggml-{}.bin"
model_list = models + [model + suffix for model in models for suffix in suffixes]

lang_codes = {'auto': 'Autodetect', 'af': 'Afrikaans', 'am': 'Amharic', 'ar': 'Arabic', 'as': 'Assamese',
           'az': 'Azerbaijani', 'be': 'Belarusian', 'bg': 'Bulgarian', 'bn': 'Bengali', 'br': 'Breton',
           'bs': 'Bosnian', 'ca': 'Catalan', 'cs': 'Czech', 'cy': 'Welsh', 'da': 'Danish',
           'de': 'German', 'el': 'Greek', 'en': 'English', 'eo': 'Esperanto', 'es': 'Spanish',
           'et': 'Estonian', 'eu': 'Basque', 'fa': 'Persian', 'fi': 'Finnish', 'fo': 'Faroese',
           'fr': 'French', 'ga': 'Irish', 'gl': 'Galician', 'gu': 'Gujarati', 'ha': 'Bantu',
           'haw': 'Hawaiian', 'he': 'Hebrew', 'hi': 'Hindi', 'hr': 'Croatian', 'ht': 'Haitian Creole',
           'hu': 'Hungarian', 'hy': 'Armenian', 'id': 'Indonesian', 'is': 'Icelandic', 'it': 'Italian',
           'ja': 'Japanese', 'jv': 'Javanese', 'ka': 'Georgian', 'kk': 'Kazakh',
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
          "Middle East": ['ar', "fa", "he", "yi"],
          "Oceania": ["haw", "mi", "mg"],
          "Americas": ["ht"],
          "World": ["ar", "en", "eo", "es", "de", "fr", "pt", "ru", "zh"]}


# Array of executable names in priority order
whisper_executables = ["./build/bin/whisper-cli", "./main", "whisper-cpp", "pwcpp", "whisper"]

# Function to find and select executable
def find_and_select_executable():
    for exe in whisper_executables:
        # Check if the executable exists in the PATH
        full_path = shutil.which(exe)
        if full_path is not None:
            # Save the first executable found and exit loop
            return exe
    return None

# Call function to find and select executable
default_executable = find_and_select_executable()

if default_executable is None:
    print("Whisper executable is required.")
    exit(1)
else:
    print("Found whisper executable:", default_executable, "(", shutil.which(default_executable), ")")
    current_dir = os.getcwd()
    models_dir = os.path.join(current_dir, "models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

# Determine the path to the quantize executable
quantize_executable = None  # Initialize to None
if default_executable is not None: # Proceed only if whisper was found
    quantize_paths = ["./build/bin/quantize", "./quantize"]
    for path in quantize_paths:
        if os.path.exists(path):
            quantize_executable = path
            break  # Stop searching once found

    if quantize_executable is None:
        print("Warning: quantize executable not found.  Quantization will be skipped if attempted.")


# Check if ffmpeg is installed
ffmpeg_process = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

if ffmpeg_process.returncode != 0:
    print(f"Error: ffmpeg command returned non-zero exit status {ffmpeg_process.returncode}")

output = ffmpeg_process.stdout
if output == "":
    output = ffmpeg_process.stderr
    if output == "":
        print("ffmpeg is required (https://ffmpeg.org).")
        exit(1)

terminal_installed = []
for term in terminal:
  if check_terminal_installed(term):
      terminal_installed.append(term)

player_installed = []
for play in player:
  if check_player_installed(play):
      player_installed.append(play)

if subprocess.call(["trans", "-V"], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL) == 0:
  options_frame1_text="Only for translate-shell - Online translation and Text-to-Speech"
else:
  options_frame1_text="translate-shell Not installed for online translation and speak!!!"

if subprocess.call(["vlc", "--version"], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL) == 0:
  options_frame3_text="Only for VLC player - Large files will be stored in /tmp directory!!!"
else:
  options_frame3_text="VLC player not installed for Timeshift!!!"


class CustomFileDialog(tk.Toplevel):
    """
    A custom file selection dialog for Tkinter that allows users to select files from a list.

    This dialog displays a list of files from a specified directory, allows users to preview
    the contents of text files (.srt and specific .txt files), and provides buttons to save
    the selected files or cancel the selection. The dialog is modal and resizable, with a
    minimum size constraint.
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("Select Files")
        self.minsize(800, 600) # Set minimum size constraint

        # Center the dialog on the screen
        self.center_window()

        self.selected_files = []

        # File selection frame
        self.file_selection_frame = tk.Frame(self)
        self.file_selection_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # File list
        self.file_list_frame = tk.Frame(self.file_selection_frame)
        self.file_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.file_list = tk.Listbox(self.file_list_frame, width=35, height=10, selectmode=tk.EXTENDED)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.file_list_scrollbar = tk.Scrollbar(self.file_list_frame, orient=tk.VERTICAL)
        self.file_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.config(yscrollcommand=self.file_list_scrollbar.set)
        self.file_list_scrollbar.config(command=self.file_list.yview)

        # File viewer
        self.file_viewer = scrolledtext.ScrolledText(self.file_selection_frame, width=60, height=10)
        self.file_viewer.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.file_list.bind("<ButtonRelease-1>", self.update_file_viewer)  # Bind mouse click event

        # Buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10, fill=tk.X)

        self.select_button = tk.Button(self.button_frame, text="Save selected", command=self.select_files)
        self.select_button.pack(side=tk.LEFT, padx=10)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.RIGHT, padx=10)

        # Populate the file list
        self.populate_file_list()

    def populate_file_list(self):
        directory = "/tmp"
        file_paths = [os.path.join(directory, filename) for filename in os.listdir(directory) if
                   filename.endswith(".srt")  or (filename.endswith(".txt")  and (
                                filename.startswith("translation") or filename.startswith("transcription")))]
        for file_path in file_paths:
          self.file_list.insert(tk.END, file_path)

    def select_files(self):
        self.selected_files = [self.file_list.get(idx) for idx in self.file_list.curselection()]
        self.destroy()

    def update_file_viewer(self, event):
        # Get the index of the clicked item
        index = self.file_list.nearest(event.y)
        if index != -1:
            # Get the file path at the clicked index
            selected_file = self.file_list.get(index)
            try:
                with open(selected_file, 'r') as file:
                    content = file.read()
                    self.file_viewer.delete('1.0', tk.END)
                    self.file_viewer.insert('1.0', content)
                    self.file_viewer.see('1.0')  # Scroll to the beginning of the file
            except (FileNotFoundError, PermissionError):
                pass

    def center_window(self):
        self.update_idletasks()  # Update "requested size" from geometry manager

        # Get the main window's size and position
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()

        # Get the dialog's size
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        # Calculate the position to center the dialog in the main window
        x = master_x + (master_width // 2) - (dialog_width // 2)
        y = master_y + (master_height // 2) - (dialog_height // 2)

        self.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')


class VideoSaverDialog(tk.Toplevel):
    """
    Optimized version of the real-time clock sync player.
    Reduces update frequency to improve responsiveness while maintaining sync.
    Includes all necessary methods and window layering fixes.
    """
    def __init__(self, master):
        super().__init__(master)
        self.title("Manage and Save Temporary Videos")
        self.geometry("900x700")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.transient(master)

        # Player state variables
        self.video_reader = None
        self.is_playing = False
        self.duration_seconds = 0
        self.fps = 1.0
        self.total_frames = 0
        self.current_frame_number = 0
        self.playback_job = None
        self.path_map = {}
        self.is_loading = False

        # Real-time clock sync variables
        self.playback_start_time = 0
        self.playback_start_frame = 0

        self.center_window()
        self.create_widgets()

        self.after(100, self.populate_file_list)

    def create_widgets(self):
        main_frame = tk.Frame(self)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        self.file_list = tk.Listbox(list_frame, width=50, selectmode=tk.EXTENDED)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_list.bind("<<ListboxSelect>>", self.on_file_select)
        list_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.config(yscrollcommand=list_scrollbar.set)

        player_container = tk.Frame(main_frame)
        player_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.video_label = tk.Label(player_container, bg="black", fg="white", text="Select a video to preview")
        self.video_label.pack(fill=tk.BOTH, expand=True)

        controls_frame = tk.Frame(player_container)
        controls_frame.pack(fill=tk.X, pady=5)
        self.play_pause_button = tk.Button(controls_frame, text="Play", width=10, command=self.toggle_play_pause, state=tk.DISABLED)
        self.play_pause_button.pack(side=tk.LEFT, padx=5)
        self.time_slider = ttk.Scale(controls_frame, from_=0, to=1, orient=tk.HORIZONTAL, value=0, state=tk.DISABLED)
        self.time_slider.bind("<ButtonPress-1>", self._on_slider_press)
        self.time_slider.bind("<ButtonRelease-1>", self._on_slider_release)
        self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.time_label = tk.Label(controls_frame, text="--:-- / --:--", width=12)
        self.time_label.pack(side=tk.LEFT, padx=5)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10, padx=10, fill=tk.X)
        self.merge_button = tk.Button(button_frame, text="Merge Selected", command=self.merge_selected_videos)
        self.merge_button.pack(side=tk.LEFT, padx=5)
        self.save_button = tk.Button(button_frame, text="Save Selected", command=self.save_selected)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = tk.Button(button_frame, text="Close", command=self._on_closing)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)

    def on_file_select(self, event=None):
        if self.is_loading: return
        selection_indices = self.file_list.curselection()
        if not selection_indices: return
        selected_filename = self.file_list.get(selection_indices[0])
        if selected_filename and "No temporary" not in selected_filename:
            full_path = self.path_map.get(selected_filename)
            if full_path and os.path.exists(full_path):
                self.video_label.config(image=None, text="Loading video...")
                self.is_loading = True
                self.update_idletasks()
                self.after(50, lambda: self.load_video(full_path))

    def load_video(self, file_path):
        self.stop_playback()
        try:
            self.video_reader = imageio.get_reader(file_path)
            metadata = self.video_reader.get_meta_data()
            self.duration_seconds = metadata.get('duration', 0)
            self.fps = metadata.get('fps', 30)
            if self.fps <= 0: self.fps = 30
            self.total_frames = int(self.duration_seconds * self.fps)

            self.play_pause_button.config(state=tk.NORMAL)
            self.time_slider.config(state=tk.NORMAL, to=self.duration_seconds, value=0)
            self.current_frame_number = 0
            self.is_playing = False
            self.play_pause_button.config(text="Play")

            self.display_frame(0)
            self.update_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read the video file.\n\nError: {e}", parent=self)
            self.video_reader = None
        finally:
            self.is_loading = False

    def display_frame(self, frame_number):
        if not self.video_reader: return
        try:
            frame = self.video_reader.get_data(frame_number)
            self.update_idletasks()
            label_w, label_h = self.video_label.winfo_width(), self.video_label.winfo_height()
            if label_w <= 1 or label_h <= 1: return

            img = Image.fromarray(frame)
            img.thumbnail((label_w, label_h), Image.Resampling.LANCZOS)
            photo_img = ImageTk.PhotoImage(image=img)
            self.video_label.config(image=photo_img, text="")
            self.video_label.image = photo_img
        except IndexError:
             self.stop_playback()
        except Exception as e:
            print(f"Error displaying frame {frame_number}: {e}")

    def toggle_play_pause(self):
        if not self.video_reader or self.is_loading: return
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_pause_button.config(text="Pause")
            self.start_playback()
        else:
            self.play_pause_button.config(text="Play")
            self.stop_playback()

    def start_playback(self):
        if not self.is_playing: return
        self.playback_start_time = time.time()
        self.playback_start_frame = self.current_frame_number
        self._playback_loop()

    def _playback_loop(self):
        if not self.is_playing: return

        target_preview_fps = 20
        delay_ms = int(1000 / target_preview_fps)

        elapsed_time = time.time() - self.playback_start_time
        target_frame = self.playback_start_frame + int(elapsed_time * self.fps)

        if target_frame >= self.total_frames:
            self.stop_playback()
            self.current_frame_number = self.total_frames - 1 if self.total_frames > 0 else 0
            self.display_frame(self.current_frame_number)
            self.update_ui()
            return

        if target_frame > self.current_frame_number:
            self.current_frame_number = target_frame
            self.display_frame(self.current_frame_number)

        self.update_ui()
        self.playback_job = self.after(delay_ms, self._playback_loop)

    def stop_playback(self):
        self.is_playing = False
        if self.playback_job:
            self.after_cancel(self.playback_job)
            self.playback_job = None
        if self.video_reader and self.play_pause_button.winfo_exists():
            self.play_pause_button.config(text="Play")

    def update_ui(self):
        if self.video_reader:
            current_seconds = self.current_frame_number / self.fps if self.fps > 0 else 0
            if current_seconds > self.duration_seconds:
                current_seconds = self.duration_seconds
            self.time_slider.set(current_seconds)

            duration_str = time.strftime('%M:%S', time.gmtime(self.duration_seconds))
            current_time_str = time.strftime('%M:%S', time.gmtime(current_seconds))
            self.time_label.config(text=f"{current_time_str} / {duration_str}")

    def _on_slider_press(self, event):
        if self.is_playing:
            self.was_playing = True
            self.stop_playback()
        else:
            self.was_playing = False

    def _on_slider_release(self, event):
        if self.video_reader:
            seek_seconds = self.time_slider.get()
            self.current_frame_number = int(seek_seconds * self.fps)
            if self.current_frame_number >= self.total_frames:
                self.current_frame_number = self.total_frames - 1 if self.total_frames > 0 else 0

            self.display_frame(self.current_frame_number)
            self.update_ui()

            if self.was_playing:
                self.is_playing = True
                self.play_pause_button.config(text="Pause")
                self.start_playback()

    def merge_selected_videos(self):
        self.stop_playback()
        selected_indices = self.file_list.curselection()
        if len(selected_indices) < 2:
            messagebox.showwarning("Selection Error", "Please select at least two files to merge.", parent=self)
            return
        selected_filenames = [self.file_list.get(i) for i in selected_indices]
        pids = set()
        pid_to_use = None
        for name in selected_filenames:
            match = re.search(r'whisper-live_(\d+)_', name)
            if match:
                pid_to_use = match.group(1)
                pids.add(pid_to_use)
        if len(pids) > 1:
            messagebox.showerror("Merge Error", "Cannot merge videos from different recording sources (PIDs).", parent=self)
            return
        if not pids:
            messagebox.showerror("Merge Error", "Could not identify the source of the selected files.", parent=self)
            return
        min_idx, max_idx = min(selected_indices), max(selected_indices)
        if len(selected_indices) != (max_idx - min_idx + 1):
            messagebox.showerror("Merge Error", "The selection must be a continuous block.", parent=self)
            return

        file_paths_to_merge = [self.path_map.get(name) for name in selected_filenames]
        final_file_list, temp_copies = [], []
        try:
            for path in file_paths_to_merge:
                if "_buf" in path:
                    copy_path = os.path.join(tempfile.gettempdir(), f"merge_copy_{os.path.basename(path)}")
                    shutil.copy(path, copy_path)
                    final_file_list.append(copy_path)
                    temp_copies.append(copy_path)
                else:
                    final_file_list.append(path)

            default_name = f"merged_timeshift-{pid_to_use}.avi"

            output_file = filedialog.asksaveasfilename(title="Save Merged Video As...", initialfile=default_name, filetypes=[("AVI video", "*.avi"), ("All files", "*.*")], parent=self)
            if not output_file: return

            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8') as f:
                for p in final_file_list: f.write(f"file '{p}'\n")
                list_file_path = f.name

            ffmpeg_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path, "-c", "copy", output_file]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            messagebox.showinfo("Success", f"Videos merged successfully into:\n{output_file}", parent=self)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("FFmpeg Error", f"Failed to merge videos.\n\n{e.stderr.decode('utf-8', 'ignore')}", parent=self)
        except Exception as e:
             messagebox.showerror("Error", f"An error occurred during the merge process: {e}", parent=self)
        finally:
            if 'list_file_path' in locals() and os.path.exists(list_file_path):
                os.remove(list_file_path)
            for copy in temp_copies:
                if os.path.exists(copy):
                    os.remove(copy)

    def save_selected(self):
        self.stop_playback()
        selected_filenames = [self.file_list.get(idx) for idx in self.file_list.curselection()]
        if not selected_filenames:
            messagebox.showwarning("No Files Selected", "No files were selected to save.", parent=self)
            return

        destination_dir = filedialog.askdirectory(title="Select Destination Folder", parent=self)
        if not destination_dir: return

        copied_count = 0
        skipped_count = 0

        for filename in selected_filenames:
            source_path = self.path_map.get(filename)
            if not source_path:
                continue

            destination_file_path = os.path.join(destination_dir, filename)

            should_copy = True
            if os.path.exists(destination_file_path):
                response = messagebox.askquestion(
                    "File Exists",
                    f"The file '{filename}' already exists.\nDo you want to overwrite it?",
                    icon='warning',
                    parent=self
                )
                if response == 'no':
                    should_copy = False
                    skipped_count += 1

            if should_copy:
                try:
                    shutil.copy(source_path, destination_file_path)
                    copied_count += 1
                except Exception as e:
                    skipped_count += 1
                    messagebox.showerror("Copy Error", f"Could not copy file '{filename}'.\n\nError: {e}", parent=self)

        messagebox.showinfo(
            "Copying Complete",
            f"Process finished.\n\nFiles copied: {copied_count}\nFiles skipped: {skipped_count}",
            parent=self
        )

    def _on_closing(self):
        self.stop_playback()
        if self.video_reader:
            self.video_reader.close()
        self.destroy()

    def center_window(self):
        self.update_idletasks()
        master = self.master
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')

    def populate_file_list(self):
        directory = "/tmp"
        pattern = os.path.join(directory, "whisper-live_*_*.avi")
        all_files = glob.glob(pattern)
        video_files = [f for f in all_files if not os.path.islink(f)]

        self.file_list.delete(0, tk.END)
        if not video_files:
            self.file_list.insert(tk.END, "No temporary video files found.")
            return

        try:
            sorted_files = sorted(video_files, key=lambda f: Path(f).stat().st_mtime)
        except FileNotFoundError:
            self.after(100, self.populate_file_list)
            return

        for file_path in sorted_files:
            self.file_list.insert(tk.END, os.path.basename(file_path))

        self.path_map = {os.path.basename(p): p for p in sorted_files}


class EnhancedStringDialog(tk.Toplevel):
    """
    A custom dialog class for Tkinter that prompts the user to enter a string.

    This dialog allows for an initial value to be set in the input field and provides
    standard dialog buttons (OK and Cancel). Additionally, it includes a context menu
    for cut, copy, paste, and delete actions within the entry widget.
    """

    def __init__(self, master, title, prompt_string, initial_value="", width=40):
        super().__init__(master)
        self.prompt_string = prompt_string + (" " * 2 * width)
        self.initial_value = initial_value
        self.width = width
        self.result = None
        self.transient(master)  # Set dialog to be transient with respect to master
        self.title(title)
        self.grab_set()  # Make the dialog modal

        self.body(self)
        self.buttonbox()
        self.protocol("WM_DELETE_WINDOW", self.cancel)  # Handle window close event

        self.center_window(master)
        self.wait_window(self)  # Wait until this window is closed

    def body(self, master):
        self.entry_label = tk.Label(master, text=self.prompt_string, padx=5)
        self.entry_label.pack(padx=5, pady=5, anchor='center')
        self.entry = tk.Entry(master, width=self.width)
        self.entry.pack(padx=5, pady=5, anchor='center')
        self.entry.insert(0, self.initial_value)  # Insert initial value into the entry
        self.entry.focus_set()  # Set focus to the entry widget
        self.entry.bind("<Button-3>", self.show_popup_menu)  # Bind right-click to show popup menu

    def buttonbox(self):
        box = tk.Frame(self)
        ok_button = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        ok_button.pack(side=tk.LEFT, padx=5, pady=5)
        cancel_button = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
        box.pack(anchor='center')

    def ok(self, event=None):
        self.apply()  # Save the current value of the entry
        self.cancel()  # Close the dialog

    def cancel(self, event=None):
        self.master.focus_set()  # Return focus to the master window
        self.destroy()  # Destroy the dialog

    def apply(self):
        self.result = self.entry.get()  # Get the value from the entry widget

    def show_popup_menu(self, event):
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Cut", command=self.cut)
        self.popup_menu.add_command(label="Copy", command=self.copy)
        self.popup_menu.add_command(label="Paste", command=self.paste)
        self.popup_menu.add_command(label="Delete", command=self.delete)
        self.popup_menu.tk_popup(event.x_root, event.y_root)  # Show the popup menu at the cursor position

    def cut(self):
        if self.entry.selection_present():
            selected_text = self.entry.selection_get()
            self.copy_to_clipboard(selected_text)  # Copy selected text to clipboard
            self.entry.delete(tk.SEL_FIRST, tk.SEL_LAST)  # Delete the selected text

    def copy(self):
        if self.entry.selection_present():
            selected_text = self.entry.selection_get()
            self.copy_to_clipboard(selected_text)  # Copy selected text to clipboard

    def paste(self):
        if self.entry.selection_present():
            self.entry.delete(tk.SEL_FIRST, tk.SEL_LAST)  # Delete selected text
        clipboard_text = self.master.clipboard_get()
        if clipboard_text is not None:
            self.entry.insert(tk.INSERT, clipboard_text)  # Insert clipboard text at cursor position

    def delete(self):
        if self.entry.selection_present():
            self.entry.delete(tk.SEL_FIRST, tk.SEL_LAST)  # Delete selected text

    def copy_to_clipboard(self, text):
        if text is not None:
            self.master.clipboard_clear()  # Clear the clipboard
            self.master.clipboard_append(text)  # Append text to the clipboard

    def center_window(self, master):
        self.update_idletasks()  # Update "requested size" from geometry manager

        # Get the main window's size and position
        master_width = master.winfo_width()
        master_height = master.winfo_height()
        master_x = master.winfo_x()
        master_y = master.winfo_y()

        # Get the dialog's size
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        # Calculate the position to center the dialog in the main window
        x = master_x + (master_width // 2) - (dialog_width // 2)
        y = master_y + (master_height // 2) - (dialog_height // 2)

        self.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')


class M3uPlaylistPlayer(tk.Frame):
    """
    A custom Tkinter frame for playing M3U playlists.

    This class represents a frame designed for playing M3U playlists. It includes functionality
    for displaying playlist items, managing options, and handling playback events.

    Attributes:
        parent: The parent widget of the frame.
        spec: The specification of the playlist.
        bash_script: The bash script used for playing playlist items.
        error_messages: A queue for storing error messages during playback.
        main_window: The main Tkinter window.
    """

    def __init__(self, parent, spec, bash_script, error_messages, main_window):
        super().__init__(parent)
        self.root = parent
        self.main_window = main_window  # Store main_window reference

        self.spec = spec
        self.bash_script = bash_script
        self.error_messages = error_messages
        self.current_options = {}
        self.list_number = 0
        self.playlist = []
        self.subtitles = ""
        self.selected_model_old = ""
        self._dragging_item = None  # new attribute for drag-and-drop
        self.create_widgets()
        self.populate_playlist()
        self.load_options()

    def create_widgets(self):

        # Search box frame
        self.search_frame = tk.Frame(self)
        self.search_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.search_label = tk.Label(self.search_frame, text="Search:")
        self.search_label.pack(side=tk.LEFT, padx=5)

        self.search_entry = tk.Entry(self.search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_playlist)
        self.search_entry.bind("<Button-3>", self.show_popup_menu)

        # Label to display the search match count, now positioned after the entry box.
        self.search_count_label = tk.Label(self.search_frame, text="0/0")
        self.search_count_label.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_button = tk.Button(self.search_frame, text="Clear", command=self.clear_search)
        self.clear_button.pack(side=tk.LEFT, padx=2)

        self.prev_button = tk.Button(self.search_frame, text="Prev", command=self.prev_match)
        self.prev_button.pack(side=tk.LEFT, padx=2)

        self.next_button = tk.Button(self.search_frame, text="Next", command=self.next_match)
        self.next_button.pack(side=tk.LEFT, padx=2)

        # Treeview for playlist
        self.tree = ttk.Treeview(self, columns=("list_number", "name", "url"), show="headings")
        self.tree.heading("list_number", text="#")
        self.tree.heading("name", text="Channel")
        self.tree.heading("url", text="URL")
        self.tree.column("list_number", width=35, stretch=False, minwidth=15)
        self.tree.column("name", width=200, stretch=True, minwidth=50)
        self.tree.column("url", width=400, stretch=True, minwidth=50)
        self.tree.bind('<Double-Button-1>', self.play_channel)
        # Bind mouse dragging events for drag-and-drop
        self.tree.bind('<ButtonPress-1>', self.on_treeview_button_press)
        self.tree.bind('<B1-Motion>', self.on_treeview_motion)
        self.tree.bind('<ButtonRelease-1>', self.on_treeview_button_release)
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

        # Executable selector
        self.executable_label = tk.Label(self.options_frame0, text="Executable", padx=10)
        self.executable_label.pack(side=tk.LEFT)

        self.executable_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.executable_frame.pack(side=tk.LEFT)

        self.executable = tk.StringVar(value=default_executable)

        def update_executable_button():
            selected_option = self.executable.get()
            self.executable_option_menu.configure(text=selected_option)
            self.save_options()

        self.executable_option_menu = tk.Menubutton(self.executable_frame, textvariable=self.executable, indicatoron=True,
                                                  relief="raised")
        self.executable_option_menu.pack(side=tk.LEFT)

        executable_menu = tk.Menu(self.executable_option_menu, tearoff=0)
        self.executable_option_menu.configure(menu=executable_menu)

        for exe in whisper_executables:
            if shutil.which(exe) is not None:
                executable_menu.add_radiobutton(label=exe, value=exe, variable=self.executable,
                                              command=update_executable_button)
            else:
                executable_menu.add_radiobutton(label=exe, value=exe, variable=self.executable,
                                              command=update_executable_button, state="disabled")

        self.executable_option_menu.bind("<<MenuSelect>>", lambda e: update_executable_button())

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
        self.models_installed = []
        self.update_installed_models()

        self.model_label = tk.Label(self.options_frame0, text="Model", padx=4)
        self.model_label.pack(side=tk.LEFT)

        self.model_frame = tk.Frame(self.options_frame0, highlightthickness=1, highlightbackground="black")
        self.model_frame.pack(side=tk.LEFT)

        self.model = tk.StringVar(value="base")
        self.model_option_menu = tk.Menubutton(self.model_frame, textvariable=self.model, indicatoron=True, relief="raised")
        self.model_option_menu.pack(side=tk.LEFT)

        self.model_menu = tk.Menu(self.model_option_menu, tearoff=0)
        self.model_option_menu.configure(menu=self.model_menu)

        self.update_model_menu()  # Initialize the model menu


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

        # Second Down Frame

        self.options_frame1 = tk.LabelFrame(self.container_frame, text=options_frame1_text, padx=10, pady=2)

        self.options_frame1.pack(fill="both", expand=True, padx=10, pady=2)

        # Online translation
        self.online_translation_label = tk.Label(self.options_frame1, text="Online translation", padx=10)
        self.online_translation_label.pack(side=tk.LEFT)

        self.online_translation_frame = tk.Frame(self.options_frame1, highlightthickness=1, highlightbackground="black")
        self.online_translation_frame.pack(side=tk.LEFT)

        self.online_translation = tk.BooleanVar(value=False)
        self.online_translation_checkbox = tk.Checkbutton(self.online_translation_frame, variable=self.online_translation, onvalue=True,
                                                 offvalue=False, command=self.save_options)
        self.online_translation_checkbox.pack(side=tk.LEFT)

        # Translation language

        # Regions and their languages
        self.trans_language_label = tk.Label(self.options_frame1, text="Language translation", padx=4)
        self.trans_language_label.pack(side=tk.LEFT)

        self.trans_language_frame = tk.Frame(self.options_frame1, highlightthickness=1, highlightbackground="black")
        self.trans_language_frame.pack(side=tk.LEFT)

        self.trans_language = tk.StringVar(value="en (English)")

        def update_trans_language_button():
            selected_option = self.trans_language.get()
            self.trans_language_option_menu.configure(text=selected_option)
            self.save_options()

        self.trans_language_option_menu = tk.Menubutton(self.trans_language_frame, textvariable=self.trans_language, indicatoron=True,
                                                  relief="raised")
        self.trans_language_option_menu.pack(side=tk.LEFT)

        trans_language_menu = tk.Menu(self.trans_language_option_menu, tearoff=0)
        self.trans_language_option_menu.configure(menu=trans_language_menu)

        for region, langs in regions.items():
            sublanguage_menu = tk.Menu(trans_language_menu, tearoff=0)
            for lang in langs:
                lang_name = lang_codes.get(lang)
                full_language_name = f"{lang} ({lang_name})"
                sublanguage_menu.add_radiobutton(label=full_language_name, value=full_language_name,
                                                 variable=self.trans_language, command=update_trans_language_button)
            trans_language_menu.add_cascade(label=region, menu=sublanguage_menu)

        self.trans_language_option_menu["menu"] = trans_language_menu

        self.trans_language_option_menu.bind("<<MenuSelect>>", lambda e: update_trans_language_button())

        # Output text
        output_text = ["original", "translation", "both", "none"]

        self.output_text_label = tk.Label(self.options_frame1, text="Output text", padx=10)
        self.output_text_label.pack(side=tk.LEFT)

        self.output_text_frame = tk.Frame(self.options_frame1, highlightthickness=1, highlightbackground="black")
        self.output_text_frame.pack(side=tk.LEFT)

        self.output_text = tk.StringVar(value="original")

        def update_output_text_button():
            selected_option = self.output_text.get()
            self.output_text_option_menu.configure(text=selected_option)
            self.save_options()

        self.output_text_option_menu = tk.Menubutton(self.output_text_frame, textvariable=self.output_text, indicatoron=True,
                                                 relief="raised")
        self.output_text_option_menu.pack(side=tk.LEFT)

        output_text_menu = tk.Menu(self.output_text_option_menu, tearoff=0)
        self.output_text_option_menu.configure(menu=output_text_menu)

        for qua in output_text:
            output_text_menu.add_radiobutton(label=qua, value=qua, variable=self.output_text, command=update_output_text_button)

        self.output_text_option_menu.bind("<<MenuSelect>>", lambda e: update_output_text_button())

        # text-to-speech
        self.speak_label = tk.Label(self.options_frame1, text="Text-to-Speech", padx=10)
        self.speak_label.pack(side=tk.LEFT)

        self.speak_frame = tk.Frame(self.options_frame1, highlightthickness=1, highlightbackground="black")
        self.speak_frame.pack(side=tk.LEFT)

        self.speak = tk.BooleanVar(value=False)
        self.speak_checkbox = tk.Checkbutton(self.speak_frame, variable=self.speak, onvalue=True,
                                                 offvalue=False, command=self.save_options)
        self.speak_checkbox.pack(side=tk.LEFT)

        self.save_text_button = tk.Button(self.options_frame1, text="Save texts", command=self.select_files)
        self.save_text_button.pack(side=tk.RIGHT, padx=10)


        # Third Down Frame

        self.options_frame2 = tk.Frame(self.container_frame)
        self.options_frame2.pack(side=tk.TOP, anchor=tk.W)

        # Quality
        quality = ["raw", "upper", "lower"]

        self.quality_label = tk.Label(self.options_frame2, text="Video Quality", padx=10)
        self.quality_label.pack(side=tk.LEFT)

        self.quality_frame = tk.Frame(self.options_frame2, highlightthickness=1, highlightbackground="black")
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
        self.playeronly_label = tk.Label(self.options_frame2, text="Player Only", padx=4)
        self.playeronly_label.pack(side=tk.LEFT)

        self.playeronly_frame = tk.Frame(self.options_frame2, highlightthickness=1, highlightbackground="black")
        self.playeronly_frame.pack(side=tk.LEFT)

        self.playeronly = tk.BooleanVar(value=False)
        self.playeronly_checkbox = tk.Checkbutton(self.playeronly_frame, variable=self.playeronly, onvalue=True,
                                                  offvalue=False, command=self.save_options)
        self.playeronly_checkbox.pack(side=tk.LEFT)

        # Players
        self.player_label = tk.Label(self.options_frame2, text="Player", padx=4)
        self.player_label.pack(side=tk.LEFT)

        self.player_frame = tk.Frame(self.options_frame2, highlightthickness=1, highlightbackground="black")
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
        self.mpv_options_label = tk.Label(self.options_frame2, text="Player Options", padx=4)
        self.mpv_options_label.pack(side=tk.LEFT)

        self.mpv_options_entry = tk.Entry(self.options_frame2, width=44)
        self.mpv_options_entry.insert(0, self.current_options.get("mpv_options", ""))
        self.mpv_options_entry.pack(side=tk.LEFT)

        self.mpv_options_entry.bind("<KeyRelease>", self.schedule_save_options)

        self.mpv_options_entry.bind("<Button-3>", self.show_popup_menu)

        self.mpv_fg = self.mpv_options_entry.cget("fg")
        self.mpv_bg = self.mpv_options_entry.cget("bg")


        # Fourth Down Frame

        self.options_frame3 = tk.LabelFrame(self.container_frame, text=options_frame3_text, padx=10, pady=2)

        self.options_frame3.pack(fill="both", expand=True, padx=10, pady=2)

        # Timeshift
        self.timeshiftactive_label = tk.Label(self.options_frame3, text="Timeshift", padx=10)
        self.timeshiftactive_label.pack(side=tk.LEFT)

        self.timeshiftactive_frame = tk.Frame(self.options_frame3, highlightthickness=1, highlightbackground="black")
        self.timeshiftactive_frame.pack(side=tk.LEFT)

        self.timeshiftactive = tk.BooleanVar(value=False)
        self.timeshiftactive_checkbox = tk.Checkbutton(self.timeshiftactive_frame, variable=self.timeshiftactive, onvalue=True,
                                                 offvalue=False, command=self.save_options)
        self.timeshiftactive_checkbox.pack(side=tk.LEFT)

        # Synchronization
        self.sync_label = tk.Label(self.options_frame3, text="Synchronization(sec)", padx=4)
        self.sync_label.pack(side=tk.LEFT)

        self.sync_frame = tk.Frame(self.options_frame3, highlightthickness=1, highlightbackground="black")
        self.sync_frame.pack(side=tk.LEFT)

        self.sync_options_id = None
        self.sync = tk.StringVar(value="3")
        self.sync_spinner = tk.Spinbox(self.sync_frame, from_=0, to=57, width=2, textvariable=self.sync,
                                         command=self.schedule_save_options)
        self.sync_spinner.pack(side=tk.LEFT)

        self.sync_spinner.bind("<KeyRelease>", self.schedule_save_options)

        # Segments
        self.segments_label = tk.Label(self.options_frame3, text="Segments", padx=4)
        self.segments_label.pack(side=tk.LEFT)

        self.segments_frame = tk.Frame(self.options_frame3, highlightthickness=1, highlightbackground="black")
        self.segments_frame.pack(side=tk.LEFT)

        self.save_options_id = None
        self.segments = tk.StringVar(value="4")
        self.segments_spinner = tk.Spinbox(self.segments_frame, from_=2, to=99, width=2, textvariable=self.segments,
                                         command=self.schedule_save_options)
        self.segments_spinner.pack(side=tk.LEFT)

        self.segments_spinner.bind("<KeyRelease>", self.schedule_save_options)

        # Segment time
        self.segment_time_label = tk.Label(self.options_frame3, text="Segment Time(minutes)", padx=4)
        self.segment_time_label.pack(side=tk.LEFT)

        self.segment_time_frame = tk.Frame(self.options_frame3, highlightthickness=1, highlightbackground="black")
        self.segment_time_frame.pack(side=tk.LEFT)

        self.segment_time_options_id = None
        self.segment_time = tk.StringVar(value="10")
        self.segment_time_spinner = tk.Spinbox(self.segment_time_frame, from_=1, to=99, width=2, textvariable=self.segment_time,
                                         command=self.schedule_save_options)
        self.segment_time_spinner.pack(side=tk.LEFT)

        self.segment_time_spinner.bind("<KeyRelease>", self.schedule_save_options)

        self.save_videos_button = tk.Button(self.options_frame3, text="Save Videos", padx=5, command=self.open_video_saver)
        self.save_videos_button.pack(side=tk.LEFT, padx=(10, 0))

        self.delete_videos_button = tk.Button(self.options_frame3, text="Delete all temp files", padx=5, command=self.delete_videos)
        self.delete_videos_button.pack(side=tk.LEFT, padx=(10, 10))


        # Buttons

        # Bottom options frame with Global Options and Playlist buttons
        self.bottom_frame = tk.Frame(self.container_frame)
        self.bottom_frame.pack(side=tk.LEFT, expand=True, padx=1, pady=10)

        # Global options frame on left side of bottom
        self.global_options_frame = tk.Frame(self.bottom_frame)
        self.global_options_frame.pack(side=tk.LEFT, padx=10)

        self.override_label = tk.Label(self.global_options_frame, text="Global options")
        self.override_label.pack(side=tk.TOP)

        self.override_options = tk.BooleanVar()
        self.override_checkbox = tk.Checkbutton(self.global_options_frame, variable=self.override_options,
                                            command=self.change_override)
        self.override_checkbox.pack(side=tk.TOP)

        # Playlist buttons on right side of bottom
        self.options_frame4 = tk.Frame(self.bottom_frame)
        self.options_frame4.pack(side=tk.LEFT, expand=True, padx=1)

        self.playlist_label = tk.Label(self.options_frame4, text="Playlist")
        self.playlist_label.pack(side=tk.TOP)

        self.load_button = tk.Button(self.options_frame4, text="Load", command=self.load_playlist, padx=4)
        self.load_button.pack(side=tk.LEFT)

        self.append_button = tk.Button(self.options_frame4, text="Append", command=self.append_playlist, padx=4)
        self.append_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(self.options_frame4, text="Save", command=self.save_playlist, padx=4)
        self.save_button.pack(side=tk.LEFT)


        self.options_frame5 = tk.Frame(self.container_frame)
        self.options_frame5.pack(side=tk.LEFT, expand=True, pady=2)

        self.channel_label = tk.Label(self.options_frame5, text="Channel/Media File/Audio source")
        self.channel_label.pack(side=tk.TOP)

        self.add_label = tk.Label(self.options_frame5, text="", padx=2)
        self.add_label.pack(side=tk.LEFT)

        self.add_button = tk.Button(self.options_frame5, text="Add URL", command=self.add_channel, padx=4)
        self.add_button.pack(side=tk.LEFT)

        self.add_file_button = tk.Button(self.options_frame5, text="Add File", command=self.add_file_channel, padx=4)
        self.add_file_button.pack(side=tk.LEFT)

        self.add_audio_button = tk.Button(self.options_frame5, text="Add Audio", command=self.add_audio_source, padx=4)
        self.add_audio_button.pack(side=tk.LEFT)

        self.delete_button = tk.Button(self.options_frame5, text="Delete", command=self.delete_channel, padx=4)
        self.delete_button.pack(side=tk.LEFT)

        self.edit_button = tk.Button(self.options_frame5, text="Edit", command=self.edit_channel, padx=4)
        self.edit_button.pack(side=tk.LEFT)

        self.move_up_button = tk.Button(self.options_frame5, text="Move up", command=self.move_up_channel, padx=4)
        self.move_up_button.pack(side=tk.LEFT)

        self.move_down_button = tk.Button(self.options_frame5, text="Move down", command=self.move_down_channel, padx=4)
        self.move_down_button.pack(side=tk.LEFT)

        self.options_frame6 = tk.Frame(self.container_frame)
        self.options_frame6.pack(side=tk.LEFT, expand=True, pady=2)

        self.subtitles_label = tk.Label(self.options_frame6, text="Subtitles")
        self.subtitles_label.pack(side=tk.TOP)

        self.subtitles_label2 = tk.Label(self.options_frame6, text="", padx=2)
        self.subtitles_label2.pack(side=tk.LEFT)

        self.subtitles_button = tk.Button(self.options_frame6, text="Generate", command=self.generate_subtitles, padx=4)
        self.subtitles_button.pack(side=tk.LEFT)

        self.split_video_button = tk.Button(self.options_frame6, text="Split File", command=self.split_video, padx=4)
        self.split_video_button.pack(side=tk.LEFT, padx=(5, 0)) # Add some padding to the left

        self.options_frame7 = tk.Frame(self.container_frame)
        self.options_frame7.pack(side=tk.LEFT, expand=True, pady=2)

        self.about_label = tk.Label(self.options_frame7, text="")
        self.about_label.pack(side=tk.TOP)

        self.about_label2 = tk.Label(self.options_frame7, text="", padx=4)
        self.about_label2.pack(side=tk.LEFT)

        self.about_button = tk.Button(self.options_frame7, text="About", command=self.show_about_window, padx=4)
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
            err_message = ("File Not Found", f"The default playlist_{self.spec}.m3u file was not found.")
            self.error_messages.put(err_message)


    def update_installed_models(self):
        self.models_installed = []

        if self.executable == "whisper":
            self.models_installed = models
        else:
            for model in models:
                if os.path.exists(model_path.format(model)):
                    self.models_installed.append(model)
                for suffix in suffixes:
                    full_model_name = f"{model}{suffix}"
                    if os.path.exists(model_path.format(full_model_name)):
                        self.models_installed.append(full_model_name)


    def update_model_menu(self):
        self.model_menu.delete(0, tk.END)

        default_fg = tk.Label().cget("fg")
        disabled_fg = tk.Label().cget("disabledforeground")

        for model in models:
            suffix_menu = tk.Menu(self.model_menu, tearoff=0)
            model_installed = model in self.models_installed

            suffix_menu.add_radiobutton(
                label=f"{model}*" if model_installed else model,
                value=model,
                variable=self.model,
                command=self.update_model_button,
                state="normal",
                foreground=default_fg if model_installed else disabled_fg,
                activeforeground=default_fg if model_installed else disabled_fg,
                activebackground="white",
            )

            for suffix in suffixes:
                full_model_name = f"{model}{suffix}"
                model_suffix_installed = full_model_name in self.models_installed

                suffix_menu.add_radiobutton(
                    label=f"{full_model_name}*" if model_suffix_installed else full_model_name,
                    value=full_model_name,
                    variable=self.model,
                    command=self.update_model_button,
                    state="normal",
                    foreground=default_fg if model_suffix_installed else disabled_fg,
                    activeforeground=default_fg if model_suffix_installed else disabled_fg,
                    activebackground="white",
                )

            self.model_menu.add_cascade(label=model, menu=suffix_menu)

        self.model_option_menu.grab_release()

    def install_model(self, model_name):
        terminal = self.terminal.get()

        if quantize_executable:  # Check if quantize_executable is not None
            try:
                base_model, suffix = self.parse_model_name(model_name)

                if terminal == "gnome-terminal" and subprocess.run(["gnome-terminal", "--version"]).returncode == 0:
                    if suffix:
                        subprocess.Popen(["gnome-terminal", "--tab", "--", "/bin/bash", "-c", f"make {base_model}; {quantize_executable} ./models/ggml-{base_model}.bin ./models/ggml-{model_name}.bin {suffix.lstrip('-')}; exit"])
                    else:
                        subprocess.Popen(["gnome-terminal", "--tab", "--", "/bin/bash", "-c", f"make {model_name}; exit"])

                elif terminal == "konsole" and subprocess.run(["konsole", "--version"]).returncode == 0:
                    if suffix:
                        script_content = f"""\
                                        make {base_model}
                                        {quantize_executable} ./models/ggml-{base_model}.bin ./models/ggml-{model_name}.bin {suffix.lstrip('-')}
                                        """
                    else:
                        script_content = f"make {model_name}"
                    subprocess.Popen(["konsole", "-e", f"bash -c '{script_content}'"])

                elif terminal == "lxterm" and subprocess.run(["lxterm", "-version"]).returncode == 0:
                    if suffix:
                        subprocess.Popen(["lxterm", "-e", f"make {base_model}; {quantize_executable} ./models/ggml-{base_model}.bin ./models/ggml-{model_name}.bin {suffix.lstrip('-')}"])
                    else:
                        subprocess.Popen(["lxterm", "-e", f"make {model_name}"])

                elif terminal == "mate-terminal" and subprocess.run(["mate-terminal", "--version"]).returncode == 0:
                    if suffix:
                        script_content = f"""\
                                        make {base_model}
                                        {quantize_executable} ./models/ggml-{base_model}.bin ./models/ggml-{model_name}.bin {suffix.lstrip('-')}
                                        """
                    else:
                        script_content = f"make {model_name}"

                    subprocess.Popen(["mate-terminal", "-e", f"bash -c '{script_content}'"])
                elif terminal == "mlterm":
                    result = subprocess.run(["mlterm", "--version"], capture_output=True, text=True)
                    mlterm_output = result.stdout
                    if "mlterm" in mlterm_output:
                        if suffix:
                            script_content = f"""\
                                            bash -c '
                                            make {base_model}
                                            {quantize_executable} ./models/ggml-{base_model}.bin ./models/ggml-{model_name}.bin {suffix.lstrip('-')}'
                                            """
                        else:
                            script_content = f"""\
                                            bash -c '
                                            make {model_name}'
                                            """
                        subprocess.Popen(["bash", "-c", f"mlterm -e {script_content}"])


                elif terminal == "xfce4-terminal" and subprocess.run(["xfce4-terminal", "--version"]).returncode == 0:
                    if suffix:
                        script_content = f"""\
                                        make {base_model}
                                        {quantize_executable} ./models/ggml-{base_model}.bin ./models/ggml-{model_name}.bin {suffix.lstrip('-')}
                                        """
                    else:
                        script_content = f"make {model_name}"

                    subprocess.Popen(["xfce4-terminal", "-e", f"bash -c '{script_content}'"])

                elif terminal == "xterm" and subprocess.run(["xterm", "-version"]).returncode == 0:
                    if suffix:
                        script_content = f"""\
                                        make {base_model}
                                        {quantize_executable} ./models/ggml-{base_model}.bin ./models/ggml-{model_name}.bin {suffix.lstrip('-')}
                                        """
                    else:
                        script_content = f"make {model_name}"

                    subprocess.Popen(["xterm", "-e", f"bash -c '{script_content}'"])

                else:
                    err_message = "No compatible terminal found."
                    print(err_message)
                    messagebox.showerror("Error", err_message)

                root = tk.Toplevel(self.master)
                root.title("Model Installation")
                root.transient(self.master)
                root.grab_set()
                root.focus_force()
                root.resizable(False, False)
                root.attributes('-topmost', False)

                root.update_idletasks()
                width = 600
                height = 100
                x = (root.winfo_screenwidth() // 2) - (width // 2)
                y = (root.winfo_screenheight() // 2) - (height // 2)
                root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

                message = f"Installing {model_name} model. Please note that the model will be installed may not be optimized for an accelerated version of Whisper-cpp. Please wait..."
                label = tk.Label(root, text=message, wraplength=550, justify="left")
                label.pack(padx=20, pady=20)

                root.update()
                time.sleep(5)
                # Get the PIDs of all processes containing the command "make {base_model}"
                process_ids = self.find_make_model_processes(base_model)

                # Wait for all found processes to finish
                if process_ids:
                    self.wait_for_process_completion(process_ids, f"make {base_model}")
                else:
                    print("No processes found to wait for.")


                root.grab_release()
                root.destroy()


            except OSError as e:
                print("Error executing command:", e)
                messagebox.showerror("Error", "Error executing command.")
        else:
            err_message = "Quantize executable does not exist."
            print(err_message)
            messagebox.showerror("Error", err_message)


    def find_make_model_processes(self, base_model):
        try:
            result = subprocess.run(["ps", "x"], capture_output=True, text=True)
            process_ids = []
            for line in result.stdout.split("\n"):
                columns = line.split()
                if len(columns) > 4:
                    command = columns[4:]
                    full_command = ' '.join(command)
                    if f"make {base_model}" in full_command:
                        pid = columns[0]
                        process_ids.append(pid)
            return process_ids
        except Exception as e:
            print(f"Error finding 'make {base_model}' processes: {e}")
            return []

    def wait_for_process_completion(self, pids, process_name):
        timeout = 5
        for pid in pids:
            while True:
                time.sleep(1)
                try:
                    check_pid = subprocess.run(["ps", "-p", str(pid), "-o", "command"], capture_output=True, text=True, timeout=timeout).stdout.strip()
                    if process_name not in check_pid:
                        print(f"Process {pid} has finished.")
                        break
                except subprocess.TimeoutExpired:
                    print(f"Process {pid} ({process_name}) has finished (timeout expired).")
                    break


    def parse_model_name(self, model_name):
        suffix = ""
        if model_name in models:
            base_model = model_name
        else:
            for model in models:
                for sfx in suffixes:
                    full_model_name = f"{model}{sfx}"
                    if full_model_name == model_name:
                        base_model = model
                        suffix = sfx
                        break
                if suffix:
                    break

        return base_model, suffix


    def update_model_button(self):
        selected_option = self.model.get()
        if selected_option not in self.models_installed:
            action = messagebox.askquestion("Model Installation",
                                            f"The model {selected_option} is not installed. Do you want to install it?",
                                            icon='warning',
                                            type='yesnocancel',
                                            default='yes')
            if action == 'yes':
                self.install_model(selected_option)
                self.update_installed_models()
                self.update_model_menu()

                if os.path.exists(model_path.format(selected_option)):
                    self.model_option_menu.configure(text=selected_option)
                    self.save_options()
                    err_message = f"Successfully installed {selected_option} model."
                    print(err_message)
                    messagebox.showinfo("Model Installed", err_message)
                else:
                    self.model_option_menu.configure(text=self.selected_model_old)
                    self.model.set(self.selected_model_old)
                    err_message = f"The model {selected_option} could not be installed."
                    print(err_message)
                    messagebox.showerror("Error", err_message)
            else:
                self.model_option_menu.configure(text=self.selected_model_old)
                self.model.set(self.selected_model_old)

        else:
            self.model_option_menu.configure(text=selected_option)
            self.save_options()


    def widgets_updates(self):
        executable_option = self.current_options["executable_option"]
        terminal_option = self.current_options["terminal_option"]
        bash_options = self.current_options["bash_options"]
        playeronly_option = self.current_options["playeronly_option"]
        player_option = self.current_options["player_option"]
        mpv_options = self.current_options["mpv_options"]
        timeshiftactive_option = self.current_options["timeshiftactive_option"]
        timeshift_options = self.current_options["timeshift_options"]
        online_translation_option = self.current_options["online_translation_option"]
        trans_options = self.current_options["trans_options"]

        self.executable_frame.config(highlightthickness=1, highlightbackground="black")
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
        self.online_translation_frame.config(highlightthickness=1, highlightbackground="black")
        self.trans_language_frame.config(highlightthickness=1, highlightbackground="black")
        self.output_text_frame.config(highlightthickness=1, highlightbackground="black")
        self.speak_frame.config(highlightthickness=1, highlightbackground="black")

        if not self.override_options.get():
            self.mpv_options_entry.config(fg=self.mpv_fg, bg=self.mpv_bg, insertbackground=self.mpv_fg)
            selection = self.tree.focus()
            if selection:
                url = self.tree.item(selection, "values")[2]
                if url in self.current_options:
                    executable_option = self.current_options[url].get("executable_option", "")
                    terminal_option = self.current_options[url].get("terminal_option", "")
                    bash_options = self.current_options[url].get("bash_options", "")
                    playeronly_option = self.current_options[url].get("playeronly_option", "")
                    player_option = self.current_options[url].get("player_option", "")
                    mpv_options = self.current_options[url].get("mpv_options", "")
                    timeshiftactive_option = self.current_options[url].get("timeshiftactive_option", "")
                    timeshift_options = self.current_options[url].get("timeshift_options", "")
                    online_translation_option = self.current_options[url].get("online_translation_option", "")
                    trans_options = self.current_options[url].get("trans_options", "")

                    self.executable_frame.config(highlightthickness=1, highlightbackground="red")
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
                    self.online_translation_frame.config(highlightthickness=1, highlightbackground="red")
                    self.trans_language_frame.config(highlightthickness=1, highlightbackground="red")
                    self.output_text_frame.config(highlightthickness=1, highlightbackground="red")
                    self.speak_frame.config(highlightthickness=1, highlightbackground="red")
        else:
            self.mpv_options_entry.config(fg=self.mpv_bg, bg=self.mpv_fg, insertbackground=self.mpv_bg)

        self.terminal_option_menu.unbind("<<MenuSelect>>")
        self.terminal.set(terminal_option)
        self.terminal_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())

        if not terminal_option in terminal_installed:
            err_message = ("Terminal Not Installed", f"Warning: Terminal {terminal_option} was not found. Please install it" \
                          f" or choose other terminal.")
            self.error_messages.put(err_message)

        # Set executable with error checking
        self.executable_option_menu.unbind("<<MenuSelect>>")
        self.executable.set(executable_option)
        self.executable_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())

        if shutil.which(executable_option) is None:
            err_message = ("Whisper executable Not Installed", f"Warning: Whisper executable {executable_option} was not found. Please install it" \
                          f" or choose other.")
            self.error_messages.put(err_message)

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
                self.selected_model_old = self.model.get()
                self.model_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
                if not option in self.models_installed:
                    model_path = "./models/ggml-{}.bin".format(option)
                    err_message = ("Model Not Installed", f"Warning: File for model {option} was not found. " \
                                  f"Please install it in {model_path} or choose other model.")
                    self.error_messages.put(err_message)
            elif option in lang_codes:
                self.language_option_menu.unbind("<<MenuSelect>>")
                lang_name = lang_codes.get(option)
                full_language_name = f"{option} ({lang_name})"
                self.language.set(full_language_name)
                self.language_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
            else:
                err_message=("Wrong option",f"Wrong option {option} found, try again after deleting"
                                                    f" config_{self.spec}.json file")
                self.error_messages.put(err_message)

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
            err_message=("Wrong option",f"Wrong option {option} found, try again after deleting"
                                                    f" config_{self.spec}.json file")
            self.error_messages.put(err_message)

        option = options_list.pop(0)
        if option.isdigit() and (2 <= int(option) <= 99):
            self.segments.set(option)
            self.segments_spinner.update()
        else:
            err_message=("Wrong option",f"Wrong option {option} found, try again after deleting"
                                                f" config_{self.spec}.json file")
            self.error_messages.put(err_message)

        option = options_list.pop(0)
        if option.isdigit() and (1 <= int(option) <= 99):
            self.segment_time.set(option)
            self.segment_time_spinner.update()
        else:
            err_message=("Wrong option",f"Wrong option {option} found, try again after deleting"
                                                    f" config_{self.spec}.json file")
            self.error_messages.put(err_message)

        options_list = trans_options.split()
        self.speak.set(False)
        while options_list:
            option = options_list.pop(0)
            if option in lang_codes:
                self.trans_language_option_menu.unbind("<<MenuSelect>>")
                lang_name = lang_codes.get(option)
                full_language_name = f"{option} ({lang_name})"
                self.trans_language.set(full_language_name)
                self.trans_language_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
            elif option in ["original", "translation", "both", "none"]:
                self.output_text_option_menu.unbind("<<MenuSelect>>")
                self.output_text.set(option)
                self.output_text_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
            elif option == "speak":
                self.speak.set(True)
            else:
                err_message=("Wrong option",f"Wrong option {option} found, try again after deleting"
                                                    f" config_{self.spec}.json file")
                self.error_messages.put(err_message)

        self.playeronly.set(playeronly_option)
        self.player_option_menu.unbind("<<MenuSelect>>")
        self.player.set(player_option)
        self.player_option_menu.bind("<<MenuSelect>>", lambda e: self.save_options())
        if not player_option in player_installed:
            err_message = ("Video Player Not Installed", f"Warning: Video player {player_option} was not found. Please install it " \
                          f"or choose other video player.")
            self.error_messages.put(err_message)

        self.mpv_options_entry.delete(0, tk.END)
        self.mpv_options_entry.insert(0, mpv_options)
        self.timeshiftactive.set(timeshiftactive_option)
        self.online_translation.set(online_translation_option)


    def play_channel(self, event=None):

        if self.subtitles == "subtitles":
            region = "cell"
        else:
            region = self.tree.identify_region(event.x, event.y)

        if region == "cell":
            item = self.tree.selection()[0]
            url = self.tree.item(item, "values")[2]

            mpv_options = self.mpv_options_entry.get()

            language_text = self.language.get()
            language_cleaned = language_text.split('(')[0].strip()

            if self.translate.get():
                translate_value = " --translate"
            else:
                translate_value = ""

            if self.subtitles == "subtitles":
                region = "cell"
            else:
                print("Playing channel:", url)

            videoplayer = self.player.get()
            quality = self.quality.get()

            if self.subtitles == "" and (not url.startswith("pulse") and not url.startswith("avfoundation")):

                if self.timeshiftactive.get():
                    if subprocess.call(["vlc", "--version"], stdout=subprocess.DEVNULL,
                                                         stderr=subprocess.DEVNULL) == 0:
                        print("Timeshift active.")
                    else:
                        err_message= f"Warning: Video player VLC was not found. Please install it."
                        print(err_message)
                        messagebox.showerror("Timeshift Player Not Installed", err_message)

                # Try launching smplayer, mpv, or mplayer
                elif self.playeronly.get() or quality == "raw":
                    try:
                        if videoplayer == "smplayer" and videoplayer in player_installed:
                            subprocess.Popen(["smplayer", url, mpv_options])
                            print("Launching smplayer...")
                        elif videoplayer == "mpv" and videoplayer in player_installed:
                            temp_file = tempfile.NamedTemporaryFile(delete=False)
                            with open(temp_file.name, "w") as log_file:
                                process = subprocess.Popen(["mpv", url, mpv_options], stdout=log_file, stderr=log_file)
                                print("Launching mpv...")
                                threading.Thread(target=wait_and_check_process, args=(process, log_file, url, mpv_options)).start()
                        elif videoplayer == "none":
                            if self.playeronly.get():
                                mpv_options = ""
                                err_message = "None video player selected."
                                print(err_message)
                                messagebox.showerror("Error", err_message)
                        else:
                            mpv_options = ""
                            err_message = f"No {videoplayer} video player found."
                            print(err_message)
                            messagebox.showerror("Error", err_message)
                    except Exception as e:
                        error_message = f"Error occurred while launching {videoplayer}: {str(e)}"
                        print(error_message)
                        messagebox.showerror("Error", error_message)

            if quality == "raw":
                videoplayer = "none"

            # Try launching gnome-terminal, konsole, lxterm, mlterm, xfce4-terminal, xterm
            terminal = self.terminal.get()
            bash_options = "--step " + self.step_s.get() + " --model " + self.model.get() + " --language " + language_cleaned + \
                           translate_value + " --" + quality

            if self.playeronly.get():
                bash_options = bash_options + " --playeronly"
            if self.timeshiftactive.get():
                bash_options = bash_options + " --timeshift --sync " + self.sync.get() + " --segments " + self.segments.get() + " --segment_time " + self.segment_time.get()
            if self.spec == "streamlink":
                bash_options = bash_options + " --streamlink"
            if self.spec == "yt-dlp":
                bash_options = bash_options + " --yt-dlp"
            if self.subtitles == "subtitles":
                bash_options = bash_options + " --subtitles"

            if self.online_translation.get():
                if subprocess.call(["trans", "-V"], stdout=subprocess.DEVNULL,
                                                     stderr=subprocess.DEVNULL) == 0:
                    trans_language_text = self.trans_language.get()
                    trans_language_cleaned = trans_language_text.split('(')[0].strip()
                    if self.speak.get():
                        speak_value = " speak"
                    else:
                        speak_value = ""

                    bash_options = bash_options + " --trans " + trans_language_cleaned + " " + self.output_text.get() + speak_value
                    print("Online translation active.")
                else:
                    err_message = ("translate-shell Not Installed", f"Warning: Online translation program 'trans' was not found. Please install it.")
                    self.error_messages.put(err_message)

            if not self.playeronly.get() or self.timeshiftactive.get() or self.subtitles == "subtitles":
                url = '"' + url + '"'

                executable = self.executable.get()
                if shutil.which(executable) is None:
                    err_message = ("Whisper executable Not Installed", f"Warning: Whisper executable {executable} was not found. Please install it" \
                                        f" or choose other.")
                    self.error_messages.put(err_message)
                executable_option = f"--executable {executable}"

                if self.timeshiftactive.get() or self.subtitles == "subtitles":
                    mpv_options = f"--player vlc {mpv_options}"
                elif videoplayer == "smplayer" and videoplayer in player_installed:
                    mpv_options = f"--player smplayer {mpv_options}"
                elif videoplayer == "mpv" and videoplayer in player_installed:
                    mpv_options = f"--player mpv {mpv_options}"
                elif videoplayer == "none":
                    mpv_options = f"--player none"
                else:
                    mpv_options = ""
                    err_message = f"No {videoplayer} video player found."
                    print(err_message)
                    messagebox.showerror("Error", err_message)

                if os.path.exists(self.bash_script):
                    print("Script Options:", f"{self.bash_script} {url} {bash_options} {executable_option} {mpv_options}")
                    try:
                        if terminal == "gnome-terminal" and subprocess.run(
                                ["gnome-terminal", "--version"]).returncode == 0:
                            subprocess.Popen(["gnome-terminal", "--tab", "--", "/bin/bash", "-c",
                                              f"{self.bash_script} {url} {bash_options} {executable_option} {mpv_options}; exec /bin/bash -i"])
                        elif terminal == "konsole" and subprocess.run(["konsole", "--version"]).returncode == 0:
                            subprocess.Popen(["konsole", "--noclose", "-e", f"{self.bash_script} {url} {bash_options} "
                                                                            f"{executable_option} {mpv_options}"])
                        elif terminal == "lxterm" and subprocess.run(["lxterm", "-version"]).returncode == 0:
                            subprocess.Popen(["lxterm", "-hold", "-e", f"{self.bash_script} {url} {bash_options} "
                                                                       f"{executable_option} {mpv_options}"])
                        elif terminal == "mate-terminal" and subprocess.run(
                                ["mate-terminal", "--version"]).returncode == 0:
                            subprocess.Popen(["mate-terminal", "-e", f"{self.bash_script} {url} {bash_options} "
                                                                     f"{executable_option} {mpv_options}"])
                        elif terminal == "mlterm":
                            result = subprocess.run(["mlterm", "--version"], capture_output=True, text=True)
                            mlterm_output = result.stdout
                            if "mlterm" in mlterm_output:
                                subprocess.Popen(["bash", "-c", f"mlterm -e {self.bash_script} {url} {bash_options} "
                                                                f"{executable_option} {mpv_options} & sleep 2 ; disown"])
                        elif terminal == "xfce4-terminal" and subprocess.run(
                                ["xfce4-terminal", "--version"]).returncode == 0:
                            subprocess.Popen(["xfce4-terminal", "--hold", "-e", f"{self.bash_script} {url} "
                                                                                f"{bash_options} {executable_option} {mpv_options}"])
                        elif terminal == "xterm" and subprocess.run(["xterm", "-version"]).returncode == 0:
                            subprocess.Popen(["xterm", "-e", f"{self.bash_script} {url} {bash_options} "
                                                                      f"{executable_option} {mpv_options}"])
                        else:
                            err_message= "No compatible terminal found."
                            print(err_message)
                            messagebox.showerror("Error", err_message)
                    except OSError as e:
                        print("Error executing command:", e)
                        messagebox.showerror("Error", "Error executing command.")
                else:
                    err_message="Script does not exist."
                    print(err_message)
                    messagebox.showerror("Error", err_message)


    # Function to Save texts
    def get_overwrite_action(self, filename):
        action = messagebox.askquestion("Overwrite File",
                                        f"The file {filename} already exists. Do you want to overwrite it?",
                                        icon='warning',
                                        type='yesnocancel',
                                        default='yes')
        if action == 'yes':
            return 'overwrite'
        elif action == 'cancel':
            return 'skip'
        elif action == 'no':
            new_filename = filedialog.asksaveasfilename(initialdir=self.destination_dir,
                                                        initialfile=filename,
                                                        title="Rename File")
            if new_filename:
                return new_filename  # Return the new filename if chosen
            else:
                return 'skip'  # User cancelled rename selection

    def select_files(self):
        custom_file_dialog = CustomFileDialog(self.main_window)
        self.wait_window(custom_file_dialog)
        if custom_file_dialog.selected_files:
            self.source_files = custom_file_dialog.selected_files
            self.select_destination()
        else:
            messagebox.showwarning("No Files Selected", "No files were selected.")

    def select_destination(self):
        self.destination_dir = filedialog.askdirectory()
        if self.destination_dir:
            self.copy_files()
        else:
            messagebox.showwarning("No Destination Selected", "No destination directory was selected.")

    def copy_files(self):
        for file_path in self.source_files:
            filename = os.path.basename(file_path)
            destination_file_path = os.path.join(self.destination_dir, filename)
            if os.path.exists(destination_file_path):
                if os.path.samefile(file_path, destination_file_path):
                    messagebox.showwarning("Same File", f"The file {filename} is the same as the source file. Skipping.")
                    continue

                action = self.get_overwrite_action(filename)
                if action == 'overwrite':
                    shutil.copyfile(file_path, destination_file_path)
                elif action == 'skip':
                    continue
                else:  # action is the new filename
                    shutil.copyfile(file_path, action)
            else:
                shutil.copyfile(file_path, destination_file_path)
        messagebox.showinfo("Copying Process Completed", "Copying Process completed successfully.")


    # Function to open the video saver dialog
    def open_video_saver(self):
        VideoSaverDialog(self.main_window)


    # Function to delete temporary videos
    def delete_videos(self):
        try:
            used_files = set()
            file_info = {}

            # Get the list of files matching the pattern
            files = set(glob.glob("/tmp/*whisper-live*.*"))

            # Check the initial timestamp of each file
            for file in files:
                try:
                    initial_timestamp = os.path.getmtime(file)
                    file_info[file] = initial_timestamp
                except FileNotFoundError:
                    pass

            # Wait for 5 seconds
            time.sleep(5)

            # Get the list of files again after the wait period
            files_after_wait = set(glob.glob("/tmp/*whisper-live*.*"))

            # Add the new files to the files set
            files.update(files_after_wait)

            # Check the final timestamp of each file
            for file in files:
                try:
                    final_timestamp = os.path.getmtime(file)
                    if final_timestamp != file_info.get(file, None) or (time.time() - final_timestamp) <= 60:
                        used_files.add(file)
                except FileNotFoundError:
                    pass

            # Extract numbers from filenames of files in use
            used_numbers = set()
            for file in used_files:
                match = re.search(r'whisper-live_(\d+)', file)
                if match:
                    number = match.group(1)
                    used_numbers.add(number)

            # Delete files not in use
            deleted_files = 0
            for file in files:
                match = re.search(r'whisper-live?_(\d+)', file)
                if match and match.group(1) not in used_numbers:
                    os.remove(file)
                    deleted_files += 1

            if deleted_files == 0:
                messagebox.showinfo("Info", "There are no files to delete, or wait at least 1 minute.")
            else:
                messagebox.showinfo("Success", "Successfully deleted all /tmp videos and related files, except those in use.")
        except Exception as e:
            error_message = f"Unable to delete /tmp videos: {str(e)}"
            print(error_message)
            messagebox.showerror("Error", error_message)


    # Popup menu for cut, copy, paste, delete that works for any entry
    def show_popup_menu(self, event):
        # Create the popup menu with tearoff disabled
        self.popup_menu = tk.Menu(self, tearoff=0)

        # Use the widget that triggered the event
        widget = event.widget

        # Add menu commands using the triggering widget
        self.popup_menu.add_command(label="Cut", command=lambda: self.cut(widget))
        self.popup_menu.add_command(label="Copy", command=lambda: self.copy(widget))
        self.popup_menu.add_command(label="Paste", command=lambda: self.paste(widget))
        self.popup_menu.add_command(label="Delete", command=lambda: self.delete(widget))

        # Display the popup menu at the right-click position
        self.popup_menu.tk_popup(event.x_root, event.y_root)

    def cut(self, entry, event=None):
        if entry.selection_present():
            selected_text = entry.selection_get()
            self.copy_to_clipboard(selected_text)
            entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.schedule_save_options()

    def copy(self, entry, event=None):
        if entry.selection_present():
            selected_text = entry.selection_get()
            self.copy_to_clipboard(selected_text)

    def paste(self, entry, event=None):
        if entry.selection_present():
            entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
        clipboard_text = self.master.clipboard_get()
        if clipboard_text is not None:
            entry.insert(tk.INSERT, clipboard_text)
        else:
            pass
        self.schedule_save_options()

    def delete(self, entry, event=None):
        if entry.selection_present():
            entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.schedule_save_options()

    def copy_to_clipboard(self, text):
        if text is not None:
            self.master.clipboard_clear()
            self.master.clipboard_append(text)
        else:
            pass


    # Function to add a channel
    def add_channel(self):
        name_dialog = EnhancedStringDialog(self.main_window, "Edit Channel", "Channel Name:")
        name = name_dialog.result
        url_dialog = EnhancedStringDialog(self.main_window, "Edit Channel", "Channel URL:")
        url = url_dialog.result

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
            self.update_list_numbers()

            messagebox.showinfo("Success", "Channel added successfully. Don't forget to save the playlist.")
        else:
            messagebox.showerror("Error", "Both name and URL are required.")

    # Function to add a file channel
    def add_file_channel(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[
                ("Media files", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.mpeg *.mpg *.3gp *.webm *.mkv *.ogg *.ogm *.mp3 *.wav *.flac *.aac *.oga *.opus"),
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.mpeg *.mpg *.3gp *.webm *.mkv *.ogg *.ogm"),
                ("Audio files", "*.mp3 *.wav *.flac *.aac *.ogg *.oga *.opus"),
                ("All files", "*.*")
            ]
        )

        if file_paths:
            for file_path in file_paths:
                # Extract the file name without extension
                name = os.path.splitext(os.path.basename(file_path))[0]

                selection = self.tree.selection()
                if selection:
                    index = self.tree.index(selection[0])
                    index += 1
                else:
                    index = len(self.tree.get_children()) + 1

                # Add file to the list
                self.tree.insert("", index, values=(index, name, file_path))
                self.update_list_numbers()

            messagebox.showinfo("Success", "File(s) added successfully. Don't forget to save the playlist.")
        else:
            messagebox.showerror("Error", "No file selected.")


    def get_input_sources(self):
        try:
            if platform.system() == "Linux":
                output = subprocess.check_output(["pactl", "list", "short", "sources"]).decode("utf-8")
                sources = []
                for line in output.splitlines():
                    parts = line.split()
                    index = parts[0]
                    name = re.match(r'\d+\s+(\S+)', line).group(1)
                    sources.append(f"{index} {name}")
                return sources

            elif platform.system() == "Darwin":
                ffmpeg_process = subprocess.run(["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                if ffmpeg_process.returncode != 0:
                    print(f"Error: ffmpeg command returned non-zero exit status {ffmpeg_process.returncode}")

                output = ffmpeg_process.stdout
                if output == "":
                    output = ffmpeg_process.stderr
                    if output == "":
                        print("Error: ffmpeg command did not produce any output")
                        return []

                sources = []
                in_audio_devices = False
                for line in output.splitlines():
                    line = line.strip()
                    if "AVFoundation audio devices:" in line:
                        in_audio_devices = True
                    elif in_audio_devices:
                        match = re.search(r'\[(\d+)\]\s*(.*?)$', line)
                        if match:
                            index, name = match.groups()
                            sources.append(f"{index} {name.strip()}")
                        else:
                            in_audio_devices = False
                return sources

            else:
                return []
        except subprocess.CalledProcessError as e:
            print("Error:", e.output)
            return []


    def add_audio_source(self):
        # Create a new window or widget to select the sound card
        audio_select_window = tk.Toplevel(self.root)
        audio_select_window.title("Select Sound Card")

        # Get the screen dimensions
        screen_width = audio_select_window.winfo_screenwidth()
        screen_height = audio_select_window.winfo_screenheight()

        # Calculate the coordinates for the window to be in the middle
        x = (screen_width / 2) - (400 / 2)  # Adjust 400 to your desired window width
        y = (screen_height / 2) - (300 / 2)  # Adjust 300 to your desired window height

        # Set the window size and position
        audio_select_window.geometry(f"400x300+{int(x)}+{int(y)}")  # Adjust width and height as needed

        # Get the list of available input sources
        input_sources = self.get_input_sources()

        # Create a frame to hold the text message and radio buttons
        frame = tk.Frame(audio_select_window)
        frame.pack(pady=10)

        # Determine the appropriate message based on the platform
        if platform.system() == "Linux":
            message = "Please select a sound device. Devices suffixed with 'monitor' are loopback devices that allow you to record all sounds 'what you hear' on your desktop. These devices, along with applications, can be configured individually using PulseAudio Volume Control."
        elif platform.system() == "Darwin":
            message = "Please select a sound device. Loopback devices allow you to record all sounds 'what you hear' on your desktop. First, create a virtual device using an Audio Loopback Driver like Blackhole, VB-Cable or Loopback."
        else:
            message = "Select one sound device."

        # Create a label with the message
        label = tk.Label(frame, text=message, wraplength=380, justify="left")
        label.pack()

        # Create a frame to hold the radio buttons
        radio_frame = tk.Frame(frame)
        radio_frame.pack(pady=10)

        # Create a StringVar to store the user's selection
        self.selected_sound_card = tk.StringVar()

        # Create radio buttons for each input source
        for source in input_sources:
            radio_button = tk.Radiobutton(radio_frame, text=source, variable=self.selected_sound_card, value=source)
            radio_button.pack(anchor=tk.W)

        # Create button frame
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        # Create a button to confirm the selection
        confirm_button = tk.Button(button_frame, text="Confirm", command=lambda: self.add_audio_source_confirm(audio_select_window, input_sources, self.selected_sound_card.get()))
        confirm_button.pack(side=tk.LEFT, padx=5)

        # Create a button to cancel the operation
        cancel_button = tk.Button(button_frame, text="Cancel", command=audio_select_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)


    def add_audio_source_confirm(self, audio_select_window, input_sources, selected_text):
        ffmpeg_process = None
        ffplay_process = None

        # Close the sound card selection window
        audio_select_window.destroy()

        if selected_text:
            selected_index_str, _ = selected_text.split(" ", 1)
            selected_index = int(selected_index_str)

            # Get the selected input source
            selected_source = None
            for source in input_sources:
                if source.startswith(selected_index_str):
                    selected_source = source
                    break

            if selected_source is not None:

                # Perform actions with the selected input source based on platform
                if platform.system() == "Linux":
                    # Linux
                    audio_path = f"pulse:{selected_index}"
                    name = f"Linux Input pulse - {selected_source}"
                elif platform.system() == "Darwin":
                    # macOS
                    audio_path = f"avfoundation:{selected_index}"
                    name = f"macOS Input avfoundation - {selected_source}"
                else:
                    print("Unsupported platform")
                    return

                test = True

                # Prompt the user to test the selected sound source
                test_sound_source = tk.messagebox.askyesno("Test Sound Source", "Do you want to test the selected sound source?")

                if test_sound_source:
                    action = tk.messagebox.askquestion("Test Sound Source",
                                                    f"Ensure you have anything connected or anything playing in the selected sound device: {name}. An audio will be recorded to test it. Proceed?",
                                                    icon='warning',
                                                    type='yesnocancel',
                                                    default='yes')
                    if action == 'yes':
                        try:
                            if audio_path.startswith("pulse:"):
                                ffmpeg_process = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-y", "-f", "pulse", "-i", f"{selected_index}", "/tmp/whisper-live_0_test.wav"])
                            elif audio_path.startswith("avfoundation:"):
                                ffmpeg_process = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-y", "-f", "avfoundation", "-i", f":{selected_index}", "/tmp/whisper-live_0_test.wav"])

                            max_wait_time = 5
                            file_path = '/tmp/whisper-live_0_test.wav'
                            start_time = time.time()

                            # Loop until the file exists or the maximum wait time is reached
                            while not os.path.exists(file_path):
                                # Check if the maximum wait time is exceeded
                                if time.time() - start_time >= max_wait_time:
                                    print("Maximum wait time exceeded.")
                                    break

                                # Wait for a short interval before checking again
                                time.sleep(0.1)

                            # Wait for a short interval again
                            time.sleep(2)
                            # Check if the file exists after the loop
                            if os.path.exists(file_path):

                                ffplay_process = subprocess.Popen(["ffplay", "-loglevel", "quiet", "/tmp/whisper-live_0_test.wav"])

                                action = tk.messagebox.askquestion("Test Sound Source",
                                                                f"Testing selected sound device: {name}. Do you hear it?",
                                                                icon='warning',
                                                                type='yesnocancel',
                                                                default='yes')
                                if action == 'yes':
                                    test = True
                                else:
                                    test = False

                            else:
                                print(f"File {file_path} does not exist.")
                                test = False

                        except Exception as e:
                            # Handle other exceptions
                            tk.messagebox.showerror("Error", f"Error testing sound source: {str(e)}")
                            test = False

                    else:
                        tk.messagebox.showerror("Error", "Could not test the selected audio device.")
                        test = False

                if ffmpeg_process:
                    ffmpeg_process.terminate()
                if ffplay_process:
                    ffplay_process.terminate()

                if test:
                    selection = self.tree.selection()
                    if selection:
                        index = self.tree.index(selection[0])
                        index += 1
                    else:
                        index = len(self.tree.get_children()) + 1

                    # Add audio source to the list
                    self.tree.insert("", index, values=(index, name, audio_path))
                    self.update_list_numbers()
                    messagebox.showinfo("Success", "Audio source added successfully. Don't forget to save the playlist.")
                    print(f"Selected sound card: {name}")

            else:
                messagebox.showerror("Error", "No audio source selected.")

        else:
            messagebox.showerror("Error", "No audio source selected.")


    # Function to generate subtitles
    def generate_subtitles(self):
        selection = self.tree.selection()
        if selection:
            item = self.tree.selection()[0]
            url = self.tree.item(item, "values")[2]
            if re.match(r'^/|^\./', url):
                self.subtitles="subtitles"
                self.play_channel()
                self.subtitles=""
                err_message = f"Please wait while generating subtitles for {url}"
                print(err_message)
                messagebox.showinfo("Generating Subtitles", err_message)
            else:
                messagebox.showerror("Error", "Select a valid local file to generate subtitles.")
        else:
            messagebox.showerror("Error", "Select a file to generate subtitles.")


    # Function to split a video/audio file in half using a non-blocking thread
    def split_video(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Error", "Select a local file to split.")
            return

        item = self.tree.selection()[0]
        url = self.tree.item(item, "values")[2]

        if not re.match(r'^/|^\./', url) or not os.path.exists(url):
            messagebox.showerror("Error", "Select a valid local file to split.")
            return

        # --- Define a worker function to be run in a separate thread ---
        def split_worker(url, item_id, result_queue, should_overwrite):
            try:
                # Get duration
                ffprobe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", url]
                result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
                total_duration = float(result.stdout.strip())
                midpoint_seconds = total_duration / 2

                # Define filenames
                directory, filename = os.path.split(url)
                name, ext = os.path.splitext(filename)
                output_part1 = os.path.join(directory, f"{name}_part1{ext}")
                output_part2 = os.path.join(directory, f"{name}_part2{ext}")

                # Build ffmpeg commands
                ffmpeg_cmd_part1 = ["ffmpeg", "-i", url, "-to", str(midpoint_seconds), "-c", "copy", output_part1]
                ffmpeg_cmd_part2 = ["ffmpeg", "-ss", str(midpoint_seconds), "-i", url, "-c", "copy", output_part2]

                if should_overwrite:
                    ffmpeg_cmd_part1.insert(1, "-y")
                    ffmpeg_cmd_part2.insert(1, "-y")

                # CORRECTION: Use capture_output=True without specifying stderr/stdout manually.
                subprocess.run(ffmpeg_cmd_part1, check=True, capture_output=True)
                subprocess.run(ffmpeg_cmd_part2, check=True, capture_output=True)

                # On success, put a dictionary with results in the queue
                result_queue.put({
                    'original_item': item_id,
                    'name_part1': f"{name}_part1",
                    'name_part2': f"{name}_part2",
                    'output_part1': output_part1,
                    'output_part2': output_part2,
                })
            except Exception as e:
                # On failure, put the exception object in the queue
                result_queue.put(e)

        # --- Main part of the function (runs in the GUI thread) ---
        try:
            directory, filename = os.path.split(url)
            name, ext = os.path.splitext(filename)
            output_part1 = os.path.join(directory, f"{name}_part1{ext}")
            output_part2 = os.path.join(directory, f"{name}_part2{ext}")
            should_overwrite = False

            if os.path.exists(output_part1) or os.path.exists(output_part2):
                response = messagebox.askquestion(
                    "Files Exist",
                    "One or more output files already exist. Do you want to overwrite them?\n\n"
                    f"- {os.path.basename(output_part1)}\n"
                    f"- {os.path.basename(output_part2)}",
                    icon='warning'
                )
                if response == 'no':
                    messagebox.showinfo("Operation Cancelled", "The split operation was cancelled by the user.")
                    return
                should_overwrite = True

            # --- Create and display the non-modal notification window ---
            notification = tk.Toplevel(self)
            notification.title("Processing")
            notification.transient(self.winfo_toplevel())
            # Use grab_set() to temporarily disable the main window, preventing user from starting another long task
            notification.grab_set()
            notification.resizable(False, False)

            msg = f"Splitting '{filename}'...\nThis may take a moment."
            tk.Label(notification, text=msg, padx=20, pady=20).pack()
            notification.update_idletasks()

            x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() / 2) - (notification.winfo_width() / 2)
            y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() / 2) - (notification.winfo_height() / 2)
            notification.geometry(f"+{int(x)}+{int(y)}")

            # --- Start the worker thread ---
            result_queue = queue.Queue()
            thread = threading.Thread(target=split_worker, args=(url, item, result_queue, should_overwrite))
            thread.daemon = True
            thread.start()

            # --- Start polling for the result ---
            self.after(100, self._check_split_thread, result_queue, notification)

        except FileNotFoundError:
             messagebox.showerror("Error", "FFmpeg/ffprobe not found. Please ensure it is installed and in your system's PATH.")
        except Exception as e:
            # This will catch errors during filename preparation, before the thread starts
            messagebox.showerror("An Unexpected Error Occurred", str(e))


    # Helper method to check the result from the split video thread
    def _check_split_thread(self, result_queue, notification_window):
        """Checks the queue for a result from the worker thread."""
        try:
            result = result_queue.get(block=False)

            # We have a result, close the notification and process it
            notification_window.destroy()

            if isinstance(result, Exception):
                # An error occurred in the thread
                if isinstance(result, subprocess.CalledProcessError):
                    error_output = result.stderr.decode('utf-8', 'ignore') if result.stderr else "No error output from FFmpeg."
                    messagebox.showerror("FFmpeg Error", f"An error occurred while processing the file.\n\nFFmpeg error:\n{error_output}")
                else:
                    messagebox.showerror("An Unexpected Error Occurred", str(result))
            else:
                # Success! The result dictionary contains the needed info
                original_item_index = self.tree.index(result['original_item'])
                name_part1 = result['name_part1']
                name_part2 = result['name_part2']
                output_part1 = result['output_part1']
                output_part2 = result['output_part2']

                self.tree.insert("", original_item_index + 1, values=(0, name_part2, output_part2))
                self.tree.insert("", original_item_index + 1, values=(0, name_part1, output_part1))
                self.update_list_numbers()

                messagebox.showinfo("Success", "The file was split successfully. Don't forget to save the playlist.")

        except queue.Empty:
            # No result yet, check again after 100ms
            self.after(100, self._check_split_thread, result_queue, notification_window)


    # Function to delete a channel
    def delete_channel(self):
        selection = self.tree.selection()
        if selection:
            current_index = self.tree.index(selection[0])
            self.tree.delete(selection[0])
            self.update_list_numbers()

            # Find the next item after the deleted one
            next_index = current_index
            all_items = self.tree.get_children()
            total_items = len(all_items)

            if next_index < total_items:
                next_item = all_items[next_index]
                self.tree.selection_set(next_item)
            else:
                # No more items left, so clear any existing selection
                self.tree.selection_remove()

            err_message=("Success", "Channel(s) deleted successfully. Don't forget to save the playlist.")
            self.error_messages.put(err_message)
        else:
            messagebox.showerror("Error", "Select a channel to delete.")

    # Function to edit a channel
    def edit_channel(self):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            list_number, name, url = self.tree.item(item, "values")

            name_dialog = EnhancedStringDialog(self.main_window, "Edit Channel", "Channel Name:", initial_value=self.tree.item(item, "values")[1])
            name = name_dialog.result
            url_dialog = EnhancedStringDialog(self.main_window, "Edit Channel", "Channel URL:", initial_value=self.tree.item(item, "values")[2])
            url = url_dialog.result

            if name and url:
                self.tree.item(item, values=(list_number, name, url))

                messagebox.showinfo("Success", "Channel edited successfully. Don't forget to save the playlist.")
            else:
                # Show an error message if either name or URL is not provided
                messagebox.showerror("Error", "Both name and URL are required.")
        else:
            messagebox.showerror("Error", "Select a channel to edit.")

    # Function to move up channel
    def move_up_channel(self):
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            if index > 0:
                self.tree.move(selection[0], "", index - 1)
                self.update_list_numbers()

                err_message=("Success", "Channel(s) moved successfully. Don't forget to save the playlist.")
                self.error_messages.put(err_message)
            else:
                messagebox.showinfo("Info", "The selected channel is already at the top.")
        else:
            messagebox.showerror("Error", "Select a channel to move.")

    # Function to move down channel
    def move_down_channel(self):
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            total_items = len(self.tree.get_children())

            if index < total_items - 1:  # Check if not the last item
                self.tree.move(selection[0], "", index + 1)
                self.update_list_numbers()

                err_message=("Success", "Channel(s) moved successfully. Don't forget to save the playlist.")
                self.error_messages.put(err_message)
            else:
                messagebox.showinfo("Info", "The selected channel is already at the bottom.")
        else:
            messagebox.showerror("Error", "Select a channel to move.")


    # Function to iterate over all items and update their list_number
    def update_list_numbers(self):
        for i, item in enumerate(self.tree.get_children()):
            self.tree.item(item, values=(i + 1,) + tuple(self.tree.item(item)['values'][1:]))


    # New method to record the item being dragged on mouse press
    def on_treeview_button_press(self, event):
        self._dragging_item = self.tree.identify_row(event.y)
        if self._dragging_item:
            item_text = self.tree.item(self._dragging_item, "values")[1]
            self.drag_label = tk.Label(self.tree, text=item_text, bg="white", relief="solid", bd=1)
            self.drag_label.place(x=event.x, y=event.y)

    # New method to update potential drop target on mouse movement
    def on_treeview_motion(self, event):
        if not self._dragging_item:
            return
        if hasattr(self, "drag_label"):
            self.drag_label.place(x=event.x, y=event.y)

    def remove_drag_label(self):
        if hasattr(self, "drag_label"):
            self.drag_label.destroy()
            del self.drag_label

    # New method to perform the item move on mouse release
    def on_treeview_button_release(self, event):
        if self._dragging_item:
            self.remove_drag_label()  # Ensure drag label is always removed
            # Identify the drop target at the y-coordinate of the release event
            drop_item = self.tree.identify_row(event.y)
            # Only move the item if a valid drop_item is found; otherwise do nothing
            if drop_item:
                drop_index = self.tree.index(drop_item)
                if drop_item != self._dragging_item:
                    err_message = ("Success", "Channel(s) moved successfully. Don't forget to save the playlist.")
                    self.error_messages.put(err_message)
                    self.tree.move(self._dragging_item, '', drop_index)
                    self.update_list_numbers()
            self._dragging_item = None

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
            self.update_list_numbers()

    # Function to save a playlist
    def save_playlist(self):
        default_filename = f'playlist_{self.spec}.m3u'
        filename = filedialog.asksaveasfilename(filetypes=[("Playlist Files", "*.m3u")], initialfile=default_filename)
        if filename:
            with open(filename, "w") as file:
                for item in self.tree.get_children():
                    list_number, name, url = self.tree.item(item, "values")
                    file.write(f"#EXTINF:-1,{name}\n{url}\n")

    # New helper method to update the search counter label
    def _update_search_counter(self):
        """Updates the search count label to show 'current/total' matches."""
        total_matches = len(self.match_items)
        current_selection_num = 0

        # If there are matches and an item is currently selected, show its 1-based index
        if total_matches > 0 and self.current_match_index >= 0:
            current_selection_num = self.current_match_index + 1

        self.search_count_label.config(text=f"{current_selection_num}/{total_matches}")

    # Function to filter playlist based on search text
    def filter_playlist(self, event=None):
        search_text = self.search_entry.get() # Get text without converting to lower yet

        # Reset tags and current match index
        self.match_items = []
        self.current_match_index = -1

        if not search_text:
            # If search is empty, restore all items and reset the counter
            for item in self.tree.get_children():
                self.tree.item(item, tags=())
            self._update_search_counter() # Update counter to 0/0
            return

        # --- Wildcard search logic ---
        # Convert user input with wildcards to a valid regex pattern.
        # 1. Escape special regex characters in the user's input.
        # 2. Replace the escaped wildcard '\*' with the regex '.*' (matches any character, any number of times).
        pattern_str = re.escape(search_text).replace(r'\*', '.*')
        try:
            # Compile the pattern for efficient searching, ignoring case.
            search_pattern = re.compile(pattern_str, re.IGNORECASE)
        except re.error:
            # Handle cases where the user might enter an invalid pattern
            self.search_count_label.config(text="Invalid pattern")
            return

        # Filter items based on the regex pattern
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            # We don't need to convert to lower() because re.IGNORECASE handles it
            name = values[1]
            url = values[2]

            if search_pattern.search(name) or search_pattern.search(url):
                # Highlight matching items
                self.tree.item(item, tags=("match",))
                self.match_items.append(item)
            else:
                # Make non-matching items gray
                self.tree.item(item, tags=("nomatch",))

        # Configure tag appearance
        self.tree.tag_configure("match", background="#e6f3ff")
        self.tree.tag_configure("nomatch", foreground="gray")
        self.tree.tag_configure("current_match", background="#c2e0ff")  # Current match gets darker highlight

        # Select the first match if available
        if self.match_items:
            self.current_match_index = 0
            first_match = self.match_items[0]

            self.tree.selection_set(first_match)
            self.tree.see(first_match)
            self.adjust_view(first_match)
            self.tree.item(first_match, tags=("current_match",))
            self.load_options()
        else:
             self.tree.selection_remove(*self.tree.selection())

        # Update the counter label with the results
        self._update_search_counter()

    # Helper function to adjust the view so that the item is fully visible
    def adjust_view(self, item):
        # Force widget update to ensure current layout info
        self.tree.update_idletasks()
        # Get the bounding box of the item (returns x, y, width, height)
        bbox = self.tree.bbox(item)
        if bbox:
            x, y, width, height = bbox
            visible_height = self.tree.winfo_height()
            # If the top of the item is above the visible area, scroll up
            if y < 0:
                self.tree.yview_scroll(-1, "units")
            # If the bottom of the item is below the visible area, scroll down
            elif y + height > visible_height:
                self.tree.yview_scroll(1, "units")

    # Function to move to the next matching item
    def next_match(self):
        # Check if there are matching items
        if not hasattr(self, 'match_items') or not self.match_items:
            return

        # Clear current match highlight, if any
        if self.current_match_index >= 0:
            current_item = self.match_items[self.current_match_index]
            self.tree.item(current_item, tags=("match",))

        # Move to the next match, wrapping around to the beginning if necessary
        self.current_match_index = (self.current_match_index + 1) % len(self.match_items)
        next_item = self.match_items[self.current_match_index]

        # Highlight and select the next match
        self.tree.item(next_item, tags=("current_match",))
        self.tree.selection_remove(*self.tree.selection())
        self.tree.selection_set(next_item)
        self.tree.focus(next_item)      # Ensure the widget's focus is updated
        self.tree.see(next_item)        # Ensure the item is visible
        self.adjust_view(next_item)     # Adjust view if needed

        # Load options for the newly selected item
        self.load_options()
        self._update_search_counter()

    # Function to move to the previous matching item
    def prev_match(self):
        # Check if there are matching items
        if not hasattr(self, 'match_items') or not self.match_items:
            return

        # Clear current match highlight, if any
        if self.current_match_index >= 0:
            current_item = self.match_items[self.current_match_index]
            self.tree.item(current_item, tags=("match",))

        # Move to the previous match, wrapping around to the end if necessary
        self.current_match_index = (self.current_match_index - 1) % len(self.match_items)
        prev_item = self.match_items[self.current_match_index]

        # Highlight and select the previous match
        self.tree.item(prev_item, tags=("current_match",))
        self.tree.selection_remove(*self.tree.selection())
        self.tree.selection_set(prev_item)
        self.tree.focus(prev_item)      # Ensure the widget's focus is updated
        self.tree.see(prev_item)        # Ensure the item is visible
        self.adjust_view(prev_item)     # Adjust view if needed

        # Load options for the newly selected item
        self.load_options()
        self._update_search_counter()

    # Function to clear search
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        # Reset all items to default appearance
        for item in self.tree.get_children():
            self.tree.item(item, tags=())

        # Reset match tracking
        self.match_items = []
        self.current_match_index = -1
        self._update_search_counter()

    # Functions to load and save config.json
    def load_options(self, event=None):
        self.load_config()
        override_option = self.current_options["override_option"]
        self.override_options.set(override_option)

        self.widgets_updates()

        selected_items = self.tree.selection()
        if not selected_items:
            # If nothing is selected, ensure the counter reflects this
            if hasattr(self, 'match_items') and self.match_items:
                 self.current_match_index = -1
                 self._update_search_counter()
            return

        # Use the first selected item
        selected_item = selected_items[0]

        # If a search is active, update the index and counter based on the selection
        if hasattr(self, 'match_items') and self.match_items:
            # First, clear the highlight from the previously selected match
            if self.current_match_index >= 0 and self.current_match_index < len(self.match_items):
                previous_match_item = self.match_items[self.current_match_index]
                if self.tree.exists(previous_match_item): # Check if item still exists
                    self.tree.item(previous_match_item, tags=("match",))

            # Now, check if the new selection is a valid match
            if selected_item in self.match_items:
                # It is a valid match, find its index
                self.current_match_index = self.match_items.index(selected_item)
                # Highlight the new current match
                self.tree.item(selected_item, tags=("current_match",))
                self.tree.see(selected_item)
                self.adjust_view(selected_item)
            else:
                # The selection is not a search result (e.g., a greyed-out item was clicked)
                self.current_match_index = -1

            # Finally, update the counter regardless of whether it was a match or not
            self._update_search_counter()

    def load_config(self):
        try:
            config_file = f'config_{self.spec}.json'
            self.current_options["executable_option"] = default_executable_option
            self.current_options["terminal_option"] = default_terminal_option
            self.current_options["bash_options"] = default_bash_options
            self.current_options["playeronly_option"] = default_playeronly_option
            self.current_options["player_option"] = default_player_option
            self.current_options["mpv_options"] = default_mpv_options
            self.current_options["override_option"] = default_override_option
            self.current_options["timeshiftactive_option"] = default_timeshiftactive_option
            self.current_options["timeshift_options"] = default_timeshift_options
            self.current_options["online_translation_option"] = default_online_translation_option
            self.current_options["trans_options"] = default_trans_options

            if os.path.exists(config_file):
                with open(config_file, "r") as file:
                    self.current_options = json.load(file)
        except:
            err_message=("Wrong option",f"Wrong option found, try again after deleting"
                                        f" config_{self.spec}.json file")
            self.error_messages.put(err_message)

    def schedule_save_options(self, event=None):
        if self.save_options_id:
            self.after_cancel(self.save_options_id)
        self.save_options_id = self.after(1000, self.save_options)

    def save_options(self, event=None):
        self.executable_frame.config(highlightthickness=1, highlightbackground="black")
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
        self.online_translation_frame.config(highlightthickness=1, highlightbackground="black")
        self.trans_language_frame.config(highlightthickness=1, highlightbackground="black")
        self.output_text_frame.config(highlightthickness=1, highlightbackground="black")
        self.speak_frame.config(highlightthickness=1, highlightbackground="black")

        executable_option = self.executable.get()
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
            messagebox.showerror("Invalid Integer", f"The value is not a valid integer.")

        timeshift_options = self.sync.get() + " " + self.segments.get() + " " + self.segment_time.get()

        trans_language_text = self.trans_language.get()
        trans_language_cleaned = trans_language_text.split('(')[0].strip()
        if self.speak.get():
            speak_value = " speak"
        else:
            speak_value = ""

        online_translation_option = self.online_translation.get()

        trans_options = trans_language_cleaned + " " + self.output_text.get() + speak_value

        if self.override_options.get():
            self.current_options["executable_option"] = executable_option
            self.current_options["terminal_option"] = terminal_option
            self.current_options["bash_options"] = bash_options
            self.current_options["playeronly_option"] = playeronly_option
            self.current_options["player_option"] = player_option
            self.current_options["mpv_options"] = mpv_options
            self.current_options["timeshiftactive_option"] = timeshiftactive_option
            self.current_options["timeshift_options"] = timeshift_options
            self.current_options["online_translation_option"] = online_translation_option
            self.current_options["trans_options"] = trans_options
            self.current_options["override_option"] = True
        else:
            selection = self.tree.focus()
            if selection:
                self.executable_frame.config(highlightthickness=1, highlightbackground="red")
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
                self.online_translation_frame.config(highlightthickness=1, highlightbackground="red")
                self.trans_language_frame.config(highlightthickness=1, highlightbackground="red")
                self.output_text_frame.config(highlightthickness=1, highlightbackground="red")
                self.speak_frame.config(highlightthickness=1, highlightbackground="red")

                url = self.tree.item(selection, "values")[2]
                self.current_options[url] = {}
                self.current_options[url]["executable_option"] = executable_option
                self.current_options[url]["terminal_option"] = terminal_option
                self.current_options[url]["bash_options"] = bash_options
                self.current_options[url]["playeronly_option"] = playeronly_option
                self.current_options[url]["player_option"] = player_option
                self.current_options[url]["mpv_options"] = mpv_options
                self.current_options[url]["timeshiftactive_option"] = timeshiftactive_option
                self.current_options[url]["timeshift_options"] = timeshift_options
                self.current_options[url]["online_translation_option"] = online_translation_option
                self.current_options[url]["trans_options"] = trans_options

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
        messagebox.showinfo("About",
                                         "playlist4whisper Version: 3.12\n\nCopyright (C) 2023 Antonio R.\n\n"
                                         "Playlist for livestream_video.sh, "
                                         "it plays online videos and transcribes them. "
                                         "A simple GUI using Python and Tkinter library. "
                                         "Based on whisper.cpp.\n\n"
                                         "License: GPL 3.0\n\n"
                                         "This program comes with ABSOLUTELY NO WARRANTY."
                                         "This is free software, and you are welcome to redistribute it "
                                         "under certain conditions; see source code for details.")


class MainApplication:
    """
    The main application for managing M3U playlists.

    This class represents the main application window for managing M3U playlists. It contains
    tabs for different types of playlists, each with its own playlist player. It also handles
    error messages during playback and provides functionality for closing the application.

    Attributes:
        tab_names: The names of the tabs.
        tab_colors: The colors of the tabs.
        error_messages: A queue for storing error messages.
        main_window: The main Tkinter window.
    """

    def __init__(self, tab_names, tab_colors):
        self.error_messages = queue.Queue()

        self.main_window = tk.Tk()
        self.main_window.title("playlist4whisper")
        self.main_window.geometry("1000x800")

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

        self.main_window.iconphoto(True, PhotoImage(data=icon))

        bash_script = "./livestream_video.sh"

        tab_control = ttk.Notebook(self.main_window)

        tabs = []
        canvases = []
        for name, color in zip(tab_names, tab_colors):
            tab = ttk.Frame(tab_control)
            tab_control.add(tab, text=name, compound="left")
            tabs.append(tab)

            text_color = self.get_text_color(color)  # Determine the appropriate text color based on the background color
            canvas = tk.Canvas(tab, width=25, height=80, bg=color, highlightthickness=0)
            canvas.pack(side=tk.LEFT, fill=tk.Y)
            canvas.create_text(15, 40, text=name, angle=90, fill=text_color, anchor='center')
            canvases.append(canvas)

        tab_control.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        playlist_players = []
        for tab, spec in zip(tabs, tab_names):
            spec_lower = spec.lower().replace(" ", "_")
            playlist_player = M3uPlaylistPlayer(tab, spec_lower, bash_script, self.error_messages, self.main_window)
            playlist_player.pack(fill=tk.BOTH, expand=True)
            playlist_players.append(playlist_player)
        self.playlist_players = playlist_players  # store playlist players

        self.main_window.protocol("WM_DELETE_WINDOW", self.on_close)
        check_error_thread = threading.Thread(target=self.check_error_messages)
        check_error_thread.daemon = True
        check_error_thread.start()

    def on_close(self):
        self.main_window.destroy()

    def remove_all_drag_labels(self):
        for player in self.playlist_players:
            player.remove_drag_label()

    def check_error_messages(self):
        while True:
            error_messages = set()
            while not self.error_messages.empty():
                error_message = self.error_messages.get(block=False)
                error_messages.add(error_message)
            # Call show_error_messages with the callback to remove labels
            show_error_messages(error_messages, self.remove_all_drag_labels)
            time.sleep(3)

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_rgb(self, color):
        """Get the RGB tuple for a color name or hex value."""
        if color.startswith('#'):
            return self.hex_to_rgb(color)
        else:
            # Use Tkinter's winfo_rgb to get RGB values for color names
            r, g, b = self.main_window.winfo_rgb(color)
            return (r // 256, g // 256, b // 256)  # Convert to 8-bit RGB

    def get_luminance(self, color):
        """Calculate the luminance of a given color."""
        r, g, b = self.get_rgb(color)
        return 0.299 * r + 0.587 * g + 0.114 * b

    def get_text_color(self, bg_color):
        """Determine text color (black or white) based on the luminance of the background color."""
        luminance = self.get_luminance(bg_color)
        return 'black' if luminance > 128 else 'white'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Application for managing M3U playlists to play and transcribe with Whisper AI.")

    parser.add_argument('--tabs', nargs='+', default=["IPTV", "YouTube", "Twitch", "streamlink", "yt-dlp"],
                        help='List of tab names')

    parser.add_argument('--colors', nargs='+', default=["black", "#ff0000", "#9146ff", "#2c7ef2", "#ff7e00"],
                        help='List of tab colors')

    args = parser.parse_args()

    app = MainApplication(args.tabs, args.colors)
    app.main_window.mainloop()
