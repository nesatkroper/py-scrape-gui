#!/usr/bin/env python3
"""
🌐 Smart IP Checker GUI (Modern Version)
Author: ChatGPT
Description:
    A stylish dark GUI tool to resolve domains to IP addresses.
    Auto-corrects full URLs and extracts domains automatically.
"""

import socket
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlparse
import re


def extract_domain(raw_input: str) -> str:
    """
    Extract a clean domain name from a full URL or text.
    Examples:
      https://chat.openai.com/c/abc -> chat.openai.com
      www.example.com/path -> www.example.com
      example.com -> example.com
    """
    raw_input = raw_input.strip()

    if raw_input.startswith(("http://", "https://")):
        parsed = urlparse(raw_input)
        return parsed.netloc or parsed.path.split("/")[0]

    raw_input = re.sub(r"^www\.", "", raw_input)
    raw_input = re.split(r"[/:]", raw_input)[0]
    return raw_input


def resolve_domain(domain: str):
    """Return list of IP addresses for a domain, or error message."""
    try:
        if not domain:
            return ["❌ Empty domain input."]
        name, alias, addrs = socket.gethostbyname_ex(domain)
        return addrs
    except socket.gaierror as e:
        return [f"❌ Unable to resolve: {e}"]
    except Exception as e:
        return [f"⚠️ Error: {e}"]


def create_gui():
    root = tk.Tk()
    root.title("🌐 Smart IP Checker - dig +short")
    root.geometry("400x350")
    root.configure(bg="#1e1e1e")
    root.resizable(False, False)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        "TLabel", background="#1e1e1e", foreground="#dcdcdc", font=("Segoe UI", 10)
    )
    style.configure(
        "Header.TLabel",
        font=("Segoe UI", 15, "bold"),
        foreground="#00ffff",
        background="#1e1e1e",
    )
    style.configure(
        "TButton",
        background="#0078d7",
        foreground="#ffffff",
        font=("Segoe UI", 10, "bold"),
        padding=6,
    )
    style.map("TButton", background=[("active", "#0098ff"), ("pressed", "#005b99")])

    ttk.Label(root, text="🌐 Smart IP Checker", style="Header.TLabel").pack(
        pady=(15, 5)
    )
    ttk.Label(
        root, text="Enter domain or URL (auto extracts domain):", style="TLabel"
    ).pack()

    frame_input = tk.Frame(root, bg="#1e1e1e")
    frame_input.pack(pady=(10, 5))

    domain_var = tk.StringVar()
    entry = tk.Entry(
        frame_input,
        textvariable=domain_var,
        font=("Consolas", 12),
        bg="#2d2d2d",
        fg="#00ff88",
        insertbackground="#00ff88",
        relief="flat",
        justify="center",
        width=35,
    )
    entry.pack(ipady=8)
    entry.focus()

    entry.configure(
        highlightthickness=1, highlightcolor="#00ffff", highlightbackground="#333"
    )

    output_box = tk.Text(
        root,
        height=6,
        width=39,
        font=("Consolas", 11),
        bg="#1e1e1e",
        fg="#00ff88",
        relief="flat",
        wrap="word",
    )
    output_box.pack(pady=(10, 5))
    output_box.config(state=tk.DISABLED)

    frame_btns = tk.Frame(root, bg="#1e1e1e")
    frame_btns.pack(pady=(5, 10))

    def on_check():
        raw = domain_var.get().strip()
        clean_domain = extract_domain(raw)

        if not clean_domain:
            messagebox.showwarning(
                "Input Required", "Please enter a valid domain or URL."
            )
            return

        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, f"[INFO] Resolving {clean_domain}...\n")
        output_box.config(state=tk.DISABLED)
        root.update()

        results = resolve_domain(clean_domain)

        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        for line in results:
            output_box.insert(tk.END, f"{line}\n")
        output_box.config(state=tk.DISABLED)

    def on_clear():
        domain_var.set("")
        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.config(state=tk.DISABLED)

    ttk.Button(frame_btns, text="Check IP", command=on_check, width=15).pack(
        side="left", padx=10
    )
    ttk.Button(frame_btns, text="Clear", command=on_clear, width=15).pack(
        side="left", padx=10
    )

    ttk.Label(
        root,
        text="Made with ❤️ by ChatGPT | Auto-domain extraction enabled",
        font=("Segoe UI", 8, "italic"),
        foreground="#888",
        background="#1e1e1e",
    ).pack(side=tk.BOTTOM, pady=(5, 5))

    root.mainloop()


if __name__ == "__main__":
    create_gui()
