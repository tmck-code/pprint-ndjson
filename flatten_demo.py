#!/usr/bin/env python3

import io
import json
import sys
from collections.abc import Generator
from typing import Any

from pygments import highlight
from pygments.formatters import Terminal256Formatter

from laser_prynter.pp import ColumnStyle, ColumnTabulateLexer, flatten


def parse_stream(stream: io.TextIOBase) -> Generator[list, None, None]:
    for line in stream:
        try:
            yield list(map(str, flatten(json.loads(line.strip())).values()))
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON line: {line}", file=sys.stderr)


def open_stream() -> Any:
    if len(sys.argv) > 1:
        return open(sys.argv[1], 'r')
    else:
        return sys.stdin


for parsed in parse_stream(open_stream()):
    print(
        highlight(
            '\t'.join(parsed),
            ColumnTabulateLexer(),
            Terminal256Formatter(style=ColumnStyle),
        ).strip()
    )
