#!/usr/bin/env python3
"""Exact typed-arm permutation-stabilizer obstruction certificates."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import permutations
from typing import Sequence

Matrix = tuple[tuple[Fraction, ...], ...]
Label = tuple[int, int] | str
Permutation = tuple[int, ...]

DECLARED_GRIDS = ((2, 6), (3, 6), (4, 6))
DECLARED_PROFILES = (
    ("neutral-both", (2, 2, 2, 2, 2), (2, 2, 2, 2, 2)),
    ("duplicate-both", (2, 2, 3, 4, 5), (2, 2, 3, 4, 5)),
    ("source-neutral-destination-distinct", (2, 2, 2, 2, 2), (2, 3, 4, 5, 6)),
    ("source-distinct-destination-neutral", (2, 3, 4, 5, 6), (2, 2, 2, 2, 2)),
    ("rigid-distinct", (2, 3, 4, 5, 6), (2, 3, 4, 5, 6)),
)
IDENTITY = (0, 1, 2, 3, 4)
HUB_LABEL = "auxiliary-hub"
OBSTRUCTION = "obstruction present"
NO_CONCLUSION = "obstruction absent / no conclusion"


class TypedArmError(ValueError):
    """Raised when a typed-arm theorem assumption or certificate fails."""


@dataclass(frozen=True)
class TypedArmSeed:
    s: int
    rows: int
    profile: str
    source_types: tuple[int, ...]
    destination_types: tuple[int, ...]
    labels: tuple[Label, ...]
    cells: tuple[tuple[int, ...], ...]
    source_gadgets: tuple[tuple[int, int, int, int], ...]
    destination_gadgets: tuple[tuple[int, int, int, int], ...]
    entrance: int
    exit: int
    adjacency: Matrix

    @property
    def size(self) -> int:
        return len(self.labels)

    @property
    def p(self) -> int:
        return self.rows * (self.s + 1) // 2 - 1

    @property
    def h(self) -> int:
        return self.p - 5

    @property
    def matching_weight(self) -> int:
        return self.p + 15


@dataclass(frozen=True)
class SimilarityWitness:
    permutation: Permutation
    alpha: Permutation
    beta: Permutation
    vertex_map: tuple[int, ...]


@dataclass(frozen=True)
class ControlAssessment:
    permutation: Permutation
    status: str
    invisible: bool
    witness: SimilarityWitness | None
    fair_pointwise_degrees: bool
    fair_edge_weights: bool
    exact_rank: int
    exact_nullity: int
    zero_projector_endpoint_element: Fraction


def validate_permutation(value: Sequence[int]) -> Permutation:
    result = tuple(value)
    if len(result) != 5 or any(type(item) is not int for item in result):
        raise TypedArmError("permutation must contain five exact integers")
    if sorted(result) != list(range(5)):
        raise TypedArmError("permutation must be bijective")
    return result


def compose(left: Sequence[int], right: Sequence[int]) -> Permutation:
    a, b = validate_permutation(left), validate_permutation(right)
    return tuple(a[b[index]] for index in range(5))


def inverse(value: Sequence[int]) -> Permutation:
    permutation = validate_permutation(value)
    result = [0] * 5
    for index, image in enumerate(permutation):
        result[image] = index
    return tuple(result)


def _profile(name: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if type(name) is not str:
        raise TypedArmError("profile name must be an exact string")
    for declared, source, destination in DECLARED_PROFILES:
        if name == declared:
            return source, destination
    raise TypedArmError("only fixed declared arm profiles are allowed")


def coordinate_index(s: int, row: int, column: int) -> int:
    if any(type(item) is not int for item in (s, row, column)):
        raise TypedArmError("coordinates must be exact integers")
    if s < 1 or row < 0 or column < 0 or column > s:
        raise TypedArmError("coordinate is outside the declared grid")
    return row * (s + 1) + column


def _base_cells(s: int, rows: int) -> tuple[tuple[int, ...], ...]:
    count = rows * (s + 1)
    entrance = coordinate_index(s, 0, 0)
    exit_state = coordinate_index(s, rows - 1, s)
    sources = tuple(coordinate_index(s, row, s) for row in range(5))
    destinations = tuple(coordinate_index(s, row + 1, 0) for row in range(5))
    reserved = {entrance, exit_state, *sources, *destinations}
    support = tuple(index for index in range(count) if index not in reserved)
    if len(support) % 2:
        raise TypedArmError("support coordinates do not split evenly")
    half = len(support) // 2
    return (
        (entrance,), (count,), *((vertex,) for vertex in sources), support[:half],
        *((vertex,) for vertex in destinations), support[half:], (exit_state,),
    )


def source_vertices(seed: TypedArmSeed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[2:7]) + seed.cells[7]


def destination_vertices(seed: TypedArmSeed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[8:13]) + seed.cells[13]


def _boundary(position: int) -> int:
    return 2 if position < 5 else 1


def _add_edge(matrix: list[list[Fraction]], left: int, right: int, weight: int) -> None:
    if left == right or type(weight) is not int or weight <= 0 or matrix[left][right]:
        raise TypedArmError("edge must be new, loop-free, and positive integral")
    matrix[left][right] = matrix[right][left] = Fraction(weight)


def _adjacency(seed: TypedArmSeed, permutation: Sequence[int]) -> Matrix:
    genuine = validate_permutation(permutation)
    sources, destinations = source_vertices(seed), destination_vertices(seed)
    full_matching = genuine + tuple(range(5, seed.p))
    matrix = [[Fraction(0) for _ in range(seed.size)] for _ in range(seed.size)]
    _add_edge(matrix, seed.entrance, seed.cells[1][0], 1)
    for position, source in enumerate(sources):
        _add_edge(matrix, seed.cells[1][0], source, _boundary(position))
    for source_position, destination_position in enumerate(full_matching):
        _add_edge(matrix, sources[source_position], destinations[destination_position], seed.matching_weight)
    for position, destination in enumerate(destinations):
        _add_edge(matrix, destination, seed.exit, _boundary(position))
    for vertex, anchor, terminal, arm_type in seed.source_gadgets + seed.destination_gadgets:
        _add_edge(matrix, vertex, anchor, arm_type)
        _add_edge(matrix, anchor, terminal, seed.matching_weight)
    return tuple(tuple(row) for row in matrix)


@lru_cache(maxsize=15, typed=True)
def build_seed(s: int, rows: int = 6, profile: str = "neutral-both") -> TypedArmSeed:
    if type(s) is not int or type(rows) is not int or (s, rows) not in DECLARED_GRIDS:
        raise TypedArmError("only declared structural grids are allowed")
    source_types, destination_types = _profile(profile)
    count = rows * (s + 1)
    cells = _base_cells(s, rows)
    labels: list[Label] = [(row, column) for row in range(rows) for column in range(s + 1)]
    labels.append(HUB_LABEL)
    next_index = count + 1
    source_gadgets: list[tuple[int, int, int, int]] = []
    destination_gadgets: list[tuple[int, int, int, int]] = []
    gadget_cells: list[tuple[int, ...]] = []
    for side, roots, types, target in (
        ("source", tuple(cell[0] for cell in cells[2:7]), source_types, source_gadgets),
        ("destination", tuple(cell[0] for cell in cells[8:13]), destination_types, destination_gadgets),
    ):
        for index, (root, arm_type) in enumerate(zip(roots, types, strict=True)):
            anchor, terminal = next_index, next_index + 1
            next_index += 2
            labels.extend((f"{side}-anchor-{index}", f"{side}-terminal-{index}"))
            target.append((root, anchor, terminal, arm_type))
            gadget_cells.extend(((anchor,), (terminal,)))
    shell = TypedArmSeed(s, rows, profile, source_types, destination_types, tuple(labels),
                         cells + tuple(gadget_cells), tuple(source_gadgets),
                         tuple(destination_gadgets), cells[0][0], cells[14][0], tuple())
    seed = TypedArmSeed(**{**shell.__dict__, "adjacency": _adjacency(shell, IDENTITY)})
    validate_seed(seed)
    return seed


def validate_matrix(matrix: Matrix, size: int) -> None:
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise TypedArmError("matrix dimensions changed")
    for left in range(size):
        for right in range(size):
            value = matrix[left][right]
            if type(value) is not Fraction or value < 0:
                raise TypedArmError("every matrix entry must be a nonnegative exact Fraction")
            if value != matrix[right][left] or (left == right and value):
                raise TypedArmError("matrix must be symmetric and loop-free")


def validate_seed_shape(seed: TypedArmSeed) -> None:
    if (
        not isinstance(seed, TypedArmSeed)
        or type(seed.s) is not int
        or type(seed.rows) is not int
        or (seed.s, seed.rows) not in DECLARED_GRIDS
    ):
        raise TypedArmError("seed or grid is not declared")
    expected_source, expected_destination = _profile(seed.profile)
    if seed.source_types != expected_source or seed.destination_types != expected_destination:
        raise TypedArmError("declared rooted arm types changed")
    count = seed.rows * (seed.s + 1)
    base_cells = _base_cells(seed.s, seed.rows)
    labels: list[Label] = [
        (row, column)
        for row in range(seed.rows)
        for column in range(seed.s + 1)
    ] + [HUB_LABEL]
    next_index = count + 1
    source_gadgets: list[tuple[int, int, int, int]] = []
    destination_gadgets: list[tuple[int, int, int, int]] = []
    gadget_cells: list[tuple[int, ...]] = []
    for side, roots, types, target in (
        ("source", tuple(cell[0] for cell in base_cells[2:7]), expected_source, source_gadgets),
        ("destination", tuple(cell[0] for cell in base_cells[8:13]), expected_destination, destination_gadgets),
    ):
        for index, (root, arm_type) in enumerate(zip(roots, types, strict=True)):
            anchor, terminal = next_index, next_index + 1
            next_index += 2
            labels.extend((f"{side}-anchor-{index}", f"{side}-terminal-{index}"))
            target.append((root, anchor, terminal, arm_type))
            gadget_cells.extend(((anchor,), (terminal,)))
    expected_cells = base_cells + tuple(gadget_cells)
    if seed.labels != tuple(labels):
        raise TypedArmError("coordinate or gadget labels changed")
    if seed.cells != expected_cells or len(seed.cells) != 35:
        raise TypedArmError("35-cell neutral-anchor partition changed")
    if seed.source_gadgets != tuple(source_gadgets) or seed.destination_gadgets != tuple(destination_gadgets):
        raise TypedArmError("rooted arm metadata changed")
    if seed.entrance != base_cells[0][0] or seed.exit != base_cells[14][0]:
        raise TypedArmError("declared endpoints changed")
    flat = tuple(vertex for cell in seed.cells for vertex in cell)
    if sorted(flat) != list(range(seed.size)) or len(set(flat)) != seed.size:
        raise TypedArmError("cells must partition all vertices")
    if seed.size not in (39, 45, 51) or seed.size <= len(seed.cells):
        raise TypedArmError("declared partition compression changed")
    if seed.p != count // 2 - 1 or seed.h != seed.p - 5 or seed.matching_weight != seed.p + 15:
        raise TypedArmError("fixed channel count or M=p+15 changed")


def control_adjacency(seed: TypedArmSeed, permutation: Sequence[int]) -> Matrix:
    validate_seed_shape(seed)
    return _adjacency(seed, validate_permutation(permutation))


def quotient_matrix(seed: TypedArmSeed, matrix: Matrix | None = None) -> Matrix:
    adjacency = seed.adjacency if matrix is None else matrix
    validate_matrix(adjacency, seed.size)
    rows: list[tuple[Fraction, ...]] = []
    for cell in seed.cells:
        signatures = {
            tuple(sum((adjacency[vertex][target] for target in targets), Fraction(0))
                  for targets in seed.cells)
            for vertex in cell
        }
        if len(signatures) != 1:
            raise TypedArmError("35-cell partition is not exactly equitable")
        rows.append(signatures.pop())
    return tuple(rows)


def exact_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    values = [[Fraction(value) for value in row] for row in matrix]
    columns = len(values[0]) if values else 0
    if any(len(row) != columns for row in values):
        raise TypedArmError("rank input must be rectangular")
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
                values[row] = [value - factor * base
                               for value, base in zip(values[row], values[rank], strict=True)]
        rank += 1
        if rank == len(values):
            break
    return rank


def common_zero_vector(seed: TypedArmSeed) -> tuple[Fraction, ...]:
    vector = [Fraction(0) for _ in range(seed.size)]
    m = seed.matching_weight
    vector[seed.entrance] = vector[seed.exit] = -Fraction(m * m)
    for position, source in enumerate(source_vertices(seed)):
        vector[source] = Fraction(_boundary(position) * m)
    for _root, _anchor, terminal, arm_type in seed.source_gadgets:
        vector[terminal] = -Fraction(2 * arm_type)
    return tuple(vector)


def matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> tuple[Fraction, ...]:
    if len(matrix) != len(vector):
        raise TypedArmError("matrix-vector dimensions differ")
    return tuple(sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
                 for row in matrix)


def weighted_degrees(matrix: Matrix) -> tuple[Fraction, ...]:
    return tuple(sum(row, Fraction(0)) for row in matrix)


def edge_weights(matrix: Matrix) -> tuple[Fraction, ...]:
    return tuple(sorted(matrix[left][right] for left in range(len(matrix))
                        for right in range(left + 1, len(matrix)) if matrix[left][right]))


def endpoint_moment(matrix: Matrix, entrance: int, exit_state: int, power: int) -> Fraction:
    if type(power) is not int or power < 0:
        raise TypedArmError("moment power must be a nonnegative exact integer")
    state = tuple(Fraction(index == entrance) for index in range(len(matrix)))
    for _ in range(power):
        state = matrix_vector(matrix, state)
    return state[exit_state]


def stabilizer(types: Sequence[int]) -> tuple[Permutation, ...]:
    rooted = tuple(types)
    if len(rooted) != 5 or any(type(item) is not int or item <= 0 for item in rooted):
        raise TypedArmError("five positive exact rooted types are required")
    return tuple(permutation for permutation in permutations(range(5))
                 if all(rooted[index] == rooted[permutation[index]] for index in range(5)))


@lru_cache(maxsize=15)
def source_stabilizer(seed: TypedArmSeed) -> tuple[Permutation, ...]:
    validate_seed_shape(seed)
    return stabilizer(seed.source_types)


@lru_cache(maxsize=15)
def destination_stabilizer(seed: TypedArmSeed) -> tuple[Permutation, ...]:
    validate_seed_shape(seed)
    return stabilizer(seed.destination_types)


@lru_cache(maxsize=15)
def invisible_witnesses(seed: TypedArmSeed) -> tuple[SimilarityWitness, ...]:
    found: dict[Permutation, tuple[Permutation, Permutation]] = {}
    for alpha in source_stabilizer(seed):
        for beta in destination_stabilizer(seed):
            permutation = compose(beta, inverse(alpha))
            found.setdefault(permutation, (alpha, beta))
    return tuple(SimilarityWitness(permutation, found[permutation][0], found[permutation][1],
                                   build_vertex_map(seed, *found[permutation]))
                 for permutation in sorted(found))


def find_witness(seed: TypedArmSeed, permutation: Sequence[int]) -> SimilarityWitness | None:
    genuine = validate_permutation(permutation)
    return next((item for item in invisible_witnesses(seed) if item.permutation == genuine), None)


def build_vertex_map(seed: TypedArmSeed, alpha: Sequence[int], beta: Sequence[int]) -> tuple[int, ...]:
    source_map, destination_map = validate_permutation(alpha), validate_permutation(beta)
    if source_map not in source_stabilizer(seed) or destination_map not in destination_stabilizer(seed):
        raise TypedArmError("arm map swaps unequal rooted types")
    mapping = list(range(seed.size))
    for gadgets, arm_map in ((seed.source_gadgets, source_map),
                             (seed.destination_gadgets, destination_map)):
        for index, image in enumerate(arm_map):
            for position in range(3):
                mapping[gadgets[index][position]] = gadgets[image][position]
    return tuple(mapping)


def certify_similarity(
    seed: TypedArmSeed,
    permutation: Sequence[int],
    alpha: Sequence[int],
    beta: Sequence[int],
    vertex_map: Sequence[int] | None = None,
    candidate_override: Matrix | None = None,
    control_override: Matrix | None = None,
) -> SimilarityWitness:
    genuine = validate_permutation(permutation)
    source_map, destination_map = validate_permutation(alpha), validate_permutation(beta)
    if compose(destination_map, inverse(source_map)) != genuine:
        raise TypedArmError("witness does not satisfy pi=beta composed with alpha^-1")
    expected_map = build_vertex_map(seed, source_map, destination_map)
    mapping = expected_map if vertex_map is None else tuple(vertex_map)
    if len(mapping) != seed.size or sorted(mapping) != list(range(seed.size)):
        raise TypedArmError("vertex map must be a bijection")
    if mapping != expected_map:
        raise TypedArmError("vertex map is not the declared typed-arm witness")
    if mapping[seed.entrance] != seed.entrance or mapping[seed.exit] != seed.exit:
        raise TypedArmError("vertex map must fix both endpoints")
    candidate = seed.adjacency if candidate_override is None else candidate_override
    expected_control = control_adjacency(seed, genuine)
    control = expected_control if control_override is None else control_override
    validate_matrix(candidate, seed.size)
    validate_matrix(control, seed.size)
    if candidate != seed.adjacency or control != expected_control:
        raise TypedArmError("foreign edges or unequal matching weights are forbidden")
    for left in range(seed.size):
        for right in range(seed.size):
            if control[mapping[left]][mapping[right]] != candidate[left][right]:
                raise TypedArmError("false permutation-similarity witness")
    zero = common_zero_vector(seed)
    if tuple(zero[mapping[index]] for index in range(seed.size)) != zero:
        raise TypedArmError("common zero vector is not invariant under the witness")
    if matrix_vector(candidate, zero) != (Fraction(0),) * seed.size:
        raise TypedArmError("candidate common-zero residual is nonzero")
    if matrix_vector(control, zero) != (Fraction(0),) * seed.size:
        raise TypedArmError("control common-zero residual is nonzero")
    return SimilarityWitness(genuine, source_map, destination_map, mapping)


def projector_formula(seed: TypedArmSeed) -> tuple[Fraction, Fraction]:
    vector = common_zero_vector(seed)
    norm = sum((value * value for value in vector), Fraction(0))
    expected = Fraction(seed.matching_weight ** 3 * (2 * seed.matching_weight + 1)
                        + 4 * sum(value * value for value in seed.source_types))
    if norm != expected:
        raise TypedArmError("zero-vector norm formula failed")
    projector = abs(vector[seed.entrance] * vector[seed.exit]) / norm
    if projector != Fraction(seed.matching_weight ** 4, expected):
        raise TypedArmError("zero-projector formula failed")
    return norm, projector


@lru_cache(maxsize=15)
def validate_candidate_rank(seed: TypedArmSeed) -> tuple[int, int]:
    rank = exact_rank(seed.adjacency)
    nullity = seed.size - rank
    if rank != seed.size - 1 or nullity != 1:
        raise TypedArmError("candidate must have exact rank n-1 and nullity one")
    return rank, nullity


def validate_control_rank(seed: TypedArmSeed, permutation: Sequence[int], matrix: Matrix) -> tuple[int, int]:
    """Certify full chiral rank from an exact triangular maximal minor."""
    genuine = validate_permutation(permutation)
    if matrix != control_adjacency(seed, genuine):
        raise TypedArmError("rank certificate requires the exact declared control")
    sources, destinations = source_vertices(seed), destination_vertices(seed)
    full_matching = genuine + tuple(range(5, seed.p))
    source_anchors = tuple(item[1] for item in seed.source_gadgets)
    source_terminals = tuple(item[2] for item in seed.source_gadgets)
    destination_anchors = tuple(item[1] for item in seed.destination_gadgets)
    destination_terminals = tuple(item[2] for item in seed.destination_gadgets)
    rows = ((seed.entrance,) + source_terminals + sources + destination_anchors)
    columns = ((seed.cells[1][0],) + source_anchors
               + tuple(destinations[index] for index in full_matching)
               + destination_terminals)
    dimension = seed.p + 11
    if len(rows) != dimension or len(columns) != dimension:
        raise TypedArmError("control rank witness has the wrong dimension")
    expected_diagonal = (Fraction(1),) + (Fraction(seed.matching_weight),) * (dimension - 1)
    for index in range(dimension):
        if matrix[rows[index]][columns[index]] != expected_diagonal[index]:
            raise TypedArmError("control rank witness diagonal changed")
        if any(matrix[rows[index]][columns[later]] for later in range(index + 1, dimension)):
            raise TypedArmError("control rank witness is not triangular")
    rank = 2 * dimension
    if rank != seed.size - 1:
        raise TypedArmError("control rank witness is not maximal")
    return rank, 1


@lru_cache(maxsize=15)
def validate_seed(seed: TypedArmSeed) -> None:
    validate_seed_shape(seed)
    validate_matrix(seed.adjacency, seed.size)
    if seed.adjacency != _adjacency(seed, IDENTITY):
        raise TypedArmError("candidate is not the fixed identity matching")
    quotient_matrix(seed)
    zero = common_zero_vector(seed)
    if matrix_vector(seed.adjacency, zero) != (Fraction(0),) * seed.size:
        raise TypedArmError("candidate common-zero residual is nonzero")
    validate_candidate_rank(seed)
    projector_formula(seed)


def assess_control(
    seed: TypedArmSeed,
    permutation: Sequence[int],
    control_override: Matrix | None = None,
    claimed_separation: bool = False,
) -> ControlAssessment:
    if type(claimed_separation) is not bool:
        raise TypedArmError("claimed_separation must be exact bool")
    validate_seed(seed)
    genuine = validate_permutation(permutation)
    expected = control_adjacency(seed, genuine)
    control = expected if control_override is None else control_override
    validate_matrix(control, seed.size)
    if control != expected:
        raise TypedArmError("control has unequal matching weights or foreign edges")
    degrees_ok = weighted_degrees(control) == weighted_degrees(seed.adjacency)
    weights_ok = edge_weights(control) == edge_weights(seed.adjacency)
    if not degrees_ok or not weights_ok:
        raise TypedArmError("matching-only fairness failed")
    zero = common_zero_vector(seed)
    if matrix_vector(control, zero) != (Fraction(0),) * seed.size:
        raise TypedArmError("control changed the common zero vector")
    witness = find_witness(seed, genuine)
    if witness is not None:
        witness = certify_similarity(
            seed,
            genuine,
            witness.alpha,
            witness.beta,
            witness.vertex_map,
            control_override=control,
        )
    if claimed_separation:
        if witness is not None:
            raise TypedArmError("an invisible control cannot support a separation claim")
        raise TypedArmError("absence of a stabilizer witness cannot support a separation claim")
    rank, nullity = validate_control_rank(seed, genuine, control)
    _norm, projector = projector_formula(seed)
    return ControlAssessment(genuine, OBSTRUCTION if witness else NO_CONCLUSION, witness is not None,
                             witness, degrees_ok, weights_ok, rank, nullity, projector)


def repeated_type_obstruction(seed: TypedArmSeed) -> SimilarityWitness:
    if len(set(seed.source_types)) == 5 and len(set(seed.destination_types)) == 5:
        raise TypedArmError("both typed sides are rigid; no repeated-type theorem applies")
    witness = next((item for item in invisible_witnesses(seed) if item.permutation != IDENTITY), None)
    if witness is None:
        raise TypedArmError("repeated rooted type failed to produce a nonidentity obstruction")
    return certify_similarity(seed, witness.permutation, witness.alpha, witness.beta,
                              witness.vertex_map)
