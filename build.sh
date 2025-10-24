#!/bin/bash

APP_NAME="nuntube"
APP_FILE="src/app.py"
LOGO_FILE="assets/download.png"
VERSION="1.0.0"
MAINTAINER="Nun"
OUTPUT_DIR="release"
DEB_ROOT="${APP_NAME}_deb"
DEB_PACKAGE_NAME="${APP_NAME}_${VERSION}_amd64.deb"

echo "--- Starting build process for ${APP_NAME} v${VERSION} ---"

if [ ! -f "$APP_FILE" ] || [ ! -f "$LOGO_FILE" ]; then
    echo "ERROR: Required files not found. Check paths:"
    echo "  Application: $APP_FILE"
    echo "  Logo: $LOGO_FILE"
    exit 1
fi

echo "Installing/Upgrading Python dependencies inside the virtual environment..."
pip install --upgrade pyinstaller customtkinter
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install PyInstaller or CustomTkinter."
    echo "HINT: If you ran this script with 'sudo', please run it without 'sudo' after activating your virtual environment."
    exit 1
fi

rm -rf build dist "$DEB_ROOT" "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "--- Building Windows Executable (.exe) ---"
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --name "$APP_NAME" \
            --icon "$LOGO_FILE" \
            "$APP_FILE"

if [ -f "dist/${APP_NAME}.exe" ]; then
    cp "dist/${APP_NAME}.exe" "$OUTPUT_DIR/"
    echo "SUCCESS: Windows executable created: ${OUTPUT_DIR}/${APP_NAME}.exe"
else
    echo "WARNING: Windows executable failed or was skipped (typically when cross-compiling on Linux without Wine)."
fi


echo "--- Building Linux Executable (Standalone Binary) ---"
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --name "$APP_NAME" \
            --icon "$LOGO_FILE" \
            "$APP_FILE"


if [ ! -f "dist/${APP_NAME}" ]; then
    echo "ERROR: Linux executable 'dist/${APP_NAME}' not found. Cannot create .deb package."
    exit 1
fi

echo "--- Creating Debian (.deb) package structure ---"

mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/DEBIAN"

cp "dist/${APP_NAME}" "$DEB_ROOT/usr/bin/"

chmod 755 "$DEB_ROOT/usr/bin/$APP_NAME"

cat > "$DEB_ROOT/DEBIAN/control" <<- EOL
Package: $APP_NAME
Version: $VERSION
Architecture: amd64
Maintainer: $MAINTAINER
Installed-Size: $(du -s "$DEB_ROOT" | awk '{print $1}')
Priority: optional
Section: utils
Description: YouTube Channel Downloader built with CustomTkinter and PyInstaller.
 Depends: python3, python3-pip, yt-dlp
Homepage: 

EOL

echo "Building final .deb package using dpkg-deb..."
dpkg-deb --build --root-owner-group "$DEB_ROOT"

if [ $? -eq 0 ]; then
    echo "SUCCESS: Debian package built: ${DEB_ROOT}.deb"
    mv "${DEB_ROOT}.deb" "$OUTPUT_DIR/$DEB_PACKAGE_NAME"
    echo "FINAL ARTIFACT: ${OUTPUT_DIR}/$DEB_PACKAGE_NAME"
else
    echo "ERROR: dpkg-deb failed to create the package."
fi

rm -rf build dist "$DEB_ROOT"
echo "--- Build process finished ---"
echo "Artifacts are available in the '${OUTPUT_DIR}' directory."
