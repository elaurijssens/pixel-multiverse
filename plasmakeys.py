import time
import serial
import threading
from collections import namedtuple

# Define a NamedTuple for RGBl (Red, Green, Blue, Brightness)
RGBl = namedtuple('RGBl', ['red', 'green', 'blue', 'brightness'])

class LEDStatus:
    def __init__(self):
        self.mode = 'normal'  # Mode of operation ('normal', 'blink', 'sync blink', 'fade', 'fade sweep')
        self.color = RGBl(0, 0, 0, 0)  # Color in normal mode
        self.color_off = RGBl(0, 0, 0, 0)  # Off color for blinking modes
        self.blink_rate = 0  # Blinks per second for blinking modes
        self.fade_to = RGBl(0, 0, 0, 0)  # Target color for fade modes
        self.fade_time = 0  # Duration of the fade in seconds
        self.ticks_since_last_transition = 0  # Ticks since the last transition for timing calculations
        self.start_from = RGBl(0, 0, 0, 0)  # Starting color for fade modes

class PlasmaButtons:
    PREFIX = b"multiverse:data"  # Prefix for data sent to the serial port
    COLOR_MASK = 0b00111111  # Mask to limit color values to a maximum of 63
    BRIGHTNESS_MASK = 0b00001111  # Mask to limit brightness values to a maximum of 15

    def __init__(self, num_leds, serial_port_path="/dev/plasmabuttons", refresh_rate=60, button_map=None):
        """
        Initialize the PlasmaButtons class.

        :param num_leds: The number of LEDs to control.
        :param serial_port_path: The path to the serial port.
        :param refresh_rate: The refresh rate (times per second) for writing to the display.
        :param button_map: An optional dictionary mapping button labels to button numbers.
        """
        self.num_leds = num_leds
        self.button_leds = bytearray([0] * (num_leds * 4))
        self.serial_port_path = serial_port_path
        self.refresh_rate = refresh_rate
        self.led_statuses = [LEDStatus() for _ in range(num_leds)]
        self.button_map = button_map if button_map is not None else {}  # Initialize button mapping
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._start_refresh_thread()

    def set_led_mode(self, led_number, mode, **kwargs):
        """
        Set the mode and parameters for a specific LED.

        :param led_number: The index of the LED to update.
        :param mode: The mode to set ('normal', 'blink', 'sync blink', 'fade', 'fade sweep').
        :param kwargs: Additional parameters based on the mode.
        """
        led_status = self.led_statuses[led_number]
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
        Set the mode and parameters for all LEDs in a button by button number.

        :param button_number: The index of the button to update.
        :param mode: The mode to set ('normal', 'blink', 'sync blink', 'fade', 'fade sweep').
        :param kwargs: Additional parameters based on the mode.
        """
        for i in range(button_number * 4, (button_number + 1) * 4):
            self.set_led_mode(i, mode, **kwargs)

    def set_button_mode_by_label(self, button_label, mode, **kwargs):
        """
        Set the mode and parameters for all LEDs in a button by button label.

        :param button_label: The label of the button to update (e.g., 'P1:A', 'P2:B').
        :param mode: The mode to set ('normal', 'blink', 'sync blink', 'fade', 'fade sweep').
        :param kwargs: Additional parameters based on the mode.
        """
        # Check if the button label exists in the mapping
        if self.button_map and button_label in self.button_map:
            button_number = self.button_map[button_label]
            self.set_button_mode(button_number, mode, **kwargs)
        else:
            print(f"Button label '{button_label}' not found in button map or no map provided.")

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
            total_ticks_for_fade = self.refresh_rate * led_status.fade_time
            if ticks >= total_ticks_for_fade:
                self.set_led_mode(led_number, 'normal', color=led_status.fade_to)
                return led_status.fade_to
            ratio = ticks / total_ticks_for_fade
            red = int(led_status.start_from.red + (led_status.fade_to.red - led_status.start_from.red) * ratio)
            green = int(led_status.start_from.green + (led_status.fade_to.green - led_status.start_from.green) * ratio)
            blue = int(led_status.start_from.blue + (led_status.fade_to.blue - led_status.start_from.blue) * ratio)
            brightness = int(led_status.start_from.brightness + (
                    led_status.fade_to.brightness - led_status.start_from.brightness) * ratio)
            return RGBl(red, green, blue, brightness)
        elif led_status.mode == 'fade sweep':
            total_ticks_for_fade = self.refresh_rate * led_status.fade_time
            half_time_ticks = total_ticks_for_fade / 2
            if ticks >= total_ticks_for_fade:
                led_status.ticks_since_last_transition = 0
                return led_status.start_from
            if ticks < half_time_ticks:
                ratio = ticks / half_time_ticks
            else:
                ratio = (total_ticks_for_fade - ticks) / half_time_ticks
            red = int(led_status.start_from.red + (led_status.fade_to.red - led_status.start_from.red) * ratio)
            green = int(led_status.start_from.green + (led_status.fade_to.green - led_status.start_from.green) * ratio)
            blue = int(led_status.start_from.blue + (led_status.fade_to.blue - led_status.start_from.blue) * ratio)
            brightness = int(led_status.start_from.brightness + (
                    led_status.fade_to.brightness - led_status.start_from.brightness) * ratio)
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
        with self._lock:
            data_to_send = self.PREFIX + self.button_leds

        try:
            with serial.Serial(self.serial_port_path, baudrate=115200, timeout=1) as ser:
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
        """
        Return a string representation of the button_leds byte array for debugging.
        """
        with self._lock:
            return str(list(self.button_leds))


# Example usage:

# Define a button map
button_map = {
    'P1:A': 0,
    'P1:B': 1,
    'P2:A': 2,
    'P2:B': 3,
    # ... other button mappings
}

num_leds = 128
refresh_rate = 60
serial_port = "/dev/plasmabuttons"

# Initialize the PlasmaButtons object with the button map
plasma_buttons = PlasmaButtons(num_leds, serial_port, refresh_rate, button_map)

# Set LED modes using button labels
plasma_buttons.set_button_mode_by_label('P1:A', 'blink', color=RGBl(63, 0, 0, 15), color_off=RGBl(0, 0, 0, 0), blink_rate=2)
plasma_buttons.set_button_mode_by_label('P2:B', 'fade', fade_to=RGBl(0, 63, 0, 15), fade_time=2)

# Allow the program to run for a while before stopping (example)
time.sleep(30)

# Stop the refresh loop when done
plasma_buttons.stop()
