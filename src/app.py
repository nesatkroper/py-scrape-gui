import customtkinter
import tkinter.filedialog as filedialog
from threading import Thread
import subprocess
import os
import re
import sys
import platform
import time
import webbrowser

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "YouTubeDownloads")
if not os.path.exists(DEFAULT_DOWNLOAD_DIR):
    try:
        os.makedirs(DEFAULT_DOWNLOAD_DIR)
    except OSError as e:
        DEFAULT_DOWNLOAD_DIR = os.getcwd()

class YouTubeDownloaderApp(customtkinter.CTk):
    """
    A modern, minimal YouTube Channel Downloader GUI built with CustomTkinter.
    Uses yt-dlp via subprocess for robust downloading and real-time progress.
    """

    def open_telegram(event=None):
        webbrowser.open("https://t.me/devphanun") 


    def __init__(self):
        super().__init__()

        self.title("NunTube Downloader")
        self.geometry("700x650")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self.is_downloading = False
        self.download_process = None
        self.total_videos = 0
        self.completed_videos = 0


        self.title_label = customtkinter.CTkLabel(self, text="YouTube Channel Downloader", font=customtkinter.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.url_entry = customtkinter.CTkEntry(self, placeholder_text="Paste Channel or Playlist URL Here...", height=40)
        self.url_entry.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")

        self.path_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.path_frame.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)
        self.path_frame.grid_columnconfigure(1, weight=0)

        self.path_entry = customtkinter.CTkEntry(self.path_frame, placeholder_text="Output Directory", height=40)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.path_entry.insert(0, DEFAULT_DOWNLOAD_DIR)

        self.browse_button = customtkinter.CTkButton(self.path_frame, text="Browse", width=100, command=self.select_output_path)
        self.browse_button.grid(row=0, column=1, sticky="e")

        self.action_button = customtkinter.CTkButton(self, text="Start Download", command=self.start_stop_action, height=40, font=customtkinter.CTkFont(size=16, weight="bold"), fg_color="#E53935", hover_color="#C62828")
        self.action_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.progress_bar = customtkinter.CTkProgressBar(self, mode="determinate")
        self.progress_bar.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.progress_bar.set(0)

        # self.status_label = customtkinter.CTkLabel(self, text=f"Ready. Default path: {DEFAULT_DOWNLOAD_DIR}", text_color="gray")
        # self.status_label.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.footer_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="ew")

        self.status_label = customtkinter.CTkLabel(
            self.footer_frame,
            text="Developed with love ❤️ ",
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=(10, 0))

        self.name_label = customtkinter.CTkLabel(
            self.footer_frame,
            text="Suon Phanun",
            text_color="white",
            cursor="hand2"
        )
        self.name_label.pack(side="left")
        self.name_label.bind("<Button-1>", self.open_telegram)
        
        self.log_text = customtkinter.CTkTextbox(self, width=500, height=200, state="disabled")
        self.log_text.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        self.log("Application initialized. Ensure yt-dlp is installed and in your PATH.")


    def log(self, message, color="white"):
        """Helper function to safely append messages to the log box."""
        def update_log():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n", color)
            self.log_text.tag_config("white", foreground="white")
            self.log_text.tag_config("orange", foreground="#FFA500")
            self.log_text.tag_config("red", foreground="#E53935")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
            
        self.after(0, update_log)


    def select_output_path(self):
        """Opens a dialog to select the output directory."""
        directory = filedialog.askdirectory(initialdir=self.path_entry.get())
        if directory:
            self.path_entry.delete(0, customtkinter.END)
            self.path_entry.insert(0, directory)
            self.log(f"Output directory set to: {directory}")

    
    def update_overall_progress(self):
        """Updates the main progress bar based on completed vs total videos."""
        
        if self.total_videos > 0:
            overall_progress = self.completed_videos / self.total_videos
            overall_text = f"Overall Progress: {self.completed_videos}/{self.total_videos} videos completed ({round(overall_progress * 100, 1)}%)"
            
            def update_gui():
                self.progress_bar.set(overall_progress)
                self.status_label.configure(text=overall_text, text_color="white")
            
            self.after(0, update_gui)


    def start_stop_action(self):
        """Toggles between starting and stopping the download."""
        if self.is_downloading:
            self.stop_download()
        else:
            self.start_download()

    
    def start_download(self):
        """Initial check and starts the counting/download thread."""
        url = self.url_entry.get().strip()
        output_dir = self.path_entry.get().strip()
        
        if not url:
            self.log("ERROR: Please enter a valid YouTube Channel or Playlist URL.", color="red")
            self.status_label.configure(text="ERROR: No URL provided.", text_color="#E53935")
            return
            
        if not os.path.isdir(output_dir):
             self.log(f"Creating output directory: {output_dir}", color="orange")
             try:
                 os.makedirs(output_dir)
             except Exception as e:
                 self.log(f"FATAL ERROR: Could not create directory {output_dir}. {e}", color="red")
                 self.status_label.configure(text="FATAL ERROR: Directory access denied.", text_color="#E53935")
                 return
        
        self.is_downloading = True
        self.url_entry.configure(state="disabled")
        self.path_entry.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.action_button.configure(text="Stop Download", fg_color="#2A61AE", hover_color="#21618C")
        self.progress_bar.set(0)
        self.completed_videos = 0
        self.total_videos = 0
        
        self.log("\n--- STARTING NEW DOWNLOAD ---", color="orange")
        self.log("Starting video count...")
        self.status_label.configure(text="Step 1/2: Counting total videos...", text_color="orange")

        Thread(target=self.pre_download_check, args=(url, output_dir), daemon=True).start()


    def stop_download(self):
        """Stops the active download subprocess."""
        if self.download_process and self.download_process.poll() is None:
            self.log("Sending termination signal to yt-dlp process...", color="red")
            
            if platform.system() == "Windows":
                self.download_process.terminate()
            else:
                self.download_process.kill() 
            
            time.sleep(0.5) 

            self.log("Download stopped by user.", color="red")
            self.reset_state()
        else:
            self.log("No active download process to stop.", color="orange")
            self.reset_state()


    def reset_state(self):
        """Resets all UI and state variables after download completion or stop."""
        self.is_downloading = False
        self.download_process = None
        self.total_videos = 0
        self.completed_videos = 0
        
        self.url_entry.configure(state="normal")
        self.path_entry.configure(state="normal")
        self.browse_button.configure(state="normal")
        self.action_button.configure(text="Start Download", fg_color="#E53935", hover_color="#C62828")
        self.progress_bar.set(0)
        self.status_label.configure(text="Ready. Enter a channel or playlist URL.", text_color="gray")


    def pre_download_check(self, url, output_dir):
        """Runs yt-dlp with --flat-playlist to count total videos."""
        try:
            count_command = ["yt-dlp", "--flat-playlist", "--get-id", url]
            
            process = subprocess.run(
                count_command,
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8',
                errors='ignore'
            )
            
            video_ids = [line.strip() for line in process.stdout.split('\n') if line.strip()]
            self.total_videos = len(video_ids)
            
            if self.total_videos == 0:
                error_message = f"Could not find any videos or playlist is invalid. Error output:\n{process.stderr}"
                self.log(f"ERROR: {error_message}", color="red")
                self.reset_state()
                return

            self.log(f"Total videos found: {self.total_videos}. Starting download...")
            self.status_label.configure(text=f"Step 2/2: Found {self.total_videos} videos. Downloading...", text_color="green")
            
            self.download_videos(url, output_dir)

        except FileNotFoundError:
            self.log("FATAL ERROR: 'yt-dlp' executable not found. Please ensure it is installed and in your system PATH.", color="red")
            self.reset_state()
        except Exception as e:
            self.log(f"An unexpected error occurred during pre-check: {e}", color="red")
            self.reset_state()


    def download_videos(self, url, output_dir):
        """Runs the main yt-dlp download command in a streaming process."""
        try:
            command = [
                "yt-dlp",
                "--ignore-errors",
                "-o", os.path.join(output_dir, '%(uploader)s', '%(title)s.%(ext)s'),
                "--progress",
                "--newline",
                url
            ]
            
            self.log(f"Executing: {' '.join(command)}")

            self.download_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in self.download_process.stdout:
                line = line.strip()
                if line:
                    self.log(line)
                    
                    if "[download] Destination:" in line and "has finished" in line:
                        self.completed_videos += 1
                        self.update_overall_progress()

            return_code = self.download_process.wait()

            if return_code == 0:
                final_status = "Download COMPLETE! All videos processed successfully."
                self.log(final_status, color="green")
                self.progress_bar.set(1)
            else:
                final_status = f"Download FINISHED with ERRORS (Code: {return_code}). Check log for failed videos."
                self.log(final_status, color="red")
                
        except Exception as e:
            if self.is_downloading:
                self.log(f"An unexpected error occurred during download: {e}", color="red")
        finally:
            self.reset_state()
            

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
