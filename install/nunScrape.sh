#!/bin/bash
# nunScrape Installer
# Run with: sudo bash install.sh

APP_NAME="nunscrape"
APP_TITLE="nunScrape"
PY_FILE="src/pyscrape.py"
ICON_PATH="assets/images/ts-logo.png"

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

if ! python3 -c "import requests" &> /dev/null; then
  echo "📦 Installing missing dependency: requests"
  pip3 install requests
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
cp nunscrape.desktop /usr/share/applications/nunscrape.desktop
sed -i "s|/usr/bin/nunscrape|/usr/local/bin/$APP_NAME|" /usr/share/applications/nunscrape.desktop

echo "✅ Installation complete!"
echo "You can now run it from the app menu or by typing: nunscrape"
