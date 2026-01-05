import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import requests
from PIL import Image, ImageTk
import os
import threading
from yt_dlp import YoutubeDL
import re
import subprocess
import sys
import urllib.request
import json


# ------------------------------------------------------------
# AUTO UPDATE: Version Normalization
# ------------------------------------------------------------

def normalize_version(version_str):
    """Normalize version number (fixes 2025.12.08 vs 2025.12.8 issue)."""
    parts = version_str.split(".")
    normalized = ".".join(str(int(p)) for p in parts)
    return normalized


def update_yt_dlp():
    """Update yt-dlp via pip inside the running Python environment."""
    try:
        python_exec = sys.executable
        subprocess.run([python_exec, "-m", "pip", "install", "--upgrade", "yt-dlp"], check=True)
        messagebox.showinfo("Update Complete", "yt-dlp has been updated.\nRestart the program.")
    except Exception as e:
        messagebox.showerror("Update Failed", f"Could not update yt-dlp:\n{str(e)}")


def check_for_yt_dlp_update():
    """Check PyPI for latest yt-dlp version."""
    try:
        import yt_dlp
        local_raw = yt_dlp.version.__version__
        local_ver = normalize_version(local_raw)

        with urllib.request.urlopen("https://pypi.org/pypi/yt-dlp/json") as url:
            latest_raw = json.loads(url.read().decode())["info"]["version"]
            latest_ver = normalize_version(latest_raw)

        if local_ver != latest_ver:
            answer = messagebox.askyesno(
                "Update Available",
                f"A new version of yt-dlp is available.\n\n"
                f"Local version: {local_raw}\n"
                f"Latest version: {latest_raw}\n\n"
                f"Would you like to update now?"
            )
            if answer:
                update_yt_dlp()

    except Exception as e:
        print(f"Update check failed: {e}")


# ------------------------------------------------------------
# DOWNLOAD FUNCTIONS
# ------------------------------------------------------------

def download_video(url, save_path):
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'noprogress': False,
            'no_color': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download video: {str(e)}")
        return False


def download_audio(url, save_path):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noprogress': False,
            'no_color': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download audio: {str(e)}")
        return False


def get_video_metadata(url):
    try:
        response = requests.get(f"https://www.youtube.com/oembed?url={url}&format=json")
        data = response.json()

        return {
            'title': data.get('title', 'Unknown Title'),
            'thumbnail_url': data.get('thumbnail_url', ''),
            'author_name': data.get('author_name', 'Unknown Author')
        }
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch video metadata: {str(e)}")
        return None


# ------------------------------------------------------------
# THREAD HANDLERS
# ------------------------------------------------------------

def download_video_clicked():
    url = url_entry.get()
    save_path = filedialog.askdirectory()
    if not save_path:
        return
    threading.Thread(target=handle_video_download, args=(url, save_path)).start()


def download_audio_clicked():
    url = url_entry.get()
    save_path = filedialog.askdirectory()
    if not save_path:
        return
    threading.Thread(target=handle_audio_download, args=(url, save_path)).start()


def handle_video_download(url, save_path):
    metadata = get_video_metadata(url)
    if metadata:
        update_metadata_display(metadata)
        if download_video(url, save_path):
            messagebox.showinfo("Success", "Video downloaded successfully.")


def handle_audio_download(url, save_path):
    metadata = get_video_metadata(url)
    if metadata:
        update_metadata_display(metadata)
        if download_audio(url, save_path):
            messagebox.showinfo("Success", "Audio downloaded successfully.")


# ------------------------------------------------------------
# UI SUPPORT FUNCTIONS
# ------------------------------------------------------------

def update_metadata_display(metadata):
    title_label.config(text="Title: " + metadata['title'])
    channel_label.config(text="Channel: " + metadata['author_name'])

    thumbnail_response = requests.get(metadata['thumbnail_url'])
    thumbnail_data = thumbnail_response.content
    from io import BytesIO
    thumbnail_image = Image.open(BytesIO(thumbnail_data))
    thumbnail_image = thumbnail_image.resize((150, 150), Image.BICUBIC)
    thumbnail_photo = ImageTk.PhotoImage(thumbnail_image)
    thumbnail_label.config(image=thumbnail_photo)
    thumbnail_label.image = thumbnail_photo


def progress_hook(d):
    if d['status'] == 'downloading':
        clean = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', d['_percent_str'])
        try:
            pct = float(clean.strip('%'))
            progress_var.set(pct)
        except:
            pass
    elif d['status'] == 'finished':
        progress_var.set(100)


# ------------------------------------------------------------
# GUI SETUP
# ------------------------------------------------------------

root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("800x400")

url_label = tk.Label(root, text="Enter YouTube URL:")
url_label.pack()
url_entry = tk.Entry(root, width=50)
url_entry.pack()

buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=10)

download_video_button = tk.Button(buttons_frame, text="Download Video", command=download_video_clicked)
download_video_button.pack(side=tk.LEFT, padx=5)

download_audio_button = tk.Button(buttons_frame, text="Download Audio", command=download_audio_clicked)
download_audio_button.pack(side=tk.LEFT, padx=5)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill=tk.X, padx=10, pady=10)

metadata_frame = tk.Frame(root)
metadata_frame.pack(pady=10)

title_label = tk.Label(metadata_frame, text="Title: ")
title_label.pack()
channel_label = tk.Label(metadata_frame, text="Channel: ")
channel_label.pack()

thumbnail_label = tk.Label(root)
thumbnail_label.pack()


# ------------------------------------------------------------
# DARK / LIGHT MODE
# ------------------------------------------------------------

def toggle_dark_mode():
    if dark_mode.get() == "light":
        dark_mode.set("dark")
        set_dark_mode()
    else:
        dark_mode.set("light")
        set_light_mode()


def set_dark_mode():
    root.config(bg="black")
    url_label.config(bg="black", fg="white")
    url_entry.config(bg="black", fg="white", insertbackground="white")
    buttons_frame.config(bg="black")
    download_video_button.config(bg="gray", fg="white")
    download_audio_button.config(bg="gray", fg="white")
    metadata_frame.config(bg="black")
    title_label.config(bg="black", fg="white")
    channel_label.config(bg="black", fg="white")
    thumbnail_label.config(bg="black")
    progress_bar.config(style="dark.Horizontal.TProgressbar")
    toggle_button.config(text="Light Mode", bg="white", fg="black")
    save_mode_preference()


def set_light_mode():
    root.config(bg="white")
    url_label.config(bg="white", fg="black")
    url_entry.config(bg="white", fg="black", insertbackground="black")
    buttons_frame.config(bg="white")
    download_video_button.config(bg="darkgray", fg="black")
    download_audio_button.config(bg="darkgray", fg="black")
    metadata_frame.config(bg="white")
    title_label.config(bg="white", fg="black")
    channel_label.config(bg="white", fg="black")
    thumbnail_label.config(bg="white")
    progress_bar.config(style="light.Horizontal.TProgressbar")
    toggle_button.config(text="Dark Mode", bg="darkgray", fg="white")
    save_mode_preference()


def save_mode_preference():
    with open("mode_preference.txt", "w") as f:
        f.write(dark_mode.get())


def load_mode_preference():
    try:
        with open("mode_preference.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "light"


dark_mode = tk.StringVar()
dark_mode.set(load_mode_preference())

toggle_button = tk.Button(root, text="Dark Mode", command=toggle_dark_mode,
                          bg="darkgray", fg="white", font=("Arial", 12))
toggle_button.pack(pady=5)

style = ttk.Style()
style.configure("light.Horizontal.TProgressbar", troughcolor="white", background="blue")
style.configure("dark.Horizontal.TProgressbar", troughcolor="black", background="blue")

if dark_mode.get() == "light":
    set_light_mode()
else:
    set_dark_mode()


# ------------------------------------------------------------
# RUN UPDATE CHECK ON STARTUP
# ------------------------------------------------------------
check_for_yt_dlp_update()

root.mainloop()

