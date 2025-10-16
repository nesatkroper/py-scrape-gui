#!/bin/bash
# Remove Comments Installer
# Run with: sudo bash install.sh

APP_NAME="remove-comments"
APP_TITLE="Remove Comments"
PY_FILE="src/remove.py"
ICON_PATH="assets/images/remove.png"

echo "🔧 Installing $APP_TITLE..."

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root: sudo bash install.sh"
  exit 1
fi

# Check dependencies
if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 not found. Please install it first."
  exit 1
fi

if ! python3 -c "import tkinter" &> /dev/null; then
  echo "📦 Installing missing dependency: tkinter"
  sudo apt install -y python3-tk
fi

# Copy Python script
echo "📂 Copying Python file..."
cp "$PY_FILE" /usr/local/bin/$APP_NAME
chmod +x /usr/local/bin/$APP_NAME

# Copy icon
echo "🖼️ Copying icon..."
mkdir -p /usr/share/pixmaps/
cp "$ICON_PATH" /usr/share/pixmaps/$APP_NAME.png

# Copy .desktop file
echo "🧩 Installing desktop entry..."
cp remove-comments.desktop /usr/share/applications/$APP_NAME.desktop
sed -i "s|/usr/bin/remove-comments|/usr/local/bin/$APP_NAME|" /usr/share/applications/$APP_NAME.desktop

echo "✅ Installation complete!"
echo "You can now run it from the app menu or by typing: $APP_NAME"
