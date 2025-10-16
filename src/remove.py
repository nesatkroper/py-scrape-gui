#!/usr/bin/env python3
"""
🌐 Comment Remover GUI
Author: ChatGPT
Description:
    Remove comments from code, support multiple languages.
    Preserves color codes (#...) and URLs (http://, https://).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re

LINE_COMMENT_PATTERNS = [
    r"//.*",
    r"#.*",
    r";.*",
    r"--.*",
]

BLOCK_COMMENT_PATTERNS = [
    r"/\*[\s\S]*?\*/",
    r"<!--[\s\S]*?-->",
    r"{-.*?-}",
]

URL_PATTERN = r"https?://[^\s]+"
COLOR_PATTERN = r"#(?:[0-9a-fA-F]{3}){1,2}\b"


def remove_comments(code_text):
    """
    Removes comments from code but keeps URLs and color codes.
    """
    preserved = {}

    def preserve_match(m):
        key = f"__PRESERVE_{len(preserved)}__"
        preserved[key] = m.group(0)
        return key

    code_text = re.sub(URL_PATTERN, preserve_match, code_text)
    code_text = re.sub(COLOR_PATTERN, preserve_match, code_text)

    for pattern in BLOCK_COMMENT_PATTERNS:
        code_text = re.sub(pattern, "", code_text, flags=re.MULTILINE)

    for pattern in LINE_COMMENT_PATTERNS:
        code_text = re.sub(pattern, "", code_text, flags=re.MULTILINE)

    for key, val in preserved.items():
        code_text = code_text.replace(key, val)

    code_text = re.sub(r"\n\s*\n", "\n", code_text)
    return code_text.strip()


def create_gui():
    root = tk.Tk()
    root.title("💻 Comment Remover GUI")
    root.geometry("700x650")
    root.configure(bg="#1e1e1e")
    root.resizable(True, True)

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

    ttk.Label(root, text="💻 Comment Remover GUI", style="Header.TLabel").pack(
        pady=(12, 5)
    )
    ttk.Label(root, text="Paste your code below:", style="TLabel").pack()

    input_box = tk.Text(
        root,
        height=12,
        font=("Consolas", 11),
        bg="#1e1e1e",
        fg="#00ff88",
        insertbackground="#00ff88",
        wrap="word",
    )
    input_box.pack(padx=12, pady=(6, 4), fill="both", expand=True)

    output_box = tk.Text(
        root,
        height=12,
        font=("Consolas", 11),
        bg="#1e1e1e",
        fg="#00ff88",
        insertbackground="#00ff88",
        wrap="word",
    )
    output_box.pack(padx=12, pady=(4, 6), fill="both", expand=True)
    output_box.config(state=tk.DISABLED)

    frame_btns = tk.Frame(root, bg="#1e1e1e")
    frame_btns.pack(pady=(4, 10))

    def do_remove():
        code = input_box.get("1.0", tk.END)
        if not code.strip():
            messagebox.showwarning("Empty Input", "Please paste some code first!")
            return
        result = remove_comments(code)
        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, result)
        output_box.config(state=tk.DISABLED)

    def do_clear():
        input_box.delete("1.0", tk.END)
        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.config(state=tk.DISABLED)

    def do_load_file():
        file_path = filedialog.askopenfilename(
            title="Open Code File", filetypes=[("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            input_box.delete("1.0", tk.END)
            input_box.insert(tk.END, content)

    ttk.Button(frame_btns, text="Remove Comments", command=do_remove, width=16).pack(
        side="left", padx=6
    )
    ttk.Button(frame_btns, text="Clear", command=do_clear, width=10).pack(
        side="left", padx=6
    )
    ttk.Button(frame_btns, text="Load File", command=do_load_file, width=10).pack(
        side="left", padx=6
    )

    root.mainloop()


if __name__ == "__main__":
    create_gui()
