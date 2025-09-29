import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
from bs4 import BeautifulSoup


class ImagePreviewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Safe Image Previewer")
        self.root.geometry("800x600")

        # URL input
        self.url_label = tk.Label(root, text="Website URL:")
        self.url_label.pack(pady=5)
        self.url_entry = tk.Entry(root, width=60)
        self.url_entry.pack(pady=5)

        # Fetch button
        self.fetch_btn = tk.Button(
            root, text="Preview Images", command=self.fetch_images
        )
        self.fetch_btn.pack(pady=5)

        # Scrollable canvas for images
        self.canvas = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(
            root, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.images = []

    def fetch_images(self):
        url = self.url_entry.get().strip()
        if not url.startswith("http"):
            url = "https://" + url
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch URL:\n{e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img")
        if not img_tags:
            messagebox.showinfo("Info", "No images found on this page.")
            return

        # Clear previous images
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.images = []

        for idx, img in enumerate(img_tags):
            src = img.get("src")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = url.rstrip("/") + src
            try:
                img_response = requests.get(src, timeout=10)
                img_response.raise_for_status()
                pil_img = Image.open(BytesIO(img_response.content))
                pil_img.thumbnail((200, 200))
                tk_img = ImageTk.PhotoImage(pil_img)
                self.images.append(tk_img)
                label = tk.Label(self.scrollable_frame, image=tk_img)
                label.grid(row=idx // 3, column=idx % 3, padx=5, pady=5)
            except Exception as e:
                print(f"Skipping image {src}: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePreviewer(root)
    root.mainloop()


# import os
# import json
# import requests
# from urllib.parse import urlparse, urljoin
# from bs4 import BeautifulSoup
# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox
# import threading
# from openpyxl import Workbook


# # ---------- Helper Functions ----------
# def sanitize_filename(name):
#     return "".join(c for c in name if c.isalnum() or c in "._-")


# def download_media(url, folder, log_panel):
#     try:
#         if url.startswith("//"):
#             url = "https:" + url
#         r = requests.get(url, stream=True, timeout=15)
#         r.raise_for_status()
#         filename = os.path.join(folder, sanitize_filename(url.split("/")[-1]))
#         with open(filename, "wb") as f:
#             for chunk in r.iter_content(1024):
#                 f.write(chunk)
#         log_panel.insert(tk.END, f"Downloaded: {url}")
#         log_panel.yview(tk.END)
#         return filename
#     except Exception as e:
#         log_panel.insert(tk.END, f"Error downloading {url}: {e}")
#         log_panel.yview(tk.END)
#         return None


# def scrape_website(
#     url, output_dir, log_panel, progress_var, export_json=True, export_excel=True
# ):
#     try:
#         r = requests.get(url, timeout=15)
#         r.raise_for_status()
#     except Exception as e:
#         messagebox.showerror("Error", f"Failed to fetch URL: {e}")
#         return

#     soup = BeautifulSoup(r.text, "html.parser")
#     domain = urlparse(url).netloc
#     domain_folder = os.path.join(output_dir, sanitize_filename(domain))
#     os.makedirs(domain_folder, exist_ok=True)

#     # Collect images and videos
#     media_urls = set()
#     for img in soup.find_all("img"):
#         src = img.get("src") or img.get("data-src")
#         if src:
#             media_urls.add(urljoin(url, src))
#         srcset = img.get("srcset")
#         if srcset:
#             largest = srcset.split(",")[-1].split()[0]
#             media_urls.add(urljoin(url, largest))
#     for video in soup.find_all("video"):
#         src = video.get("src")
#         if src:
#             media_urls.add(urljoin(url, src))
#         for source in video.find_all("source"):
#             src = source.get("src")
#             if src:
#                 media_urls.add(urljoin(url, src))

#     results = []
#     total = len(media_urls)
#     progress_step = 100 / max(total, 1)

#     for i, m_url in enumerate(media_urls, 1):
#         filename = download_media(m_url, domain_folder, log_panel)
#         if filename:
#             results.append({"url": m_url, "file": filename})
#         progress_var.set(i * progress_step)

#     # Save JSON
#     if export_json:
#         json_path = os.path.join(domain_folder, "scraped.json")
#         with open(json_path, "w", encoding="utf-8") as f:
#             json.dump(results, f, ensure_ascii=False, indent=2)

#     # Save Excel
#     if export_excel:
#         wb = Workbook()
#         ws = wb.active
#         ws.append(["URL", "Saved File"])
#         for item in results:
#             ws.append([item["url"], item["file"]])
#         excel_path = os.path.join(domain_folder, "scraped.xlsx")
#         wb.save(excel_path)

#     log_panel.insert(
#         tk.END, f"Scraping complete! {len(results)} items saved in {domain_folder}"
#     )
#     log_panel.yview(tk.END)
#     progress_var.set(0)


# # ---------- GUI ----------
# class ScraperGUI:
#     def __init__(self, root):
#         self.root = root
#         root.title("Python Web Scraper")

#         # URL input
#         tk.Label(root, text="Website URL:").grid(row=0, column=0, sticky="w")
#         self.url_entry = tk.Entry(root, width=60)
#         self.url_entry.grid(row=0, column=1, columnspan=2, pady=5, sticky="w")

#         # Output directory
#         tk.Label(root, text="Output Folder:").grid(row=1, column=0, sticky="w")
#         self.output_entry = tk.Entry(root, width=50)
#         self.output_entry.grid(row=1, column=1, pady=5, sticky="w")
#         tk.Button(root, text="Browse", command=self.browse_folder).grid(
#             row=1, column=2, padx=5
#         )

#         # Start button
#         self.start_btn = tk.Button(
#             root, text="Start Scraping", command=self.start_scraping
#         )
#         self.start_btn.grid(row=2, column=1, pady=10)

#         # Progress bar
#         self.progress_var = tk.DoubleVar()
#         self.progress = ttk.Progressbar(
#             root, variable=self.progress_var, maximum=100, length=400
#         )
#         self.progress.grid(row=3, column=0, columnspan=3, pady=5)

#         # Log panel
#         tk.Label(root, text="Log / Errors:").grid(row=4, column=0, sticky="w")
#         self.log_panel = tk.Listbox(root, width=80, height=20)
#         self.log_panel.grid(row=5, column=0, columnspan=3, pady=5)

#         # Copy button
#         tk.Button(root, text="Copy Log", command=self.copy_log).grid(
#             row=6, column=1, pady=5
#         )

#     def browse_folder(self):
#         folder = filedialog.askdirectory()
#         if folder:
#             self.output_entry.delete(0, tk.END)
#             self.output_entry.insert(0, folder)

#     def copy_log(self):
#         self.root.clipboard_clear()
#         self.root.clipboard_append("\n".join(self.log_panel.get(0, tk.END)))
#         messagebox.showinfo("Copied", "Log copied to clipboard!")

#     def start_scraping(self):
#         url = self.url_entry.get().strip()
#         output_dir = self.output_entry.get().strip()
#         if not url or not output_dir:
#             messagebox.showwarning(
#                 "Input Required", "Please enter URL and output folder"
#             )
#             return
#         threading.Thread(
#             target=scrape_website,
#             args=(url, output_dir, self.log_panel, self.progress_var),
#         ).start()


# # ---------- Run ----------
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = ScraperGUI(root)
#     root.mainloop()
