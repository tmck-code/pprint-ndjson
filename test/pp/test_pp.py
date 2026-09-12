import unittest
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from io import StringIO

from laser_prynter import pp


class TestJSONDefault(unittest.TestCase):
    def test_str(self) -> None:
        'Print a dict as JSON'

        s = StringIO()
        pp.ppd({'a': 'b'}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"a": "b"}')

    def test_dataclass(self) -> None:
        'Print a dataclass as JSON'

        s = StringIO()
        @dataclass
        class A:
            a: str

        pp.ppd(A('b'), indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"a": "b"}')

    def test_datetime(self) -> None:
        'Print a datetime as JSON'

        s = StringIO()
        pp.ppd({'a': datetime(2021, 1, 1, 12, 34, 56)}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"a": "2021-01-01T12:34:56"}')

    def test_class(self) -> None:
        'Print a class instance as JSON'

        s = StringIO()
        class A:
            def __init__(self, a: str) -> None:
                self.a = a

        pp.ppd({'a': A('b')}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"a": {"a": "b"}}')

    def test_function(self) -> None:
        'Print a function as JSON'

        s = StringIO()
        def a() -> None: pass

        pp.ppd({'a': a}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"a": "a()"}')

    def test_slots(self) -> None:
        'Print a class with __slots__ as JSON'

        s = StringIO()
        class A:
            __slots__ = ['a']
            def __init__(self, a: str) -> None:
                self.a = a
        pp.ppd({'a': A('b')}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"a": {"a": "b"}}')

    def test_namedtuple(self) -> None:
        'Print a namedtuple as JSON'

        s = StringIO()
        Testr = namedtuple('Testr', ('a', 'b'))

        pp.ppd({'x': Testr(1, 2)}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"x": {"a": 1, "b": 2}}')

    def test_list_of_namedtuple(self) -> None:
        'Print a namedtuple as JSON'

        s = StringIO()
        Testr = namedtuple('Testr', ('a', 'b'))
        pp.ppd([Testr(1, 2), Testr(3, 4)], indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '[{"a": 1, "b": 2}, {"a": 3, "b": 4}]')

    def test_other(self) -> None:
        'Print an object with a __str__ method as JSON'

        s = StringIO()
        class Testr:
            def t(self) -> None: pass

        t = Testr()
        pp.ppd({'a': t.t}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"a": "t"}')

    def test_tuple_keys(self) -> None:
        'Print a dict with tuple keys as JSON'

        s = StringIO()
        pp.ppd({('a', 'b'): 'c'}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{"(\'a\', \'b\')": "c"}')



class TestArguments(unittest.TestCase):

    def tearDown(self) -> None:
        # Reset pp.enabled to default state after each test
        pp.enabled = True

    def test_enabled(self) -> None:
        'The enabled property should toggle print output on & off'

        pp.enabled = False
        s = StringIO()
        pp.ppd({'a': 'b'}, indent=None, style=None, file=s)

        self.assertEqual(s.getvalue(), '')

        pp.enabled = True
        s2 = StringIO()
        pp.ppd({'a': 'b'}, indent=None, style=None, file=s2)

        self.assertEqual(s2.getvalue().strip(), '{"a": "b"}')

    def test_indent(self) -> None:
        'The indent property should set the indentation level'

        s = StringIO()
        pp.ppd({'a': {'b': 'c'}}, indent=2, style=None, file=s)

        self.assertEqual(s.getvalue().strip(), '{\n  "a": {\n    "b": "c"\n  }\n}')


class TestNormalise(unittest.TestCase):

    def test_is_namedtuple(self) -> None:
        'Detect if an object is a namedtuple'

        Testr = namedtuple('Testr', ('a', 'b'))
        t = Testr(1,2)

        self.assertTrue(pp._isnamedtuple(t))

    def test_normalise(self) -> None:
        'Normalise namedtuples into dicts'

        Testr = namedtuple('Testr', ('a', 'b'))

        result = pp._normalise({
            'x': Testr(1, 2),
            'y': [Testr(5, 6), Testr(3, 4)],
        })

        self.assertEqual(result, {
            'x': {'a': 1, 'b': 2},
            'y': [
                {'a': 5, 'b': 6},
                {'a': 3, 'b': 4},
            ]
        })

