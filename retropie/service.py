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


def overlay_text_on_image_in_memory(base_image, text, temp_file_base, font_size=20, stroke_width=2):
    """
    Overlays text with a black outline on a base image, writes it to a temporary file, and returns the path.

    Args:
        base_image (Image.Image): The base image to overlay text on.
        text (str): The text to overlay.
        temp_file_base (str): Base path for the temporary file (e.g., '/dev/shm/temp_image').
        font_size (int): Font size for the text.
        stroke_width (int): Width of the black outline around the text.

    Returns:
        str: The path to the temporary file containing the modified image.
    """
    try:
        # Create a drawing context
        draw = ImageDraw.Draw(base_image)
        w, h = base_image.width, base_image.height

        # Use a simple font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Get the size of the text with the stroke
        text_bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Center the text on the image
        x_pos = (w - text_width) // 2
        y_pos = (h - text_height) // 2

        # Draw shadow (optional for enhanced appearance)
        shadow_offset = (2, 2)
        shadow_color = (0, 0, 0)
        draw.text(
            (x_pos + shadow_offset[0], y_pos + shadow_offset[1]),
            text,
            font=font,
            fill=shadow_color,
        )

        # Draw the main text with a stroke (black outline)
        text_color = (255, 255, 255)  # White text
        stroke_color = (0, 0, 0)  # Black outline
        draw.text(
            (x_pos, y_pos),
            text,
            font=font,
            fill=text_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color,
        )

        # Determine the file extension based on the image format
        image_format = base_image.format or "PNG"  # Default to PNG if format is None
        temp_file_path = f"{temp_file_base}.{image_format.lower()}"

        # Save the modified image to the temporary file
        base_image.save(temp_file_path, format=image_format)
        return temp_file_path

    except Exception as e:
        logger.error("Failed to overlay text on image: %s", e)
        raise


def search_and_display_image(system_name, game_name, marquee, marquee_config, logger, rom_path=None):
    """
    Search and display an image based on system_name and game_name, with placeholder creation.

    Args:
        system_name (str): Name of the system.
        game_name (str): Name of the game (can be None).
        marquee (LedMatrix): Marquee object to display the image.
        marquee_config (dict): Configuration for the marquee.
        logger (Logger): Logger object for logging messages.
        rom_path (str): Path to the ROM file. If provided, ensures it is a file before creating a placeholder.

    Returns:
        bool: True if an image was successfully displayed, False otherwise.
    """
    image_path = marquee_config.get("image_dir", "/opt/pixel-multiverse/marquee")
    image_extensions = marquee_config.get("image_extensions", ["gif", "png", "jpg"])
    create_placeholders = str(marquee_config.get("create_placeholders", "false")).strip().lower() == "true"
    default_image_path = marquee_config.get("default_image", "/opt/pixel-multiverse/default.png")

    # Temporary file base path for modified images
    temp_file_base = "/dev/shm/temp_image"

    # Construct the system path
    system_path = os.path.join(image_path, system_name)

    # Ensure the system directory exists
    if create_placeholders and not os.path.exists(system_path):
        os.makedirs(system_path, exist_ok=True)
        logger.info("Created directory for system: %s", system_path)

    # Search for game-specific image
    if game_name:
        for ext in image_extensions:
            game_image_path = os.path.join(system_path, f"{game_name}.{ext}")
            if os.path.exists(game_image_path):
                try:
                    marquee.display_image(game_image_path, rescale=True)
                    logger.info("Displayed game image: %s", game_image_path)
                    return True
                except Exception as e:
                    logger.error("Failed to display game image: %s", e)
                    return False

        # If no specific game image is found, overlay text on fallback images
        logger.info("No specific image found for game '%s'. Overlaying text on fallback images.", game_name)

        # Only create a placeholder if rom_path is provided and is a valid file
        if rom_path and os.path.isfile(rom_path) and create_placeholders:
            placeholder_path = os.path.join(system_path, f"{game_name}.txt")
            if not os.path.exists(placeholder_path):
                try:
                    with open(placeholder_path, "w") as placeholder_file:
                        yaml.dump({"system_name": system_name, "game_name": game_name,
                                   "rom_path": rom_path}, placeholder_file)
                    logger.info("Created placeholder file for game: %s", placeholder_path)
                except Exception as e:
                    logger.error("Failed to create placeholder file for game %s: %s", game_name, e)

    # Fallback to system-wide image
    for ext in image_extensions:
        system_image_path = os.path.join(system_path, f"{system_name}.{ext}")
        if os.path.exists(system_image_path):
            try:
                with Image.open(system_image_path) as system_image:
                    overlayed_path = overlay_text_on_image_in_memory(system_image, game_name or system_name,
                                                                     temp_file_base)
                    marquee.display_image(overlayed_path, rescale=True)
                    logger.info("Displayed system image with overlay: %s", system_image_path)
                    return True
            except Exception as e:
                logger.error("Failed to display system image: %s", e)
                return False

    # Fallback to default image
    try:
        with Image.open(default_image_path) as default_image:
            overlayed_path = overlay_text_on_image_in_memory(default_image, game_name or system_name, temp_file_base)
            marquee.display_image(overlayed_path, rescale=True)
            logger.info("Displayed default image with overlay: %s", default_image_path)
            return True
    except Exception as e:
        logger.error("Failed to display default image: %s", e)
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
    rom_path = arguments.get("rom_path")
    if not system_name or not game_name:
        logger.warning("Missing 'system_name' or 'game_name' in arguments for 'screensaver-game-select'.")
        return

    success = search_and_display_image(system_name=system_name, game_name="",
                                       marquee=marquee, marquee_config=marquee_config, logger=logger)
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
        except Exception as exc:
            logger.error("Error while handling event '%s': %s", event_name, exc)
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
