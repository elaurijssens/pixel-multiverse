from PIL import Image, ImageSequence
from .colors import RGBl
import threading
import time
import serial

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

    def __init__(self, display=DISPLAY_GALACTIC_UNICORN, serial_port_path="/dev/unicorn", color_order=COLOR_ORDER_RGB):
        """
        Initializes the LedMatrix object.

        :param display: Type of display (e.g., DISPLAY_GALACTIC_UNICORN, DISPLAY_HUB75_128x32).
        :param serial_port_path: Path to the serial port used for communication.
        :param color_order: A tuple defining the color order (e.g., COLOR_ORDER_RGB).
        """
        (self.width, self.height) = DISPLAY_SIZES[display]
        self.display_buffer = bytearray([0] * (self.width * self.height * 4))  # 4 bytes per pixel (RGBA)
        self.serial_port_path = serial_port_path
        self.color_order = color_order  # Set the desired color order
        self._stop_event = threading.Event()
        self._thread = None

    def stop_display(self):
        """
        Stops any ongoing display, such as an animated GIF.
        """
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join()

    def write_to_display(self):
        """
        Sends the display buffer to the LED matrix by writing to the serial port.

        Translates the display buffer based on the configured color order
        before sending it to the hardware.
        """
        translated_buffer = self.translate_buffer()
        try:
            with serial.Serial(self.serial_port_path, baudrate=115200, timeout=1) as ser:
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
        self.stop_display()  # Stop any ongoing GIF animation
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
        self.stop_display()  # Stop any ongoing GIF animation
        self._stop_event.clear()  # Ensure the stop flag is cleared

        img = Image.open(image_path)

        # Check if the image is animated (i.e., has more than 1 frame)
        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
        if len(frames) == 1:
            # If it's a single-frame image, just display it as a static image
            self._display_frame(frames[0], rescale, background_color, brightness)
        else:
            # If it's an animated GIF, start a thread to display each frame
            def animate_gif():
                while True:
                    for frame in frames:
                        if self._stop_event.is_set():
                            return  # Stop the thread if requested

                        self._display_frame(frame.convert("RGBA"), rescale, background_color, brightness)
                        time.sleep(img.info.get('duration', 100) / 1000.0)  # Default to 100ms if no duration

            self._thread = threading.Thread(target=animate_gif)
            self._thread.start()

    def _display_frame(self, img, rescale, background_color, brightness):
        """
        Displays a single frame of a GIF or a PNG image.

        This method resizes or crops the image to fit the display, and updates the
        display buffer with the image's pixel data. Blends the incoming pixel with
        the current pixel based on opacity.

        :param img: The image frame to display.
        :param rescale: If True, the image will be rescaled to fit the display.
        :param background_color: The background color to fill in transparent areas.
        :param brightness: Brightness of the image being displayed.
        """
        if background_color:
            self.clear_with_background(background_color)

        if rescale:
            img = img.resize((self.width, self.height))
        else:
            img_width, img_height = img.size
            left = (img_width - self.width) // 2
            upper = (img_height - self.height) // 2
            right = left + self.width
            lower = upper + self.height
            img = img.crop((left, upper, right, lower))

        # Iterate through image pixels and update the buffer
        for x in range(img.width):
            for y in range(img.height):
                pixel = img.getpixel((x, y))
                if len(pixel) == 4:
                    r, g, b, a = pixel  # RGBA
                else:
                    r, g, b = pixel  # RGB
                    a = 255  # Assume fully opaque if no alpha channel

                # Get the current pixel for blending
                current_pixel = self._get_pixel(x, y)

                # Blend the new pixel with the current pixel based on opacity
                blended_r = (r * (a / 255)) + (current_pixel.red * (1 - a / 255))
                blended_g = (g * (a / 255)) + (current_pixel.green * (1 - a / 255))
                blended_b = (b * (a / 255)) + (current_pixel.blue * (1 - a / 255))

                # Apply brightness scaling
                blended_r = min(int(blended_r * (brightness / 255)), 255)
                blended_g = min(int(blended_g * (brightness / 255)), 255)
                blended_b = min(int(blended_b * (brightness / 255)), 255)

                self._set_pixel(x, y, RGBl(blended_r, blended_g, blended_b, 255))

        self.write_to_display()
