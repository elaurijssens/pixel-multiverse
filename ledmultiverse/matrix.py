import time
import serial
from .colors import RGBl
from PIL import Image, ImageSequence
import threading

DISPLAY_GALACTIC_UNICORN = 0
DISPLAY_HUB75_128x32 = 1

DISPLAY_SIZES = {
    DISPLAY_GALACTIC_UNICORN: (53, 11),
    DISPLAY_HUB75_128x32: (128, 32)
}

COLOR_ORDER_RGB = (0, 1, 2)  # RGB
COLOR_ORDER_RBG = (0, 2, 1)  # RBG
COLOR_ORDER_GBR = (1, 2, 0)  # GBR
COLOR_ORDER_GRB = (1, 0, 2)  # GRB
COLOR_ORDER_BGR = (2, 1, 0)  # BGR
COLOR_ORDER_BRG = (2, 0, 1)  # BRG

class LedMatrix:
    PREFIX = b"multiverse:data"  # Prefix for data sent to the serial port

    def __init__(self, display=DISPLAY_GALACTIC_UNICORN, serial_port_path="/dev/unicorn", color_order=COLOR_ORDER_RGB):
        (self.width, self.height) = DISPLAY_SIZES[display]
        self.display_buffer = bytearray([31] * (self.width * self.height * 4))  # 4 bytes per pixel (RGBA)
        self.serial_port_path = serial_port_path
        self.color_order = color_order  # Set the desired color order
        self._stop_event = threading.Event()
        self._thread = None

    def stop_display(self):
        """Stops any ongoing display, such as an animated GIF."""
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join()

    def write_to_display(self):
        """Writes the display buffer to the display after applying color translation."""
        translated_buffer = self.translate_buffer()
        try:
            with serial.Serial(self.serial_port_path, baudrate=115200, timeout=1) as ser:
                ser.write(self.PREFIX + translated_buffer)
        except serial.SerialException as e:
            print(f"Error opening serial port {self.serial_port_path}: {e}")

    def translate_buffer(self):
        """Applies the color order translation to the entire display buffer."""
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

    def set_pixel(self, x, y, color: RGBl):
        """Sets a pixel at (x, y) to the specified RGBl color."""
        self.stop_display()  # Stop any ongoing GIF animation
        if 0 <= x < self.width and 0 <= y < self.height:
            index = (x + y * self.width) * 4
            self.display_buffer[index:index + 4] = [
                color.red,
                color.green,
                color.blue,
                color.brightness  # Using brightness as the alpha channel
            ]
        self.write_to_display()

    def clear_with_background(self, background_color: RGBl):
        """Clears the display buffer with the specified background color."""
        self.stop_display()  # Stop any ongoing GIF animation
        for x in range(self.width):
            for y in range(self.height):
                self.set_pixel(x, y, background_color)

    def display_image(self, image_path, rescale=False, background_color=None):
        """Displays a static image (PNG or single-frame GIF) or animated GIF."""
        self.stop_display()  # Stop any ongoing GIF animation
        self._stop_event.clear()  # Ensure the stop flag is cleared

        img = Image.open(image_path)

        # Check if the image is animated (i.e., has more than 1 frame)
        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
        if len(frames) == 1:
            # If it's a single-frame image, just display it as a static image
            self._display_frame(frames[0], rescale, background_color)
        else:
            # If it's an animated GIF, start a thread to display each frame
            def animate_gif():
                while True:
                    for frame in frames:
                        if self._stop_event.is_set():
                            return  # Stop the thread if requested

                        self._display_frame(frame.convert("RGBA"), rescale, background_color)
                        time.sleep(img.info.get('duration', 100) / 1000.0)  # Default to 100ms if no duration

            self._thread = threading.Thread(target=animate_gif)
            self._thread.start()

    def _display_frame(self, img, rescale, background_color):
        """Displays a single frame of a GIF or a PNG image."""
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

        for x in range(img.width):
            for y in range(img.height):
                r, g, b, a = img.getpixel((x, y))
                if a > 0:  # Only update the pixel if it's not fully transparent
                    brightness = a
                    self.set_pixel(x, y, RGBl(r, g, b, brightness))

        self.write_to_display()
