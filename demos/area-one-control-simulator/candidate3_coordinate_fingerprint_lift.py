#!/usr/bin/env python3
"""Exact structural algebra for Candidate 3 coordinate fingerprints."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations
import math
from typing import Sequence

GRIDS = ((2, 6), (3, 6), (4, 6))
FINGERPRINTS = (2, 3, 4, 5, 6)
HUB_LABEL = "auxiliary-hub"
ZERO_TOLERANCE = 1.0e-10
GAP_TOLERANCE = 1.0e-12

Matrix = tuple[tuple[Fraction, ...], ...]
Label = tuple[int, int] | str


class CoordinateFingerprintError(ValueError):
    """Raised when an exact coordinate-fingerprint certificate fails."""


@dataclass(frozen=True)
class FingerprintSeed:
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
    def g(self) -> int:
        return len(FINGERPRINTS)

    @property
    def h(self) -> int:
        return len(self.cells[7])


    @property
    def p(self) -> int:
        return self.g + self.h

    @property
    def matched_weight(self) -> int:
        return sum(value * value for value in FINGERPRINTS) + self.h


@dataclass(frozen=True)
class StructuralCertificate:
    quotient: Matrix
    exact_nullity: int
    off_diagonal_rank: int
    norm_squared: Fraction
    endpoint_weight: Fraction
    zero_projector_endpoint_element: Fraction
    ldlt_pivots: tuple[Fraction, ...]
    candidate_fourth_moment: Fraction
    numerical_gap: float
    controls_checked: int


@dataclass(frozen=True)
class ControlCertificate:
    permutation: tuple[int, ...]
    correlation: Fraction
    displacement_energy: Fraction
    fair_weight_multiset: bool
    fair_vertex_weighted_degrees: bool
    edge_degree_profile_differs: bool
    candidate_fourth_moment: Fraction
    control_fourth_moment: Fraction
    moment_difference: Fraction
    zero_norm_squared: Fraction
    entrance_weight: Fraction
    exit_weight: Fraction
    zero_projector_endpoint_element: Fraction


def coordinate_index(s: int, row: int, column: int) -> int:
    if any(type(value) is not int for value in (s, row, column)):
        raise CoordinateFingerprintError("coordinates must be exact integers")
    if s < 1 or row < 0 or column < 0 or column > s:
        raise CoordinateFingerprintError("coordinate is outside the EOG grid")
    return row * (s + 1) + column


def _declared_cells(s: int, rows: int) -> tuple[tuple[int, ...], ...]:
    count = rows * (s + 1)
    entrance = coordinate_index(s, 0, 0)
    exit_state = coordinate_index(s, rows - 1, s)
    sources = tuple(coordinate_index(s, row, s) for row in range(rows - 1))
    destinations = tuple(coordinate_index(s, row + 1, 0) for row in range(rows - 1))
    reserved = {entrance, exit_state, *sources, *destinations}
    unused = tuple(index for index in range(count) if index not in reserved)
    if len(unused) % 2:
        raise CoordinateFingerprintError("support coordinates must split evenly")
    half = len(unused) // 2
    return (
        (entrance,),
        (count,),
        *((vertex,) for vertex in sources),
        unused[:half],
        *((vertex,) for vertex in destinations),
        unused[half:],
        (exit_state,),
    )


def source_vertices(seed: FingerprintSeed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[2:7]) + seed.cells[7]


def destination_vertices(seed: FingerprintSeed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[8:13]) + seed.cells[13]


def channel_factor(seed: FingerprintSeed, position: int) -> int:
    if type(position) is not int or not 0 <= position < seed.p:
        raise CoordinateFingerprintError("channel position is invalid")
    return FINGERPRINTS[position] if position < seed.g else 1


def validate_permutation(permutation: Sequence[int]) -> tuple[int, ...]:
    values = tuple(permutation)
    if len(values) != len(FINGERPRINTS) or any(type(value) is not int for value in values):
        raise CoordinateFingerprintError("genuine permutation must contain five exact integers")
    if sorted(values) != list(range(len(FINGERPRINTS))):
        raise CoordinateFingerprintError("genuine permutation must be a bijection")
    return values


def all_genuine_permutations(include_identity: bool = False) -> tuple[tuple[int, ...], ...]:
    if type(include_identity) is not bool:
        raise CoordinateFingerprintError("include_identity must be exact bool")
    identity = tuple(range(len(FINGERPRINTS)))
    return tuple(value for value in permutations(range(len(FINGERPRINTS))) if include_identity or value != identity)


def _add_edge(matrix: list[list[Fraction]], left: int, right: int, weight: Fraction) -> None:
    if left == right or type(weight) is not Fraction or weight <= 0:
        raise CoordinateFingerprintError("edges require exact positive weights and no loops")
    if matrix[left][right] or matrix[right][left]:
        raise CoordinateFingerprintError("duplicate edge")
    matrix[left][right] = weight
    matrix[right][left] = weight


def _adjacency(seed: FingerprintSeed, genuine_permutation: Sequence[int]) -> Matrix:
    genuine = validate_permutation(genuine_permutation)
    full_matching = genuine + tuple(range(seed.g, seed.p))
    sources = source_vertices(seed)
    destinations = destination_vertices(seed)
    matrix = [[Fraction(0) for _ in range(seed.size)] for _ in range(seed.size)]
    _add_edge(matrix, seed.entrance, seed.cells[1][0], Fraction(1))
    for position, source in enumerate(sources):
        _add_edge(matrix, seed.cells[1][0], source, Fraction(channel_factor(seed, position)))
    for source_position, destination_position in enumerate(full_matching):
        _add_edge(matrix, sources[source_position], destinations[destination_position], Fraction(seed.matched_weight))
    for position, destination in enumerate(destinations):
        _add_edge(matrix, destination, seed.exit, Fraction(channel_factor(seed, position)))
    return tuple(tuple(row) for row in matrix)


def build_seed(s: int, rows: int = 6) -> FingerprintSeed:
    if type(s) is not int or type(rows) is not int or (s, rows) not in GRIDS:
        raise CoordinateFingerprintError("only declared structural grids are allowed")
    count = rows * (s + 1)
    labels: tuple[Label, ...] = tuple(
        (row, column) for row in range(rows) for column in range(s + 1)
    ) + (HUB_LABEL,)
    cells = _declared_cells(s, rows)
    pairs = tuple(
        (coordinate_index(s, row, s), coordinate_index(s, row + 1, 0))
        for row in range(rows - 1)
    )
    shell = FingerprintSeed(s, rows, labels, cells, tuple(), cells[0][0], cells[14][0], pairs)
    seed = FingerprintSeed(s, rows, labels, cells, _adjacency(shell, tuple(range(5))), shell.entrance, shell.exit, pairs)
    validate_seed(seed)
    return seed



def validate_matrix(matrix: Matrix, size: int) -> None:
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise CoordinateFingerprintError("matrix dimensions changed")
    for left in range(size):
        for right in range(size):
            value = matrix[left][right]
            if type(value) is not Fraction or value < 0:
                raise CoordinateFingerprintError("weights must be nonnegative exact Fractions")
            if left == right and value:
                raise CoordinateFingerprintError("self-loops are forbidden")
            if value != matrix[right][left]:
                raise CoordinateFingerprintError("matrix must be symmetric")


def validate_seed_shape(seed: FingerprintSeed) -> None:
    if not isinstance(seed, FingerprintSeed) or (seed.s, seed.rows) not in GRIDS:
        raise CoordinateFingerprintError("seed type or grid changed")
    expected_labels: tuple[Label, ...] = tuple(
        (row, column) for row in range(seed.rows) for column in range(seed.s + 1)
    ) + (HUB_LABEL,)
    if seed.labels != expected_labels or seed.cells != _declared_cells(seed.s, seed.rows):
        raise CoordinateFingerprintError("labels or 15-cell partition changed")
    flat = tuple(vertex for cell in seed.cells for vertex in cell)
    if len(seed.cells) != 15 or seed.size <= len(seed.cells):
        raise CoordinateFingerprintError("partition must be a strict 15-cell compression")
    if sorted(flat) != list(range(seed.size)) or len(set(flat)) != seed.size:
        raise CoordinateFingerprintError("cells must cover each vertex exactly once")
    expected_p = seed.rows * (seed.s + 1) // 2 - 1
    if seed.g != 5 or seed.p != expected_p or seed.h != expected_p - 5 or seed.h <= 0:
        raise CoordinateFingerprintError("channel counts changed")
    if seed.matched_weight != seed.h + 90:
        raise CoordinateFingerprintError("fixed matched weight changed")
    if seed.entrance != coordinate_index(seed.s, 0, 0) or seed.exit != coordinate_index(seed.s, seed.rows - 1, seed.s):
        raise CoordinateFingerprintError("endpoints changed")


def validate_candidate(seed: FingerprintSeed) -> None:
    validate_matrix(seed.adjacency, seed.size)
    if seed.adjacency != _adjacency(seed, tuple(range(5))):
        raise CoordinateFingerprintError("candidate edges or weights changed")
    expected_pairs = tuple(
        (coordinate_index(seed.s, row, seed.s), coordinate_index(seed.s, row + 1, 0))
        for row in range(seed.rows - 1)
    )
    if seed.genuine_pairs != expected_pairs:
        raise CoordinateFingerprintError("genuine pair metadata changed")
    if seed.adjacency[seed.exit][seed.entrance]:
        raise CoordinateFingerprintError("false periodic edge is forbidden")
    seen = {seed.entrance}
    pending = [seed.entrance]
    while pending:
        vertex = pending.pop()
        for neighbour, weight in enumerate(seed.adjacency[vertex]):
            if weight and neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    if len(seen) != seed.size:
        raise CoordinateFingerprintError("candidate must be connected")


def quotient_matrix(seed: FingerprintSeed, adjacency: Matrix | None = None) -> Matrix:
    matrix = seed.adjacency if adjacency is None else adjacency
    validate_matrix(matrix, seed.size)
    signatures: list[tuple[Fraction, ...]] = []
    cell_of = {vertex: index for index, cell in enumerate(seed.cells) for vertex in cell}
    for cell in seed.cells:
        first: tuple[Fraction, ...] | None = None
        for vertex in cell:
            signature = tuple(
                sum((matrix[vertex][target] for target in targets), Fraction(0))
                for targets in seed.cells
            )
            if first is None:
                first = signature
            elif signature != first:
                raise CoordinateFingerprintError("partition is not exactly equitable")
        if first is None:
            raise CoordinateFingerprintError("quotient cell is empty")
        signatures.append(first)
    quotient = tuple(signatures)
    for vertex in range(seed.size):
        for target_cell, targets in enumerate(seed.cells):
            actual = sum((matrix[vertex][target] for target in targets), Fraction(0))
            if actual != quotient[cell_of[vertex]][target_cell]:
                raise CoordinateFingerprintError("exact HP=PB closure failed")
    return quotient


def expected_candidate_quotient(seed: FingerprintSeed) -> Matrix:
    result = [[Fraction(0) for _ in range(15)] for _ in range(15)]
    result[0][1] = result[1][0] = Fraction(1)
    for position, factor in enumerate(FINGERPRINTS):
        source_cell = 2 + position
        destination_cell = 8 + position
        result[1][source_cell] = Fraction(factor)
        result[source_cell][1] = Fraction(factor)
        result[source_cell][destination_cell] = Fraction(seed.matched_weight)
        result[destination_cell][source_cell] = Fraction(seed.matched_weight)
        result[destination_cell][14] = Fraction(factor)
        result[14][destination_cell] = Fraction(factor)
    result[1][7] = Fraction(seed.h)
    result[7][1] = Fraction(1)
    result[7][13] = result[13][7] = Fraction(seed.matched_weight)
    result[13][14] = Fraction(1)
    result[14][13] = Fraction(seed.h)
    return tuple(tuple(row) for row in result)


def validate_quotient(seed: FingerprintSeed) -> Matrix:
    quotient = quotient_matrix(seed)
    if quotient != expected_candidate_quotient(seed):
        raise CoordinateFingerprintError("candidate quotient changed")
    return quotient


def validate_chiral(seed: FingerprintSeed, adjacency: Matrix | None = None) -> None:
    matrix = seed.adjacency if adjacency is None else adjacency
    positive_cells = {0, 2, 3, 4, 5, 6, 7, 14}
    signs = [0] * seed.size
    for index, cell in enumerate(seed.cells):
        for vertex in cell:
            signs[vertex] = 1 if index in positive_cells else -1
    if signs.count(1) - signs.count(-1) != 1:
        raise CoordinateFingerprintError("sublattice imbalance must be one")
    for left, row in enumerate(matrix):
        for right, weight in enumerate(row):
            if signs[left] * weight * signs[right] != -weight:
                raise CoordinateFingerprintError("exact chiral symmetry failed")



def matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> tuple[Fraction, ...]:
    if len(matrix) != len(vector):
        raise CoordinateFingerprintError("matrix-vector dimensions differ")
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def exact_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    values = [[Fraction(value) for value in row] for row in matrix]
    columns = len(values[0]) if values else 0
    if any(len(row) != columns for row in values):
        raise CoordinateFingerprintError("rank input must be rectangular")
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, len(values)) if values[row][column]), None)
        if pivot is None:
            continue
        values[rank], values[pivot] = values[pivot], values[rank]
        divisor = values[rank][column]
        values[rank] = [value / divisor for value in values[rank]]
        for row in range(len(values)):
            if row == rank:
                continue
            factor = values[row][column]
            if factor:
                values[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(values[row], values[rank], strict=True)
                ]
        rank += 1
        if rank == len(values):
            break
    return rank


def candidate_zero_vector(seed: FingerprintSeed) -> tuple[Fraction, ...]:
    vector = [Fraction(0) for _ in range(seed.size)]
    vector[seed.entrance] = -Fraction(seed.matched_weight)
    vector[seed.exit] = -Fraction(seed.matched_weight)
    for position, source in enumerate(source_vertices(seed)):
        vector[source] = Fraction(channel_factor(seed, position))
    return tuple(vector)


def control_correlation(seed: FingerprintSeed, permutation: Sequence[int]) -> Fraction:
    genuine = validate_permutation(permutation)
    return Fraction(seed.h + sum(FINGERPRINTS[index] * FINGERPRINTS[genuine[index]] for index in range(seed.g)))


def control_zero_vector(seed: FingerprintSeed, permutation: Sequence[int]) -> tuple[Fraction, ...]:
    genuine = validate_permutation(permutation)
    full_matching = genuine + tuple(range(seed.g, seed.p))
    vector = [Fraction(0) for _ in range(seed.size)]
    vector[seed.entrance] = -control_correlation(seed, genuine)
    vector[seed.exit] = -Fraction(seed.matched_weight)
    for source_position, destination_position in enumerate(full_matching):
        vector[source_vertices(seed)[source_position]] = Fraction(channel_factor(seed, destination_position))
    return tuple(vector)


def off_diagonal_and_gram(seed: FingerprintSeed) -> tuple[Matrix, Matrix]:
    positive = (seed.entrance,) + source_vertices(seed) + (seed.exit,)
    negative = (seed.cells[1][0],) + destination_vertices(seed)
    block = tuple(tuple(seed.adjacency[left][right] for right in negative) for left in positive)
    gram = tuple(tuple(
        sum((block[row][left] * block[row][right] for row in range(len(block))), Fraction(0))
        for right in range(len(negative))
    ) for left in range(len(negative)))
    return block, gram


def exact_ldlt_pivots(matrix: Matrix) -> tuple[Fraction, ...]:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise CoordinateFingerprintError("LDL input must be nonempty and square")
    if any(matrix[left][right] != matrix[right][left] for left in range(size) for right in range(size)):
        raise CoordinateFingerprintError("LDL input must be symmetric")
    lower = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    pivots = [Fraction(0) for _ in range(size)]
    for row in range(size):
        lower[row][row] = Fraction(1)
        pivots[row] = matrix[row][row] - sum(
            (lower[row][index] ** 2 * pivots[index] for index in range(row)), Fraction(0)
        )
        if pivots[row] == 0:
            raise CoordinateFingerprintError("LDL encountered a zero pivot")
        for target in range(row + 1, size):
            numerator = matrix[target][row] - sum(
                (lower[target][index] * lower[row][index] * pivots[index] for index in range(row)),
                Fraction(0),
            )
            lower[target][row] = numerator / pivots[row]
    return tuple(pivots)


def require_positive_ldlt(matrix: Matrix) -> tuple[Fraction, ...]:
    pivots = exact_ldlt_pivots(matrix)
    if any(pivot <= 0 for pivot in pivots):
        raise CoordinateFingerprintError("exact LDL certificate is not positive definite")
    return pivots


def validate_candidate_zero_rank_gap(seed: FingerprintSeed) -> tuple[int, int, Fraction, Fraction, tuple[Fraction, ...]]:
    vector = candidate_zero_vector(seed)
    if matrix_vector(seed.adjacency, vector) != (Fraction(0),) * seed.size:
        raise CoordinateFingerprintError("candidate vector is not an exact zero mode")
    block, gram = off_diagonal_and_gram(seed)
    block_rank = exact_rank(block)
    if block_rank != seed.p + 1:
        raise CoordinateFingerprintError("off-diagonal block lacks full column rank")
    nullity = seed.size - exact_rank(seed.adjacency)
    if nullity != 1:
        raise CoordinateFingerprintError("full nullity must be one")
    norm = sum((value * value for value in vector), Fraction(0))
    expected_norm = Fraction(seed.matched_weight * (2 * seed.matched_weight + 1))
    projector = abs(vector[seed.entrance] * vector[seed.exit]) / norm
    expected_projector = Fraction(seed.matched_weight, 2 * seed.matched_weight + 1)
    if norm != expected_norm or projector != expected_projector:
        raise CoordinateFingerprintError("candidate endpoint projector formulas failed")
    shifted = tuple(tuple(
        gram[row][column] - (Fraction(1) if row == column else Fraction(0))
        for column in range(len(gram))
    ) for row in range(len(gram)))
    pivots = require_positive_ldlt(shifted)
    return nullity, block_rank, norm, projector, pivots


def numerical_gap(seed: FingerprintSeed, exact_nullity: int) -> float:
    if exact_nullity != 1 or seed.size - exact_rank(seed.adjacency) != 1:
        raise CoordinateFingerprintError("exact nullity must precede numerical diagnosis")
    import numpy as np
    dense = np.array([[float(value) for value in row] for row in seed.adjacency], dtype=np.float64)
    values = np.linalg.eigvalsh(dense)
    if not bool(np.all(np.isfinite(values))) or int(np.count_nonzero(np.abs(values) <= ZERO_TOLERANCE)) != 1:
        raise CoordinateFingerprintError("numerical spectrum disagrees with exact certificate")
    gap = float(np.min(np.abs(values[np.abs(values) > ZERO_TOLERANCE])))
    if not math.isfinite(gap) or gap <= 1.0 + GAP_TOLERANCE:
        raise CoordinateFingerprintError("numerical gap violates exact >1 certificate")
    return gap



def endpoint_moment(matrix: Matrix, entrance: int, exit_state: int, power: int) -> Fraction:
    if type(power) is not int or power < 0:
        raise CoordinateFingerprintError("moment power must be a nonnegative exact integer")
    state = tuple(Fraction(1) if vertex == entrance else Fraction(0) for vertex in range(len(matrix)))
    for _ in range(power):
        state = matrix_vector(matrix, state)
    return state[exit_state]


def weighted_degrees(matrix: Matrix) -> tuple[Fraction, ...]:
    return tuple(sum(row, Fraction(0)) for row in matrix)


def edge_weight_multiset(matrix: Matrix) -> tuple[Fraction, ...]:
    return tuple(sorted(
        matrix[left][right]
        for left in range(len(matrix))
        for right in range(left + 1, len(matrix))
        if matrix[left][right]
    ))


def edge_degree_profile(matrix: Matrix) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    degrees = weighted_degrees(matrix)
    return tuple(sorted(
        (matrix[left][right], min(degrees[left], degrees[right]), max(degrees[left], degrees[right]))
        for left in range(len(matrix))
        for right in range(left + 1, len(matrix))
        if matrix[left][right]
    ))


def control_adjacency(seed: FingerprintSeed, permutation: Sequence[int]) -> Matrix:
    return _adjacency(seed, validate_permutation(permutation))


def control_certificate(
    seed: FingerprintSeed,
    permutation: Sequence[int],
    control_override: Matrix | None = None,
    claimed_fourth_moment: Fraction | None = None,
) -> ControlCertificate:
    genuine = validate_permutation(permutation)
    if genuine == tuple(range(seed.g)):
        raise CoordinateFingerprintError("control must be a nonidentity genuine permutation")
    expected = control_adjacency(seed, genuine)
    control = expected if control_override is None else control_override
    validate_matrix(control, seed.size)
    if control != expected:
        raise CoordinateFingerprintError("control does not match its declared permutation")
    fair_weights = edge_weight_multiset(seed.adjacency) == edge_weight_multiset(control)
    fair_degrees = weighted_degrees(seed.adjacency) == weighted_degrees(control)
    if not fair_weights or not fair_degrees:
        raise CoordinateFingerprintError("control fairness invariants failed")
    profile_differs = edge_degree_profile(seed.adjacency) != edge_degree_profile(control)
    if not profile_differs:
        raise CoordinateFingerprintError("control did not break coordinate isomorphism")
    correlation = control_correlation(seed, genuine)
    displacement = Fraction(sum(
        (FINGERPRINTS[index] - FINGERPRINTS[genuine[index]]) ** 2
        for index in range(seed.g)
    ), 2)
    if Fraction(seed.matched_weight) - correlation != displacement or displacement <= 0:
        raise CoordinateFingerprintError("rearrangement identity failed")
    candidate_moment = Fraction(seed.matched_weight * seed.matched_weight)
    control_moment = endpoint_moment(control, seed.entrance, seed.exit, 4)
    expected_moment = Fraction(seed.matched_weight) * correlation
    if control_moment != expected_moment:
        raise CoordinateFingerprintError("control fourth-moment formula failed")
    if claimed_fourth_moment is not None:
        if type(claimed_fourth_moment) is not Fraction or claimed_fourth_moment != control_moment:
            raise CoordinateFingerprintError("claimed fourth moment is inexact or false")
    difference = candidate_moment - control_moment
    if difference != Fraction(seed.matched_weight) * displacement or difference <= 0:
        raise CoordinateFingerprintError("strict fingerprint moment separation failed")
    zero = control_zero_vector(seed, genuine)
    if matrix_vector(control, zero) != (Fraction(0),) * seed.size:
        raise CoordinateFingerprintError("control zero vector failed")
    norm = sum((value * value for value in zero), Fraction(0))
    expected_norm = correlation * correlation + seed.matched_weight + seed.matched_weight ** 2
    if norm != expected_norm:
        raise CoordinateFingerprintError("control zero norm formula failed")
    entrance_weight = zero[seed.entrance] ** 2 / norm
    exit_weight = zero[seed.exit] ** 2 / norm
    projector = abs(zero[seed.entrance] * zero[seed.exit]) / norm
    return ControlCertificate(
        permutation=genuine,
        correlation=correlation,
        displacement_energy=displacement,
        fair_weight_multiset=fair_weights,
        fair_vertex_weighted_degrees=fair_degrees,
        edge_degree_profile_differs=profile_differs,
        candidate_fourth_moment=candidate_moment,
        control_fourth_moment=control_moment,
        moment_difference=difference,
        zero_norm_squared=norm,
        entrance_weight=entrance_weight,
        exit_weight=exit_weight,
        zero_projector_endpoint_element=projector,
    )


def validate_seed(seed: FingerprintSeed) -> StructuralCertificate:
    validate_seed_shape(seed)
    validate_candidate(seed)
    quotient = validate_quotient(seed)
    validate_chiral(seed)
    nullity, block_rank, norm, projector, pivots = validate_candidate_zero_rank_gap(seed)
    candidate_moment = endpoint_moment(seed.adjacency, seed.entrance, seed.exit, 4)
    if candidate_moment != Fraction(seed.matched_weight * seed.matched_weight):
        raise CoordinateFingerprintError("candidate fourth-moment formula failed")
    gap = numerical_gap(seed, nullity)
    controls = all_genuine_permutations()
    if len(controls) != 119:
        raise CoordinateFingerprintError("control family must exhaust 119 permutations")
    for permutation in controls:
        control_certificate(seed, permutation)
    return StructuralCertificate(
        quotient=quotient,
        exact_nullity=nullity,
        off_diagonal_rank=block_rank,
        norm_squared=norm,
        endpoint_weight=projector,
        zero_projector_endpoint_element=projector,
        ldlt_pivots=pivots,
        candidate_fourth_moment=candidate_moment,
        numerical_gap=gap,
        controls_checked=len(controls),
    )