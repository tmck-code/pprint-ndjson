import json
import random
import sys
from collections.abc import Iterator
from dataclasses import asdict, is_dataclass
from datetime import datetime
from types import FunctionType
from typing import Any, NamedTuple, TextIO, cast

from pygments import console, highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer
from pygments.styles import get_all_styles, get_style_by_name

STYLES = (
    'dracula', 'fruity', 'gruvbox-dark', 'gruvbox-light', 'lightbulb', 'material', 'native',
    'one-dark', 'perldoc', 'tango',
)
DEFAULT_STYLE = 'dracula'

# disable printing by setting `pp.enabled = False`
enabled = True

def _output_is_redirected(stream: TextIO = sys.stdout) -> bool:
    'detect if output is being redirected to a file or pipe'
    return stream.isatty() is False

def _print(s: str, **kwargs: Any) -> None:
    if enabled:
        print(s, **kwargs)

def _isnamedtuple(obj: object) -> bool:
    return isinstance(obj, tuple) and hasattr(obj, '_fields')

def _normalise_keys(d: dict) -> Iterator[tuple[str, Any]]:
    'norlimalise dict keys for JSON by stringifying'
    for k,v in d.items():
        if not isinstance(k, str):
            yield str(k), _normalise(v)
        else:
            yield k, _normalise(v)

def _normalise(obj: object) -> Any:
    'step through obj and normalise namedtuples to dicts'
    if isinstance(obj, dict):
        return dict(_normalise_keys(obj))
    if isinstance(obj, list):
        return [_normalise(i) for i in obj]
    if _isnamedtuple(obj):
        return cast(NamedTuple, obj)._asdict()
    return obj

def _json_default(obj: object) -> Any:
    'Default JSON serializer, supports most main class types'
    if   isinstance(obj, str):          return obj # str
    elif isinstance(obj, list):         return [_json_default(i) for i in obj]
    elif is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj) # dataclass
    elif isinstance(obj, datetime):     return obj.isoformat() # datetime
    elif isinstance(obj, FunctionType): return f'{obj.__name__}()' # function
    elif hasattr(obj, '__slots__'):     return {k: getattr(obj, k) for k in obj.__slots__} # class with slots.
    elif hasattr(obj, '__name__'):      return obj.__name__ # function/class name
    elif hasattr(obj, '__dict__'):      return obj.__dict__ # class
    return str(obj)

def ppd(d_obj: Any, indent: int|None=None, style: str|None='dracula', random_style: bool=False, **kwargs: Any) -> None:
    'pretty-print a dict'
    d = _normalise(d_obj) # convert any namedtuples to dicts

    if _output_is_redirected(cast(TextIO, kwargs.get('file', sys.stdout))):
        style = None
    elif random_style:
        style = random.choice(STYLES)
    code = json.dumps(d, indent=indent, default=_json_default)

    if style is None:
        _print(code, **kwargs)
    else:
        _print(
            highlight(
                code      = code,
                lexer     = JsonLexer(),
                formatter = Terminal256Formatter(style=get_style_by_name(style))
            ).strip(),
            **kwargs,
        )

def random_style() -> str:
    'return a random style name'
    return random.choice(STYLES)

def ppj(j: str, indent: int|None=None, style: str='dracula', random_style: bool=False, **kwargs: Any) -> None:
    'pretty-print a JSON string'
    ppd(_normalise(json.loads(j)), indent=indent, style=style, random_style=random_style)

def ps(s: str, style: str='yellow', random_style: bool=False) -> str|Any:
    'add color to a string'
    if random_style:
        style = random.choice(console.dark_colors + console.light_colors)
    return console.colorize(style, s)

def pps(s: str, style: str='yellow', random_style: bool=False) -> None:
    'pretty-print a string'
    _print(ps(s, style=style, random_style=random_style))

def demo(all_styles: bool=False, **kwargs: Any) -> None:
    'demonstrate pretty-printing colours'

    print('selected styles:')
    for s in STYLES:
        ppd({'message': {'Hello': 'World', 'The answer is': 42}, 'style': s}, style=s, **kwargs)

    if all_styles:
        print('\nall other styles:')
        for s in set(get_all_styles()) - set(STYLES):
            ppd({'message': {'Hello': 'World', 'The answer is': 42}, 'style': s}, style=s, **kwargs)

