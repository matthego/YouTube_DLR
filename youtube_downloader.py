import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import requests
from PIL import Image, ImageTk
import os
import threading
import re
import subprocess
import sys
import urllib.request
import json


# ------------------------------------------------------------
# PATHS / yt-dlp LOCATION
# ------------------------------------------------------------

def get_application_directory():
    """
    Get the directory where the application/script is located.

    For a PyInstaller EXE:
        Returns the folder containing the EXE.

    For a normal Python script:
        Returns the folder containing the .py file.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))


APP_DIR = get_application_directory()
YT_DLP_PATH = os.path.join(APP_DIR, "yt-dlp.exe")


# Official yt-dlp GitHub endpoints
YT_DLP_LATEST_API = (
    "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
)

YT_DLP_DOWNLOAD_URL = (
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
)


# ------------------------------------------------------------
# yt-dlp VERSION FUNCTIONS
# ------------------------------------------------------------

def get_local_yt_dlp_version():
    """
    Get the version of the external yt-dlp.exe.
    """
    try:
        if not os.path.exists(YT_DLP_PATH):
            return None

        result = subprocess.run(
            [YT_DLP_PATH, "--version"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            return None

        return result.stdout.strip()

    except Exception as e:
        print(f"Could not determine yt-dlp version: {e}")
        return None


def get_latest_yt_dlp_version():
    """
    Get the latest yt-dlp version from the official GitHub API.
    """
    try:
        request = urllib.request.Request(
            YT_DLP_LATEST_API,
            headers={
                "User-Agent": "YouTube-Downloader-App"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())

        latest_version = data["tag_name"]

        # GitHub tag is normally something like:
        # 2026.08.19
        # or potentially v2026.08.19
        latest_version = latest_version.lstrip("v")

        return latest_version

    except Exception as e:
        print(f"Could not check latest yt-dlp version: {e}")
        return None


# ------------------------------------------------------------
# DOWNLOAD yt-dlp.exe
# ------------------------------------------------------------

def download_yt_dlp():
    """
    Download the latest official yt-dlp.exe from GitHub.
    """
    try:
        temp_path = YT_DLP_PATH + ".new"

        request = urllib.request.Request(
            YT_DLP_DOWNLOAD_URL,
            headers={
                "User-Agent": "YouTube-Downloader-App"
            }
        )

        print("Downloading latest yt-dlp.exe...")

        with urllib.request.urlopen(request, timeout=60) as response:
            with open(temp_path, "wb") as output_file:
                while True:
                    chunk = response.read(1024 * 1024)

                    if not chunk:
                        break

                    output_file.write(chunk)

        # Make sure the download actually exists
        if not os.path.exists(temp_path):
            raise Exception("Downloaded yt-dlp file was not found.")

        # Remove existing yt-dlp.exe if present
        if os.path.exists(YT_DLP_PATH):
            os.remove(YT_DLP_PATH)

        # Rename downloaded file
        os.replace(temp_path, YT_DLP_PATH)

        print("yt-dlp.exe downloaded successfully.")

        return True

    except Exception as e:
        # Clean up temporary file if something went wrong
        temp_path = YT_DLP_PATH + ".new"

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

        messagebox.showerror(
            "yt-dlp Download Failed",
            f"Could not download yt-dlp:\n\n{str(e)}"
        )

        return False


# ------------------------------------------------------------
# AUTO UPDATE yt-dlp
# ------------------------------------------------------------

def update_yt_dlp():
    """
    Update the external yt-dlp.exe using yt-dlp's official updater.
    """
    try:
        if not os.path.exists(YT_DLP_PATH):
            return download_yt_dlp()

        messagebox.showinfo(
            "Updating yt-dlp",
            "yt-dlp will now update itself.\n\n"
            "Please wait while the update completes."
        )

        result = subprocess.run(
            [YT_DLP_PATH, "-U"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        print("yt-dlp update output:")
        print(result.stdout)

        if result.stderr:
            print("yt-dlp update errors:")
            print(result.stderr)

        if result.returncode != 0:
            raise Exception(
                result.stderr.strip()
                or result.stdout.strip()
                or "yt-dlp returned an unknown error."
            )

        # Verify the version after updating
        updated_version = get_local_yt_dlp_version()

        if updated_version:
            messagebox.showinfo(
                "Update Complete",
                f"yt-dlp has been updated successfully.\n\n"
                f"Installed version: {updated_version}"
            )
        else:
            messagebox.showwarning(
                "Update Complete",
                "yt-dlp reported that the update completed, "
                "but the new version could not be verified."
            )

        return True

    except Exception as e:
        messagebox.showerror(
            "Update Failed",
            f"Could not update yt-dlp:\n\n{str(e)}"
        )

        return False


def check_for_yt_dlp_update():
    """
    Check GitHub for the latest yt-dlp version.
    """
    try:
        # If yt-dlp.exe doesn't exist, download it automatically.
        if not os.path.exists(YT_DLP_PATH):

            answer = messagebox.askyesno(
                "yt-dlp Required",
                "yt-dlp.exe was not found.\n\n"
                "Would you like to download it now?"
            )

            if answer:
                if download_yt_dlp():
                    local_version = get_local_yt_dlp_version()

                    if local_version:
                        messagebox.showinfo(
                            "yt-dlp Installed",
                            f"yt-dlp has been installed successfully.\n\n"
                            f"Version: {local_version}"
                        )
            else:
                messagebox.showwarning(
                    "yt-dlp Required",
                    "yt-dlp is required to download videos and audio."
                )

            return

        local_version = get_local_yt_dlp_version()

        if not local_version:
            messagebox.showerror(
                "yt-dlp Error",
                "yt-dlp.exe was found, but its version could not be determined."
            )
            return

        latest_version = get_latest_yt_dlp_version()

        if not latest_version:
            print("Could not determine latest yt-dlp version.")
            return

        print(f"Local yt-dlp version: {local_version}")
        print(f"Latest yt-dlp version: {latest_version}")

        # Compare versions numerically by splitting the version string.
        local_parts = tuple(
            int(x) for x in local_version.split(".")
        )

        latest_parts = tuple(
            int(x) for x in latest_version.split(".")
        )

        if latest_parts > local_parts:

            answer = messagebox.askyesno(
                "Update Available",
                f"A new version of yt-dlp is available.\n\n"
                f"Local version: {local_version}\n"
                f"Latest version: {latest_version}\n\n"
                f"Would you like to update now?"
            )

            if answer:
                update_yt_dlp()

        else:
            print("yt-dlp is up to date.")

    except Exception as e:
        print(f"Update check failed: {e}")


# ------------------------------------------------------------
# DOWNLOAD FUNCTIONS
# ------------------------------------------------------------

def download_video(url, save_path):
    try:

        output_template = os.path.join(
            save_path,
            "%(title)s.%(ext)s"
        )

        command = [
            YT_DLP_PATH,

            "--format",
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",

            "--output",
            output_template,

            "--newline",

            "--no-color",

            url
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        for line in process.stdout:

            print(line, end="")

            match = re.search(
                r"(\d+(?:\.\d+)?)%",
                line
            )

            if match:
                try:
                    pct = float(match.group(1))
                    root.after(
                        0,
                        lambda value=pct:
                        progress_var.set(value)
                    )
                except:
                    pass

        process.wait()

        if process.returncode == 0:
            root.after(
                0,
                lambda: progress_var.set(100)
            )
            return True

        raise Exception(
            f"yt-dlp exited with code {process.returncode}"
        )

    except Exception as e:
        root.after(
            0,
            lambda error=str(e):
            messagebox.showerror(
                "Error",
                f"Failed to download video:\n{error}"
            )
        )

        return False


def download_audio(url, save_path):
    try:

        output_template = os.path.join(
            save_path,
            "%(title)s.%(ext)s"
        )

        command = [
            YT_DLP_PATH,

            "--format",
            "bestaudio/best",

            "--output",
            output_template,

            "--extract-audio",

            "--audio-format",
            "mp3",

            "--audio-quality",
            "192K",

            "--newline",

            "--no-color",

            url
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        for line in process.stdout:

            print(line, end="")

            match = re.search(
                r"(\d+(?:\.\d+)?)%",
                line
            )

            if match:
                try:
                    pct = float(match.group(1))
                    root.after(
                        0,
                        lambda value=pct:
                        progress_var.set(value)
                    )
                except:
                    pass

        process.wait()

        if process.returncode == 0:
            root.after(
                0,
                lambda: progress_var.set(100)
            )
            return True

        raise Exception(
            f"yt-dlp exited with code {process.returncode}"
        )

    except Exception as e:
        root.after(
            0,
            lambda error=str(e):
            messagebox.showerror(
                "Error",
                f"Failed to download audio:\n{error}"
            )
        )

        return False


# ------------------------------------------------------------
# VIDEO METADATA
# ------------------------------------------------------------

def get_video_metadata(url):
    try:
        response = requests.get(
            f"https://www.youtube.com/oembed?url={url}&format=json",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
            "title": data.get(
                "title",
                "Unknown Title"
            ),

            "thumbnail_url": data.get(
                "thumbnail_url",
                ""
            ),

            "author_name": data.get(
                "author_name",
                "Unknown Author"
            )
        }

    except Exception as e:
        root.after(
            0,
            lambda error=str(e):
            messagebox.showerror(
                "Error",
                f"Failed to fetch video metadata:\n{error}"
            )
        )

        return None


# ------------------------------------------------------------
# THREAD HANDLERS
# ------------------------------------------------------------

def download_video_clicked():

    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning(
            "Missing URL",
            "Please enter a YouTube URL."
        )
        return

    save_path = filedialog.askdirectory()

    if not save_path:
        return

    progress_var.set(0)

    threading.Thread(
        target=handle_video_download,
        args=(url, save_path),
        daemon=True
    ).start()


def download_audio_clicked():

    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning(
            "Missing URL",
            "Please enter a YouTube URL."
        )
        return

    save_path = filedialog.askdirectory()

    if not save_path:
        return

    progress_var.set(0)

    threading.Thread(
        target=handle_audio_download,
        args=(url, save_path),
        daemon=True
    ).start()


def handle_video_download(url, save_path):

    metadata = get_video_metadata(url)

    if metadata:

        root.after(
            0,
            lambda: update_metadata_display(metadata)
        )

        if download_video(url, save_path):

            root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    "Video downloaded successfully."
                )
            )


def handle_audio_download(url, save_path):

    metadata = get_video_metadata(url)

    if metadata:

        root.after(
            0,
            lambda: update_metadata_display(metadata)
        )

        if download_audio(url, save_path):

            root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    "Audio downloaded successfully."
                )
            )


# ------------------------------------------------------------
# UI SUPPORT FUNCTIONS
# ------------------------------------------------------------

def update_metadata_display(metadata):

    title_label.config(
        text="Title: " + metadata["title"]
    )

    channel_label.config(
        text="Channel: " + metadata["author_name"]
    )

    try:

        thumbnail_response = requests.get(
            metadata["thumbnail_url"],
            timeout=10
        )

        thumbnail_response.raise_for_status()

        from io import BytesIO

        thumbnail_image = Image.open(
            BytesIO(thumbnail_response.content)
        )

        thumbnail_image = thumbnail_image.resize(
            (150, 150),
            Image.BICUBIC
        )

        thumbnail_photo = ImageTk.PhotoImage(
            thumbnail_image
        )

        thumbnail_label.config(
            image=thumbnail_photo
        )

        thumbnail_label.image = thumbnail_photo

    except Exception as e:
        print(f"Could not load thumbnail: {e}")


# ------------------------------------------------------------
# GUI SETUP
# ------------------------------------------------------------

root = tk.Tk()

root.title("YouTube Downloader")

root.geometry("800x400")


url_label = tk.Label(
    root,
    text="Enter YouTube URL:"
)

url_label.pack()


url_entry = tk.Entry(
    root,
    width=50
)

url_entry.pack()


buttons_frame = tk.Frame(root)

buttons_frame.pack(
    pady=10
)


download_video_button = tk.Button(
    buttons_frame,
    text="Download Video",
    command=download_video_clicked
)

download_video_button.pack(
    side=tk.LEFT,
    padx=5
)


download_audio_button = tk.Button(
    buttons_frame,
    text="Download Audio",
    command=download_audio_clicked
)

download_audio_button.pack(
    side=tk.LEFT,
    padx=5
)


progress_var = tk.DoubleVar()

progress_bar = ttk.Progressbar(
    root,
    variable=progress_var,
    maximum=100
)

progress_bar.pack(
    fill=tk.X,
    padx=10,
    pady=10
)


metadata_frame = tk.Frame(root)

metadata_frame.pack(
    pady=10
)


title_label = tk.Label(
    metadata_frame,
    text="Title: "
)

title_label.pack()


channel_label = tk.Label(
    metadata_frame,
    text="Channel: "
)

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

    root.config(
        bg="black"
    )

    url_label.config(
        bg="black",
        fg="white"
    )

    url_entry.config(
        bg="black",
        fg="white",
        insertbackground="white"
    )

    buttons_frame.config(
        bg="black"
    )

    download_video_button.config(
        bg="gray",
        fg="white"
    )

    download_audio_button.config(
        bg="gray",
        fg="white"
    )

    metadata_frame.config(
        bg="black"
    )

    title_label.config(
        bg="black",
        fg="white"
    )

    channel_label.config(
        bg="black",
        fg="white"
    )

    thumbnail_label.config(
        bg="black"
    )

    progress_bar.config(
        style="dark.Horizontal.TProgressbar"
    )

    toggle_button.config(
        text="Light Mode",
        bg="white",
        fg="black"
    )

    save_mode_preference()


def set_light_mode():

    root.config(
        bg="white"
    )

    url_label.config(
        bg="white",
        fg="black"
    )

    url_entry.config(
        bg="white",
        fg="black",
        insertbackground="black"
    )

    buttons_frame.config(
        bg="white"
    )

    download_video_button.config(
        bg="darkgray",
        fg="black"
    )

    download_audio_button.config(
        bg="darkgray",
        fg="black"
    )

    metadata_frame.config(
        bg="white"
    )

    title_label.config(
        bg="white",
        fg="black"
    )

    channel_label.config(
        bg="white",
        fg="black"
    )

    thumbnail_label.config(
        bg="white"
    )

    progress_bar.config(
        style="light.Horizontal.TProgressbar"
    )

    toggle_button.config(
        text="Dark Mode",
        bg="darkgray",
        fg="white"
    )

    save_mode_preference()


def save_mode_preference():

    preference_path = os.path.join(
        APP_DIR,
        "mode_preference.txt"
    )

    with open(
        preference_path,
        "w"
    ) as f:

        f.write(
            dark_mode.get()
        )


def load_mode_preference():

    preference_path = os.path.join(
        APP_DIR,
        "mode_preference.txt"
    )

    try:

        with open(
            preference_path,
            "r"
        ) as f:

            return f.read().strip()

    except FileNotFoundError:

        return "light"


dark_mode = tk.StringVar()

dark_mode.set(
    load_mode_preference()
)


toggle_button = tk.Button(
    root,
    text="Dark Mode",
    command=toggle_dark_mode,
    bg="darkgray",
    fg="white",
    font=("Arial", 12)
)

toggle_button.pack(
    pady=5
)


style = ttk.Style()

style.configure(
    "light.Horizontal.TProgressbar",
    troughcolor="white",
    background="blue"
)

style.configure(
    "dark.Horizontal.TProgressbar",
    troughcolor="black",
    background="blue"
)


if dark_mode.get() == "light":

    set_light_mode()

else:

    set_dark_mode()


# ------------------------------------------------------------
# RUN yt-dlp UPDATE CHECK ON STARTUP
# ------------------------------------------------------------

check_for_yt_dlp_update()


# ------------------------------------------------------------
# START GUI
# ------------------------------------------------------------

root.mainloop()