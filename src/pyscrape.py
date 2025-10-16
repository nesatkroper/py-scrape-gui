#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox
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
        self.geometry("800x600")
        self.scraping_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()
        self.error_logs = []
        self.after(100, self.process_queue)
        self.build_ui()

    def build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill="x", pady=10)
        ttk.Label(url_frame, text="Enter URL to scrape", font=("Helvetica", 12)).pack(
            side="left", padx=5
        )
        self.url_entry = ttk.Entry(url_frame, width=50, font=("Helvetica", 10))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)

        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill="x", pady=10)
        ttk.Label(save_frame, text="Save location", font=("Helvetica", 12)).pack(
            side="left", padx=5
        )
        self.save_path = tk.StringVar(value=os.getcwd())
        ttk.Entry(
            save_frame, textvariable=self.save_path, width=40, font=("Helvetica", 10)
        ).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(
            save_frame, text="Browse", command=self.browse_save, style="primary.TButton"
        ).pack(side="left", padx=5)
        ttk.Button(
            save_frame,
            text="New Dir",
            command=self.create_new_dir,
            style="secondary.TButton",
        ).pack(side="left", padx=5)

        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill="x", pady=10)
        ttk.Label(
            name_frame, text="Custom result name (optional)", font=("Helvetica", 12)
        ).pack(side="left", padx=5)
        self.custom_name = ttk.Entry(name_frame, width=30, font=("Helvetica", 10))
        self.custom_name.pack(side="left", fill="x", expand=True, padx=5)

        options_frame = ttk.LabelFrame(main_frame, text="Scraping Options", padding=10)
        options_frame.pack(fill="x", pady=10)
        self.options = {}
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
        self.check_all_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Check All",
            variable=self.check_all_var,
            command=self.toggle_check_all,
            style="info.TCheckbutton",
        ).pack(anchor="w", pady=2)
        for opt in opts:
            self.options[opt] = tk.BooleanVar()
            ttk.Checkbutton(
                options_frame,
                text=opt,
                variable=self.options[opt],
                style="info.TCheckbutton",
            ).pack(anchor="w", pady=2)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=10)
        self.start_btn = ttk.Button(
            control_frame,
            text="Start",
            command=self.start_scraping,
            style="success.TButton",
        )
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop",
            command=self.stop_scraping,
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

        self.progress = ttk.Progressbar(
            main_frame, mode="indeterminate", style="success.TProgressbar"
        )
        self.progress.pack(fill="x", pady=10)

        self.log_text = ttk.Text(main_frame, height=10, font=("Helvetica", 10))
        self.log_text.pack(fill="both", expand=True, pady=10)

        ttk.Label(main_frame, text="Files downloaded:", font=("Helvetica", 12)).pack(
            anchor="w", pady=5
        )
        self.file_count = tk.IntVar(value=0)
        ttk.Label(
            main_frame, textvariable=self.file_count, font=("Helvetica", 12)
        ).pack(anchor="w", pady=5)

    def browse_save(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path.set(path)

    def create_new_dir(self):
        new_dir = tk.simpledialog.askstring(
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
        folder_name = custom if custom else domain
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
                    if "Error" in msg[1] or "Failed" in msg[1]:
                        self.error_logs.append(msg[1].strip())
                elif msg[0] == "inc_count":
                    self.file_count.set(self.file_count.get() + msg[1])
                elif msg[0] == "done":
                    self.progress.stop()
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    if self.scraping_thread:
                        self.scraping_thread.join()
                        self.scraping_thread = None
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def scrape(self, start_url, base_path, images_path, videos_path):
        options = {k: v.get() for k, v in self.options.items()}

        to_visit = collections.deque([(start_url, 0)])
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
            self.log_queue.put(("log", f"Scraping {url} (depth {current_depth})\n"))

            try:
                resp = requests.get(url, timeout=10, headers=headers)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                page_data = {"url": url}

                if options["Extract metadata (title, description, keywords)"]:
                    try:
                        title = (
                            soup.title.string.strip()
                            if soup.title and soup.title.string
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
                    except (AttributeError, TypeError) as e:
                        error_msg = f"Error extracting metadata from {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)
                        page_data["title"] = ""
                        page_data["description"] = ""
                        page_data["keywords"] = ""

                if options["Extract text content"]:
                    try:
                        text = soup.get_text(separator="\n", strip=True)
                        page_data["text"] = text
                    except Exception as e:
                        error_msg = f"Error extracting text from {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)
                        page_data["text"] = ""

                if options["Extract all URLs from <a> tags"]:
                    try:
                        links = [
                            urljoin(url, a["href"])
                            for a in soup.find_all("a", href=True)
                        ]
                        page_data["links"] = links
                    except Exception as e:
                        error_msg = f"Error extracting links from {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)
                        page_data["links"] = []

                if options["Download all images from <img> tags"]:
                    imgs = soup.find_all("img", src=True)
                    for img in imgs:
                        img_url = urljoin(url, img["src"])
                        try:
                            if not img_url or not any(
                                img_url.lower().endswith(ext)
                                for ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp")
                            ):
                                error_msg = f"Skipping invalid image URL {img_url}"
                                self.log_queue.put(("log", error_msg + "\n"))
                                self.error_logs.append(error_msg)
                                continue
                            img_resp = requests.get(img_url, timeout=5, headers=headers)
                            img_resp.raise_for_status()
                            img_path = urlparse(img_url).path
                            filename = os.path.basename(img_path)
                            if not filename or os.path.isdir(
                                os.path.join(images_path, filename)
                            ):
                                filename = f"image_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg"
                            full_path = os.path.join(images_path, filename)
                            if os.path.isdir(full_path):
                                error_msg = f"Cannot save image to {full_path}: Path is a directory"
                                self.log_queue.put(("log", error_msg + "\n"))
                                self.error_logs.append(error_msg)
                                continue
                            with open(full_path, "wb") as f:
                                f.write(img_resp.content)
                            self.log_queue.put(
                                ("log", f"Downloaded {img_url} to {full_path}\n")
                            )
                            self.log_queue.put(("inc_count", 1))
                        except (requests.exceptions.RequestException, OSError) as e:
                            error_msg = f"Error downloading {img_url}: {str(e)}"
                            self.log_queue.put(("log", error_msg + "\n"))
                            self.error_logs.append(error_msg)

                if options["Download all videos from <video> tags"]:
                    videos = soup.find_all("video")
                    for video in videos:
                        # Look for source tags inside video
                        sources = video.find_all("source", src=True)
                        if sources:
                            for source in sources:
                                video_url = urljoin(url, source["src"])
                                self.download_video(video_url, videos_path, headers)
                        elif video.get("src"):
                            video_url = urljoin(url, video["src"])
                            self.download_video(video_url, videos_path, headers)

                if options["Save raw HTML"]:
                    try:
                        path_parts = urlparse(url).path.strip("/").replace("/", "_")
                        html_filename = f"{path_parts or 'index'}.html"
                        html_path = os.path.join(base_path, html_filename)
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(resp.text)
                        self.log_queue.put(("log", f"Saved HTML to {html_path}\n"))
                        self.log_queue.put(("inc_count", 1))
                    except OSError as e:
                        error_msg = f"Error saving HTML for {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)

                data.append(page_data)

                if (
                    options["Follow internal links (recursive scraping)"]
                    or options["Follow external links"]
                ):
                    try:
                        links = [
                            urljoin(url, a["href"])
                            for a in soup.find_all("a", href=True)
                        ]
                        for link in links:
                            parsed_link = urlparse(link)
                            if parsed_link.scheme not in ("http", "https"):
                                continue
                            is_internal = (
                                parsed_link.netloc == urlparse(start_url).netloc
                            )
                            if (
                                is_internal
                                and options[
                                    "Follow internal links (recursive scraping)"
                                ]
                            ) or (not is_internal and options["Follow external links"]):
                                if link not in visited:
                                    to_visit.append((link, current_depth + 1))
                    except Exception as e:
                        error_msg = f"Error processing links for {url}: {str(e)}"
                        self.log_queue.put(("log", error_msg + "\n"))
                        self.error_logs.append(error_msg)

            except requests.exceptions.RequestException as e:
                error_msg = f"Error scraping {url}: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)

        if options["Save as JSON"] and data and not self.stop_event.is_set():
            try:
                json_path = os.path.join(base_path, "data.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                self.log_queue.put(("log", f"Saved JSON to {json_path}\n"))
                self.log_queue.put(("inc_count", 1))
            except (OSError, TypeError) as e:
                error_msg = f"Error saving JSON to {json_path}: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)

        if options["Save as CSV"] and data and not self.stop_event.is_set():
            try:
                fields = set()
                for d in data:
                    fields.update(d.keys())
                fields = sorted(fields)
                csv_path = os.path.join(base_path, "data.csv")
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(data)
                self.log_queue.put(("log", f"Saved CSV to {csv_path}\n"))
                self.log_queue.put(("inc_count", 1))
            except (OSError, TypeError) as e:
                error_msg = f"Error saving CSV to {csv_path}: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)

        self.log_queue.put(("log", "Scraping completed.\n"))
        self.log_queue.put(("done",))

    def download_video(self, video_url, videos_path, headers):
        try:
            if not video_url or not any(
                video_url.lower().endswith(ext)
                for ext in (".mp4", ".webm", ".ogg", ".mov", ".avi")
            ):
                error_msg = f"Skipping invalid video URL {video_url}"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)
                return
            video_resp = requests.get(
                video_url, timeout=10, headers=headers, stream=True
            )
            video_resp.raise_for_status()
            video_path = urlparse(video_url).path
            filename = os.path.basename(video_path)
            if not filename or os.path.isdir(os.path.join(videos_path, filename)):
                filename = f"video_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.mp4"
            full_path = os.path.join(videos_path, filename)
            if os.path.isdir(full_path):
                error_msg = f"Cannot save video to {full_path}: Path is a directory"
                self.log_queue.put(("log", error_msg + "\n"))
                self.error_logs.append(error_msg)
                return
            with open(full_path, "wb") as f:
                for chunk in video_resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.log_queue.put(("log", f"Downloaded {video_url} to {full_path}\n"))
            self.log_queue.put(("inc_count", 1))
        except (requests.exceptions.RequestException, OSError) as e:
            error_msg = f"Error downloading {video_url}: {str(e)}"
            self.log_queue.put(("log", error_msg + "\n"))
            self.error_logs.append(error_msg)


if __name__ == "__main__":
    app = ScraperApp()
    app.mainloop()
