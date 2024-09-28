# Pixel-Multiverse

**Pixel-Multiverse** is a Python library designed to simplify controlling LED buttons and LED matrices for Pimoroni Picade 
projects. The library includes abstractions for both button LED control and matrix LED displays, providing an 
easy-to-use interface for managing complex lighting effects and patterns.

## Features

- **Button LED Control**: Provides an interface to control multiple LED buttons, including support for 
different lighting modes (such as blinking, fading, and color transitions).
- **Matrix LED Display**: Offers methods for controlling LED matrices with support for drawing images, 
setting pixel colors, and handling brightness and opacity.

## Installation

To install the Pixel-Multiverse library, you can add it to your project by cloning the repository:

```bash
pip install pixel-multiverse
```

## Usage

### Button LED Control

The `PlasmaButtons` class provides an interface to control a set of LEDs via a serial port. It supports various modes of operation for each LED (such as blinking, fading, and sweeping transitions), and can control LED colors, brightness, and update rates.

#### Example:

```python
import time
from pixelpusher import PlasmaButtons, RGBl

# Initialize PlasmaButtons for 16 LEDs with a specific serial port path
plasma_buttons = PlasmaButtons(num_leds=16, serial_port_path="/dev/ttyUSB0", refresh_rate=60)

# Set the first LED to blink between red and black
plasma_buttons.set_led_mode(0, mode='blink', color_to=RGBl(255, 0, 0), color_from=RGBl(0, 0, 0), transition_time=1)

# Start the display update loop
time.sleep(10)

# Stop the display
plasma_buttons.stop()
```

### **Methods:**

- `__init__(self, num_leds, serial_port_path="/dev/plasmabuttons", refresh_rate=60, button_map=None, coord_map=None)`:
  Initializes the PlasmaButtons class to control a specific number of LEDs connected to a serial port.
  
  - `num_leds`: The number of LEDs to control.
  - `serial_port_path`: Path to the serial port device.
  - `refresh_rate`: How often the display should refresh (in frames per second).
  - `button_map`: Optional dictionary mapping button labels to button numbers. A button map is a dictionary containing
text labels and button numbers, e.g. `{"A":1, "B":2, "X":3}`
  - `coord_map`: Optional dictionary mapping coordinates to LED indices. A coordinates map is a dictionary containing
x,y coordinates and led numbers, e.g. `{(68, 14): 0, (65, 12): 1, (63, 15): 2, (66, 17): 3}`

- `set_led_mode(self, led_number, mode, color_to=None, color_from=None, transition_time=None)`:
  Sets the mode and parameters for a specific LED.
  
  - `led_number`: Index of the LED to update.
  - `mode`: Mode to set ('normal', 'blink', 'fade', 'fade sweep').
  - `color_to`: Target color for the mode.
  - `color_from`: Starting color for transitions.
  - `transition_time`: Time interval for transitions like blinking or fading.

- `set_button_mode(self, button_number, mode, color_to=None, color_from=None, transition_time=None)`:
  Sets the mode for all LEDs within a button (assuming 4 LEDs per button).

- `set_button_mode_by_label(self, button_label, mode, color_to=None, color_from=None, transition_time=None)`:
  Sets the mode for a button using a label (e.g., `'P1:A'`, `'P2:B'`).

- `set_led_mode_by_coord(self, coord, mode, color_to=None, color_from=None, transition_time=None)`:
  Sets the mode for an LED by its world coordinate, if coordinates are mapped.

- `write_to_display(self)`:
  Writes the current LED state to the display via the serial port.

- `stop(self)`:
  Stops the refresh loop, halting the updating of LED colors.

#### Additional Features:

- **Color Calculations**: The class handles color blending and transitioning for modes like fade and sweep.
- **Threading for Refresh**: The display is updated in a separate thread to maintain real-time responsiveness.

### Matrix LED Control

The `LedMatrix` class is designed to control an LED matrix display. It supports both static images and animated GIFs, and allows for flexible control over color orders and display sizes. The class can handle image cropping, rescaling, and pixel blending for smooth transitions.

#### Example:

```python
from pixelpusher import LedMatrix, COLOR_ORDER_RGB, DISPLAY_GALACTIC_UNICORN

# Initialize a Galactic Unicorn display with RGB color order
matrix = LedMatrix(display=DISPLAY_GALACTIC_UNICORN, color_order=COLOR_ORDER_RGB)

# Display a static image
matrix.display_image("path/to/image.png", rescale=True, brightness=150)

# Stop the display when done
matrix.stop()
```

### **Methods:**

- `__init__(self, display=DISPLAY_GALACTIC_UNICORN, serial_port_path="/dev/unicorn", color_order=COLOR_ORDER_RGB)`:
  Initializes the `LedMatrix` object with a specified display size, serial port for communication, and color order.
  
  - `display`: Type of display (e.g., `DISPLAY_GALACTIC_UNICORN`, `DISPLAY_INTERSTATE75_128x32`).
  - `serial_port_path`: Path to the serial port.
  - `color_order`: Tuple defining the order of color channels (e.g., RGB, BGR).

- `stop(self)`:
  Stops any ongoing display, such as an animated GIF, and halts updates to the LED matrix.

- `write_to_display(self)`:
  Sends the contents of the display buffer to the LED matrix via the serial port.

- `translate_buffer(self)`:
  Translates the internal display buffer according to the configured color order before sending it to the LED matrix.

- `_set_pixel(self, x, y, color: RGBl)`:
  Internal method to set the color of a pixel at coordinates `(x, y)` to a specific `RGBl` color.

- `_get_pixel(self, x, y)`:
  Internal method to retrieve the color of a pixel at coordinates `(x, y)`.

- `clear_with_background(self, background_color: RGBl)`:
  Clears the display buffer by filling it with the specified background color.

- `display_image(self, image_path, rescale=False, background_color=None, brightness=127)`:
  Displays a static image (PNG or single-frame GIF) or an animated GIF on the LED matrix. Animated GIFs will loop asynchronously in a separate thread.
  
  - `image_path`: Path to the PNG or GIF file.
  - `rescale`: If `True`, the image is rescaled to fit the display dimensions.
  - `background_color`: The background color to use for transparent areas (optional).
  - `brightness`: Brightness of the display (default is 127).

- `_display_frame(self, img, rescale, brightness)`:
  Displays a single frame from an image or GIF on the matrix, with support for rescaling and blending pixels based on opacity and brightness.

- `display_text(self, message, brightness)`:
  Displays a text message on the LED matrix.
  
  - `message`: The text message to display.
  - `brightness`: Brightness of the displayed text.

## examples.py

`/dev/unicorn`? Yes, I have remapped the Galactic Unicorn's USB tty to /dev/unicorn through udev. But please do 
replace it with your own USB connection, usually /dev/ttyACM0 or /dev/ttyACM1.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

