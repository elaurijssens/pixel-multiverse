from collections import namedtuple

# Define a NamedTuple for RGBl (Red, Green, Blue, Brightness)
RGBl = namedtuple('RGBl', ['red', 'green', 'blue', 'brightness'])

#TODO: Define standard colors (idea: use C64 palette)
C64_WHITE = RGBl(255, 255, 255, 255)
C64_CYAN = RGBl(0, 255, 255, 255)
C64_RED = RGBl(255, 0, 0, 255)
C64_GREEN = RGBl(0, 255, 0, 255)
C64_BLUE = RGBl(0, 0, 255, 255)
C64_BLACK = RGBl(0, 0, 0, 255)