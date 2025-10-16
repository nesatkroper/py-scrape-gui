#!/home/nun/Desktop/Personal/py-scrape-gui/venv/bin/python3
"""
🌐 Smart IP Checker + My Info GUI (Modern Version)
Author: ChatGPT

Adds a "My Info" button to fetch:
 - Public IP (via api.ipify.org)
 - Geolocation for public IP (via ip-api.com)
 - Local LAN IP, hostname, OS, Python version

Notes:
 - Requires 'requests' (pip install requests)
 - Network calls run in a background thread to avoid blocking the GUI.
"""

import socket
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlparse
import re
import threading
import platform
import requests
import sys
import time
import webbrowser


def extract_domain(raw_input: str) -> str:
    """
    Extract domain from full URL or raw text.
    Examples:
      https://chat.openai.com/c/abc -> chat.openai.com
      www.example.com/path -> example.com
      example.com -> example.com
    """
    raw_input = raw_input.strip()
    if raw_input.startswith(("http://", "https://")):
        parsed = urlparse(raw_input)
        host = parsed.netloc or parsed.path.split("/")[0]
        if "@" in host:
            host = host.split("@")[-1]
        host = host.split(":")[0]
        return host
    s = raw_input
    s = re.sub(r"^https?://", "", s)
    s = re.sub(r"^www\.", "", s, flags=re.IGNORECASE)
    s = re.split(r"[/:]", s)[0]
    s = s.split(":")[0]
    return s


def resolve_domain(domain: str):
    """Return list of IP addresses for a domain, or an error message list."""
    try:
        if not domain:
            return ["❌ Empty domain input."]
        name, alias, addrs = socket.gethostbyname_ex(domain)
        if addrs:
            return addrs
        return [f"❌ No addresses found for {domain}"]
    except socket.gaierror as e:
        return [f"❌ Unable to resolve: {e}"]
    except Exception as e:
        return [f"⚠️ Error: {e}"]


def get_public_ip(timeout=6):
    """
    Returns public IP string or raises requests.RequestException/ValueError.
    Uses api.ipify.org (simple JSON).
    """
    url = "https://api.ipify.org?format=json"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("ip")


def get_geo_for_ip(ip: str, timeout=6):
    """
    Returns dict of geo info for an IP using ip-api.com (free, simple).
    Example response fields we use: country, regionName, city, isp, org
    """
    url = f"http://ip-api.com/json/{ip}"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data


def get_local_lan_ip():
    """
    Obtain local LAN IP by opening a UDP socket to an external IP (no data sent).
    This is a common trick to detect the local interface IP that would be used.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "Unknown"


def create_gui():
    root = tk.Tk()
    root.title("🌐 nun IP Checker + Info")
    root.geometry("450x540")
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
        pady=(12, 4)
    )
    ttk.Label(
        root, text="Enter domain or URL (auto extracts domain):", style="TLabel"
    ).pack()

    frame_input = tk.Frame(root, bg="#1e1e1e")
    frame_input.pack(pady=(10, 6))
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
        width=40,
    )
    entry.pack(ipady=8)
    entry.focus()
    entry.configure(
        highlightthickness=1, highlightcolor="#00ffff", highlightbackground="#333"
    )

    output_box = tk.Text(
        root,
        height=16,
        width=44,
        font=("Consolas", 11),
        bg="#1e1e1e",
        fg="#00ff88",
        relief="flat",
        wrap="word",
    )
    output_box.pack(padx=12, pady=(8, 6))
    output_box.config(state=tk.DISABLED)

    frame_btns = tk.Frame(root, bg="#1e1e1e")
    frame_btns.pack(pady=(4, 8))

    def threaded_task(fn, *args, **kwargs):
        t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
        t.start()

    def do_resolve():
        raw = domain_var.get().strip()
        clean = extract_domain(raw)
        if not clean:
            messagebox.showwarning(
                "Input Required", "Please enter a valid domain or URL."
            )
            return

        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, f"[INFO] Resolving {clean}...\n")
        output_box.config(state=tk.DISABLED)
        root.update()

        def worker():
            try:
                results = resolve_domain(clean)
                output_box.after(0, lambda: display_lines(results))
            except Exception as e:
                output_box.after(0, lambda: display_lines([f"⚠️ Error: {e}"]))

        threaded_task(worker)

    def do_clear():
        domain_var.set("")
        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.config(state=tk.DISABLED)

    def do_my_info():
        """
        Fetch public IP, geolocation, local IP, hostname, OS info.
        Runs in background thread.
        """
        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, "[INFO] Gathering public IP & device info...\n")
        output_box.config(state=tk.DISABLED)
        root.update()

        def worker():
            lines = []
            start = time.time()
            try:
                public_ip = get_public_ip(timeout=6)
                lines.append(f"Public IP: {public_ip}")
            except requests.RequestException as rexc:
                lines.append(f"Public IP: Error ({rexc.__class__.__name__}) - {rexc}")
                public_ip = None
            except Exception as e:
                lines.append(f"Public IP: Unexpected error - {e}")
                public_ip = None

            if public_ip:
                try:
                    geo = get_geo_for_ip(public_ip, timeout=6)
                    if isinstance(geo, dict) and geo.get("status") == "success":
                        c = geo.get("country", "N/A")
                        r = geo.get("regionName", "N/A")
                        city = geo.get("city", "N/A")
                        isp = geo.get("isp", "N/A")
                        org = geo.get("org", "N/A")
                        lines.append(f"Location: {city}, {r}, {c}")
                        lines.append(f"ISP / Org: {isp} / {org}")
                    else:
                        msg = (
                            geo.get("message", "unknown")
                            if isinstance(geo, dict)
                            else "unknown"
                        )
                        lines.append(f"Location: Unable to determine ({msg})")
                except requests.RequestException as rexc:
                    lines.append(
                        f"Location: Error fetching geo ({rexc.__class__.__name__}) - {rexc}"
                    )
                except Exception as e:
                    lines.append(f"Location: Unexpected error - {e}")
            else:
                lines.append("Location: Skipped (no public IP)")

            try:
                lan_ip = get_local_lan_ip()
                lines.append(f"Local LAN IP: {lan_ip}")
            except Exception:
                lines.append("Local LAN IP: Unknown")

            try:
                hostname = socket.gethostname()
                lines.append(f"Hostname: {hostname}")
            except Exception:
                lines.append("Hostname: Unknown")

            try:
                os_info = (
                    f"{platform.system()} {platform.release()} ({platform.machine()})"
                )
                lines.append(f"OS: {os_info}")
            except Exception:
                lines.append("OS: Unknown")

            try:
                pyv = platform.python_version()
                lines.append(f"Python: {pyv}")
            except Exception:
                lines.append("Python: Unknown")

            elapsed = time.time() - start
            lines.append(f"[Done in {elapsed:.2f}s]")

            output_box.after(0, lambda: display_lines(lines))

        threaded_task(worker)

    def display_lines(lines):
        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        for ln in lines:
            output_box.insert(tk.END, ln + "\n")
        output_box.config(state=tk.DISABLED)

    ttk.Button(
        frame_btns, text="Check IP", command=lambda: threaded_task(do_resolve), width=12
    ).pack(side="left", padx=8)
    ttk.Button(
        frame_btns, text="My Info", command=lambda: threaded_task(do_my_info), width=12
    ).pack(side="left", padx=8)
    ttk.Button(frame_btns, text="Clear", command=do_clear, width=12).pack(
        side="left", padx=8
    )

    # ttk.Label(
    #     root,
    #     text="Made with ❤️ by Dev.Nun | Auto-domain extraction enabled",
    #     font=("Segoe UI", 8, "italic"),
    #     foreground="#888",
    #     background="#1e1e1e",
    # ).pack(side=tk.BOTTOM, pady=(5, 5))

    def open_telegram(event=None):
        webbrowser.open_new("https://t.me/devphanun")

    frame = ttk.Frame(root)
    frame.pack(side=tk.BOTTOM, pady=(5, 5))

    ttk.Label(
        frame,
        text="Made with ❤️ by ",
        font=("Segoe UI", 8, "italic"),
        foreground="#888",
        background="#1e1e1e",
    ).pack(side=tk.LEFT)

    devnun_label = ttk.Label(
        frame,
        text="Dev.Nun",
        font=("Segoe UI", 8, "italic", "underline"),
        foreground="#61dafb",
        background="#1e1e1e",
        cursor="hand2",
    )
    devnun_label.pack(side=tk.LEFT)
    devnun_label.bind("<Button-1>", open_telegram)

    ttk.Label(
        frame,
        text=" | Auto-domain extraction enabled",
        font=("Segoe UI", 8, "italic"),
        foreground="#888",
        background="#1e1e1e",
    ).pack(side=tk.LEFT)

    root.mainloop()


if __name__ == "__main__":
    try:
        import requests
    except Exception:
        messagebox.showerror(
            "Missing dependency",
            "Please install the 'requests' library:\n\npip install requests",
        )
        sys.exit(1)
    create_gui()
