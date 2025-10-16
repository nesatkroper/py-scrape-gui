import tkinter as tk
from tkinter import ttk, messagebox
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
        master.title("Live Screen Color Picker")
        master.geometry("400x350")
        master.minsize(300, 250)
        master.configure(bg="#2c3e50")

        self.picking_mode = False
        self.current_rgb = (0, 0, 0)
        self.current_hex = "#000000"
        self.after_id = None
        self.tk_image = None

        self.MAGNIFIER_SIZE = 200
        self.mag_zoom_level = 10
        self.mag_capture_size = 21

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=0)
        master.grid_rowconfigure(2, weight=0)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#2c3e50")
        style.configure(
            "TLabel", background="#2c3e50", foreground="#ecf0f1", font=("Inter", 12)
        )
        style.configure(
            "TButton",
            background="#3498db",
            foreground="white",
            font=("Inter", 12, "bold"),
            borderwidth=0,
            padding=10,
        )
        style.map("TButton", background=[("active", "#2980b9")])

        self.color_display_frame = ttk.Frame(
            master, style="TFrame", padding="20 10 20 10"
        )
        self.color_display_frame.grid(row=0, column=0, sticky="nsew")
        self.color_display_frame.grid_columnconfigure(0, weight=1)
        self.color_display_frame.grid_rowconfigure(0, weight=1)

        self.color_box = tk.Canvas(
            self.color_display_frame,
            bg="#000000",
            height=100,
            bd=0,
            highlightthickness=0,
            relief=tk.RAISED,
        )
        self.color_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.results_frame = ttk.Frame(self.color_display_frame, style="TFrame")
        self.results_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.results_frame, text="HEX:", font=("Inter", 10, "bold")).grid(
            row=0, column=0, padx=5, pady=2, sticky="e"
        )
        self.hex_label = ttk.Label(
            self.results_frame, text=self.current_hex, font=("Inter", 14)
        )
        self.hex_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(self.results_frame, text="RGB:", font=("Inter", 10, "bold")).grid(
            row=1, column=0, padx=5, pady=2, sticky="e"
        )
        self.rgb_label = ttk.Label(
            self.results_frame, text=str(self.current_rgb), font=("Inter", 14)
        )
        self.rgb_label.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        self.pick_button = ttk.Button(
            master,
            text="🎨 Start Picking (Ctrl+C to select)",
            command=self.start_picking,
        )
        self.pick_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        credit_label = ttk.Label(
            master,
            text="Credit: devphanun (telegram)",
            foreground="#7f8c8d",
            font=("Inter", 9),
            cursor="hand2",
        )
        credit_label.grid(row=2, column=0, padx=5, pady=5, sticky="s")
        credit_label.bind("<Button-1>", self.open_credit_link)

        self.update_ui()

    def open_credit_link(self, event):
        """Opens the developer's telegram link in the default browser."""
        webbrowser.open_new_tab("https://t.me/devphanun")

    def update_ui(self):
        """Updates the color box and labels based on current color."""
        self.color_box.config(bg=self.current_hex)
        self.hex_label.config(text=self.current_hex)
        self.rgb_label.config(text=str(self.current_rgb))

    def start_picking(self):
        """Initiates the color picking mode with live zoom and key bindings."""
        if self.picking_mode:
            self.stop_picking()
            return

        self.picking_mode = True
        self.pick_button.config(text="❌ Stop Picking (Esc or Ctrl+C)")

        self.master.bind("<Escape>", lambda e: self.stop_picking())
        self.master.bind("<Control-c>", self.select_color)
        self.master.bind("<Control-C>", self.select_color)

        self.magnifier = tk.Toplevel(self.master)
        self.magnifier.overrideredirect(True)

        self.magnifier.geometry(f"{self.MAGNIFIER_SIZE + 2}x{self.MAGNIFIER_SIZE + 50}")
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
            text="Press Ctrl+C to Select",
            background="#2c3e50",
            foreground="#ecf0f1",
            font=("Inter", 10, "bold"),
        )
        self.mag_label.pack(fill="x", padx=1, pady=(0, 1))

        self.poll_mouse()

    def select_color(self, event=None):
        """Action taken when the user presses Ctrl+C."""
        if not self.picking_mode:
            return

        self.stop_picking()

        self.update_ui()

        messagebox.showinfo(
            "Color Picked",
            f"Color selected and saved to app state:\n\n"
            f"HEX: {self.current_hex}\n"
            f"RGB: {self.current_rgb}",
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

            img_magnified = img.resize(
                (self.MAGNIFIER_SIZE, self.MAGNIFIER_SIZE), resample=Image.NEAREST
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
                text=f"HEX: {hex_code} | RGB: {rgb}",
                background=hex_code,
                foreground="white" if sum(rgb) < 382 else "black",
            )

        except Exception as e:
            self.mag_label.config(text=f"Error: {e}")
            pass

        self.after_id = self.master.after(50, self.poll_mouse)

    def stop_picking(self, event=None):
        """Stops the picking mode and cleans up resources, handling ESC key."""
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

        self.pick_button.config(text="🎨 Start Picking (Ctrl+C to select)")


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
