#!/usr/bin/python3

import os
import sys
import socket
import json

# Define the Unix socket path
SOCKET_PATH = "/run/pixel_multiverse.sock"

# Extract the event name from the directory containing the symlink
event_name = os.path.basename(os.path.dirname(sys.argv[0]))

# Argument names for each event type
argument_names = {
    "quit": ["quit_mode"],
    "theme-changed": ["new_theme", "old_theme"],
    "game-start": ["rom_path", "rom_name", "game_name"],
    "screensaver-game-select": ["system_name", "rom_path", "game_name", "media"],
    "system-selected": ["system_name", "access_type"],
    "game-selected": ["system_name", "rom_path", "game_name", "access_type"]
}

# Prepare the arguments dictionary based on the event type
arguments = {}
if event_name in argument_names:
    for i, arg_name in enumerate(argument_names[event_name]):
        if i < len(sys.argv) - 1:  # sys.argv[0] is the script name
            arguments[arg_name] = sys.argv[i + 1]
else:
    arguments = {}  # Empty arguments if the event has no predefined arguments

# Prepare JSON message
message = {
    "event": event_name,
    "arguments": arguments
}

# Send the JSON message to the Unix socket
try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(message).encode("utf-8"))
        print(f"Sent to daemon: {json.dumps(message)}")
except FileNotFoundError:
    print(f"Error: Unix socket at {SOCKET_PATH} not found.")
    sys.exit(1)
except PermissionError:
    print(f"Error: Permission denied when accessing {SOCKET_PATH}.")
    sys.exit(1)
except Exception as e:
    print(f"Error: Failed to send message to daemon: {e}")
    sys.exit(1)
