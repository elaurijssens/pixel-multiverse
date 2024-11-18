import time
import serial
import threading
import math
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
    COLOR_MASK = 0b11111111  # Mask to limit color values to a maximum of 255
    BRIGHTNESS_MASK = 0b00011111  # Mask to limit brightness values to a maximum of 31

    def __init__(self, num_leds, serial_port_path="/dev/plasmabuttons",
                 refresh_rate=60, button_map=None, coord_map=None):
        """
        Initialize the PlasmaButtons class.
        """
        self.num_leds = num_leds
        self.button_leds = bytearray([0] * (num_leds * 4))
        self.serial_port_path = serial_port_path
        self.refresh_rate = refresh_rate
        self.led_statuses = [LEDStatus() for _ in range(num_leds)]
        self.button_map = button_map if button_map is not None else {}
        self.coord_map = coord_map if coord_map is not None else {}
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._start_refresh_thread()

        # Attract mode variables
        self._attract_mode_running = False
        self._attract_mode_thread = None
        self._attract_mode_stop_event = threading.Event()
        self._pattern_queue = []
        self._current_pattern_index = 0

    # Existing methods...

    # Refactored attract mode methods with pattern queue and color parameters
    def start_attract_mode(self, pattern_queue):
        """
        Start the attract mode with the specified pattern queue.

        :param pattern_queue: A list of tuples (pattern_name, pattern_params)
        """
        if not self._attract_mode_running:
            self._attract_mode_running = True
            self._attract_mode_stop_event.clear()
            self._pattern_queue = pattern_queue
            self._current_pattern_index = 0
            self._attract_mode_thread = threading.Thread(target=self._run_attract_mode)
            self._attract_mode_thread.daemon = True
            self._attract_mode_thread.start()

    def stop_attract_mode(self):
        """
        Stop the attract mode.
        """
        if self._attract_mode_running:
            self._attract_mode_running = False
            self._attract_mode_stop_event.set()
            self._attract_mode_thread.join()
            self._clear_leds()  # Clear LEDs when stopping attract mode

    def attract_mode_active(self):
        return self._attract_mode_running

    def _run_attract_mode(self):
        """
        Run the attract mode patterns in the queue.
        """
        patterns = {
            'linear': self._pattern_linear,
            'radial': self._pattern_radial,
            'circular': self._pattern_circular,
        }

        while not self._attract_mode_stop_event.is_set():
            pattern_name, pattern_params = self._pattern_queue[self._current_pattern_index]
            pattern_func = patterns.get(pattern_name)
            if pattern_func:
                pattern_func(**pattern_params)
            else:
                print(f"Pattern '{pattern_name}' not recognized.")
            self._current_pattern_index = (self._current_pattern_index + 1) % len(self._pattern_queue)

    def _clear_leds(self):
        """
        Clear all LEDs by setting them to off.
        """
        with self._lock:
            for led_status in self.led_statuses:
                led_status.mode = 'normal'
                led_status.color_to = RGBl(0, 0, 0, 0)

    # Generalized linear pattern method
    def _pattern_linear(self, direction, color_on=RGBl(31, 31, 31, 5), color_off=RGBl(0, 0, 0, 0), delay=0.05):
        """
        Generalized method for linear patterns.

        :param direction: Direction of the pattern ('left_to_right', 'right_to_left', 'top_to_bottom', 'bottom_to_top')
        :param color_on: Color when LEDs are activated.
        :param color_off: Color when LEDs are reset.
        :param delay: Delay between steps.
        """
        x_values = sorted(set(coord[0] for coord in self.coord_map.keys()))
        y_values = sorted(set(coord[1] for coord in self.coord_map.keys()))

        min_x, max_x = min(x_values), max(x_values) + 1
        min_y, max_y = min(y_values), max(y_values) + 1

        if direction == 'left_to_right':
            x_range = range(min_x, max_x)
            y_range = range(min_y, max_y)
        elif direction == 'right_to_left':
            x_range = reversed(range(min_x, max_x))
            y_range = range(min_y, max_y)
        elif direction == 'top_to_bottom':
            x_range = range(min_x, max_x)
            y_range = range(min_y, max_y)
        elif direction == 'bottom_to_top':
            x_range = range(min_x, max_x)
            y_range = reversed(range(min_y, max_y))
        else:
            print(f"Direction '{direction}' not recognized.")
            return

        # Determine iteration order based on direction
        if direction in ['left_to_right', 'right_to_left']:
            outer_range = x_range
            inner_range = y_range
            outer_coord_index = 0  # x-coordinate
            inner_coord_index = 1  # y-coordinate
        else:
            outer_range = y_range
            inner_range = x_range
            outer_coord_index = 1  # y-coordinate
            inner_coord_index = 0  # x-coordinate

        # First loop: Turn on LEDs
        for outer in outer_range:
            for inner in inner_range:
                coord = [0, 0]
                coord[outer_coord_index] = outer
                coord[inner_coord_index] = inner
                coord = tuple(coord)
                if coord in self.coord_map:
                    self.set_led_mode_by_coord(coord=coord, mode="normal", color_to=color_on)
            time.sleep(delay)
            if self._attract_mode_stop_event.is_set():
                return
        time.sleep(0.2)
        # Second loop: Reset LEDs
        for outer in outer_range:
            for inner in inner_range:
                coord = [0, 0]
                coord[outer_coord_index] = outer
                coord[inner_coord_index] = inner
                coord = tuple(coord)
                if coord in self.coord_map:
                    self.set_led_mode_by_coord(coord=coord, mode="normal", color_to=color_off)
            time.sleep(delay)
            if self._attract_mode_stop_event.is_set():
                return

    # Implement radial and circular patterns with parameters
    def _pattern_circular(self, direction, color_on=RGBl(31, 31, 31, 5), color_off=RGBl(0, 0, 0, 0), delay=0.05):
        """
        Generalized method for circular patterns.

        :param direction: Direction of the pattern ('outward', 'inward')
        :param color_on: Color when LEDs are activated.
        :param color_off: Color when LEDs are reset.
        :param delay: Delay between steps.
        """
        # Calculate the center of the playfield
        x_values = [coord[0] for coord in self.coord_map.keys()]
        y_values = [coord[1] for coord in self.coord_map.keys()]
        center_x = (min(x_values) + max(x_values)) / 2
        center_y = (min(y_values) + max(y_values)) / 2

        # Calculate distances from the center for all coordinates
        coord_distances = {}
        for coord in self.coord_map.keys():
            dx = coord[0] - center_x
            dy = coord[1] - center_y
            distance = math.hypot(dx, dy)
            coord_distances[coord] = distance

        # Sort coordinates by distance
        sorted_coords = sorted(coord_distances.items(), key=lambda item: item[1])

        # Determine the range of steps based on direction
        max_distance = max(coord_distances.values())
        num_steps = int(max_distance) + 1

        if direction == 'outward':
            steps_range = range(num_steps)
        elif direction == 'inward':
            steps_range = reversed(range(num_steps))
        else:
            print(f"Direction '{direction}' not recognized for circular pattern.")
            return

        # First loop: Activate LEDs based on distance
        for step in steps_range:
            for coord, distance in sorted_coords:
                if int(distance) == step:
                    self.set_led_mode_by_coord(coord=coord, mode="normal", color_to=color_on)
            time.sleep(delay)
            if self._attract_mode_stop_event.is_set():
                return
        time.sleep(0.2)
        # Second loop: Reset LEDs based on distance
        for step in steps_range:
            for coord, distance in sorted_coords:
                if int(distance) == step:
                    self.set_led_mode_by_coord(coord=coord, mode="normal", color_to=color_off)
            time.sleep(delay)
            if self._attract_mode_stop_event.is_set():
                return

    # Implement radial patterns
    def _pattern_radial(self, direction, color_on=RGBl(31, 31, 0, 5), color_off=RGBl(0, 0, 0, 0), delay=0.05):
        x_values = [coord[0] for coord in self.coord_map.keys()]
        y_values = [coord[1] for coord in self.coord_map.keys()]
        center_x = (min(x_values) + max(x_values)) / 2
        center_y = (min(y_values) + max(y_values)) / 2

        # Calculate angles
        coord_angles = {}
        for coord in self.coord_map.keys():
            dx = coord[0] - center_x
            dy = coord[1] - center_y
            angle = (math.atan2(dy, dx) + 2 * math.pi) % (2 * math.pi)
            coord_angles[coord] = angle

        # Sort coordinates by angle
        sorted_coords = sorted(coord_angles.items(), key=lambda item: item[1], reverse=(direction == 'anticlockwise'))

        # First loop: Turn on LEDs
        for coord, angle in sorted_coords:
            self.set_led_mode_by_coord(coord=coord, mode="normal", color_to=color_on)
            time.sleep(delay)
            if self._attract_mode_stop_event.is_set():
                return
        time.sleep(0.5)
        # Second loop: Reset LEDs
        for coord, angle in sorted_coords:
            self.set_led_mode_by_coord(coord=coord, mode="normal", color_to=color_off)
            time.sleep(delay)
            if self._attract_mode_stop_event.is_set():
                return

    # Existing methods continued...

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


    def set_all_leds(self, mode, color_to=None, color_from=None, transition_time=None):
        for led in range(0, self.num_leds):
            self.set_led_mode(led, mode=mode, color_to=color_to, color_from=color_from, transition_time=transition_time)

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
