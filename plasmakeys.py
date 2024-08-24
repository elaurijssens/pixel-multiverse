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

    def set_led_data(self, led_number, rgbl: RGBl):
        """
        Set the data for the specified LED in the button_leds array.

        :param led_number: The index of the LED to update.
        :param rgbl: An RGBl NamedTuple with red, green, blue, and brightness values.
        """
        start_index = led_number * 4
        with self._lock:  # Ensure thread safety when modifying the button_leds array
            self.button_leds[start_index] = rgbl.red
            self.button_leds[start_index + 1] = rgbl.green
            self.button_leds[start_index + 2] = rgbl.blue
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
                print(f"Data sent to {self.serial_port_path}")
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


# Example usage:
num_leds = 128
serial_port_path = "/dev/ttyACM0"
refresh_rate = 60

# Initialize the PlasmaButtons object
plasma_buttons = PlasmaButtons(num_leds, serial_port_path, refresh_rate)

# Create an RGBl object
rgbl_values = RGBl(255, 255, 255, 255)

# Set data for the first LED
plasma_buttons.set_led_data(0, rgbl_values)

# Allow the program to run for a while before stopping (example)
time.sleep(5)

# Stop the refresh loop when done
plasma_buttons.stop()
