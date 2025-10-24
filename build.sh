#!/bin/bash

# --- Configuration ---
APP_NAME="nuntube"
APP_FILE="src/app.py"
LOGO_FILE="assets/download.png"
VERSION="1.0.0"
MAINTAINER="Nun"
OUTPUT_DIR="release"
DEB_ROOT="${APP_NAME}_deb"
DEB_PACKAGE_NAME="${APP_NAME}_${VERSION}_amd64.deb"
ICON_SIZE="48x48" # Standard size for menu icons

# --- 1. Setup and Cleanup ---
echo "--- Starting build process for ${APP_NAME} v${VERSION} ---"

# Check for required assets
if [ ! -f "$APP_FILE" ] || [ ! -f "$LOGO_FILE" ]; then
    echo "ERROR: Required files not found. Check paths:"
    echo "  Application: $APP_FILE"
    echo "  Logo: $LOGO_FILE"
    exit 1
fi

# Install required Python dependencies (PyInstaller and CustomTkinter)
echo "Installing/Upgrading Python dependencies inside the virtual environment..."
pip install --upgrade pyinstaller customtkinter
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install PyInstaller or CustomTkinter."
    echo "HINT: If you ran this script with 'sudo', please run it without 'sudo' after activating your virtual environment."
    exit 1
fi

# Clean up previous builds
rm -rf build dist "$DEB_ROOT" "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# --- 2. Build Windows Executable (.exe) ---
echo "--- Building Windows Executable (.exe) ---"
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --name "$APP_NAME" \
            --icon "$LOGO_FILE" \
            --add-data "$LOGO_FILE:assets" \
            "$APP_FILE"

# Copy the Windows executable to the release folder
if [ -f "dist/${APP_NAME}.exe" ]; then
    cp "dist/${APP_NAME}.exe" "$OUTPUT_DIR/"
    echo "SUCCESS: Windows executable created: ${OUTPUT_DIR}/${APP_NAME}.exe"
else
    echo "WARNING: Windows executable failed or was skipped (typically when cross-compiling on Linux without Wine)."
fi


# --- 3. Build Linux Executable (Standalone Binary) ---
echo "--- Building Linux Executable (Standalone Binary) ---"
# Running PyInstaller for Linux binary
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --name "$APP_NAME" \
            --icon "$LOGO_FILE" \
            --add-data "$LOGO_FILE:assets" \
            "$APP_FILE"

# --- 4. Package into Debian (.deb) ---

if [ ! -f "dist/${APP_NAME}" ]; then
    echo "ERROR: Linux executable 'dist/${APP_NAME}' not found. Cannot create .deb package."
    exit 1
fi

echo "--- Creating Debian (.deb) package structure and desktop files ---"

# --- DEB Structure ---
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/share/applications"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/$ICON_SIZE/apps"

# 4a. Copy the standalone executable
cp "dist/${APP_NAME}" "$DEB_ROOT/usr/bin/"
chmod 755 "$DEB_ROOT/usr/bin/$APP_NAME"

# 4b. Copy the icon file
cp "$LOGO_FILE" "$DEB_ROOT/usr/share/icons/hicolor/$ICON_SIZE/apps/$APP_NAME.png"

# 4c. Create the Desktop Entry File (.desktop)
# This file is essential for the icon to appear in the application menu
cat > "$DEB_ROOT/usr/share/applications/$APP_NAME.desktop" <<- EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=NuNTube Downloader
Comment=YouTube Channel and Playlist Downloader
Exec=/usr/bin/$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;Network;
EOL

# 4d. Create the DEBIAN/control file
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

# Build the .deb file
echo "Building final .deb package using dpkg-deb..."
dpkg-deb --build --root-owner-group "$DEB_ROOT"

if [ $? -eq 0 ]; then
    echo "SUCCESS: Debian package built: ${DEB_ROOT}.deb"
    mv "${DEB_ROOT}.deb" "$OUTPUT_DIR/$DEB_PACKAGE_NAME"
    echo "FINAL ARTIFACT: ${OUTPUT_DIR}/$DEB_PACKAGE_NAME"
else
    echo "ERROR: dpkg-deb failed to create the package."
fi

# --- 5. Final Cleanup ---
rm -rf build dist "$DEB_ROOT"
echo "--- Build process finished ---"
echo "Artifacts are available in the '${OUTPUT_DIR}' directory."
