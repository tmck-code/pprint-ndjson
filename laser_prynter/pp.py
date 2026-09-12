import json
import random
import sys
from collections.abc import Generator, Iterator
from dataclasses import asdict, is_dataclass
from datetime import datetime
from itertools import chain
from types import FunctionType
from typing import Any, ClassVar, NamedTuple, TextIO, cast

from pygments import console, highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexer import Lexer
from pygments.lexers import JsonLexer
from pygments.style import Style
from pygments.styles import get_all_styles, get_style_by_name
from pygments.token import Token

STYLES = (
    'dracula', 'fruity', 'gruvbox-dark', 'gruvbox-light', 'lightbulb', 'material', 'native',
    'one-dark', 'perldoc', 'tango',
)
DEFAULT_STYLE = 'dracula'

# disable printing by setting `pp.enabled = False`
enabled = True


class ColumnStyle(Style):
    styles: ClassVar[dict[Token, str]] = {
        Token.Column.Zero: 'ansired bold',
        Token.Column.One: 'ansigreen',
        Token.Column.Two: 'ansiblue',
        Token.Column.Three: 'ansiyellow',
        Token.Column.Four: 'ansimagenta',
        Token.Column.Five: 'ansicyan',
        Token.Column.Six: 'ansibrightred',
        Token.Column.Seven: 'ansibrightgreen',
        Token.Column.Eight: 'ansibrightblue',
        Token.Column.Nine: 'ansibrightyellow',
        Token.Column.Ten: 'ansibrightmagenta',
    }


class ColumnTabulateLexer(Lexer):
    column_tokens: ClassVar = [
        Token.Column.Zero,
        Token.Column.One,
        Token.Column.Two,
        Token.Column.Three,
        Token.Column.Four,
        Token.Column.Five,
        Token.Column.Six,
        Token.Column.Seven,
        Token.Column.Eight,
        Token.Column.Nine,
        Token.Column.Ten,
    ]

    def get_tokens_unprocessed(self, text: str) -> Generator[tuple[int, Token, str], None, None]:
        pos = 0
        for line in text.splitlines(keepends=True):
            parts = line.split('\t')
            nParts = len(parts)

            for col_idx, part in enumerate(parts):
                if not part:
                    yield pos, Token.Text, ''
                    pos += len(part)
                    continue

                tok_type = self.column_tokens[col_idx % len(self.column_tokens)]
                if col_idx < nParts - 1:
                    part += '\t'
                yield pos, tok_type, part
                pos += len(part)


def flatten(d: dict, prefix: str = "") -> dict:
    def pairs(d: dict[str, Any], prefix: str) -> Iterator[tuple[str, Any]]:
        return chain.from_iterable(
            pairs(v, f'{prefix}{k}.') if isinstance(v, dict) else [(f'{prefix}{k}', v)]
            for k, v in d.items()
        )

    return dict(pairs(d, prefix))


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
    for k, v in d.items():
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

def random_style() -> str:
    'return a random style name'
    return random.choice(STYLES)

def ps(s: str, style: str='yellow', random_style: bool=False) -> str|Any:
    'add color to a string'
    if random_style:
        style = random.choice(console.dark_colors + console.light_colors)
    return console.colorize(style, s)

# Main pretty-printing functions ----------------

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

def ppj(j: str, indent: int|None=None, style: str='dracula', random_style: bool=False, **kwargs: Any) -> None:
    'pretty-print a JSON string'
    ppd(_normalise(json.loads(j)), indent=indent, style=style, random_style=random_style)

def pps(s: str, style: str='yellow', random_style: bool=False) -> None:
    'pretty-print a string'
    _print(ps(s, style=style, random_style=random_style))


def demo(all_styles: bool=False, **kwargs: Any) -> None:
    'demonstrate pretty-printing colours'

    print('selected styles:')
    for s in sorted(STYLES):
        ppd({'message': {'Hello': 'World', 'The answer is': 42}, 'style': s}, style=s, **kwargs)

    if all_styles:
        print('\nall other styles:')
        for s in sorted(set(get_all_styles()) - set(STYLES)):
            ppd({'message': {'Hello': 'World', 'The answer is': 42}, 'style': s}, style=s, **kwargs)

