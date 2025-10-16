#!/usr/bin/env fish
echo "🚀 Installing Nun Speed..."

set venv_dir "$HOME/nun-speed-venv"

# Create venv if not exists
if not test -d $venv_dir
    echo "📦 Creating Python virtual environment..."
    python3 -m venv $venv_dir
end

# Activate venv
source $venv_dir/bin/activate.fish

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip setuptools wheel pyinstaller customtkinter psutil speedtest-cli --break-system-packages

# Paths
set APP_NAME "Nun Speed"
set SRC_PATH "src/g-speed.py"
set ICON_PATH "assets/images/speed.png"
set DIST_PATH "dist/nun-speed"

# Build app
echo "🛠️ Building $APP_NAME..."
pyinstaller --noconfirm --onefile --name="nun-speed" --icon=$ICON_PATH $SRC_PATH

# Install to system
echo "📂 Installing executable..."
sudo cp dist/nun-speed /usr/local/bin/

# Install icon
echo "🖼️ Installing icon..."
sudo mkdir -p /usr/share/icons/hicolor/256x256/apps
sudo cp $ICON_PATH /usr/share/icons/hicolor/256x256/apps/nun-speed.png

# Desktop entry
echo "🧩 Creating desktop entry..."
echo "[Desktop Entry]
Name=Nun Speed
Comment=Check internet speed and monitor system usage
Exec=nun-speed
Icon=nun-speed
Terminal=false
Type=Application
Categories=Utility;Network;
StartupNotify=true" | sudo tee /usr/share/applications/nun-speed.desktop > /dev/null

echo "✅ Installation complete!"
echo "You can now launch Nun Speed from the app menu or by typing: nun-speed"
