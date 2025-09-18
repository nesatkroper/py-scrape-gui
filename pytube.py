import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import yt_dlp
import threading
import os
import queue
import re
from urllib.parse import urlparse
from datetime import datetime


class VideoDownloaderApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Video Downloader (YouTube & TikTok)")
        self.geometry("800x600")
        self.download_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.error_logs = []
        self.after(100, self.process_queue)

        # Default save path
        default_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(default_path):
            default_path = os.getcwd()
        self.default_save_path = default_path

        self.build_ui()

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # URL Frame
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill="x", pady=10)
        ttk.Label(
            url_frame, text="Enter URL (YouTube or TikTok):", font=("Helvetica", 12)
        ).pack(side="left", padx=5)
        self.url_entry = ttk.Entry(url_frame, width=50, font=("Helvetica", 10))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Help text
        help_label = ttk.Label(
            main_frame,
            text="YouTube: Single video/playlist/channel URLs | TikTok: Profile URL[](https://www.tiktok.com/@username)",
            font=("Helvetica", 10),
            foreground="gray",
        )
        help_label.pack(fill="x", pady=(0, 10))

        # Save location frame
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill="x", pady=10)
        ttk.Label(save_frame, text="Save location", font=("Helvetica", 12)).pack(
            side="left", padx=5
        )
        self.save_path = tk.StringVar(value=self.default_save_path)
        path_entry = ttk.Entry(
            save_frame, textvariable=self.save_path, width=40, font=("Helvetica", 10)
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(
            save_frame, text="Browse", command=self.browse_save, style="primary.TButton"
        ).pack(side="left", padx=5)
        ttk.Button(
            save_frame,
            text="New Dir",
            command=self.create_new_dir,
            style="secondary.TButton",
        ).pack(side="left", padx=5)

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Download Options", padding=10)
        options_frame.pack(fill="x", pady=10)

        self.download_scope = tk.StringVar(value="single")
        ttk.Radiobutton(
            options_frame,
            text="Single Video",
            variable=self.download_scope,
            value="single",
            style="info.TRadiobutton",
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            options_frame,
            text="Entire Playlist (YouTube)",
            variable=self.download_scope,
            value="playlist",
            style="info.TRadiobutton",
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            options_frame,
            text="All Videos from Channel/Profile",
            variable=self.download_scope,
            value="channel",
            style="info.TRadiobutton",
        ).pack(anchor="w", pady=2)

        self.download_type = tk.StringVar(value="video")
        ttk.Radiobutton(
            options_frame,
            text="Download as Video",
            variable=self.download_type,
            value="video",
            style="info.TRadiobutton",
        ).pack(anchor="w", pady=5)
        ttk.Radiobutton(
            options_frame,
            text="Download as Audio Only",
            variable=self.download_type,
            value="audio",
            style="info.TRadiobutton",
        ).pack(anchor="w", pady=2)

        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=10)
        self.start_btn = ttk.Button(
            control_frame,
            text="Start Download",
            command=self.start_download,
            style="success.TButton",
        )
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop",
            command=self.stop_download,
            style="danger.TButton",
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=5)
        ttk.Button(
            control_frame,
            text="Copy Errors",
            command=self.copy_errors,
            style="warning.TButton",
        ).pack(side="left", padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame, mode="determinate", style="success.TProgressbar"
        )
        self.progress.pack(fill="x", pady=10)

        # Log text area
        self.log_text = ttk.Text(main_frame, height=10, font=("Helvetica", 9))
        self.log_text.pack(fill="both", expand=True, pady=10)

        # File count
        ttk.Label(main_frame, text="Files downloaded:", font=("Helvetica", 12)).pack(
            anchor="w", pady=5
        )
        self.file_count = tk.IntVar(value=0)
        ttk.Label(
            main_frame, textvariable=self.file_count, font=("Helvetica", 12)
        ).pack(anchor="w", pady=5)

    def validate_url(self, url):
        """Validate if URL is from supported platforms"""
        if not url:
            return False, "URL cannot be empty"

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"

            # YouTube validation
            if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
                return True, "YouTube URL detected"

            # TikTok validation
            if "tiktok.com" in parsed.netloc:
                return True, "TikTok URL detected"

            return False, "Unsupported platform. Only YouTube and TikTok are supported."

        except Exception as e:
            return False, f"URL parsing error: {str(e)}"

    def browse_save(self):
        path = filedialog.askdirectory(initialdir=self.save_path.get())
        if path:
            self.save_path.set(path)

    def create_new_dir(self):
        new_dir = simpledialog.askstring(
            "New Directory", "Enter new directory name:", parent=self
        )
        if new_dir:
            new_path = os.path.join(self.save_path.get(), new_dir)
            try:
                os.makedirs(new_path, exist_ok=True)
                self.save_path.set(new_path)
                self.log_queue.put(("log", f"Created directory: {new_path}\n"))
            except OSError as e:
                error_msg = f"Failed to create directory: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)
                messagebox.showerror("Error", error_msg)

    def copy_errors(self):
        try:
            import pyperclip

            if self.error_logs:
                pyperclip.copy("\n".join(self.error_logs))
                messagebox.showinfo("Success", "Error messages copied to clipboard")
            else:
                messagebox.showinfo("Info", "No error messages to copy")
        except ImportError:
            messagebox.showwarning(
                "Warning",
                "pyperclip not installed. Install with: pip install pyperclip",
            )

    def start_download(self):
        # Validate URL
        url = self.url_entry.get().strip()
        is_valid, message = self.validate_url(url)
        if not is_valid:
            messagebox.showerror("Error", message)
            return

        # Validate save path
        download_path = self.save_path.get()
        if not download_path:
            messagebox.showerror("Error", "Please select a save location")
            return
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path, exist_ok=True)
            except OSError as e:
                messagebox.showerror("Error", f"Cannot access save location: {str(e)}")
                return

        # Confirm large downloads
        scope = self.download_scope.get()
        if scope in ["playlist", "channel"]:
            confirm = messagebox.askyesno(
                "Large Download",
                f"Downloading {scope} may take a long time and use significant storage.\nContinue?",
            )
            if not confirm:
                return

        # Start download
        self.stop_event.clear()
        self.error_logs = []
        self.download_thread = threading.Thread(
            target=self.download_content, args=(url, download_path)
        )
        self.download_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress["value"] = 0
        self.progress["mode"] = "determinate"
        self.file_count.set(0)
        self.log_text.delete(1.0, tk.END)
        self.log_queue.put(("log", f"Starting {scope} download from: {url}\n"))

    def stop_download(self):
        self.stop_event.set()
        self.log_queue.put(("log", "Stopping download...\n"))

    def process_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg[0] == "log":
                    self.log_text.insert(tk.END, msg[1])
                    self.log_text.see(tk.END)
                    if "Error" in msg[1] or "Failed" in msg[1]:
                        self.error_logs.append(msg[1].strip())
                elif msg[0] == "progress":
                    self.progress["value"] = msg[1]
                elif msg[0] == "inc_count":
                    self.file_count.set(self.file_count.get() + msg[1])
                elif msg[0] == "set_max":
                    self.progress["maximum"] = msg[1]
                elif msg[0] == "done":
                    self.progress.stop()
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    if self.download_thread and self.download_thread.is_alive():
                        self.download_thread.join(timeout=2)
                    self.download_thread = None
                    self.log_queue.put(("log", "Download process completed.\n"))
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def get_ydl_options(self, url, download_path, scope, download_type):
        """Configure yt-dlp options based on scope and type"""
        # Simple output template that works for all cases
        outtmpl = os.path.join(download_path, "%(title)s.%(ext)s")

        # For playlists/channels, add numbering
        if scope in ["playlist", "channel"]:
            outtmpl = os.path.join(
                download_path, "%(playlist_index|%03d.)%(title)s.%(ext)s"
            )

        base_options = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,  # Stop on errors
            "continuedl": True,  # Resume partial downloads
            "writesubtitles": False,
            "writeinfojson": False,
            "writethumbnail": False,
            "restrictfilenames": True,  # Avoid problematic characters
        }

        # Platform-specific settings
        if "youtube.com" in url.lower() or "youtu.be" in url.lower():
            base_options["extract_flat"] = False
        elif "tiktok.com" in url.lower():
            base_options["extract_flat"] = False
            # TikTok specific settings
            base_options["format"] = "best"

        # Scope-specific settings
        if scope == "single":
            base_options["noplaylist"] = True
        else:
            base_options["noplaylist"] = False
            base_options["playlistend"] = None  # Download all items

        if scope == "channel":
            # For channels, extract all videos
            base_options["playlist_items"] = None

        # Format selection
        if download_type == "audio":
            base_options.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                    "audioformat": "mp3",
                    "keepvideo": False,
                }
            )
        else:  # video
            if "tiktok.com" not in url.lower():
                base_options.update(
                    {
                        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                        "merge_output_format": "mp4",
                    }
                )
            else:
                # TikTok videos are usually smaller, use best available
                base_options.update(
                    {
                        "format": "best[ext=mp4]/best",
                    }
                )

        return base_options

    def download_content(self, url, download_path):
        """Main download function with proper error handling"""
        scope = self.download_scope.get()
        download_type = self.download_type.get()

        try:
            self.log_queue.put(("log", f"Preparing download options for {scope}...\n"))

            ydl_opts = self.get_ydl_options(url, download_path, scope, download_type)
            ydl_opts["progress_hooks"] = [self.ydl_hook]

            self.log_queue.put(("log", "Initializing yt-dlp...\n"))

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First, extract info to get total count
                self.log_queue.put(("log", "Analyzing content...\n"))

                try:
                    # Try to get info without downloading first
                    info = ydl.extract_info(url, download=False)

                    # Get total items for progress bar
                    total_items = 1
                    if "entries" in info and info["entries"]:
                        total_items = len(info["entries"])
                    elif "_type" in info and info["_type"] in ["playlist", "channel"]:
                        total_items = info.get("playlist_count", 1)

                    self.log_queue.put(("set_max", max(total_items, 1)))
                    self.log_queue.put(
                        ("log", f"Found {total_items} item(s) to download\n")
                    )

                except Exception as analysis_error:
                    self.log_queue.put(
                        (
                            "log",
                            f"Could not analyze content fully, proceeding with download: {str(analysis_error)}\n",
                        )
                    )
                    total_items = 1
                    self.log_queue.put(("set_max", 1))

                # Now download
                self.log_queue.put(("log", "Starting download process...\n"))
                ydl.download([url])

                self.log_queue.put(
                    ("log", f"Successfully processed {total_items} item(s)\n")
                )
                self.log_queue.put(("done",))

        except yt_dlp.utils.DownloadCancelled:
            self.log_queue.put(("log", "Download cancelled by user\n"))
        except yt_dlp.utils.DownloadError as e:
            error_msg = f"Download error: {str(e)}"
            self.log_queue.put(("log", error_msg + "\n"))
            self.error_logs.append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}\n{str(e.__class__.__name__)}"
            self.log_queue.put(("log", error_msg + "\n"))
            self.error_logs.append(error_msg)
        finally:
            self.log_queue.put(("done",))

    def ydl_hook(self, d):
        """Progress hook for yt-dlp"""
        if self.stop_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Download stopped by user")

        try:
            if d["status"] == "downloading":
                # Single file download progress
                if "_percent_str" in d:
                    percent_str = d.get("_percent_str", "0%").strip().rstrip("%")
                    try:
                        percent = float(percent_str)
                        self.log_queue.put(("progress", percent))
                    except (ValueError, TypeError):
                        pass

                # Show download info (but less verbose to avoid spam)
                title = d.get("title", "Unknown")[:50]  # Truncate long titles
                if len(title) > 50:
                    title = title[:47] + "..."

                percent_str = d.get("_percent_str", "0%")
                self.log_queue.put(("log", f"Downloading: {title} ({percent_str})\n"))

            elif d["status"] == "finished":
                # File download completed
                filename = d.get("filename", "Unknown file")
                self.log_queue.put(("log", f"✓ Saved: {os.path.basename(filename)}\n"))
                self.log_queue.put(("inc_count", 1))

            elif d["status"] == "error":
                # Download error
                error = d.get("error", "Unknown error")
                title = d.get("title", "Unknown")[:50]
                self.log_queue.put(
                    ("log", f"✗ Error downloading '{title}': {error[:100]}...\n")
                )
                self.error_logs.append(f"Download error for '{title}': {error}")

        except Exception as e:
            # Don't let progress hook errors crash the download
            self.log_queue.put(("log", f"Progress update error: {str(e)}\n"))


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()


# import tkinter as tk
# from tkinter import filedialog
# from tkinter import messagebox
# import threading
# import os
# import yt_dlp


# class YouTubeDownloaderApp:
#     def __init__(self, master):
#         self.master = master
#         master.title("YouTube Downloader")
#         master.geometry("600x300")
#         master.resizable(False, False)

#         screen_width = master.winfo_screenwidth()
#         screen_height = master.winfo_screenheight()
#         center_x = int(screen_width / 2 - 600 / 2)
#         center_y = int(screen_height / 2 - 300 / 2)
#         master.geometry(f"600x300+{center_x}+{center_y}")

#         main_frame = tk.Frame(master, padx=20, pady=20)
#         main_frame.pack(fill="both", expand=True)

#         self.url_label = tk.Label(
#             main_frame, text="Enter YouTube URL:", font=("Helvetica", 12)
#         )
#         self.url_label.pack(pady=(0, 5))

#         self.url_entry = tk.Entry(main_frame, width=50, font=("Helvetica", 12))
#         self.url_entry.pack(pady=(0, 10))

#         self.type_frame = tk.Frame(main_frame)
#         self.type_frame.pack(pady=(0, 10))

#         self.download_type = tk.StringVar(value="video")

#         self.video_radio = tk.Radiobutton(
#             self.type_frame,
#             text="Download Video",
#             variable=self.download_type,
#             value="video",
#             font=("Helvetica", 10),
#         )
#         self.video_radio.pack(side="left", padx=10)

#         self.audio_radio = tk.Radiobutton(
#             self.type_frame,
#             text="Download Audio Only",
#             variable=self.download_type,
#             value="audio",
#             font=("Helvetica", 10),
#         )
#         self.audio_radio.pack(side="left", padx=10)

#         self.download_button = tk.Button(
#             main_frame,
#             text="Download",
#             command=self.start_download,
#             font=("Helvetica", 12),
#             bg="#4CAF50",
#             fg="white",
#             relief=tk.RAISED,
#             bd=3,
#         )
#         self.download_button.pack(pady=(0, 10))

#         self.status_label = tk.Label(
#             main_frame, text="", font=("Helvetica", 10), fg="blue"
#         )
#         self.status_label.pack(pady=(5, 0))

#     def start_download(self):
#         """Starts the download process in a new thread to keep the GUI responsive."""
#         self.download_button.config(state=tk.DISABLED, text="Downloading...")
#         self.status_label.config(text="Starting download...")

#         download_thread = threading.Thread(target=self.download_content)
#         download_thread.start()

#     def download_content(self):
#         """Handles downloading using yt-dlp."""
#         url = self.url_entry.get()
#         if not url:
#             messagebox.showerror("Error", "Please enter a YouTube URL.")
#             self.reset_ui()
#             return

#         try:
#             download_path = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
#             if not download_path:
#                 self.status_label.config(text="Download canceled.")
#                 self.reset_ui()
#                 return

#             download_choice = self.download_type.get()

#             self.status_label.config(text="Fetching info...")

#             ydl_opts = {
#                 "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
#                 "quiet": True,
#                 "progress_hooks": [self.ydl_hook],
#             }

#             if download_choice == "audio":
#                 ydl_opts.update(
#                     {
#                         "format": "bestaudio/best",
#                         "postprocessors": [
#                             {
#                                 "key": "FFmpegExtractAudio",
#                                 "preferredcodec": "mp3",
#                                 "preferredquality": "192",
#                             }
#                         ],
#                     }
#                 )
#             else:  # video
#                 ydl_opts.update(
#                     {
#                         "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
#                         "merge_output_format": "mp4",
#                     }
#                 )

#             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#                 info_dict = ydl.extract_info(url, download=True)
#                 title = info_dict.get("title", "Video")
#                 self.status_label.config(text=f"Download complete: {title}")
#                 messagebox.showinfo("Success", f"'{title}' downloaded successfully!")

#         except Exception as e:
#             messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
#             self.status_label.config(text="Download failed.")
#         finally:
#             self.reset_ui()

#     def ydl_hook(self, d):
#         if d["status"] == "downloading":
#             percent = d.get("_percent_str", "").strip()
#             self.status_label.config(text=f"Downloading... {percent}")
#         elif d["status"] == "finished":
#             self.status_label.config(text="Download finished, finalizing...")

#     def reset_ui(self):
#         self.download_button.config(state=tk.NORMAL, text="Download")


# if __name__ == "__main__":
#     root = tk.Tk()
#     app = YouTubeDownloaderApp(root)
#     root.mainloop()
