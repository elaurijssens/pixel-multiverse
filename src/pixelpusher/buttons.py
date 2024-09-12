import time
import serial
import threading
from .colors import RGBl


class LEDStatus:
    def __init__(self):
        # Initialize LED status to default values
        self.mode = 'normal'  # Mode of operation ('normal', 'blink', 'sync blink', 'fade', 'fade sweep')
        self.color_from = RGBl(0, 0, 0, 0)  # Off color for blinking modes, start color for fade modes
        self.transition_time = 0  # Blinks per second for blinking modes
        self.color_to = RGBl(0, 0, 0, 0)  # Normal color, target color for fade modes, blink color for blink modes
        self.ticks_since_last_transition = 0  # Ticks since the last transition for timing calculations


class PlasmaButtons:
    PREFIX = b"multiverse:data"  # Prefix for data sent to the serial port
    COLOR_MASK = 0b00111111  # Mask to limit color values to a maximum of 63
    BRIGHTNESS_MASK = 0b00001111  # Mask to limit brightness values to a maximum of 15

    def __init__(self, num_leds, serial_port_path="/dev/plasmabuttons",
                 refresh_rate=60, button_map=None, coord_map=None):
        """
        Initialize the PlasmaButtons class.

        :param num_leds: The number of LEDs to control.
        :param serial_port_path: The path to the serial port.
        :param refresh_rate: The refresh rate (times per second) for writing to the display.
        :param button_map: An optional dictionary mapping button labels to button numbers.
        :param coord_map: An optional dictionary mapping integer coordinates to LED indices.
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
        # Initialize button mapping if provided
        self.button_map = button_map if button_map is not None else {}
        # Initialize coordinate mapping if provided
        self.coord_map = coord_map if coord_map is not None else {}
        # Create a threading event to control the refresh loop
        self._stop_event = threading.Event()
        # Create a lock for thread safety
        self._lock = threading.Lock()
        # Start the refresh thread
        self._start_refresh_thread()

    def set_led_mode(self, led_number, mode, color_to=None, color_from=None, transition_time=None):
        """
        Set the mode and parameters for a specific LED.

        :param led_number: The index of the LED to update.
        :param mode: The mode to set ('normal', 'blink', 'fade', 'fade sweep').
        :param color_to: The target color or blink color.
        :param color_from: The starting color for fade or off color for blinking.
        :param transition_time: The transition time for fade or blink interval.
        """
        # Access the LED status for the given LED number
        led_status = self.led_statuses[led_number]
        led_status.mode = mode  # Set the mode

        if mode == 'normal':
            led_status.color_to = color_to if color_to else RGBl(0, 0, 0, 0)
        elif mode == 'blink':
            led_status.color_from = color_from if color_from else led_status.color_to
            led_status.color_to = color_to if color_to else led_status.color_to
            led_status.transition_time = transition_time if transition_time else led_status.transition_time
            led_status.ticks_since_last_transition = 0  # Reset tick counter
        elif mode == 'fade':
            led_status.color_from = color_from if color_from else led_status.color_to
            led_status.color_to = color_to if color_to else led_status.color_to
            led_status.transition_time = transition_time if transition_time else led_status.transition_time
            led_status.ticks_since_last_transition = 0  # Reset tick counter
        elif mode == 'fade sweep':
            led_status.color_from = color_from if color_from else led_status.color_to
            led_status.color_to = color_to if color_to else led_status.color_to
            led_status.transition_time = transition_time if transition_time else led_status.transition_time
            led_status.ticks_since_last_transition = 0  # Reset tick counter

    def set_button_mode(self, button_number, mode, color_to=None, color_from=None, transition_time=None):
        """
        Set the mode and parameters for all LEDs in a button by button number.

        :param button_number: The index of the button to update.
        :param mode: The mode to set ('normal', 'blink', 'fade', 'fade sweep').
        :param color_to: The target color or blink color.
        :param color_from: The starting color for fade or off color for blinking.
        :param transition_time: The transition time for fade or blink interval.
        """
        # Update all LEDs in the specified button (assuming 4 LEDs per button)
        for i in range(button_number * 4, (button_number + 1) * 4):
            self.set_led_mode(i, mode, color_to=color_to, color_from=color_from, transition_time=transition_time)

    def set_button_mode_by_label(self, button_label, mode, color_to=None, color_from=None, transition_time=None):
        """
        Set the mode and parameters for all LEDs in a button by button label.

        :param button_label: The label of the button to update (e.g., 'P1:A', 'P2:B').
        :param mode: The mode to set ('normal', 'blink', 'fade', 'fade sweep').
        :param color_to: The target color or blink color.
        :param color_from: The starting color for fade or off color for blinking.
        :param transition_time: The transition time for fade or blink interval.
        """
        # Check if the button label exists in the mapping
        if self.button_map and button_label in self.button_map:
            button_number = self.button_map[button_label]
            # Use the existing method to set button mode by number
            self.set_button_mode(button_number, mode,
                                 color_to=color_to, color_from=color_from, transition_time=transition_time)

    def set_led_mode_by_coord(self, coord, mode, color_to=None, color_from=None, transition_time=None):
        """
        Set the mode and parameters for a specific LED by world coordinate.

        :param coord: A tuple representing the (x, y) coordinate of the LED.
        :param mode: The mode to set ('normal', 'blink', 'fade', 'fade sweep').
        :param color_to: The target color or blink color.
        :param color_from: The starting color for fade or off color for blinking.
        :param transition_time: The transition time for fade or blink interval.
        """
        # Check if the coordinate exists in the mapping
        if self.coord_map and coord in self.coord_map:
            led_number = self.coord_map[coord]
            # Use the existing method to set LED mode by LED number
            self.set_led_mode(led_number, mode,
                              color_to=color_to, color_from=color_from, transition_time=transition_time)

    def _calculate_color(self, led_number):
        """
        Calculate the color of the LED based on its status and elapsed ticks.

        :param led_number: The index of the LED.
        :return: An RGBl tuple representing the calculated color.
        """
        # Get the status of the LED
        led_status = self.led_statuses[led_number]
        # Get the number of ticks since the last transition
        ticks = led_status.ticks_since_last_transition

        # Determine the color based on the mode
        if led_status.mode == 'normal':
            return led_status.color_to
        elif led_status.mode == 'blink':
            # Calculate blink status based on ticks
            cycle_length = self.refresh_rate * led_status.transition_time
            if (ticks % cycle_length) < (cycle_length / 2):
                return led_status.color_to
            else:
                return led_status.color_from
        elif led_status.mode == 'fade':
            # Calculate fade status based on ticks
            total_ticks_for_fade = self.refresh_rate * led_status.transition_time
            if ticks >= total_ticks_for_fade:
                # Fade is complete, switch to normal mode with final color
                self.set_led_mode(led_number, 'normal', color_to=led_status.color_to)
                return led_status.color_to
            # Calculate intermediate color during fade
            ratio = ticks / total_ticks_for_fade
            red = int(led_status.color_from.red + (led_status.color_to.red - led_status.color_from.red) * ratio)
            green = int(led_status.color_from.green + (led_status.color_to.green - led_status.color_from.green) * ratio)
            blue = int(led_status.color_from.blue + (led_status.color_to.blue - led_status.color_from.blue) * ratio)
            brightness = int(led_status.color_from.brightness + (
                    led_status.color_to.brightness - led_status.color_from.brightness) * ratio)
            return RGBl(red, green, blue, brightness)
        elif led_status.mode == 'fade sweep':
            # Calculate fade sweep status based on ticks
            total_ticks_for_fade = self.refresh_rate * led_status.transition_time
            half_time_ticks = total_ticks_for_fade / 2
            if ticks >= total_ticks_for_fade:
                # Sweep complete, reset ticks
                led_status.ticks_since_last_transition = 0
                return led_status.color_from
            # Calculate intermediate color during fade sweep
            if ticks < half_time_ticks:
                ratio = ticks / half_time_ticks
            else:
                ratio = (total_ticks_for_fade - ticks) / half_time_ticks
            red = int(led_status.color_from.red + (led_status.color_to.red - led_status.color_from.red) * ratio)
            green = int(led_status.color_from.green + (led_status.color_to.green - led_status.color_from.green) * ratio)
            blue = int(led_status.color_from.blue + (led_status.color_to.blue - led_status.color_from.blue) * ratio)
            brightness = int(led_status.color_from.brightness + (
                    led_status.color_to.brightness - led_status.color_from.brightness) * ratio)
            return RGBl(red, green, blue, brightness)

    def _update_led_colors(self):
        """
        Update all LED colors based on their statuses.
        """
        with self._lock:  # Ensure thread safety when updating LED colors
            for i in range(self.num_leds):
                # Increment ticks for timing calculations
                self.led_statuses[i].ticks_since_last_transition += 1
                # Calculate the current color based on the mode and ticks
                current_color = self._calculate_color(i)
                start_index = i * 4
                # Update the button_leds byte array with the calculated color values
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
            with serial.Serial(self.serial_port_path, baudrate=115200, timeout=1) as ser:
                ser.write(data_to_send)
        except serial.SerialException as e:
            print(f"Error opening serial port {self.serial_port_path}: {e}")

    def _refresh_loop(self):
        """
        Continuously refresh the display at the specified refresh rate.
        """
        while not self._stop_event.is_set():
            # Update LED colors and send to display
            self._update_led_colors()
            self.write_to_display()
            time.sleep(1 / self.refresh_rate)  # Sleep to maintain the refresh rate

    def _start_refresh_thread(self):
        """
        Start the thread for continuously refreshing the display.
        """
        self._refresh_thread = threading.Thread(target=self._refresh_loop)
        self._refresh_thread.daemon = True  # Daemon thread will automatically close when the main program exits
        self._refresh_thread.start()

    def stop(self):
        """
        Stop the refresh loop.
        """
        self._stop_event.set()  # Signal the refresh loop to stop
        self._refresh_thread.join()  # Wait for the refresh thread to finish

    def __str__(self):
        """
        Return a string representation of the button_leds byte array for debugging.
        """
        with self._lock:  # Ensure thread safety when accessing the button_leds array
            return str(list(self.button_leds))
