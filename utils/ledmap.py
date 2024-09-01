# tool to calculate leds based on button coordinates

button_positions_30_2 = {
    0: (66, 15),
    1: (65, 8),
    2: (60, 17),
    3: (59, 10),
    4: (54, 19),
    5: (53, 12),
    6: (53, 26)
}
button_positions_30_1 = {
    7: (29, 19),
    8: (31, 13),
    9: (23, 19),
    10: (25, 13),
    11: (17, 19),
    12: (19, 13),
    13: (14, 25)
}

button_positions_24 = {
    14: (2, 3),
    15: (11, 3),
    16: (17, 3),
    17: (23, 3),
    18: (29, 3),
    19: (41, 3),
    20: (50, 3),
    21: (56, 3),
    22: (62, 3),
    23: (68, 3)
}

# Create the mapping
led_map = {}
for button_num, (xc, yc) in button_positions_30_2.items():
    led_map[(xc + 2, yc - 1)] = button_num * 4 + 0
    led_map[(xc - 1, yc - 3)] = button_num * 4 + 1
    led_map[(xc - 3, yc)] = button_num * 4 + 2
    led_map[(xc, yc + 2)] = button_num * 4 + 3

for button_num, (xc, yc) in button_positions_30_1.items():
    led_map[(xc + 2, yc )] = button_num * 4 + 0
    led_map[(xc , yc - 3)] = button_num * 4 + 1
    led_map[(xc - 3, yc - 1)] = button_num * 4 + 2
    led_map[(xc - 1 , yc + 2)] = button_num * 4 + 3

for button_num, (xc, yc) in button_positions_24.items():
    led_map[(xc + 2, yc)] = button_num * 4 + 0
    led_map[(xc, yc - 2)] = button_num * 4 + 1
    led_map[(xc - 2, yc)] = button_num * 4 + 2
    led_map[(xc, yc + 2)] = button_num * 4 + 3
# Example to print the map
print(led_map)


