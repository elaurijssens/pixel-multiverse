from ledmultiverse import PlasmaButtons, RGBl
import time

# Define a button map
button_map = {'P1:START': 14, 'P1:A': 13, 'P1:B': 11, 'P1:X': 9, 'P1:Y': 7, 'P1:L1': 12, 'P1:L2': 15, 'P1:R1': 8,
              'P1:R2': 18, 'P1:SELECT': 10, 'P1:L3': 16, 'P1:R3': 17, 'P1:HOTKEY': 24, 'P1:X1': 29, 'P1:X2': 26,
              'P2:START': 19, 'P2:A': 6, 'P2:B': 4, 'P2:X': 2, 'P2:Y': 0, 'P2:L1': 5, 'P2:L2': 20, 'P2:R1': 1,
              'P2:R2': 23, 'P2:SELECT': 3, 'P2:L3': 21, 'P2:R3': 22, 'P2:HOTKEY': 25, 'P2:X1': 28, 'P2:X2': 27}

# Define a coordinate map
coord_map = {
    (68, 14): 0, (65, 12): 1, (63, 15): 2, (66, 17): 3, (67, 7): 4, (64, 5): 5, (62, 8): 6, (65, 10): 7, (62, 16): 8,
    (59, 14): 9, (57, 17): 10, (60, 19): 11, (61, 9): 12, (58, 7): 13, (56, 10): 14, (59, 12): 15, (56, 18): 16,
    (53, 16): 17, (51, 19): 18, (54, 21): 19, (55, 11): 20, (52, 9): 21, (50, 12): 22, (53, 14): 23, (55, 25): 24,
    (52, 23): 25, (50, 26): 26, (53, 28): 27, (31, 19): 28, (29, 16): 29, (26, 18): 30, (28, 21): 31, (33, 13): 32,
    (31, 10): 33, (28, 12): 34, (30, 15): 35, (25, 19): 36, (23, 16): 37, (20, 18): 38, (22, 21): 39, (27, 13): 40,
    (25, 10): 41, (22, 12): 42, (24, 15): 43, (19, 19): 44, (17, 16): 45, (14, 18): 46, (16, 21): 47, (21, 13): 48,
    (19, 10): 49, (16, 12): 50, (18, 15): 51, (16, 25): 52, (14, 22): 53, (11, 24): 54, (13, 27): 55, (4, 3): 56,
    (2, 1): 57, (0, 3): 58, (2, 5): 59, (13, 3): 60, (11, 1): 61, (9, 3): 62, (11, 5): 63, (19, 3): 64, (17, 1): 65,
    (15, 3): 66, (17, 5): 67, (25, 3): 68, (23, 1): 69, (21, 3): 70, (23, 5): 71, (31, 3): 72, (29, 1): 73,
    (27, 3): 74, (29, 5): 75, (43, 3): 76, (41, 1): 77, (39, 3): 78, (41, 5): 79, (52, 3): 80, (50, 1): 81,
    (48, 3): 82, (50, 5): 83, (58, 3): 84, (56, 1): 85, (54, 3): 86, (56, 5): 87, (64, 3): 88, (62, 1): 89,
    (60, 3): 90, (62, 5): 91, (70, 3): 92, (68, 1): 93, (66, 3): 94, (68, 5): 95
}

num_leds = 128
refresh_rate = 60
serial_port = "/dev/plasmabuttons"

# Initialize the PlasmaButtons object with the button map and coordinate map
plasma_buttons = PlasmaButtons(num_leds, serial_port, refresh_rate, button_map, coord_map)


# Set LED modes using button labels
plasma_buttons.set_button_mode(0, 'blink', color_to=RGBl(0, 63, 0, 15), color_from=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(1, 'blink', color_to=RGBl(0, 0, 63, 15), color_from=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(2, 'blink', color_to=RGBl(63, 0, 0, 15), color_from=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(3, 'blink', color_to=RGBl(63, 63, 0, 15), color_from=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(4, 'blink', color_to=RGBl(0, 63, 63, 15), color_from=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(5, 'blink', color_to=RGBl(63, 0, 63, 15), color_from=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(6, 'blink', color_to=RGBl(63, 63, 63, 15), color_from=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(7, 'blink', color_from=RGBl(0, 63, 0, 15), color_to=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(8, 'blink', color_from=RGBl(0, 0, 63, 15), color_to=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(9, 'blink', color_from=RGBl(63, 0, 0, 15), color_to=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(10, 'blink', color_from=RGBl(63, 63, 0, 15), color_to=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(11, 'blink', color_from=RGBl(0, 63, 63, 15), color_to=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(12, 'blink', color_from=RGBl(63, 0, 63, 15), color_to=RGBl(0, 0, 0, 0), transition_time=0.25)
plasma_buttons.set_button_mode(13, 'blink', color_from=RGBl(63, 63, 63, 15), color_to=RGBl(0, 0, 0, 0), transition_time=0.25)

time.sleep(3)

plasma_buttons.set_button_mode(0, 'normal', color_to=RGBl(0, 63, 0, 15))
plasma_buttons.set_button_mode(1, 'normal', color_to=RGBl(0, 0, 63, 15))
plasma_buttons.set_button_mode(2, 'normal', color_to=RGBl(63, 0, 0, 15))
plasma_buttons.set_button_mode(3, 'normal', color_to=RGBl(63, 63, 0, 15))
plasma_buttons.set_button_mode(4, 'normal', color_to=RGBl(0, 63, 63, 15))
plasma_buttons.set_button_mode(5, 'normal', color_to=RGBl(63, 0, 63, 15))
plasma_buttons.set_button_mode(6, 'normal', color_to=RGBl(63, 63, 63, 15))
plasma_buttons.set_button_mode(7, 'normal', color_to=RGBl(0, 63, 0, 15))
plasma_buttons.set_button_mode(8, 'normal', color_to=RGBl(0, 0, 63, 15))
plasma_buttons.set_button_mode(9, 'normal', color_to=RGBl(63, 0, 0, 15))
plasma_buttons.set_button_mode(10, 'normal', color_to=RGBl(63, 63, 0, 15))
plasma_buttons.set_button_mode(11, 'normal', color_to=RGBl(0, 63, 63, 15))
plasma_buttons.set_button_mode(12, 'normal', color_to=RGBl(63, 0, 63, 15))
plasma_buttons.set_button_mode(13, 'normal', color_to=RGBl(63, 63, 63, 15))

time.sleep(3)

plasma_buttons.set_button_mode(0, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(1, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(2, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(3, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(4, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(5, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(6, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(7, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(8, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(9, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(10, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(11, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(12, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)
plasma_buttons.set_button_mode(13, 'fade', color_to=RGBl(10, 10, 10, 5), transition_time=2)

# Allow the program to run for a while before stopping (example)
time.sleep(5)

x_values = sorted(set(coord[0] for coord in coord_map.keys()))
y_values = sorted(set(coord[1] for coord in coord_map.keys()))

# Calculate the full range of x values, including those without LEDs
min_x, max_x = min(x_values), max(x_values)+1
min_y, max_y = min(y_values), max(y_values)+1

for _ in range(1, 5):
    for column in range (min_x, max_x):
        for row in range (min_y, max_y):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(31, 31, 31, 5))
        time.sleep(0.01)
    for column in range(min_x, max_x):
        for row in range (min_y, max_y):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(15, 15, 0, 5))
        time.sleep(0.01)
    time.sleep(0.2)

for _ in range(1, 10):
    for row in range (min_y, max_y):
        for column in range (min_x, max_x):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(31, 31, 31, 5))
        time.sleep(0.01)
    for row in range (min_y, max_y):
        for column in range (min_x, max_x):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(0, 15, 15, 5))
        time.sleep(0.01)
    time.sleep(0.2)

for _ in range(1, 5):
    for column in range (max_x, min_x, -1):
        for row in range (min_y, max_y):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(31, 31, 31, 5))
        time.sleep(0.01)
    for column in range(max_x, min_x, -1):
        for row in range (min_y, max_y):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(15, 0, 15, 5))
        time.sleep(0.01)
    time.sleep(0.2)

for _ in range(1, 10):
    for row in range (max_y, min_y, -1):
        for column in range (min_x, max_x):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(31, 31, 31, 5))
        time.sleep(0.01)
    for row in range (max_y, min_y, -1):
        for column in range (min_x, max_x):
            plasma_buttons.set_led_mode_by_coord(coord=(column, row),mode="normal", color_to=RGBl(0, 0, 0, 5))
        time.sleep(0.01)
    time.sleep(0.2)

plasma_buttons.set_button_mode_by_label(button_label="P1:A", mode="fade sweep", color_from=RGBl(0,63,63,15),
                                        color_to=RGBl(0,0,63,15), transition_time=0.5)
plasma_buttons.set_button_mode_by_label(button_label="P1:B", mode="normal", color_to=RGBl(15,15,63,15))
plasma_buttons.set_button_mode_by_label(button_label="P1:X", mode="normal", color_to=RGBl(15,15,63,15))
plasma_buttons.set_button_mode_by_label(button_label="P1:Y", mode="normal", color_to=RGBl(15,15,63,15))
plasma_buttons.set_button_mode_by_label(button_label="P1:L1", mode="normal", color_to=RGBl(15,15,63,15))
plasma_buttons.set_button_mode_by_label(button_label="P1:R1", mode="normal", color_to=RGBl(15,15,63,15))
plasma_buttons.set_button_mode_by_label(button_label="P1:SELECT", mode="blink", color_from=RGBl(31,31,63,15),
                                        color_to=RGBl(5,5,63,15),transition_time=0.5)

plasma_buttons.set_button_mode_by_label(button_label="P2:A", mode="fade sweep", color_from=RGBl(63,63,0,15),
                                        color_to=RGBl(63,0,0,15), transition_time=0.5)
plasma_buttons.set_button_mode_by_label(button_label="P2:B", mode="normal", color_to=RGBl(63,15,15,15))
plasma_buttons.set_button_mode_by_label(button_label="P2:X", mode="normal", color_to=RGBl(63,15,15,15))
plasma_buttons.set_button_mode_by_label(button_label="P2:Y", mode="normal", color_to=RGBl(63,15,15,15))
plasma_buttons.set_button_mode_by_label(button_label="P2:L1", mode="normal", color_to=RGBl(63,15,15,15))
plasma_buttons.set_button_mode_by_label(button_label="P2:R1", mode="normal", color_to=RGBl(63,15,15,15))
plasma_buttons.set_button_mode_by_label(button_label="P2:SELECT", mode="blink", color_from=RGBl(63,31,31,15),
                                        color_to=RGBl(63,5,5,15),transition_time=0.5)

time.sleep(10)

plasma_buttons.set_button_mode(0, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(1, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(2, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(3, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(4, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(5, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(6, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(7, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(8, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(9, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(10, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(11, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(12, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)
plasma_buttons.set_button_mode(13, 'fade', color_to=RGBl(0, 0, 0, 0), transition_time=2)

time.sleep(5)

plasma_buttons.stop()