import customtkinter as ctk
from tkinter import messagebox
import psutil
import threading
import time
import speedtest
import webbrowser

ACCENT_COLOR = "#1f6aa5"
WINDOW_BG_DARK = "#242424"


class SystemMonitorApp(ctk.CTk):
    """
    A customtkinter-based GUI application for monitoring system usage and
    testing internet speed, featuring a minimal, modern, and interactive UI.
    """

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("Minimal System & Network Monitor")
        self.geometry("500x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.monitoring_active = True
        self.net_io_before = psutil.net_io_counters()
        self.progress_bars = {}
        self.labels = {}

        self.setup_ui()

        self.after(100, self.update_system_metrics)

    def open_telegram_link(self):
        """Opens the developer's Telegram link in the default web browser."""
        try:
            webbrowser.open_new("https://t.me/devphanun")
        except Exception as e:
            print(f"Failed to open link: {e}")

    def setup_ui(self):

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text="System Resource Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT_COLOR,
        ).grid(row=0, column=0, sticky="w")

        monitor_card = ctk.CTkFrame(self, corner_radius=10)
        monitor_card.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        monitor_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            monitor_card,
            text="Hardware & Network Usage",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        metrics = [
            ("CPU Usage", ACCENT_COLOR),
            ("RAM Usage", "green"),
            ("Disk Usage", "orange"),
        ]
        for i, (metric, color) in enumerate(metrics):

            label = ctk.CTkLabel(
                monitor_card, text=f"{metric}: 0.0%", font=ctk.CTkFont(size=14)
            )
            label.grid(row=i * 2 + 1, column=0, padx=20, pady=(10, 5), sticky="w")
            self.labels[metric] = label

            progress = ctk.CTkProgressBar(
                monitor_card,
                orientation="horizontal",
                mode="determinate",
                height=15,
                corner_radius=5,
                progress_color=color,
            )
            progress.grid(row=i * 2 + 2, column=0, padx=20, pady=(0, 10), sticky="ew")
            progress.set(0)
            self.progress_bars[metric] = progress

        net_frame = ctk.CTkFrame(monitor_card, fg_color="transparent")
        net_frame.grid(row=9, column=0, padx=20, pady=(10, 20), sticky="ew")
        net_frame.grid_columnconfigure((0, 1), weight=1)

        self.labels["Net Download"] = ctk.CTkLabel(
            net_frame, text="Download: 0.00 KB/s", font=ctk.CTkFont(size=14)
        )
        self.labels["Net Download"].grid(row=0, column=0, sticky="w")

        self.labels["Net Upload"] = ctk.CTkLabel(
            net_frame, text="Upload: 0.00 KB/s", font=ctk.CTkFont(size=14)
        )
        self.labels["Net Upload"].grid(row=0, column=1, sticky="e")

        speed_card = ctk.CTkFrame(self, corner_radius=10)
        speed_card.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        speed_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            speed_card,
            text="Internet Speed Test",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.speed_test_button = ctk.CTkButton(
            speed_card,
            text="Run Speed Test (Mbps)",
            command=self.trigger_speed_test,
            fg_color=ACCENT_COLOR,
            hover_color="#185685",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.speed_test_button.grid(
            row=1, column=0, padx=40, pady=(10, 10), sticky="ew"
        )

        self.speed_results = ctk.CTkLabel(
            speed_card,
            text="Ready to test internet bandwidth.",
            font=ctk.CTkFont(size=14),
            justify="center",
            height=60,
        )
        self.speed_results.grid(row=2, column=0, padx=40, pady=(10, 20), sticky="ew")

        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        credit_button = ctk.CTkButton(
            footer_frame,
            text="Developed by devphanun (Telegram)",
            command=self.open_telegram_link,
            font=ctk.CTkFont(size=12, underline=True),
            text_color="#888888",
            fg_color="transparent",
            hover_color=WINDOW_BG_DARK,
            width=1,
        )
        credit_button.grid(row=0, column=0, sticky="e")

    def format_bytes(self, bytes_val, suffix="/s"):
        """Converts bytes to a human-readable format (e.g., KB/s, MB/s)."""
        if bytes_val is None:
            return f"0.00 KB{suffix}"

        for unit in ["", "K", "M", "G", "T"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:5.2f} {unit}B{suffix}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} P B{suffix}"

    def update_system_metrics(self):
        """Fetches and updates system metrics and network I/O.
        This function calls itself recursively every 1000ms using self.after().
        """
        if not self.monitoring_active:
            return

        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            ram_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage("/").percent

            self.labels["CPU Usage"].configure(text=f"CPU Usage: {cpu_percent:.1f}%")
            self.progress_bars["CPU Usage"].set(cpu_percent / 100)

            self.labels["RAM Usage"].configure(text=f"RAM Usage: {ram_percent:.1f}%")
            self.progress_bars["RAM Usage"].set(ram_percent / 100)

            self.labels["Disk Usage"].configure(text=f"Disk Usage: {disk_percent:.1f}%")
            self.progress_bars["Disk Usage"].set(disk_percent / 100)

            net_io_after = psutil.net_io_counters()

            bytes_sent_delta = net_io_after.bytes_sent - self.net_io_before.bytes_sent
            bytes_recv_delta = net_io_after.bytes_recv - self.net_io_before.bytes_recv

            self.labels["Net Download"].configure(
                text=f"Download: {self.format_bytes(bytes_recv_delta)}"
            )
            self.labels["Net Upload"].configure(
                text=f"Upload: {self.format_bytes(bytes_sent_delta)}"
            )

            self.net_io_before = net_io_after

        except Exception as e:
            print(f"Error updating metrics: {e}")

        self.after(1000, self.update_system_metrics)

    def trigger_speed_test(self):
        """Starts the internet speed test in a new thread to avoid freezing the GUI."""
        self.speed_test_button.configure(
            state="disabled", text="Testing... Finding Server."
        )
        self.speed_results.configure(
            text="Status: Starting Speed Test...", text_color="#FFFFFF"
        )

        test_thread = threading.Thread(target=self.run_speed_test, daemon=True)
        test_thread.start()

    def run_speed_test(self):
        """Performs the actual speed test using the speedtest library."""
        try:
            st = speedtest.Speedtest()

            self.after(
                0,
                lambda: self.speed_test_button.configure(
                    text="Testing... Finding Optimal Server."
                ),
            )
            st.get_best_server()

            self.after(
                0,
                lambda: self.speed_test_button.configure(
                    text="Testing... Running Download Test."
                ),
            )
            download_speed = st.download()

            self.after(
                0,
                lambda: self.speed_test_button.configure(
                    text="Testing... Running Upload Test."
                ),
            )
            upload_speed = st.upload()

            download_mbps = download_speed / 1024 / 1024
            upload_mbps = upload_speed / 1024 / 1024

            result_text = (
                f"Download: {download_mbps:.2f} Mbps\n"
                f"Upload: {upload_mbps:.2f} Mbps\n"
                f"Ping: {st.results.ping:.2f} ms"
            )

            self.after(
                0,
                lambda: self.speed_results.configure(
                    text=result_text, text_color="#4CAF50"
                ),
            )

        except Exception as e:
            error_message = (
                f"Speed Test Error: Could not connect or failed.\nDetails: {e}"
            )
            self.after(
                0,
                lambda: self.speed_results.configure(
                    text=error_message, text_color="#FF6347"
                ),
            )

        finally:
            self.after(
                0,
                lambda: self.speed_test_button.configure(
                    state="normal", text="Run Speed Test (Mbps)"
                ),
            )

    def on_closing(self):
        """Handles application closing by stopping the monitoring flag."""
        self.monitoring_active = False
        self.destroy()


if __name__ == "__main__":
    app = SystemMonitorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
