from collections import namedtuple

# Define a NamedTuple for RGBl (Red, Green, Blue, Brightness)
RGBl = namedtuple('RGBl', ['red', 'green', 'blue', 'brightness'])

# Some standard colours, taken from the Colodore palette:
C64_BLACK = RGBl(0, 0, 0, 255)
C64_DARK_GREY = RGBl(74, 74, 74, 255)
C64_GREY = RGBl(123, 123, 123, 255)
C64_LIGHT_GREY = RGBl(178, 178, 178, 255)
C64_WHITE = RGBl(255, 255, 255, 255)
C64_RED = RGBl(129, 51, 56, 255)
C64_PINK = RGBl(196, 108, 113, 255)
C64_BROWN = RGBl(85, 56, 0, 255)
C64_ORANGE = RGBl(142, 80, 41, 255)
C64_YELLOW = RGBl(237, 241, 113, 255)
C64_LIGHT_GREEN = RGBl(169, 255, 159, 255)
C64_GREEN = RGBl(86, 172, 77, 255)
C64_CYAN = RGBl(117, 206, 200, 255)
C64_LIGHT_BLUE = RGBl(112, 109, 235, 255)
C64_BLUE = RGBl(46, 44, 155, 255)
C64_PURPLE = RGBl(142, 60, 151, 255)
