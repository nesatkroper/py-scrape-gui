#!/usr/bin/env python3
"""
Credential Exposure Auditor (Improved Detection)

Single-file Python 3 application using tkinter for GUI and requests for web checks.

Features:
- Two scan modes: Web URL Scan and Local Directory Scan.
- Improved web heuristics to reduce false positives:
  * Examines Content-Type and body shape (HTML vs non-HTML)
  * Detects redirects (final URL != requested URL)
  * Searches for suspicious secret-like keywords before flagging
  * Option toggles: "Conservative mode" (safer, fewer false positives) and "Follow Redirects"
- Local scan searches recursively for sensitive filenames (case-insensitive).
- Threaded scanning so GUI remains responsive.
- Robust error handling with clear status updates and result logs.

Security & usage reminders:
- Only scan systems you own or have explicit permission to test.
- The tool intentionally avoids printing local file contents to prevent leaking secrets in the UI.
"""

import threading
import time
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText


WEB_TARGET_PATHS = ["/.env", "/config.json", "/wp-config.php", "/~.bash_history"]

LOCAL_SENSITIVE_PATTERNS = [
    ".env",
    "credentials",
    "secrets",
    "config.ini",
    "config.json",
    "config.yml",
    "docker-compose.yml",
    "database.yml",
]

SUSPICIOUS_KEYWORDS = [
    "db_password",
    "database_url",
    "app_key",
    "secret_key",
    "aws_access_key_id",
    "aws_secret_access_key",
    "password=",
    "passwd=",
    "username=",
    "api_key",
    "auth_token",
    "token=",
]

HTTP_TIMEOUT = 10


def normalize_base_url(raw_url: str) -> str:
    """
    Ensure the provided URL includes a scheme and ends with a slash to make urljoin predictable.
    """
    url = raw_url.strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "http://" + url
    if not url.endswith("/"):
        url += "/"
    return url


def looks_like_html(content_bytes: bytes, content_type_header: str) -> bool:
    """
    Heuristic to determine if response content looks like HTML.
    - Checks Content-Type header for 'html'
    - Checks if the decoded text starts with '<'
    - Falls back to bytes check (leading '<')
    """
    if content_type_header and "html" in content_type_header.lower():
        return True
    if not content_bytes:
        return False
    try:
        text = content_bytes.decode("utf-8", errors="ignore").lstrip()
        if text.startswith("<"):
            return True
    except Exception:
        pass
    if content_bytes.startswith(b"<"):
        return True
    return False


def contains_suspicious_keyword(content_bytes: bytes) -> bool:
    """
    Case-insensitive search for suspicious keywords inside the response content.
    Returns True if any keyword found.
    """
    if not content_bytes:
        return False
    try:
        text = content_bytes.decode("utf-8", errors="ignore").lower()
    except Exception:
        try:
            text = str(content_bytes).lower()
        except Exception:
            text = ""
    for kw in SUSPICIOUS_KEYWORDS:
        if kw.lower() in text:
            return True
    return False


class CredentialExposureAuditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Credential Exposure Auditor")
        self.geometry("920x620")

        self.scan_mode = tk.StringVar(value="web")
        self.input_value = tk.StringVar()
        self.is_scanning = False
        self.found_count = 0

        self.conservative_mode = tk.BooleanVar(value=True)
        self.follow_redirects = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Target URL or Local Path:").grid(
            row=0, column=0, sticky=tk.W
        )
        self.entry = ttk.Entry(top, textvariable=self.input_value, width=80)
        self.entry.grid(row=0, column=1, padx=8, sticky=tk.W)
        self.entry.bind("<Return>", lambda e: self.start_scan())

        mode_frame = ttk.Frame(top)
        mode_frame.grid(row=1, column=1, sticky=tk.W, pady=(6, 0))
        ttk.Label(mode_frame, text="Scanning Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(
            mode_frame, text="Web URL Scan", variable=self.scan_mode, value="web"
        ).pack(side=tk.LEFT, padx=(8, 4))
        ttk.Radiobutton(
            mode_frame,
            text="Local Directory Scan",
            variable=self.scan_mode,
            value="local",
        ).pack(side=tk.LEFT, padx=(4, 4))

        options_frame = ttk.Frame(top)
        options_frame.grid(row=2, column=1, sticky=tk.W, pady=(8, 0))
        ttk.Checkbutton(
            options_frame,
            text="Conservative mode (require non-HTML + secret keywords)",
            variable=self.conservative_mode,
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            options_frame, text="Follow redirects", variable=self.follow_redirects
        ).pack(side=tk.LEFT, padx=(12, 0))

        button_frame = ttk.Frame(top)
        button_frame.grid(row=0, column=2, rowspan=3, padx=(6, 0))
        self.start_button = ttk.Button(
            button_frame, text="Start Scan", command=self.start_scan
        )
        self.start_button.pack(side=tk.TOP, fill=tk.X)
        self.stop_button = ttk.Button(
            button_frame, text="Stop Scan", command=self.stop_scan, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))

        results_frame = ttk.Frame(self, padding=(10, 10))
        results_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        ttk.Label(results_frame, text="Scan Results:").pack(anchor=tk.W)
        self.results_text = ScrolledText(results_frame, wrap=tk.WORD, height=30)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)

        status_frame = ttk.Frame(self, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(status_frame, text="Ready.", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        help_text = "Tip: For Web scans use 'https://example.com'. For Local scans use '/var/www/html' or 'C:\\\\inetpub\\\\wwwroot'."
        ttk.Label(status_frame, text=help_text).pack(side=tk.RIGHT, padx=6)

    def append_result(self, line: str):
        def inner():
            self.results_text.config(state=tk.NORMAL)
            self.results_text.insert(tk.END, line + "\n")
            self.results_text.see(tk.END)
            self.results_text.config(state=tk.DISABLED)

        self.results_text.after(0, inner)

    def set_status(self, text: str):
        def inner():
            self.status_label.config(text=text)

        self.status_label.after(0, inner)

    def enable_controls(self, scanning: bool):
        def inner():
            if scanning:
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.entry.config(state=tk.DISABLED)
            else:
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.entry.config(state=tk.NORMAL)

        self.start_button.after(0, inner)

    def start_scan(self):
        if self.is_scanning:
            messagebox.showinfo("Scan running", "A scan is already in progress.")
            return
        target = self.input_value.get().strip()
        if not target:
            messagebox.showwarning(
                "Input required", "Please enter a URL or local directory path to scan."
            )
            return

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state=tk.DISABLED)

        self.is_scanning = True
        self.found_count = 0
        self.enable_controls(True)
        self.set_status("Initializing scan...")

        worker = threading.Thread(
            target=self._scan_worker, args=(target, self.scan_mode.get()), daemon=True
        )
        worker.start()

    def stop_scan(self):
        if not self.is_scanning:
            return
        self.is_scanning = False
        self.set_status("Stopping scan...")

    def _scan_worker(self, target: str, mode: str):
        try:
            if mode == "web":
                self._perform_web_scan(target)
            elif mode == "local":
                self._perform_local_scan(target)
            else:
                self.append_result(f"[ERROR] Unknown mode: {mode}")
        except Exception as e:
            self.append_result(f"[ERROR] Unexpected exception: {e}")
        finally:
            self.is_scanning = False
            self.enable_controls(False)
            self.set_status(
                f"Scan complete. Found {self.found_count} potential exposures."
            )

    def _perform_web_scan(self, raw_url: str):
        base_url = normalize_base_url(raw_url)
        if not base_url:
            self.append_result("[ERROR] Invalid URL provided.")
            self.set_status("Invalid URL.")
            return

        self.append_result(f"[INFO] Starting web scan on {base_url}")
        self.set_status("Scanning web targets...")
        checked = 0

        for path in WEB_TARGET_PATHS:
            if not self.is_scanning:
                self.append_result("[INFO] Scan stopped by user.")
                break

            target_url = urljoin(base_url, path.lstrip("/"))
            self.append_result(f"[CHECK] {target_url}")
            checked += 1

            try:
                resp = requests.get(
                    target_url,
                    timeout=HTTP_TIMEOUT,
                    allow_redirects=self.follow_redirects.get(),
                )
                status = resp.status_code
                content_bytes = resp.content or b""
                content_len = len(content_bytes)
                content_type = resp.headers.get("Content-Type", "")

                self.append_result(
                    f"  → HTTP {status}, Content Length: {content_len}, Content-Type: {content_type}"
                )

                flagged = False
                diagnostic_reasons = []

                if status != 200:
                    diagnostic_reasons.append(f"status_{status}")
                else:
                    if self.conservative_mode.get():
                        if looks_like_html(content_bytes, content_type):
                            diagnostic_reasons.append("looks_like_html")
                        else:
                            if contains_suspicious_keyword(content_bytes):
                                flagged = True
                            else:
                                diagnostic_reasons.append("no_secret_keywords")
                    else:
                        if content_len > 0 and not looks_like_html(
                            content_bytes, content_type
                        ):
                            flagged = True
                        else:
                            if contains_suspicious_keyword(content_bytes):
                                flagged = True
                            else:
                                diagnostic_reasons.append(
                                    "not_flagged_by_aggressive_rules"
                                )

                final_url = getattr(resp, "url", "")
                if final_url and final_url.rstrip("/") != target_url.rstrip("/"):
                    diagnostic_reasons.append("redirected")

                if flagged:
                    try:
                        snippet = resp.text.replace("\n", " ").replace("\r", " ")[:50]
                    except Exception:
                        snippet = "[Could not decode snippet]"
                    self.found_count += 1
                    self.append_result(f"  !! EXPOSURE FOUND: {target_url}")
                    self.append_result(f"     Snippet (first 50 chars): {snippet}")
                else:
                    reasons = (
                        ", ".join(diagnostic_reasons) if diagnostic_reasons else "none"
                    )
                    self.append_result(f"  [INFO] Not flagged ({reasons}).")

            except requests.exceptions.Timeout:
                self.append_result(
                    f"  [ERROR] Timeout after {HTTP_TIMEOUT}s for {target_url}"
                )
            except requests.exceptions.SSLError as se:
                self.append_result(f"  [ERROR] SSL error for {target_url}: {se}")
            except requests.exceptions.ConnectionError as ce:
                self.append_result(f"  [ERROR] Connection error for {target_url}: {ce}")
            except requests.exceptions.RequestException as rexc:
                self.append_result(
                    f"  [ERROR] Request exception for {target_url}: {rexc}"
                )
            except Exception as e:
                self.append_result(f"  [ERROR] Unexpected error for {target_url}: {e}")

            self.set_status(
                f"Web scan: checked {checked}/{len(WEB_TARGET_PATHS)} targets. Found {self.found_count}"
            )
            time.sleep(0.12)

        self.set_status(
            f"Web scan complete. Found {self.found_count} potential exposures."
        )
        if self.found_count == 0:
            self.append_result(
                "[INFO] No clear exposures found. Note: conservative mode reduces false positives; try disabling it for a more aggressive scan (may increase false positives)."
            )

    def _perform_local_scan(self, raw_path: str):
        path_expanded = os.path.expanduser(raw_path)
        p = Path(path_expanded)

        if not p.exists():
            self.append_result(f"[ERROR] Path not found: {path_expanded}")
            self.set_status("Path not found.")
            return
        if not p.is_dir():
            self.append_result(
                f"[ERROR] Provided path is not a directory: {path_expanded}"
            )
            self.set_status("Not a directory.")
            return

        self.append_result(f"[INFO] Starting local directory scan on: {p.resolve()}")
        self.set_status("Scanning local files...")
        checked_files = 0

        try:
            for root, dirs, files in os.walk(p, topdown=True):
                if not self.is_scanning:
                    self.append_result("[INFO] Scan stopped by user.")
                    break
                for fname in files:
                    if not self.is_scanning:
                        break
                    checked_files += 1
                    fname_lower = fname.lower()

                    matched = False
                    for pattern in LOCAL_SENSITIVE_PATTERNS:
                        if pattern.lower() in fname_lower:
                            matched = True
                            break

                    if matched:
                        full_path = os.path.join(root, fname)
                        self.found_count += 1
                        self.append_result(f"!! POTENTIAL EXPOSURE: {full_path}")
                        self.append_result(
                            "   WARNING: Filename matches sensitive pattern. Review file permissions & contents manually."
                        )
                    if checked_files % 100 == 0:
                        self.set_status(
                            f"Scanned {checked_files} files... Found {self.found_count}"
                        )
                time.sleep(0.01)
        except PermissionError as pe:
            self.append_result(f"[ERROR] Permission denied while traversing: {pe}")
        except OSError as oe:
            self.append_result(f"[ERROR] File system error: {oe}")
        except Exception as e:
            self.append_result(f"[ERROR] Unexpected error during local scan: {e}")

        self.set_status(
            f"Local scan complete. Scanned {checked_files} files. Found {self.found_count} potential exposures."
        )
        if self.found_count == 0:
            self.append_result(
                "[INFO] No suspicious filenames found. Manual review is still recommended."
            )


def main():
    try:
        import requests
    except Exception:
        messagebox.showerror(
            "Missing dependency",
            "The 'requests' library is required. Install it with: pip install requests",
        )
        return

    app = CredentialExposureAuditor()
    app.mainloop()


if __name__ == "__main__":
    main()
