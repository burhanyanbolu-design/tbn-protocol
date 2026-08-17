#!/usr/bin/env python3
"""Exact structural algebra for the zero-mode-neutral anchor family."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import permutations
import math
from typing import Sequence

GRIDS = ((2, 6), (3, 6), (4, 6))
ANCHOR_WEIGHTS = (2, 3, 4, 5, 6)
HUB_LABEL = "auxiliary-hub"
ZERO_TOLERANCE = 1.0e-10

Matrix = tuple[tuple[Fraction, ...], ...]
Label = tuple[int, int] | str


class NeutralAnchorError(ValueError):
    """Raised when an exact neutral-anchor certificate fails."""


@dataclass(frozen=True)
class AnchorSeed:
    s: int
    rows: int
    labels: tuple[Label, ...]
    cells: tuple[tuple[int, ...], ...]
    adjacency: Matrix
    entrance: int
    exit: int
    genuine_pairs: tuple[tuple[int, int], ...]
    source_gadgets: tuple[tuple[int, int, int, int], ...]
    destination_gadgets: tuple[tuple[int, int, int, int], ...]

    @property
    def size(self) -> int:
        return len(self.labels)

    @property
    def g(self) -> int:
        return len(ANCHOR_WEIGHTS)

    @property
    def h(self) -> int:
        return len(self.cells[7])

    @property
    def p(self) -> int:
        return self.g + self.h


    @property
    def matched_weight(self) -> int:
        return 4 * self.g + self.h

    @property
    def terminal_weight(self) -> int:
        return self.matched_weight


@dataclass(frozen=True)
class StructuralCertificate:
    quotient: Matrix
    exact_nullity: int
    off_diagonal_rank: int
    norm_squared: Fraction
    endpoint_weight: Fraction
    zero_projector_endpoint_element: Fraction
    gram_trace: int
    gram_dimension: int
    gap_bound_exponent: Fraction
    numerical_gap: float
    fourth_moment: Fraction
    sixth_moment: Fraction
    controls_checked: int


@dataclass(frozen=True)
class ControlCertificate:
    permutation: tuple[int, ...]
    fair_weight_multiset: bool
    fair_vertex_weighted_degrees: bool
    edge_degree_profile_differs: bool
    zero_vector_identical: bool
    fourth_moment: Fraction
    sixth_moment: Fraction
    eighth_moment: Fraction
    candidate_eighth_moment: Fraction
    eighth_moment_difference: Fraction


def coordinate_index(s: int, row: int, column: int) -> int:
    if any(type(value) is not int for value in (s, row, column)):
        raise NeutralAnchorError("coordinates must be exact integers")
    if s < 1 or row < 0 or column < 0 or column > s:
        raise NeutralAnchorError("coordinate is outside the EOG grid")
    return row * (s + 1) + column


def validate_permutation(permutation: Sequence[int]) -> tuple[int, ...]:
    values = tuple(permutation)
    if len(values) != 5 or any(type(value) is not int for value in values):
        raise NeutralAnchorError("genuine permutation must contain five exact integers")
    if sorted(values) != list(range(5)):
        raise NeutralAnchorError("genuine permutation must be bijective")
    return values


def all_genuine_permutations(include_identity: bool = False) -> tuple[tuple[int, ...], ...]:
    if type(include_identity) is not bool:
        raise NeutralAnchorError("include_identity must be exact bool")
    identity = tuple(range(5))
    return tuple(value for value in permutations(range(5)) if include_identity or value != identity)


def _base_cells(s: int, rows: int) -> tuple[tuple[int, ...], ...]:
    count = rows * (s + 1)
    entrance = coordinate_index(s, 0, 0)
    exit_state = coordinate_index(s, rows - 1, s)
    sources = tuple(coordinate_index(s, row, s) for row in range(rows - 1))
    destinations = tuple(coordinate_index(s, row + 1, 0) for row in range(rows - 1))
    reserved = {entrance, exit_state, *sources, *destinations}
    unused = tuple(index for index in range(count) if index not in reserved)
    if len(unused) % 2:
        raise NeutralAnchorError("support coordinates must split evenly")
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


def source_vertices(seed: AnchorSeed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[2:7]) + seed.cells[7]


def destination_vertices(seed: AnchorSeed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[8:13]) + seed.cells[13]


def boundary_factor(seed: AnchorSeed, position: int) -> int:
    if type(position) is not int or not 0 <= position < seed.p:
        raise NeutralAnchorError("channel position is invalid")
    return 2 if position < seed.g else 1


def _add_edge(matrix: list[list[Fraction]], left: int, right: int, weight: Fraction) -> None:
    if left == right or type(weight) is not Fraction or weight <= 0:
        raise NeutralAnchorError("edges require positive exact weights and no loops")
    if matrix[left][right] or matrix[right][left]:
        raise NeutralAnchorError("duplicate edge")
    matrix[left][right] = weight
    matrix[right][left] = weight


def _adjacency(seed: AnchorSeed, genuine_permutation: Sequence[int]) -> Matrix:
    genuine = validate_permutation(genuine_permutation)
    full_matching = genuine + tuple(range(seed.g, seed.p))
    sources = source_vertices(seed)
    destinations = destination_vertices(seed)
    matrix = [[Fraction(0) for _ in range(seed.size)] for _ in range(seed.size)]
    _add_edge(matrix, seed.entrance, seed.cells[1][0], Fraction(1))
    for position, source in enumerate(sources):
        _add_edge(matrix, seed.cells[1][0], source, Fraction(boundary_factor(seed, position)))
    for source_position, destination_position in enumerate(full_matching):
        _add_edge(matrix, sources[source_position], destinations[destination_position], Fraction(seed.matched_weight))
    for position, destination in enumerate(destinations):
        _add_edge(matrix, destination, seed.exit, Fraction(boundary_factor(seed, position)))
    for vertex, anchor, terminal, weight in seed.source_gadgets + seed.destination_gadgets:
        _add_edge(matrix, vertex, anchor, Fraction(weight))
        _add_edge(matrix, anchor, terminal, Fraction(seed.terminal_weight))
    return tuple(tuple(row) for row in matrix)



@lru_cache(maxsize=len(GRIDS), typed=True)
def build_seed(s: int, rows: int = 6) -> AnchorSeed:
    """Build and certify an immutable declared seed, cached by grid."""
    if type(s) is not int or type(rows) is not int or (s, rows) not in GRIDS:
        raise NeutralAnchorError("only declared structural grids are allowed")
    count = rows * (s + 1)
    base_cells = _base_cells(s, rows)
    labels: list[Label] = [
        (row, column) for row in range(rows) for column in range(s + 1)
    ] + [HUB_LABEL]
    next_index = len(labels)
    source_gadgets: list[tuple[int, int, int, int]] = []
    destination_gadgets: list[tuple[int, int, int, int]] = []
    gadget_cells: list[tuple[int, ...]] = []
    for side, vertices, target in (
        ("source", tuple(cell[0] for cell in base_cells[2:7]), source_gadgets),
        ("destination", tuple(cell[0] for cell in base_cells[8:13]), destination_gadgets),
    ):
        for row, (vertex, weight) in enumerate(zip(vertices, ANCHOR_WEIGHTS, strict=True)):
            anchor, terminal = next_index, next_index + 1
            next_index += 2
            labels.extend((f"{side}-anchor-{row}", f"{side}-terminal-{row}"))
            target.append((vertex, anchor, terminal, weight))
            gadget_cells.extend(((anchor,), (terminal,)))
    cells = base_cells + tuple(gadget_cells)
    pairs = tuple(
        (coordinate_index(s, row, s), coordinate_index(s, row + 1, 0))
        for row in range(rows - 1)
    )
    shell = AnchorSeed(
        s=s,
        rows=rows,
        labels=tuple(labels),
        cells=cells,
        adjacency=tuple(),
        entrance=base_cells[0][0],
        exit=base_cells[14][0],
        genuine_pairs=pairs,
        source_gadgets=tuple(source_gadgets),
        destination_gadgets=tuple(destination_gadgets),
    )
    seed = AnchorSeed(
        s=s,
        rows=rows,
        labels=shell.labels,
        cells=shell.cells,
        adjacency=_adjacency(shell, tuple(range(5))),
        entrance=shell.entrance,
        exit=shell.exit,
        genuine_pairs=shell.genuine_pairs,
        source_gadgets=shell.source_gadgets,
        destination_gadgets=shell.destination_gadgets,
    )
    validate_seed(seed)
    return seed


def validate_matrix(matrix: Matrix, size: int) -> None:
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise NeutralAnchorError("matrix dimensions changed")
    for left in range(size):
        for right in range(size):
            value = matrix[left][right]
            if type(value) is not Fraction or value < 0:
                raise NeutralAnchorError("weights must be nonnegative exact Fractions")
            if left == right and value:
                raise NeutralAnchorError("self-loops are forbidden")
            if value != matrix[right][left]:
                raise NeutralAnchorError("matrix must be symmetric")


def validate_seed_shape(seed: AnchorSeed) -> None:
    if (
        not isinstance(seed, AnchorSeed)
        or type(seed.s) is not int
        or type(seed.rows) is not int
        or (seed.s, seed.rows) not in GRIDS
    ):
        raise NeutralAnchorError("seed type or grid changed")
    count = seed.rows * (seed.s + 1)
    expected_prefix: tuple[Label, ...] = tuple(
        (row, column) for row in range(seed.rows) for column in range(seed.s + 1)
    ) + (HUB_LABEL,)
    if seed.labels[: count + 1] != expected_prefix or len(seed.labels) != count + 21:
        raise NeutralAnchorError("base or gadget labels changed")
    if seed.cells[:15] != _base_cells(seed.s, seed.rows) or len(seed.cells) != 35:
        raise NeutralAnchorError("35-cell partition changed")
    flat = tuple(vertex for cell in seed.cells for vertex in cell)
    if sorted(flat) != list(range(seed.size)) or len(set(flat)) != seed.size:
        raise NeutralAnchorError("cells must cover each vertex exactly once")
    if seed.size not in (39, 45, 51) or seed.size <= len(seed.cells):
        raise NeutralAnchorError("partition must strictly compress the enlarged graph")
    expected_p = count // 2 - 1
    if seed.p != expected_p or seed.g != 5 or seed.h != expected_p - 5 or seed.h <= 0:
        raise NeutralAnchorError("channel counts changed")
    if seed.matched_weight != 20 + seed.h or seed.terminal_weight != seed.matched_weight:
        raise NeutralAnchorError("fixed M weights changed")
    if tuple(item[3] for item in seed.source_gadgets) != ANCHOR_WEIGHTS:
        raise NeutralAnchorError("source anchor weights changed")
    if tuple(item[3] for item in seed.destination_gadgets) != ANCHOR_WEIGHTS:
        raise NeutralAnchorError("destination anchor weights changed")
    expected_gadget_cells = tuple(
        cell for gadget in seed.source_gadgets + seed.destination_gadgets for cell in ((gadget[1],), (gadget[2],))
    )
    if seed.cells[15:] != expected_gadget_cells:
        raise NeutralAnchorError("gadget cell order changed")


def validate_candidate(seed: AnchorSeed) -> None:
    validate_matrix(seed.adjacency, seed.size)
    if seed.adjacency != _adjacency(seed, tuple(range(5))):
        raise NeutralAnchorError("candidate edges or fixed weights changed")
    expected_pairs = tuple(
        (coordinate_index(seed.s, row, seed.s), coordinate_index(seed.s, row + 1, 0))
        for row in range(seed.rows - 1)
    )
    if seed.genuine_pairs != expected_pairs:
        raise NeutralAnchorError("genuine pair metadata changed")
    if seed.adjacency[seed.exit][seed.entrance]:
        raise NeutralAnchorError("false periodic edge is forbidden")
    seen = {seed.entrance}
    pending = [seed.entrance]
    while pending:
        vertex = pending.pop()
        for neighbour, weight in enumerate(seed.adjacency[vertex]):
            if weight and neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    if len(seen) != seed.size:
        raise NeutralAnchorError("candidate must be connected")



def quotient_matrix(seed: AnchorSeed, adjacency: Matrix | None = None) -> Matrix:
    matrix = seed.adjacency if adjacency is None else adjacency
    validate_matrix(matrix, seed.size)
    cell_of = {vertex: index for index, cell in enumerate(seed.cells) for vertex in cell}
    signatures: list[tuple[Fraction, ...]] = []
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
                raise NeutralAnchorError("35-cell partition is not exactly equitable")
        if first is None:
            raise NeutralAnchorError("quotient cell is empty")
        signatures.append(first)
    quotient = tuple(signatures)
    for vertex in range(seed.size):
        for target_cell, targets in enumerate(seed.cells):
            actual = sum((matrix[vertex][target] for target in targets), Fraction(0))
            if actual != quotient[cell_of[vertex]][target_cell]:
                raise NeutralAnchorError("exact HP=PB closure failed")
    return quotient


def sublattice_signs(seed: AnchorSeed) -> tuple[int, ...]:
    signs = [0] * seed.size
    for vertex in (seed.entrance,) + source_vertices(seed) + (seed.exit,):
        signs[vertex] = 1
    for vertex in (seed.cells[1][0],) + destination_vertices(seed):
        signs[vertex] = -1
    for vertex, anchor, terminal, _weight in seed.source_gadgets + seed.destination_gadgets:
        signs[anchor] = -signs[vertex]
        signs[terminal] = signs[vertex]
    if any(sign == 0 for sign in signs):
        raise NeutralAnchorError("sublattice assignment is incomplete")
    return tuple(signs)


def validate_chiral(seed: AnchorSeed, adjacency: Matrix | None = None) -> None:
    matrix = seed.adjacency if adjacency is None else adjacency
    signs = sublattice_signs(seed)
    if signs.count(1) - signs.count(-1) != 1:
        raise NeutralAnchorError("sublattice imbalance must be one")
    for left, row in enumerate(matrix):
        for right, weight in enumerate(row):
            if signs[left] * weight * signs[right] != -weight:
                raise NeutralAnchorError("exact chiral symmetry failed")


def matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> tuple[Fraction, ...]:
    if len(matrix) != len(vector):
        raise NeutralAnchorError("matrix-vector dimensions differ")
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def exact_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    values = [[Fraction(value) for value in row] for row in matrix]
    columns = len(values[0]) if values else 0
    if any(len(row) != columns for row in values):
        raise NeutralAnchorError("rank input must be rectangular")
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, len(values)) if values[row][column]), None)
        if pivot is None:
            continue
        values[rank], values[pivot] = values[pivot], values[rank]
        divisor = values[rank][column]
        values[rank] = [value / divisor for value in values[rank]]
        for row in range(rank + 1, len(values)):
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


def common_zero_vector(seed: AnchorSeed) -> tuple[Fraction, ...]:
    scale = seed.terminal_weight
    vector = [Fraction(0) for _ in range(seed.size)]
    vector[seed.entrance] = vector[seed.exit] = -Fraction(seed.matched_weight * scale)
    for position, source in enumerate(source_vertices(seed)):
        vector[source] = Fraction(boundary_factor(seed, position) * scale)
    for _vertex, _anchor, terminal, weight in seed.source_gadgets:
        vector[terminal] = -Fraction(2 * weight)
    return tuple(vector)


def off_diagonal_and_gram(seed: AnchorSeed, adjacency: Matrix | None = None) -> tuple[Matrix, Matrix]:
    matrix = seed.adjacency if adjacency is None else adjacency
    signs = sublattice_signs(seed)
    positive = tuple(index for index, sign in enumerate(signs) if sign == 1)
    negative = tuple(index for index, sign in enumerate(signs) if sign == -1)
    block = tuple(tuple(matrix[left][right] for right in negative) for left in positive)
    gram = tuple(tuple(
        sum((block[row][left] * block[row][right] for row in range(len(block))), Fraction(0))
        for right in range(len(negative))
    ) for left in range(len(negative)))
    return block, gram


def validate_zero_rank_gap(
    seed: AnchorSeed, adjacency: Matrix | None = None,
) -> tuple[int, int, Fraction, Fraction, int, int, Fraction]:
    """Certify one graph by exact generic elimination and integral Gram bounds."""
    matrix = seed.adjacency if adjacency is None else adjacency
    validate_matrix(matrix, seed.size)
    validate_chiral(seed, matrix)
    vector = common_zero_vector(seed)
    if matrix_vector(matrix, vector) != (Fraction(0),) * seed.size:
        raise NeutralAnchorError("common vector is not an exact zero mode")
    block, gram = off_diagonal_and_gram(seed, matrix)
    block_rank = exact_rank(block)
    dimension = seed.p + 11
    if len(gram) != dimension or block_rank != dimension:
        raise NeutralAnchorError("off-diagonal block lacks full column rank")
    nullity = seed.size - exact_rank(matrix)
    if nullity != 1:
        raise NeutralAnchorError("full nullity must be one")
    norm = sum((value * value for value in vector), Fraction(0))
    expected_norm = Fraction(
        seed.terminal_weight ** 2 * seed.matched_weight * (2 * seed.matched_weight + 1)
        + 4 * sum(weight * weight for weight in ANCHOR_WEIGHTS)
    )
    projector = abs(vector[seed.entrance] * vector[seed.exit]) / norm
    expected_projector = Fraction(seed.matched_weight ** 4, expected_norm)
    if norm != expected_norm or projector != expected_projector:
        raise NeutralAnchorError("common zero-projector formulas failed")
    trace = sum((gram[index][index] for index in range(dimension)), Fraction(0))
    expected_trace = Fraction(
        181
        + 2 * seed.matched_weight
        + seed.p * seed.matched_weight ** 2
        + 10 * seed.terminal_weight ** 2
    )
    if trace != expected_trace or trace.denominator != 1:
        raise NeutralAnchorError("integral Gram trace formula failed")
    exponent = Fraction(dimension - 1, 2)
    if exponent <= 0:
        raise NeutralAnchorError("gap-bound exponent is invalid")
    return nullity, block_rank, norm, projector, int(trace), dimension, exponent


def validate_uniform_control_nullity_theorem(
    seed: AnchorSeed,
    permutation: Sequence[int],
    adjacency: Matrix | None = None,
) -> tuple[int, int, int]:
    """Prove control nullity one from a fixed nonsingular triangular minor.

    Terminal equations eliminate source-anchor amplitudes, the entrance equation
    eliminates the hub, source equations eliminate all matched destinations, and
    destination-anchor equations eliminate destination-terminal amplitudes.
    """
    genuine = validate_permutation(permutation)
    expected = control_adjacency(seed, genuine)
    matrix = expected if adjacency is None else adjacency
    validate_matrix(matrix, seed.size)
    if matrix != expected:
        raise NeutralAnchorError("control does not match the uniform nullity theorem")
    validate_chiral(seed, matrix)
    vector = common_zero_vector(seed)
    if matrix_vector(matrix, vector) != (Fraction(0),) * seed.size:
        raise NeutralAnchorError("control does not preserve the common zero mode")

    sources = source_vertices(seed)
    destinations = destination_vertices(seed)
    full_matching = genuine + tuple(range(seed.g, seed.p))
    matched_destinations = tuple(destinations[index] for index in full_matching)
    source_anchors = tuple(anchor for _vertex, anchor, _terminal, _weight in seed.source_gadgets)
    source_terminals = tuple(terminal for _vertex, _anchor, terminal, _weight in seed.source_gadgets)
    destination_anchors = tuple(anchor for _vertex, anchor, _terminal, _weight in seed.destination_gadgets)
    destination_terminals = tuple(terminal for _vertex, _anchor, terminal, _weight in seed.destination_gadgets)
    witness_rows = (seed.entrance,) + source_terminals + sources + destination_anchors
    witness_columns = (seed.cells[1][0],) + source_anchors + matched_destinations + destination_terminals
    dimension = seed.p + 11
    signs = sublattice_signs(seed)
    negative = tuple(index for index, sign in enumerate(signs) if sign == -1)
    if (
        len(witness_rows) != dimension
        or len(set(witness_rows)) != dimension
        or len(witness_columns) != dimension
        or len(set(witness_columns)) != dimension
        or set(witness_columns) != set(negative)
        or seed.size != 2 * dimension + 1
        or any(signs[row] != 1 for row in witness_rows)
    ):
        raise NeutralAnchorError("uniform control rank witnesses do not span the chiral block")
    expected_diagonal = (Fraction(1),) + (Fraction(seed.terminal_weight),) * (dimension - 1)
    for index, (row, column) in enumerate(zip(witness_rows, witness_columns, strict=True)):
        if matrix[row][column] != expected_diagonal[index]:
            raise NeutralAnchorError("uniform control rank witness diagonal changed")
        if any(matrix[row][witness_columns[later]] for later in range(index + 1, dimension)):
            raise NeutralAnchorError("uniform control rank witness is not triangular")

    positive = tuple(index for index, sign in enumerate(signs) if sign == 1)
    trace = sum(
        (matrix[left][right] ** 2 for left in positive for right in negative),
        Fraction(0),
    )
    expected_trace = Fraction(
        181
        + 2 * seed.matched_weight
        + seed.p * seed.matched_weight ** 2
        + 10 * seed.terminal_weight ** 2
    )
    if trace != expected_trace or trace.denominator != 1:
        raise NeutralAnchorError("uniform control integral Gram trace formula failed")
    return 1, dimension, int(trace)


def numerical_gap(seed: AnchorSeed, exact_nullity: int) -> float:
    if exact_nullity != 1:
        raise NeutralAnchorError("exact nullity must precede numerical diagnosis")
    import numpy as np
    dense = np.array([[float(value) for value in row] for row in seed.adjacency], dtype=np.float64)
    values = np.linalg.eigvalsh(dense)
    if not bool(np.all(np.isfinite(values))) or int(np.count_nonzero(np.abs(values) <= ZERO_TOLERANCE)) != 1:
        raise NeutralAnchorError("numerical spectrum disagrees with exact nullity")
    gap = float(np.min(np.abs(values[np.abs(values) > ZERO_TOLERANCE])))
    if not math.isfinite(gap) or gap <= 0:
        raise NeutralAnchorError("numerical gap must be finite and positive")
    return gap


def endpoint_moment(matrix: Matrix, entrance: int, exit_state: int, power: int) -> Fraction:
    if type(power) is not int or power < 0:
        raise NeutralAnchorError("moment power must be a nonnegative exact integer")
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


def control_adjacency(seed: AnchorSeed, permutation: Sequence[int]) -> Matrix:
    return _adjacency(seed, validate_permutation(permutation))


def expected_fourth_moment(seed: AnchorSeed) -> Fraction:
    return Fraction(seed.matched_weight ** 2)


def expected_sixth_moment(seed: AnchorSeed) -> Fraction:
    return Fraction(
        seed.matched_weight ** 2 * (seed.matched_weight + 1) ** 2
        + 8 * seed.matched_weight * sum(weight * weight for weight in ANCHOR_WEIGHTS)
    )


def expected_eighth_difference(seed: AnchorSeed, permutation: Sequence[int]) -> Fraction:
    genuine = validate_permutation(permutation)
    return Fraction(2 * seed.matched_weight * sum(
        (ANCHOR_WEIGHTS[index] ** 2 - ANCHOR_WEIGHTS[genuine[index]] ** 2) ** 2
        for index in range(seed.g)
    ))



def control_certificate(
    seed: AnchorSeed,
    permutation: Sequence[int],
    control_override: Matrix | None = None,
    claimed_eighth_moment: Fraction | None = None,
) -> ControlCertificate:
    genuine = validate_permutation(permutation)
    if genuine == tuple(range(seed.g)):
        raise NeutralAnchorError("control must be a nonidentity genuine permutation")
    expected = control_adjacency(seed, genuine)
    control = expected if control_override is None else control_override
    validate_matrix(control, seed.size)
    if control != expected:
        raise NeutralAnchorError("control does not match its declared permutation")
    fair_weights = edge_weight_multiset(seed.adjacency) == edge_weight_multiset(control)
    fair_degrees = weighted_degrees(seed.adjacency) == weighted_degrees(control)
    if not fair_weights or not fair_degrees:
        raise NeutralAnchorError("control fairness invariants failed")
    profile_differs = edge_degree_profile(seed.adjacency) != edge_degree_profile(control)
    if not profile_differs:
        raise NeutralAnchorError("control did not break coordinate-anchor isomorphism")
    validate_chiral(seed, control)
    quotient_matrix(seed, control)
    validate_uniform_control_nullity_theorem(seed, genuine, control)
    common = common_zero_vector(seed)
    zero_identical = matrix_vector(seed.adjacency, common) == matrix_vector(control, common)
    if not zero_identical or matrix_vector(control, common) != (Fraction(0),) * seed.size:
        raise NeutralAnchorError("candidate and control zero vectors differ")
    fourth = endpoint_moment(control, seed.entrance, seed.exit, 4)
    sixth = endpoint_moment(control, seed.entrance, seed.exit, 6)
    eighth = endpoint_moment(control, seed.entrance, seed.exit, 8)
    if fourth != expected_fourth_moment(seed) or sixth != expected_sixth_moment(seed):
        raise NeutralAnchorError("control moments through order six changed")
    candidate_eighth = endpoint_moment(seed.adjacency, seed.entrance, seed.exit, 8)
    difference = candidate_eighth - eighth
    expected_difference = expected_eighth_difference(seed, genuine)
    if difference != expected_difference or difference <= 0:
        raise NeutralAnchorError("strict eighth-moment identity separation failed")
    if claimed_eighth_moment is not None:
        if type(claimed_eighth_moment) is not Fraction or claimed_eighth_moment != eighth:
            raise NeutralAnchorError("claimed eighth moment is inexact or false")
    return ControlCertificate(
        permutation=genuine,
        fair_weight_multiset=fair_weights,
        fair_vertex_weighted_degrees=fair_degrees,
        edge_degree_profile_differs=profile_differs,
        zero_vector_identical=zero_identical,
        fourth_moment=fourth,
        sixth_moment=sixth,
        eighth_moment=eighth,
        candidate_eighth_moment=candidate_eighth,
        eighth_moment_difference=difference,
    )


@lru_cache(maxsize=16)
def validate_seed(seed: AnchorSeed) -> StructuralCertificate:
    """Return the exact certificate; safe to cache because AnchorSeed is immutable."""
    validate_seed_shape(seed)
    validate_candidate(seed)
    quotient = quotient_matrix(seed)
    validate_chiral(seed)
    nullity, block_rank, norm, projector, trace, dimension, exponent = validate_zero_rank_gap(seed)
    fourth = endpoint_moment(seed.adjacency, seed.entrance, seed.exit, 4)
    sixth = endpoint_moment(seed.adjacency, seed.entrance, seed.exit, 6)
    if fourth != expected_fourth_moment(seed) or sixth != expected_sixth_moment(seed):
        raise NeutralAnchorError("candidate fourth/sixth moment formulas failed")
    for power in (0, 1, 2, 3, 5, 7):
        if endpoint_moment(seed.adjacency, seed.entrance, seed.exit, power) != 0:
            raise NeutralAnchorError("forbidden low or odd endpoint moment appeared")
    controls = all_genuine_permutations()
    if len(controls) != 119:
        raise NeutralAnchorError("control family must contain 119 permutations")
    for permutation in controls:
        control_certificate(seed, permutation)
    return StructuralCertificate(
        quotient=quotient,
        exact_nullity=nullity,
        off_diagonal_rank=block_rank,
        norm_squared=norm,
        endpoint_weight=projector,
        zero_projector_endpoint_element=projector,
        gram_trace=trace,
        gram_dimension=dimension,
        gap_bound_exponent=exponent,
        numerical_gap=numerical_gap(seed, nullity),
        fourth_moment=fourth,
        sixth_moment=sixth,
        controls_checked=len(controls),
    )