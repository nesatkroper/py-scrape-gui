#!/usr/bin/env python3



import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import os
import threading
import random
import string

# Core Utility Libraries
from PIL import Image
from rembg import remove
import pytesseract
import hashlib
from cryptography.fernet import Fernet
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import pdfplumber
from moviepy import VideoFileClip
import re 

# --- Configuration and Setup ---

# Tesseract path configuration (REQUIRED for OCR tools)
# Replace 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' with your actual path
# If tesseract is in your system PATH, you can comment this line out.
# try:
#     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# except Exception:
#     pass # Handled gracefully if not set, but OCR will fail

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MultiToolApp(ctk.CTk):
    """
    Main application class for the MultiTool Utility.
    Uses CustomTkinter for a modern, dark-mode GUI.
    """
    def __init__(self):
        super().__init__()
        self.title("MultiTool Utility 🛠️")
        self.geometry("1100x700")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Current files selected for multi-file operations
        self.selected_files = []
        
        # --- Sidebar Navigation ---
        self.sidebar_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(14, weight=1) # Push 'About' to the bottom
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="MultiTool 🛠️", 
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Navigation buttons
        tools = [
            ("Image Compressor", self.show_image_compressor),
            ("Video Compressor", self.show_video_compressor),
            ("Remove Background", self.show_bg_remover),
            ("Image to Text (OCR)", self.show_image_ocr),
            ("PDF to Text", self.show_pdf_to_text),
            ("Password Generator", self.show_password_generator),
            ("Hash Generator", self.show_hash_generator),
            ("Hash Compare", self.show_hash_compare),
            ("Encrypt/Decrypt Text", self.show_cryptography),
            ("PDF to Word (DOCX)", self.show_pdf_to_word),
            ("PDF to Excel (XLSX)", self.show_pdf_to_excel),
        ]
        
        for i, (text, command) in enumerate(tools):
            btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, anchor="w")
            btn.grid(row=i + 1, column=0, padx=20, pady=5, sticky="ew")

        self.about_button = ctk.CTkButton(self.sidebar_frame, text="About/Help", 
                                          command=self.show_about_help)
        self.about_button.grid(row=15, column=0, padx=20, pady=(10, 20), sticky="s")
        
        # --- Main Content Area ---
        self.main_content_frame = ctk.CTkFrame(self)
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Ready.", anchor="w", fg_color="gray20")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(0,0))
        
        # Initial view
        self.current_view = None
        self.show_about_help()

    # --- UI Helpers ---

    def clear_content(self):
        """Clears the main content frame."""
        if self.current_view:
            self.current_view.destroy()
        
    def create_tool_frame(self, title):
        """Creates a standardized frame for a tool with a title."""
        self.clear_content()
        
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(99, weight=1) # Reserve a row for flexible content
        self.current_view = frame

        title_label = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        return frame

    def show_status(self, message, is_error=False):
        """Updates the status bar."""
        color = "red" if is_error else "green"
        self.status_bar.configure(text=message, fg_color=color)
        self.after(5000, lambda: self.status_bar.configure(text="Ready.", fg_color="gray20"))

    def select_files(self, filetypes, title="Select Files"):
        """Opens a file dialog to select multiple files."""
        files = filedialog.askopenfilenames(
            title=title, 
            filetypes=filetypes
        )
        if files:
            self.selected_files = list(files)
            self.show_status(f"Selected {len(self.selected_files)} file(s).")
            return self.selected_files
        return []

    def select_output_folder(self, title="Select Output Folder"):
        """Opens a directory dialog to choose the save location."""
        folder = filedialog.askdirectory(title=title)
        if folder:
            self.show_status(f"Output folder set to: {folder}")
            return folder
        return None

    def create_progress_bar(self, parent_frame, row):
        """Creates a standard progress bar widget."""
        progress_bar = ctk.CTkProgressBar(parent_frame, orientation="horizontal", mode="determinate")
        progress_bar.grid(row=row, column=0, padx=20, pady=10, sticky="ew")
        progress_bar.set(0)
        return progress_bar
    
    # --- Tool Implementations (Functions) ---

    def _compress_image_task(self, files, output_folder, quality, progress_bar, file_list_label):
        """Worker thread for image compression."""
        if not files or not output_folder:
            self.show_status("Error: Files or output folder not selected.", is_error=True)
            return

        total_files = len(files)
        
        for i, file_path in enumerate(files):
            try:
                # Update UI for current file
                self.after(0, lambda f=os.path.basename(file_path): file_list_label.configure(text=f"Processing: {f}..."))

                img = Image.open(file_path).convert('RGB')
                
                # Construct output path
                file_name = os.path.basename(file_path)
                base, ext = os.path.splitext(file_name)
                output_path = os.path.join(output_folder, f"{base}_comp.jpg")
                
                # Save with compression (JPEG supports quality parameter)
                img.save(output_path, "JPEG", quality=quality)
                
                # Update progress
                progress = (i + 1) / total_files
                self.after(0, lambda p=progress: progress_bar.set(p))
                
            except Exception as e:
                self.after(0, lambda e=e, f=file_path: messagebox.showerror("Compression Error", f"Failed to compress {f}: {e}"))

        self.after(0, lambda: [
            file_list_label.configure(text="Processing complete."),
            progress_bar.set(1),
            self.show_status(f"Successfully compressed {total_files} images to {output_folder}")
        ])

    def start_image_compression(self, files_list_label, quality_entry):
        """Starts the image compression thread."""
        files = self.selected_files
        quality_str = quality_entry.get()

        try:
            quality = int(quality_str)
            if not 0 < quality <= 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Quality must be an integer between 1 and 100.")
            return

        output_folder = self.select_output_folder("Choose folder to save compressed images")
        if not output_folder:
            return

        # Create progress bar dynamically
        progress_bar = self.create_progress_bar(self.current_view, 8)
        
        thread = threading.Thread(
            target=self._compress_image_task, 
            args=(files, output_folder, quality, progress_bar, files_list_label)
        )
        thread.start()

    # --- Tool: Video Compressor (Placeholder for complexity) ---
    # Due to the complexity and reliance on external tools (ffmpeg) for video, 
    # and to keep the script size manageable while demonstrating threading, 
    # this will use a simplified approach focused on re-encoding with a new bitrate.
    # Full, robust video compression would require more complex settings.
    def _compress_video_task(self, files, output_folder, bitrate_kbps, progress_bar, file_list_label):
        """Worker thread for video compression."""
        if not files or not output_folder:
            self.show_status("Error: Files or output folder not selected.", is_error=True)
            return

        total_files = len(files)
        target_bitrate = f"{bitrate_kbps}k" # e.g., '1000k'

        for i, file_path in enumerate(files):
            try:
                self.after(0, lambda f=os.path.basename(file_path): file_list_label.configure(text=f"Processing: {f}..."))

                # Use moviepy for re-encoding with a specified bitrate
                clip = VideoFileClip(file_path)
                
                file_name = os.path.basename(file_path)
                base, ext = os.path.splitext(file_name)
                output_path = os.path.join(output_folder, f"{base}_comp.mp4")

                clip.write_videofile(
                    output_path, 
                    codec='libx264', 
                    audio_codec='aac', 
                    bitrate=target_bitrate, 
                    verbose=False, 
                    logger=None
                )
                clip.close()
                
                progress = (i + 1) / total_files
                self.after(0, lambda p=progress: progress_bar.set(p))
                
            except Exception as e:
                self.after(0, lambda e=e, f=file_path: messagebox.showerror("Video Error", f"Failed to compress {f}. Ensure 'ffmpeg' is installed and in PATH: {e}"))
                break # Stop on error

        self.after(0, lambda: [
            file_list_label.configure(text="Processing complete."),
            progress_bar.set(1),
            self.show_status(f"Successfully compressed {total_files} videos to {output_folder}")
        ])

    def start_video_compression(self, files_list_label, bitrate_entry):
        """Starts the video compression thread."""
        files = self.selected_files
        bitrate_str = bitrate_entry.get()

        try:
            bitrate_kbps = int(bitrate_str)
            if bitrate_kbps < 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Bitrate must be an integer (e.g., 1000 for 1Mbps) and a reasonable value.")
            return

        output_folder = self.select_output_folder("Choose folder to save compressed videos")
        if not output_folder:
            return

        progress_bar = self.create_progress_bar(self.current_view, 8)
        
        thread = threading.Thread(
            target=self._compress_video_task, 
            args=(files, output_folder, bitrate_kbps, progress_bar, files_list_label)
        )
        thread.start()

    # --- Tool: Remove Image Background ---
    def _remove_bg_task(self, files, output_folder, progress_bar, file_list_label):
        """Worker thread for background removal."""
        if not files or not output_folder:
            self.show_status("Error: Files or output folder not selected.", is_error=True)
            return

        total_files = len(files)
        
        for i, file_path in enumerate(files):
            try:
                self.after(0, lambda f=os.path.basename(file_path): file_list_label.configure(text=f"Processing: {f}..."))

                # Use rembg
                with open(file_path, 'rb') as i_file:
                    input_data = i_file.read()
                
                output_data = remove(input_data)
                
                file_name = os.path.basename(file_path)
                base, _ = os.path.splitext(file_name)
                output_path = os.path.join(output_folder, f"{base}_nobg.png")
                
                with open(output_path, 'wb') as o_file:
                    o_file.write(output_data)
                
                progress = (i + 1) / total_files
                self.after(0, lambda p=progress: progress_bar.set(p))
                
            except Exception as e:
                self.after(0, lambda e=e, f=file_path: messagebox.showerror("Rembg Error", f"Failed to remove background for {f}: {e}"))

        self.after(0, lambda: [
            file_list_label.configure(text="Processing complete."),
            progress_bar.set(1),
            self.show_status(f"Successfully processed {total_files} images to {output_folder}")
        ])

    def start_bg_removal(self, files_list_label):
        """Starts the background removal thread."""
        files = self.selected_files
        
        output_folder = self.select_output_folder("Choose folder to save images with transparent backgrounds")
        if not output_folder:
            return

        progress_bar = self.create_progress_bar(self.current_view, 6)
        
        thread = threading.Thread(
            target=self._remove_bg_task, 
            args=(files, output_folder, progress_bar, files_list_label)
        )
        thread.start()

    # --- Tool: Image to Text (OCR) ---
    def _image_ocr_task(self, file_path, text_output):
        """Worker thread for Image OCR."""
        try:
            self.after(0, lambda: text_output.delete("1.0", "end"))
            self.show_status(f"Starting OCR on {os.path.basename(file_path)}...")
            
            # Use Pillow to open and pytesseract to extract text
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            
            self.after(0, lambda t=text: [
                text_output.insert("1.0", t),
                self.show_status("OCR complete. Text extracted.")
            ])

        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("OCR Error", f"Failed to perform OCR. Ensure Tesseract is installed and configured in the script: {e}"))
            self.show_status("OCR Failed.", is_error=True)

    def start_image_ocr(self, text_output):
        """Starts the image OCR thread."""
        files = self.select_files([("Image files", "*.png *.jpg *.jpeg *.tiff")], "Select Image for OCR")
        if not files:
            return

        thread = threading.Thread(
            target=self._image_ocr_task, 
            args=(files[0], text_output)
        )
        thread.start()
        
    def save_text_output(self, text_output):
        """Saves the content of the text widget to a file."""
        text_content = text_output.get("1.0", "end-1c")
        if not text_content.strip():
            messagebox.showinfo("Empty", "Nothing to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Extracted Text As"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                self.show_status(f"Text successfully saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {e}")

    # --- Tool: PDF to Text ---
    def _pdf_to_text_task(self, file_path, text_output, use_ocr):
        """Worker thread for PDF to Text extraction."""
        try:
            self.after(0, lambda: text_output.delete("1.0", "end"))
            self.show_status(f"Starting PDF text extraction on {os.path.basename(file_path)}...")
            
            full_text = []
            
            if use_ocr:
                # Use pdfplumber/Pillow/Pytesseract for OCR-based extraction (slow)
                with pdfplumber.open(file_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        # The actual OCR process is complex (converting page to image and running OCR)
                        # We'll stick to a simpler path in this example for robustness, 
                        # but alert the user if OCR is selected.
                        self.after(0, lambda: self.show_status("OCR on PDF is highly resource-intensive and slow. Using direct text extraction for speed/stability."))
                        break # Fall through to direct extraction
            
            # Direct text extraction (Preferred and faster)
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                num_pages = len(reader.pages)
                for i in range(num_pages):
                    page = reader.pages[i]
                    full_text.append(page.extract_text() or f"--- Page {i+1} (No extractable text) ---\n")
                    
            text = "\n\n".join(full_text)
            
            self.after(0, lambda t=text: [
                text_output.insert("1.0", t),
                self.show_status("PDF text extraction complete.")
            ])

        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("PDF Error", f"Failed to extract text from PDF: {e}"))
            self.show_status("PDF Text Extraction Failed.", is_error=True)

    def start_pdf_to_text(self, text_output, ocr_var):
        """Starts the PDF to Text thread."""
        files = self.select_files([("PDF files", "*.pdf")], "Select PDF for Text Extraction")
        if not files:
            return
        
        use_ocr = ocr_var.get() == 1

        thread = threading.Thread(
            target=self._pdf_to_text_task, 
            args=(files[0], text_output, use_ocr)
        )
        thread.start()

    # --- Tool: Password Generator ---
    def generate_password(self, length_entry, upper_var, lower_var, number_var, symbol_var, quantity_entry, output_textbox):
        """Generates secure passwords."""
        try:
            length = int(length_entry.get())
            quantity = int(quantity_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Length and Quantity must be integers.")
            return

        if length <= 0 or quantity <= 0:
            messagebox.showerror("Invalid Input", "Length and Quantity must be greater than zero.")
            return

        characters = ""
        if upper_var.get():
            characters += string.ascii_uppercase
        if lower_var.get():
            characters += string.ascii_lowercase
        if number_var.get():
            characters += string.digits
        if symbol_var.get():
            characters += string.punctuation
            
        if not characters:
            messagebox.showerror("Selection Error", "Select at least one character type.")
            return

        output_textbox.delete("1.0", "end")
        passwords = []
        for _ in range(quantity):
            password = ''.join(random.choice(characters) for _ in range(length))
            passwords.append(password)
            
        output_textbox.insert("1.0", "\n".join(passwords))
        self.show_status(f"Generated {quantity} passwords.")
        
    def copy_password(self, output_textbox):
        """Copies the generated password(s) to the clipboard."""
        text = output_textbox.get("1.0", "end-1c")
        if text.strip():
            self.clipboard_clear()
            self.clipboard_append(text)
            self.show_status("Copied to clipboard.")
        else:
            self.show_status("Nothing to copy.", is_error=True)

    # --- Tool: Hash Generator/Compare ---
    def _get_input_data(self, input_text_box, file_path_var):
        """Helper to get input data (text or file content)."""
        file_path = file_path_var.get()
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    return f.read(), "file"
            except Exception as e:
                messagebox.showerror("File Error", f"Could not read file {file_path}: {e}")
                return None, None
        else:
            text = input_text_box.get("1.0", "end-1c")
            return text.encode('utf-8'), "text"
            
    def _hash_task(self, data, algorithm, output_textbox):
        """Worker thread for hash generation."""
        try:
            if not data:
                self.after(0, lambda: self.show_status("No input data.", is_error=True))
                return

            hasher = hashlib.new(algorithm)
            hasher.update(data)
            hash_result = hasher.hexdigest()

            self.after(0, lambda h=hash_result: [
                output_textbox.delete("1.0", "end"),
                output_textbox.insert("1.0", h),
                self.show_status(f"{algorithm.upper()} hash generated.")
            ])
            
        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("Hash Error", f"Failed to generate hash: {e}"))

    def start_hash_generation(self, input_text_box, file_path_var, algorithm_combobox, output_textbox):
        """Starts the hash generation thread."""
        data, _ = self._get_input_data(input_text_box, file_path_var)
        algorithm = algorithm_combobox.get().lower().replace('-', '')

        if data is None:
            return

        thread = threading.Thread(
            target=self._hash_task, 
            args=(data, algorithm, output_textbox)
        )
        thread.start()

    def compare_hashes(self, hash1_box, hash2_box, result_label):
        """Compares two hashes (or data inputs)."""
        hash1 = hash1_box.get("1.0", "end-1c").strip()
        hash2 = hash2_box.get("1.0", "end-1c").strip()

        if not hash1 or not hash2:
            result_label.configure(text="Input both hashes/texts.", text_color="yellow")
            return

        if hash1 == hash2:
            result_label.configure(text="✅ Hashes/Data MATCH", text_color="green")
            self.show_status("Hashes/Data MATCH.")
        else:
            result_label.configure(text="❌ Hashes/Data DO NOT MATCH", text_color="red")
            self.show_status("Hashes/Data DO NOT MATCH.", is_error=True)

    # --- Tool: Encrypt and Decrypt Text ---
    def generate_fernet_key(self, key_output_box):
        """Generates a Fernet (AES) key."""
        key = Fernet.generate_key()
        key_output_box.delete("1.0", "end")
        key_output_box.insert("1.0", key.decode())
        self.show_status("New Fernet key generated.")
        
    def _cryptography_task(self, text, key, is_encrypt, output_textbox):
        """Worker thread for encryption/decryption."""
        try:
            if not text or not key:
                self.after(0, lambda: self.show_status("Text and Key are required.", is_error=True))
                return

            f = Fernet(key.encode())
            
            if is_encrypt:
                # Text input must be bytes for Fernet
                encrypted_text = f.encrypt(text.encode()).decode()
                result = encrypted_text
                status_msg = "Text encrypted successfully."
            else:
                # Encrypted text (ciphertext) must be bytes for decryption
                decrypted_text = f.decrypt(text.encode()).decode()
                result = decrypted_text
                status_msg = "Text decrypted successfully."

            self.after(0, lambda r=result: [
                output_textbox.delete("1.0", "end"),
                output_textbox.insert("1.0", r),
                self.show_status(status_msg)
            ])

        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("Crypto Error", f"Operation failed. Check if the key and text are correct (e.g., text must be valid Fernet ciphertext for decryption): {e}"))
            self.show_status("Cryptography operation failed.", is_error=True)

    def start_cryptography(self, text_input_box, key_input_box, output_textbox, is_encrypt):
        """Starts the cryptography thread."""
        text = text_input_box.get("1.0", "end-1c").strip()
        key = key_input_box.get("1.0", "end-1c").strip()

        thread = threading.Thread(
            target=self._cryptography_task, 
            args=(text, key, is_encrypt, output_textbox)
        )
        thread.start()

    # --- Tool: PDF to Word (DOCX) ---
    def _pdf_to_word_task(self, pdf_path, output_path):
        """Worker thread for PDF to DOCX conversion (simplified)."""
        try:
            self.show_status(f"Starting PDF to Word conversion: {os.path.basename(pdf_path)}...")
            
            doc = Document()
            
            # Simple Text Extraction using PyPDF2 (Lossy conversion, images/layout are not preserved)
            # Full, accurate PDF to Word conversion requires complex commercial libraries or web services.
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    text = page.extract_text()
                    if text:
                        doc.add_paragraph(text)
                        doc.add_page_break()
                        
            doc.save(output_path)

            self.after(0, lambda: self.show_status(f"PDF to Word conversion complete (text-only): {os.path.basename(output_path)}"))

        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("Conversion Error", f"Failed to convert PDF to Word: {e}"))
            self.show_status("PDF to Word Failed.", is_error=True)

    def start_pdf_to_word(self):
        """Selects files and starts PDF to DOCX thread."""
        files = self.select_files([("PDF files", "*.pdf")], "Select PDF for DOCX Conversion")
        if not files:
            return
            
        pdf_path = files[0]
        base, _ = os.path.splitext(os.path.basename(pdf_path))
        
        output_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialfile=f"{base}.docx",
            title="Save DOCX File As"
        )
        
        if not output_path:
            return

        thread = threading.Thread(
            target=self._pdf_to_word_task, 
            args=(pdf_path, output_path)
        )
        thread.start()

    # --- Tool: PDF to Excel (XLSX) ---
    def _pdf_to_excel_task(self, pdf_path, output_path):
        """Worker thread for PDF to XLSX conversion."""
        try:
            self.show_status(f"Starting PDF to Excel conversion: {os.path.basename(pdf_path)}...")
            
            # Use pdfplumber for robust table extraction
            all_tables = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # 'extract_tables()' returns a list of lists of lists (tables, rows, cells)
                    tables = page.extract_tables()
                    for table in tables:
                        # Convert table (list of rows) into a pandas DataFrame
                        df = pd.DataFrame(table[1:], columns=table[0]) # Assuming first row is header
                        all_tables.append(df)
            
            if not all_tables:
                self.after(0, lambda: messagebox.showwarning("No Tables", "No tables were detected in the PDF using automated parsing."))
                self.show_status("PDF to Excel Failed: No tables found.", is_error=True)
                return

            # Save all extracted tables to a single Excel workbook, each table on a new sheet
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, df in enumerate(all_tables):
                    sheet_name = f"Table_{i+1}"
                    # Clean up column names for Excel
                    df.columns = [re.sub(r'[\s]+', ' ', str(col)).strip() for col in df.columns]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
            self.after(0, lambda: self.show_status(f"PDF to Excel conversion complete: {os.path.basename(output_path)}"))

        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("Conversion Error", f"Failed to convert PDF to Excel: {e}. Check if the PDF has clear tabular data."))
            self.show_status("PDF to Excel Failed.", is_error=True)

    def start_pdf_to_excel(self):
        """Selects files and starts PDF to XLSX thread."""
        files = self.select_files([("PDF files", "*.pdf")], "Select PDF for XLSX Conversion")
        if not files:
            return
            
        pdf_path = files[0]
        base, _ = os.path.splitext(os.path.basename(pdf_path))
        
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile=f"{base}.xlsx",
            title="Save XLSX File As"
        )
        
        if not output_path:
            return

        thread = threading.Thread(
            target=self._pdf_to_excel_task, 
            args=(pdf_path, output_path)
        )
        thread.start()

    # --- Tool UI Layouts (show_ methods) ---
    
    def show_about_help(self):
        frame = self.create_tool_frame("About/Help - MultiTool Utility")
        
        # Configure layout for better readability
        frame.grid_columnconfigure(0, weight=0) # Title column
        frame.grid_columnconfigure(1, weight=1) # Content column

        # Text Content
        help_text = ctk.CTkTextbox(frame, wrap="word", height=450, font=("Sans-serif", 14))
        help_text.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        
        content = """
**MultiTool Utility: Help & Usage** 🛠️

This application provides a collection of essential desktop utility tools, designed for simplicity and efficiency.

---
### 🖥️ General Usage:
1.  **Select a Tool:** Use the sidebar on the left to navigate between different utilities.
2.  **Input:** Most tools require file selections (via "Browse" buttons) or direct text input.
3.  **Process:** Click the main action button (e.g., "Compress," "Generate," "Encrypt").
4.  **Status:** Watch the status bar at the bottom for process feedback, errors, and completion messages.
5.  **Responsiveness:** Long-running tasks (like compression or conversion) run in the background (multi-threaded) to keep the GUI responsive.

---
### 🗜️ Key Tools:
* **Compress Images/Videos:** Select multiple files, set a target quality/bitrate, and save the smaller output files to a chosen folder.
* **Remove Image Background:** Select images, and the tool uses an intelligent algorithm (`rembg`) to output a transparent PNG.
* **Image/PDF to Text (OCR):** Extracts text from images or PDF documents. *Note: PDF conversion uses direct extraction, which is faster. Image OCR requires Tesseract-OCR.*
* **Password Generator:** Creates secure, customizable passwords with control over length and character sets.
* **Hash Generator/Compare:** Computes secure hashes (MD5, SHA-256 etc.) of text or files for integrity checking.
* **Encrypt/Decrypt Text:** Uses the strong AES standard (`Fernet`) for symmetric encryption. **Always save your generated key!**
* **PDF to Word/Excel:** Converts PDF content to editable formats. *Note: Conversion quality, especially for layout, is limited to text and detected tables.*

---
### ⚠️ Installation Notes:
This app requires several external Python libraries.
You must install them via `pip install ...` as specified in the script comments.
For OCR, the **Tesseract-OCR executable** must also be installed on your system.
For Video compression, **FFmpeg** must be installed and accessible.
        """
        
        help_text.insert("1.0", content)
        help_text.configure(state="disabled") # Make it read-only
        
        self.show_status("Welcome to MultiTool Utility!")

    def show_image_compressor(self):
        frame = self.create_tool_frame("Compress Multiple Images")
        
        # Layout setup
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. File Selection
        row_idx = 1
        ctk.CTkLabel(frame, text="1. Select Input Images (.jpg, .png):").grid(row=row_idx, column=0, padx=20, pady=(10, 0), sticky="w")
        row_idx += 1
        
        browse_button = ctk.CTkButton(frame, text="Browse Files...", 
                                      command=lambda: self.select_files([("Image files", "*.png *.jpg *.jpeg")], "Select Images"))
        browse_button.grid(row=row_idx, column=0, padx=20, pady=5, sticky="ew")
        row_idx += 1
        
        files_list_label = ctk.CTkLabel(frame, text="0 files selected.", anchor="w")
        files_list_label.grid(row=row_idx, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # 2. Quality/Settings
        row_idx += 1
        ctk.CTkLabel(frame, text="2. Compression Quality (1-100, 100=highest):").grid(row=row_idx, column=0, padx=20, pady=(10, 0), sticky="w")
        row_idx += 1
        
        quality_entry = ctk.CTkEntry(frame, placeholder_text="e.g., 75 (for 75% quality)")
        quality_entry.insert(0, "75")
        quality_entry.grid(row=row_idx, column=0, padx=20, pady=5, sticky="ew")
        row_idx += 1

        # 3. Action Button
        row_idx += 1
        action_button = ctk.CTkButton(frame, text="COMPRESS AND SAVE IMAGES", 
                                      command=lambda: self.start_image_compression(files_list_label, quality_entry))
        action_button.grid(row=row_idx, column=0, padx=20, pady=20, sticky="ew")
        
        # Update selected files label on action
        self.after(100, lambda: files_list_label.configure(text=f"{len(self.selected_files)} files selected.") if self.selected_files else None)
        self.show_status("Ready to compress images.")

    def show_video_compressor(self):
        frame = self.create_tool_frame("Compress Multiple Videos")
        
        # Layout setup
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. File Selection
        row_idx = 1
        ctk.CTkLabel(frame, text="1. Select Input Videos (.mp4, .mov, etc.):").grid(row=row_idx, column=0, padx=20, pady=(10, 0), sticky="w")
        row_idx += 1
        
        browse_button = ctk.CTkButton(frame, text="Browse Files...", 
                                      command=lambda: self.select_files([("Video files", "*.mp4 *.mov *.avi")], "Select Videos"))
        browse_button.grid(row=row_idx, column=0, padx=20, pady=5, sticky="ew")
        row_idx += 1
        
        files_list_label = ctk.CTkLabel(frame, text="0 files selected.", anchor="w")
        files_list_label.grid(row=row_idx, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # 2. Bitrate/Settings
        row_idx += 1
        ctk.CTkLabel(frame, text="2. Target Video Bitrate (in kbps, e.g., 1000 for 1Mbps):").grid(row=row_idx, column=0, padx=20, pady=(10, 0), sticky="w")
        row_idx += 1
        
        bitrate_entry = ctk.CTkEntry(frame, placeholder_text="e.g., 1000 (Standard HD)")
        bitrate_entry.insert(0, "1000")
        bitrate_entry.grid(row=row_idx, column=0, padx=20, pady=5, sticky="ew")
        row_idx += 1

        # 3. Action Button
        row_idx += 1
        action_button = ctk.CTkButton(frame, text="COMPRESS AND SAVE VIDEOS", 
                                      command=lambda: self.start_video_compression(files_list_label, bitrate_entry))
        action_button.grid(row=row_idx, column=0, padx=20, pady=20, sticky="ew")
        
        # Note/Warning
        row_idx += 1
        ctk.CTkLabel(frame, text="Note: Requires **FFmpeg** to be installed and accessible on your system for video processing.", 
                     text_color="orange").grid(row=row_idx, column=0, padx=20, pady=(0, 10), sticky="w")

        self.after(100, lambda: files_list_label.configure(text=f"{len(self.selected_files)} files selected.") if self.selected_files else None)
        self.show_status("Ready to compress videos.")
        
    def show_bg_remover(self):
        frame = self.create_tool_frame("Remove Image Background")
        
        # Layout setup
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. File Selection
        row_idx = 1
        ctk.CTkLabel(frame, text="1. Select Input Images (.jpg, .png):").grid(row=row_idx, column=0, padx=20, pady=(10, 0), sticky="w")
        row_idx += 1
        
        browse_button = ctk.CTkButton(frame, text="Browse Files...", 
                                      command=lambda: self.select_files([("Image files", "*.png *.jpg *.jpeg")], "Select Images"))
        browse_button.grid(row=row_idx, column=0, padx=20, pady=5, sticky="ew")
        row_idx += 1
        
        files_list_label = ctk.CTkLabel(frame, text="0 files selected.", anchor="w")
        files_list_label.grid(row=row_idx, column=0, padx=20, pady=(0, 10), sticky="w")

        # 2. Action Button
        row_idx += 1
        action_button = ctk.CTkButton(frame, text="REMOVE BACKGROUNDS AND SAVE (as PNG)", 
                                      command=lambda: self.start_bg_removal(files_list_label))
        action_button.grid(row=row_idx, column=0, padx=20, pady=20, sticky="ew")
        
        # Note
        row_idx += 1
        ctk.CTkLabel(frame, text="Output images will be saved as transparent PNGs.", 
                     text_color="gray").grid(row=row_idx, column=0, padx=20, pady=(0, 10), sticky="w")

        self.after(100, lambda: files_list_label.configure(text=f"{len(self.selected_files)} files selected.") if self.selected_files else None)
        self.show_status("Ready to remove image backgrounds.")

    def show_image_ocr(self):
        frame = self.create_tool_frame("Image to Text (OCR)")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. Input/Action Frame
        input_frame = ctk.CTkFrame(frame)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        
        # File Select Button
        browse_button = ctk.CTkButton(input_frame, text="1. Select Image File", 
                                      command=lambda: self.select_files([("Image files", "*.png *.jpg *.jpeg *.tiff")], "Select Image"))
        browse_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        # OCR Button
        ocr_button = ctk.CTkButton(input_frame, text="2. PERFORM OCR", 
                                   command=lambda: self.start_image_ocr(text_output))
        ocr_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        # 2. Output Text Area
        ctk.CTkLabel(frame, text="Extracted Text Output:").grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        text_output = ctk.CTkTextbox(frame, wrap="word", height=300)
        text_output.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        
        # 3. Output Actions
        action_frame = ctk.CTkFrame(frame)
        action_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        copy_button = ctk.CTkButton(action_frame, text="Copy Text", command=lambda: self.copy_password(text_output))
        copy_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        save_button = ctk.CTkButton(action_frame, text="Save to .txt File", command=lambda: self.save_text_output(text_output))
        save_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        ctk.CTkLabel(frame, text="Note: This tool requires Tesseract-OCR to be installed and configured.").grid(row=5, column=0, padx=20, pady=(0, 10), sticky="w")
        self.show_status("Ready to perform OCR on an image.")

    def show_pdf_to_text(self):
        frame = self.create_tool_frame("PDF to Text")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. Input/Action Frame
        input_frame = ctk.CTkFrame(frame)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        
        # File Select Button
        browse_button = ctk.CTkButton(input_frame, text="1. Select PDF File", 
                                      command=lambda: self.select_files([("PDF files", "*.pdf")], "Select PDF"))
        browse_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        # OCR Option (mostly a warning placeholder)
        ocr_var = ctk.IntVar()
        ocr_checkbox = ctk.CTkCheckBox(input_frame, text="Use OCR (Slow/Tesseract needed)", variable=ocr_var)
        ocr_checkbox.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # Extraction Button
        extract_button = ctk.CTkButton(input_frame, text="2. EXTRACT TEXT", 
                                       command=lambda: self.start_pdf_to_text(text_output, ocr_var))
        extract_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        # 2. Output Text Area
        ctk.CTkLabel(frame, text="Extracted Text Output:").grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        text_output = ctk.CTkTextbox(frame, wrap="word", height=300)
        text_output.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        
        # 3. Output Actions
        action_frame = ctk.CTkFrame(frame)
        action_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        copy_button = ctk.CTkButton(action_frame, text="Copy Text", command=lambda: self.copy_password(text_output))
        copy_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        save_button = ctk.CTkButton(action_frame, text="Save to .txt File", command=lambda: self.save_text_output(text_output))
        save_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        
        self.show_status("Ready to extract text from PDF (uses fast direct extraction by default).")

    def show_password_generator(self):
        frame = self.create_tool_frame("Secure Password Generator")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. Settings Frame
        settings_frame = ctk.CTkFrame(frame)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Length
        ctk.CTkLabel(settings_frame, text="Length:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        length_entry = ctk.CTkEntry(settings_frame, placeholder_text="e.g., 16")
        length_entry.insert(0, "16")
        length_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Quantity
        ctk.CTkLabel(settings_frame, text="Quantity:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        quantity_entry = ctk.CTkEntry(settings_frame, placeholder_text="e.g., 1")
        quantity_entry.insert(0, "1")
        quantity_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Character Types
        char_frame = ctk.CTkFrame(frame)
        char_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        char_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        upper_var = ctk.BooleanVar(value=True)
        lower_var = ctk.BooleanVar(value=True)
        number_var = ctk.BooleanVar(value=True)
        symbol_var = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(char_frame, text="Uppercase (A-Z)", variable=upper_var).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkCheckBox(char_frame, text="Lowercase (a-z)", variable=lower_var).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkCheckBox(char_frame, text="Numbers (0-9)", variable=number_var).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkCheckBox(char_frame, text="Symbols (!@#$)", variable=symbol_var).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # 2. Action and Output
        action_button = ctk.CTkButton(frame, text="GENERATE PASSWORD(S)", 
                                      command=lambda: self.generate_password(length_entry, upper_var, lower_var, number_var, symbol_var, quantity_entry, output_textbox))
        action_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(frame, text="Generated Passwords:").grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        output_textbox = ctk.CTkTextbox(frame, wrap="word", height=150)
        output_textbox.grid(row=5, column=0, padx=20, pady=5, sticky="nsew")
        
        copy_button = ctk.CTkButton(frame, text="Copy All to Clipboard", command=lambda: self.copy_password(output_textbox))
        copy_button.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        self.show_status("Ready to generate secure passwords.")

    def show_hash_generator(self):
        frame = self.create_tool_frame("Hash Generator")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. Input Selection
        input_frame = ctk.CTkFrame(frame)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(input_frame, text="Input Text or File:").grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")
        
        input_text_box = ctk.CTkTextbox(input_frame, wrap="word", height=50)
        input_text_box.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        file_path_var = ctk.StringVar(value="")
        file_path_label = ctk.CTkLabel(input_frame, textvariable=file_path_var, text_color="gray", anchor="w")
        file_path_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")
        
        def select_input_file():
            path = filedialog.askopenfilename(title="Select File to Hash")
            if path:
                file_path_var.set(path)
                input_text_box.delete("1.0", "end") # Clear text if file is selected
            else:
                file_path_var.set("")
        
        ctk.CTkButton(input_frame, text="Select File (overrides text)", command=select_input_file).grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # 2. Algorithm and Action
        action_frame = ctk.CTkFrame(frame)
        action_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(action_frame, text="Algorithm:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        algorithms = ["MD5", "SHA-1", "SHA-256", "SHA-512"]
        algorithm_combobox = ctk.CTkComboBox(action_frame, values=algorithms)
        algorithm_combobox.set("SHA-256")
        algorithm_combobox.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        output_textbox = ctk.CTkTextbox(frame, wrap="word", height=50)

        action_button = ctk.CTkButton(action_frame, text="GENERATE HASH", 
                                      command=lambda: self.start_hash_generation(input_text_box, file_path_var, algorithm_combobox, output_textbox))
        action_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # 3. Output
        ctk.CTkLabel(frame, text="Resulting Hash:").grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        output_textbox.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkButton(frame, text="Copy Hash", command=lambda: self.copy_password(output_textbox)).grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        self.show_status("Ready to generate cryptographic hashes.")

    def show_hash_compare(self):
        frame = self.create_tool_frame("Hash Compare (Integrity Check)")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. Hash 1 Input
        ctk.CTkLabel(frame, text="Input 1 (Hash or Text/File):").grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        hash1_box = ctk.CTkTextbox(frame, wrap="word", height=50)
        hash1_box.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        # 2. Hash 2 Input
        ctk.CTkLabel(frame, text="Input 2 (Hash or Text/File):").grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        hash2_box = ctk.CTkTextbox(frame, wrap="word", height=50)
        hash2_box.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        # 3. Compare Action
        compare_button = ctk.CTkButton(frame, text="COMPARE", 
                                       command=lambda: self.compare_hashes(hash1_box, hash2_box, result_label))
        compare_button.grid(row=5, column=0, padx=20, pady=20, sticky="ew")

        # 4. Result
        ctk.CTkLabel(frame, text="Comparison Result:").grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        result_label = ctk.CTkLabel(frame, text="Waiting for input...", font=ctk.CTkFont(size=18, weight="bold"), text_color="yellow")
        result_label.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(frame, text="Note: For file comparison, hash the files first in the 'Hash Generator' tool and paste the results here.", 
                     text_color="gray").grid(row=8, column=0, padx=20, pady=(0, 10), sticky="w")

        self.show_status("Ready to compare hashes or texts.")

    def show_cryptography(self):
        frame = self.create_tool_frame("Encrypt and Decrypt Text (AES-Fernet)")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. Key Input/Generation
        key_frame = ctk.CTkFrame(frame)
        key_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        key_frame.grid_columnconfigure(0, weight=1)
        key_frame.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(key_frame, text="Key (REQUIRED - Store this key safely):").grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="w")
        key_input_box = ctk.CTkTextbox(key_frame, wrap="word", height=30)
        key_input_box.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkButton(key_frame, text="Generate Key", 
                      command=lambda: self.generate_fernet_key(key_input_box)).grid(row=1, column=1, padx=(0, 10), pady=5, sticky="e")
        
        # 2. Text Input
        ctk.CTkLabel(frame, text="Input Text (Plaintext for Encrypt, Ciphertext for Decrypt):").grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        text_input_box = ctk.CTkTextbox(frame, wrap="word", height=80)
        text_input_box.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        # 3. Action Buttons
        action_frame = ctk.CTkFrame(frame)
        action_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        encrypt_button = ctk.CTkButton(action_frame, text="ENCRYPT TEXT", fg_color="green",
                                       command=lambda: self.start_cryptography(text_input_box, key_input_box, output_textbox, True))
        encrypt_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        decrypt_button = ctk.CTkButton(action_frame, text="DECRYPT TEXT", fg_color="red",
                                       command=lambda: self.start_cryptography(text_input_box, key_input_box, output_textbox, False))
        decrypt_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        # 4. Output
        ctk.CTkLabel(frame, text="Result (Ciphertext or Decrypted Plaintext):").grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        output_textbox = ctk.CTkTextbox(frame, wrap="word", height=80)
        output_textbox.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        
        ctk.CTkButton(frame, text="Copy Result", command=lambda: self.copy_password(output_textbox)).grid(row=7, column=0, padx=20, pady=10, sticky="ew")

        self.show_status("Ready to encrypt/decrypt text using Fernet.")
        
    def show_pdf_to_word(self):
        frame = self.create_tool_frame("PDF to Word (DOCX)")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. File Selection
        row_idx = 1
        ctk.CTkLabel(frame, text="1. Select Input PDF File:").grid(row=row_idx, column=0, padx=20, pady=(10, 0), sticky="w")
        row_idx += 1
        
        browse_button = ctk.CTkButton(frame, text="Browse PDF...", 
                                      command=lambda: self.select_files([("PDF files", "*.pdf")], "Select PDF for DOCX"))
        browse_button.grid(row=row_idx, column=0, padx=20, pady=5, sticky="ew")
        row_idx += 1
        
        # 2. Action Button
        action_button = ctk.CTkButton(frame, text="CONVERT TO WORD (.DOCX) and Save", 
                                      command=self.start_pdf_to_word)
        action_button.grid(row=row_idx, column=0, padx=20, pady=20, sticky="ew")
        row_idx += 1
        
        # Note
        ctk.CTkLabel(frame, text="Note: This conversion is primarily text-based. Complex layout, images, and tables may not be preserved accurately.", 
                     text_color="orange").grid(row=row_idx, column=0, padx=20, pady=(0, 10), sticky="w")

        self.show_status("Ready to convert PDF to DOCX.")
        
    def show_pdf_to_excel(self):
        frame = self.create_tool_frame("PDF to Excel (XLSX)")
        
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. File Selection
        row_idx = 1
        ctk.CTkLabel(frame, text="1. Select Input PDF File (with tabular data):").grid(row=row_idx, column=0, padx=20, pady=(10, 0), sticky="w")
        row_idx += 1
        
        browse_button = ctk.CTkButton(frame, text="Browse PDF...", 
                                      command=lambda: self.select_files([("PDF files", "*.pdf")], "Select PDF for XLSX"))
        browse_button.grid(row=row_idx, column=0, padx=20, pady=5, sticky="ew")
        row_idx += 1
        
        # 2. Action Button
        action_button = ctk.CTkButton(frame, text="CONVERT TO EXCEL (.XLSX) and Save", 
                                      command=self.start_pdf_to_excel)
        action_button.grid(row=row_idx, column=0, padx=20, pady=20, sticky="ew")
        row_idx += 1
        
        # Note
        ctk.CTkLabel(frame, text="Note: This tool uses intelligent parsing to find tables. Ensure your PDF has clearly defined tabular data.", 
                     text_color="orange").grid(row=row_idx, column=0, padx=20, pady=(0, 10), sticky="w")

        self.show_status("Ready to convert tabular PDF data to XLSX.")

if __name__ == "__main__":
    app = MultiToolApp()
    app.mainloop()