import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import yt_dlp
import threading
import os
import queue
from urllib.parse import urlparse
import re


class TikTokProfileDownloader(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("TikTok Profile Downloader")
        self.geometry("700x500")
        self.download_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.error_logs = []
        self.after(100, self.process_queue)

        # Default save path
        default_path = os.path.join(os.path.expanduser("~"), "TikTok_Downloads")
        if not os.path.exists(default_path):
            os.makedirs(default_path, exist_ok=True)
        self.default_save_path = default_path

        self.build_ui()

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Profile URL Frame
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill="x", pady=10)
        ttk.Label(
            url_frame, text="TikTok Profile URL:", font=("Helvetica", 12, "bold")
        ).pack(side="left", padx=5)
        self.url_entry = ttk.Entry(url_frame, width=50, font=("Helvetica", 10))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Example URL
        example_label = ttk.Label(
            main_frame,
            text="Example: https://www.tiktok.com/@username",
            font=("Helvetica", 9),
            foreground="gray",
        )
        example_label.pack(anchor="w", pady=(0, 10))

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

        # Download type
        self.download_type = tk.StringVar(value="video")
        ttk.Radiobutton(
            options_frame,
            text="Download Videos (MP4)",
            variable=self.download_type,
            value="video",
            style="info.TRadiobutton",
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            options_frame,
            text="Download Audio Only (MP3)",
            variable=self.download_type,
            value="audio",
            style="info.TRadiobutton",
        ).pack(anchor="w", pady=2)

        # Video quality
        ttk.Separator(options_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(
            options_frame, text="Video Quality:", font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))

        self.quality_var = tk.StringVar(value="best")
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill="x", pady=2)

        ttk.Radiobutton(
            quality_frame,
            text="Best Quality",
            variable=self.quality_var,
            value="best",
            style="info.TRadiobutton",
        ).pack(side="left", padx=10)
        ttk.Radiobutton(
            quality_frame,
            text="720p (Faster)",
            variable=self.quality_var,
            value="720p",
            style="info.TRadiobutton",
        ).pack(side="left", padx=10)

        # Max videos
        ttk.Separator(options_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(
            options_frame,
            text="Maximum videos to download:",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        max_frame = ttk.Frame(options_frame)
        max_frame.pack(fill="x", pady=2)
        self.max_videos_var = tk.StringVar(value="all")
        ttk.Radiobutton(
            max_frame,
            text="All Videos",
            variable=self.max_videos_var,
            value="all",
            style="info.TRadiobutton",
        ).pack(side="left", padx=10)

        self.max_videos_entry = ttk.Entry(max_frame, width=10, font=("Helvetica", 10))
        self.max_videos_entry.pack(side="left", padx=(20, 5))
        ttk.Label(max_frame, text="videos", font=("Helvetica", 10)).pack(
            side="left", padx=5
        )

        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=15)
        self.start_btn = ttk.Button(
            control_frame,
            text="Start Download",
            command=self.start_download,
            style="success.TButton",
            width=15,
        )
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop",
            command=self.stop_download,
            style="danger.TButton",
            state="disabled",
            width=10,
        )
        self.stop_btn.pack(side="left", padx=5)
        ttk.Button(
            control_frame,
            text="Copy Errors",
            command=self.copy_errors,
            style="warning.TButton",
            width=12,
        ).pack(side="left", padx=5)

        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=10)

        ttk.Label(
            progress_frame, text="Progress:", font=("Helvetica", 11, "bold")
        ).pack(anchor="w")
        self.progress = ttk.Progressbar(
            progress_frame, mode="determinate", style="success.TProgressbar"
        )
        self.progress.pack(fill="x", pady=(2, 0))

        # Stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=5)
        self.stats_label = ttk.Label(
            stats_frame, text="Files: 0 | Profile: Not loaded", font=("Helvetica", 10)
        )
        self.stats_label.pack(anchor="w")

        # Log text area
        log_frame = ttk.LabelFrame(main_frame, text="Download Log", padding=5)
        log_frame.pack(fill="both", expand=True, pady=10)

        self.log_text = ttk.Text(log_frame, height=8, font=("Helvetica", 9))
        scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def validate_tiktok_url(self, url):
        """Validate TikTok profile URL"""
        if not url:
            return False, "URL cannot be empty"

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"

            if "tiktok.com" not in parsed.netloc:
                return False, "Please enter a TikTok URL"

            # Extract username
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 1 and path_parts[0].startswith("@"):
                username = path_parts[0][1:]  # Remove @
                if username:
                    return True, f"TikTok profile detected: @{username}"

            return (
                False,
                "Invalid TikTok profile URL. Use format: https://www.tiktok.com/@username",
            )

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
        is_valid, message = self.validate_tiktok_url(url)
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

        # Get max videos
        max_videos = self.max_videos_var.get()
        if max_videos != "all":
            try:
                max_videos = int(self.max_videos_entry.get())
                if max_videos <= 0:
                    raise ValueError("Must be positive")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number of videos")
                return

        # Confirm large downloads
        confirm = messagebox.askyesno(
            "Confirm Download",
            f"Download all videos from TikTok profile?\n\nThis may take a long time and use significant storage space.\n\nContinue?",
        )
        if not confirm:
            return

        # Start download
        self.stop_event.clear()
        self.error_logs = []
        self.download_thread = threading.Thread(
            target=self.download_profile, args=(url, download_path, max_videos)
        )
        self.download_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress["value"] = 0
        self.progress["mode"] = "determinate"
        self.file_count = 0
        self.total_videos = 0
        self.profile_name = ""
        self.log_text.delete(1.0, tk.END)
        self.log_queue.put(("log", f"Starting TikTok profile download: {url}\n"))

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
                elif msg[0] == "set_max":
                    self.progress["maximum"] = msg[1]
                    self.total_videos = msg[1]
                elif msg[0] == "inc_count":
                    self.file_count += msg[1]
                elif msg[0] == "profile_info":
                    self.profile_name = msg[1]
                elif msg[0] == "update_stats":
                    stats_text = f"Files: {self.file_count} | Profile: {self.profile_name} | Progress: {self.progress['value']}/{self.total_videos}"
                    self.stats_label.config(text=stats_text)
                elif msg[0] == "done":
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    if self.download_thread and self.download_thread.is_alive():
                        self.download_thread.join(timeout=2)
                    self.download_thread = None
                    final_stats = f"Download completed! Files: {self.file_count} | Profile: {self.profile_name}"
                    self.stats_label.config(text=final_stats)
                    self.log_queue.put(
                        (
                            "log",
                            f"\n🎉 Download finished! Successfully downloaded {self.file_count} videos.\n",
                        )
                    )
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def get_tiktok_options(self, download_path, download_type, quality, max_videos):
        """Get TikTok-specific yt-dlp options"""
        # Base output template with username folder
        outtmpl = os.path.join(
            download_path,
            "%(uploader)s/%(title|%(upload_date)s - %(duration_string)s - %(view_count)s views).%(ext)s",
        )

        base_options = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,  # Continue on errors for TikTok
            "continuedl": True,
            "writesubtitles": False,
            "writeinfojson": True,  # Save metadata
            "writethumbnail": True,  # Save thumbnails
            "embed_subs": False,
            "restrictfilenames": True,
        }

        # Max videos limit
        if max_videos != "all":
            base_options["playlistend"] = max_videos

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
                    "keepvideo": False,
                    "outtmpl": os.path.join(
                        download_path,
                        "%(uploader)s/%(title|%(upload_date)s - %(duration_string)s - %(view_count)s views).%(ext)s",
                    ),
                }
            )
        else:  # video
            if quality == "720p":
                base_options.update(
                    {
                        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                        "merge_output_format": "mp4",
                    }
                )
            else:
                base_options.update(
                    {
                        "format": "bestvideo+bestaudio/best",
                        "merge_output_format": "mp4",
                    }
                )

        # TikTok specific settings
        base_options.update(
            {
                "extract_flat": False,
                "playliststart": 1,
                "noplaylist": False,  # We want the full profile playlist
            }
        )

        return base_options

    def download_profile(self, url, download_path, max_videos):
        """Download entire TikTok profile"""
        download_type = self.download_type.get()
        quality = self.quality_var.get()

        try:
            self.log_queue.put(("log", "Preparing TikTok download options...\n"))

            ydl_opts = self.get_tiktok_options(
                download_path, download_type, quality, max_videos
            )
            ydl_opts["progress_hooks"] = [self.ydl_hook]

            self.log_queue.put(("log", "Initializing yt-dlp for TikTok...\n"))

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First, analyze the profile
                self.log_queue.put(("log", "Analyzing TikTok profile...\n"))

                try:
                    # Extract info without downloading
                    info = ydl.extract_info(url, download=False)

                    # Get profile info
                    profile_name = info.get("uploader", "Unknown")
                    total_videos = info.get("playlist_count", 0)

                    self.log_queue.put(("profile_info", profile_name))
                    self.log_queue.put(("set_max", total_videos))
                    self.log_queue.put(("log", f"Found profile: @{profile_name}\n"))
                    self.log_queue.put(
                        ("log", f"Total videos available: {total_videos}\n")
                    )

                    # Create profile folder
                    profile_folder = os.path.join(download_path, profile_name)
                    os.makedirs(profile_folder, exist_ok=True)

                    self.log_queue.put(("update_stats", ""))

                except Exception as analysis_error:
                    self.log_queue.put(
                        ("log", f"Analysis warning: {str(analysis_error)}\n")
                    )
                    self.log_queue.put(("set_max", 100))  # Default max
                    self.log_queue.put(("profile_info", "Unknown"))
                    total_videos = 100

                # Start downloading
                self.log_queue.put(("log", "🚀 Starting video downloads...\n"))
                ydl.download([url])

                self.log_queue.put(
                    (
                        "log",
                        f"\n✅ Profile download completed for @{self.profile_name}\n",
                    )
                )
                self.log_queue.put(("done",))

        except yt_dlp.utils.DownloadCancelled:
            self.log_queue.put(("log", "\n⏹️ Download cancelled by user\n"))
        except yt_dlp.utils.DownloadError as e:
            error_msg = f"TikTok download error: {str(e)}"
            self.log_queue.put(("log", f"\n❌ {error_msg}\n"))
            self.error_logs.append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.log_queue.put(("log", f"\n❌ {error_msg}\n"))
            self.error_logs.append(error_msg)
        finally:
            self.log_queue.put(("done",))

    def ydl_hook(self, d):
        """Progress hook for yt-dlp"""
        if self.stop_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Download stopped by user")

        try:
            if d["status"] == "downloading":
                # Get video info
                title = d.get("title", "Unknown video")[:60]
                uploader = d.get("uploader", "Unknown")[:20]
                duration = d.get("duration_string", "Unknown")

                if "_percent_str" in d:
                    percent_str = d.get("_percent_str", "0%")
                    try:
                        percent = float(percent_str.rstrip("%"))
                        self.log_queue.put(("progress", percent))
                    except (ValueError, TypeError):
                        pass

                # Update progress for current video
                self.log_queue.put(
                    ("log", f"⬇️ [{uploader}] {title} ({duration}) - {percent_str}\n")
                )

            elif d["status"] == "finished":
                # File completed
                filename = d.get("filename", "")
                if filename:
                    basename = os.path.basename(filename)
                    self.log_queue.put(("log", f"✅ Saved: {basename}\n"))
                    self.log_queue.put(("inc_count", 1))
                    self.log_queue.put(("update_stats", ""))

            elif d["status"] == "error":
                # Download error
                error = d.get("error", "Unknown error")
                title = d.get("title", "Unknown video")[:50]
                self.log_queue.put(("log", f"❌ Failed '{title}': {error[:80]}...\n"))
                self.error_logs.append(f"Error downloading '{title}': {error}")

        except Exception as e:
            self.log_queue.put(("log", f"⚠️ Progress error: {str(e)}\n"))


if __name__ == "__main__":
    app = TikTokProfileDownloader()
    app.mainloop()
