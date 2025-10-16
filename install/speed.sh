#!/usr/bin/env fish

set APP_NAME "Nun Speed"
set PYTHON_SCRIPT "src/g-speed.py"
set APP_ICON "assets/images/speed.png"
set EXECUTABLE_NAME "nun-speed"
set DESKTOP_FILE "$HOME/.local/share/applications/$EXECUTABLE_NAME.desktop"
set VENV_DIR "$HOME/.nun_speed_venv"

echo "-------------------------------------------------"
echo "Nun Speed Installer (Fish shell)"
echo "-------------------------------------------------"

# Step 1: Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-venv python3-tk python3-pip

# Step 2: Create virtual environment
if not test -d $VENV_DIR
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
end

# Step 3: Activate venv and install Python packages
echo "Installing Python packages in venv..."
source $VENV_DIR/bin/activate.fish
pip install --upgrade pip
pip install psutil speedtest-cli pyinstaller

# Step 4: Build the executable
echo "Building the app..."
pyinstaller --name "$APP_NAME" \
            --onefile \
            --windowed \
            --add-data "$APP_ICON:assets/images" \
            "$PYTHON_SCRIPT"

# Step 5: Install executable
echo "Installing executable..."
mkdir -p $HOME/.local/bin
cp "dist/$APP_NAME" "$HOME/.local/bin/$EXECUTABLE_NAME"
chmod +x "$HOME/.local/bin/$EXECUTABLE_NAME"

# Step 6: Create .desktop launcher
echo "Creating launcher..."
mkdir -p (dirname $DESKTOP_FILE)
echo "[Desktop Entry]" > $DESKTOP_FILE
echo "Name=$APP_NAME" >> $DESKTOP_FILE
echo "Comment=System & Internet Monitor" >> $DESKTOP_FILE
echo "Exec=$HOME/.local/bin/$EXECUTABLE_NAME" >> $DESKTOP_FILE
echo "Icon="(realpath $APP_ICON) >> $DESKTOP_FILE
echo "Terminal=false" >> $DESKTOP_FILE
echo "Type=Application" >> $DESKTOP_FILE
echo "Categories=Utility;" >> $DESKTOP_FILE
chmod +x $DESKTOP_FILE

echo "-------------------------------------------------"
echo "$APP_NAME installed successfully!"
echo "You can run it via Applications menu or type '$EXECUTABLE_NAME' in terminal."
echo "-------------------------------------------------"
