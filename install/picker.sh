#!/bin/bash
# Nun Picker Installer
# Installs the Python screen color picker application.
# Run: sudo bash install.sh

# --- Configuration ---
APP_NAME="nunpicker"
APP_TITLE="Nun Picker"
PY_FILE="src/picker.py"
ICON_PATH="assets/images/picker.png"
DESKTOP_FILE="picker.desktop"
# ---------------------

echo "🔧 Starting installation of $APP_TITLE..."

# 1. Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run the installer as root using: sudo bash install.sh"
  exit 1
fi

# 2. Check dependencies (Python 3)
if ! command -v python3 &> /dev/null; then
  echo "❌ Error: Python3 not found. Please install Python 3 first."
  exit 1
fi

# 3. Check and install Python dependencies (Pillow is essential for screen capture)
if ! python3 -c "import PIL" &> /dev/null; then
  echo "📦 Installing missing dependency: Pillow (PIL)"
  pip3 install Pillow
  if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install Pillow. Installation aborted."
    exit 1
  fi
fi

# 4. Copy the Python script (The core executable)
echo "📂 Copying Python file and setting executable path to /usr/local/bin/$APP_NAME..."
cp "$PY_FILE" /usr/local/bin/$APP_NAME
chmod +x /usr/local/bin/$APP_NAME

# 5. Copy icon
if [ -f "$ICON_PATH" ]; then
    echo "🖼️ Copying icon to /usr/share/pixmaps..."
    mkdir -p /usr/share/pixmaps/
    cp "$ICON_PATH" /usr/share/pixmaps/$APP_NAME.png
else
    echo "⚠️ Warning: Icon file ($ICON_PATH) not found. Skipping icon installation."
fi

# 6. Copy .desktop file
if [ -f "$DESKTOP_FILE" ]; then
    echo "🧩 Installing desktop entry to /usr/share/applications/..."
    cp "$DESKTOP_FILE" /usr/share/applications/$DESKTOP_FILE
    # Ensure the desktop file points to the correct executable path
    sed -i "s|Exec=/usr/local/bin/nunpicker|Exec=/usr/local/bin/$APP_NAME|" /usr/share/applications/$DESKTOP_FILE
else
    echo "❌ Error: Desktop file ($DESKTOP_FILE) not found. Installation aborted."
    exit 1
fi

echo "✅ Installation complete!"
echo "You can now run '$APP_TITLE' from your application menu or by typing: $APP_NAME"
