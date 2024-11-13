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

# Create service user and group
sudo groupadd -f $SERVICE_GROUP
sudo id -u $SERVICE_USER &>/dev/null || sudo useradd -r -s /bin/false -g $SERVICE_GROUP $SERVICE_USER

# Create installation directory
sudo mkdir -p $INSTALL_DIR
sudo chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR

# Copy application files to installation directory
sudo cp $SERVICE_SCRIPT $INSTALL_DIR/
sudo chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/$SERVICE_SCRIPT

# Create and activate virtual environment
sudo -u $SERVICE_USER $PYTHON_EXEC -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install required Python packages
pip install pixel-multiverse

# Deactivate virtual environment
deactivate

# Create systemd service file
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
sudo chmod 644 $SERVICE_FILE

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Installation and service setup complete."
