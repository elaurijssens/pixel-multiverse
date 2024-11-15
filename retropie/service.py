import socket
import os
import sys
import yaml
import logging
from pixelpusher import (LedMatrix, DISPLAY_INTERSTATE75_128x32, DISPLAY_GALACTIC_UNICORN, COLOR_ORDER_RGB,
                         COLOR_ORDER_RBG, COLOR_ORDER_BGR, COLOR_ORDER_BRG, COLOR_ORDER_GRB, COLOR_ORDER_GBR)


# Define paths
SOCKET_PATH = "/tmp/pixel_multiverse.sock"
CONFIG_PATH = "/opt/pixel-multiverse/pixel-multiverse.yml"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
logger = logging.getLogger("PixelMultiverseService")

# Load configuration
config = {}
try:
    with open(CONFIG_PATH, "r") as file:
        config = yaml.safe_load(file)
        logger.info("Configuration loaded successfully from %s", CONFIG_PATH)
except FileNotFoundError:
    logger.error("Configuration file not found at %s. Ensure it is in the correct location.", CONFIG_PATH)
    sys.exit(1)
except yaml.YAMLError as e:
    logger.error("Error parsing configuration file: %s", e)
    sys.exit(1)

# Set logging level
logging_level = config.get("general", {}).get("logging", {}).get("level", "INFO").upper()
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.info("Logging level set to %s", logging_level)

# Process Marquee Section
marquee_config = config.get("general", {}).get("marquee", {})
marquee_enabled = str(marquee_config.get("enabled", "false")).strip().lower() == "true"
if marquee_enabled:
    # Map display type
    display_type = marquee_config.get("type", "").upper()
    display_mapping = {
        "I75_128X32": DISPLAY_INTERSTATE75_128x32,
        "GALACTIC_UNICORN": DISPLAY_GALACTIC_UNICORN
    }
    display = display_mapping.get(display_type)
    if display is None:
        valid_types = ", ".join(display_mapping.keys())
        logger.error("Invalid marquee type '%s' in configuration. Expected one of: %s",
                     display_type, valid_types)
        sys.exit(1)

    # Check connection path
    connection_path = marquee_config.get("connection")
    if not connection_path or not os.path.exists(connection_path):
        logger.error("Connection path '%s' does not exist. Ensure the path is correct.", connection_path)
        sys.exit(1)

    # Define color order mapping explicitly
    color_order_mapping = {
        "RGB": COLOR_ORDER_RGB,
        "RBG": COLOR_ORDER_RBG,
        "BGR": COLOR_ORDER_BGR,
        "BRG": COLOR_ORDER_BRG,
        "GRB": COLOR_ORDER_GRB,
        "GBR": COLOR_ORDER_GBR
    }

    # Set color order
    color_order = marquee_config.get("color_order", "RGB").upper()
    if color_order not in color_order_mapping:
        logger.error("Invalid color order '%s'. Expected one of %s.", color_order,
                     ", ".join(color_order_mapping.keys()))
        sys.exit(1)
    color_order_constant = color_order_mapping[color_order]

    # Instantiate LedMatrix
    try:
        marquee = LedMatrix(display=display, serial_port_path=connection_path, color_order=color_order_constant,
                            compress=True)
        logger.info("Marquee successfully initialized with type '%s', connection '%s', color order '%s'.",
                    display_type, connection_path, color_order)
    except Exception as e:
        logger.error("Failed to initialize marquee: %s", e)
        sys.exit(1)

    default_image_path = marquee_config.get("default_image", "/opt/pixel-multiverse/default.png")
    try:
        marquee.display_image(default_image_path, rescale=True)
        logger.info("Displayed default image from %s.", default_image_path)
    except Exception as e:
        logger.error("Failed to display default image: %s", e)
        sys.exit(1)

else:
    logger.info("Marquee is disabled in the configuration.")

# Socket handling and remaining code here...


# Clean up the socket file if it already exists
if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

# Set up the Unix socket
server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Define event handlers
def handle_quit(arguments):
    logger.info("Handling 'quit' event with arguments: %s", arguments)

def handle_reboot(arguments):
    logger.info("Handling 'reboot' event with arguments: %s", arguments)

def handle_shutdown(arguments):
    logger.info("Handling 'shutdown' event with arguments: %s", arguments)

def handle_config_changed(arguments):
    logger.info("Handling 'config-changed' event with arguments: %s", arguments)

def handle_controls_changed(arguments):
    logger.info("Handling 'controls-changed' event with arguments: %s", arguments)

def handle_settings_changed(arguments):
    logger.info("Handling 'settings-changed' event with arguments: %s", arguments)

def handle_theme_changed(arguments):
    logger.info("Handling 'theme-changed' event with arguments: %s", arguments)

def handle_game_start(arguments):
    logger.info("Handling 'game-start' event with arguments: %s", arguments)

def handle_game_end(arguments):
    logger.info("Handling 'game-end' event with arguments: %s", arguments)

def handle_sleep(arguments):
    logger.info("Handling 'sleep' event with arguments: %s", arguments)

def handle_wake(arguments):
    logger.info("Handling 'wake' event with arguments: %s", arguments)

def handle_screensaver_start(arguments):
    logger.info("Handling 'screensaver-start' event with arguments: %s", arguments)

def handle_screensaver_stop(arguments):
    logger.info("Handling 'screensaver-stop' event with arguments: %s", arguments)

def handle_screensaver_game_select(arguments):
    logger.info("Handling 'screensaver-game-select' event with arguments: %s", arguments)

def handle_system_select(arguments):
    logger.info("Handling 'system-select' event with arguments: %s", arguments)

def handle_game_select(arguments):
    logger.info("Handling 'game-select' event with arguments: %s", arguments)

# Add handlers for all defined events
event_handlers = {
    "quit": handle_quit,
    "reboot": handle_reboot,
    "shutdown": handle_shutdown,
    "config-changed": handle_config_changed,
    "controls-changed": handle_controls_changed,
    "settings-changed": handle_settings_changed,
    "theme-changed": handle_theme_changed,
    "game-start": handle_game_start,
    "game-end": handle_game_end,
    "sleep": handle_sleep,
    "wake": handle_wake,
    "screensaver-start": handle_screensaver_start,
    "screensaver-stop": handle_screensaver_stop,
    "screensaver-game-select": handle_screensaver_game_select,
    "system-select": handle_system_select,
    "game-select": handle_game_select,
}

# Function to process an incoming event
def process_event(event_name, arguments):
    handler = event_handlers.get(event_name)
    if handler:
        try:
            handler(arguments)
        except Exception as e:
            logger.error("Error while handling event '%s': %s", event_name, e)
    else:
        logger.warning("Unhandled event '%s' with arguments: %s", event_name, arguments)

# Event loop for processing incoming messages
try:
    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()
        with client_socket:
            while True:
                data = client_socket.recv(1024)  # Receive data from client
                if not data:
                    break  # No more data; client has closed the connection
                try:
                    # Parse the incoming JSON message
                    message = yaml.safe_load(data.decode().strip())
                    event_name = message.get("event")
                    arguments = message.get("arguments", {})
                    logger.debug("Received event '%s' with arguments: %s", event_name, arguments)
                    process_event(event_name, arguments)
                except Exception as e:
                    logger.error("Failed to process incoming message: %s", e)

except Exception as e:
    logger.error("Error: %s", e)
finally:
    # Clean up on exit
    server_socket.close()
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    logger.info("Server shut down.")
