# scraper_ui.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import queue
import collections
import pyperclip
from urllib.parse import urlparse
import threading

# Import the core logic
from scraper_core import ScraperCore


class ScraperApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        # Set minimal size and center the window
        self.width = 700
        self.height = 550
        self.center_window()

        self.title("Minimal Web Scraper")
        self.scraping_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.error_logs = []
        self.file_count = tk.IntVar(value=0)
        self.after(100, self.process_queue)
        self.build_ui()

    def center_window(self):
        """Calculates and sets the window to the center of the screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")
        self.resizable(False, False)  # Keep it minimal and fixed

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=5)

        self.setup_tab = ttk.Frame(self.notebook, padding=15)
        self.options_tab = ttk.Frame(self.notebook, padding=15)
        self.status_tab = ttk.Frame(self.notebook, padding=15)

        self.notebook.add(self.setup_tab, text="🌐 Setup")
        self.notebook.add(self.options_tab, text="⚙️ Options")
        self.notebook.add(self.status_tab, text="📊 Status")

        self.build_setup_tab()
        self.build_options_tab()
        self.build_status_tab()

    def build_setup_tab(self):
        # --- URL Frame ---
        url_frame = ttk.LabelFrame(self.setup_tab, text="Target URL", padding=10)
        url_frame.pack(fill="x", pady=10)
        ttk.Label(url_frame, text="URL:", font=("Helvetica", 11, "bold")).pack(
            side="left", padx=5
        )
        self.url_entry = ttk.Entry(url_frame, font=("Helvetica", 10))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)

        # --- Save Location Frame ---
        save_frame = ttk.LabelFrame(self.setup_tab, text="Save Location", padding=10)
        save_frame.pack(fill="x", pady=10)
        ttk.Label(save_frame, text="Path:", font=("Helvetica", 11, "bold")).pack(
            side="left", padx=5
        )
        self.save_path = tk.StringVar(value=os.getcwd())
        ttk.Entry(save_frame, textvariable=self.save_path, font=("Helvetica", 10)).pack(
            side="left", fill="x", expand=True, padx=5
        )
        ttk.Button(
            save_frame, text="Browse", command=self.browse_save, bootstyle="primary"
        ).pack(side="left", padx=5)
        ttk.Button(
            save_frame,
            text="New Dir",
            command=self.create_new_dir,
            bootstyle="secondary",
        ).pack(side="left", padx=5)

        # --- Custom Name Frame ---
        name_frame = ttk.LabelFrame(
            self.setup_tab, text="Output Folder Name", padding=10
        )
        name_frame.pack(fill="x", pady=10)
        ttk.Label(name_frame, text="Custom Name:", font=("Helvetica", 11, "bold")).pack(
            side="left", padx=5
        )
        self.custom_name = ttk.Entry(name_frame, font=("Helvetica", 10))
        self.custom_name.pack(side="left", fill="x", expand=True, padx=5)

        # --- Control Frame ---
        control_frame = ttk.Frame(self.setup_tab)
        control_frame.pack(fill="x", pady=20)
        self.start_btn = ttk.Button(
            control_frame,
            text="▶ Start",
            command=self.start_scraping,
            bootstyle="success.outline",
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=5)
        self.stop_btn = ttk.Button(
            control_frame,
            text="■ Stop",
            command=self.stop_scraping,
            bootstyle="danger.outline",
            state="disabled",
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=5)

    def build_options_tab(self):
        opts = [
            "Extract all URLs from <a> tags",
            "Download all images from <img> tags",
            "Download all videos from <video> tags",
            "Extract text content",
            "Extract metadata (title, description, keywords)",
            "Follow internal links (recursive scraping)",
            "Follow external links",
            "Save as JSON",
            "Save as CSV",
            "Save raw HTML",
        ]
        self.options = {}

        # Top Frame for 'Check All'
        top_options_frame = ttk.Frame(self.options_tab)
        top_options_frame.pack(fill="x", pady=5)
        self.check_all_var = tk.BooleanVar()
        ttk.Checkbutton(
            top_options_frame,
            text="Check/Uncheck All",
            variable=self.check_all_var,
            command=self.toggle_check_all,
            bootstyle="info-round-toggle",
        ).pack(anchor="w", pady=5)

        # Two-column layout
        content_opts_frame = ttk.Frame(self.options_tab)
        content_opts_frame.pack(fill="both", expand=True, pady=5)

        col1 = ttk.LabelFrame(content_opts_frame, text="Content", padding=10)
        col1.pack(side="left", fill="both", expand=True, padx=5)
        col2 = ttk.LabelFrame(content_opts_frame, text="Recursion & Output", padding=10)
        col2.pack(side="left", fill="both", expand=True, padx=5)

        for i, opt in enumerate(opts):
            self.options[opt] = tk.BooleanVar()
            checkbutton = ttk.Checkbutton(
                text=opt, variable=self.options[opt], bootstyle="primary-round-toggle"
            )
            target_col = col1 if i < 5 else col2
            checkbutton.pack(in_=target_col, anchor="w", pady=3, padx=5)

    def build_status_tab(self):
        # --- Progress & File Count ---
        # status_frame = ttk.LabelFrame(self.status_tab, text="Status", padding=10)
        # status_frame.pack(fill="x", pady=5)

        # ttk.Label(status_frame, text="Progress:", font=("Helvetica", 10, "bold")).pack(
        #     anchor="w", pady=2
        # )
        # self.progress = ttk.Progressbar(
        #     status_frame, mode="indeterminate", bootstyle="success-striped"
        # )
        # self.progress.pack(fill="x", pady=5)

        status_frame = ttk.LabelFrame(self.status_tab, text="Status", padding=10)
        status_frame.pack(fill="x", pady=5)

        ttk.Label(status_frame, text="Progress:", font=("Helvetica", 10, "bold")).pack(
            anchor="w", pady=2
        )

        self.progress = ttk.Progressbar(
            status_frame,
            mode="indeterminate",
            bootstyle="info-striped",
        )
        self.progress.pack(fill="x", pady=5)

        count_frame = ttk.Frame(status_frame)
        count_frame.pack(fill="x")
        ttk.Label(
            count_frame, text="Files Saved:", font=("Helvetica", 10, "bold")
        ).pack(side="left", anchor="w", padx=(0, 10))
        ttk.Label(
            count_frame,
            textvariable=self.file_count,
            font=("Helvetica", 12, "bold", "italic"),
            bootstyle="primary",
        ).pack(side="left", anchor="w")

        # --- Log & Error Frame ---
        log_frame = ttk.LabelFrame(self.status_tab, text="Execution Log", padding=10)
        log_frame.pack(fill="both", expand=True, pady=10)

        text_container = ttk.Frame(log_frame)
        text_container.pack(fill="both", expand=True)

        log_scroll = ttk.Scrollbar(text_container, orient=VERTICAL)
        self.log_text = ttk.Text(
            text_container, height=7, font=("Courier", 9), yscrollcommand=log_scroll.set
        )

        log_scroll.config(command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        ttk.Button(
            log_frame, text="Copy Errors", command=self.copy_errors, bootstyle="warning"
        ).pack(fill="x", pady=(5, 0))

    # --- UI Utility Methods ---
    def browse_save(self):
        path = filedialog.askdirectory()
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
            except OSError as e:
                messagebox.showerror("Error", f"Failed to create directory: {str(e)}")

    def toggle_check_all(self):
        state = self.check_all_var.get()
        for var in self.options.values():
            var.set(state)

    def copy_errors(self):
        if self.error_logs:
            pyperclip.copy("\n".join(self.error_logs))
            messagebox.showinfo("Success", "Error messages copied to clipboard")
        else:
            messagebox.showinfo("Info", "No error messages to copy")

    # --- Threading/Queue Methods ---
    def start_scraping(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Enter a URL")
            return

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError
            domain = parsed.netloc
        except ValueError:
            messagebox.showerror("Error", "Invalid URL format")
            return

        # Setup paths and folders (Moved to UI to handle immediate file system errors)
        custom = self.custom_name.get().strip()
        folder_name = custom if custom else domain.replace("www.", "")
        base_path = os.path.join(self.save_path.get(), folder_name)

        try:
            os.makedirs(base_path, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Error", f"Failed to create base directory: {str(e)}")
            return

        images_path = os.path.join(base_path, "images")
        videos_path = os.path.join(base_path, "videos")

        if self.options["Download all images from <img> tags"].get():
            os.makedirs(images_path, exist_ok=True)
        if self.options["Download all videos from <video> tags"].get():
            os.makedirs(videos_path, exist_ok=True)

        self.stop_event.clear()
        self.error_logs = []
        options_dict = {k: v.get() for k, v in self.options.items()}

        # Start the core scraping logic in a separate thread
        self.scraping_thread = ScraperCore(
            url,
            base_path,
            images_path,
            videos_path,
            options_dict,
            self.log_queue,
            self.stop_event,
        )
        self.scraping_thread.start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start()
        self.file_count.set(0)
        self.log_text.delete(1.0, tk.END)
        self.notebook.select(self.status_tab)

    def stop_scraping(self):
        self.stop_event.set()
        self.log_queue.put(("log", "Stopping...\n"))

    def process_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg[0] == "log":
                    self.log_text.insert(tk.END, msg[1])
                    self.log_text.see(tk.END)
                    if "Error" in msg[1] or "Failed" in msg[1] or "Skipping" in msg[1]:
                        self.log_text.tag_config("error", foreground="#dc3545")
                        self.log_text.tag_add("error", "end-2l", "end-1c")
                        self.error_logs.append(msg[1].strip())
                elif msg[0] == "inc_count":
                    self.file_count.set(self.file_count.get() + msg[1])
                elif msg[0] == "done":
                    self.progress.stop()
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    if self.scraping_thread and self.scraping_thread.is_alive():
                        self.scraping_thread.join()
                        self.scraping_thread = None
        except queue.Empty:
            pass
        self.after(100, self.process_queue)
