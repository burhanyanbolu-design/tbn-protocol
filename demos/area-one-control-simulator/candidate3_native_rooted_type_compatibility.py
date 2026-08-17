#!/usr/bin/env python3
"""Exact certificates: direct natural Candidate 3 bipartite/chiral mechanism incompatible."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import permutations
from typing import Sequence

Matrix = tuple[tuple[Fraction, ...], ...]
Permutation = tuple[int, ...]
Partition = tuple[tuple[int, ...], ...]
Signature = tuple[int, int]

DECLARED_GRIDS = ((2, 6), (3, 6), (4, 6))
IDENTITY = (0, 1, 2, 3, 4)
NO_CONCLUSION = "obstruction absent / no conclusion"
DIRECT_BIPARTITE_CHIRAL_INCOMPATIBLE = (
    "direct natural Candidate 3 bipartite/chiral mechanism incompatible"
)
SEPARATION_NO_CONCLUSION = "separation no conclusion"


class NativeRootedTypeError(ValueError):
    """Raised when an exact theorem assumption or certificate is false."""


@dataclass(frozen=True)
class NativeSeed:
    s: int
    rows: int
    labels: tuple[tuple[int, int], ...]
    entrance: int
    exit: int
    sources: tuple[int, ...]
    destinations: tuple[int, ...]
    native_edges: tuple[tuple[int, int], ...]
    adjacency: Matrix

    @property
    def size(self) -> int:
        return len(self.labels)


@dataclass(frozen=True)
class ControlCertificate:
    permutation: Permutation
    fair_weighted_degrees: bool
    fair_edge_weight_multisets: bool


@dataclass(frozen=True)
class CompatibilityAssessment:
    native_rooted_types: bool
    source_signatures: tuple[Signature, ...]
    destination_signatures: tuple[Signature, ...]
    roots_fixed_by_endpoint_fixing_side_preserving_native_automorphisms: bool
    repeated_type_status: str
    direct_bipartite_chiral_mechanism: str
    separation: str
    candidate_nullity: int
    common_kernel_dimension: int


def coordinate_index(s: int, row: int, column: int) -> int:
    if any(type(value) is not int for value in (s, row, column)):
        raise NativeRootedTypeError("coordinates must be exact integers")
    if s < 1 or not 0 <= row < 6 or not 0 <= column <= s:
        raise NativeRootedTypeError("coordinate lies outside the fixed torus")
    return row * (s + 1) + column


def validate_permutation(value: Sequence[int]) -> Permutation:
    result = tuple(value)
    if len(result) != 5 or any(type(item) is not int for item in result):
        raise NativeRootedTypeError("matching permutation must contain five exact integers")
    if sorted(result) != list(range(5)):
        raise NativeRootedTypeError("matching permutation must be bijective")
    return result


def _native_edges(s: int, rows: int) -> tuple[tuple[int, int], ...]:
    edges: set[tuple[int, int]] = set()
    width = s + 1
    for row in range(rows):
        for column in range(width):
            here = row * width + column
            for neighbour in (
                ((row + 1) % rows) * width + column,
                row * width + (column + 1) % width,
            ):
                if here == neighbour:
                    raise NativeRootedTypeError("native cycle produced a loop")
                edges.add(tuple(sorted((here, neighbour))))
    return tuple(sorted(edges))


def _roots(s: int, rows: int) -> tuple[int, int, tuple[int, ...], tuple[int, ...]]:
    entrance = coordinate_index(s, 0, 0)
    exit_state = coordinate_index(s, rows - 1, s)
    sources = tuple(coordinate_index(s, index, s) for index in range(5))
    destinations = tuple(coordinate_index(s, index + 1, 0) for index in range(5))
    return entrance, exit_state, sources, destinations


def matching_edges(seed: NativeSeed, permutation: Sequence[int]) -> tuple[tuple[int, int], ...]:
    genuine = validate_permutation(permutation)
    return tuple((seed.sources[index], seed.destinations[genuine[index]]) for index in range(5))


def _adjacency(s: int, rows: int, permutation: Sequence[int]) -> Matrix:
    genuine = validate_permutation(permutation)
    size = rows * (s + 1)
    matrix = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    for left, right in _native_edges(s, rows):
        matrix[left][right] = matrix[right][left] = Fraction(1)
    _entrance, _exit, sources, destinations = _roots(s, rows)
    for index, image in enumerate(genuine):
        left, right = sources[index], destinations[image]
        matrix[left][right] += Fraction(1)
        matrix[right][left] += Fraction(1)
    return tuple(tuple(row) for row in matrix)


@lru_cache(maxsize=3, typed=True)
def build_seed(s: int, rows: int = 6) -> NativeSeed:
    if type(s) is not int or type(rows) is not int or (s, rows) not in DECLARED_GRIDS:
        raise NativeRootedTypeError("only (s,R)=(2,6),(3,6),(4,6) are declared")
    labels = tuple((row, column) for row in range(rows) for column in range(s + 1))
    entrance, exit_state, sources, destinations = _roots(s, rows)
    seed = NativeSeed(s, rows, labels, entrance, exit_state, sources, destinations,
                      _native_edges(s, rows), _adjacency(s, rows, IDENTITY))
    validate_seed(seed)
    return seed


def validate_matrix(matrix: Matrix, size: int) -> None:
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise NativeRootedTypeError("matrix dimensions changed")
    for left in range(size):
        for right in range(size):
            value = matrix[left][right]
            if type(value) is not Fraction or value < 0:
                raise NativeRootedTypeError("matrix entries must be nonnegative exact Fractions")
            if value != matrix[right][left] or (left == right and value):
                raise NativeRootedTypeError("matrix must be symmetric and loop-free")


def validate_seed_shape(seed: NativeSeed) -> None:
    if (not isinstance(seed, NativeSeed) or type(seed.s) is not int
            or type(seed.rows) is not int or (seed.s, seed.rows) not in DECLARED_GRIDS):
        raise NativeRootedTypeError("seed and grid must be exactly declared")
    labels = tuple((row, column) for row in range(seed.rows) for column in range(seed.s + 1))
    entrance, exit_state, sources, destinations = _roots(seed.s, seed.rows)
    if seed.labels != labels:
        raise NativeRootedTypeError("fixed coordinate labels changed")
    if (seed.entrance, seed.exit, seed.sources, seed.destinations) != (
            entrance, exit_state, sources, destinations):
        raise NativeRootedTypeError("endpoints or genuine root sets changed")
    expected_edges = _native_edges(seed.s, seed.rows)
    if seed.native_edges != expected_edges:
        raise NativeRootedTypeError("native torus topology changed")
    if len(set(seed.sources + seed.destinations)) != 10:
        raise NativeRootedTypeError("source and destination root sets must be disjoint")


def validate_seed(seed: NativeSeed) -> None:
    validate_seed_shape(seed)
    validate_matrix(seed.adjacency, seed.size)
    expected = _adjacency(seed.s, seed.rows, IDENTITY)
    if seed.adjacency != expected:
        raise NativeRootedTypeError(
            "candidate must contain every native edge and only the identity genuine matching")
    for left, right in seed.native_edges:
        if seed.adjacency[left][right] != Fraction(1):
            raise NativeRootedTypeError("an unweighted native edge is missing or changed")


def native_adjacency(seed: NativeSeed) -> Matrix:
    validate_seed_shape(seed)
    size = seed.size
    matrix = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    for left, right in seed.native_edges:
        matrix[left][right] = matrix[right][left] = Fraction(1)
    return tuple(tuple(row) for row in matrix)


def control_adjacency(seed: NativeSeed, permutation: Sequence[int]) -> Matrix:
    validate_seed_shape(seed)
    return _adjacency(seed.s, seed.rows, validate_permutation(permutation))


def _distances(matrix: Matrix, start: int) -> tuple[int, ...]:
    distances = [-1] * len(matrix)
    distances[start] = 0
    pending = [start]
    for vertex in pending:
        for neighbour, weight in enumerate(matrix[vertex]):
            if weight and distances[neighbour] < 0:
                distances[neighbour] = distances[vertex] + 1
                pending.append(neighbour)
    if any(value < 0 for value in distances):
        raise NativeRootedTypeError("native backbone must be connected")
    return tuple(distances)


def endpoint_signatures(seed: NativeSeed) -> tuple[tuple[Signature, ...], tuple[Signature, ...]]:
    validate_seed_shape(seed)
    backbone = native_adjacency(seed)
    from_entrance = _distances(backbone, seed.entrance)
    from_exit = _distances(backbone, seed.exit)
    signature = lambda vertex: (from_entrance[vertex], from_exit[vertex])
    return (tuple(signature(vertex) for vertex in seed.sources),
            tuple(signature(vertex) for vertex in seed.destinations))


def certify_native_rooted_types(
    seed: NativeSeed,
    claimed_source: Sequence[Sequence[int]] | None = None,
    claimed_destination: Sequence[Sequence[int]] | None = None,
) -> tuple[tuple[Signature, ...], tuple[Signature, ...]]:
    validate_seed(seed)
    source, destination = endpoint_signatures(seed)
    expected_source = ((1, 1), (2, 2), (3, 3), (4, 2), (3, 1))
    expected_destination = ((1, 3), (2, 4), (3, 3), (2, 2), (1, 1))
    if source != expected_source or destination != expected_destination:
        raise NativeRootedTypeError("native backbone did not derive the exact rooted signatures")
    if len(set(source)) != 5 or len(set(destination)) != 5:
        raise NativeRootedTypeError("each rooted side must have five distinct signatures")
    for claim, actual in ((claimed_source, source), (claimed_destination, destination)):
        if claim is not None:
            normalized = tuple(tuple(item) for item in claim)
            if normalized != actual:
                raise NativeRootedTypeError("metadata-only or false rooted-type claim rejected")
    return source, destination


def certify_root_fixing_implication(seed: NativeSeed) -> bool:
    """Certify the root-fixing theorem for all maps satisfying its hypotheses.

    The signatures are derived from native weighted-backbone distances and are
    distinct within each preserved side. A weighted graph automorphism maps
    paths to paths with the same weights, so one fixing both endpoints preserves
    both endpoint distances. Side preservation and signature distinctness then
    force every source and destination root to be fixed pointwise.
    """
    validate_seed(seed)
    backbone = native_adjacency(seed)
    if any(weight not in (Fraction(0), Fraction(1)) for row in backbone for weight in row):
        raise NativeRootedTypeError("native endpoint signatures require unit-weight distances")
    source, destination = certify_native_rooted_types(seed)
    derived_source, derived_destination = endpoint_signatures(seed)
    if (source, destination) != (derived_source, derived_destination):
        raise NativeRootedTypeError("native endpoint signatures must be distance-derived")
    if len(set(source)) != len(seed.sources) or len(set(destination)) != len(seed.destinations):
        raise NativeRootedTypeError("native endpoint signatures must be distinct within each side")
    return True


def certify_root_fixing_automorphism(seed: NativeSeed, vertex_map: Sequence[int]) -> tuple[int, ...]:
    """Validate one endpoint-fixing, side-preserving native weighted automorphism."""
    validate_seed(seed)
    mapping = tuple(vertex_map)
    if (len(mapping) != seed.size or any(type(item) is not int for item in mapping)
            or sorted(mapping) != list(range(seed.size))):
        raise NativeRootedTypeError("native automorphism map must be a bijection")
    if mapping[seed.entrance] != seed.entrance or mapping[seed.exit] != seed.exit:
        raise NativeRootedTypeError("native automorphism must fix both endpoints")
    if ({mapping[item] for item in seed.sources} != set(seed.sources)
            or {mapping[item] for item in seed.destinations} != set(seed.destinations)):
        raise NativeRootedTypeError("native automorphism must preserve each rooted side")
    backbone = native_adjacency(seed)
    for left in range(seed.size):
        for right in range(seed.size):
            if backbone[mapping[left]][mapping[right]] != backbone[left][right]:
                raise NativeRootedTypeError("map is not a native weighted automorphism")
    certify_root_fixing_implication(seed)
    source_signatures, destination_signatures = endpoint_signatures(seed)
    typed = {vertex: signature for vertex, signature in zip(seed.sources, source_signatures, strict=True)}
    typed.update(zip(seed.destinations, destination_signatures, strict=True))
    for root in seed.sources + seed.destinations:
        if typed[mapping[root]] != typed[root] or mapping[root] != root:
            raise NativeRootedTypeError("distinct native signatures require pointwise root fixing")
    return mapping


def weighted_degrees(matrix: Matrix) -> tuple[Fraction, ...]:
    return tuple(sum(row, Fraction(0)) for row in matrix)


def channel_weight_multisets(seed: NativeSeed, permutation: Sequence[int]) -> tuple[tuple[Fraction, ...], ...]:
    """Incident edge-channel weights, retaining coincident unit channels separately."""
    validate_seed_shape(seed)
    incident: list[list[Fraction]] = [[] for _ in range(seed.size)]
    for left, right in seed.native_edges + matching_edges(seed, permutation):
        incident[left].append(Fraction(1))
        incident[right].append(Fraction(1))
    return tuple(tuple(sorted(values)) for values in incident)


def certify_control(
    seed: NativeSeed,
    permutation: Sequence[int],
    control_override: Matrix | None = None,
    claimed_separation: bool = False,
) -> ControlCertificate:
    if type(claimed_separation) is not bool:
        raise NativeRootedTypeError("claimed_separation must be exact bool")
    if claimed_separation:
        raise NativeRootedTypeError("native rooted types never prove separation")
    validate_seed(seed)
    genuine = validate_permutation(permutation)
    expected = control_adjacency(seed, genuine)
    control = expected if control_override is None else control_override
    validate_matrix(control, seed.size)
    if control != expected:
        raise NativeRootedTypeError("foreign edge, changed weight, or malformed matching rejected")
    degree_fair = weighted_degrees(control) == weighted_degrees(seed.adjacency)
    incident_fair = channel_weight_multisets(seed, genuine) == channel_weight_multisets(seed, IDENTITY)
    if not degree_fair or not incident_fair:
        raise NativeRootedTypeError("named-vertex matching fairness failed")
    return ControlCertificate(genuine, degree_fair, incident_fair)


def _validate_partition(partition: Sequence[Sequence[int]], size: int) -> Partition:
    cells = tuple(tuple(cell) for cell in partition if cell)
    flat = tuple(vertex for cell in cells for vertex in cell)
    if (any(type(vertex) is not int for vertex in flat)
            or sorted(flat) != list(range(size)) or len(set(flat)) != size):
        raise NativeRootedTypeError("partition must cover each vertex exactly once")
    return cells


def row_partition(seed: NativeSeed) -> Partition:
    validate_seed_shape(seed)
    return tuple(tuple(coordinate_index(seed.s, row, column)
                       for column in range(seed.s + 1)) for row in range(seed.rows))


def column_partition(seed: NativeSeed) -> Partition:
    validate_seed_shape(seed)
    return tuple(tuple(coordinate_index(seed.s, row, column)
                       for row in range(seed.rows)) for column in range(seed.s + 1))


def overlap_fiber_partition(seed: NativeSeed) -> Partition:
    validate_seed_shape(seed)
    cells: list[tuple[int, ...]] = [(seed.entrance,), (seed.exit,)]
    cells.extend((seed.sources[index], seed.destinations[index]) for index in range(5))
    cells.extend(tuple(coordinate_index(seed.s, row, column) for row in range(seed.rows))
                 for column in range(1, seed.s))
    return _validate_partition(cells, seed.size)


def reflection_partition(seed: NativeSeed) -> Partition:
    validate_seed_shape(seed)
    remaining = set(range(seed.size))
    cells: list[tuple[int, ...]] = []
    while remaining:
        first = min(remaining)
        row, column = seed.labels[first]
        reflected = coordinate_index(seed.s, seed.rows - 1 - row, seed.s - column)
        cell = tuple(sorted({first, reflected}))
        cells.append(cell)
        remaining.difference_update(cell)
    return tuple(cells)


def endpoint_seed_partition(seed: NativeSeed) -> Partition:
    validate_seed_shape(seed)
    others = tuple(vertex for vertex in range(seed.size)
                   if vertex not in (seed.entrance, seed.exit))
    return ((seed.entrance,), (seed.exit,), others)


def equitable_refinement(matrix: Matrix, partition: Sequence[Sequence[int]]) -> Partition:
    validate_matrix(matrix, len(matrix))
    current = _validate_partition(partition, len(matrix))
    while True:
        refined: list[tuple[int, ...]] = []
        for cell in current:
            buckets: dict[tuple[Fraction, ...], list[int]] = {}
            for vertex in cell:
                signature = tuple(sum((matrix[vertex][target] for target in targets), Fraction(0))
                                  for targets in current)
                buckets.setdefault(signature, []).append(vertex)
            refined.extend(tuple(bucket) for bucket in sorted(buckets.values(), key=lambda item: item[0]))
        result = tuple(refined)
        if result == current:
            return result
        current = result


def partition_properties(seed: NativeSeed, partition: Sequence[Sequence[int]]) -> dict[str, bool | int]:
    validate_seed(seed)
    cells = _validate_partition(partition, seed.size)
    equitable = True
    for cell in cells:
        signatures = {
            tuple(sum((seed.adjacency[vertex][target] for target in targets), Fraction(0))
                  for targets in cells)
            for vertex in cell
        }
        equitable &= len(signatures) == 1
    entrance_cell = next(cell for cell in cells if seed.entrance in cell)
    exit_cell = next(cell for cell in cells if seed.exit in cell)
    endpoint_representing = entrance_cell == (seed.entrance,) and exit_cell == (seed.exit,)
    return {
        "cell_count": len(cells),
        "equitable": equitable,
        "endpoint_representing": endpoint_representing,
        "endpoints_separate": entrance_cell != exit_cell,
        "strict_compression": len(cells) < seed.size,
    }


def certify_no_endpoint_compression(seed: NativeSeed, claimed_compression: bool = False) -> Partition:
    if type(claimed_compression) is not bool:
        raise NativeRootedTypeError("claimed_compression must be exact bool")
    validate_seed(seed)
    refined = equitable_refinement(seed.adjacency, endpoint_seed_partition(seed))
    if len(refined) != seed.size or any(len(cell) != 1 for cell in refined):
        raise NativeRootedTypeError("endpoint-seeded exact refinement must be discrete")
    natural = (row_partition(seed), column_partition(seed), overlap_fiber_partition(seed))
    if any(all(partition_properties(seed, cells)[key] for key in (
            "equitable", "endpoint_representing", "endpoints_separate", "strict_compression"))
            for cells in natural):
        raise NativeRootedTypeError("a natural strict endpoint quotient unexpectedly survived")
    reflected = reflection_partition(seed)
    reflected_cell = next(cell for cell in reflected if seed.entrance in cell)
    if seed.exit not in reflected_cell:
        raise NativeRootedTypeError("declared reflection must merge the endpoints")
    if claimed_compression:
        raise NativeRootedTypeError("no strict endpoint-representing compression survives")
    return refined


def certify_candidate_nonbipartite(seed: NativeSeed, claimed_bipartite: bool = False) -> tuple[int, ...]:
    if type(claimed_bipartite) is not bool:
        raise NativeRootedTypeError("claimed_bipartite must be exact bool")
    validate_seed(seed)
    if claimed_bipartite:
        raise NativeRootedTypeError("the direct native candidate is non-bipartite")
    if seed.s in (2, 4):
        cycle = tuple(coordinate_index(seed.s, 0, column) for column in range(seed.s + 1))
        if len(cycle) % 2 != 1:
            raise NativeRootedTypeError("horizontal witness must be an odd native cycle")
        pairs = tuple(zip(cycle, cycle[1:] + cycle[:1], strict=True))
        if any(seed.adjacency[left][right] != Fraction(1) for left, right in pairs):
            raise NativeRootedTypeError("odd horizontal native cycle is missing")
        return cycle
    left, right = seed.sources[0], seed.destinations[0]
    if seed.adjacency[left][right] != Fraction(1):
        raise NativeRootedTypeError("identity matching witness edge is missing")
    left_parity = sum(seed.labels[left]) % 2
    right_parity = sum(seed.labels[right]) % 2
    if left_parity != right_parity:
        raise NativeRootedTypeError("matching witness must join equal torus parity")
    return (left, right)


def exact_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    values = [[Fraction(value) for value in row] for row in matrix]
    columns = len(values[0]) if values else 0
    if any(len(row) != columns for row in values):
        raise NativeRootedTypeError("rank input must be rectangular")
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
        if rank == min(len(values), columns):
            break
    return rank


def exact_nullspace(matrix: Sequence[Sequence[Fraction]]) -> tuple[tuple[Fraction, ...], ...]:
    values = [[Fraction(value) for value in row] for row in matrix]
    columns = len(values[0]) if values else 0
    if any(len(row) != columns for row in values):
        raise NativeRootedTypeError("nullspace input must be rectangular")
    pivot_columns: list[int] = []
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, len(values)) if values[row][column]), None)
        if pivot is None:
            continue
        values[rank], values[pivot] = values[pivot], values[rank]
        divisor = values[rank][column]
        values[rank] = [value / divisor for value in values[rank]]
        for row in range(len(values)):
            if row != rank and values[row][column]:
                factor = values[row][column]
                values[row] = [value - factor * base
                               for value, base in zip(values[row], values[rank], strict=True)]
        pivot_columns.append(column)
        rank += 1
        if rank == len(values):
            break
    free_columns = [column for column in range(columns) if column not in pivot_columns]
    basis: list[tuple[Fraction, ...]] = []
    for free in free_columns:
        vector = [Fraction(0) for _ in range(columns)]
        vector[free] = Fraction(1)
        for row, pivot in enumerate(pivot_columns):
            vector[pivot] = -values[row][free]
        basis.append(tuple(vector))
    return tuple(basis)


def matrix_vector(matrix: Matrix, vector: Sequence[Fraction]) -> tuple[Fraction, ...]:
    if len(matrix) != len(vector):
        raise NativeRootedTypeError("matrix-vector dimensions differ")
    return tuple(sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
                 for row in matrix)


@lru_cache(maxsize=3)
def candidate_nullspace(seed: NativeSeed) -> tuple[tuple[Fraction, ...], ...]:
    validate_seed(seed)
    basis = exact_nullspace(seed.adjacency)
    expected = {2: 0, 3: 0, 4: 1}[seed.s]
    if len(basis) != expected:
        raise NativeRootedTypeError("candidate exact nullity changed")
    for vector in basis:
        if matrix_vector(seed.adjacency, vector) != (Fraction(0),) * seed.size:
            raise NativeRootedTypeError("exact null vector residual is nonzero")
    if seed.s == 4 and (basis[0][seed.entrance] or basis[0][seed.exit]):
        raise NativeRootedTypeError("s=4 null vector must vanish at entrance and exit")
    return basis


def common_kernel_difference_constraints(seed: NativeSeed) -> tuple[tuple[Fraction, ...], ...]:
    """Rows forced by control differences: all sources and destinations are side-constant."""
    validate_seed(seed)
    rows: list[tuple[Fraction, ...]] = []
    for roots in (seed.sources, seed.destinations):
        for vertex in roots[1:]:
            row = [Fraction(0) for _ in range(seed.size)]
            row[vertex], row[roots[0]] = Fraction(1), Fraction(-1)
            rows.append(tuple(row))
    return tuple(rows)


@lru_cache(maxsize=3)
def common_kernel_certificate(seed: NativeSeed) -> tuple[int, int]:
    validate_seed(seed)
    controls = tuple(permutations(range(5)))
    stacked: list[tuple[Fraction, ...]] = []
    for permutation in controls:
        control = control_adjacency(seed, permutation)
        certify_control(seed, permutation, control)
        stacked.extend(control)
    stacked_rank = exact_rank(stacked)
    constrained_rank = exact_rank(seed.adjacency + common_kernel_difference_constraints(seed))
    if stacked_rank != seed.size or constrained_rank != seed.size:
        raise NativeRootedTypeError("all-control common kernel must be trivial")
    return stacked_rank, seed.size - stacked_rank


def assess_candidate(
    seed: NativeSeed,
    claimed_direct_bipartite_chiral_compatible: bool = False,
    claimed_separation: bool = False,
) -> CompatibilityAssessment:
    if (type(claimed_direct_bipartite_chiral_compatible) is not bool
            or type(claimed_separation) is not bool):
        raise NativeRootedTypeError("theorem claims must be exact bools")
    if claimed_direct_bipartite_chiral_compatible:
        raise NativeRootedTypeError(DIRECT_BIPARTITE_CHIRAL_INCOMPATIBLE)
    if claimed_separation:
        raise NativeRootedTypeError("every affirmative separation claim fails closed")
    source, destination = certify_native_rooted_types(seed)
    root_fixing_implication = certify_root_fixing_implication(seed)
    certify_candidate_nonbipartite(seed)
    certify_no_endpoint_compression(seed)
    nullspace = candidate_nullspace(seed)
    _rank, common_dimension = common_kernel_certificate(seed)
    return CompatibilityAssessment(
        True,
        source,
        destination,
        root_fixing_implication,
        NO_CONCLUSION,
        DIRECT_BIPARTITE_CHIRAL_INCOMPATIBLE,
        SEPARATION_NO_CONCLUSION,
        len(nullspace),
        common_dimension,
    )


if __name__ == "__main__":
    for declared_s in (2, 3, 4):
        result = assess_candidate(build_seed(declared_s, 6))
        print(f"s={declared_s} native_types=yes nullity={result.candidate_nullity} "
              f"direct_bipartite_chiral_mechanism="
              f"{result.direct_bipartite_chiral_mechanism} separation=no-conclusion")
