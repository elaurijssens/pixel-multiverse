#!/bin/bash

# Define the Unix socket path
SOCKET_PATH="/tmp/pixel_multiverse.sock"

# Extract the event name from the script's path
EVENT_NAME=$(basename "$(dirname "$0")")

# Define argument names based on the event type
declare -A ARGUMENT_NAMES
ARGUMENT_NAMES=(
    ["quit"]="quit_mode"
    ["theme-changed"]="new_theme old_theme"
    ["game-start"]="rom_path rom_name game_name"
    ["screensaver-game-select"]="system_name rom_path game_name media"
    ["system-select"]="system_name access_type"
    ["game-select"]="system_name rom_path game_name access_type"
)

# Prepare JSON payload
ARGUMENTS_JSON="{}"
if [[ -n "${ARGUMENT_NAMES[$EVENT_NAME]}" ]]; then
    ARGUMENTS_JSON="{"
    index=1
    for arg_name in ${ARGUMENT_NAMES[$EVENT_NAME]}; do
        eval "value=\${$index}"
        if [[ -n "$value" ]]; then
            ARGUMENTS_JSON+="\"$arg_name\": \"$value\""
            ((index++))
            if [[ $index -le $# ]]; then
                ARGUMENTS_JSON+=", "
            fi
        fi
    done
    ARGUMENTS_JSON+="}"
fi

# Complete JSON message to send
MESSAGE="{ \"event\": \"$EVENT_NAME\", \"arguments\": $ARGUMENTS_JSON }"

# Function to send a message to the Unix socket
send_to_socket() {
    if [[ -w $SOCKET_PATH ]]; then
        echo "$1" | socat - UNIX-CONNECT:"$SOCKET_PATH"
    else
        echo "Error: Cannot write to socket at $SOCKET_PATH"
        exit 1
    fi
}

# Send JSON message to the daemon
send_to_socket "$MESSAGE"
