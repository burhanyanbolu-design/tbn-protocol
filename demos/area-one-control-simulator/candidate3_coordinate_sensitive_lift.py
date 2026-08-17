#!/usr/bin/env python3
"""Exact structural algebra for the coordinate-sensitive Candidate 3 lift."""

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


class CoordinateSensitiveError(ValueError):
    """Raised when a coordinate-sensitive structural certificate fails."""


@dataclass(frozen=True)
class CoordinateSensitiveSeed:
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
        return len(self.cells[2])

    @property
    def h(self) -> int:
        return len(self.cells[3])

    @property
    def p(self) -> int:
        return self.g + self.h

    @property
    def balance(self) -> int:
        return 4 * self.g + self.h


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


@dataclass(frozen=True)
class ControlCertificate:
    cross_count: int
    fair_weight_multiset: bool
    fair_vertex_weighted_degrees: bool
    candidate_edge_degree_profile: tuple[tuple[Fraction, Fraction, Fraction], ...]
    control_edge_degree_profile: tuple[tuple[Fraction, Fraction, Fraction], ...]
    edge_degree_profile_differs: bool
    candidate_fourth_moment: Fraction
    control_fourth_moment: Fraction
    moment_difference: Fraction


def coordinate_index(s: int, row: int, column: int) -> int:
    if type(s) is not int or type(row) is not int or type(column) is not int:
        raise CoordinateSensitiveError("coordinates and s must be exact integers")
    if s < 1 or row < 0 or column < 0 or column > s:
        raise CoordinateSensitiveError("coordinate is outside the EOG grid")
    return row * (s + 1) + column


def _zero_matrix(size: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(size)] for _ in range(size)]


def _add_edge(
    adjacency: list[list[Fraction]], left: int, right: int, weight: Fraction,
) -> None:
    if left == right or type(weight) is not Fraction or weight <= 0:
        raise CoordinateSensitiveError("edges must have exact positive weight and no loop")
    if adjacency[left][right] != 0 or adjacency[right][left] != 0:
        raise CoordinateSensitiveError("duplicate edge")
    adjacency[left][right] = weight
    adjacency[right][left] = weight


def _declared_cells(s: int, rows: int) -> tuple[tuple[int, ...], ...]:
    coordinate_count = rows * (s + 1)
    entrance = coordinate_index(s, 0, 0)
    exit_state = coordinate_index(s, rows - 1, s)
    genuine_sources = tuple(coordinate_index(s, row, s) for row in range(rows - 1))
    genuine_destinations = tuple(coordinate_index(s, row + 1, 0) for row in range(rows - 1))
    reserved = {entrance, exit_state, *genuine_sources, *genuine_destinations}
    unused = tuple(index for index in range(coordinate_count) if index not in reserved)
    if len(unused) % 2:
        raise CoordinateSensitiveError("unused coordinates must split evenly")
    half = len(unused) // 2
    return (
        (entrance,),
        (coordinate_count,),
        genuine_sources,
        unused[:half],
        genuine_destinations,
        unused[half:],
        (exit_state,),
    )


def _source_vertices(seed: CoordinateSensitiveSeed) -> tuple[int, ...]:
    return seed.cells[2] + seed.cells[3]


def _destination_vertices(seed: CoordinateSensitiveSeed) -> tuple[int, ...]:
    return seed.cells[4] + seed.cells[5]


def source_factor(seed: CoordinateSensitiveSeed, position: int) -> int:
    if type(position) is not int or not 0 <= position < seed.p:
        raise CoordinateSensitiveError("source position is invalid")
    return 2 if position < seed.g else 1


def destination_factor(seed: CoordinateSensitiveSeed, position: int) -> int:
    if type(position) is not int or not 0 <= position < seed.p:
        raise CoordinateSensitiveError("destination position is invalid")
    return 2 if position < seed.g else 1


def validate_permutation(
    seed: CoordinateSensitiveSeed, permutation: Sequence[int],
) -> tuple[int, ...]:
    values = tuple(permutation)
    if any(type(value) is not int for value in values):
        raise CoordinateSensitiveError("permutation entries must be exact integers")
    if len(values) != seed.p or sorted(values) != list(range(seed.p)):
        raise CoordinateSensitiveError("matching must be a bijection of all channels")
    return values


def _adjacency_for_permutation(
    seed: CoordinateSensitiveSeed, permutation: Sequence[int],
) -> Matrix:
    matching = validate_permutation(seed, permutation)
    sources = _source_vertices(seed)
    destinations = _destination_vertices(seed)
    adjacency = _zero_matrix(seed.size)
    _add_edge(adjacency, seed.cells[0][0], seed.cells[1][0], Fraction(1))
    for position, vertex in enumerate(sources):
        _add_edge(
            adjacency, seed.cells[1][0], vertex, Fraction(source_factor(seed, position))
        )
    for source_position, destination_position in enumerate(matching):
        _add_edge(
            adjacency,
            sources[source_position],
            destinations[destination_position],
            Fraction(seed.balance),
        )
    for position, vertex in enumerate(destinations):
        _add_edge(
            adjacency, vertex, seed.cells[6][0], Fraction(destination_factor(seed, position))
        )
    return tuple(tuple(row) for row in adjacency)


def build_seed(s: int, rows: int = 6) -> CoordinateSensitiveSeed:
    if type(s) is not int or type(rows) is not int or (s, rows) not in GRIDS:
        raise CoordinateSensitiveError("only declared structural grids are allowed")
    coordinate_count = rows * (s + 1)
    labels: tuple[Label, ...] = tuple(
        (row, column) for row in range(rows) for column in range(s + 1)
    ) + (HUB_LABEL,)
    cells = _declared_cells(s, rows)
    genuine_pairs = tuple(
        (coordinate_index(s, row, s), coordinate_index(s, row + 1, 0))
        for row in range(rows - 1)
    )
    shell = CoordinateSensitiveSeed(
        s=s,
        rows=rows,
        labels=labels,
        cells=cells,
        adjacency=tuple(),
        entrance=cells[0][0],
        exit=cells[6][0],
        genuine_pairs=genuine_pairs,
    )
    seed = CoordinateSensitiveSeed(
        s=s,
        rows=rows,
        labels=labels,
        cells=cells,
        adjacency=_adjacency_for_permutation(shell, tuple(range(shell.p))),
        entrance=shell.entrance,
        exit=shell.exit,
        genuine_pairs=genuine_pairs,
    )
    validate_seed(seed)
    return seed


def validate_coordinates_and_cells(seed: CoordinateSensitiveSeed) -> None:
    if not isinstance(seed, CoordinateSensitiveSeed) or (seed.s, seed.rows) not in GRIDS:
        raise CoordinateSensitiveError("seed type or grid is invalid")
    expected_labels: tuple[Label, ...] = tuple(
        (row, column)
        for row in range(seed.rows)
        for column in range(seed.s + 1)
    ) + (HUB_LABEL,)
    if seed.labels != expected_labels or len(set(seed.labels)) != seed.size:
        raise CoordinateSensitiveError("coordinate and hub labels changed")
    expected_cells = _declared_cells(seed.s, seed.rows)
    if seed.cells != expected_cells:
        raise CoordinateSensitiveError("coordinate-role cells changed")
    flattened = tuple(vertex for cell in seed.cells for vertex in cell)
    if sorted(flattened) != list(range(seed.size)) or len(set(flattened)) != seed.size:
        raise CoordinateSensitiveError("cells must cover every vertex exactly once")
    expected_p = seed.rows * (seed.s + 1) // 2 - 1
    if seed.g != seed.rows - 1 or seed.p != expected_p or seed.h != expected_p - seed.g:
        raise CoordinateSensitiveError("role counts changed")
    if seed.h <= 0 or tuple(map(len, seed.cells)) != (1, 1, seed.g, seed.h, seed.g, seed.h, 1):
        raise CoordinateSensitiveError("seven-cell sizes changed")
    if seed.balance != seed.p + 3 * seed.g:
        raise CoordinateSensitiveError("fixed balance scale changed")
    if seed.entrance != coordinate_index(seed.s, 0, 0):
        raise CoordinateSensitiveError("entrance changed")
    if seed.exit != coordinate_index(seed.s, seed.rows - 1, seed.s):
        raise CoordinateSensitiveError("exit changed")


def validate_matrix(adjacency: Matrix, size: int) -> None:
    if len(adjacency) != size or any(len(row) != size for row in adjacency):
        raise CoordinateSensitiveError("adjacency dimensions changed")
    for left in range(size):
        for right in range(size):
            weight = adjacency[left][right]
            if type(weight) is not Fraction:
                raise CoordinateSensitiveError("weights must be exact Fractions")
            if weight < 0:
                raise CoordinateSensitiveError("negative weights are forbidden")
            if left == right and weight:
                raise CoordinateSensitiveError("self-loops are forbidden")
            if weight != adjacency[right][left]:
                raise CoordinateSensitiveError("adjacency must be symmetric")


def validate_declared_candidate(seed: CoordinateSensitiveSeed) -> None:
    validate_matrix(seed.adjacency, seed.size)
    expected = _adjacency_for_permutation(seed, tuple(range(seed.p)))
    if seed.adjacency != expected:
        raise CoordinateSensitiveError("candidate edge set or fixed weights changed")
    expected_pairs = tuple(
        (coordinate_index(seed.s, row, seed.s), coordinate_index(seed.s, row + 1, 0))
        for row in range(seed.rows - 1)
    )
    if seed.genuine_pairs != expected_pairs or len(expected_pairs) != 5:
        raise CoordinateSensitiveError("genuine overlap metadata changed")
    for left, right in expected_pairs:
        if seed.adjacency[left][right] != Fraction(seed.balance):
            raise CoordinateSensitiveError("genuine edge weight changed")
    if seed.adjacency[seed.exit][seed.entrance] != 0:
        raise CoordinateSensitiveError("false periodic overlap edge is forbidden")
    seen = {seed.entrance}
    pending = [seed.entrance]
    while pending:
        vertex = pending.pop()
        for neighbour, weight in enumerate(seed.adjacency[vertex]):
            if weight > 0 and neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    if len(seen) != seed.size:
        raise CoordinateSensitiveError("candidate must be connected")


def expected_quotient(seed: CoordinateSensitiveSeed) -> Matrix:
    g = Fraction(seed.g)
    h = Fraction(seed.h)
    scale = Fraction(seed.balance)
    return tuple(tuple(Fraction(value) for value in row) for row in (
        (0, 1, 0, 0, 0, 0, 0),
        (1, 0, 2 * g, h, 0, 0, 0),
        (0, 2, 0, 0, scale, 0, 0),
        (0, 1, 0, 0, 0, scale, 0),
        (0, 0, scale, 0, 0, 0, 2),
        (0, 0, 0, scale, 0, 0, 1),
        (0, 0, 0, 0, 2 * g, h, 0),
    ))


def quotient_matrix(seed: CoordinateSensitiveSeed) -> Matrix:
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
                raise CoordinateSensitiveError("seven-cell partition is not exactly equitable")
        if first is None:
            raise CoordinateSensitiveError("quotient cell is empty")
        signatures.append(first)
    quotient = tuple(signatures)
    for vertex in range(seed.size):
        for target_cell, targets in enumerate(seed.cells):
            hp = sum((seed.adjacency[vertex][target] for target in targets), Fraction(0))
            if hp != quotient[cell_of[vertex]][target_cell]:
                raise CoordinateSensitiveError("exact H P = P B closure failed")
    return quotient


def validate_quotient(seed: CoordinateSensitiveSeed) -> Matrix:
    quotient = quotient_matrix(seed)
    if quotient != expected_quotient(seed):
        raise CoordinateSensitiveError("directional seven-cell quotient changed")
    return quotient


def validate_chiral(seed: CoordinateSensitiveSeed) -> None:
    signs = [0] * seed.size
    for cell_index, cell in enumerate(seed.cells):
        sign = 1 if cell_index in (0, 2, 3, 6) else -1
        for vertex in cell:
            signs[vertex] = sign
    if signs.count(1) - signs.count(-1) != 1:
        raise CoordinateSensitiveError("sublattice imbalance must be one")
    for left, row in enumerate(seed.adjacency):
        for right, weight in enumerate(row):
            if signs[left] * weight * signs[right] != -weight:
                raise CoordinateSensitiveError("Gamma H Gamma = -H failed exactly")


def _rref(matrix: Sequence[Sequence[Fraction]]) -> tuple[list[list[Fraction]], tuple[int, ...]]:
    values = [[Fraction(value) for value in row] for row in matrix]
    column_count = len(values[0]) if values else 0
    if any(len(row) != column_count for row in values):
        raise CoordinateSensitiveError("matrix must be rectangular")
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


def zero_vector(seed: CoordinateSensitiveSeed) -> tuple[Fraction, ...]:
    values = (
        -Fraction(seed.balance),
        Fraction(0),
        Fraction(2),
        Fraction(1),
        Fraction(0),
        Fraction(0),
        -Fraction(seed.balance),
    )
    vector = [Fraction(0) for _ in range(seed.size)]
    for cell, value in zip(seed.cells, values, strict=True):
        for vertex in cell:
            vector[vertex] = value
    return tuple(vector)


def matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> tuple[Fraction, ...]:
    if len(vector) != len(matrix):
        raise CoordinateSensitiveError("matrix-vector dimensions differ")
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def _off_diagonal_and_gram(seed: CoordinateSensitiveSeed) -> tuple[Matrix, Matrix]:
    positive = seed.cells[0] + seed.cells[2] + seed.cells[3] + seed.cells[6]
    negative = seed.cells[1] + seed.cells[4] + seed.cells[5]
    off_diagonal = tuple(
        tuple(seed.adjacency[vertex][neighbour] for neighbour in negative)
        for vertex in positive
    )
    gram = tuple(tuple(
        sum(
            (off_diagonal[row][left] * off_diagonal[row][right] for row in range(len(positive))),
            Fraction(0),
        )
        for right in range(len(negative))
    ) for left in range(len(negative)))
    return off_diagonal, gram


def exact_ldlt_pivots(matrix: Matrix) -> tuple[Fraction, ...]:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise CoordinateSensitiveError("LDL input must be nonempty and square")
    if any(matrix[left][right] != matrix[right][left] for left in range(size) for right in range(size)):
        raise CoordinateSensitiveError("LDL input must be symmetric")
    lower = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    pivots = [Fraction(0) for _ in range(size)]
    for row in range(size):
        lower[row][row] = Fraction(1)
        pivot = matrix[row][row] - sum(
            (lower[row][index] ** 2 * pivots[index] for index in range(row)),
            Fraction(0),
        )
        if pivot == 0:
            raise CoordinateSensitiveError("LDL encountered a zero pivot")
        pivots[row] = pivot
        for target in range(row + 1, size):
            numerator = matrix[target][row] - sum(
                (
                    lower[target][index]
                    * lower[row][index]
                    * pivots[index]
                    for index in range(row)
                ),
                Fraction(0),
            )
            lower[target][row] = numerator / pivot
    return tuple(pivots)


def require_positive_ldlt(matrix: Matrix) -> tuple[Fraction, ...]:
    pivots = exact_ldlt_pivots(matrix)
    if any(pivot <= 0 for pivot in pivots):
        raise CoordinateSensitiveError("exact LDL certificate is not positive definite")
    return pivots


def validate_zero_rank_and_gap(
    seed: CoordinateSensitiveSeed,
    candidate_vector: Sequence[Fraction] | None = None,
) -> tuple[int, int, Fraction, Fraction, tuple[Fraction, ...]]:
    vector = zero_vector(seed) if candidate_vector is None else tuple(candidate_vector)
    if len(vector) != seed.size or any(type(value) is not Fraction for value in vector):
        raise CoordinateSensitiveError("zero mode must be an exact full-length Fraction vector")
    if any(value != 0 for value in matrix_vector(seed.adjacency, vector)):
        raise CoordinateSensitiveError("declared coordinate-sensitive vector is not a zero mode")
    if vector[seed.entrance] != vector[seed.exit] or vector[seed.entrance] == 0:
        raise CoordinateSensitiveError("zero-mode endpoints are not balanced and nonzero")
    off_diagonal, gram = _off_diagonal_and_gram(seed)
    off_rank = exact_rank(off_diagonal)
    if off_rank != seed.p + 1:
        raise CoordinateSensitiveError("off-diagonal block lacks full column rank")
    nullity = seed.size - exact_rank(seed.adjacency)
    if nullity != 1:
        raise CoordinateSensitiveError("full Hamiltonian nullity must be one")
    norm_squared = sum((value * value for value in vector), Fraction(0))
    expected_norm = Fraction(seed.balance * (2 * seed.balance + 1))
    if norm_squared != expected_norm:
        raise CoordinateSensitiveError("zero-mode norm formula failed")
    endpoint_weight = vector[seed.entrance] ** 2 / norm_squared
    projector_element = abs(vector[seed.entrance] * vector[seed.exit]) / norm_squared
    expected_endpoint = Fraction(seed.balance, 2 * seed.balance + 1)
    if endpoint_weight != expected_endpoint or projector_element != expected_endpoint:
        raise CoordinateSensitiveError("endpoint projector formula failed")
    shifted = tuple(tuple(
        gram[row][column] - (Fraction(1) if row == column else Fraction(0))
        for column in range(len(gram))
    ) for row in range(len(gram)))
    pivots = require_positive_ldlt(shifted)
    return nullity, off_rank, norm_squared, projector_element, pivots


def numerical_gap(seed: CoordinateSensitiveSeed, exact_nullity: int) -> float:
    if exact_nullity != 1 or seed.size - exact_rank(seed.adjacency) != 1:
        raise CoordinateSensitiveError("exact nullity must precede numerical diagnosis")
    import numpy as np

    dense = np.array([[float(value) for value in row] for row in seed.adjacency], dtype=np.float64)
    eigenvalues = np.linalg.eigvalsh(dense)
    if not bool(np.all(np.isfinite(eigenvalues))):
        raise CoordinateSensitiveError("numerical spectrum contains nonfinite values")
    zeros = eigenvalues[np.abs(eigenvalues) <= ZERO_TOLERANCE]
    if len(zeros) != 1:
        raise CoordinateSensitiveError("numerical zero count disagrees with exact nullity")
    nonzero = np.abs(eigenvalues[np.abs(eigenvalues) > ZERO_TOLERANCE])
    gap = float(nonzero.min()) if len(nonzero) else 0.0
    if not math.isfinite(gap) or gap <= 1.0 + GAP_TOLERANCE:
        raise CoordinateSensitiveError("numerical gap does not respect the exact >1 certificate")
    return gap


def endpoint_moment(
    adjacency: Matrix, entrance: int, exit_state: int, power: int,
) -> Fraction:
    if type(power) is not int or power < 0:
        raise CoordinateSensitiveError("moment power must be a nonnegative exact integer")
    state = tuple(
        Fraction(1) if vertex == entrance else Fraction(0)
        for vertex in range(len(adjacency))
    )
    for _ in range(power):
        state = matrix_vector(adjacency, state)
    return state[exit_state]


def expected_candidate_fourth_moment(seed: CoordinateSensitiveSeed) -> Fraction:
    return Fraction(seed.balance * seed.balance)


def validate_candidate_fourth_moment(seed: CoordinateSensitiveSeed) -> Fraction:
    for power in range(4):
        if endpoint_moment(seed.adjacency, seed.entrance, seed.exit, power) != 0:
            raise CoordinateSensitiveError("endpoint moment appeared before graph distance four")
    moment = endpoint_moment(seed.adjacency, seed.entrance, seed.exit, 4)
    if moment != expected_candidate_fourth_moment(seed):
        raise CoordinateSensitiveError("candidate fourth-moment formula failed")
    return moment


def weighted_degrees(adjacency: Matrix) -> tuple[Fraction, ...]:
    """Return each vertex's weighted degree in stable vertex order."""
    return tuple(sum(row, Fraction(0)) for row in adjacency)


def edge_degree_profile(adjacency: Matrix) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    degrees = tuple(sum(row, Fraction(0)) for row in adjacency)
    return tuple(sorted(
        (
            adjacency[left][right],
            min(degrees[left], degrees[right]),
            max(degrees[left], degrees[right]),
        )
        for left in range(len(adjacency))
        for right in range(left + 1, len(adjacency))
        if adjacency[left][right] != 0
    ))


def edge_weight_multiset(adjacency: Matrix) -> tuple[Fraction, ...]:
    return tuple(sorted(
        adjacency[left][right]
        for left in range(len(adjacency))
        for right in range(left + 1, len(adjacency))
        if adjacency[left][right] != 0
    ))


def canonical_cross_permutation(seed: CoordinateSensitiveSeed, cross_count: int) -> tuple[int, ...]:
    if type(cross_count) is not int or not 1 <= cross_count <= min(seed.g, seed.h):
        raise CoordinateSensitiveError("cross count is outside the declared nonzero range")
    permutation = list(range(seed.p))
    for offset in range(cross_count):
        genuine = offset
        support = seed.g + offset
        permutation[genuine], permutation[support] = support, genuine
    return tuple(permutation)


def matching_cross_count(seed: CoordinateSensitiveSeed, permutation: Sequence[int]) -> int:
    matching = validate_permutation(seed, permutation)
    genuine_to_support = sum(
        source < seed.g and destination >= seed.g
        for source, destination in enumerate(matching)
    )
    support_to_genuine = sum(
        source >= seed.g and destination < seed.g
        for source, destination in enumerate(matching)
    )
    if genuine_to_support != support_to_genuine:
        raise CoordinateSensitiveError("bijection cross counts are inconsistent")
    return genuine_to_support


def control_adjacency(
    seed: CoordinateSensitiveSeed, permutation: Sequence[int],
) -> Matrix:
    return _adjacency_for_permutation(seed, validate_permutation(seed, permutation))


def control_certificate(
    seed: CoordinateSensitiveSeed,
    permutation: Sequence[int],
    control_override: Matrix | None = None,
    claimed_fourth_moment: Fraction | None = None,
) -> ControlCertificate:
    matching = validate_permutation(seed, permutation)
    cross_count = matching_cross_count(seed, matching)
    if cross_count <= 0:
        raise CoordinateSensitiveError("coordinate-sensitive control must cross role classes")
    expected_control_adjacency = control_adjacency(seed, matching)
    control = expected_control_adjacency if control_override is None else control_override
    validate_matrix(control, seed.size)
    if control != expected_control_adjacency:
        raise CoordinateSensitiveError("control adjacency does not match its declared permutation")
    candidate_weights = edge_weight_multiset(seed.adjacency)
    control_weights = edge_weight_multiset(control)
    fair = candidate_weights == control_weights
    if not fair:
        raise CoordinateSensitiveError("control changed the edge-weight multiset")
    candidate_degrees = weighted_degrees(seed.adjacency)
    control_degrees = weighted_degrees(control)
    fair_degrees = candidate_degrees == control_degrees
    if not fair_degrees:
        raise CoordinateSensitiveError("control changed at least one vertex's weighted degree")
    candidate_profile = edge_degree_profile(seed.adjacency)
    control_profile = edge_degree_profile(control)
    profile_difference = candidate_profile != control_profile
    if not profile_difference:
        raise CoordinateSensitiveError("cross-role control did not break edge-degree isomorphism")
    candidate_moment = validate_candidate_fourth_moment(seed)
    control_moment = endpoint_moment(control, seed.entrance, seed.exit, 4)
    if claimed_fourth_moment is not None:
        if type(claimed_fourth_moment) is not Fraction:
            raise CoordinateSensitiveError("claimed fourth moment must be an exact Fraction")
        if claimed_fourth_moment != control_moment:
            raise CoordinateSensitiveError("claimed fourth moment disagrees with the exact control")
    expected_control_moment = Fraction(seed.balance * (seed.balance - cross_count))
    if control_moment != expected_control_moment:
        raise CoordinateSensitiveError("control fourth-moment formula failed")
    difference = candidate_moment - control_moment
    if difference != Fraction(cross_count * seed.balance) or difference <= 0:
        raise CoordinateSensitiveError("positive coordinate-role moment separation failed")
    return ControlCertificate(
        cross_count=cross_count,
        fair_weight_multiset=fair,
        fair_vertex_weighted_degrees=fair_degrees,
        candidate_edge_degree_profile=candidate_profile,
        control_edge_degree_profile=control_profile,
        edge_degree_profile_differs=profile_difference,
        candidate_fourth_moment=candidate_moment,
        control_fourth_moment=control_moment,
        moment_difference=difference,
    )


def validate_seed(seed: CoordinateSensitiveSeed) -> StructuralCertificate:
    validate_coordinates_and_cells(seed)
    validate_declared_candidate(seed)
    quotient = validate_quotient(seed)
    validate_chiral(seed)
    nullity, off_rank, norm_squared, projector_element, pivots = validate_zero_rank_and_gap(seed)
    moment = validate_candidate_fourth_moment(seed)
    gap = numerical_gap(seed, nullity)
    for cross_count in range(1, min(seed.g, seed.h) + 1):
        control_certificate(seed, canonical_cross_permutation(seed, cross_count))
    return StructuralCertificate(
        quotient=quotient,
        exact_nullity=nullity,
        off_diagonal_rank=off_rank,
        norm_squared=norm_squared,
        endpoint_weight=projector_element,
        zero_projector_endpoint_element=projector_element,
        ldlt_pivots=pivots,
        candidate_fourth_moment=moment,
        numerical_gap=gap,
    )
