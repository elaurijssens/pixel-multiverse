import socket
import os
import sys
import yaml
import logging
from pixelpusher import (LedMatrix, DISPLAY_INTERSTATE75_128x32, DISPLAY_GALACTIC_UNICORN, COLOR_ORDER_RGB,
                         COLOR_ORDER_RBG, COLOR_ORDER_BGR, COLOR_ORDER_BRG, COLOR_ORDER_GRB, COLOR_ORDER_GBR)
from PIL import Image, ImageDraw, ImageFont

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

def overlay_text_on_image(image_path, text, output_path, logger):
    """
    Overlays text on an image and saves the result.

    Args:
        image_path (str): Path to the base image.
        text (str): Text to overlay.
        output_path (str): Path to save the resulting image.
        logger (Logger): Logger object for logging messages.
    """
    try:
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            # Set font size proportional to the image size
            font_size = int(img.height / 10)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

            # Calculate text size and position
            text_width, text_height = draw.textsize(text, font=font)
            text_x = (img.width - text_width) / 2
            text_y = img.height - text_height - 10  # Padding from the bottom

            # Add text overlay
            draw.text((text_x, text_y), text, fill="white", font=font)

            # Save the updated image
            img.save(output_path)
            logger.info("Overlayed text '%s' on image and saved to %s.", text, output_path)
    except Exception as e:
        logger.error("Failed to overlay text on image %s: %s", image_path, e)

def search_and_display_image(system_name, game_name, marquee, marquee_config, logger):
    """
    Search and display an image based on system_name and game_name.

    Args:
        system_name (str): Name of the system.
        game_name (str): Name of the game (can be None).
        marquee (LedMatrix): Marquee object to display the image.
        marquee_config (dict): Configuration for the marquee.
        logger (Logger): Logger object for logging messages.

    Returns:
        bool: True if an image was successfully displayed, False otherwise.
    """
    image_path = marquee_config.get("image_dir", "/opt/pixel-multiverse/marquee")
    image_extensions = marquee_config.get("image_extensions", ["gif", "png", "jpg"])
    create_placeholders = str(marquee_config.get("create_placeholders", "false")).strip().lower() == "true"
    default_image_path = marquee_config.get("default_image", "/opt/pixel-multiverse/default.png")

    # Construct the system path
    system_path = os.path.join(image_path, system_name)

    # Ensure the system directory exists
    if create_placeholders and not os.path.exists(system_path):
        try:
            os.makedirs(system_path, exist_ok=True)
            logger.info("Created directory for system: %s", system_path)
        except Exception as e:
            logger.error("Failed to create directory for system %s: %s", system_path, e)
            return False

    # If game_name is provided, attempt to display a game-specific image
    if game_name:
        game_image = None
        for ext in image_extensions:
            candidate = os.path.join(system_path, f"{game_name}.{ext}")
            if os.path.exists(candidate):
                game_image = candidate
                break

        if game_image:
            try:
                marquee.display_image(game_image, rescale=True)
                logger.info("Displayed game image: %s", game_image)
                return True
            except Exception as e:
                logger.error("Failed to display game image %s: %s", game_image, e)
                return False

        # Create a placeholder for the game if enabled and missing
        if create_placeholders:
            placeholder_path = os.path.join(system_path, f"{game_name}.txt")
            if not os.path.exists(placeholder_path):
                try:
                    with open(placeholder_path, "w") as placeholder_file:
                        yaml.dump({"system_name": system_name, "game_name": game_name}, placeholder_file)
                    logger.info("Created placeholder file for game: %s", placeholder_path)
                except Exception as e:
                    logger.error("Failed to create placeholder file for game %s: %s", placeholder_path, e)

    # Look for system-wide image
    system_image = None
    for ext in image_extensions:
        candidate = os.path.join(system_path, f"{system_name}.{ext}")
        if os.path.exists(candidate):
            system_image = candidate
            break

    if system_image:
        # Overlay game_name if enabled and display system image
        if create_placeholders and game_name:
            overlayed_image_path = os.path.join(system_path, f"{system_name}_overlayed.png")
            overlay_text_on_image(system_image, game_name, overlayed_image_path, logger)
            system_image = overlayed_image_path

        try:
            marquee.display_image(system_image, rescale=True)
            logger.info("Displayed system image: %s", system_image)
            return True
        except Exception as e:
            logger.error("Failed to display system image %s: %s", system_image, e)
            return False

    # Create a placeholder for the system if enabled and missing
    if create_placeholders:
        placeholder_path = os.path.join(system_path, f"{system_name}.txt")
        if not os.path.exists(placeholder_path):
            try:
                with open(placeholder_path, "w") as placeholder_file:
                    yaml.dump({"system_name": system_name}, placeholder_file)
                logger.info("Created placeholder file for system: %s", placeholder_path)
            except Exception as e:
                logger.error("Failed to create placeholder file for system %s: %s", placeholder_path, e)

    # Overlay game_name on default image if enabled
    if create_placeholders and game_name:
        overlayed_default_path = os.path.join(system_path, "default_overlayed.png")
        overlay_text_on_image(default_image_path, game_name, overlayed_default_path, logger)
        default_image_path = overlayed_default_path

    # Display the default image as a fallback
    try:
        marquee.display_image(default_image_path, rescale=True)
        logger.info("Displayed default image: %s", default_image_path)
        return True
    except Exception as e:
        logger.error("Failed to display default image %s: %s", default_image_path, e)
        return False


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
    if not marquee_enabled:
        logger.info("game-select' ignored because marquee is disabled.")
        return

    system_name = arguments.get("system_name")
    game_name = arguments.get("game_name")
    if not system_name or not game_name:
        logger.warning("Missing 'system_name' or 'game_name' in arguments for 'screensaver-game-select'.")
        return

    success = search_and_display_image(system_name, game_name, marquee, marquee_config, logger)
    if not success:
        logger.error("Failed to display image for 'screensaver-game-select'.")

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
    if not marquee_enabled:
        logger.info("'screensaver-game-select' ignored because marquee is disabled.")
        return

    system_name = arguments.get("system_name")
    game_name = arguments.get("game_name")
    if not system_name or not game_name:
        logger.warning("Missing 'system_name' or 'game_name' in arguments for 'screensaver-game-select'.")
        return

    success = search_and_display_image(system_name, game_name, marquee, marquee_config, logger)
    if not success:
        logger.error("Failed to display image for 'screensaver-game-select'.")


def handle_system_select(arguments):
    if not marquee_enabled:
        logger.info("'system-select' ignored because marquee is disabled.")
        return

    system_name = arguments.get("system_name")
    if not system_name:
        logger.warning("Missing 'system_name' in arguments for 'system-select'.")
        return

    success = search_and_display_image(system_name, None, marquee, marquee_config, logger)
    if not success:
        logger.error("Failed to display image for 'system-select'.")


def handle_game_select(arguments):
    if not marquee_enabled:
        logger.info("game-select' ignored because marquee is disabled.")
        return

    system_name = arguments.get("system_name")
    game_name = arguments.get("game_name")
    if not system_name or not game_name:
        logger.warning("Missing 'system_name' or 'game_name' in arguments for 'screensaver-game-select'.")
        return

    success = search_and_display_image(system_name, game_name, marquee, marquee_config, logger)
    if not success:
        logger.error("Failed to display image for 'screensaver-game-select'.")

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
            logger.info("Handling event '%s' with arguments: %s", event_name, arguments)
            handler(arguments)
        except Exception as e:
            logger.error("Error while handling event '%s': %s", event_name, e)
    else:
        logger.warning("Unhandled event '%s' with arguments: %s", event_name, arguments)

# Event loop for processing incoming messages
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
