import time
import serial

class PlasmaButtons:
    PREFIX = b"multiverse:data"

    def __init__(self, num_leds, serial_port_path):
        """
        Initialize the PlasmaButtons class.
        
        :param num_leds: The number of LEDs to control.
        :param serial_port_path: The path to the serial port.
        """
        # Initialize the button_leds byte array with 0's, ensuring all values are zeroed
        self.button_leds = bytearray([0] * (num_leds * 4))
        # Store the serial port path
        self.serial_port_path = serial_port_path

    def update_led(self, led_number, rgbl):
        """
        Update the button_leds array at the position corresponding to led_number
        with the values from the rgbl list.

        :param led_number: The index of the LED to update
        :param rgbl: A list of 4 values (R, G, B, L) to set at the position
        """
        start_index = led_number * 4
        for i in range(4):
            self.button_leds[start_index + i] = rgbl[i]

    def update_leds(self):
        """
        Send the button_leds byte array, prefixed with "multiverse:data", to the specified serial port.
        """
        # Combine the prefix and button_leds data
        data_to_send = self.PREFIX + self.button_leds

        # Open the serial port and send the data
        try:
            with serial.Serial(self.serial_port_path, baudrate=9600, timeout=1) as ser:
                ser.write(data_to_send)
                print(f"Data sent to {self.serial_port_path}")
        except serial.SerialException as e:
            print(f"Error opening serial port {self.serial_port_path}: {e}")

    def __str__(self):
        return str(list(self.button_leds))


# Example usage:
num_leds = 128  # We have 128 LEDs
serial_port_path = "/dev/ttyACM0"  # Define the serial port path

# Initialize the PlasmaButtons object with the serial port path
plasma_buttons = PlasmaButtons(num_leds, serial_port_path)

# Define the RGBl value to set
rgbl_values = [255, 0, 0, 64]

# Loop continuously through all 128 LEDs
while True:
    for i in range(num_leds):  # Loop through all 128 LEDs
        # Set the current position to rgbl_values
        plasma_buttons.update_led(i, rgbl_values)
        
        # Send the data to the serial port
        plasma_buttons.update_leds()
        
        # If this is not the first position, reset the previous position to 0's
        if i > 0:
            plasma_buttons.update_led(i - 1, [0, 0, 0, 0])
        else:
            # Reset the last LED in the previous cycle to 0's when starting a new cycle
            plasma_buttons.update_led(num_leds - 1, [0, 0, 0, 0])
        
        # Short delay for visualization purposes
        time.sleep(0.5)

