#!/bin/bash

set -e

APP_NAME="Nun Media"
SCRIPT_NAME="g-media.py"
ICON_NAME="media.png"
INSTALL_DIR="$HOME/.local/share/nun-media"
DESKTOP_FILE="$HOME/.local/share/applications/nun-media.desktop"

echo "[+] Installing $APP_NAME..."

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy script and icon
cp "$(dirname "$0")/../src/$SCRIPT_NAME" "$INSTALL_DIR/"
cp "$(dirname "$0")/../assets/images/$ICON_NAME" "$INSTALL_DIR/"

# Ensure script has proper shebang
if ! head -n1 "$INSTALL_DIR/$SCRIPT_NAME" | grep -q "^#\!"; then
    sed -i '1i #!/usr/bin/env python3' "$INSTALL_DIR/$SCRIPT_NAME"
fi

# Make script executable
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Create desktop launcher
echo "[+] Creating desktop launcher..."
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Media tool using MoviePy and Rembg
Exec=$INSTALL_DIR/$SCRIPT_NAME
Icon=$INSTALL_DIR/$ICON_NAME
Terminal=false
Type=Application
Categories=Utility;Multimedia;
EOL

chmod +x "$DESKTOP_FILE"

echo "[✓] $APP_NAME installed successfully. You can find it in your application menu."

# Optional: build .deb package
read -p "Build .deb package? (y/n): " build_deb
if [[ "$build_deb" == "y" ]]; then
    echo "[+] Building .deb package..."

    TMP_DIR="./nun-media-deb"
    rm -rf "$TMP_DIR"
    mkdir -p "$TMP_DIR/DEBIAN"
    mkdir -p "$TMP_DIR/usr/local/bin"
    mkdir -p "$TMP_DIR/usr/share/applications"
    mkdir -p "$TMP_DIR/usr/share/icons"

    # Copy files to package
    cp "$INSTALL_DIR/$SCRIPT_NAME" "$TMP_DIR/usr/local/bin/$SCRIPT_NAME"
    cp "$INSTALL_DIR/$ICON_NAME" "$TMP_DIR/usr/share/icons/nun-media.png"

    # Desktop entry for .deb
    cat > "$TMP_DIR/usr/share/applications/nun-media.desktop" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Media tool using MoviePy and Rembg
Exec=/usr/local/bin/$SCRIPT_NAME
Icon=/usr/share/icons/nun-media.png
Terminal=false
Type=Application
Categories=Utility;Multimedia;
EOL

    # DEBIAN/control
    cat > "$TMP_DIR/DEBIAN/control" <<EOL
Package: nun-media
Version: 1.0
Section: utils
Priority: optional
Architecture: all
Depends: python3
Maintainer: $(whoami)
Description: Nun Media - Media Processing Tool
 A simple app to manipulate media using MoviePy and Rembg.
EOL

    dpkg-deb --build "$TMP_DIR"
    mv nun-media-deb.deb nun-media_1.0_all.deb

    echo "[✓] .deb package created: nun-media_1.0_all.deb"
fi

# Optional: build Windows .exe with PyInstaller
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

    ICON_PATH="$(dirname "$0")/../assets/images/media.ico"
    echo "[+] Generating .ico icon..."
    convert "$(dirname "$0")/../assets/images/$ICON_NAME" "$ICON_PATH"

    echo "[+] Building .exe with PyInstaller..."
    pyinstaller --onefile --noconsole --icon="$ICON_PATH" "$(dirname "$0")/../src/$SCRIPT_NAME"

    echo "[✓] Windows .exe created: dist/g-media.exe"
fi

echo "[✔] Done!"



# python3 /usr/local/bin/g-media.py
