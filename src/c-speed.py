import tkinter as tk
from tkinter import ttk
import psutil
import speedtest
import threading
import webbrowser


# ----- Styling -----
def apply_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", font=("Segoe UI", 12))
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
    style.configure(
        "TButton", font=("Segoe UI", 12), foreground="#ffffff", background="#0078D7"
    )
    style.map(
        "TButton",
        foreground=[("pressed", "#ffffff"), ("active", "#ffffff")],
        background=[("pressed", "#005A9E"), ("active", "#005A9E")],
    )


# ----- Main App -----
class ModernMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System & Internet Monitor")
        self.root.geometry("450x550")
        self.root.configure(bg="#f4f4f4")
        self.root.resizable(True, True)

        apply_style()

        # Title
        self.title_label = ttk.Label(
            root,
            text="System & Internet Monitor",
            style="Title.TLabel",
            background="#f4f4f4",
        )
        self.title_label.pack(pady=15)

        # Stats Frame
        self.stats_frame = ttk.Frame(root)
        self.stats_frame.pack(pady=10, fill="x", padx=20)

        self.cpu_label = ttk.Label(self.stats_frame, text="CPU Usage: 0%")
        self.cpu_label.pack(pady=8, anchor="w")

        self.ram_label = ttk.Label(self.stats_frame, text="RAM Usage: 0%")
        self.ram_label.pack(pady=8, anchor="w")

        self.disk_label = ttk.Label(self.stats_frame, text="Disk Usage: 0%")
        self.disk_label.pack(pady=8, anchor="w")

        self.net_label = ttk.Label(
            self.stats_frame, text="Network: 0 KB/s up / 0 KB/s down"
        )
        self.net_label.pack(pady=8, anchor="w")

        # Speed Test
        self.speed_button = ttk.Button(
            root, text="Test Internet Speed", command=self.run_speed_test
        )
        self.speed_button.pack(pady=20, ipadx=10, ipady=5)

        self.speed_label = ttk.Label(root, text="", background="#f4f4f4")
        self.speed_label.pack(pady=10)

        # Clickable Credit
        self.credit_label = tk.Label(
            root,
            text="Developed by @devphanun",
            fg="#0078D7",
            bg="#f4f4f4",
            font=("Segoe UI", 10, "italic"),
            cursor="hand2",
        )
        self.credit_label.pack(side="bottom", pady=10)
        self.credit_label.bind(
            "<Button-1>", lambda e: webbrowser.open_new("https://t.me/devphanun")
        )

        # Network previous values
        self.previous_bytes_sent = psutil.net_io_counters().bytes_sent
        self.previous_bytes_recv = psutil.net_io_counters().bytes_recv

        # Start monitoring
        self.update_stats()

    def update_stats(self):
        # CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        self.cpu_label.config(text=f"CPU Usage: {cpu_usage}%")

        # RAM
        ram_usage = psutil.virtual_memory().percent
        self.ram_label.config(text=f"RAM Usage: {ram_usage}%")

        # Disk
        disk_usage = psutil.disk_usage("/").percent
        self.disk_label.config(text=f"Disk Usage: {disk_usage}%")

        # Network speed
        current_bytes_sent = psutil.net_io_counters().bytes_sent
        current_bytes_recv = psutil.net_io_counters().bytes_recv
        up_speed = (current_bytes_sent - self.previous_bytes_sent) / 1024
        down_speed = (current_bytes_recv - self.previous_bytes_recv) / 1024
        self.previous_bytes_sent = current_bytes_sent
        self.previous_bytes_recv = current_bytes_recv
        self.net_label.config(
            text=f"Network: {up_speed:.2f} KB/s up / {down_speed:.2f} KB/s down"
        )

        self.root.after(1000, self.update_stats)

    def run_speed_test(self):
        def test():
            self.speed_label.config(text="Testing...")
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Mbps
            upload_speed = st.upload() / 1_000_000
            ping = st.results.ping
            self.speed_label.config(
                text=f"Download: {download_speed:.2f} Mbps\nUpload: {upload_speed:.2f} Mbps\nPing: {ping} ms"
            )

        threading.Thread(target=test).start()


# ----- Run App -----
if __name__ == "__main__":
    root = tk.Tk()
    app = ModernMonitorApp(root)
    root.mainloop()
