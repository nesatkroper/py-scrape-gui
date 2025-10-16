# scraper_core.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import os
import json
import csv
import threading
import collections
from datetime import datetime
import queue


class ScraperCore(threading.Thread):
    def __init__(
        self,
        start_url,
        base_path,
        images_path,
        videos_path,
        options,
        log_queue,
        stop_event,
    ):
        super().__init__()
        self.start_url = start_url
        self.base_path = base_path
        self.images_path = images_path
        self.videos_path = videos_path
        self.options = options
        self.log_queue = log_queue
        self.stop_event = stop_event
        self.error_logs = []
        self.max_depth = 3
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def run(self):
        """Main scraping method called when the thread starts."""
        self.log_queue.put(("log", f"Starting scrape on: {self.start_url}\n"))

        to_visit = collections.deque([(self.start_url, 0)])
        visited = set()
        data = []

        while to_visit and not self.stop_event.is_set():
            url, current_depth = to_visit.popleft()
            if url in visited or current_depth > self.max_depth:
                continue
            visited.add(url)
            self.log_queue.put(("log", f"Scraping {url} (depth {current_depth})...\n"))

            try:
                resp = requests.get(url, timeout=15, headers=self.headers)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                page_data = {"url": url}
                self._extract_data(soup, url, page_data)

                # Save Raw HTML (if selected)
                if self.options["Save raw HTML"]:
                    self._save_raw_html(resp.text, url)

                data.append(page_data)

                # Process links for recursion
                self._process_links(soup, url, to_visit, current_depth, self.start_url)

            except requests.exceptions.RequestException as e:
                error_msg = f"Error scraping {url}: {str(e)}"
                self.log_queue.put(("log", error_msg + "\n"))

        # Final saving steps
        if data and not self.stop_event.is_set():
            if self.options["Save as JSON"]:
                self._save_json(data)
            if self.options["Save as CSV"]:
                self._save_csv(data)

        self.log_queue.put(("log", "Scraping completed.\n"))
        self.log_queue.put(("done",))

    def _extract_data(self, soup, url, page_data):
        """Handles metadata, text, links, and file downloading."""
        opts = self.options

        # Metadata
        if opts["Extract metadata (title, description, keywords)"]:
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
                page_data.update(
                    {"title": title, "description": desc, "keywords": keys}
                )
            except Exception as e:
                self.log_queue.put(
                    ("log", f"Error extracting metadata from {url}: {str(e)}\n")
                )

        # Text Content
        if opts["Extract text content"]:
            try:
                for script_or_style in soup(["script", "style"]):
                    script_or_style.extract()
                page_data["text"] = soup.get_text(separator="\n", strip=True)
            except Exception:
                page_data["text"] = ""

        # Links (used for recursion and CSV/JSON output)
        links = []
        try:
            links = [
                urljoin(url, a["href"])
                for a in soup.find_all("a", href=True)
                if urlparse(urljoin(url, a["href"])).scheme in ("http", "https")
            ]
            if opts["Extract all URLs from <a> tags"]:
                page_data["links"] = links
        except Exception:
            pass

        # Images
        if opts["Download all images from <img> tags"]:
            for img in soup.find_all("img", src=True):
                self.download_file(urljoin(url, img["src"]), self.images_path, "image")

        # Videos
        if opts["Download all videos from <video> tags"]:
            for video in soup.find_all("video"):
                sources = video.find_all("source", src=True)
                if sources:
                    for source in sources:
                        self.download_file(
                            urljoin(url, source["src"]), self.videos_path, "video"
                        )
                elif video.get("src"):
                    self.download_file(
                        urljoin(url, video["src"]), self.videos_path, "video"
                    )

    def _save_raw_html(self, html_content, url):
        """Saves the raw HTML content of the page."""
        try:
            path_parts = urlparse(url).path.strip("/").replace("/", "_")
            html_filename = (
                f"{path_parts or 'index'}_{datetime.now().strftime('%H%M%S')}.html"
            )
            html_path = os.path.join(self.base_path, html_filename)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.log_queue.put(("log", f"Saved HTML: {html_filename}\n"))
            self.log_queue.put(("inc_count", 1))
        except OSError as e:
            self.log_queue.put(("log", f"Error saving HTML for {url}: {str(e)}\n"))

    def _process_links(self, soup, current_url, to_visit, current_depth, start_url):
        """Handles internal/external link processing for recursive scraping."""
        opts = self.options
        if not (
            opts["Follow internal links (recursive scraping)"]
            or opts["Follow external links"]
        ):
            return

        for a in soup.find_all("a", href=True):
            link = urljoin(current_url, a["href"])
            parsed_link = urlparse(link)

            if parsed_link.scheme not in ("http", "https") or not parsed_link.netloc:
                continue

            is_internal = parsed_link.netloc == urlparse(start_url).netloc

            if (is_internal and opts["Follow internal links (recursive scraping)"]) or (
                not is_internal and opts["Follow external links"]
            ):
                if link not in to_visit and current_depth + 1 <= self.max_depth:
                    to_visit.append((link, current_depth + 1))

    def _save_json(self, data):
        """Saves the extracted data to a JSON file."""
        try:
            json_path = os.path.join(self.base_path, "data.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.log_queue.put(("log", "Saved JSON to data.json\n"))
            self.log_queue.put(("inc_count", 1))
        except Exception as e:
            self.log_queue.put(("log", f"Error saving JSON: {str(e)}\n"))

    def _save_csv(self, data):
        """Saves the extracted data to a CSV file."""
        try:
            fields = set()
            for d in data:
                # Exclude list fields (like 'links') for cleaner CSV output
                fields.update(k for k, v in d.items() if not isinstance(v, list))
            fields = sorted(fields)
            csv_path = os.path.join(self.base_path, "data.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                cleaned_data = [
                    {k: v for k, v in row.items() if k in fields} for row in data
                ]
                writer.writerows(cleaned_data)
            self.log_queue.put(("log", "Saved CSV to data.csv\n"))
            self.log_queue.put(("inc_count", 1))
        except Exception as e:
            self.log_queue.put(("log", f"Error saving CSV: {str(e)}\n"))

    def download_file(self, file_url, save_path, file_type):
        """Generic method to download a file (image or video)."""
        if self.stop_event.is_set():
            return

        allowed_extensions = {
            "image": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"),
            "video": (".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv"),
        }

        try:
            if not file_url or not any(
                file_url.lower().endswith(ext)
                for ext in allowed_extensions.get(file_type, ())
            ):
                self.log_queue.put(
                    ("log", f"Skipping invalid {file_type.upper()} URL: {file_url}\n")
                )
                return

            timeout = 10 if file_type == "video" else 5
            resp = requests.get(
                file_url, timeout=timeout, headers=self.headers, stream=True
            )
            resp.raise_for_status()

            url_path = urlparse(file_url).path
            filename = os.path.basename(url_path)

            if not filename or os.path.isdir(os.path.join(save_path, filename)):
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

            with open(full_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.log_queue.put(("log", f"Downloaded {file_type}: {filename}\n"))
            self.log_queue.put(("inc_count", 1))

        except Exception as e:
            self.log_queue.put(
                ("log", f"Error downloading {file_type} {file_url}: {str(e)}\n")
            )
