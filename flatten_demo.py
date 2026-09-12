#!/usr/bin/env python3

import json
import sys
from typing import Any

from laser_prynter.pp import ppf


def open_stream() -> Any:
    if len(sys.argv) > 1:
        return open(sys.argv[1], 'r')
    else:
        return sys.stdin


for line in open_stream():
    try:
        ppf(json.loads(line.strip()))
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON line: {line}", file=sys.stderr)
