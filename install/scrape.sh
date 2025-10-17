#!/bin/bash

# ┌────────────────────────────────────────────┐
# │             Nun Scrape Installer           │
# └────────────────────────────────────────────┘

set -e

APP_NAME="Nun Scrape"
SCRIPT_NAME="scrape.py"
ICON_NAME="crawling.png"
INSTALL_DIR="$HOME/.local/share/nun-scrape"
DESKTOP_FILE="$HOME/.local/share/applications/nun-scrape.desktop"

echo "[+] Installing $APP_NAME..."

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy app files
cp "$(dirname "$0")/../src/$SCRIPT_NAME" "$INSTALL_DIR/"
cp "$(dirname "$0")/../assets/images/$ICON_NAME" "$INSTALL_DIR/"

# Create desktop launcher
echo "[+] Creating desktop launcher..."

cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Scrape data from websites easily
Exec=python3 $INSTALL_DIR/$SCRIPT_NAME
Icon=$INSTALL_DIR/$ICON_NAME
Terminal=false
Type=Application
Categories=Network;Utility;Development;
EOL

chmod +x "$DESKTOP_FILE"

echo "[✓] $APP_NAME installed successfully. You can find it in your application menu."

# ─────────────────────────────────────────────
# Optional: Build .deb package
# ─────────────────────────────────────────────
read -p "Build .deb package? (y/n): " build_deb
if [[ "$build_deb" == "y" ]]; then
    echo "[+] Building .deb package..."

    TMP_DIR="./nun-scrape-deb"
    rm -rf "$TMP_DIR"
    mkdir -p "$TMP_DIR/DEBIAN"
    mkdir -p "$TMP_DIR/usr/local/bin"
    mkdir -p "$TMP_DIR/usr/share/applications"
    mkdir -p "$TMP_DIR/usr/share/icons"

    # Copy app files
    cp "$(dirname "$0")/../src/$SCRIPT_NAME" "$TMP_DIR/usr/local/bin/$SCRIPT_NAME"
    cp "$(dirname "$0")/../assets/images/$ICON_NAME" "$TMP_DIR/usr/share/icons/nun-scrape.png"

    # Desktop entry for system-wide install
    cat > "$TMP_DIR/usr/share/applications/nun-scrape.desktop" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Scrape data from websites easily
Exec=python3 /usr/local/bin/$SCRIPT_NAME
Icon=/usr/share/icons/nun-scrape.png
Terminal=false
Type=Application
Categories=Network;Utility;Development;
EOL

    # Control file
    cat > "$TMP_DIR/DEBIAN/control" <<EOL
Package: nun-scrape
Version: 1.0
Section: web
Priority: optional
Architecture: all
Depends: python3
Maintainer: $(whoami)
Description: Nun Scrape - Web Scraping Tool
 A lightweight GUI tool for extracting data from websites quickly and easily.
EOL

    dpkg-deb --build "$TMP_DIR"
    mv nun-scrape-deb.deb nun-scrape_1.0_all.deb

    echo "[✓] .deb package created: nun-scrape_1.0_all.deb"
fi

# ─────────────────────────────────────────────
# Optional: Build .exe for Windows
# ─────────────────────────────────────────────
read -p "Build Windows .exe with PyInstaller? (y/n): " build_exe
if [[ "$build_exe" == "y" ]]; then
    if ! command -v pyinstaller &> /dev/null; then
        echo "[!] PyInstaller not found. Installing..."
        pip install pyinstaller
    fi

    if ! command -v convert &> /dev/null; then
        echo "[!] ImageMagick (convert) not found. Please install it to convert PNG to ICO."
        exit 1
    fi

    ICON_PATH="$(dirname "$0")/../assets/images/nun-scrape.ico"
    echo "[+] Generating .ico icon..."
    convert "$(dirname "$0")/../assets/images/$ICON_NAME" "$ICON_PATH"

    echo "[+] Building .exe with PyInstaller..."
    pyinstaller --onefile --noconsole --icon="$ICON_PATH" "$(dirname "$0")/../src/$SCRIPT_NAME"

    echo "[✓] Windows .exe created: dist/scrape.exe"
fi

echo "[✔] Done!"
