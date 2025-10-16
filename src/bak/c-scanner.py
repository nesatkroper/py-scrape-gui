#!/usr/bin/env python3
"""
Credential Exposure Auditor
Author: ChatGPT (as requested)
Description:
    - A single-file Python3 application using tkinter for GUI that helps auditors
      and developers quickly check for exposed credential/configuration files
      either on a public web host or in a local server directory.

    - Mode 1 (Web URL Scan): appends common sensitive filenames to a base URL,
      performs HTTP GET requests, and reports files that return 200 OK with
      non-zero content length. For confirmed exposures the first 50 characters
      of the file are shown as a snippet to help verify whether the response
      is meaningful (not a generic 200 error page).

    - Mode 2 (Local Server Directory Scan): recursively traverses a local path
      and reports files whose names contain or exactly match sensitive patterns.
      Useful for scanning a developer workstation or server file tree.

Requirements:
    - Python 3
    - requests (pip install requests)
    - Uses only standard library + requests
"""

import threading
import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

# ------------------------------
# Configuration / Constants
# ------------------------------

# Web scan targets: common files that often contain credentials or configuration.
# Security rationale: Files like .env, wp-config.php, config.json, or user history
# may contain API keys, database credentials, or other secrets that must never be
# served publicly. Penetration testers check these to find accidental exposures.
WEB_TARGET_PATHS = ["/.env", "/config.json", "/wp-config.php", "/~.bash_history"]

# Local file name patterns to look for (case-insensitive). A match may indicate
# a file that contains credentials or other secrets.
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

# Network settings
HTTP_TIMEOUT = 10  # seconds for requests.get

# ------------------------------
# Helper / Utility Functions
# ------------------------------


def normalize_base_url(raw_url: str) -> str:
    """
    Ensure the URL has a scheme. If not, default to http://.
    Also strip trailing spaces.
    """
    url = raw_url.strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "http://" + url
    # Ensure it ends with a slash for proper urljoin behaviour (we join explicit paths)
    if not url.endswith("/"):
        url = url + "/"
    return url


# ------------------------------
# GUI App Class
# ------------------------------


class CredentialExposureAuditor(tk.Tk):
    """
    Main application window using tkinter.
    """

    def __init__(self):
        super().__init__()
        self.title("Credential Exposure Auditor")
        self.geometry("900x600")
        self.resizable(True, True)

        # ------------------------------
        # GUI Variables
        # ------------------------------
        self.scan_mode = tk.StringVar(value="web")  # 'web' or 'local'
        self.input_value = tk.StringVar()
        self.is_scanning = False
        self.found_count = 0

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """
        Create and lay out all GUI widgets: input, mode selector, start button,
        results area, and status bar.
        """
        # Top frame for input and mode selection
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        top_frame.pack(side=tk.TOP, fill=tk.X)

        # Label + entry
        ttk.Label(top_frame, text="Target URL or Local Path:").grid(
            row=0, column=0, sticky=tk.W
        )
        self.entry = ttk.Entry(top_frame, textvariable=self.input_value, width=80)
        self.entry.grid(row=0, column=1, padx=(8, 8), sticky=tk.W)
        self.entry.bind("<Return>", lambda e: self.start_scan())

        # Mode selector (radio buttons)
        mode_frame = ttk.Frame(top_frame)
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

        # Start & Stop buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.grid(row=0, column=2, rowspan=2, padx=(6, 0))
        self.start_button = ttk.Button(
            button_frame, text="Start Scan", command=self.start_scan
        )
        self.start_button.pack(side=tk.TOP, fill=tk.X)
        self.stop_button = ttk.Button(
            button_frame, text="Stop Scan", command=self.stop_scan, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))

        # Results area
        results_frame = ttk.Frame(self, padding=(10, 10))
        results_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        ttk.Label(results_frame, text="Scan Results:").pack(anchor=tk.W)
        self.results_text = ScrolledText(results_frame, wrap=tk.WORD, height=25)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)  # read-only to user

        # Status bar
        status_frame = ttk.Frame(self, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(status_frame, text="Ready.", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        # Hint / help
        help_text = (
            "Tip: For Web scans enter a base URL like 'https://example.com'.\n"
            "For Local scans enter a folder path like '/var/www/html' or 'C:\\\\inetpub\\\\wwwroot'."
        )
        self.help_label = ttk.Label(status_frame, text=help_text, anchor=tk.E)
        self.help_label.pack(side=tk.RIGHT, padx=6)

    # ------------------------------
    # UI Update Helpers (thread-safe)
    # ------------------------------

    def append_result(self, text: str):
        """
        Append text to the results area in a thread-safe way.
        """

        def inner():
            self.results_text.config(state=tk.NORMAL)
            self.results_text.insert(tk.END, text + "\n")
            self.results_text.see(tk.END)
            self.results_text.config(state=tk.DISABLED)

        self.results_text.after(0, inner)

    def set_status(self, text: str):
        """
        Update the status label in a thread-safe way.
        """

        def inner():
            self.status_label.config(text=text)

        self.status_label.after(0, inner)

    def enable_controls(self, scanning: bool):
        """
        Enable/disable Start/Stop controls depending on scanning state.
        """

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

    # ------------------------------
    # Scan Control Handlers
    # ------------------------------

    def start_scan(self):
        """
        Entry point when user clicks "Start Scan". Validates input and spawns a
        worker thread to perform the scan so the GUI remains responsive.
        """
        if self.is_scanning:
            messagebox.showinfo("Scan in progress", "A scan is already running.")
            return

        target = self.input_value.get().strip()
        mode = self.scan_mode.get()

        if not target:
            messagebox.showwarning(
                "Input required", "Please enter a URL or local directory path to scan."
            )
            return

        # Clear previous results
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state=tk.DISABLED)

        self.is_scanning = True
        self.found_count = 0
        self.enable_controls(True)
        self.set_status("Initializing scan...")

        # Start thread
        worker = threading.Thread(
            target=self._scan_worker, args=(target, mode), daemon=True
        )
        worker.start()

    def stop_scan(self):
        """
        Signal to stop scanning. The worker thread checks self.is_scanning to
        gracefully stop.
        """
        if not self.is_scanning:
            return
        self.is_scanning = False
        self.set_status("Stopping scan... (will stop shortly)")

    # ------------------------------
    # Scanning Worker
    # ------------------------------

    def _scan_worker(self, target: str, mode: str):
        """
        Worker thread that dispatches to web or local scanning functions.
        """
        try:
            if mode == "web":
                self._perform_web_scan(target)
            elif mode == "local":
                self._perform_local_scan(target)
            else:
                self.append_result(f"[ERROR] Unknown scan mode: {mode}")
        except Exception as e:
            # Catch-all to ensure GUI remains stable; log to results area.
            self.append_result(f"[ERROR] Unexpected exception: {e}")
        finally:
            self.is_scanning = False
            self.enable_controls(False)
            self.set_status(
                f"Scan complete. Found {self.found_count} potential exposures."
            )

    # ------------------------------
    # Web Scan Logic
    # ------------------------------

    def _perform_web_scan(self, raw_url: str):
        """
        For each path in WEB_TARGET_PATHS, append to base URL and perform a GET.
        Report as exposed if status_code == 200 and content length > 0.
        """
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

            # urljoin handles slashes correctly
            target_url = urljoin(base_url, path.lstrip("/"))
            self.append_result(f"[CHECK] {target_url}")
            checked += 1
            try:
                # Important security note: we use a reasonable timeout and
                # do not follow redirects by default (requests will follow by default;
                # if desirable, you can set allow_redirects=False)
                resp = requests.get(target_url, timeout=HTTP_TIMEOUT)
                status = resp.status_code
                content_len = len(resp.content) if resp.content is not None else 0
                self.append_result(f"  → HTTP {status}, Content Length: {content_len}")
                # Validation: exposed only if 200 and non-zero content length
                if status == 200 and content_len > 0:
                    # Snippet: first 50 characters; decode best-effort
                    try:
                        snippet = resp.text[:50]
                        # Remove newlines for a compact snippet
                        snippet = snippet.replace("\n", " ").replace("\r", " ")
                    except Exception:
                        snippet = "[Could not decode content preview]"
                    self.found_count += 1
                    self.append_result(f"  !! EXPOSURE FOUND: {target_url}")
                    self.append_result(f"     Snippet (first 50 chars): {snippet}")
                else:
                    # Not flagged, but included as checked entry
                    pass
            except requests.exceptions.Timeout:
                self.append_result(
                    f"  [ERROR] Timeout after {HTTP_TIMEOUT}s for {target_url}"
                )
            except requests.exceptions.ConnectionError as ce:
                self.append_result(f"  [ERROR] Connection error for {target_url}: {ce}")
            except requests.exceptions.SSLError as se:
                self.append_result(f"  [ERROR] SSL error for {target_url}: {se}")
            except Exception as e:
                self.append_result(f"  [ERROR] Unexpected error for {target_url}: {e}")

            # Update status dynamically
            self.set_status(
                f"Web scan: checked {checked}/{len(WEB_TARGET_PATHS)} targets. Found {self.found_count}"
            )
            # Small sleep to make UI updates perceptible (and be polite)
            time.sleep(0.15)

        self.set_status(
            f"Web scan complete. Found {self.found_count} potential exposures."
        )
        if self.found_count == 0:
            self.append_result(
                "[INFO] No obvious exposures found for the scanned paths. This is NOT a guarantee; further testing may be needed."
            )

    # ------------------------------
    # Local Scan Logic
    # ------------------------------

    def _perform_local_scan(self, raw_path: str):
        """
        Recursively scan the provided local path for filenames that contain
        or exactly match patterns in LOCAL_SENSITIVE_PATTERNS (case-insensitive).
        """
        # Expand user and resolve
        expanded = os.path.expanduser(raw_path)
        p = Path(expanded)

        if not p.exists():
            self.append_result(f"[ERROR] Path not found: {expanded}")
            self.set_status("Path not found.")
            return

        if not p.is_dir():
            self.append_result(f"[ERROR] Provided path is not a directory: {expanded}")
            self.set_status("Not a directory.")
            return

        self.append_result(f"[INFO] Starting local directory scan on: {p.resolve()}")
        self.set_status("Scanning local files...")
        checked_files = 0

        try:
            # Walk the directory tree. Using os.walk for robust permission handling.
            for root, dirs, files in os.walk(p, topdown=True):
                # Early termination check
                if not self.is_scanning:
                    self.append_result("[INFO] Scan stopped by user.")
                    break

                # Optionally we could filter out large directories like .git, node_modules, etc.
                # but for an auditor we check everything by default.
                for fname in files:
                    if not self.is_scanning:
                        break
                    checked_files += 1
                    fname_lower = fname.lower()

                    # If any sensitive pattern is contained in the filename, flag it.
                    matched = False
                    for pattern in LOCAL_SENSITIVE_PATTERNS:
                        # pattern match is case-insensitive; check containment
                        if pattern.lower() in fname_lower:
                            matched = True
                            break

                    # If matched, prepare a strong warning message.
                    if matched:
                        full_path = os.path.join(root, fname)
                        self.found_count += 1
                        self.append_result(f"!! POTENTIAL EXPOSURE: {full_path}")
                        self.append_result(
                            f"   WARNING: File name matches sensitive pattern. Review file permissions & contents immediately."
                        )
                        # Optionally show small snippet of the file if readable; but that might expose secrets
                        # in the UI. We intentionally DO NOT display file contents beyond the path to avoid
                        # leaking secrets into displayed logs. The auditor can open files separately if needed.
                    # Update status occasionally to avoid too verbose updates
                    if checked_files % 50 == 0:
                        self.set_status(
                            f"Scanned {checked_files} files... Found {self.found_count}"
                        )
                # Small delay to allow UI to update for very large trees
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
                "[INFO] No obvious sensitive filenames found during the local scan. This is NOT a guarantee; manual review may still be necessary."
            )


# ------------------------------
# Main Entry
# ------------------------------


def main():
    # Verify that 'requests' is available
    try:
        import requests  # already imported but validate
    except Exception:
        messagebox.showerror(
            "Missing dependency",
            "The 'requests' library is required. Install it with: pip install requests",
        )
        return

    # Create and run the app
    app = CredentialExposureAuditor()
    app.mainloop()


if __name__ == "__main__":
    main()
