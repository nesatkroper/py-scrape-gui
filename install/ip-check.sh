#!/bin/bash

# ┌────────────────────────────────────────────┐
# │           Nun Info Installer               │
# └────────────────────────────────────────────┘

set -e

APP_NAME="Nun Check"
SCRIPT_NAME="ip-check.py"
ICON_NAME="ip-check.png"
INSTALL_DIR="$HOME/.local/share/nun-info"
DESKTOP_FILE="$HOME/.local/share/applications/nun-info.desktop"

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
Comment=Check your IP and network info
Exec=python3 $INSTALL_DIR/$SCRIPT_NAME
Icon=$INSTALL_DIR/$ICON_NAME
Terminal=false
Type=Application
Categories=Utility;Network;
EOL

chmod +x "$DESKTOP_FILE"

echo "[✓] $APP_NAME installed. Find it in your application menu."

# Prompt to build .deb
read -p "Build .deb package? (y/n): " build_deb
if [[ "$build_deb" == "y" ]]; then
    echo "[+] Building .deb package..."

    TMP_DIR="./nun-info-deb"
    rm -rf "$TMP_DIR"
    mkdir -p "$TMP_DIR/DEBIAN"
    mkdir -p "$TMP_DIR/usr/local/bin"
    mkdir -p "$TMP_DIR/usr/share/applications"
    mkdir -p "$TMP_DIR/usr/share/icons"

    # Copy files
    cp "$(dirname "$0")/../src/$SCRIPT_NAME" "$TMP_DIR/usr/local/bin/$SCRIPT_NAME"
    cp "$(dirname "$0")/../assets/images/$ICON_NAME" "$TMP_DIR/usr/share/icons/nun-info.png"

    # Desktop entry for system-wide install
    cat > "$TMP_DIR/usr/share/applications/nun-info.desktop" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Check your IP and network info
Exec=python3 /usr/local/bin/$SCRIPT_NAME
Icon=/usr/share/icons/nun-info.png
Terminal=false
Type=Application
Categories=Utility;Network;
EOL

    # Control file
    cat > "$TMP_DIR/DEBIAN/control" <<EOL
Package: nun-info
Version: 1.0
Section: utils
Priority: optional
Architecture: all
Depends: python3
Maintainer: $(whoami)
Description: Nun Info - IP and Network Information Tool
 A simple app to show your IP and network info.
EOL

    dpkg-deb --build "$TMP_DIR"
    mv nun-info-deb.deb nun-info_1.0_all.deb

    echo "[✓] .deb package created: nun-info_1.0_all.deb"
fi

# Prompt to build .exe (optional)
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

    ICON_PATH="$(dirname "$0")/../assets/images/ip-check.ico"
    echo "[+] Generating .ico icon..."
    convert "$(dirname "$0")/../assets/images/$ICON_NAME" "$ICON_PATH"

    echo "[+] Building .exe with PyInstaller..."
    pyinstaller --onefile --noconsole --icon="$ICON_PATH" "$(dirname "$0")/../src/$SCRIPT_NAME"

    echo "[✓] Windows .exe created: dist/ip-check.exe"
fi

echo "[✔] Done!"
