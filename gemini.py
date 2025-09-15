import tkinter as tk
from tkinter import filedialog, ttk
import requests
from bs4 import BeautifulSoup
import os
import threading
import json
import csv
from urllib.parse import urljoin, urlparse


class ScrapingThread(threading.Thread):
    """A thread to handle the web scraping logic."""

    def __init__(self, app, url, options, save_path):
        super().__init__()
        self.app = app
        self.url = url
        self.options = options
        self.save_path = save_path
        self._stop_event = threading.Event()
        self.scraped_urls = set()
        self.file_count = 0

    def run(self):
        """Main scraping loop."""
        self.app.log("Starting scraping process...")
        self.scrape(self.url)
        self.app.log("Scraping finished.")
        self.app.update_progress(100)
        self.app.stop_button.config(state=tk.DISABLED)
        self.app.start_button.config(state=tk.NORMAL)

    def stop(self):
        """Stops the scraping process."""
        self._stop_event.set()

    def is_stopped(self):
        """Checks if the thread is stopped."""
        return self._stop_event.is_set()

    def scrape(self, url):
        """Performs the scraping for a single URL."""
        if self.is_stopped() or url in self.scraped_urls:
            return

        self.scraped_urls.add(url)
        self.app.log(f"Scraping: {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses
            soup = BeautifulSoup(response.text, "html.parser")

            # Create a folder for the domain if it doesn't exist
            domain_name = urlparse(url).netloc
            domain_folder = os.path.join(self.save_path, domain_name)
            os.makedirs(domain_folder, exist_ok=True)

            # Process content based on options
            data = {}
            if self.options["save_raw_html"]:
                with open(
                    os.path.join(domain_folder, "raw_html.html"), "w", encoding="utf-8"
                ) as f:
                    f.write(response.text)
                self.file_count += 1

            if self.options["extract_metadata"]:
                data["title"] = soup.title.string if soup.title else "No Title"
                data["description"] = (
                    soup.find("meta", attrs={"name": "description"})["content"]
                    if soup.find("meta", attrs={"name": "description"})
                    else "No Description"
                )
                data["keywords"] = (
                    soup.find("meta", attrs={"name": "keywords"})["content"]
                    if soup.find("meta", attrs={"name": "keywords"})
                    else "No Keywords"
                )
                self.app.log(f"Extracted metadata: {data['title']}")

            if self.options["extract_text_content"]:
                text_content = " ".join(p.text for p in soup.find_all("p"))
                data["text_content"] = text_content[:500] + "..."  # Truncate for log
                self.app.log(f"Extracted text content.")

            if self.options["download_images"]:
                images_folder = os.path.join(domain_folder, "images")
                os.makedirs(images_folder, exist_ok=True)
                for img in soup.find_all("img"):
                    img_url = urljoin(url, img.get("src"))
                    if img_url:
                        try:
                            img_response = requests.get(img_url, timeout=10)
                            img_name = os.path.basename(urlparse(img_url).path)
                            if not img_name:
                                img_name = "image.jpg"
                            with open(os.path.join(images_folder, img_name), "wb") as f:
                                f.write(img_response.content)
                            self.file_count += 1
                            self.app.log(f"Downloaded image: {img_name}")
                        except requests.exceptions.RequestException as e:
                            self.app.log(
                                f"Error downloading image {img_url}: {e}", "error"
                            )

            if self.options["extract_all_urls"]:
                urls = {"internal": [], "external": []}
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    full_url = urljoin(url, href)
                    if urlparse(full_url).netloc == domain_name:
                        urls["internal"].append(full_url)
                    else:
                        urls["external"].append(full_url)
                data["urls"] = urls
                self.app.log(
                    f"Found {len(urls['internal'])} internal and {len(urls['external'])} external links."
                )

            # Save data based on format options
            if data and self.options["save_as_json"]:
                with open(
                    os.path.join(domain_folder, "data.json"), "w", encoding="utf-8"
                ) as f:
                    json.dump(data, f, indent=4)
                self.file_count += 1

            if data and self.options["save_as_csv"]:
                with open(
                    os.path.join(domain_folder, "data.csv"),
                    "w",
                    newline="",
                    encoding="utf-8",
                ) as f:
                    writer = csv.DictWriter(f, fieldnames=data.keys())
                    writer.writeheader()
                    writer.writerow(data)
                self.file_count += 1

            # Update GUI
            self.app.file_count_var.set(f"Files downloaded: {self.file_count}")
            self.app.update_progress(len(self.scraped_urls))

            # Recursive scraping
            if (
                self.options["follow_internal_links"]
                or self.options["follow_external_links"]
            ):
                links_to_follow = []
                if self.options["follow_internal_links"] and "urls" in data:
                    links_to_follow.extend(data["urls"]["internal"])
                if self.options["follow_external_links"] and "urls" in data:
                    links_to_follow.extend(data["urls"]["external"])

                for link in links_to_follow:
                    self.scrape(link)
                    if self.is_stopped():
                        break

        except requests.exceptions.HTTPError as e:
            self.app.log(f"HTTP Error: {e}", "error")
        except requests.exceptions.RequestException as e:
            self.app.log(f"Connection Error: {e}", "error")
        except Exception as e:
            self.app.log(f"An unexpected error occurred: {e}", "error")


class ScraperApp(tk.Tk):
    """The main GUI application."""

    def __init__(self):
        super().__init__()
        self.title("Web Scraper GUI")
        self.geometry("600x600")
        self.scraper_thread = None
        self.create_widgets()

    def create_widgets(self):
        """Creates all GUI widgets."""
        # Main Frame
        main_frame = ttk.LabelFrame(self, text="Web Scraper Settings", padding=(20, 10))
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # URL Input
        ttk.Label(main_frame, text="Enter URL to scrape:").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Save Location
        ttk.Label(main_frame, text="Save location:").grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        self.save_path_var = tk.StringVar()
        self.save_path_entry = ttk.Entry(
            main_frame, textvariable=self.save_path_var, state="readonly", width=50
        )
        self.save_path_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.browse_button = ttk.Button(
            main_frame, text="Browse", command=self.browse_for_folder
        )
        self.browse_button.grid(row=3, column=1, padx=(5, 0), sticky="e")

        # Result Name (Optional) - Not implemented as per requirement, domain name is used
        # Checkboxes for scraping options
        options_frame = ttk.LabelFrame(main_frame, text="Scraping Options", padding=5)
        options_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        self.options_vars = {}
        options = [
            ("Extract all URLs from <a> tags", "extract_all_urls"),
            ("Download all images (full resolution)", "download_images"),
            ("Extract text content", "extract_text_content"),
            ("Extract metadata (title, description, keywords)", "extract_metadata"),
            ("Follow internal links (recursive)", "follow_internal_links"),
            ("Follow external links", "follow_external_links"),
            ("Save as JSON", "save_as_json"),
            ("Save as CSV", "save_as_csv"),
            ("Save raw HTML", "save_raw_html"),
        ]
        for i, (text, var_name) in enumerate(options):
            self.options_vars[var_name] = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                options_frame, text=text, variable=self.options_vars[var_name]
            ).grid(row=i, column=0, sticky="w")

        # Buttons and Status
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        self.start_button = ttk.Button(
            button_frame, text="Start Scraping", command=self.start_scraping
        )
        self.start_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Scraping",
            command=self.stop_scraping,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side="left", padx=5)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(
            main_frame, orient="horizontal", mode="indeterminate"
        )
        self.progress_bar.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        # File Counter
        self.file_count_var = tk.StringVar(value="Files downloaded: 0")
        ttk.Label(main_frame, textvariable=self.file_count_var).grid(
            row=7, column=0, columnspan=2, sticky="w"
        )

        # Log Area
        ttk.Label(main_frame, text="Scraping Log:").grid(
            row=8, column=0, sticky="w", pady=(10, 5)
        )
        self.log_text = tk.Text(main_frame, height=10, state="disabled", wrap="word")
        self.log_text.grid(row=9, column=0, columnspan=2, sticky="nsew")
        main_frame.grid_rowconfigure(9, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

    def log(self, message, message_type="info"):
        """Appends a message to the log area."""
        self.log_text.config(state="normal")
        if message_type == "error":
            self.log_text.insert("end", f"[ERROR] {message}\n", "error")
        else:
            self.log_text.insert("end", f"[INFO] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def update_progress(self, value):
        """Updates the progress bar."""
        if value < 100:
            self.progress_bar.config(mode="indeterminate")
            self.progress_bar.start()
        else:
            self.progress_bar.config(mode="determinate", value=value)
            self.progress_bar.stop()

    def browse_for_folder(self):
        """Opens a file dialog to select a save location."""
        folder = filedialog.askdirectory()
        if folder:
            self.save_path_var.set(folder)

    def start_scraping(self):
        """Starts the scraping thread."""
        url = self.url_entry.get().strip()
        save_path = self.save_path_var.get().strip()

        if not url:
            self.log("Please enter a URL.", "error")
            return
        if not save_path:
            self.log("Please choose a save location.", "error")
            return

        options = {var: self.options_vars[var].get() for var in self.options_vars}

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_progress(0)
        self.log_text.delete(1.0, tk.END)
        self.file_count_var.set("Files downloaded: 0")

        # Start the scraping in a new thread
        self.scraper_thread = ScrapingThread(self, url, options, save_path)
        self.scraper_thread.start()

    def stop_scraping(self):
        """Stops the scraping thread."""
        if self.scraper_thread and self.scraper_thread.is_alive():
            self.scraper_thread.stop()
            self.log("Stopping scraping...")
            self.progress_bar.stop()
            self.stop_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    app = ScraperApp()
    app.mainloop()
