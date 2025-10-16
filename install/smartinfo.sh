#!/bin/bash
# Smart Info Installer
# Run: sudo bash install.sh

APP_NAME="nuninfo"
APP_TITLE="Nun Info"
PY_FILE="src/ip-check.py"
ICON_PATH="assets/images/logo.png"

echo "🔧 Installing $APP_TITLE..."

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root: sudo bash smartinfo.sh"
  exit 1
fi

# Check dependencies
if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 not found. Please install it first."
  exit 1
fi

if ! python3 -c "import requests" &> /dev/null; then
  echo "📦 Installing missing dependency: requests"
  pip3 install requests
fi

# Copy the Python script
echo "📂 Copying Python file..."
cp "$PY_FILE" /usr/local/bin/$APP_NAME
chmod +x /usr/local/bin/$APP_NAME

# Copy icon
echo "🖼️ Copying icon..."
mkdir -p /usr/share/pixmaps/
cp "$ICON_PATH" /usr/share/pixmaps/$APP_NAME.png

# Copy .desktop file
echo "🧩 Installing desktop entry..."
cp smartinfo.desktop /usr/share/applications/smartinfo.desktop

# Replace Exec path inside desktop file
sed -i "s|/usr/bin/smartinfo|/usr/local/bin/$APP_NAME|" /usr/share/applications/smartinfo.desktop

echo "✅ Installation complete!"
echo "You can now run it from the app menu or by typing: smartinfo"
