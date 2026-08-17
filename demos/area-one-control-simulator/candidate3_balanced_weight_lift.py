#!/usr/bin/env python3
"""Exact theorem checks for the pre-protocol Candidate 3 balanced-weight lift."""

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


class BalancedWeightError(ValueError):
    """Raised when an exact balanced-weight structural certificate fails."""


@dataclass(frozen=True)
class BalancedSeed:
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

    @property
    def p(self) -> int:
        return len(self.cells[2])


@dataclass(frozen=True)
class SpectralCertificate:
    exact_nullity: int
    off_diagonal_rank: int
    norm_squared: Fraction
    entrance_weight: Fraction
    exit_weight: Fraction
    endpoint_transfer: Fraction
    repeated_singular_square: Fraction
    repeated_multiplicity: int
    quadratic_trace: Fraction
    quadratic_determinant: Fraction
    polynomial_at_one: Fraction
    polynomial_at_two: Fraction
    numerical_gap: float


@dataclass(frozen=True)
class PermutationCertificate:
    permutation: tuple[int, ...]
    vertex_map: tuple[int, ...]
    endpoints_fixed: bool
    exact_conjugacy: bool


def coordinate_index(s: int, row: int, column: int) -> int:
    if type(s) is not int or type(row) is not int or type(column) is not int:
        raise BalancedWeightError("coordinates and s must be exact integers")
    if s < 1 or row < 0 or column < 0 or column > s:
        raise BalancedWeightError("coordinate is outside the EOG grid")
    return row * (s + 1) + column


def _zero_matrix(size: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(size)] for _ in range(size)]


def _add_edge(
    adjacency: list[list[Fraction]], left: int, right: int, weight: Fraction,
) -> None:
    if left == right or type(weight) is not Fraction or weight <= 0:
        raise BalancedWeightError("edges must be loop-free with exact positive weight")
    if adjacency[left][right] != 0 or adjacency[right][left] != 0:
        raise BalancedWeightError("duplicate edges are forbidden")
    adjacency[left][right] = weight
    adjacency[right][left] = weight


def _declared_cells(s: int, rows: int) -> tuple[tuple[int, ...], ...]:
    coordinate_count = rows * (s + 1)
    entrance = coordinate_index(s, 0, 0)
    exit_state = coordinate_index(s, rows - 1, s)
    sources = tuple(coordinate_index(s, row, s) for row in range(rows - 1))
    destinations = tuple(coordinate_index(s, row + 1, 0) for row in range(rows - 1))
    reserved = {entrance, exit_state, *sources, *destinations}
    unused = tuple(index for index in range(coordinate_count) if index not in reserved)
    if len(unused) % 2:
        raise BalancedWeightError("unused coordinates must split evenly")
    half = len(unused) // 2
    return (
        (entrance,),
        (coordinate_count,),
        sources + unused[:half],
        destinations + unused[half:],
        (exit_state,),
    )


def _adjacency_for_matching(
    cells: tuple[tuple[int, ...], ...],
    size: int,
    permutation: Sequence[int],
) -> Matrix:
    p = len(cells[2])
    validated = validate_permutation(permutation, p)
    adjacency = _zero_matrix(size)
    _add_edge(adjacency, cells[0][0], cells[1][0], Fraction(1))
    for vertex in cells[2]:
        _add_edge(adjacency, cells[1][0], vertex, Fraction(1))
    for source_position, destination_position in enumerate(validated):
        _add_edge(
            adjacency,
            cells[2][source_position],
            cells[3][destination_position],
            Fraction(p),
        )
    for vertex in cells[3]:
        _add_edge(adjacency, vertex, cells[4][0], Fraction(1))
    return tuple(tuple(row) for row in adjacency)


def build_seed(s: int, rows: int = 6) -> BalancedSeed:
    """Build and fully certify the fixed candidate matching."""
    if type(s) is not int or type(rows) is not int or (s, rows) not in GRIDS:
        raise BalancedWeightError("only the declared structural grids are allowed")
    coordinate_count = rows * (s + 1)
    labels: tuple[Label, ...] = tuple(
        (row, column) for row in range(rows) for column in range(s + 1)
    ) + (HUB_LABEL,)
    cells = _declared_cells(s, rows)
    genuine_pairs = tuple(
        (coordinate_index(s, row, s), coordinate_index(s, row + 1, 0))
        for row in range(rows - 1)
    )
    seed = BalancedSeed(
        s=s,
        rows=rows,
        labels=labels,
        cells=cells,
        adjacency=_adjacency_for_matching(cells, len(labels), tuple(range(len(cells[2])))),
        entrance=cells[0][0],
        exit=cells[4][0],
        genuine_pairs=genuine_pairs,
    )
    validate_seed(seed)
    return seed


def validate_permutation(permutation: Sequence[int], p: int) -> tuple[int, ...]:
    if type(p) is not int or p <= 0:
        raise BalancedWeightError("p must be a positive exact integer")
    values = tuple(permutation)
    if any(type(value) is not int for value in values):
        raise BalancedWeightError("permutation entries must be exact integers")
    if len(values) != p or sorted(values) != list(range(p)):
        raise BalancedWeightError("matching control must be a bijection of 0 through p-1")
    return values


def validate_coordinates_and_partition(seed: BalancedSeed) -> None:
    if not isinstance(seed, BalancedSeed) or (seed.s, seed.rows) not in GRIDS:
        raise BalancedWeightError("seed type or grid is invalid")
    expected_labels: tuple[Label, ...] = tuple(
        (row, column)
        for row in range(seed.rows)
        for column in range(seed.s + 1)
    ) + (HUB_LABEL,)
    if seed.labels != expected_labels or len(set(seed.labels)) != seed.size:
        raise BalancedWeightError("coordinate and hub labels changed")
    if seed.cells != _declared_cells(seed.s, seed.rows):
        raise BalancedWeightError("ordered deterministic cells changed")
    flattened = tuple(vertex for cell in seed.cells for vertex in cell)
    if sorted(flattened) != list(range(seed.size)) or len(set(flattened)) != seed.size:
        raise BalancedWeightError("partition must cover every vertex exactly once")
    coordinate_count = seed.rows * (seed.s + 1)
    p = coordinate_count // 2 - 1
    if tuple(map(len, seed.cells)) != (1, 1, p, p, 1):
        raise BalancedWeightError("cell sizes changed")
    if seed.entrance != coordinate_index(seed.s, 0, 0):
        raise BalancedWeightError("entrance changed")
    if seed.exit != coordinate_index(seed.s, seed.rows - 1, seed.s):
        raise BalancedWeightError("exit changed")


def validate_matrix(adjacency: Matrix, size: int) -> None:
    if len(adjacency) != size or any(len(row) != size for row in adjacency):
        raise BalancedWeightError("adjacency dimensions changed")
    for left in range(size):
        for right in range(size):
            weight = adjacency[left][right]
            if type(weight) is not Fraction:
                raise BalancedWeightError("all weights must be exact Fractions")
            if weight < 0:
                raise BalancedWeightError("negative weights are forbidden")
            if left == right and weight:
                raise BalancedWeightError("self-loops are forbidden")
            if weight != adjacency[right][left]:
                raise BalancedWeightError("adjacency must be symmetric")


def validate_declared_weights(seed: BalancedSeed) -> None:
    validate_matrix(seed.adjacency, seed.size)
    expected = _adjacency_for_matching(seed.cells, seed.size, tuple(range(seed.p)))
    if seed.adjacency != expected:
        raise BalancedWeightError("edge set or fixed balanced weights changed")
    expected_pairs = tuple(
        (coordinate_index(seed.s, row, seed.s), coordinate_index(seed.s, row + 1, 0))
        for row in range(seed.rows - 1)
    )
    if seed.genuine_pairs != expected_pairs or len(expected_pairs) != 5:
        raise BalancedWeightError("genuine overlap metadata changed")
    for left, right in expected_pairs:
        if seed.adjacency[left][right] != Fraction(seed.p):
            raise BalancedWeightError("genuine overlap edge has the wrong fixed weight")
    if seed.adjacency[seed.exit][seed.entrance] != 0:
        raise BalancedWeightError("false periodic overlap edge is forbidden")
    seen = {seed.entrance}
    pending = [seed.entrance]
    while pending:
        vertex = pending.pop()
        for neighbour, weight in enumerate(seed.adjacency[vertex]):
            if weight > 0 and neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    if len(seen) != seed.size:
        raise BalancedWeightError("balanced lift must be connected")


def expected_quotient(seed: BalancedSeed) -> Matrix:
    p = Fraction(seed.p)
    return tuple(tuple(Fraction(value) for value in row) for row in (
        (0, 1, 0, 0, 0),
        (1, 0, p, 0, 0),
        (0, 1, 0, p, 0),
        (0, 0, p, 0, 1),
        (0, 0, 0, p, 0),
    ))


def quotient_matrix(seed: BalancedSeed) -> Matrix:
    signatures: list[tuple[Fraction, ...]] = []
    cell_of: dict[int, int] = {}
    for cell_index, cell in enumerate(seed.cells):
        for vertex in cell:
            cell_of[vertex] = cell_index
        first: tuple[Fraction, ...] | None = None
        for vertex in cell:
            signature = tuple(
                sum((seed.adjacency[vertex][target] for target in targets), Fraction(0))
                for targets in seed.cells
            )
            if first is None:
                first = signature
            elif signature != first:
                raise BalancedWeightError("partition is not exactly equitable")
        if first is None:
            raise BalancedWeightError("quotient cells must not be empty")
        signatures.append(first)
    quotient = tuple(signatures)
    for vertex in range(seed.size):
        for target_cell, targets in enumerate(seed.cells):
            hp = sum((seed.adjacency[vertex][target] for target in targets), Fraction(0))
            if hp != quotient[cell_of[vertex]][target_cell]:
                raise BalancedWeightError("exact H P = P B closure failed")
    return quotient


def validate_quotient(seed: BalancedSeed) -> Matrix:
    quotient = quotient_matrix(seed)
    if quotient != expected_quotient(seed):
        raise BalancedWeightError("balanced directional quotient changed")
    return quotient


def validate_chiral(seed: BalancedSeed) -> None:
    signs = [0] * seed.size
    for cell_index, cell in enumerate(seed.cells):
        sign = 1 if cell_index in (0, 2, 4) else -1
        for vertex in cell:
            signs[vertex] = sign
    if signs.count(1) - signs.count(-1) != 1:
        raise BalancedWeightError("sublattice imbalance must be one")
    for left, row in enumerate(seed.adjacency):
        for right, weight in enumerate(row):
            if signs[left] * weight * signs[right] != -weight:
                raise BalancedWeightError("Gamma H Gamma = -H failed exactly")


def _rref(matrix: Sequence[Sequence[Fraction]]) -> tuple[list[list[Fraction]], tuple[int, ...]]:
    values = [[Fraction(value) for value in row] for row in matrix]
    column_count = len(values[0]) if values else 0
    if any(len(row) != column_count for row in values):
        raise BalancedWeightError("exact matrix must be rectangular")
    pivots: list[int] = []
    pivot_row = 0
    for column in range(column_count):
        pivot = next((row for row in range(pivot_row, len(values)) if values[row][column]), None)
        if pivot is None:
            continue
        values[pivot_row], values[pivot] = values[pivot], values[pivot_row]
        divisor = values[pivot_row][column]
        values[pivot_row] = [value / divisor for value in values[pivot_row]]
        for row in range(len(values)):
            if row == pivot_row:
                continue
            factor = values[row][column]
            if factor:
                values[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(values[row], values[pivot_row], strict=True)
                ]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(values):
            break
    return values, tuple(pivots)


def exact_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    return len(_rref(matrix)[1])


def balanced_zero_vector(seed: BalancedSeed) -> tuple[Fraction, ...]:
    values = (-Fraction(seed.p), Fraction(0), Fraction(1), Fraction(0), -Fraction(seed.p))
    vector = [Fraction(0) for _ in range(seed.size)]
    for cell, value in zip(seed.cells, values, strict=True):
        for vertex in cell:
            vector[vertex] = value
    return tuple(vector)


def _matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> tuple[Fraction, ...]:
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def validate_zero_mode(
    seed: BalancedSeed,
    vector: Sequence[Fraction] | None = None,
) -> tuple[int, Fraction, Fraction, Fraction]:
    zero_vector = balanced_zero_vector(seed) if vector is None else tuple(vector)
    if len(zero_vector) != seed.size or any(type(value) is not Fraction for value in zero_vector):
        raise BalancedWeightError("zero mode must be an exact full-length Fraction vector")
    if any(value != 0 for value in _matrix_vector(seed.adjacency, zero_vector)):
        raise BalancedWeightError("balanced vector is not an exact zero mode")
    if zero_vector[seed.entrance] != zero_vector[seed.exit] or zero_vector[seed.entrance] == 0:
        raise BalancedWeightError("zero-mode endpoints are not exactly balanced and nonzero")
    rank = exact_rank(seed.adjacency)
    nullity = seed.size - rank
    if nullity != 1:
        raise BalancedWeightError("exact nullity must be one")
    norm_squared = sum((value * value for value in zero_vector), Fraction(0))
    expected_norm = Fraction(seed.p * (2 * seed.p + 1))
    if norm_squared != expected_norm:
        raise BalancedWeightError("balanced zero-mode norm formula failed")
    endpoint_weight = zero_vector[seed.entrance] ** 2 / norm_squared
    endpoint_transfer = abs(zero_vector[seed.entrance] * zero_vector[seed.exit]) / norm_squared
    expected_weight = Fraction(seed.p, 2 * seed.p + 1)
    if endpoint_weight != expected_weight or endpoint_transfer != expected_weight:
        raise BalancedWeightError("balanced endpoint support or transfer formula failed")
    return nullity, norm_squared, endpoint_weight, endpoint_transfer


def _stable_small_quadratic_root(trace: int, determinant: int) -> float:
    discriminant = float(trace * trace - 4 * determinant)
    if not math.isfinite(discriminant) or discriminant < 0:
        raise BalancedWeightError("spectral quadratic discriminant is invalid")
    denominator = float(trace) + math.sqrt(discriminant)
    return 2.0 * float(determinant) / denominator


def validate_numerical_spectrum(
    eigenvalues: Sequence[float], exact_nullity: int, expected_gap: float,
) -> float:
    if type(exact_nullity) is not int or exact_nullity != 1:
        raise BalancedWeightError("numerical diagnosis requires exact nullity one")
    if not math.isfinite(expected_gap) or expected_gap <= GAP_TOLERANCE:
        raise BalancedWeightError("expected numerical gap is invalid")
    values = tuple(float(value) for value in eigenvalues)
    if not values or any(not math.isfinite(value) for value in values):
        raise BalancedWeightError("numerical spectrum contains a nonfinite value")
    zeros = tuple(value for value in values if abs(value) <= ZERO_TOLERANCE)
    if len(zeros) != exact_nullity:
        raise BalancedWeightError("numerical zero count disagrees with exact nullity")
    nonzero = tuple(abs(value) for value in values if abs(value) > ZERO_TOLERANCE)
    gap = min(nonzero) if nonzero else 0.0
    if not math.isfinite(gap) or gap <= GAP_TOLERANCE:
        raise BalancedWeightError("numerical spectral gap is not safely positive")
    if not math.isclose(gap, expected_gap, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise BalancedWeightError("numerical gap disagrees with the exact spectral polynomial")
    return gap


def numerical_gap(seed: BalancedSeed, exact_nullity: int) -> float:
    if exact_nullity != 1 or seed.size - exact_rank(seed.adjacency) != 1:
        raise BalancedWeightError("exact nullity must be established before numerical diagnosis")
    import numpy as np

    dense = np.array([[float(value) for value in row] for row in seed.adjacency], dtype=np.float64)
    eigenvalues = np.linalg.eigvalsh(dense)
    trace = (seed.p + 1) ** 2
    determinant = seed.p * (2 * seed.p + 1)
    expected = math.sqrt(_stable_small_quadratic_root(trace, determinant))
    return validate_numerical_spectrum(eigenvalues.tolist(), exact_nullity, expected)


def _exact_spectral_invariants(
    seed: BalancedSeed,
) -> tuple[int, Fraction, int, Fraction, Fraction]:
    positive = seed.cells[0] + seed.cells[2] + seed.cells[4]
    negative = seed.cells[1] + seed.cells[3]
    off_diagonal = tuple(
        tuple(seed.adjacency[vertex][neighbour] for neighbour in negative)
        for vertex in positive
    )
    off_diagonal_rank = exact_rank(off_diagonal)
    if off_diagonal_rank != seed.p + 1:
        raise BalancedWeightError("off-diagonal block must have full column rank")
    gram = tuple(tuple(
        sum(
            (off_diagonal[row][left] * off_diagonal[row][right] for row in range(len(positive))),
            Fraction(0),
        )
        for right in range(len(negative))
    ) for left in range(len(negative)))
    p = seed.p
    repeated_square = Fraction(p * p)
    for index in range(p - 1):
        vector = [Fraction(0) for _ in negative]
        vector[index + 1] = Fraction(1)
        vector[-1] = Fraction(-1)
        product = _matrix_vector(gram, vector)
        if product != tuple(repeated_square * value for value in vector):
            raise BalancedWeightError("repeated singular-value sector failed exactly")
    hub = (Fraction(1),) + (Fraction(0),) * p
    symmetric = (Fraction(0),) + (Fraction(1),) * p
    gram_hub = _matrix_vector(gram, hub)
    gram_symmetric = _matrix_vector(gram, symmetric)
    expected_hub = tuple(
        Fraction(p + 1) * hub[index] + Fraction(p) * symmetric[index]
        for index in range(p + 1)
    )
    expected_symmetric = tuple(
        Fraction(p * p) * hub[index] + Fraction(p * p + p) * symmetric[index]
        for index in range(p + 1)
    )
    if gram_hub != expected_hub or gram_symmetric != expected_symmetric:
        raise BalancedWeightError("two-dimensional singular-value sector failed exactly")
    trace = Fraction((p + 1) + (p * p + p))
    determinant = Fraction((p + 1) * (p * p + p) - p * p * p)
    return off_diagonal_rank, repeated_square, p - 1, trace, determinant


def spectral_certificate(seed: BalancedSeed) -> SpectralCertificate:
    nullity, norm_squared, endpoint_weight, endpoint_transfer = validate_zero_mode(seed)
    p = seed.p
    (
        off_diagonal_rank,
        repeated_square,
        repeated_multiplicity,
        trace,
        determinant,
    ) = _exact_spectral_invariants(seed)
    if trace != Fraction((p + 1) ** 2) or determinant != Fraction(p * (2 * p + 1)):
        raise BalancedWeightError("exact spectral invariants disagree with closed form")
    at_one = Fraction(1) - trace + determinant
    at_two = Fraction(4) - 2 * trace + determinant
    if at_one != Fraction(p * (p - 1)) or at_one <= 0:
        raise BalancedWeightError("lower exact gap bound failed")
    if at_two != Fraction(2 - 3 * p) or at_two >= 0:
        raise BalancedWeightError("upper exact gap bound failed")
    if p - 1 <= 0:
        raise BalancedWeightError("repeated singular-value sector is invalid")
    gap = numerical_gap(seed, nullity)
    return SpectralCertificate(
        exact_nullity=nullity,
        off_diagonal_rank=off_diagonal_rank,
        norm_squared=norm_squared,
        entrance_weight=endpoint_weight,
        exit_weight=endpoint_weight,
        endpoint_transfer=endpoint_transfer,
        repeated_singular_square=repeated_square,
        repeated_multiplicity=repeated_multiplicity,
        quadratic_trace=trace,
        quadratic_determinant=determinant,
        polynomial_at_one=at_one,
        polynomial_at_two=at_two,
        numerical_gap=gap,
    )


def control_adjacency(seed: BalancedSeed, permutation: Sequence[int]) -> Matrix:
    validated = validate_permutation(permutation, seed.p)
    return _adjacency_for_matching(seed.cells, seed.size, validated)


def permutation_certificate(
    seed: BalancedSeed, permutation: Sequence[int],
) -> PermutationCertificate:
    validated = validate_permutation(permutation, seed.p)
    control = control_adjacency(seed, validated)
    vertex_map = list(range(seed.size))
    for source_position, destination_position in enumerate(validated):
        vertex_map[seed.cells[3][source_position]] = seed.cells[3][destination_position]
    if len(set(vertex_map)) != seed.size:
        raise BalancedWeightError("control vertex map is not bijective")
    exact_conjugacy = all(
        seed.adjacency[left][right] == control[vertex_map[left]][vertex_map[right]]
        for left in range(seed.size)
        for right in range(seed.size)
    )
    endpoints_fixed = vertex_map[seed.entrance] == seed.entrance and vertex_map[seed.exit] == seed.exit
    if not exact_conjugacy or not endpoints_fixed:
        raise BalancedWeightError("matching control isomorphism certificate failed")
    return PermutationCertificate(
        permutation=validated,
        vertex_map=tuple(vertex_map),
        endpoints_fixed=endpoints_fixed,
        exact_conjugacy=exact_conjugacy,
    )


def unit_weight_endpoint_metrics(p: int) -> tuple[Fraction, Fraction, Fraction]:
    if type(p) is not int or p <= 0:
        raise BalancedWeightError("p must be a positive exact integer")
    denominator = p * p + p + 1
    return Fraction(p * p, denominator), Fraction(1, denominator), Fraction(p, denominator)


def validate_seed(seed: BalancedSeed) -> SpectralCertificate:
    validate_coordinates_and_partition(seed)
    validate_declared_weights(seed)
    validate_quotient(seed)
    validate_chiral(seed)
    certificate = spectral_certificate(seed)
    if certificate.entrance_weight < Fraction(8, 17):
        raise BalancedWeightError("declared-grid endpoint support lower bound failed")
    permutation_certificate(seed, tuple(range(seed.p)))
    return certificate
