#!/bin/bash

# Variables
SERVICE_NAME="pixel-multiverse"
SERVICE_USER="pixelpusher"
SERVICE_GROUP="pixelpusher"
INSTALL_DIR="/opt/$SERVICE_NAME"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
PYTHON_EXEC="/usr/bin/python3"
SERVICE_SCRIPT="service.py"

# Function to print error messages
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Check if service already exists
if systemctl list-units --full -all | grep -q "$SERVICE_NAME.service"; then
    echo "Service $SERVICE_NAME already exists. Checking installation..."

    # Verify the service file
    if [[ ! -f "$SERVICE_FILE" ]]; then
        error_exit "Service file $SERVICE_FILE is missing."
    fi

    # Check if the virtual environment exists
    if [[ ! -d "$VENV_DIR" ]]; then
        error_exit "Virtual environment $VENV_DIR is missing."
    fi

    # Check if the service script exists
    if [[ ! -f "$INSTALL_DIR/$SERVICE_SCRIPT" ]]; then
        error_exit "Service script $SERVICE_SCRIPT is missing in $INSTALL_DIR."
    fi

    echo "Service $SERVICE_NAME is already correctly installed."
    exit 0
fi

# Create service user and group if they do not exist
if ! id -u $SERVICE_USER &>/dev/null; then
    sudo groupadd -f $SERVICE_GROUP || error_exit "Failed to create group $SERVICE_GROUP."
    sudo useradd -r -s /bin/false -g $SERVICE_GROUP $SERVICE_USER || error_exit "Failed to create user $SERVICE_USER."
else
    echo "User $SERVICE_USER already exists."
fi

# Create installation directory
if [[ ! -d "$INSTALL_DIR" ]]; then
    sudo mkdir -p $INSTALL_DIR || error_exit "Failed to create installation directory $INSTALL_DIR."
    sudo chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
else
    echo "Installation directory $INSTALL_DIR already exists."
fi

# Copy application files to installation directory
if [[ -f "$SERVICE_SCRIPT" ]]; then
    sudo cp $SERVICE_SCRIPT $INSTALL_DIR/ || error_exit "Failed to copy $SERVICE_SCRIPT to $INSTALL_DIR."
    sudo chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/$SERVICE_SCRIPT
else
    error_exit "Service script $SERVICE_SCRIPT not found in the current directory."
fi

# Create and activate virtual environment if it doesn't exist
if [[ ! -d "$VENV_DIR" ]]; then
    sudo -u $SERVICE_USER $PYTHON_EXEC -m venv $VENV_DIR || error_exit "Failed to create virtual environment in $VENV_DIR."
else
    echo "Virtual environment already exists in $VENV_DIR."
fi

# Install required Python packages
source $VENV_DIR/bin/activate || error_exit "Failed to activate virtual environment."
pip install pixel-multiverse || error_exit "Failed to install pixel-multiverse package."
deactivate

# Create systemd service file
if [[ ! -f "$SERVICE_FILE" ]]; then
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
    sudo chmod 644 $SERVICE_FILE || error_exit "Failed to set permissions on service file $SERVICE_FILE."
else
    echo "Service file $SERVICE_FILE already exists."
fi

# Reload systemd and enable/start the service
sudo systemctl daemon-reload || error_exit "Failed to reload systemd."
sudo systemctl enable $SERVICE_NAME || error_exit "Failed to enable $SERVICE_NAME service."
sudo systemctl start $SERVICE_NAME || error_exit "Failed to start $SERVICE_NAME service."

echo "Installation and service setup complete."
