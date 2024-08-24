import time
import serial
import threading
from collections import namedtuple

# Define a NamedTuple for RGBl
RGBl = namedtuple('RGBl', ['red', 'green', 'blue', 'brightness'])

class PlasmaButtons:
    PREFIX = b"multiverse:data"

    def __init__(self, num_leds, serial_port_path, refresh_rate=60):
        """
        Initialize the PlasmaButtons class.

        :param num_leds: The number of LEDs to control.
        :param serial_port_path: The path to the serial port.
        :param refresh_rate: The refresh rate (times per second) for writing to the display.
        """
        self.num_leds = num_leds
        # Initialize the button_leds byte array with 0's, ensuring all values are zeroed
        self.button_leds = bytearray([0] * (num_leds * 4))
        # Store the serial port path
        self.serial_port_path = serial_port_path
        # Set the refresh rate
        self.refresh_rate = refresh_rate
        # Create a threading event to control the refresh loop
        self._stop_event = threading.Event()
        # Create a lock for thread safety
        self._lock = threading.Lock()
        # Start the refresh thread
        self._start_refresh_thread()

    def set_all_leds_data(self, rgbl_values):
        """
        Set the data for all LEDs in one go.

        :param rgbl_values: A list of RGBl NamedTuple with red, green, blue, and brightness values.
        """
        with self._lock:
            for i in range(self.num_leds):
                start_index = i * 4
                rgbl = rgbl_values[i]
                self.button_leds[start_index] = rgbl.blue  # Corrected to set blue first
                self.button_leds[start_index + 1] = rgbl.green
                self.button_leds[start_index + 2] = rgbl.red  # Corrected to set red last
                self.button_leds[start_index + 3] = rgbl.brightness

    def write_to_display(self):
        """
        Write the button_leds byte array to the display via the serial port.
        """
        with self._lock:  # Ensure thread safety when reading the button_leds array
            # Combine the prefix and button_leds data
            data_to_send = self.PREFIX + self.button_leds

        # Open the serial port and send the data
        try:
            with serial.Serial(self.serial_port_path, baudrate=9600, timeout=1) as ser:
                ser.write(data_to_send)
        except serial.SerialException as e:
            print(f"Error opening serial port {self.serial_port_path}: {e}")

    def _refresh_loop(self):
        """
        Continuously refresh the display at the specified refresh rate.
        """
        while not self._stop_event.is_set():
            self.write_to_display()
            time.sleep(1 / self.refresh_rate)

    def _start_refresh_thread(self):
        """
        Start the thread for continuously refreshing the display.
        """
        self._refresh_thread = threading.Thread(target=self._refresh_loop)
        self._refresh_thread.daemon = True
        self._refresh_thread.start()

    def stop(self):
        """
        Stop the refresh loop.
        """
        self._stop_event.set()
        self._refresh_thread.join()

    def __str__(self):
        with self._lock:  # Ensure thread safety when accessing the button_leds array
            return str(list(self.button_leds))

    def fade_effect(self, start_rgbl, end_rgbl, duration):
        """
        Create a fade effect from one color to another across all LEDs.

        :param start_rgbl: The RGBl value to start the fade from.
        :param end_rgbl: The RGBl value to end the fade at.
        :param duration: The duration of the fade in seconds.
        """
        steps = int(self.refresh_rate * duration)
        rgbl_values = []
        for i in range(steps):
            ratio = i / steps
            current_rgbl = RGBl(
                red=int(start_rgbl.red + (end_rgbl.red - start_rgbl.red) * ratio),
                green=int(start_rgbl.green + (end_rgbl.green - start_rgbl.green) * ratio),
                blue=int(start_rgbl.blue + (end_rgbl.blue - start_rgbl.blue) * ratio),
                brightness=int(start_rgbl.brightness + (end_rgbl.brightness - start_rgbl.brightness) * ratio)
            )
            rgbl_values = [current_rgbl] * self.num_leds
            self.set_all_leds_data(rgbl_values)
            time.sleep(1 / self.refresh_rate)

    def blink_effect(self, color1, color2, blink_rate, duration):
        """
        Create a blink effect between two colors.

        :param color1: The first RGBl color.
        :param color2: The second RGBl color.
        :param blink_rate: The rate at which the LEDs should blink (times per second).
        :param duration: The duration of the blinking effect in seconds.
        """
        total_blinks = int(duration * blink_rate)
        for _ in range(total_blinks):
            self.set_all_leds_data([color1] * self.num_leds)
            time.sleep(1 / (2 * blink_rate))
            self.set_all_leds_data([color2] * self.num_leds)
            time.sleep(1 / (2 * blink_rate))


# Example usage:
num_leds = 128
serial_port_path = "/dev/ttyACM0"
refresh_rate = 60

# Initialize the PlasmaButtons object
plasma_buttons = PlasmaButtons(num_leds, serial_port_path, refresh_rate)

# Create RGBl objects for the effects
start_rgbl = RGBl(255, 0, 0, 64)
end_rgbl = RGBl(0, 0, 255, 64)
blink_color1 = RGBl(255, 255, 255, 64)
blink_color2 = RGBl(0, 0, 0, 64)

# Perform a fade effect
plasma_buttons.fade_effect(start_rgbl, end_rgbl, duration=3)

# Perform a blink effect
plasma_buttons.blink_effect(blink_color1, blink_color2, blink_rate=2, duration=5)

# Stop the refresh loop when done
plasma_buttons.stop()
