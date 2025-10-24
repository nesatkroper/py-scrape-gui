import customtkinter
from threading import Thread
import subprocess
import os
import re
import time
import sys

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class YouTubeDownloaderApp(customtkinter.CTk):
    """
    A modern, minimal YouTube Channel Downloader GUI built with CustomTkinter.
    It uses yt-dlp via subprocess in a separate thread to prevent the GUI from freezing.
    """
    def __init__(self):
        super().__init__()

        self.title("Minimal YouTube Channel Downloader")
        self.geometry("700x580")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.is_downloading = False
        self.download_process = None
        

        self.title_label = customtkinter.CTkLabel(self, text="YouTube Channel Downloader", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.url_entry = customtkinter.CTkEntry(self, placeholder_text="Paste Channel or Playlist URL Here...", width=500)
        self.url_entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.download_button = customtkinter.CTkButton(self, text="Start Download", command=self.start_download_thread, fg_color="#E53935", hover_color="#C62828")
        self.download_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.progress_bar = customtkinter.CTkProgressBar(self, mode="determinate")
        self.progress_bar.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = customtkinter.CTkLabel(self, text="Ready. Enter a channel or playlist URL.", text_color="gray")
        self.status_label.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="ew")
        
        self.log_text = customtkinter.CTkTextbox(self, width=500, height=200, state="disabled")
        self.log_text.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.log("Application started.")
        self.log(f"Downloads will be saved to: {os.getcwd()}")


    def log(self, message):
        """Helper function to safely append messages to the log box."""
        def update_log():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
            
        self.after(0, update_log)


    def update_progress(self, progress_text):
        """Parses yt-dlp output and updates the progress bar and status label."""
        
        match = re.search(r"(\d+\.\d+)%", progress_text)
        
        if match:
            percent = float(match.group(1)) / 100.0
            
            speed_match = re.search(r"(\d+\.\d+\w+/s)", progress_text)
            eta_match = re.search(r"ETA\s+(\d+:\d+|\d+s)", progress_text)
            
            speed = speed_match.group(1) if speed_match else "N/A"
            eta = eta_match.group(1) if eta_match else "N/A"
            
            status_message = f"Downloading... {round(percent * 100, 2)}% at {speed} | ETA: {eta}"
            
            def update_gui():
                self.progress_bar.set(percent)
                self.status_label.configure(text=status_message)
            
            self.after(0, update_gui)
            
        self.log(progress_text)
        
    def start_download_thread(self):
        """Initiates the download function in a new thread."""
        if self.is_downloading:
            self.log("Download already in progress. Please wait.")
            return

        url = self.url_entry.get().strip()
        if not url:
            self.log("ERROR: Please enter a valid YouTube Channel or Playlist URL.")
            self.status_label.configure(text="ERROR: No URL provided.", text_color="#E53935")
            return

        self.is_downloading = True
        self.download_button.configure(text="Downloading...", state="disabled", fg_color="gray")
        self.status_label.configure(text="Starting process...", text_color="orange")
        self.progress_bar.set(0)
        
        Thread(target=self.download_channel, args=(url,), daemon=True).start()


    def download_channel(self, url):
        """The main logic that runs yt-dlp and captures its output."""
        try:
            command = [
                "yt-dlp",
                "--ignore-errors",
                "-o", os.path.join(os.getcwd(), 'YouTubeDownloads', '%(uploader)s', '%(title)s.%(ext)s'),
                "--progress",
                "--newline",
                url
            ]
            
            self.log(f"Executing command: {' '.join(command)}")

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.download_process = process
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.update_progress(line)
            
            return_code = process.wait()

            if return_code == 0:
                final_status = "Download COMPLETE! Check your 'YouTubeDownloads' folder."
                self.status_label.configure(text=final_status, text_color="green")
                self.progress_bar.set(1)
            else:
                final_status = f"Download FINISHED with ERRORS (Code: {return_code}). Check log."
                self.status_label.configure(text=final_status, text_color="#E53935")
                self.progress_bar.set(0)

            self.log(final_status)

        except FileNotFoundError:
            self.log("FATAL ERROR: 'yt-dlp' executable not found. Please ensure it is installed and in your system PATH.")
            self.status_label.configure(text="FATAL ERROR: yt-dlp not found.", text_color="#E53935")
        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")
            self.status_label.configure(text="Download failed.", text_color="#E53935")
        finally:
            self.is_downloading = False
            self.download_process = None
            self.download_button.configure(text="Start Download", state="normal", fg_color="#E53935")
            

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
