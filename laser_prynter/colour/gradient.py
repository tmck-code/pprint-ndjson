from __future__ import annotations

import operator
import os
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from itertools import chain, repeat
from typing import Literal

from laser_prynter.colour import c

type Cell = c.ANSIColour
Row = list[Cell]


@dataclass
class Face:
    rows: list[Row]
    with_rotations: bool = True
    rotations: list[Face] = field(default_factory=list)
    flipped_rotations: list[Face] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.with_rotations:
            self.rotations = [Face._rot90(self.rows, n, flip=False) for n in range(4)]
            self.flipped_rotations = [Face._rot90(self.rows, n, flip=True) for n in range(4)]

    @staticmethod
    def _rot90(rows: list[Row], n: int = 1, flip: bool = False) -> Face:
        'Rotate a matrix 90 degrees, n times, optionally flipped'
        if flip:
            rows = list(reversed(rows))
        for _ in range(n):
            rows = list(map(list, zip(*rows[::-1])))
        return Face(rows, with_rotations=False)

    def rot90(self, n: int = 1, flip: bool = False) -> Face:
        'Rotate a matrix 90 degrees, n times, optionally flipped'
        if flip:
            return self.flipped_rotations[n]
        return self.rotations[n]

    def __iter__(self) -> Iterator[Row]:
        yield from self.rows

    def __next__(self) -> Row:
        return next(self.__iter__())

    def __getitem__(self, i: int) -> Row:
        return self.rows[i]

    @staticmethod
    def empty_face(width: int = 6) -> Face:
        return Face([[c.from_ansi(256)] * width] * width)

    def iter_s(self, padding_top: int = 0, padding_bottom: int = 0, cell_width: int = 15) -> Iterable[str]:
        for row in iter(self):
            p = [cell.colorise(' ' * cell_width) for cell in row]
            # r = [cell.colorise(f'{cell.ansi_n:^{cell_width}}') for cell in row]
            r = [cell.colorise(f'{cell.rgb!s:^{cell_width}}') for cell in row]

            for row_str in chain(repeat(p, padding_top), [r], repeat(p, padding_bottom)):
                yield ''.join(row_str)

    def print(self, padding_top: int = 0, padding_bottom: int = 0, cell_width: int = 6) -> None:
        'Print the face, with optional cell padding top/bottom to make it more "square"'

        print('\n'.join(self.iter_s(padding_top, padding_bottom, cell_width)))


ANSI_COLOURS = re.compile(
    r"""
    \x1b     # literal ESC
    \[       # literal [
    [;\d]*   # zero or more digits or semicolons
    [A-Za-z] # a letter
    """,
    re.VERBOSE,
)


@dataclass
class Faces:
    faces: list[list[Face]]

    def __iter__(self) -> Iterator[Face]:
        for face_row in self.faces:
            yield from face_row

    def __next__(self) -> Face:
        return next(self.__iter__())

    def iter_rows(self) -> Iterator[Row]:
        for face_row in self.faces:
            for row in zip(*face_row):
                yield list(row)

    def iter_s(self, padding_top: int = 0, padding_bottom: int = 0, cell_width: int = 6) -> Iterable[str]:
        for face_row in self.faces:
            for row in zip(*[face.iter_s(padding_top, padding_bottom, cell_width) for face in face_row]):
                yield ''.join(row)

    def as_str(self, padding_top: int = 0, padding_bottom: int = 0, cell_width: int = 6) -> str:
        s = ''
        for row in self.iter_s(padding_top, padding_bottom, cell_width):
            s += row + '\n'
        return s

    def print(self, padding_top: int = 0, padding_bottom: int = 0, cell_width: int = 6) -> None:
        'Print the faces of the cube, with optional cell padding top/bottom to make it more "square"'

        print(self.as_str(padding_top, padding_bottom, cell_width))


def distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    return float(abs(sum(map(operator.sub, c2, c1))))


@dataclass
class RGBCube:
    faces: Faces
    width: int = 6

    def print(self) -> None:
        self.faces.print()

    @property
    def str_width(self) -> int:
        return max(len(ANSI_COLOURS.sub('', line)) for line in self.faces.iter_s())

    @staticmethod
    def compare_rows(r1: Row, r2: Row) -> bool:
        return all(c1 == c2 for c1, c2 in zip(r1, r2))

    def find_face_with_edge(self, face: Face, edge_type: str = 'ts') -> Face:
        if edge_type == 'ts':
            edge = face[0]
        elif edge_type == 'bs':
            edge = face[-1]
        elif edge_type == 'lhs':
            edge = [r[0] for r in face]
        elif edge_type == 'rhs':
            edge = [r[-1] for r in face]

        for candidate in self.faces:
            for rot in range(4):
                for flip in (False, True):
                    if (
                        (edge_type == 'ts' and RGBCube.compare_rows(candidate.rot90(rot, flip=flip)[-1], edge))
                        or (edge_type == 'bs' and RGBCube.compare_rows(candidate.rot90(rot, flip=flip)[0], edge))
                        or (edge_type == 'lhs' and RGBCube.compare_rows([r[-1] for r in candidate.rot90(rot, flip=flip)], edge))
                        or (edge_type == 'rhs' and RGBCube.compare_rows([r[0] for r in candidate.rot90(rot, flip=flip)], edge))
                    ):
                        return candidate.rot90(rot, flip=flip)
        raise ValueError('No face with matching edge found')

    @staticmethod
    def from_ranges(c1: Literal[c._RGB_COMPONENT], c2: c._RGB_COMPONENT, c3: c._RGB_COMPONENT) -> RGBCube:
        '''
        Create a 6x6x6 cube of RGB values, where each face is a 6x6 grid of cells.
        Takes an 'order' of RGB components, where
        - c1 is iterated once per face
        - c2 is iterated once per row
        - c3 is iterated once per cell
        '''
        faces = []
        for r1 in range(6):
            face = []
            for r2 in range(6):
                row = []
                for r3 in range(6):
                    coords = {c1: r1, c2: r2, c3: r3}
                    row.append(c.from_cube_coords(r=coords['r'], g=coords['g'], b=coords['b']))
                face.append(row)
            faces.append([Face(face)])
        return RGBCube(Faces(faces))


@dataclass
class RGBCubeCollection:
    cubes: dict[str, RGBCube]

    def __post_init__(self) -> None:
        self.width = os.get_terminal_size().columns

    def print(
        self,
        grid_sep: str = ' ' * 2,
        padding_top: int = 0,
        padding_bottom: int = 0,
        cell_width: int = 6,
    ) -> None:
        groups: list[dict[str, RGBCube]] = []
        current_group: dict[str, RGBCube] = {}
        for name, cube in self.cubes.items():
            if sum(v.str_width for v in current_group.values()) + cube.str_width <= self.width:
                current_group[name] = cube
            else:
                groups.append(current_group)
                current_group = {name: cube}
        groups.append(current_group)

        for g in groups:
            for name, cube in g.items():
                print(f'{name:<{cube.str_width}s}', end=grid_sep)
            print()
            for rows in zip(*[cube.faces.iter_s(padding_top, padding_bottom, cell_width) for cube in g.values()]):
                print(grid_sep.join(rows))


def find_face_with_edge(collection: RGBCubeCollection, face_name: str, face: Face, edge_type: str) -> tuple[Face, str]:
    for n, cube in collection.cubes.items():
        if n == face_name:
            continue
        try:
            f = cube.find_face_with_edge(face, edge_type)
            return f, n
        except ValueError:
            continue
    raise ValueError('No face with matching edge found')


def create_cube(f1: Face, f1_name: str, cube_collection: RGBCubeCollection) -> None:
    f2, _ = find_face_with_edge(cube_collection, f1_name, f1, 'lhs')
    f3, f3_name = find_face_with_edge(cube_collection, f1_name, f1, 'bs')
    f4, _ = find_face_with_edge(cube_collection, f1_name, f1, 'ts')
    f5, _ = find_face_with_edge(cube_collection, f3_name, f3, 'rhs')
    f6, _ = find_face_with_edge(cube_collection, f3_name, f3, 'bs')

    faces = [
        [Face.empty_face(6), f4, Face.empty_face(6)],
        [f2, f1, Face.empty_face(6)],
        [Face.empty_face(6), f3, f5],
        [Face.empty_face(6), f6, Face.empty_face(6)],
    ]
    Faces(faces).print(padding_top=0, padding_bottom=1, cell_width=15)


@dataclass
class Gradient:
    'Represents a gradient between two RGB colours.'

    start: c.RGBColour
    end: c.RGBColour
    steps: int

    @staticmethod
    def lerp(val0: float, val1: float, fraction: float) -> float:
        '''
        Precise method for iterpolation, which guarantees v = v1 when t = 1.
        (the very end value of this gradient will be exactly the end colour i.e. no rounding errors)
        (from: https://en.wikipedia.org/wiki/Linear_interpolation#Programming_language_support)

        note: 0.0 <= fraction <= 1.0
        '''
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f'Fraction must be between 0.0 and 1.0: {fraction}')
        return round(
            (1 - fraction) * val0 + fraction * val1,
            2,
        )

    @staticmethod
    def interp(v0: float, v1: float, n_steps: int) -> list[float]:
        return [Gradient.lerp(v0, v1, i / (n_steps - 1)) for i in range(n_steps)]

    @staticmethod
    def interp_xyz(c1: tuple[int, int, int], c2: tuple[int, int, int], n_steps: int) -> list[tuple[float, ...]]:
        return list(zip(*map(Gradient.interp, c1, c2, repeat(n_steps))))


@dataclass
class RGBGradient(Gradient):
    sequence: list[c.RGBColour] = field(init=False)

    def __post_init__(self) -> None:
        seq = self.interp_xyz(
            c1=(self.start.r, self.start.g, self.start.b),
            c2=(self.end.r, self.end.g, self.end.b),
            n_steps=self.steps,
        )
        self.sequence = [c.RGBColour(*map(int, color)) for color in seq]
