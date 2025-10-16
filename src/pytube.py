import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os
import json
import csv
import threading
import queue
from datetime import datetime
import collections
import pyperclip


class ScraperApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Web Scraper")
        # Increased initial size to better accommodate the tabbed design
        self.geometry("700x500")
        self.scraping_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.error_logs = []
        # The file count is now an attribute initialized in build_status_tab
        self.file_count = tk.IntVar(value=0)
        self.after(100, self.process_queue)
        self.build_ui()

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # 1. Create a Notebook widget for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)

        # 2. Create the three main tabs (frames)
        self.setup_tab = ttk.Frame(self.notebook, padding=15)
        self.options_tab = ttk.Frame(self.notebook, padding=15)
        self.status_tab = ttk.Frame(self.notebook, padding=15)

        # 3. Add the tabs to the notebook
        self.notebook.add(self.setup_tab, text="🌐 Setup & Control")
        self.notebook.add(self.options_tab, text="⚙️ Scraping Options")
        self.notebook.add(self.status_tab, text="📊 Status & Logs")

        # Build the content for each tab
        self.build_setup_tab()
        self.build_options_tab()
        self.build_status_tab()

    def build_setup_tab(self):
        # --- URL Frame ---
        url_frame = ttk.LabelFrame(self.setup_tab, text="Target URL", padding=15)
        url_frame.pack(fill="x", pady=10)
        ttk.Label(url_frame, text="URL:", font=("Helvetica", 14, "bold")).pack(
            side="left", padx=5
        )
        self.url_entry = ttk.Entry(url_frame, width=50, font=("Helvetica", 12))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10)

        # --- Save Location Frame ---
        save_frame = ttk.LabelFrame(self.setup_tab, text="Save Location", padding=15)
        save_frame.pack(fill="x", pady=20)
        ttk.Label(save_frame, text="Path:", font=("Helvetica", 14, "bold")).pack(
            side="left", padx=5
        )
        self.save_path = tk.StringVar(value=os.getcwd())
        ttk.Entry(
            save_frame, textvariable=self.save_path, width=40, font=("Helvetica", 12)
        ).pack(side="left", fill="x", expand=True, padx=10)
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
            self.setup_tab, text="Output Folder Name", padding=15
        )
        name_frame.pack(fill="x", pady=20)
        ttk.Label(
            name_frame, text="Custom Name (optional):", font=("Helvetica", 14, "bold")
        ).pack(side="left", padx=5)
        self.custom_name = ttk.Entry(name_frame, width=30, font=("Helvetica", 12))
        self.custom_name.pack(side="left", fill="x", expand=True, padx=10)

        # --- Control Frame ---
        control_frame = ttk.Frame(self.setup_tab)
        control_frame.pack(fill="x", pady=40)
        self.start_btn = ttk.Button(
            control_frame,
            text="▶ Start Scraping",
            command=self.start_scraping,
            bootstyle="success.outline",
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=10)
        self.stop_btn = ttk.Button(
            control_frame,
            text="■ Stop Scraping",
            command=self.stop_scraping,
            bootstyle="danger.outline",
            state="disabled",
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=10)

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

        # Frame for 'Check All'
        top_options_frame = ttk.LabelFrame(
            self.options_tab, text="Global Options", padding=10
        )
        top_options_frame.pack(fill="x", pady=5)

        self.check_all_var = tk.BooleanVar()
        ttk.Checkbutton(
            top_options_frame,
            text="Check All / Uncheck All",
            variable=self.check_all_var,
            command=self.toggle_check_all,
            bootstyle="info-round-toggle",
        ).pack(anchor="w", pady=5, padx=5)

        # Use Columns for better layout of the main options
        content_opts_frame = ttk.Frame(self.options_tab)
        content_opts_frame.pack(fill="both", expand=True, pady=10)

        # Column 1: Data & Files
        col1 = ttk.LabelFrame(content_opts_frame, text="Content Extraction", padding=15)
        col1.pack(side="left", fill="both", expand=True, padx=10)

        # Column 2: Recursion & Format
        col2 = ttk.LabelFrame(
            content_opts_frame, text="Linking & Output Format", padding=15
        )
        col2.pack(side="left", fill="both", expand=True, padx=10)

        for i, opt in enumerate(opts):
            self.options[opt] = tk.BooleanVar()
            checkbutton = ttk.Checkbutton(
                text=opt,
                variable=self.options[opt],
                bootstyle="primary-round-toggle",
            )
            if i < 5:  # Put first 5 in column 1 (Data & Files)
                checkbutton.pack(in_=col1, anchor="w", pady=5, padx=5)
            else:  # Put remaining 5 in column 2 (Recursion & Format)
                checkbutton.pack(in_=col2, anchor="w", pady=5, padx=5)

    def build_status_tab(self):
        # --- Progress & File Count ---
        status_frame = ttk.LabelFrame(
            self.status_tab, text="Scraping Status", padding=15
        )
        status_frame.pack(fill="x", pady=10)

        # Progressbar
        ttk.Label(
            status_frame, text="Activity Progress:", font=("Helvetica", 12, "bold")
        ).pack(anchor="w", pady=5)
        self.progress = ttk.Progressbar(
            status_frame, mode="indeterminate", bootstyle="success-striped"
        )
        self.progress.pack(fill="x", pady=10)

        # File Count
        count_frame = ttk.Frame(status_frame)
        count_frame.pack(fill="x")
        ttk.Label(
            count_frame, text="Total Files Saved:", font=("Helvetica", 12, "bold")
        ).pack(side="left", anchor="w", pady=5, padx=(0, 10))
        # self.file_count is initialized in __init__
        ttk.Label(
            count_frame,
            textvariable=self.file_count,
            font=("Helvetica", 14, "bold", "italic"),
            bootstyle="primary",
        ).pack(side="left", anchor="w", pady=5)

        # --- Log & Error Frame ---
        log_frame = ttk.LabelFrame(self.status_tab, text="Execution Log", padding=15)
        log_frame.pack(fill="both", expand=True, pady=15)

        # Text widget and Scrollbar
        log_scroll = ttk.Scrollbar(log_frame, orient=VERTICAL)
        self.log_text = ttk.Text(
            log_frame, height=10, font=("Courier", 10), yscrollcommand=log_scroll.set
        )

        log_scroll.config(command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Copy Errors Button
        ttk.Button(
            log_frame,
            text="Copy Errors to Clipboard",
            command=self.copy_errors,
            bootstyle="warning",
        ).pack(
            fill="x", pady=(10, 0)
        )  # Placed under the log

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
                error_msg = f"Failed to create directory: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)
                messagebox.showerror("Error", error_msg)

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
            error_msg = "Invalid URL format"
            self.log_queue.put(("log", error_msg + "\n"))
            self.error_logs.append(error_msg)
            messagebox.showerror("Error", error_msg)
            return

        custom = self.custom_name.get().strip()
        folder_name = custom if custom else domain.replace("www.", "")
        base_path = os.path.join(self.save_path.get(), folder_name)
        try:
            os.makedirs(base_path, exist_ok=True)
        except OSError as e:
            error_msg = f"Failed to create base directory {base_path}: {str(e)}"
            self.log_queue.put(("log", error_msg + "\n"))
            self.error_logs.append(error_msg)
            messagebox.showerror("Error", error_msg)
            return

        images_path = os.path.join(base_path, "images")
        if self.options["Download all images from <img> tags"].get():
            try:
                os.makedirs(images_path, exist_ok=True)
            except OSError as e:
                error_msg = f"Failed to create images directory {images_path}: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)
                messagebox.showerror("Error", error_msg)
                return

        videos_path = os.path.join(base_path, "videos")
        if self.options["Download all videos from <video> tags"].get():
            try:
                os.makedirs(videos_path, exist_ok=True)
            except OSError as e:
                error_msg = f"Failed to create videos directory {videos_path}: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)
                messagebox.showerror("Error", error_msg)
                return

        self.stop_event.clear()
        self.error_logs = []
        self.scraping_thread = threading.Thread(
            target=self.scrape, args=(url, base_path, images_path, videos_path)
        )
        self.scraping_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start()
        self.file_count.set(0)
        self.log_text.delete(1.0, tk.END)
        self.log_queue.put(("log", "Starting scraping...\n"))
        # Switch to the Status tab automatically
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
                        # Add a visual highlight for errors
                        self.log_text.tag_config("error", foreground="#dc3545")
                        self.log_text.tag_add("error", "end-2l", "end-1c")
                        self.error_logs.append(msg[1].strip())
                elif msg[0] == "inc_count":
                    self.file_count.set(self.file_count.get() + msg[1])
                elif msg[0] == "done":
                    self.progress.stop()
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    # Ensure the thread is properly joined
                    if self.scraping_thread and self.scraping_thread.is_alive():
                        self.scraping_thread.join()
                        self.scraping_thread = None
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def scrape(self, start_url, base_path, images_path, videos_path):
        options = {k: v.get() for k, v in self.options.items()}

        to_visit = collections.deque([(start_url, 0)])
        # Use (URL, current_depth) in visited to allow revisiting at different depths if necessary, but here we keep it simple with just URL
        visited = set()
        data = []
        max_depth = 3
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        while to_visit and not self.stop_event.is_set():
            url, current_depth = to_visit.popleft()
            if url in visited or current_depth > max_depth:
                continue
            visited.add(url)
            self.log_queue.put(("log", f"Scraping {url} (depth {current_depth})...\n"))

            try:
                # Set a shorter timeout for large recursive scrapes
                resp = requests.get(url, timeout=15, headers=headers)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                page_data = {"url": url}

                # --- 1. Extract Metadata ---
                if options["Extract metadata (title, description, keywords)"]:
                    try:
                        title = (
                            soup.find("title").string.strip()
                            if soup.find("title") and soup.find("title").string
                            else ""
                        )
                        desc_tag = soup.find("meta", attrs={"name": "description"})
                        desc = (
                            desc_tag["content"].strip()
                            if desc_tag and desc_tag.get("content")
                            else ""
                        )
                        keys_tag = soup.find("meta", attrs={"name": "keywords"})
                        keys = (
                            keys_tag["content"].strip()
                            if keys_tag and keys_tag.get("content")
                            else ""
                        )
                        page_data["title"] = title
                        page_data["description"] = desc
                        page_data["keywords"] = keys
                    except Exception as e:
                        error_msg = f"Error extracting metadata from {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)
                        page_data.update(
                            {"title": "", "description": "", "keywords": ""}
                        )

                # --- 2. Extract Text Content ---
                if options["Extract text content"]:
                    try:
                        # Improved text extraction to remove script/style tags
                        for script_or_style in soup(["script", "style"]):
                            script_or_style.extract()
                        text = soup.get_text(separator="\n", strip=True)
                        page_data["text"] = text
                    except Exception as e:
                        error_msg = f"Error extracting text from {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)
                        page_data["text"] = ""

                # --- 3. Extract Links ---
                if options["Extract all URLs from <a> tags"]:
                    try:
                        links = [
                            urljoin(url, a["href"])
                            for a in soup.find_all("a", href=True)
                            # Basic filtering of non-HTTP/HTTPS links
                            if urlparse(urljoin(url, a["href"])).scheme
                            in ("http", "https")
                        ]
                        page_data["links"] = links
                    except Exception as e:
                        error_msg = f"Error extracting links from {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)
                        page_data["links"] = []

                # --- 4. Download Images ---
                if options["Download all images from <img> tags"]:
                    imgs = soup.find_all("img", src=True)
                    for img in imgs:
                        img_url = urljoin(url, img["src"])
                        self.download_file(img_url, images_path, "image", headers)

                # --- 5. Download Videos ---
                if options["Download all videos from <video> tags"]:
                    videos = soup.find_all("video")
                    for video in videos:
                        sources = video.find_all("source", src=True)
                        if sources:
                            for source in sources:
                                self.download_file(
                                    urljoin(url, source["src"]),
                                    videos_path,
                                    "video",
                                    headers,
                                )
                        elif video.get("src"):
                            self.download_file(
                                urljoin(url, video["src"]),
                                videos_path,
                                "video",
                                headers,
                            )

                # --- 6. Save Raw HTML ---
                if options["Save raw HTML"]:
                    try:
                        # Create a clean filename from the URL path
                        path_parts = urlparse(url).path.strip("/").replace("/", "_")
                        # If path is empty (homepage), use 'index'
                        html_filename = f"{path_parts or 'index'}_{datetime.now().strftime('%H%M%S')}.html"
                        html_path = os.path.join(base_path, html_filename)
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(resp.text)
                        self.log_queue.put(("log", f"Saved HTML to {html_filename}\n"))
                        self.log_queue.put(("inc_count", 1))
                    except OSError as e:
                        error_msg = f"Error saving HTML for {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)

                data.append(page_data)

                # --- 7. Recursive / External Linking ---
                if (
                    options["Follow internal links (recursive scraping)"]
                    or options["Follow external links"]
                ):
                    for link in page_data.get("links", []):
                        parsed_link = urlparse(link)
                        # Skip fragment links and links outside http/https (already filtered, but good to check)
                        if not parsed_link.netloc or parsed_link.scheme not in (
                            "http",
                            "https",
                        ):
                            continue

                        # Check if the link is internal (same netloc)
                        is_internal = parsed_link.netloc == urlparse(start_url).netloc

                        if (
                            is_internal
                            and options["Follow internal links (recursive scraping)"]
                        ) or (not is_internal and options["Follow external links"]):
                            if link not in visited and current_depth + 1 <= max_depth:
                                to_visit.append((link, current_depth + 1))

            except requests.exceptions.RequestException as e:
                error_msg = f"Error scraping {url}: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)

        # --- 8. Save Final JSON/CSV ---
        if data and not self.stop_event.is_set():
            if options["Save as JSON"]:
                try:
                    json_path = os.path.join(base_path, "data.json")
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    self.log_queue.put(("log", f"Saved JSON to data.json\n"))
                    self.log_queue.put(("inc_count", 1))
                except (OSError, TypeError) as e:
                    error_msg = f"Error saving JSON: {str(e)}"
                    self.log_queue.put(("log", error_msg + "\n"))
                    self.error_logs.append(error_msg)

            if options["Save as CSV"]:
                try:
                    fields = set()
                    for d in data:
                        # Handle list type fields (like 'links') for CSV simplicity by skipping them
                        fields.update(
                            k for k, v in d.items() if not isinstance(v, list)
                        )
                    fields = sorted(fields)
                    csv_path = os.path.join(base_path, "data.csv")
                    with open(csv_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=fields)
                        writer.writeheader()
                        # Clean up data before writing to CSV
                        cleaned_data = [
                            {k: v for k, v in row.items() if k in fields}
                            for row in data
                        ]
                        writer.writerows(cleaned_data)
                    self.log_queue.put(("log", f"Saved CSV to data.csv\n"))
                    self.log_queue.put(("inc_count", 1))
                except (OSError, TypeError) as e:
                    error_msg = f"Error saving CSV: {str(e)}"
                    self.log_queue.put(("log", error_msg + "\n"))
                    self.error_logs.append(error_msg)

        self.log_queue.put(("log", "Scraping completed.\n"))
        self.log_queue.put(("done",))

    def download_file(self, file_url, save_path, file_type, headers):
        """Generic method to download a file (image or video) and handle errors."""

        # Check for stop signal before initiating download
        if self.stop_event.is_set():
            return

        allowed_extensions = {
            "image": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"),
            "video": (".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv"),
        }

        try:
            # Check for valid URL and file extension
            if not file_url or not any(
                file_url.lower().endswith(ext)
                for ext in allowed_extensions.get(file_type, ())
            ):
                error_msg = f"Skipping invalid {file_type.upper()} URL: {file_url}"
                self.log_queue.put(("log", error_msg + "\n"))
                return

            # Request the file
            timeout = 10 if file_type == "video" else 5
            # Use stream=True for potentially large files (videos/images)
            resp = requests.get(file_url, timeout=timeout, headers=headers, stream=True)
            resp.raise_for_status()

            # Determine filename
            url_path = urlparse(file_url).path
            filename = os.path.basename(url_path)

            # Fallback/default filename if path is empty or invalid
            if not filename or os.path.isdir(os.path.join(save_path, filename)):
                # Use a unique timestamp for a filename
                ext = next(
                    (
                        ext
                        for ext in allowed_extensions.get(file_type, ())
                        if file_url.lower().endswith(ext)
                    ),
                    f".{file_type}",
                )
                filename = (
                    f"{file_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
                )

            full_path = os.path.join(save_path, filename)

            # Save the file in chunks
            with open(full_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.log_queue.put(("log", f"Downloaded {file_type} {filename}\n"))
            self.log_queue.put(("inc_count", 1))

        except (requests.exceptions.RequestException, OSError, ValueError) as e:
            error_msg = f"Error downloading {file_type} {file_url}: {str(e)}"
            self.log_queue.put(("log", error_msg + "\n"))


if __name__ == "__main__":
    app = ScraperApp()
    app.mainloop()
