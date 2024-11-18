# Pixel-Multiverse

**Pixel-Multiverse** is a Python library designed to simplify controlling LED buttons and LED matrices for Pimoroni Picade and other similar projects. The library includes abstractions for both button LED control and matrix LED displays, providing an easy-to-use interface for managing complex lighting effects and patterns.

## Features

- **Button LED Control**: Provides an interface to control multiple LED buttons, including support for different lighting modes such as blinking, fading, and color transitions.
- **Attract Mode**: Supports running continuous background animations (patterns) with customizable parameters, including pattern queues for sequencing multiple animations.
- **Matrix LED Display**: Offers methods for controlling LED matrices with support for drawing images, setting pixel colors, displaying text, and handling brightness and opacity.

## Installation

To install the Pixel-Multiverse library, you can add it to your project by cloning the repository or installing via `pip` (if available):

```bash
pip install pixel-multiverse
```

## Usage

### Button LED Control

The `PlasmaButtons` class provides an interface to control a set of LEDs via a serial port. It supports various modes of operation for each LED (such as blinking, fading, and sweeping transitions), and can control LED colors, brightness, and update rates.

#### Example:

```python
import time
from pixel_multiverse import PlasmaButtons, RGBl

# Initialize PlasmaButtons for 16 LEDs with a specific serial port path
plasma_buttons = PlasmaButtons(
    num_leds=16,
    serial_port_path="/dev/ttyUSB0",
    refresh_rate=60,
    coord_map={
        (0, 0): 0,
        (1, 0): 1,
        # ... add mappings for all your LEDs
    }
)

# Set the first LED to blink between red and black
plasma_buttons.set_led_mode(
    led_number=0,
    mode='blink',
    color_to=RGBl(255, 0, 0, 15),
    color_from=RGBl(0, 0, 0, 0),
    transition_time=1
)

# Start an attract mode with a pattern queue
pattern_queue = [
    ('linear', {'direction': 'left_to_right', 'color_on': RGBl(31, 0, 0, 5), 'color_off': RGBl(0, 0, 0, 0), 'delay': 0.05}),
    ('circular', {'direction': 'outward', 'color_on': RGBl(0, 31, 0, 5), 'color_off': RGBl(0, 0, 0, 0), 'delay': 0.1}),
    ('radial', {'direction': 'clockwise', 'color_on': RGBl(0, 0, 31, 5), 'color_off': RGBl(0, 0, 0, 0), 'delay': 0.05}),
    # Add more patterns as needed
]


plasma_buttons.start_attract_mode(pattern_queue)

# Let the attract mode run for 30 seconds
time.sleep(30)

# Stop the attract mode and the display
plasma_buttons.stop_attract_mode()
plasma_buttons.stop()
```

#### **Class Initialization:**

```python
plasma_buttons = PlasmaButtons(
    num_leds,
    serial_port_path="/dev/plasmabuttons",
    refresh_rate=60,
    button_map=None,
    coord_map=None
)
```

- `num_leds`: The number of LEDs to control.
- `serial_port_path`: Path to the serial port device.
- `refresh_rate`: How often the display should refresh (in frames per second).
- `button_map`: Optional dictionary mapping button labels to button numbers.
- `coord_map`: Optional dictionary mapping coordinates to LED indices.

#### **Methods:**

- `set_led_mode(self, led_number, mode, color_to=None, color_from=None, transition_time=None)`: Sets the mode and parameters for a specific LED.
  - `led_number`: Index of the LED to update.
  - `mode`: Mode to set (`'normal'`, `'blink'`, `'fade'`, `'fade sweep'`).
  - `color_to`: Target color for the mode.
  - `color_from`: Starting color for transitions.
  - `transition_time`: Time interval for transitions like blinking or fading.

- `set_led_mode_by_coord(self, coord, mode, color_to=None, color_from=None, transition_time=None)`: Sets the mode for an LED by its coordinate.
  - `coord`: A tuple representing the `(x, y)` coordinate of the LED.
  - Other parameters are the same as `set_led_mode`.

- `set_button_mode(self, button_number, mode, color_to=None, color_from=None, transition_time=None)`: Sets the mode for all LEDs within a button (assuming multiple LEDs per button).

- `set_button_mode_by_label(self, button_label, mode, color_to=None, color_from=None, transition_time=None)`: Sets the mode for a button using a label (e.g., `'P1:A'`, `'P2:B'`).

- `start_attract_mode(self, pattern_queue)`: Starts the attract mode with a queue of patterns.
  - `pattern_queue`: A list of tuples, each containing a pattern name and a dictionary of parameters.
    - Example: `[('left_to_right', {'color_on': RGBl(...), 'color_off': RGBl(...), 'delay': 0.05}), ...]`

- `stop_attract_mode(self)`: Stops the attract mode.

- `attract_mode_active(self)`: returns True if acctract mode is active

- `write_to_display(self)`: Writes the current LED state to the display via the serial port.

- `stop(self)`: Stops the refresh loop, halting the updating of LED colors.

#### **Attract Mode Patterns:**

The attract mode supports several built-in patterns with directions:

- `'linear'`
  - `'left_to_right'`
  - `'right_to_left'`
  - `'top_to_bottom'`
  - `'bottom_to_top'`
- `'radial'`
  - `'clockwise'`
  - `'anticlockwise'`
- `'circular'`
  - `'outward'`
  - `'inward'`

Each pattern method accepts parameters:

- `direction`: a diretion tht is valid for the pattern
- `color_on`: The color to set LEDs to during activation.
- `color_off`: The color to set LEDs to during reset (default is off).
- `delay`: Delay between steps in the pattern (controls speed).

#### **Additional Features:**

- **Color Calculations**: The class handles color blending and transitioning for modes like fade and sweep.
- **Threading for Refresh and Attract Mode**: The display and attract mode are updated in separate threads to maintain real-time responsiveness.
- **Pattern Queue**: Allows sequencing multiple patterns in the attract mode, with customizable parameters for each.

### Matrix LED Control

The `LedMatrix` class is designed to control an LED matrix display. It supports both static images and animated GIFs, and allows for flexible control over color orders and display sizes. The class can handle image cropping, rescaling, and pixel blending for smooth transitions.

#### Example:

```python
from pixel_multiverse import LedMatrix, RGBl, COLOR_ORDER_RGB, DISPLAY_GALACTIC_UNICORN

# Initialize a Galactic Unicorn display with RGB color order
matrix = LedMatrix(
    display=DISPLAY_GALACTIC_UNICORN,
    serial_port_path="/dev/ttyACM0",
    color_order=COLOR_ORDER_RGB
)

# Display a static image
matrix.display_image("path/to/image.png", rescale=True, brightness=150)

# Stop the display when done
matrix.stop()
```

#### **Class Initialization:**

```python
matrix = LedMatrix(
    display=DISPLAY_GALACTIC_UNICORN,
    serial_port_path="/dev/unicorn",
    color_order=COLOR_ORDER_RGB,
    compress=False
)
```

- `display`: Type of display (e.g., `DISPLAY_GALACTIC_UNICORN`, `DISPLAY_INTERSTATE75_128x32`).
- `serial_port_path`: Path to the serial port.
- `color_order`: Tuple defining the order of color channels (e.g., RGB, BGR).
- `compress`: If `True`, the data is compressed before sending to the display.

#### **Methods:**

- `display_image(self, image_path, rescale=False, background_color=None, brightness=127)`: Displays a static image or an animated GIF on the LED matrix.
  - `image_path`: Path to the image file.
  - `rescale`: Rescales the image to fit the display dimensions if `True`.
  - `background_color`: Background color for transparent areas (optional).
  - `brightness`: Brightness level.

- `display_text(self, message, brightness)`: Displays a text message on the LED matrix.
  - `message`: The text message to display.
  - `brightness`: Brightness level.

- `stop(self)`: Stops any ongoing display and halts updates to the LED matrix.

- `write_to_display(self)`: Sends the contents of the display buffer to the LED matrix via the serial port.

#### **Additional Features:**

- **Image Rescaling and Cropping**: Automatically rescale and crop images to fit the display.
- **Animated GIF Support**: Plays animated GIFs asynchronously.
- **Custom Color Orders**: Supports different color channel orders for compatibility with various hardware.

## examples.py

**Note:** `/dev/unicorn` is a custom serial port mapping. Replace it with your own USB connection path, usually `/dev/ttyACM0` or `/dev/ttyACM1`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

### **Summary of Updates:**

- **Attract Mode**: Added explanation and examples for the new attract mode feature in `PlasmaButtons`, including how to use the pattern queue and customize patterns with parameters like `color_on`, `color_off`, and `delay`.
- **Updated Examples**: Provided updated code snippets that demonstrate the new features, ensuring users can quickly understand how to implement them.
- **Method Descriptions**: Included the new methods (`start_attract_mode`, `stop_attract_mode`) and updated existing method descriptions to reflect the latest functionality.
- **Pattern Details**: Added a section that lists available patterns and explains how to customize them.
