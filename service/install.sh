#!/bin/bash

# Variables
SERVICE_NAME="pixel-multiverse"
SERVICE_USER="pixelpusher"
SERVICE_GROUP="pixelpusher"
INSTALL_DIR="/opt/$SERVICE_NAME"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
ESSCRIPT_PATH="esscript.py"
PYTHON_EXEC="/usr/bin/python3"
SERVICE_SCRIPT="service.py"

# List of possible event names based on the spreadsheet data
EVENT_NAMES=("quit" "reboot" "shutdown" "config-changed" "controls-changed" "settings-changed" "theme-changed"
             "game-start" "game-end" "sleep" "wake" "screensaver-start" "screensaver-stop"
             "screensaver-game-select" "system-select" "game-select")

# Parse command-line arguments
UPGRADE_MODE=false
for arg in "$@"; do
    if [[ "$arg" == "--upgrade" ]]; then
        UPGRADE_MODE=true
    fi
done

# Function to print error messages
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Check for systemd
if ! pidof systemd &>/dev/null; then
    error_exit "Systemd is not running. This installer requires a systemd-based Linux distribution."
fi

# Check for socat and install if missing
if ! command -v socat &>/dev/null; then
    echo "socat is not installed. Installing socat..."

    if command -v apt-get &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y socat || error_exit "Failed to install socat using apt-get."
    elif command -v yum &>/dev/null; then
        sudo yum install -y socat || error_exit "Failed to install socat using yum."
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y socat || error_exit "Failed to install socat using dnf."
    else
        error_exit "No compatible package manager found. Please install socat manually."
    fi
else
    echo "socat is already installed."
fi

# Check if service already exists
if systemctl list-units --full -all | grep -q "$SERVICE_NAME.service"; then
    echo "Service $SERVICE_NAME already exists. Checking installation..."

    if [[ "$UPGRADE_MODE" == true ]]; then
        RECREATE_SERVICE_FILE=true
        RECREATE_VENV=true
        RECOPY_SERVICE_SCRIPT=true
        RECOPY_ESSCRIPT=true
    else
        # Verify the service file
        if [[ ! -f "$SERVICE_FILE" ]]; then
            echo "Service file $SERVICE_FILE is missing. Recreating..."
            RECREATE_SERVICE_FILE=true
        fi

        # Check if the virtual environment exists
        if [[ ! -d "$VENV_DIR" ]]; then
            echo "Virtual environment $VENV_DIR is missing. Recreating..."
            RECREATE_VENV=true
        fi

        # Check if the service script exists
        if [[ ! -f "$INSTALL_DIR/$SERVICE_SCRIPT" ]]; then
            echo "Service script $SERVICE_SCRIPT is missing in $INSTALL_DIR. Recopying..."
            RECOPY_SERVICE_SCRIPT=true
        fi

        # Check if esscript exists
        if [[ ! -f "$INSTALL_DIR/$ESSCRIPT_PATH" ]]; then
            echo "Esscript $ESSCRIPT_PATH is missing in $INSTALL_DIR. Recopying..."
            RECOPY_ESSCRIPT=true
        fi
    fi
else
    echo "Service $SERVICE_NAME does not exist. Proceeding with fresh installation..."
    RECREATE_SERVICE_FILE=true
    RECREATE_VENV=true
    RECOPY_SERVICE_SCRIPT=true
    RECOPY_ESSCRIPT=true
fi

# Create service user and group if they do not exist
if ! id -u $SERVICE_USER &>/dev/null; then
    sudo groupadd -f $SERVICE_GROUP || error_exit "Failed to create group $SERVICE_GROUP."
    sudo useradd -r -s /bin/false -g $SERVICE_GROUP $SERVICE_USER || error_exit "Failed to create user $SERVICE_USER."
else
    echo "User $SERVICE_USER already exists."
fi

# Create installation directory if missing
if [[ ! -d "$INSTALL_DIR" ]]; then
    sudo mkdir -p $INSTALL_DIR || error_exit "Failed to create installation directory $INSTALL_DIR."
    sudo chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
else
    echo "Installation directory $INSTALL_DIR already exists."
fi

# Copy service script if required
if [[ "$RECOPY_SERVICE_SCRIPT" == true ]]; then
    if [[ -f "$SERVICE_SCRIPT" ]]; then
        sudo cp "$SERVICE_SCRIPT" "$INSTALL_DIR/" || error_exit "Failed to copy $SERVICE_SCRIPT to $INSTALL_DIR."
        sudo chown $SERVICE_USER:$SERVICE_GROUP "$INSTALL_DIR/$SERVICE_SCRIPT"
        echo "Service script copied to $INSTALL_DIR."
    else
        error_exit "Service script $SERVICE_SCRIPT not found in the current directory."
    fi
fi

# Copy esscript.py if required
if [[ "$RECOPY_ESSCRIPT" == true ]]; then
    if [[ -f "$ESSCRIPT_PATH" ]]; then
        sudo cp "$ESSCRIPT_PATH" "$INSTALL_DIR/" || error_exit "Failed to copy $ESSCRIPT_PATH to $INSTALL_DIR."
        sudo chmod 755 "$INSTALL_DIR/$ESSCRIPT_PATH" || error_exit "Failed to set world-executable permissions on $ESSCRIPT_PATH."
        sudo chown $SERVICE_USER:$SERVICE_GROUP "$INSTALL_DIR/$ESSCRIPT_PATH"
        echo "Esscript.py copied to $INSTALL_DIR and set to world-executable."
    else
        error_exit "Esscript.py not found in the current directory."
    fi
fi

# Create and activate virtual environment if required
if [[ "$RECREATE_VENV" == true ]]; then
    sudo -u $SERVICE_USER $PYTHON_EXEC -m venv $VENV_DIR || error_exit "Failed to create virtual environment in $VENV_DIR."
    echo "Virtual environment created."
fi

# Install required Python packages
sudo -u $SERVICE_USER bash -c "source $VENV_DIR/bin/activate && pip install pixel-multiverse" || error_exit "Failed to install pixel-multiverse package."

# Recreate systemd service file if required
if [[ "$RECREATE_SERVICE_FILE" == true ]]; then
    sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Pixel Multiverse Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/$SERVICE_SCRIPT
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

    # Set permissions for the service file
    sudo chmod 644 "$SERVICE_FILE" || error_exit "Failed to set permissions on service file $SERVICE_FILE."
    echo "Service file $SERVICE_FILE created."
else
    echo "Service file $SERVICE_FILE already exists and is valid."
fi

# Reload systemd and enable/start the service
sudo systemctl daemon-reload || error_exit "Failed to reload systemd."
sudo systemctl enable "$SERVICE_NAME" || error_exit "Failed to enable $SERVICE_NAME service."
sudo systemctl restart "$SERVICE_NAME" || error_exit "Failed to start $SERVICE_NAME service."

# Create symlinks in the user's home directory for each event
USER_HOME=$(eval echo "~$SUDO_USER")
SCRIPT_DIR="$USER_HOME/.emulationstation/scripts"
for event in "${EVENT_NAMES[@]}"; do
    EVENT_DIR="$SCRIPT_DIR/$event"
    mkdir -p "$EVENT_DIR" || error_exit "Failed to create directory $EVENT_DIR."
    ln -sf "$INSTALL_DIR/$ESSCRIPT_PATH" "$EVENT_DIR/$ESSCRIPT_PATH" || error_exit "Failed to create symlink for $event in $EVENT_DIR."
    echo "Symlink created for $event in $EVENT_DIR."
done

echo "Installation and service setup complete."
