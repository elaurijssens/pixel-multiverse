import time
import serial
import threading
from collections import namedtuple

# Define a NamedTuple for RGBl
RGBl = namedtuple('RGBl', ['red', 'green', 'blue', 'brightness'])

class LEDStatus:
    def __init__(self):
        # Default to normal mode with a black color
        self.mode = 'normal'
        self.color = RGBl(0, 0, 0, 0)
        self.color_off = RGBl(0, 0, 0, 0)
        self.blink_rate = 0
        self.fade_to = RGBl(0, 0, 0, 0)
        self.fade_time = 0
        self.ticks_since_last_transition = 0
        self.start_from = RGBl(0, 0, 0, 0)

class PlasmaButtons:
    PREFIX = b"multiverse:data"
    COLOR_MASK = 0b00111111  # Mask to limit color values to a maximum of 63
    BRIGHTNESS_MASK = 0b00111111  # Mask to limit brightness values to a maximum of 63

    def __init__(self, num_leds, serial_port_path="/dev/plasmabuttons", refresh_rate=60):
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
        # Initialize LED statuses
        self.led_statuses = [LEDStatus() for _ in range(num_leds)]
        # Create a threading event to control the refresh loop
        self._stop_event = threading.Event()
        # Create a lock for thread safety
        self._lock = threading.Lock()
        # Start the refresh thread
        self._start_refresh_thread()

    def set_led_mode(self, led_number, mode, **kwargs):
        """
        Set the mode and parameters for a specific LED.

        :param led_number: The index of the LED to update.
        :param mode: The mode to set ('normal', 'blink', 'sync blink', 'fade', 'fade sweep').
        :param kwargs: Additional parameters based on the mode.
        """
        led_status = self.led_statuses[led_number]
        with self._lock:
            led_status.mode = mode
            if mode == 'normal':
                led_status.color = kwargs.get('color', led_status.color)
            elif mode in ['blink', 'sync blink']:
                led_status.color = kwargs.get('color', led_status.color)
                led_status.color_off = kwargs.get('color_off', led_status.color)
                led_status.blink_rate = kwargs.get('blink_rate', led_status.blink_rate)
                led_status.ticks_since_last_transition = 0
            elif mode == 'fade':
                led_status.start_from = kwargs.get('start_from', led_status.color)
                led_status.fade_to = kwargs.get('fade_to', led_status.fade_to)
                led_status.fade_time = kwargs.get('fade_time', led_status.fade_time)
                led_status.ticks_since_last_transition = 0
            elif mode == 'fade sweep':
                led_status.start_from = kwargs.get('start_from', led_status.color)
                led_status.fade_to = kwargs.get('fade_to', led_status.fade_to)
                led_status.fade_time = kwargs.get('fade_time', led_status.fade_time)
                led_status.ticks_since_last_transition = 0

    def set_button_mode(self, button_number, mode, **kwargs):
        """
        Set the mode and parameters for all LEDs in a button.

        :param button_number: The index of the button to update.
        :param mode: The mode to set ('normal', 'blink', 'sync blink', 'fade', 'fade sweep').
        :param kwargs: Additional parameters based on the mode.
        """
        for i in range(button_number * 4, (button_number + 1) * 4):
            self.set_led_mode(i, mode, **kwargs)

    def _calculate_color(self, led_number):
        """
        Calculate the color of the LED based on its status and elapsed ticks.

        :param led_number: The index of the LED.
        """
        led_status = self.led_statuses[led_number]
        ticks = led_status.ticks_since_last_transition
        if led_status.mode == 'normal':
            return led_status.color
        elif led_status.mode == 'blink':
            cycle_length = self.refresh_rate / led_status.blink_rate
            if (ticks % cycle_length) < (cycle_length / 2):
                return led_status.color
            else:
                return led_status.color_off
        elif led_status.mode == 'sync blink':
            cycle_length = self.refresh_rate / led_status.blink_rate
            if (ticks % cycle_length) < (cycle_length / 2):
                return led_status.color
            else:
                return led_status.color_off
        elif led_status.mode == 'fade':
            ratio = min(ticks / (self.refresh_rate * led_status.fade_time), 1)
            red = int(led_status.start_from.red + (led_status.fade_to.red - led_status.start_from.red) * ratio)
            green = int(led_status.start_from.green + (led_status.fade_to.green - led_status.start_from.green) * ratio)
            blue = int(led_status.start_from.blue + (led_status.fade_to.blue - led_status.start_from.blue) * ratio)
            brightness = int(led_status.start_from.brightness + (led_status.fade_to.brightness - led_status.start_from.brightness) * ratio)
            return RGBl(red, green, blue, brightness)
        elif led_status.mode == 'fade sweep':
            half_time = self.refresh_rate * led_status.fade_time / 2
            if ticks < half_time:
                ratio = ticks / half_time
            else:
                ratio = (2 - (ticks / half_time)) if ticks < 2 * half_time else 0
            red = int(led_status.start_from.red + (led_status.fade_to.red - led_status.start_from.red) * ratio)
            green = int(led_status.start_from.green + (led_status.fade_to.green - led_status.start_from.green) * ratio)
            blue = int(led_status.start_from.blue + (led_status.fade_to.blue - led_status.start_from.blue) * ratio)
            brightness = int(led_status.start_from.brightness + (led_status.fade_to.brightness - led_status.start_from.brightness) * ratio)
            return RGBl(red, green, blue, brightness)

    def _update_led_colors(self):
        """
        Update all LED colors based on their statuses.
        """
        with self._lock:
            for i in range(self.num_leds):
                self.led_statuses[i].ticks_since_last_transition += 1
                current_color = self._calculate_color(i)
                start_index = i * 4
                self.button_leds[start_index] = current_color.blue & self.COLOR_MASK
                self.button_leds[start_index + 1] = current_color.green & self.COLOR_MASK
                self.button_leds[start_index + 2] = current_color.red & self.COLOR_MASK
                self.button_leds[start_index + 3] = current_color.brightness & self.BRIGHTNESS_MASK

    def write_to_display(self):
        """
        Write the button_leds byte array to the display via the serial port.
        """
        with self._lock:  # Ensure thread safety when reading the button_leds array
            data_to_send = self.PREFIX + self.button_leds

        # Open the serial port and send the data
        try:
            with serial.Serial(self.serial_port_path, baudrate=115200, timeout=1) as ser:  # Updated baud rate to 115200
                ser.write(data_to_send)
        except serial.SerialException as e:
            print(f"Error opening serial port {self.serial_port_path}: {e}")

    def _refresh_loop(self):
        """
        Continuously refresh the display at the specified refresh rate.
        """
        while not self._stop_event.is_set():
            self._update_led_colors()
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
serial_port_path = "/dev/plasmabuttons"
refresh_rate = 60

# Initialize the PlasmaButtons object
plasma_buttons = PlasmaButtons(num_leds, serial_port_path, refresh_rate)

# Set LED 0 to blink mode
plasma_buttons.set_led_mode(0, 'blink', color=RGBl(255, 0, 0, 64), color_off=RGBl(0, 0, 0, 0), blink_rate=2)

# Set Button 1 (LEDs 4-7) to fade mode
plasma_buttons.set_button_mode(1, 'fade', fade_to=RGBl(0, 255, 0, 64), fade_time=3)

# Allow the program to run for a while before stopping (example)
time.sleep(5)

# Stop the refresh loop when done
plasma_buttons.stop()
