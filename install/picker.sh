#!/bin/bash


set -e

APP_NAME="Nun Picker"
SCRIPT_NAME="picker.py"
ICON_NAME="color-picker.png"
INSTALL_DIR="$HOME/.local/share/nun-picker"
DESKTOP_FILE="$HOME/.local/share/applications/nun-picker.desktop"

echo "[+] Installing $APP_NAME..."

mkdir -p "$INSTALL_DIR"

cp "$(dirname "$0")/../src/$SCRIPT_NAME" "$INSTALL_DIR/"
cp "$(dirname "$0")/../assets/images/$ICON_NAME" "$INSTALL_DIR/"

echo "[+] Creating desktop launcher..."

cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Pick and identify colors from your screen
Exec=python3 $INSTALL_DIR/$SCRIPT_NAME
Icon=$INSTALL_DIR/$ICON_NAME
Terminal=false
Type=Application
Categories=Graphics;Utility;
EOL

chmod +x "$DESKTOP_FILE"

echo "[✓] $APP_NAME installed successfully. You can find it in your application menu."

read -p "Build .deb package? (y/n): " build_deb
if [[ "$build_deb" == "y" ]]; then
    echo "[+] Building .deb package..."

    TMP_DIR="./nun-picker-deb"
    rm -rf "$TMP_DIR"
    mkdir -p "$TMP_DIR/DEBIAN"
    mkdir -p "$TMP_DIR/usr/local/bin"
    mkdir -p "$TMP_DIR/usr/share/applications"
    mkdir -p "$TMP_DIR/usr/share/icons"

    cp "$(dirname "$0")/../src/$SCRIPT_NAME" "$TMP_DIR/usr/local/bin/$SCRIPT_NAME"
    cp "$(dirname "$0")/../assets/images/$ICON_NAME" "$TMP_DIR/usr/share/icons/nun-picker.png"

    cat > "$TMP_DIR/usr/share/applications/nun-picker.desktop" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Pick and identify colors from your screen
Exec=python3 /usr/local/bin/$SCRIPT_NAME
Icon=/usr/share/icons/nun-picker.png
Terminal=false
Type=Application
Categories=Graphics;Utility;
EOL

    cat > "$TMP_DIR/DEBIAN/control" <<EOL
Package: nun-picker
Version: 1.0
Section: graphics
Priority: optional
Architecture: all
Depends: python3
Maintainer: $(whoami)
Description: Nun Picker - Color Picker Tool
 A simple and lightweight tool to pick and identify colors from your screen.
EOL

    dpkg-deb --build "$TMP_DIR"
    mv nun-picker-deb.deb nun-picker_1.0_all.deb

    echo "[✓] .deb package created: nun-picker_1.0_all.deb"
fi

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

    ICON_PATH="$(dirname "$0")/../assets/images/nun-picker.ico"
    echo "[+] Generating .ico icon..."
    convert "$(dirname "$0")/../assets/images/$ICON_NAME" "$ICON_PATH"

    echo "[+] Building .exe with PyInstaller..."
    pyinstaller --onefile --noconsole --icon="$ICON_PATH" "$(dirname "$0")/../src/$SCRIPT_NAME"

    echo "[✓] Windows .exe created: dist/picker.exe"
fi

echo "[✔] Done!"
