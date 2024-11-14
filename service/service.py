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
        logger.error("Invalid marquee type '%s' in configuration. Expected one of: %s", display_type, valid_types)
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
        logger.info("Marquee successfully initialized with type '%s', connection '%s', color order '%s'.", display_type,
                    connection_path, color_order)
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

try:
    # Bind the socket to the path and listen for incoming connections
    server_socket.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)
    server_socket.listen(1)
    logger.info(f"Listening on {SOCKET_PATH}...")

    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()

        with client_socket:
            while True:
                data = client_socket.recv(1024)  # Receive data from client
                if not data:
                    # No more data; client has closed the connection
                    break
                # Log received data (in real use, replace this with actual handling logic)
                logger.info("Received: %s", data.decode().strip())

except Exception as e:
    logger.error("Error: %s", e)
finally:
    # Clean up on exit
    server_socket.close()
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    logger.info("Server shut down.")
