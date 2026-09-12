from __future__ import annotations

import math
import os
import signal
import sys
import time
import types
from collections.abc import Iterator
from random import randint
from types import TracebackType
from typing import Self

from laser_prynter.colour.c import RGBColour
from laser_prynter.colour.gradient import RGBGradient


def _print_to_terminal(s: str) -> None:
    'Helper function to perform ANSI escape sequences.'
    sys.stderr.write(s)
    sys.stderr.flush()


def _get_terminal_size() -> tuple[int, int]:
    '''
    Get terminal size (width, height)
    - first try STDERR (as STDOUT is more likely to be redirected),
    - then try STDOUT
    - if both fail, return default (80, 24).
    '''
    try:
        size = os.get_terminal_size(2)
    except OSError:
        try:
            size = os.get_terminal_size(1)
        except OSError:
            return (80, 24)
    return (size.columns, size.lines)


DEFAULT_C1, DEFAULT_C2 = RGBColour(240, 50, 0), RGBColour(10, 220, 0)


class PBar:
    def __init__(self, total: int, c1: RGBColour = DEFAULT_C1, c2: RGBColour = DEFAULT_C2):
        self.t = total
        self.w, self.h = _get_terminal_size()
        self.x_pos, self.i = 0, 0
        self.start_time = time.time()

        self.g = RGBGradient(start=c1, end=c2, steps=self.w)

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGWINCH, self.sigwinch_handler)

    def sigint_handler(self, _signum: int, _frame: types.FrameType | None) -> None:
        self._reset_terminal()
        sys.exit(0)

    def sigwinch_handler(self, _signum: int, _frame: types.FrameType | None) -> None:
        self.handle_resize()

    def handle_resize(self) -> None:
        i, h = self.i, self.h
        self.w, self.h = _get_terminal_size()

        _print_to_terminal(
            f'\x1b[{h - 1};0H\x1b[2K'  # move to old info line & clear it
            f'\x1b[{h};0H\x1b[2K'  # move to old bar line & clear it
            f'\x1b[{self.h - 1};0H\x1b[2K'  # move to info line & clear it
            f'\x1b[{self.h};0H\x1b[2K'  # move to bar line & clear it
            f'\x1b[0;{self.h - 2}r'  # set scrolling region, reserve 2 lines at bottom
            f'\x1b[{self.h - 2};0H'  # move cursor to last line of scrollable area
        )

        self.g = RGBGradient(start=self.g.start, end=self.g.end, steps=self.w)
        self._initial_bar()

        self.i, self.x_pos = 0, 0

        if i > 0:
            self.update(i)
        else:
            self._print_info()

    @staticmethod
    def randgrad() -> tuple[RGBColour, RGBColour]:
        'Generate a random gradient colour pair.'
        return (
            RGBColour(randint(0, 255), randint(0, 255), randint(0, 255)),
            RGBColour(randint(0, 255), randint(0, 255), randint(0, 255)),
        )

    def _pbar_terminal_x_at(self, n: int) -> int:
        'Where 0 <= n <= self.t, return the corresponding terminal position the progress bar.'

        if 0 <= n <= self.t:
            return math.ceil((n / self.t) * self.w)
        else:
            return self.w

    def _pbar_colour_at(self, n: int) -> RGBColour:
        'Where 0 <= n <= self.t, return the corresponding colour for the progress bar.'
        return self.g.sequence[n] if n < self.w else self.g.end

    def _pbar(self) -> Iterator[tuple[tuple[int, RGBColour]]]:
        for x in range(self.w):
            yield ((x, self.g.sequence[x]),)

    def __iter__(self) -> PBar:
        return self

    @staticmethod
    def _true_colour(rgbColour: RGBColour) -> str:
        return f'\x1b[48;2;{rgbColour.r};{rgbColour.g};{rgbColour.b}m'

    @staticmethod
    def _format_time(seconds: float) -> str:
        'Format seconds into human-readable time string.'

        if seconds < 60:
            isec, fsec = divmod(seconds, 1)
            return f'{int(isec)}.{int(fsec * 100):02d}'
        elif seconds < 3600:
            isec, fsec = divmod(seconds, 60)
            return f'{int(isec)}:{fsec:05.2f}'
        else:
            hours, rem = divmod(seconds, 3600)
            mins, secs = divmod(rem, 60)
            return f'{int(hours)}:{int(mins)}:{secs:05.2f}'

    def _print_info(self) -> None:
        'Print progress info in the line above the bar.'

        elapsed = time.time() - self.start_time

        if self.i == 0:
            eta_str = '??:??'
        else:
            eta_str = self._format_time((elapsed / self.i) * (self.t - self.i))

        if self.t == 0:
            pct = 100.0
        else:
            pct = (self.i / self.t) * 100

        items_per_sec = self.i / max(elapsed, 0.001)
        item_info = f'[\x1b[1;32m{self.i:,d}\x1b[0m/{self.t:,d}] \x1b[1;97m{pct:.1f}%\x1b[0m'
        time_info = f'\x1b[92m+{self._format_time(elapsed)}\x1b[0m \x1b[93m-{eta_str}\x1b[0m'
        rate_info = f'\x1b[1;37m{items_per_sec:.2f} it/s\x1b[0m'

        # Clear the line and print info above the progress bar
        _print_to_terminal(
            f'\x1b[{self.h - 1};0H'  # move to line above bar
            '\x1b[2K'  # clear entire line
            f'{item_info} | {time_info} ({rate_info})'
            f'\x1b[{self.h - 2};0H'  # move cursor to last line of scrollable area
        )

    def _print_bar_char(self, s: str, colour: RGBColour, x_pos: int) -> None:
        _print_to_terminal(
            f'\x1b[{self.h};{x_pos}H'  # move to bottom line
            f'\x1b[48;2;{colour.r};{colour.g};{colour.b}m'
            f'{s}'  # the 'bar' characters
            '\x1b[0m'  # reset color
            f'\x1b[{self.h - 2};0H'  # move cursor to last line of scrollable area
        )

    def _initial_bar(self) -> None:
        'print initial bar in end color'

        for x_pos in range(self.w + 1):
            self._print_bar_char(' ', self._pbar_colour_at(self.w), x_pos)

    def update(self, n: int) -> None:
        'update the progress bar by n steps'

        target_pos = self._pbar_terminal_x_at(self.i + n)

        for pos in range(self.x_pos, target_pos + 1):
            self._print_bar_char(' ', self._pbar_colour_at(pos), pos)

        self.i += n
        self.x_pos = target_pos

        self._print_info()

    def __enter__(self) -> Self:
        self.start_time = time.time()
        _print_to_terminal(
            '\x1b[?25l'  # hide cursor
            '\n\n'  # ensure space for info line and progress bar
            f'\x1b[0;{self.h - 2}r'  # set top & bottom margins
        )
        self._initial_bar()
        self._print_info()
        return self

    @staticmethod
    def _reset_terminal() -> None:
        _w, h = _get_terminal_size()
        _print_to_terminal(
            '\x1b[?25h'  # show cursor
            f'\x1b[0;{h}r'  # reset margins
            f'\x1b[{h};0H'  # move to bottom line
            '\n'
        )

    def __exit__(self, _exc_type: type[BaseException] | None, _exc_val: BaseException | None, _exc_tb: TracebackType | None) -> None:
        self._reset_terminal()


if __name__ == '__main__':
    with PBar(100, *PBar.randgrad()) as pbar:
        for i in range(100):
            time.sleep(randint(int(0.01 * 100), int(0.1 * 100)) / 100)
            print(f'-> {i}', flush=True)
            pbar.update(1)
