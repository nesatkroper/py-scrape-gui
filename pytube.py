import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import threading
import os
import yt_dlp


class YouTubeDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("YouTube Downloader")
        master.geometry("600x300")
        master.resizable(False, False)

        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        center_x = int(screen_width / 2 - 600 / 2)
        center_y = int(screen_height / 2 - 300 / 2)
        master.geometry(f"600x300+{center_x}+{center_y}")

        main_frame = tk.Frame(master, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        self.url_label = tk.Label(
            main_frame, text="Enter YouTube URL:", font=("Helvetica", 12)
        )
        self.url_label.pack(pady=(0, 5))

        self.url_entry = tk.Entry(main_frame, width=50, font=("Helvetica", 12))
        self.url_entry.pack(pady=(0, 10))

        self.type_frame = tk.Frame(main_frame)
        self.type_frame.pack(pady=(0, 10))

        self.download_type = tk.StringVar(value="video")

        self.video_radio = tk.Radiobutton(
            self.type_frame,
            text="Download Video",
            variable=self.download_type,
            value="video",
            font=("Helvetica", 10),
        )
        self.video_radio.pack(side="left", padx=10)

        self.audio_radio = tk.Radiobutton(
            self.type_frame,
            text="Download Audio Only",
            variable=self.download_type,
            value="audio",
            font=("Helvetica", 10),
        )
        self.audio_radio.pack(side="left", padx=10)

        self.download_button = tk.Button(
            main_frame,
            text="Download",
            command=self.start_download,
            font=("Helvetica", 12),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            bd=3,
        )
        self.download_button.pack(pady=(0, 10))

        self.status_label = tk.Label(
            main_frame, text="", font=("Helvetica", 10), fg="blue"
        )
        self.status_label.pack(pady=(5, 0))

    def start_download(self):
        """Starts the download process in a new thread to keep the GUI responsive."""
        self.download_button.config(state=tk.DISABLED, text="Downloading...")
        self.status_label.config(text="Starting download...")

        download_thread = threading.Thread(target=self.download_content)
        download_thread.start()

    def download_content(self):
        """Handles downloading using yt-dlp."""
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            self.reset_ui()
            return

        try:
            download_path = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
            if not download_path:
                self.status_label.config(text="Download canceled.")
                self.reset_ui()
                return

            download_choice = self.download_type.get()

            self.status_label.config(text="Fetching info...")

            ydl_opts = {
                "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
                "quiet": True,
                "progress_hooks": [self.ydl_hook],
            }

            if download_choice == "audio":
                ydl_opts.update(
                    {
                        "format": "bestaudio/best",
                        "postprocessors": [
                            {
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3",
                                "preferredquality": "192",
                            }
                        ],
                    }
                )
            else:  # video
                ydl_opts.update(
                    {
                        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                        "merge_output_format": "mp4",
                    }
                )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get("title", "Video")
                self.status_label.config(text=f"Download complete: {title}")
                messagebox.showinfo("Success", f"'{title}' downloaded successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_label.config(text="Download failed.")
        finally:
            self.reset_ui()

    def ydl_hook(self, d):
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "").strip()
            self.status_label.config(text=f"Downloading... {percent}")
        elif d["status"] == "finished":
            self.status_label.config(text="Download finished, finalizing...")

    def reset_ui(self):
        self.download_button.config(state=tk.NORMAL, text="Download")


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()


# import tkinter as tk
# from tkinter import filedialog
# from tkinter import messagebox
# from pytube import YouTube
# import threading
# import os

# class YouTubeDownloaderApp:
#     def __init__(self, master):
#         self.master = master
#         master.title("YouTube Downloader")
#         master.geometry("600x300")
#         master.resizable(False, False)

#         screen_width = master.winfo_screenwidth()
#         screen_height = master.winfo_screenheight()
#         center_x = int(screen_width/2 - 600/2)
#         center_y = int(screen_height/2 - 300/2)
#         master.geometry(f'600x300+{center_x}+{center_y}')

#         main_frame = tk.Frame(master, padx=20, pady=20)
#         main_frame.pack(fill="both", expand=True)

#         self.url_label = tk.Label(main_frame, text="Enter YouTube URL:", font=("Helvetica", 12))
#         self.url_label.pack(pady=(0, 5))

#         self.url_entry = tk.Entry(main_frame, width=50, font=("Helvetica", 12))
#         self.url_entry.pack(pady=(0, 10))

#         self.type_frame = tk.Frame(main_frame)
#         self.type_frame.pack(pady=(0, 10))

#         self.download_type = tk.StringVar(value="video")

#         self.video_radio = tk.Radiobutton(self.type_frame, text="Download Video", variable=self.download_type, value="video", font=("Helvetica", 10))
#         self.video_radio.pack(side="left", padx=10)

#         self.audio_radio = tk.Radiobutton(self.type_frame, text="Download Audio Only", variable=self.download_type, value="audio", font=("Helvetica", 10))
#         self.audio_radio.pack(side="left", padx=10)

#         self.download_button = tk.Button(main_frame, text="Download", command=self.start_download, font=("Helvetica", 12), bg="#4CAF50", fg="white", relief=tk.RAISED, bd=3)
#         self.download_button.pack(pady=(0, 10))

#         self.status_label = tk.Label(main_frame, text="", font=("Helvetica", 10), fg="blue")
#         self.status_label.pack(pady=(5, 0))

#     def start_download(self):
#         """Starts the download process in a new thread to keep the GUI responsive."""
#         self.download_button.config(state=tk.DISABLED, text="Downloading...")
#         self.status_label.config(text="Starting download...")

#         download_thread = threading.Thread(target=self.download_content)
#         download_thread.start()

#     def download_content(self):
#         """The main function to handle the download logic."""
#         url = self.url_entry.get()
#         if not url:
#             messagebox.showerror("Error", "Please enter a YouTube URL.")
#             self.download_button.config(state=tk.NORMAL, text="Download")
#             self.status_label.config(text="")
#             return

#         try:
#             yt = YouTube(url)

#             download_path = filedialog.askdirectory(initialdir=os.path.expanduser("~"))

#             if not download_path:
#                 self.status_label.config(text="Download canceled.")
#                 self.download_button.config(state=tk.NORMAL, text="Download")
#                 return

#             download_choice = self.download_type.get()

#             if download_choice == "video":
#                 stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
#                 if not stream:
#                     messagebox.showerror("Error", "No progressive video stream found. Cannot download.")
#                     self.status_label.config(text="")
#                     return
#                 self.status_label.config(text=f"Downloading video: '{yt.title}'...")
#             elif download_choice == "audio":
#                 stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
#                 if not stream:
#                     messagebox.showerror("Error", "No audio stream found. Cannot download.")
#                     self.status_label.config(text="")
#                     return
#                 self.status_label.config(text=f"Downloading audio: '{yt.title}'...")

#             file_path = stream.download(output_path=download_path)

#             self.status_label.config(text="Download complete! File saved to:\n" + file_path)
#             messagebox.showinfo("Success", f"'{yt.title}' has been downloaded successfully!")

#         except Exception as e:
#             messagebox.showerror("Error", f"An error occurred: {e}")
#             self.status_label.config(text="Download failed.")
#         finally:
#             self.download_button.config(state=tk.NORMAL, text="Download")

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = YouTubeDownloaderApp(root)
#     root.mainloop()
