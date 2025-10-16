import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import os
import pathlib
import threading
from typing import List, Dict, Tuple, Optional

APP_TITLE = "Credential Exposure Auditor 🛡️ (Advanced)"

WEB_TARGETS: List[str] = [
    "/.env",
    "/config.json",
    "/wp-config.php",
    "/appsettings.json",
    "/web.config",
    "/.git/config",
    "/.svn/entries",
    "/.hg/hgrc",
    "/.bzr/branch/branch.conf",
    "/~.bash_history",
    "/~.profile",
    "/~.bashrc",
    "/error.log",
    "/debug.log",
    "/access.log",
    "/php_errors.log",
    "/backup.zip",
    "/site.tar.gz",
    "/db_backup.sql",
    "/db_dump.sql",
    "/index.html.bak",
    "/sitemap.xml.bak",
    "/robots.txt.bak",
    "/Dockerfile",
    "/docker-compose.yml",
    "/kubeconfig",
    "/.aws/credentials",
    "/google-svc-key.json",
    "/.ssh/id_rsa.pub",
]

LOCAL_PATTERNS: List[str] = [
    ".env",
    "credentials",
    "secrets",
    "key",
    "token",
    "auth",
    "cert",
    "db",
    "password",
    "api_key",
    "jwt",
    "settings.py",
    "database.yml",
    "app.config",
    "config.ini",
    "config.json",
    "config.yml",
    "server.conf",
    "mariadb.cnf",
    "pgpass",
    "id_rsa",
    "id_dsa",
    "ssh_config",
    "terraform.tfvars",
    "ansible.cfg",
    ".log",
    ".sql",
    ".bak",
    ".old",
    ".temp",
    ".conf",
    ".yml",
    ".ini",
    "aws_credentials",
    "google-svc-key",
    "azure.json",
]

MAX_SNIPPET_LENGTH = 50


class CredentialExposureAuditor(tk.Tk):
    """
    The main application class for the Credential Exposure Auditor.
    Uses tkinter for the GUI and implements both web and local file system scans.
    """

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("800x600")
        self.configure(bg="#f0f0f0")

        self.scan_mode = tk.StringVar(value="Web")

        self._setup_ui()

    def _setup_ui(self):
        """Sets up all the GUI components (frames, widgets, status bar, etc.)."""

        control_frame = tk.Frame(self, padx=10, pady=10, bg="#e0e0e0")
        control_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            control_frame,
            text="Scanning Mode:",
            bg="#e0e0e0",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(0, 10))

        rb_web = tk.Radiobutton(
            control_frame,
            text="Web URL Scan",
            variable=self.scan_mode,
            value="Web",
            bg="#e0e0e0",
            font=("Arial", 10),
            command=self._update_input_placeholder,
        )
        rb_local = tk.Radiobutton(
            control_frame,
            text="Local Dir Scan",
            variable=self.scan_mode,
            value="Local",
            bg="#e0e0e0",
            font=("Arial", 10),
            command=self._update_input_placeholder,
        )
        rb_web.pack(side="left", padx=5)
        rb_local.pack(side="left", padx=5)

        self.input_entry = tk.Entry(control_frame, width=50, bd=2, relief=tk.SUNKEN)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=15)
        self._update_input_placeholder()

        self.scan_button = tk.Button(
            control_frame,
            text="Start Scan",
            command=self._start_scan_thread,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            activebackground="#3e8e41",
            padx=10,
        )
        self.scan_button.pack(side="right")

        tk.Label(
            self, text="Scan Results:", font=("Arial", 10, "bold"), bg="#f0f0f0"
        ).pack(fill="x", padx=10, pady=(5, 0))

        results_frame = tk.Frame(self, padx=10, pady=5, bg="#f0f0f0")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            state="disabled",
            font=("Consolas", 9),
            bg="#ffffff",
            fg="#333333",
            relief=tk.FLAT,
            bd=2,
        )
        self.results_text.pack(fill="both", expand=True)
        self._log_result(
            f"Welcome to {APP_TITLE}. Select a mode and enter your target.",
            is_status=True,
        )

        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor="w",
            bg="#cccccc",
            fg="#333333",
            font=("Arial", 9),
        )
        self.status_bar.pack(side="bottom", fill="x")
        self._update_status("Ready to scan.")

    def _update_input_placeholder(self):
        """Updates the placeholder text in the input field based on the selected scan mode."""
        mode = self.scan_mode.get()
        self.input_entry.delete(0, tk.END)
        if mode == "Web":
            self.input_entry.insert(0, "https://format.konkmeng.site")
        elif mode == "Local":
            self.input_entry.insert(0, "e.g., /var/www/html or C:\\xampp\\htdocs")

    def _update_status(self, message: str, color: str = "#333333"):
        """Updates the message and color in the status bar."""
        self.status_var.set(message)
        self.status_bar.config(fg=color)
        self.update_idletasks()

    def _log_result(self, message: str, is_status: bool = False):
        """Adds a message to the results text area with color tagging."""
        tag = "status" if is_status else "result"
        color = (
            "blue"
            if is_status
            else ("red" if "ERROR" in message or "EXPOSED" in message else "darkgreen")
        )

        self.results_text.config(state="normal")
        self.results_text.insert(tk.END, f"{message}\n", tag)
        self.results_text.tag_config(
            "status", foreground="blue", font=("Consolas", 9, "italic")
        )
        self.results_text.tag_config(
            "result", foreground=color, font=("Consolas", 9, "bold")
        )
        self.results_text.see(tk.END)
        self.results_text.config(state="disabled")

    def _clear_results(self):
        """Clears the results text area before a new scan."""
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state="disabled")

    def _start_scan_thread(self):
        """Starts the scanning process in a separate thread to prevent GUI freezing."""
        target = self.input_entry.get().strip()
        if not target or target in [
            "e.g., https://example.com or http://192.168.1.1",
            "e.g., /var/www/html or C:\\xampp\\htdocs",
        ]:
            messagebox.showwarning(
                "Input Error", "Please enter a valid URL or local directory path."
            )
            return

        self.scan_button.config(state="disabled", text="Scanning...")
        self._clear_results()
        self._update_status(f"Starting scan for: {target}", "#ffa500")

        threading.Thread(target=self._run_scan, args=(target,), daemon=True).start()

    def _run_scan(self, target: str):
        """Main function to dispatch to the correct scanning logic based on mode."""
        try:
            mode = self.scan_mode.get()

            if mode == "Web":
                self._web_scan(target)
            elif mode == "Local":
                self._local_scan(target)

            self._update_status("Scan Complete.", "#4CAF50")
        except Exception as e:
            error_msg = f"CRITICAL ERROR: {type(e).__name__} - {str(e)}"
            self._update_status(error_msg, "red")
            self._log_result(error_msg)
        finally:
            self.scan_button.config(state="normal", text="Start Scan")

    def _web_scan(self, base_url: str):
        """
        Performs a Web URL scan for all defined targets. A file is 'EXPOSED'
        if the request returns 200 OK and has non-zero content.
        """
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            base_url = "http://" + base_url

        self._log_result(f"Starting Web Scan on base URL: {base_url}", is_status=True)
        found_count = 0

        for target_file in WEB_TARGETS:
            full_url = f"{base_url.rstrip('/')}{target_file}"
            self._update_status(f"Checking URL: {full_url}")

            try:
                response = requests.get(full_url, timeout=5, allow_redirects=False)

                if response.status_code == 200:
                    if len(response.content) > 0:
                        content_snippet = (
                            response.text[:MAX_SNIPPET_LENGTH]
                            .replace("\n", " ")
                            .strip()
                        )
                        if len(response.text) > MAX_SNIPPET_LENGTH:
                            content_snippet += "..."

                        self._log_result(
                            f'**EXPOSED** URL: {full_url}\n  -> Status: 200 OK | Snippet: "{content_snippet}"'
                        )
                        found_count += 1
                    else:
                        self._log_result(
                            f"Checked URL: {full_url} -> Status: 200 OK, but content is empty."
                        )
                elif response.status_code in [401, 403]:
                    self._log_result(
                        f"Checked URL: {full_url} -> Status: {response.status_code} (Restricted/Forbidden - Good!)"
                    )
                else:
                    self._log_result(
                        f"Checked URL: {full_url} -> Status: {response.status_code} (Not Found/Error)"
                    )

            except requests.exceptions.Timeout:
                self._log_result(
                    f"NETWORK ERROR on {full_url}: Request timed out (5s)."
                )
            except requests.exceptions.ConnectionError:
                self._log_result(
                    f"NETWORK ERROR on {full_url}: Host unreachable or refused connection."
                )
            except Exception as e:
                self._log_result(
                    f"UNEXPECTED ERROR on {full_url}: {type(e).__name__} - {str(e)}"
                )

        self._log_result(
            f"\nWeb Scan Finished. Found {found_count} potential exposure(s) among {len(WEB_TARGETS)} targets.",
            is_status=True,
        )

    def _local_scan(self, base_path: str):
        """
        Performs a recursive Local Directory scan for all defined sensitive patterns.
        Uses pathlib for robust file system operations.
        """
        path = pathlib.Path(base_path)

        self._log_result(
            f"Starting Local Scan on directory: {path.resolve()}", is_status=True
        )
        found_count = 0

        try:
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {base_path}")
            if not path.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {base_path}")

            for item in path.rglob("*"):
                if item.is_file():
                    self._update_status(f"Scanning file: {item.name}")

                    item_name_lower = item.name.lower()

                    is_match = False
                    matched_pattern = ""
                    for pattern in LOCAL_PATTERNS:
                        if pattern.lower() in item_name_lower:
                            is_match = True
                            matched_pattern = pattern
                            break

                    if is_match:
                        self._log_result(
                            f"**POTENTIAL EXPOSED** FILE: {item.resolve()}\n  -> WARNING: Matches sensitive pattern: '{matched_pattern}'"
                        )
                        found_count += 1

        except PermissionError:
            self._log_result(
                f"FILE SYSTEM ERROR: Permission denied for path: {base_path}",
                is_status=True,
            )
            self._update_status(
                "Scan Failed: Permission Denied. Run with elevated privileges?", "red"
            )
        except FileNotFoundError as e:
            self._log_result(f"FILE SYSTEM ERROR: {str(e)}", is_status=True)
            self._update_status("Scan Failed: Directory Not Found.", "red")
        except NotADirectoryError as e:
            self._log_result(f"FILE SYSTEM ERROR: {str(e)}", is_status=True)
            self._update_status("Scan Failed: Not a Directory.", "red")
        except Exception as e:
            self._log_result(
                f"UNEXPECTED ERROR during local scan: {str(e)}", is_status=True
            )
            self._update_status("Scan Failed: Unexpected Error.", "red")

        self._log_result(
            f"\nLocal Scan Finished. Found {found_count} potential exposure(s) matching patterns.",
            is_status=True,
        )


if __name__ == "__main__":
    app = CredentialExposureAuditor()
    app.mainloop()
