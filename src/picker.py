import tkinter as tk
from tkinter import ttk
import webbrowser
import sys
from PIL import ImageGrab, ImageTk, Image


def rgb_to_hex(rgb):
    """Converts an RGB tuple to a hexadecimal color string."""
    try:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}".upper()
    except:
        return "#000000"


def get_pixel_color(x, y):
    """Captures a single pixel color from the screen using Pillow."""
    try:
        img = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
        rgb = img.getpixel((0, 0))
        return rgb
    except Exception as e:
        print(f"Error capturing pixel: {e}", file=sys.stderr)
        return (0, 0, 0)


class ColorPickerApp:
    def __init__(self, master):
        self.master = master
        master.title("Nun Color Picker")
        master.geometry("350x500")
        master.minsize(350, 400)
        master.configure(bg="#2c3e50")

        self.picking_mode = False
        self.current_rgb = (0, 0, 0)
        self.current_hex = "#000000"
        self.saved_colors = []
        self.after_id = None
        self.tk_image = None

        self.MAGNIFIER_SIZE = 150
        self.mag_capture_size = 21

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#2c3e50")
        style.configure(
            "TLabel",
            background="#2c3e50",
            foreground="#ecf0f1",
            font=("Inter", 12),
            padding=0,
        )
        style.configure(
            "TButton",
            background="#3498db",
            foreground="white",
            font=("Inter", 11, "bold"),
            borderwidth=0,
            padding=10,
        )
        style.map("TButton", background=[("active", "#2980b9")])

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=0)
        master.grid_rowconfigure(2, weight=2)
        master.grid_rowconfigure(3, weight=0)

        self.live_view_frame = ttk.Frame(master, style="TFrame", padding="15")
        self.live_view_frame.grid(row=0, column=0, sticky="nsew")
        self.live_view_frame.grid_columnconfigure(0, weight=1)
        self.live_view_frame.grid_rowconfigure(0, weight=1)

        self.color_box = tk.Canvas(
            self.live_view_frame, bg="#000000", height=80, bd=0, highlightthickness=0
        )
        self.color_box.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 5))

        self.results_frame = ttk.Frame(self.live_view_frame, style="TFrame")
        self.results_frame.grid(row=1, column=0, sticky="ew")
        self.results_frame.columnconfigure(0, weight=1)

        self.hex_label = ttk.Label(
            self.results_frame, text="HEX: #000000", font=("Inter", 14, "bold")
        )
        self.hex_label.pack(side=tk.LEFT, padx=10)
        self.rgb_label = ttk.Label(
            self.results_frame, text="RGB: (0, 0, 0)", font=("Inter", 12)
        )
        self.rgb_label.pack(side=tk.LEFT, padx=10)

        self.pick_button = ttk.Button(
            master, text="🎨 Start Picking (Ctrl+C to Save)", command=self.start_picking
        )
        self.pick_button.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        ttk.Label(
            master,
            text="Saved Colors (Click to Copy)",
            font=("Inter", 10, "bold"),
            anchor=tk.W,
            foreground="#bdc3c7",
            background="#34495e",
        ).grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 0))

        self.saved_frame = ttk.Frame(master, style="TFrame", padding="0")
        self.saved_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 10))
        self.saved_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.saved_frame, bg="#34495e", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(
            self.saved_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.saved_list_container = ttk.Frame(self.canvas, style="TFrame", padding=0)
        self.canvas.create_window(
            (0, 0), window=self.saved_list_container, anchor="nw", width=400
        )
        self.saved_list_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.saved_list_container.grid_columnconfigure(0, weight=1)

        self.status_bar = ttk.Label(
            master,
            text="Ready",
            foreground="#bdc3c7",
            background="#2c3e50",
            anchor=tk.W,
            font=("Inter", 10),
        )
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 5))

        credit_label = ttk.Label(
            master,
            text="Credit: devphanun (Telegram)",
            foreground="#7f8c8d",
            font=("Inter", 9),
            cursor="hand2",
            anchor=tk.E,
            background="#2c3e50",
        )
        credit_label.grid(row=4, column=0, padx=15, pady=(0, 5), sticky="ew")
        credit_label.bind("<Button-1>", self.open_credit_link)

        self.update_ui()
        self.update_saved_colors_ui()

    def open_credit_link(self, event):
        """Opens the developer's telegram link in the default browser."""
        webbrowser.open_new_tab("https://t.me/devphanun")

    def copy_to_clipboard(self, text):
        """Copies text to the system clipboard."""
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        self.status_bar.config(text=f"Copied: {text} to clipboard.")
        self.master.after(2000, lambda: self.status_bar.config(text="Ready"))

    def update_ui(self):
        """Updates the live color box and labels."""
        self.color_box.config(bg=self.current_hex)
        self.hex_label.config(text=f"HEX: {self.current_hex}")
        self.rgb_label.config(text=f"RGB: {self.current_rgb}")

    def update_saved_colors_ui(self):
        """Rebuilds the list of saved colors."""
        for widget in self.saved_list_container.winfo_children():
            widget.destroy()

        if not self.saved_colors:
            ttk.Label(
                self.saved_list_container,
                text="Ctrl+C for picking.",
                foreground="#7f8c8d",
                background="#34495e",
                padding=8,
            ).pack(fill="x")
            return

        for i, (hex_code, rgb_str) in enumerate(reversed(self.saved_colors)):

            row_frame = ttk.Frame(
                self.saved_list_container, style="TFrame", padding="5 10 5 10"
            )
            row_frame.pack(fill="x", padx=5, pady=2)
            row_frame.grid_columnconfigure(1, weight=1)

            swatch = tk.Canvas(
                row_frame, bg=hex_code, width=15, height=15, bd=0, highlightthickness=0
            )
            swatch.grid(row=0, column=0, padx=(5, 10), sticky="ns")

            text_label = ttk.Label(
                row_frame,
                text=f"{hex_code} | {rgb_str}",
                font=("Inter", 11, "bold"),
                foreground="#ecf0f1",
                background="#34495e",
                cursor="hand2",
            )
            text_label.grid(row=0, column=1, sticky="w")

            text_label.bind(
                "<Button-1>", lambda e, h=hex_code: self.copy_to_clipboard(h)
            )
            swatch.bind("<Button-1>", lambda e, h=hex_code: self.copy_to_clipboard(h))

            ttk.Separator(self.saved_list_container, orient="horizontal").pack(fill="x")

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def start_picking(self):
        """Initiates the color picking mode with live zoom and key bindings."""
        if self.picking_mode:
            self.stop_picking()
            return

        self.picking_mode = True
        self.pick_button.config(text="❌ Stop Picking (Esc) - Use Ctrl+C to Save")

        self.master.bind("<Escape>", lambda e: self.stop_picking())
        self.master.bind("<Control-c>", lambda e: self.select_color())
        self.master.bind("<Control-C>", lambda e: self.select_color())

        self.magnifier = tk.Toplevel(self.master)
        self.magnifier.overrideredirect(True)
        self.magnifier.geometry(f"{self.MAGNIFIER_SIZE + 2}x{self.MAGNIFIER_SIZE + 35}")
        self.magnifier.attributes("-topmost", True)

        try:
            self.magnifier.attributes("-alpha", 0.95)
        except tk.TclError:
            pass

        self.mag_canvas = tk.Canvas(
            self.magnifier,
            width=self.MAGNIFIER_SIZE,
            height=self.MAGNIFIER_SIZE,
            bg="gray",
            bd=1,
            relief=tk.SOLID,
        )
        self.mag_canvas.pack(padx=1, pady=(1, 0))

        self.mag_label = ttk.Label(
            self.magnifier,
            text="Press Ctrl+C to Save",
            background="#2c3e50",
            foreground="#ecf0f1",
            font=("Inter", 9, "bold"),
        )
        self.mag_label.pack(fill="x", padx=1, pady=(0, 1))

        self.poll_mouse()

    def select_color(self, event=None):
        """Saves the current live color to the list (triggered by Ctrl+C)."""
        if not self.picking_mode:
            return

        color_tuple = (self.current_hex, str(self.current_rgb))
        self.saved_colors.append(color_tuple)

        self.update_saved_colors_ui()

        self.copy_to_clipboard(self.current_hex)
        self.status_bar.config(
            text=f"Color saved and HEX code copied: {self.current_hex}"
        )

    def poll_mouse(self):
        """Continuously checks mouse position and updates the magnifier with zoom."""
        if not self.picking_mode:
            return

        x, y = self.master.winfo_pointerx(), self.master.winfo_pointery()

        self.magnifier.geometry(f"+{x + 20}+{y + 20}")

        capture_half = self.mag_capture_size // 2
        x1 = x - capture_half
        y1 = y - capture_half
        x2 = x + capture_half
        y2 = y + capture_half

        try:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            center_index = self.mag_capture_size // 2
            rgb = img.getpixel((center_index, center_index))
            hex_code = rgb_to_hex(rgb)

            self.current_rgb = rgb
            self.current_hex = hex_code
            self.update_ui()

            img_magnified = img.resize(
                (self.MAGNIFIER_SIZE, self.MAGNIFIER_SIZE),
                resample=Image.Resampling.NEAREST,
            )
            self.tk_image = ImageTk.PhotoImage(img_magnified)

            self.mag_canvas.delete("all")
            self.mag_canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

            center = self.MAGNIFIER_SIZE // 2
            cross_color = "white" if sum(rgb) < 382 else "black"
            self.mag_canvas.create_line(
                center, 0, center, self.MAGNIFIER_SIZE, fill=cross_color, width=1
            )
            self.mag_canvas.create_line(
                0, center, self.MAGNIFIER_SIZE, center, fill=cross_color, width=1
            )

            self.mag_label.config(
                text=f"{hex_code} | {rgb}",
                background=hex_code,
                foreground="white" if sum(rgb) < 382 else "black",
            )

        except Exception as e:
            self.mag_label.config(text=f"Error")
            print(f"Polling error: {e}", file=sys.stderr)
            pass

        self.after_id = self.master.after(50, self.poll_mouse)

    def stop_picking(self, event=None):
        """Stops the picking mode and cleans up resources (triggered by Esc or button)."""
        if not self.picking_mode:
            return

        self.master.unbind("<Escape>")
        self.master.unbind("<Control-c>")
        self.master.unbind("<Control-C>")

        self.picking_mode = False

        if self.after_id:
            self.master.after_cancel(self.after_id)
            self.after_id = None

        if hasattr(self, "magnifier") and self.magnifier:
            self.magnifier.destroy()

        self.tk_image = None

        self.pick_button.config(text="🎨 Start Picking (Ctrl+C to Save)")
        self.status_bar.config(text="Picking mode stopped.")


def main():
    root = tk.Tk()
    if sys.platform.startswith("win"):
        default_font = ("Segoe UI", 12)
    else:
        default_font = ("Helvetica", 12)

    try:
        root.option_add("*Font", default_font)
    except tk.TclError:
        pass

    app = ColorPickerApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    root.mainloop()


if __name__ == "__main__":
    main()
