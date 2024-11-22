import os
import sys
import socket
import yaml
import logging
from pixelpusher import (
    LedMatrix,
    PlasmaButtons,
    DISPLAY_INTERSTATE75_128x32,
    DISPLAY_GALACTIC_UNICORN,
    COLOR_ORDER_RGB,
    COLOR_ORDER_RBG,
    COLOR_ORDER_BGR,
    COLOR_ORDER_BRG,
    COLOR_ORDER_GRB,
    COLOR_ORDER_GBR,
    RGBl
)
from PIL import Image, ImageDraw, ImageFont

# Constants
SOCKET_PATH = "/tmp/pixel_multiverse.sock"
CONFIG_PATH = "/opt/pixel-multiverse/pixel-multiverse.yml"
TEMP_FILE_BASE = "/dev/shm/temp_image"

# Display Mapping
DISPLAY_MAPPING = {
    "I75_128X32": {"type": DISPLAY_INTERSTATE75_128x32, "resolution": "hi-res", "width": 128},
    "GALACTIC_UNICORN": {"type": DISPLAY_GALACTIC_UNICORN, "resolution": "lo-res", "width": 53},
}


# Logging Configuration
def configure_logging(config):
    level = config.get("general", {}).get("logging", {}).get("level", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO),
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        stream=sys.stdout)
    created_logger = logging.getLogger("PixelMultiverseService")
    created_logger.info("Logging level set to %s", level)
    return created_logger


# Load Configuration
def load_configuration():
    local_logger = logging.getLogger("PixelMultiverseService")
    try:
        with open(CONFIG_PATH, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        local_logger.error("Configuration file not found at %s. Ensure it is in the correct location.", CONFIG_PATH)
        sys.exit(1)
    except yaml.YAMLError as e:
        local_logger.error("Error parsing configuration file: %s", e)
        sys.exit(1)


def load_pattern_queue_from_yaml(yaml_config):
    """
    Load the pattern queue configuration from a YAML file.

    :param yaml_config: full yaml configuration
    :return: A list of patterns usable by the PlasmaButtons class.
    """

    local_pattern_queue = []

    for pattern_config in yaml_config.get('buttons', {}).get('attract_program', []):
        pattern_name = pattern_config.get('pattern')
        params = pattern_config.get('params', {})

        # Parse color_on and color_off if they exist
        if 'color_on' in params:
            params['color_on'] = RGBl(*params['color_on'])
        if 'color_off' in params:
            params['color_off'] = RGBl(*params['color_off'])
        else:
            # If color_off is not specified, default to off
            params['color_off'] = RGBl(0, 0, 0, 0)

        # Ensure delay is a float
        if 'delay' in params:
            params['delay'] = float(params['delay'])

        local_pattern_queue.append((pattern_name, params))

    return local_pattern_queue


# Initialize buttons
def initialize_buttons(config):
    button_config = config.get("buttons", {})
    if str(button_config.get("enabled", "false")).strip().lower() != "true":
        logger.info("Button leds are disabled in the configuration.")
        return None

    connection_path = button_config.get("connection")
    if not connection_path or not os.path.exists(connection_path):
        logger.error("Connection path '%s' does not exist. Disabling buttons", connection_path)
        return None

    num_leds = button_config.get("num_leds", 128)
    refresh_rate = button_config.get("refresh_rate", 60)
    button_map = button_config.get("button_map", {})

    try:
        led_map = {tuple(item['coord']): item['value'] for item in button_config.get("led_map", [])}
    except Exception as e:
        logger.error("Failed to create led map. Attract modes will not work", e)
        led_map = None

    try:
        plasma_buttons = PlasmaButtons(
            num_leds=num_leds,
            serial_port_path=connection_path,
            refresh_rate=refresh_rate,
            coord_map=led_map,
            button_map=button_map
        )
        logger.info("Buttons initialized with '%s' leds, connection '%s', refresh rate '%s'.",
                    num_leds, connection_path, refresh_rate)
        return plasma_buttons
    except Exception as e:
        logger.error("Failed to initialize marquee: %s. Disabling marquee", e)
        return None


# Initialize Marquee
def initialize_marquee(config):
    marquee_config = config.get("marquee", {})
    if str(marquee_config.get("enabled", "false")).strip().lower() != "true":
        logger.info("Marquee is disabled in the configuration.")
        return None, None, None

    display_type = marquee_config.get("type", "").upper()
    display_info = DISPLAY_MAPPING.get(display_type)
    if not display_info:
        valid_types = ", ".join(DISPLAY_MAPPING.keys())
        logger.error("Invalid marquee type '%s'. Expected one of: %s. Disabling marquee.", display_type, valid_types)
        return None, None, None

    connection_path = marquee_config.get("connection")
    if not connection_path or not os.path.exists(connection_path):
        logger.error("Connection path '%s' does not exist. Disabling marquee", connection_path)
        return None, None, None

    color_order = marquee_config.get("color_order", "RGB").upper()
    color_order_mapping = {
        "RGB": COLOR_ORDER_RGB,
        "RBG": COLOR_ORDER_RBG,
        "BGR": COLOR_ORDER_BGR,
        "BRG": COLOR_ORDER_BRG,
        "GRB": COLOR_ORDER_GRB,
        "GBR": COLOR_ORDER_GBR,
    }
    color_order_constant = color_order_mapping.get(color_order)
    if not color_order_constant:
        logger.error("Invalid color order '%s'. Expected one of: %s. Disabling marquee",
                     color_order, ", ".join(color_order_mapping.keys()))
        return None, None, None

    try:
        led_marquee = LedMatrix(
            display=display_info["type"],
            serial_port_path=connection_path,
            color_order=color_order_constant,
            compress=True,
        )
        logger.info("Marquee initialized with type '%s', connection '%s', color order '%s'.",
                    display_type, connection_path, color_order)
        return led_marquee, display_info["resolution"], display_info["width"]
    except Exception as e:
        logger.error("Failed to initialize marquee: %s. Disabling marquee", e)
        return None, None, None


# Overlay Text on Image
def overlay_text_on_image_in_memory(
    base_image, text, temp_file_base, max_width=None, font_size=20, stroke_width=2,
    line_spacing_factor=-0.4, vertical_offset=4
):
    """
    Overlays text with a black outline on a base image, writes it to a temporary file, and returns the path.

    Args:
        base_image (Image.Image): The base image to overlay text on.
        text (str): The text to overlay.
        temp_file_base (str): Base path for the temporary file (e.g., '/dev/shm/temp_image').
        max_width (int): Maximum width for text wrapping, or None for no wrapping.
        font_size (int): Font size for the text.
        stroke_width (int): Width of the black outline around the text.
        line_spacing_factor (float): Line spacing as a fraction of font size.
        vertical_offset (int): Additional vertical offset to adjust the text's vertical position.

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

        # Wrap text if max_width is provided
        if max_width:
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if draw.textlength(test_line, font=font) > max_width:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                lines.append(current_line)
        else:
            lines = [text]

        # Calculate text positioning
        line_spacing = int(font_size * line_spacing_factor)
        total_text_height = len(lines) * font_size + (len(lines) - 1) * line_spacing
        y_pos = (h - total_text_height) // 2 + vertical_offset

        for line in lines:
            text_width = draw.textlength(line, font=font)
            x_pos = (w - text_width) // 2

            # Draw the main text with a stroke (black outline)
            text_color = (255, 255, 255)  # White text
            stroke_color = (0, 0, 0)  # Black outline
            draw.text(
                (x_pos, y_pos),
                line,
                font=font,
                fill=text_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color,
            )
            y_pos += font_size + line_spacing

        # Determine the file extension based on the image format
        image_format = base_image.format or "PNG"  # Default to PNG if format is None
        temp_file_path = f"{temp_file_base}.{image_format.lower()}"

        # Save the modified image to the temporary file
        base_image.save(temp_file_path, format=image_format)
        return temp_file_path

    except Exception as e:
        logger.error("Failed to overlay text on image: %s", e)
        raise


def search_and_display_image(marquee, system_name="", game_name=None, rom_path=None, ui_image="default.png"):
    """
    Search and display an image based on system_name and game_name, with placeholder creation.

    Args:
        system_name (str): Name of the system.
        game_name (str): Name of the game (can be None).
        marquee (LedMatrix): Marquee object to display the image.
        rom_path (str): Path to the ROM file. If provided, ensures it is a file before creating a placeholder.
        ui_image (str): Name of de default image that should be used. Useful for

    Returns:
        bool: True if an image was successfully displayed, False otherwise.
    """
    image_path = configuration.get("marquee", {}).get("image_path", "/opt/pixel-multiverse/marquee")
    image_extensions = configuration.get("marquee", {}).get("image_extensions", ["gif", "png", "jpg"])
    create_placeholders = str(configuration.get("marquee", {}).
                              get("create_placeholders", "false")).strip().lower() == "true"
    default_image_path = configuration.get("marquee", {}).get("default_image", "/opt/pixel-multiverse/images")

    # Get display info from the mapping
    display_type = configuration.get("marquee", {}).get("type", "").upper()
    display_info = DISPLAY_MAPPING.get(display_type)
    if not display_info:
        logger.error("Unknown display type '%s' in configuration.", display_type)
        return False

    resolution = display_info["resolution"]
    max_width = display_info["width"] if resolution == "hi-res" else None

    # Temporary file base path for modified images
    temp_file_base = "/dev/shm/temp_image"

    # Construct the system path for game-specific images
    system_path = os.path.join(image_path, system_name)

    # Search for game-specific image
    if rom_path:
        for ext in image_extensions:
            game_image_path = os.path.join(system_path, f"{rom_path}.{ext}")
            if os.path.exists(game_image_path):
                try:
                    marquee.display_image(game_image_path, rescale=True)
                    logger.info("Displayed game image: %s", game_image_path)
                    return True
                except Exception as e:
                    logger.error("Failed to display game image: %s", e)
                    return False

        # No specific game image found; create placeholder if enabled
        if create_placeholders:
            placeholder_path = os.path.join(system_path, f"{rom_path}.txt")
            if not os.path.exists(placeholder_path):
                try:
                    if not os.path.exists(system_path):
                        os.makedirs(system_path, exist_ok=True)

                    placeholder_data = {"system_name": system_name, "game_name": game_name}
                    if rom_path and os.path.isfile(rom_path):
                        placeholder_data["rom_path"] = rom_path

                    with open(placeholder_path, "w") as placeholder_file:
                        yaml.dump(placeholder_data, placeholder_file)
                    os.chmod(placeholder_path, 0o666)
                    logger.info("Created placeholder file for game: %s", placeholder_path)
                except Exception as e:
                    logger.error("Failed to create placeholder file for game %s: %s", game_name, e)

    # Search for system-wide image in image_path
    for ext in image_extensions:
        system_image_path = os.path.join(image_path, f"{system_name}.{ext}")
        if os.path.exists(system_image_path):
            try:
                with Image.open(system_image_path) as system_image:
                    if resolution == "hi-res" and max_width:
                        overlayed_path = overlay_text_on_image_in_memory(
                            system_image, game_name or "", temp_file_base, max_width=max_width
                        )
                        marquee.display_image(overlayed_path, rescale=True)
                    else:
                        marquee.display_image(system_image_path, rescale=True)
                    logger.info("Displayed system image: %s", system_image_path)
                    return True
            except Exception as e:
                logger.error("Failed to display system image: %s", e)
                return False

    # Fallback to default image
    try:
        ui_image_path = os.path.join(default_image_path, ui_image)
        with Image.open(ui_image_path) as default_image:
            if resolution == "hi-res" and max_width:
                overlayed_path = overlay_text_on_image_in_memory(
                    default_image, game_name or system_name, temp_file_base, max_width=max_width
                )
                marquee.display_image(overlayed_path, rescale=True)
            else:
                marquee.display_image(default_image_path, rescale=True)
            logger.info("Displayed default image: %s", default_image_path)
            return True
    except Exception as e:
        logger.error("Failed to display default image: %s", e)
        return False


def handle_quit_event(arguments):
    logger.info("Handling 'quit' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee, ui_image="default.png")
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()


def handle_reboot_event(arguments):
    logger.info("Handling 'reboot' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee,ui_image="reboot.png")
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()


def handle_shutdown_event(arguments):
    logger.info("Handling 'shutdown' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee, ui_image="shutdown.png")
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()


def handle_config_changed_event(arguments):
    logger.info("Handling 'config-changed' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee)
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()

def handle_controls_changed_event(arguments):
    logger.info("Handling 'controls-changed' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee, ui_image="controlschanged.png")
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()


def handle_settings_changed_event(arguments):
    logger.info("Handling 'settings-changed' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee, ui_image="settingschanged.png")
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()


def handle_theme_changed_event(arguments):
    logger.info("Handling 'theme-changed' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee)
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()


def handle_game_start_event(arguments):
    if marquee:
        system_name = arguments.get("system_name")
        game_name = arguments.get("game_name")
        if not system_name or not game_name:
            logger.warning("Missing 'system_name' or 'game_name' in arguments for 'screensaver-game-start'.")
            return

        success = search_and_display_image(system_name=system_name, game_name=game_name, marquee=marquee)
        if not success:
            logger.error("Failed to display image for 'screensaver-game-select'.")
    if buttons and buttons.attract_mode_active():
        buttons.stop_attract_mode()

def handle_game_end_event(arguments):
    logger.info("Handling 'game-end' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee)
    if buttons:
        buttons.stop_attract_mode()
        buttons.set_all_leds(mode="normal", color_to=RGBl(0, 0, 0, 0), )


def handle_sleep_event(arguments):
    logger.info("Handling 'sleep' event with arguments: %s", arguments)
    if marquee:
        search_and_display_image(marquee, ui_image="sleep.png")
    if buttons:
        buttons.stop_attract_mode()
        buttons.set_all_leds(mode="normal", color_to=RGBl(0, 0, 0, 0), )

def handle_wake_event(arguments):
    logger.info("Handling 'wake' event with arguments: %s", arguments)
    search_and_display_image(marquee)
    if marquee:
        search_and_display_image(marquee, ui_image="sleep.png")
    if buttons:
        buttons.stop_attract_mode()


def handle_screensaver_start_event(arguments):
    logger.info("Handling 'screensaver-start' event with arguments: %s", arguments)
    if buttons:
        buttons.start_attract_mode(pattern_queue=load_pattern_queue_from_yaml(configuration))


def handle_screensaver_stop_event(arguments):
    logger.info("Handling 'screensaver-stop' event with arguments: %s", arguments)
    search_and_display_image(marquee)


def handle_screensaver_game_select_event(arguments):
    if marquee:
        system_name = arguments.get("system_name")
        game_name = arguments.get("game_name")
        rom_path = arguments.get("rom_path")
        if not system_name or not game_name:
            logger.warning("Missing 'system_name' or 'game_name' in arguments for 'screensaver-game-select'.")
            return

        success = search_and_display_image(system_name=system_name, game_name=game_name, marquee=marquee, rom_path=rom_path)
        if not success:
            logger.error("Failed to display image for 'screensaver-game-select'.")


def handle_system_select_event(arguments):
    if marquee:
        system_name = arguments.get("system_name")
        if not system_name:
            logger.warning("Missing 'system_name' in arguments for 'system-select'.")
            return

        success = search_and_display_image(system_name=system_name, marquee=marquee)
        if not success:
            logger.error("Failed to display image for 'system-select'.")


def handle_game_select_event(arguments):
    if marquee:
        system_name = arguments.get("system_name")
        game_name = arguments.get("game_name")
        rom_path = arguments.get("rom_path")
        if not system_name or not game_name:
            logger.warning("Missing 'system_name' or 'game_name' in arguments for 'screensaver-game-select'.")
            return

        success = search_and_display_image(system_name=system_name, game_name=game_name, marquee=marquee, rom_path=rom_path)
        if not success:
            logger.error("Failed to display image for 'screensaver-game-select'.")


def create_event_handlers():
    return {
        "quit": lambda args: handle_quit_event(args),
        "reboot": lambda args: handle_reboot_event(args),
        "shutdown": lambda args: handle_shutdown_event(args),
        "config-changed": lambda args: handle_config_changed_event(args),
        "controls-changed": lambda args: handle_controls_changed_event(args),
        "settings-changed": lambda args: handle_settings_changed_event(args),
        "theme-changed": lambda args: handle_theme_changed_event(args),
        "game_start": lambda args: handle_game_start_event(args),
        "game-end": lambda args: handle_game_end_event(args),
        "sleep": lambda args: handle_sleep_event(args),
        "wake": lambda args: handle_wake_event(args),
        "screensaver-start": lambda args: handle_screensaver_start_event(args),
        "screensaver-stop": lambda args: handle_screensaver_stop_event(args),
        "screensaver-game-select": lambda args: handle_screensaver_game_select_event(args),
        "system-select": lambda args: handle_system_select_event(args),
        "game-select": lambda args: handle_game_select_event(args),
        # Add other events and their handlers here...
    }


# Process Event
def process_event(event_name, arguments, event_handlers):
    handler = event_handlers.get(event_name)
    if handler:
        try:
            logger.info("Handling event '%s' with arguments: %s", event_name, arguments)
            handler(arguments)
        except Exception as e:
            logger.error("Error while handling event '%s': %s", event_name, e)
    else:
        logger.warning("Unhandled event '%s' with arguments: %s", event_name, arguments)


# Main Event Loop
def start_event_loop():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server_socket.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, 0o666)
        server_socket.listen(1)
        logger.info("Listening on %s...", SOCKET_PATH)

        while True:
            client_socket, _ = server_socket.accept()
            with client_socket:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    message = yaml.safe_load(data.decode().strip())
                    event_name = message.get("event")
                    arguments = message.get("arguments", {})
                    process_event(event_name, arguments, create_event_handlers())
    except Exception as e:
        logger.error("Error: %s", e)
    finally:
        server_socket.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        logger.info("Server shut down.")


# Main Service Execution
if __name__ == "__main__":
    configuration = load_configuration()
    logger = configure_logging(configuration)
    marquee, matrix_resolution, matrix_max_width = initialize_marquee(configuration)
    buttons = initialize_buttons(configuration)

    pattern_queue = [
        ('linear', {'direction': 'left_to_right', 'color_on': RGBl(31, 0, 0, 5), 'color_off': RGBl(0, 31, 0, 5), 'delay': 0.01}),
        ('linear', {'direction': 'top_to_bottom', 'color_on': RGBl(0, 0, 31, 5), 'color_off': RGBl(31, 31, 0, 5), 'delay': 0.01}),
        ('linear', {'direction': 'right_to_left', 'color_on': RGBl(31, 31, 31, 5), 'color_off': RGBl(15, 15, 15, 5), 'delay': 0.01}),
        ('linear', {'direction': 'bottom_to_top', 'color_on': RGBl(0, 31, 31, 5), 'color_off': RGBl(31, 0, 31, 5), 'delay': 0.01}),
        ('circular', {'direction': 'inward', 'color_on': RGBl(0, 31, 31, 5), 'color_off': RGBl(31, 31, 0, 5), 'delay': 0.01}),
        ('radial', {'direction': 'clockwise', 'color_on': RGBl(0, 0, 31, 5), 'color_off': RGBl(31, 31, 31, 5), 'delay': 0.01}),
        ('circular', {'direction': 'outward', 'color_on': RGBl(0, 31, 31, 5), 'color_off': RGBl(31, 31, 0, 5), 'delay': 0.01}),
        ('radial', {'direction': 'anticlockwise','color_on': RGBl(0, 0, 31, 5), 'color_off': RGBl(31, 31, 31, 5), 'delay': 0.01})
        # Add other patterns as needed
    ]

    # Start the attract mode with the pattern queue
    buttons.start_attract_mode(pattern_queue)

    start_event_loop()