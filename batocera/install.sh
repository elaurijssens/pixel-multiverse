#!/bin/bash

# Variables
SERVICE_NAME="pixel_multiverse"
INSTALL_DIR="/userdata/${SERVICE_NAME}"

PYTHON_EXEC="/usr/bin/python3"
VENV_DIR="$INSTALL_DIR/venv"

ESSCRIPT_PATH="esscript.py"
ES_CONFIG_DIR="/userdata/system/configs/emulationstation"

SERVICE_DIR="/userdata/system/services"
SERVICE_FILE="${SERVICE_DIR}/${SERVICE_NAME}"
SERVICE_CONFIG_DIR="/userdata/system/configs/${SERVICE_NAME}"
SERVICE_CONFIG="${SERVICE_NAME}.yml"
SERVICE_SCRIPT="service.py"

VISUALS_DIRECTORY="${INSTALL_DIR}/visuals"
VISUALS_REPO_URL="https://github.com/elaurijssens/pixel-multiverse-visuals/archive/refs/heads/main.zip"

DEFAULT_IMAGE_PATH="../images"
INSTALL_IMAGE_PATH="$INSTALL_DIR/images"

# List of possible event names based on the spreadsheet data
EVENT_NAMES=("quit" "reboot" "shutdown" "config-changed" "controls-changed" "settings-changed" "theme-changed"
             "game-start" "game-end" "sleep" "wake" "screensaver-start" "screensaver-stop"
             "screensaver-game-select" "system-selected" "game-selected" "start")

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

# Check if service already exists
if batocera-services list user | grep -q "$SERVICE_NAME"; then
    echo "Service $SERVICE_NAME already exists. Checking installation..."

    if [[ "$UPGRADE_MODE" == true ]]; then
        RECREATE_SERVICE_FILE=true
        RECREATE_VENV=true
        RECOPY_SERVICE_SCRIPT=true
        RECOPY_ESSCRIPT=true
        RECOPY_CONFIG=true
    else
        # Check if config file exists
        if [[ ! -f "$INSTALL_DIR/$SERVICE_CONFIG" ]]; then
            echo "Config file $SERVICE_CONFIG is missing in $INSTALL_DIR. Copying pre-existing config..."
            RECOPY_CONFIG=true
        fi

        # Check if the virtual environment exists
        if [[ ! -d "$VENV_DIR" ]]; then
            echo "Virtual environment $VENV_DIR is missing. Recreating..."
            RECREATE_VENV=true
        fi

        # Verify the service file
        if [[ ! -f "$SERVICE_FILE" ]]; then
            echo "Service file $SERVICE_FILE is missing. Recreating..."
            RECREATE_SERVICE_FILE=true
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
    RECOPY_CONFIG=true
fi

# Create installation directories if missing
if [[ ! -d "$INSTALL_DIR" ]]; then
    mkdir -p $INSTALL_DIR || error_exit "Failed to create installation directory $INSTALL_DIR."
else
    echo "Installation directory $INSTALL_DIR already exists."
fi

if [[ ! -d "$SERVICE_DIR" ]]; then
    mkdir -p $SERVICE_DIR || error_exit "Failed to create configuration directory $SERVICE_DIR."
else
    echo "Installation directory $SERVICE_DIR already exists."
fi

if [[ ! -d "$SERVICE_CONFIG_DIR" ]]; then
    mkdir -p $SERVICE_CONFIG_DIR || error_exit "Failed to create configuration directory $SERVICE_CONFIG_DIR."
else
    echo "Installation directory $SERVICE_CONFIG_DIR already exists."
fi

# Copy service script if required
if [[ "$RECOPY_SERVICE_SCRIPT" == true ]]; then
    if [[ -f "$SERVICE_SCRIPT" ]]; then
        cp "$SERVICE_SCRIPT" "$INSTALL_DIR/" || error_exit "Failed to copy $SERVICE_SCRIPT to $INSTALL_DIR."
        chmod 755 "$INSTALL_DIR/$SERVICE_SCRIPT" || error_exit "Failed to set world-executable permissions on $SERVICE_SCRIPT."
        echo "Service script copied to $INSTALL_DIR."
    else
        error_exit "Service script $SERVICE_SCRIPT not found in the current directory."
    fi
fi

# Copy esscript.py if required
if [[ "$RECOPY_ESSCRIPT" == true ]]; then
    if [[ -f "$ESSCRIPT_PATH" ]]; then
        cp "$ESSCRIPT_PATH" "$INSTALL_DIR/" || error_exit "Failed to copy $ESSCRIPT_PATH to $INSTALL_DIR."
        chmod 755 "$INSTALL_DIR/$ESSCRIPT_PATH" || error_exit "Failed to set world-executable permissions on $ESSCRIPT_PATH."
        echo "Esscript.py copied to $INSTALL_DIR and set to world-executable."
    else
        error_exit "Esscript.py not found in the current directory."
    fi
fi

# Copy configuration file if it’s a fresh installation or missing in the installation directory
if [[ "$RECOPY_CONFIG" == true && "$UPGRADE_MODE" == false ]]; then
    if [[ -f "$SERVICE_CONFIG" ]]; then
        cp "$SERVICE_CONFIG" "$INSTALL_DIR/" || error_exit "Failed to copy $SERVICE_CONFIG to $INSTALL_DIR."
        echo "Configuration file $SERVICE_CONFIG copied to $INSTALL_DIR."
    else
        error_exit "Configuration file $SERVICE_CONFIG not found in the current directory."
    fi
fi


# Check if the default image exists and copy it to the installation directory
if [ -d "$DEFAULT_IMAGE_PATH" ]; then
    mkdir -p "$INSTALL_IMAGE_PATH"
    cp -r "$DEFAULT_IMAGE_PATH/." "$INSTALL_IMAGE_PATH" || error_exit "Failed to copy default image to $INSTALL_DIR."
    echo "Default image copied to $INSTALL_DIR."
else
    error_exit "Default image not found at $DEFAULT_IMAGE_PATH. Ensure the image is in the correct location."
fi

if [ ! -d "$VISUALS_DIRECTORY" ]; then
    echo "Cloning $VISUALS_REPO_URL to $VISUALS_DIRECTORY..."
    {
        mkdir -p "$VISUALS_DIRECTORY"
        wget https://github.com/elaurijssens/pixel-multiverse-visuals/archive/refs/heads/main.zip -O /tmp/pixel-multiverse-visuals.zip
        bsdtar -xf /tmp/pixel-multiverse-visuals.zip -s'|[^/]*/||' -C "$VISUALS_DIRECTORY"
    } || {
        echo "Failed to clone the repository."
        exit 1
    }
else
    echo "Repository already exists at $VISUALS_DIRECTORY. Skipping clone."
fi

# Create and activate virtual environment if required
if [[ "$RECREATE_VENV" == true ]]; then
    $PYTHON_EXEC -m venv --system-site-packages --symlinks $VENV_DIR || error_exit "Failed to create virtual environment in $VENV_DIR."
    echo "Virtual environment created."
fi

# Install required Python packages from requirements.txt
if [[ -f "requirements.txt" ]]; then
    bash -c "source $VENV_DIR/bin/activate && pip install -r requirements.txt" || error_exit "Failed to install required Python packages from requireme
nts.txt."
else
    error_exit "requirements.txt not found. Please ensure it exists in the current directory."
fi


# Recreate systemd service file if required
if [[ "$RECREATE_SERVICE_FILE" == true ]]; then
    if [[ -f "$SERVICE_NAME".sh ]]; then
        cp "$SERVICE_NAME".sh "$SERVICE_FILE" || error_exit "Failed to copy $SERVICE_NAME.sh to $SERVICE_FILE."
        # Set permissions for the service file
        chmod 755 "$SERVICE_FILE" || error_exit "Failed to set permissions on service file $SERVICE_FILE."
        echo "Service file $SERVICE_FILE copied."
    else
        echo "Service file $SERVICE_FILE already exists and is valid."
    fi
fi

# Create symlinks in the user's home directory for each event
for event in "${EVENT_NAMES[@]}"; do
    EVENT_DIR="$ES_CONFIG_DIR/scripts/$event"
    mkdir -p "$EVENT_DIR" || error_exit "Failed to create directory $EVENT_DIR."
    ln -sf "$INSTALL_DIR/$ESSCRIPT_PATH" "$EVENT_DIR/$ESSCRIPT_PATH" || error_exit "Failed to create symlink for $event in $EVENT_DIR."
    echo "Symlink created for $event in $EVENT_DIR."
done

# Reload systemd and enable/start the service
batocera-services enable "$SERVICE_NAME" || error_exit "Failed to enable $SERVICE_NAME service."
batocera-services restart "$SERVICE_NAME" || error_exit "Failed to start $SERVICE_NAME service."

echo "Installation and service setup complete."
