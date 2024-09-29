from PIL import Image, ImageSequence, ImageDraw, ImageFont
from .colors import RGBl
import threading
import time
import serial
import os
import zlib
import struct

# Display types and sizes
DISPLAY_GALACTIC_UNICORN = 0
DISPLAY_INTERSTATE75_128x32 = 1

DISPLAY_SIZES = {
    DISPLAY_GALACTIC_UNICORN: (53, 11),
    DISPLAY_INTERSTATE75_128x32: (128, 32)
}

# Color order permutations
COLOR_ORDER_RGB = (0, 1, 2)  # RGB
COLOR_ORDER_RBG = (0, 2, 1)  # RBG
COLOR_ORDER_GBR = (1, 2, 0)  # GBR
COLOR_ORDER_GRB = (1, 0, 2)  # GRB
COLOR_ORDER_BGR = (2, 1, 0)  # BGR
COLOR_ORDER_BRG = (2, 0, 1)  # BRG


class LedMatrix:
    """
    Class for controlling an LED matrix display.

    This class allows displaying static images (PNGs) or animated GIFs
    on an LED matrix. It supports different display sizes and color
    orders and handles both cropping and rescaling of images.

    Attributes:
        width (int): Width of the LED matrix.
        height (int): Height of the LED matrix.
        display_buffer (bytearray): Internal buffer to store pixel data.
        serial_port_path (str): Path to the serial port for sending data.
        color_order (tuple): Order of the color channels (RGB, BGR, etc.).
        _stop_event (threading.Event): Event to control stopping GIF playback.
        _thread (threading.Thread): Thread for asynchronous GIF playback.
    """

    PREFIX = b"multiverse:data"  # Prefix for data sent to the serial port
    COMPRESSED_PREFIX = b"multiverse:zdat"  # Prefix for compressed data

    def __init__(self, display=DISPLAY_GALACTIC_UNICORN,
                 serial_port_path="/dev/unicorn",
                 color_order=COLOR_ORDER_RGB, compress=False):
        """
        Initializes the LedMatrix object.

        :param display: Type of display (e.g., DISPLAY_GALACTIC_UNICORN, DISPLAY_HUB75_128x32).
        :param serial_port_path: Path to the serial port used for communication.
        :param color_order: A tuple defining the color order (e.g., COLOR_ORDER_RGB).
        :param compress: Boolean indicating whether to compress the data stream.
        """
        (self.width, self.height) = DISPLAY_SIZES[display]
        self.display_buffer = bytearray([0] * (self.width * self.height * 4))  # 4 bytes per pixel (RGBA)
        self.background_buffer = bytearray([20] * (self.width * self.height * 4))  # 4 bytes per pixel (RGBA)
        self.serial_port_path = serial_port_path
        self.color_order = color_order  # Set the desired color order
        self.compress = compress  # Enable or disable compression
        self._stop_event = threading.Event()
        self._thread = None

    def stop(self):
        """
        Stops any ongoing display, such as an animated GIF.
        """
        if self._thread is not None:
            self._stop_event.set()
            # Only join if it's a different thread from the current one
            if self._thread != threading.current_thread():
                self._thread.join()
            self._thread = None  # Reset the thread variable

    def write_to_display(self):
        """
        Sends the display buffer to the LED matrix by writing to the serial port.

        Translates the display buffer based on the configured color order
        before sending it to the hardware.
        """
        translated_buffer = self.translate_buffer()
        try:
            with serial.Serial(self.serial_port_path, baudrate=115200, timeout=1) as ser:
                if self.compress:
                    # Compress the data using zlib
                    compressed_data = zlib.compress(translated_buffer)
                    compressed_size = len(compressed_data)
                    # Send the compressed data with the compressed prefix and size
                    ser.write(self.COMPRESSED_PREFIX)
                    ser.write(struct.pack('<I', compressed_size))  # Send size as 4 bytes (little-endian)
                    ser.write(compressed_data)
                else:
                    # Send the uncompressed data with the standard prefix
                    ser.write(self.PREFIX + translated_buffer)
        except serial.SerialException as e:
            print(f"Error opening serial port {self.serial_port_path}: {e}")

    def translate_buffer(self):
        """
        Translates the display buffer based on the selected color order.

        This method adjusts the RGB channels of each pixel in the buffer to match
        the hardware's color order.

        :return: Translated display buffer.
        :rtype: bytearray
        """
        translated_buffer = bytearray(len(self.display_buffer))
        for i in range(0, len(self.display_buffer), 4):
            r, g, b, a = self.display_buffer[i:i + 4]  # RGBA values
            translated_buffer[i:i + 4] = [
                self.display_buffer[i + self.color_order[0]],  # Red or equivalent channel
                self.display_buffer[i + self.color_order[1]],  # Green or equivalent channel
                self.display_buffer[i + self.color_order[2]],  # Blue or equivalent channel
                a  # Alpha remains unchanged
            ]
        return translated_buffer

    def _set_pixel(self, x, y, color: RGBl):
        """
        Internal method to set a pixel at (x, y) to the specified RGBl color.

        :param x: X coordinate of the pixel.
        :param y: Y coordinate of the pixel.
        :param color: A named tuple defining the Red, Green, Blue, and Brightness values.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            index = (x + y * self.width) * 4
            self.display_buffer[index:index + 4] = [
                color.red,
                color.green,
                color.blue,
                color.brightness  # Using brightness as the alpha channel
            ]

    def _get_pixel(self, x, y):
        """
        Internal method to retrieve the current pixel at (x, y).

        :param x: X coordinate of the pixel.
        :param y: Y coordinate of the pixel.
        :return: RGBl named tuple representing the current pixel color and brightness.
        :rtype: RGBl
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            index = (x + y * self.width) * 4
            r, g, b, a = self.display_buffer[index:index + 4]
            return RGBl(r, g, b, a)
        return RGBl(0, 0, 0, 0)

    def clear_with_background(self, background_color: RGBl):
        """
        Clears the display buffer by filling it with the specified background color.

        :param background_color: The RGBl color to fill the background with.
        """

        for x in range(self.width):
            for y in range(self.height):
                self._set_pixel(x, y, background_color)

    def display_image(self, image_path, rescale=False, background_color=None, brightness=127):
        """
        Displays a static image (PNG or single-frame GIF) or an animated GIF on the matrix.

        For animated GIFs, this method will run the animation asynchronously. If the
        image is static, it will be displayed immediately.

        :param image_path: Path to the PNG or GIF file.
        :param rescale: If True, the image will be rescaled to fit the display. Defaults to False (cropped).
        :param background_color: The color used for filling transparent areas, if provided.
        :param brightness: Brightness of the image (applies to the image as a whole). Defaults to 127.
        """
        self.stop()  # Stop any ongoing GIF animation
        self._stop_event.clear()  # Ensure the stop flag is cleared

        # Check if the image file exists
        if not image_path or not os.path.exists(image_path):
            # Display an error message if no file or file doesn't exist
            error_message = "Not found"
            self.display_text(error_message, brightness)
            return

        img = Image.open(image_path)

        # Clear with the background and save the buffer before starting the animation or static image
        if background_color:
            self.clear_with_background(background_color)

        # Always copy the current display buffer to the background buffer
        self.background_buffer = self.display_buffer[:]

        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
        if len(frames) == 1:
            self._display_frame(frames[0], rescale, brightness)
        else:
            def animate_gif():
                while not self._stop_event.is_set():
                    for frame in frames:
                        start_time = time.time()  # Record the start time
                        self._display_frame(frame.convert("RGBA"), rescale, brightness)
                        elapsed_time = time.time() - start_time  # Calculate the time taken to display the frame

                        frame_duration = frame.info.get('duration', 100) / 1000.0  # Frame duration in seconds
                        sleep_time = frame_duration - elapsed_time  # Adjust sleep time

                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        else:
                            # If the data transfer takes longer than the frame duration, skip sleeping
                            pass

            self._thread = threading.Thread(target=animate_gif)
            self._thread.start()

    def _display_frame(self, img, rescale, brightness):
        """
        Displays a single frame of a GIF or a PNG image.

        This method resizes or crops the image to fit the display, and updates the
        display buffer with the image's pixel data. Blends the incoming pixel with
        the current background based on opacity.

        :param img: The image frame to display.
        :param rescale: If True, the image will be rescaled to fit the display.
        :param brightness: Brightness of the image being displayed.
        """
        if rescale:
            img = img.resize((self.width, self.height))
        else:
            img_width, img_height = img.size
            left = (img_width - self.width) // 2
            upper = (img_height - self.height) // 2
            right = left + self.width
            lower = upper + self.height
            img = img.crop((left, upper, right, lower))

        for x in range(img.width):
            for y in range(img.height):
                pixel = img.getpixel((x, y))
                if len(pixel) == 4:
                    r, g, b, a = pixel  # RGBA
                else:
                    r, g, b = pixel  # RGB
                    a = 255  # Assume fully opaque if no alpha channel

                # Get the current pixel from the background buffer
                index = (x + y * self.width) * 4
                current_r, current_g, current_b, _ = self.background_buffer[index:index + 4]

                # Calculate blend factor based on opacity (alpha channel)
                blend_factor = a / 255

                # Perform blending calculation
                blended_r = (r * blend_factor) + (current_r * (1 - blend_factor))
                blended_g = (g * blend_factor) + (current_g * (1 - blend_factor))
                blended_b = (b * blend_factor) + (current_b * (1 - blend_factor))

                # Set the pixel on the display, passing the brightness separately
                self._set_pixel(x, y, RGBl(int(blended_r), int(blended_g), int(blended_b), brightness))

        self.write_to_display()

    def display_text(self, message, brightness):
        """
        Displays the given text message on the LED matrix.

        :param message: The text message to display.
        :param brightness: Brightness of the displayed text.
        """
        # Create an image for the text
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Use a simple font
        font = ImageFont.load_default()  # You can use ImageFont.truetype() for custom fonts

        # Get the bounding box of the text
        text_bbox = draw.textbbox((0, 0), message, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Calculate the position to center the text
        x_pos = (self.width - text_width) // 2
        y_pos = (self.height - text_height) // 2

        # Draw the text onto the image
        draw.text((x_pos, y_pos), message, font=font, fill=(255, 255, 255, 255))  # White text

        # Display the text as an image
        self._display_frame(img, rescale=True, brightness=brightness)
