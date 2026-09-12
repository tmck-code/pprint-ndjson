'This module contains functions for converting between RGB and ANSI colour codes.'

from __future__ import annotations

from random import randint
from types import MappingProxyType
from typing import Any, Literal, NamedTuple

# Valid components of an RGB tuple.
type _RGB_COMPONENT = Literal['r', 'g', 'b']
_RGB_COMPONENTS: tuple[_RGB_COMPONENT, _RGB_COMPONENT, _RGB_COMPONENT] = ('r', 'g', 'b')

# Multipliers for each component of the RGB tuple in the ANSI colour code formula.
_RGB_COMPONENT_MULTIPLIER: MappingProxyType[_RGB_COMPONENT, int] = MappingProxyType({
    'r': 36,
    'g': 6,
    'b': 1,
})


# component _must_ be one of 'r', 'g', or 'b'
def _ansi_to_rgb_component(n: int, component: _RGB_COMPONENT) -> int:
    '''
    Reverses the rgb_to_ansi formula to calculate a specific component of the RGB tuple
    given an ANSI colour code, and the component to calculate.

    n = 16 + (36 * r) + (6 * g) + (1 * b)
    '''
    if n < 16 or n >= 232:
        return 0
        # raise ValueError(f'Invalid ANSI colour code for RGB conversion: {n}')

    i = (
        (n - 16)  # 16 is the base value
        # divide by 36/6/1
        // _RGB_COMPONENT_MULTIPLIER[component]
        % 6  # each value can be 0-5
    )
    if i == 0:
        return 0
    # I have nfi what this does, but it is crucial
    return (14135 + (10280 * i)) // 256


def ansi_to_rgb(n: int) -> tuple[int, int, int]:
    'Reverses the rgb_to_ansi formula to calculate an RGB tuple given an ANSI colour code.'
    return (
        _ansi_to_rgb_component(n, 'r'),
        _ansi_to_rgb_component(n, 'g'),
        _ansi_to_rgb_component(n, 'b'),
    )


def cube_coords_to_ansi(r: int, g: int, b: int) -> int:
    ''' '
    The golden formula. Via https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit:
      0-  7:  standard colors (as in ESC [ 30–37 m)
      8- 15:  high intensity colors (as in ESC [ 90–97 m)
     16-231:  6 × 6 × 6 cube (216 colors): 16 + 36 × r + 6 × g + b (0 ≤ r, g, b ≤ 5)
    232-255:  grayscale from dark to light in 24 steps
    '''
    return 16 + (
        r * _RGB_COMPONENT_MULTIPLIER['r'] + g * _RGB_COMPONENT_MULTIPLIER['g'] + b * _RGB_COMPONENT_MULTIPLIER['b']
    )


# Valid (supported) ANSI styles.
type _ANSI_STYLES = Literal['fg', 'bg']
_ANSI_ESCAPE_CODES: MappingProxyType[_ANSI_STYLES, str] = MappingProxyType({
    'fg': '38;5',
    'bg': '48;5',
})

RESET: str = '\033[0m'


class ANSIColour(NamedTuple):
    'Represents a terminal colour in both RGB and ANSI formats.'

    ansi_n: int
    rgb: tuple[int, int, int]

    def __escape(self, escape: str) -> str:
        'Returns an ANSI escape code for setting the colour.'
        return f'\033[{escape};{self.ansi_n}m'

    def escape_code(self, style: _ANSI_STYLES) -> str:
        'Returns the ANSI escape code for setting the colour.'
        return self.__escape(_ANSI_ESCAPE_CODES[style])

    def colorise(self, text: Any, style: _ANSI_STYLES = 'bg') -> str:
        'Returns the text with the colour applied.'
        return f'{self.escape_code(style)}{text}{RESET}'


def from_cube_coords(r: int, g: int, b: int) -> ANSIColour:
    'Creates an ANSIColour from an RGB tuple.'
    ansi = cube_coords_to_ansi(r, g, b)
    return ANSIColour(rgb=ansi_to_rgb(ansi), ansi_n=ansi)


def from_ansi(n: int) -> ANSIColour:
    'Creates an ANSIColour from an ANSI colour code.'
    return ANSIColour(ansi_n=n, rgb=ansi_to_rgb(n))


class RGBColour(NamedTuple):
    r: int
    g: int
    b: int

    @staticmethod
    def randgrad() -> tuple[RGBColour, RGBColour]:
        rgb1 = RGBColour(
            randint(0, 255),
            randint(0, 255),
            randint(0, 255),
        )
        rgb2 = RGBColour(
            (rgb1.r + (255 + (255 // 2))) % 255,
            (rgb1.g + (255 + (255 // 2))) % 255,
            (rgb1.b + (255 + (255 // 2))) % 255,
        )
        return (rgb1, rgb2)
