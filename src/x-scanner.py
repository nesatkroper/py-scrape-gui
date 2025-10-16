#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import os
import pathlib
import threading
from typing import List, Dict, Tuple, Optional
import re
import platform

APP_TITLE = "Credential Exposure Auditor 🛡️ (Advanced)"

WEB_TARGETS: List[str] = [
    "/.env",
    "/.env.example",
    "/config.json",
    "/wp-config.php",
    "/appsettings.json",
    "/appsettings.Development.json",
    "/appsettings.Production.json",
    "/web.config",
    "/package.json",
    "/package-lock.json",
    "/.next/static/_ssg/",
    "/storage/logs/laravel.log",
    "/.git/config",
    "/.svn/entries",
    "/.hg/hgrc",
    "/.bzr/branch/branch.conf",
    "/~.bash_history",
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
ENV_ROOT_PATTERNS = [".git", "public", "www", "htdocs", "web", "app", "src"]


class ModernCredentialAuditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x700")
        self.configure(bg="#1e1e2e")
        try:
            if platform.system() == "Windows":
                self.state("zoomed")
            else:
                self.attributes("-zoomed", True)
        except:
            self.geometry(
                f"{self.winfo_screenwidth() - 100}x{self.winfo_screenheight() - 100}"
            )
        self.scan_mode = tk.StringVar(value="Web")
        self.found_count = 0
        self.total_checked = 0
        self.style = ttk.Style()
        self._setup_modern_theme()
        self._setup_responsive_ui()

    def _setup_modern_theme(self):
        self.style.theme_use("clam")
        colors = {
            "bg": "#1e1e2e",
            "card": "#2a2a3e",
            "accent": "#89b4fa",
            "success": "#a6e3a1",
            "danger": "#f38ba8",
            "warning": "#f9e2af",
            "text": "#cdd6f4",
            "text_mute": "#6c7086",
        }
        self.style.configure("Modern.TFrame", background=colors["bg"])
        self.style.configure("Card.TFrame", background=colors["card"])
        self.style.configure(
            "Header.TLabel",
            background=colors["bg"],
            foreground=colors["accent"],
            font=("Segoe UI", 16, "bold"),
        )
        self.style.configure(
            "Title.TLabel",
            background=colors["card"],
            foreground=colors["text"],
            font=("Segoe UI", 12, "bold"),
        )
        self.style.configure(
            "Status.TLabel",
            background=colors["bg"],
            foreground=colors["text_mute"],
            font=("Segoe UI", 9),
        )

    def _setup_responsive_ui(self):
        main_container = ttk.Frame(self, style="Modern.TFrame")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        header_frame = ttk.Frame(main_container, style="Card.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        ttk.Label(header_frame, text=APP_TITLE, style="Header.TLabel").pack(pady=15)
        self._setup_control_panel(header_frame)
        results_frame = ttk.Frame(main_container, style="Card.TFrame")
        results_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        self._setup_results_area(results_frame)
        self._setup_status_bar(main_container)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        self._log_result("🚀 Ready to secure your environment!", is_status=True)

    def _setup_control_panel(self, parent):
        control_frame = ttk.LabelFrame(
            parent, text="Scan Controls", padding=15, style="Card.TFrame"
        )
        control_frame.pack(fill="x", padx=20, pady=(10, 0))
        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(mode_frame, text="Mode:", font=("Segoe UI", 10, "bold")).pack(
            side="left"
        )
        for text, value in [("🌐 Web URL", "Web"), ("📁 Local Dir", "Local")]:
            rb = ttk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.scan_mode,
                value=value,
                command=self._update_placeholder,
            )
            rb.pack(side="left", padx=10)
        input_frame = ttk.Frame(control_frame)
        input_frame.pack(fill="x")
        input_frame.columnconfigure(0, weight=1)
        self.input_entry = ttk.Entry(input_frame, font=("Consolas", 10))
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=0, column=1)
        self.scan_btn = ttk.Button(
            btn_frame,
            text="🚀 START SCAN",
            command=self._start_scan_thread,
            style="Accent.TButton",
        )
        self.scan_btn.pack(side="left", padx=(0, 5))
        clear_btn = ttk.Button(btn_frame, text="🗑️ CLEAR", command=self._clear_results)
        clear_btn.pack(side="left")
        self._update_placeholder()

    def _setup_results_area(self, parent):
        stats_frame = ttk.Frame(parent, style="Card.TFrame")
        stats_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 10))
        self.stats_label = ttk.Label(
            stats_frame, text="📊 Found: 0 | Checked: 0", font=("Segoe UI", 10, "bold")
        )
        self.stats_label.pack(side="left", padx=15, pady=8)
        progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            stats_frame, variable=progress_var, maximum=100, length=200
        )
        self.progress.pack(side="right", padx=15, pady=8)
        ttk.Label(parent, text="📋 Scan Results", style="Title.TLabel").grid(
            row=1, column=0, sticky="w", padx=15, pady=(0, 5)
        )
        text_frame = ttk.Frame(parent)
        text_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self.results_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            state="disabled",
            font=("Consolas", 10),
            bg="#1e1e2e",
            fg="#cdd6f4",
            insertbackground="#89b4fa",
            selectbackground="#45475a",
        )
        self.results_text.grid(row=0, column=0, sticky="nsew")
        self.results_text.tag_config(
            "status", foreground="#89b4fa", font=("Consolas", 10, "italic")
        )
        self.results_text.tag_config(
            "success", foreground="#a6e3a1", font=("Consolas", 10, "bold")
        )
        self.results_text.tag_config(
            "danger", foreground="#f38ba8", font=("Consolas", 10, "bold")
        )
        self.results_text.tag_config(
            "warning", foreground="#f9e2af", font=("Consolas", 10, "bold")
        )

    def _setup_status_bar(self, parent):
        status_frame = ttk.Frame(
            parent, style="Modern.TFrame", relief="solid", borderwidth=1
        )
        status_frame.grid(row=2, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="Ready to scan...")
        ttk.Label(
            status_frame, textvariable=self.status_var, style="Status.TLabel"
        ).pack(side="left", padx=10, pady=5)

    def _update_placeholder(self):
        mode = self.scan_mode.get()
        placeholder = "🌐 https://example.com" if mode == "Web" else "📁 /var/www/html"
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, placeholder)
        self.input_entry.config(
            foreground="#6c7086" if self.input_entry.get() == placeholder else "#cdd6f4"
        )

    def _update_stats(self):
        self.stats_label.config(
            text=f"📊 Found: {self.found_count} | Checked: {self.total_checked}"
        )
        progress = (
            self.total_checked
            / max(1, len(WEB_TARGETS) if self.scan_mode.get() == "Web" else 100)
        ) * 100
        self.progress["value"] = progress

    def _log_result(self, message: str, is_status: bool = False):
        tag = (
            "status"
            if is_status
            else (
                "danger"
                if "EXPOSED" in message
                else "success" if "Good" in message else "warning"
            )
        )
        self.results_text.config(state="normal")
        emoji = (
            "🔴"
            if "EXPOSED" in message
            else "✅" if "Good" in message else "⚠️" if is_status else "📄"
        )
        self.results_text.insert(tk.END, f"{emoji} {message}\n", tag)
        self.results_text.see(tk.END)
        self.results_text.config(state="disabled")

    def _clear_results(self):
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state="disabled")
        self.found_count = 0
        self.total_checked = 0
        self._update_stats()
        self._log_result("🧹 Results cleared!", is_status=True)

    def _start_scan_thread(self):
        target = self.input_entry.get().strip()
        placeholder = (
            "🌐 https://example.com"
            if self.scan_mode.get() == "Web"
            else "📁 /var/www/html"
        )
        if target == placeholder or not target:
            messagebox.showwarning("⚠️ Input Required", "Please enter a valid target!")
            return
        self.scan_btn.config(text="⏳ SCANNING...", state="disabled")
        self._clear_results()
        self._update_status(f"🚀 Starting scan: {target}")
        threading.Thread(target=self._run_scan, args=(target,), daemon=True).start()

    def _update_status(self, message: str, color: str = "#cdd6f4"):
        self.status_var.set(message)
        self.after(0, lambda: self.status_var.set(message))

    def _run_scan(self, target: str):
        try:
            if self.scan_mode.get() == "Web":
                self._web_scan(target)
            else:
                self._local_scan(target)
            self._update_status("✅ Scan Complete!", "#a6e3a1")
        except Exception as e:
            self._update_status(f"❌ ERROR: {str(e)}", "#f38ba8")
            self._log_result(f"CRITICAL ERROR: {str(e)}")
        finally:
            self.after(
                0, lambda: self.scan_btn.config(text="🚀 START SCAN", state="normal")
            )

    def _web_scan(self, base_url: str):
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        self._log_result(f"🌐 Web Scan: {base_url}", is_status=True)
        self.found_count = 0
        self.total_checked = 0
        for target_file in WEB_TARGETS:
            full_url = f"{base_url.rstrip('/')}{target_file}"
            self.total_checked += 1
            self.after(0, self._update_stats)
            try:
                response = requests.get(full_url, timeout=5, allow_redirects=False)
                if response.status_code == 200 and len(response.content) > 0:
                    snippet = self._get_snippet(response.text)
                    self._log_result(
                        f'🔴 EXPOSED: {full_url}\n   📝 Status: 200 | Preview: "{snippet}"'
                    )
                    self.found_count += 1
                elif response.status_code in [401, 403]:
                    self._log_result(
                        f"✅ SECURE: {full_url} -> {response.status_code} (Protected)"
                    )
                else:
                    self._log_result(f"📄 {full_url} -> {response.status_code}")
            except Exception as e:
                self._log_result(f"🌐 {full_url} -> Network Error: {str(e)[:50]}")
            self.after(0, self._update_stats)

    def _local_scan(self, base_path: str):
        path = pathlib.Path(base_path)
        self._log_result(f"📁 Local Scan: {path.resolve()}", is_status=True)
        self.found_count = 0
        self.total_checked = 0
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {base_path}")
        root_path = self._find_project_root(path)
        scan_path = root_path if root_path else path
        self._log_result(f"📂 Scanning from root: {scan_path}", is_status=True)
        for item in scan_path.rglob("*"):
            if item.is_file():
                self.total_checked += 1
                self.after(0, self._update_stats)
                if self._is_sensitive_file(item):
                    exposure_type = (
                        "🔴 CRITICAL" if ".env" in item.name else "⚠️ SENSITIVE"
                    )
                    self._log_result(
                        f"{exposure_type}: {item.resolve()}\n   📂 Root navigated from: {path}"
                    )
                    self.found_count += 1
        self._update_stats()

    def _find_project_root(self, path: pathlib.Path) -> Optional[pathlib.Path]:
        current = path
        max_depth = 5
        for _ in range(max_depth):
            if any(
                pattern in str(current.name).lower() for pattern in ENV_ROOT_PATTERNS
            ):
                for parent in [current.parent] + list(current.parents)[:3]:
                    env_path = parent / ".env"
                    if env_path.exists():
                        self._log_result(
                            f"🎯 Found .env in ROOT: {parent}", is_status=True
                        )
                        return parent
            current = current.parent
        self._log_result(
            f"⚠️ No .env found in parent directories from: {path}", is_status=True
        )
        return None

    def _is_sensitive_file(self, item: pathlib.Path) -> bool:
        return any(pattern.lower() in item.name.lower() for pattern in LOCAL_PATTERNS)

    def _get_snippet(self, text: str) -> str:
        snippet = text[:MAX_SNIPPET_LENGTH].replace("\n", " ").strip()
        return snippet + "..." if len(text) > MAX_SNIPPET_LENGTH else snippet


if __name__ == "__main__":
    app = ModernCredentialAuditor()
    app.mainloop()
