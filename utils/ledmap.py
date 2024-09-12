# tool to calculate leds based on button coordinates based on the Picade MAX.
# All you need to do is check how you wired your plasma buttons and change the button number in the
# dictionaries below. The coordinates are based on the actual button position and the button function is put in the
# comment behind the coordinates.
# See example_layout.png for an example numbering. Button 0 is the button connected to the plasma connector on the
# input board, button 1 the one connected to button 1, and so on.

button_positions_30_2 = {
    0: (66, 15), # P2 Y
    1: (65, 8),  # P2 R1
    2: (60, 17), # P2 X
    3: (59, 10), # P2 Select
    4: (54, 19), # P2 B
    5: (53, 12), # P2 L1
    6: (53, 26)  # P2 A
}
button_positions_30_1 = {
    7: (29, 19),  # P1 Y
    8: (31, 13),  # P1 R1
    9: (23, 19),  # P1 X
    10: (25, 13), # P1 Select
    11: (17, 19), # P1 B
    12: (19, 13), # P1 L1
    13: (14, 25)  # P1 A
}

button_positions_24 = {
    14: (2, 3),  # P1 Start
    15: (11, 3), # P1 L2
    16: (17, 3), # P1 L3
    17: (23, 3), # P1 R3
    18: (29, 3), # P1 R2
    19: (41, 3), # P2 Start
    20: (50, 3), # P2 L2
    21: (56, 3), # P2 L3
    22: (62, 3), # P2 R3
    23: (68, 3)  # P2 L2
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


