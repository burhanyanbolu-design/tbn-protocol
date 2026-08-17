#!/usr/bin/env python3
"""Exact structural algebra for the pre-protocol Candidate 3 quotient lift."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Sequence

GRIDS = ((2, 6), (3, 6), (4, 6))
HUB_LABEL = "auxiliary-hub"
ZERO_TOLERANCE = 1.0e-10
GAP_TOLERANCE = 1.0e-12

Matrix = tuple[tuple[Fraction, ...], ...]
Label = tuple[int, int] | str


class Candidate3Error(ValueError):
    """Raised when the fixed structural seed violates its exact contract."""


@dataclass(frozen=True)
class Candidate3Seed:
    s: int
    rows: int
    labels: tuple[Label, ...]
    cells: tuple[tuple[int, ...], ...]
    adjacency: Matrix
    entrance: int
    exit: int
    genuine_pairs: tuple[tuple[int, int], ...]

    @property
    def size(self) -> int:
        return len(self.labels)


@dataclass(frozen=True)
class StructuralCertificate:
    quotient: Matrix
    exact_nullity: int
    numerical_gap: float


def coordinate_index(s: int, row: int, column: int) -> int:
    if type(s) is not int or type(row) is not int or type(column) is not int:
        raise Candidate3Error("coordinates and s must be exact integers")
    if s < 1 or row < 0 or column < 0 or column > s:
        raise Candidate3Error("coordinate is outside the declared EOG grid")
    return row * (s + 1) + column


def _mutable_zero_matrix(size: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(size)] for _ in range(size)]


def _add_unit_edge(matrix: list[list[Fraction]], left: int, right: int) -> None:
    if left == right or matrix[left][right] != 0 or matrix[right][left] != 0:
        raise Candidate3Error("declared edges must be unique and loop-free")
    matrix[left][right] = Fraction(1)
    matrix[right][left] = Fraction(1)


def build_seed(s: int, rows: int = 6) -> Candidate3Seed:
    """Construct the fixed no-parameter seed and fail closed on any defect."""
    if type(s) is not int or type(rows) is not int or (s, rows) not in GRIDS:
        raise Candidate3Error("only the declared structural grids are allowed")
    coordinate_count = rows * (s + 1)
    p = coordinate_count // 2 - 1
    labels: tuple[Label, ...] = tuple(
        (row, column) for row in range(rows) for column in range(s + 1)
    ) + (HUB_LABEL,)
    entrance = coordinate_index(s, 0, 0)
    exit_state = coordinate_index(s, rows - 1, s)
    hub = coordinate_count
    sources = tuple(coordinate_index(s, row, s) for row in range(rows - 1))
    destinations = tuple(coordinate_index(s, row + 1, 0) for row in range(rows - 1))
    reserved = {entrance, exit_state, *sources, *destinations}
    unused = tuple(index for index in range(coordinate_count) if index not in reserved)
    if len(unused) % 2:
        raise Candidate3Error("unused coordinate count must split evenly")
    half = len(unused) // 2
    cells = (
        (entrance,),
        (hub,),
        sources + unused[:half],
        destinations + unused[half:],
        (exit_state,),
    )
    if tuple(map(len, cells)) != (1, 1, p, p, 1):
        raise Candidate3Error("cell sizes do not match the fixed construction")
    mutable = _mutable_zero_matrix(len(labels))
    _add_unit_edge(mutable, cells[0][0], cells[1][0])
    for vertex in cells[2]:
        _add_unit_edge(mutable, cells[1][0], vertex)
    for left, right in zip(cells[2], cells[3], strict=True):
        _add_unit_edge(mutable, left, right)
    for vertex in cells[3]:
        _add_unit_edge(mutable, vertex, cells[4][0])
    seed = Candidate3Seed(
        s=s,
        rows=rows,
        labels=labels,
        cells=cells,
        adjacency=tuple(tuple(row) for row in mutable),
        entrance=entrance,
        exit=exit_state,
        genuine_pairs=tuple(zip(sources, destinations, strict=True)),
    )
    validate_seed(seed)
    return seed


def _expected_coordinate_labels(seed: Candidate3Seed) -> tuple[Label, ...]:
    return tuple(
        (row, column)
        for row in range(seed.rows)
        for column in range(seed.s + 1)
    ) + (HUB_LABEL,)


def validate_coordinate_coverage(seed: Candidate3Seed) -> None:
    if not isinstance(seed, Candidate3Seed):
        raise Candidate3Error("seed has the wrong type")
    if (seed.s, seed.rows) not in GRIDS:
        raise Candidate3Error("seed grid is outside the declared structural set")
    expected = _expected_coordinate_labels(seed)
    if seed.labels != expected or len(set(seed.labels)) != len(seed.labels):
        raise Candidate3Error("labels must retain every EOG coordinate exactly once plus the hub")
    if seed.entrance != coordinate_index(seed.s, 0, 0):
        raise Candidate3Error("entrance index changed")
    if seed.exit != coordinate_index(seed.s, seed.rows - 1, seed.s):
        raise Candidate3Error("exit index changed")


def validate_quotient_structure(seed: Candidate3Seed) -> None:
    cell_count = len(seed.cells)
    if cell_count % 2 == 0 or cell_count != 5:
        raise Candidate3Error("the quotient must be the declared five-cell odd path")
    if cell_count >= seed.size:
        raise Candidate3Error("the quotient must strictly compress the full lift")


def validate_partition(seed: Candidate3Seed) -> None:
    validate_quotient_structure(seed)
    flattened = tuple(vertex for cell in seed.cells for vertex in cell)
    if len(flattened) != seed.size or sorted(flattened) != list(range(seed.size)):
        raise Candidate3Error("partition must cover every vertex exactly once")
    if len(set(flattened)) != seed.size:
        raise Candidate3Error("partition contains a duplicate vertex")
    coordinate_count = seed.rows * (seed.s + 1)
    p = coordinate_count // 2 - 1
    if tuple(map(len, seed.cells)) != (1, 1, p, p, 1):
        raise Candidate3Error("partition cell sizes changed")
    sources = tuple(coordinate_index(seed.s, row, seed.s) for row in range(seed.rows - 1))
    destinations = tuple(coordinate_index(seed.s, row + 1, 0) for row in range(seed.rows - 1))
    reserved = {seed.entrance, seed.exit, *sources, *destinations}
    unused = tuple(index for index in range(coordinate_count) if index not in reserved)
    half = len(unused) // 2
    expected = (
        (seed.entrance,),
        (coordinate_count,),
        sources + unused[:half],
        destinations + unused[half:],
        (seed.exit,),
    )
    if seed.cells != expected:
        raise Candidate3Error("partition is not the deterministic declared partition")


def validate_adjacency(seed: Candidate3Seed) -> None:
    size = seed.size
    if len(seed.adjacency) != size or any(len(row) != size for row in seed.adjacency):
        raise Candidate3Error("adjacency dimensions do not match the labels")
    for left in range(size):
        for right in range(size):
            weight = seed.adjacency[left][right]
            if type(weight) is not Fraction:
                raise Candidate3Error("adjacency weights must be exact Fractions")
            if weight < 0:
                raise Candidate3Error("edge weights must be positive")
            if left == right and weight != 0:
                raise Candidate3Error("self-loops are forbidden")
            if weight != seed.adjacency[right][left]:
                raise Candidate3Error("adjacency must be exactly symmetric")
    seen = {0}
    pending = [0]
    while pending:
        vertex = pending.pop()
        for neighbour, weight in enumerate(seed.adjacency[vertex]):
            if weight > 0 and neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    if len(seen) != size:
        raise Candidate3Error("the lift must be connected")


def _expected_genuine_pairs(seed: Candidate3Seed) -> tuple[tuple[int, int], ...]:
    return tuple(
        (
            coordinate_index(seed.s, row, seed.s),
            coordinate_index(seed.s, row + 1, 0),
        )
        for row in range(seed.rows - 1)
    )


def validate_overlap_edges(seed: Candidate3Seed) -> None:
    expected = _expected_genuine_pairs(seed)
    if seed.genuine_pairs != expected or len(seed.genuine_pairs) != 5:
        raise Candidate3Error("exactly five genuine non-wrapping overlap pairs are required")
    for left, right in expected:
        if seed.adjacency[left][right] != Fraction(1):
            raise Candidate3Error("a genuine overlap edge is missing or reweighted")
    if seed.adjacency[seed.exit][seed.entrance] != 0:
        raise Candidate3Error("the false periodic overlap edge is forbidden")


def expected_quotient(seed: Candidate3Seed) -> Matrix:
    p = Fraction(len(seed.cells[2]))
    return tuple(tuple(Fraction(value) for value in row) for row in (
        (0, 1, 0, 0, 0),
        (1, 0, p, 0, 0),
        (0, 1, 0, 1, 0),
        (0, 0, 1, 0, 1),
        (0, 0, 0, p, 0),
    ))


def quotient_matrix(seed: Candidate3Seed) -> Matrix:
    validate_partition(seed)
    cell_of = {}
    for cell_index, cell in enumerate(seed.cells):
        for vertex in cell:
            cell_of[vertex] = cell_index
    signatures: list[tuple[Fraction, ...]] = []
    for cell in seed.cells:
        first_signature: tuple[Fraction, ...] | None = None
        for vertex in cell:
            signature = tuple(
                sum((seed.adjacency[vertex][target] for target in target_cell), Fraction(0))
                for target_cell in seed.cells
            )
            if first_signature is None:
                first_signature = signature
            elif signature != first_signature:
                raise Candidate3Error("partition is not exactly equitable")
        if first_signature is None:
            raise Candidate3Error("quotient cells must be nonempty")
        signatures.append(first_signature)
    quotient = tuple(signatures)
    for vertex in range(seed.size):
        source_cell = cell_of[vertex]
        for target_cell, targets in enumerate(seed.cells):
            hp = sum((seed.adjacency[vertex][target] for target in targets), Fraction(0))
            pb = quotient[source_cell][target_cell]
            if hp != pb:
                raise Candidate3Error("exact H P = P B closure failed")
    return quotient


def validate_quotient(seed: Candidate3Seed) -> Matrix:
    quotient = quotient_matrix(seed)
    if quotient != expected_quotient(seed):
        raise Candidate3Error("directional quotient neighbour counts changed")
    return quotient


def _sublattice_signs(seed: Candidate3Seed) -> tuple[int, ...]:
    signs = [0] * seed.size
    for cell_index, cell in enumerate(seed.cells):
        sign = 1 if cell_index in (0, 2, 4) else -1
        for vertex in cell:
            signs[vertex] = sign
    return tuple(signs)


def validate_chiral(seed: Candidate3Seed) -> None:
    signs = _sublattice_signs(seed)
    positive = sum(sign == 1 for sign in signs)
    negative = sum(sign == -1 for sign in signs)
    if positive - negative != 1:
        raise Candidate3Error("bipartite sublattice sizes must differ by one")
    for left, row in enumerate(seed.adjacency):
        for right, weight in enumerate(row):
            if signs[left] * weight * signs[right] != -weight:
                raise Candidate3Error("Gamma H Gamma = -H failed exactly")


def _rref(matrix: Sequence[Sequence[Fraction]]) -> tuple[list[list[Fraction]], tuple[int, ...]]:
    values = [[Fraction(value) for value in row] for row in matrix]
    row_count = len(values)
    column_count = len(values[0]) if values else 0
    if any(len(row) != column_count for row in values):
        raise Candidate3Error("exact matrix must be rectangular")
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(column_count):
        pivot = next((row for row in range(pivot_row, row_count) if values[row][column]), None)
        if pivot is None:
            continue
        values[pivot_row], values[pivot] = values[pivot], values[pivot_row]
        divisor = values[pivot_row][column]
        values[pivot_row] = [value / divisor for value in values[pivot_row]]
        for row in range(row_count):
            if row == pivot_row:
                continue
            factor = values[row][column]
            if factor:
                values[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(values[row], values[pivot_row], strict=True)
                ]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == row_count:
            break
    return values, tuple(pivot_columns)


def exact_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    return len(_rref(matrix)[1])


def exact_nullspace(matrix: Sequence[Sequence[Fraction]]) -> tuple[tuple[Fraction, ...], ...]:
    reduced, pivots = _rref(matrix)
    column_count = len(reduced[0]) if reduced else 0
    free_columns = [column for column in range(column_count) if column not in pivots]
    basis: list[tuple[Fraction, ...]] = []
    for free in free_columns:
        vector = [Fraction(0) for _ in range(column_count)]
        vector[free] = Fraction(1)
        for row, pivot in reversed(tuple(enumerate(pivots))):
            vector[pivot] = -sum(
                (reduced[row][column] * vector[column] for column in free_columns),
                Fraction(0),
            )
        basis.append(tuple(vector))
    return tuple(basis)


def candidate_zero_vector(seed: Candidate3Seed) -> tuple[Fraction, ...]:
    p = Fraction(len(seed.cells[2]))
    cell_values = (-p, Fraction(0), Fraction(1), Fraction(0), Fraction(-1))
    vector = [Fraction(0) for _ in range(seed.size)]
    for cell, value in zip(seed.cells, cell_values, strict=True):
        for vertex in cell:
            vector[vertex] = value
    return tuple(vector)


def _matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> tuple[Fraction, ...]:
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def validate_zero_mode(
    seed: Candidate3Seed,
    vector: Sequence[Fraction] | None = None,
) -> int:
    candidate = candidate_zero_vector(seed) if vector is None else tuple(vector)
    if len(candidate) != seed.size or any(type(value) is not Fraction for value in candidate):
        raise Candidate3Error("zero-mode candidate must be an exact full-length Fraction vector")
    if candidate[seed.entrance] == 0 or candidate[seed.exit] == 0:
        raise Candidate3Error("zero mode must have nonzero entrance and exit coordinates")
    if any(value != 0 for value in _matrix_vector(seed.adjacency, candidate)):
        raise Candidate3Error("declared vector is not an exact zero mode")
    nullity = len(exact_nullspace(seed.adjacency))
    if nullity != 1:
        raise Candidate3Error("the exact nullspace must be one-dimensional")
    return nullity


def validate_numerical_spectrum(
    eigenvalues: Sequence[float], exact_nullity: int,
) -> float:
    if type(exact_nullity) is not int or exact_nullity != 1:
        raise Candidate3Error("numerical diagnosis requires exact nullity one first")
    values = tuple(float(value) for value in eigenvalues)
    if not values or any(not math.isfinite(value) for value in values):
        raise Candidate3Error("numerical eigenvalues must all be finite")
    numerical_zeros = tuple(value for value in values if abs(value) <= ZERO_TOLERANCE)
    if len(numerical_zeros) != exact_nullity:
        raise Candidate3Error("binary64 zero count disagrees with exact nullity")
    nonzero = tuple(abs(value) for value in values if abs(value) > ZERO_TOLERANCE)
    gap = min(nonzero) if nonzero else 0.0
    if not math.isfinite(gap) or gap <= GAP_TOLERANCE:
        raise Candidate3Error("nearest nonzero binary64 gap is not safely positive")
    return gap


def numerical_gap(seed: Candidate3Seed, exact_nullity: int) -> float:
    if len(exact_nullspace(seed.adjacency)) != exact_nullity or exact_nullity != 1:
        raise Candidate3Error("exact nullity must be certified before binary64 diagnosis")
    import numpy as np

    dense = np.array(
        [[float(value) for value in row] for row in seed.adjacency],
        dtype=np.float64,
    )
    eigenvalues = np.linalg.eigvalsh(dense)
    return validate_numerical_spectrum(eigenvalues.tolist(), exact_nullity)


def validate_declared_edges(seed: Candidate3Seed) -> None:
    expected: set[tuple[int, int]] = set()
    expected.add(tuple(sorted((seed.cells[0][0], seed.cells[1][0]))))
    expected.update(tuple(sorted((seed.cells[1][0], vertex))) for vertex in seed.cells[2])
    expected.update(tuple(sorted(pair)) for pair in zip(seed.cells[2], seed.cells[3], strict=True))
    expected.update(tuple(sorted((vertex, seed.cells[4][0]))) for vertex in seed.cells[3])
    actual = {
        (left, right)
        for left in range(seed.size)
        for right in range(left + 1, seed.size)
        if seed.adjacency[left][right] != 0
    }
    if actual != expected:
        raise Candidate3Error("edge set differs from the fixed quotient lift")
    if any(seed.adjacency[left][right] != Fraction(1) for left, right in actual):
        raise Candidate3Error("all declared edges must have fixed unit weight")


def validate_seed(seed: Candidate3Seed) -> StructuralCertificate:
    validate_coordinate_coverage(seed)
    validate_partition(seed)
    validate_adjacency(seed)
    validate_overlap_edges(seed)
    quotient = validate_quotient(seed)
    validate_chiral(seed)
    nullity = validate_zero_mode(seed)
    validate_declared_edges(seed)
    gap = numerical_gap(seed, nullity)
    return StructuralCertificate(quotient=quotient, exact_nullity=nullity, numerical_gap=gap)
