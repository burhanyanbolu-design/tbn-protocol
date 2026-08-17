#!/usr/bin/env python3
"""Tests: direct natural Candidate 3 bipartite/chiral mechanism incompatible."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import permutations
import unittest

from candidate3_native_rooted_type_compatibility import (
    NativeRootedTypeError,
    assess_candidate,
    build_seed,
    candidate_nullspace,
    certify_candidate_nonbipartite,
    certify_control,
    certify_native_rooted_types,
    certify_no_endpoint_compression,
    certify_root_fixing_automorphism,
    certify_root_fixing_implication,
    column_partition,
    common_kernel_certificate,
    common_kernel_difference_constraints,
    control_adjacency,
    endpoint_seed_partition,
    endpoint_signatures,
    equitable_refinement,
    exact_rank,
    overlap_fiber_partition,
    partition_properties,
    reflection_partition,
    row_partition,
    validate_permutation,
    validate_seed,
)

LOCAL_GRIDS = ((2, 6), (3, 6), (4, 6))
LOCAL_IDENTITY = (0, 1, 2, 3, 4)
LOCAL_PERMUTATIONS = tuple(permutations(range(5)))
LOCAL_RANK_PRIME = 101
LOCAL_S4_NULL_ROWS = (
    (0, -1, -1, 0, 1),
    (1, 1, 0, -1, -1),
    (-1, 0, 1, 1, 0),
    (0, -1, -1, 0, 1),
    (1, 1, 0, -1, -1),
    (-1, 0, 1, 1, 0),
)
LOCAL_S4_NULL_VECTOR = tuple(Fraction(value) for row in LOCAL_S4_NULL_ROWS for value in row)


def local_index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def local_roots(s: int, rows: int):
    return (
        local_index(s, 0, 0),
        local_index(s, rows - 1, s),
        tuple(local_index(s, index, s) for index in range(5)),
        tuple(local_index(s, index + 1, 0) for index in range(5)),
    )


def local_native_edges(s: int, rows: int):
    edges = set()
    width = s + 1
    for row in range(rows):
        for column in range(width):
            here = local_index(s, row, column)
            edges.add(tuple(sorted((here, local_index(s, (row + 1) % rows, column)))))
            edges.add(tuple(sorted((here, local_index(s, row, (column + 1) % width)))))
    return tuple(sorted(edges))


def local_matrix(s: int, rows: int, permutation=LOCAL_IDENTITY, matching: bool = True):
    size = rows * (s + 1)
    matrix = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    for left, right in local_native_edges(s, rows):
        if left == right or matrix[left][right]:
            raise AssertionError("independent native edge is invalid")
        matrix[left][right] = matrix[right][left] = Fraction(1)
    if matching:
        _entrance, _exit, sources, destinations = local_roots(s, rows)
        for index, image in enumerate(permutation):
            left, right = sources[index], destinations[image]
            matrix[left][right] += Fraction(1)
            matrix[right][left] += Fraction(1)
    return tuple(tuple(row) for row in matrix)


def local_distances(matrix, start):
    distances = [-1] * len(matrix)
    distances[start] = 0
    queue = [start]
    for vertex in queue:
        for neighbour, weight in enumerate(matrix[vertex]):
            if weight and distances[neighbour] < 0:
                distances[neighbour] = distances[vertex] + 1
                queue.append(neighbour)
    if any(value < 0 for value in distances):
        raise AssertionError("independent graph disconnected")
    return tuple(distances)


def local_signatures(s: int, rows: int):
    entrance, exit_state, sources, destinations = local_roots(s, rows)
    native = local_matrix(s, rows, matching=False)
    from_entrance = local_distances(native, entrance)
    from_exit = local_distances(native, exit_state)
    get = lambda vertex: (from_entrance[vertex], from_exit[vertex])
    return tuple(get(item) for item in sources), tuple(get(item) for item in destinations)


def local_degrees(matrix):
    return tuple(sum(row, Fraction(0)) for row in matrix)


def local_channel_weights(s, rows, permutation=LOCAL_IDENTITY):
    size = rows * (s + 1)
    incident = [[] for _ in range(size)]
    _entrance, _exit, sources, destinations = local_roots(s, rows)
    channels = local_native_edges(s, rows) + tuple(
        (sources[index], destinations[permutation[index]]) for index in range(5))
    for left, right in channels:
        incident[left].append(Fraction(1))
        incident[right].append(Fraction(1))
    return tuple(tuple(sorted(values)) for values in incident)


def local_product(matrix, vector):
    return tuple(sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
                 for row in matrix)


def local_is_prime(value):
    if type(value) is not int or value < 2:
        return False
    return all(value % divisor for divisor in range(2, int(value ** 0.5) + 1))


def local_modular_rank(matrix, prime=LOCAL_RANK_PRIME):
    """Independent rank lower bound over a checked prime for integral Fractions."""
    if not local_is_prime(prime):
        raise AssertionError("independent modular-rank modulus must be prime")
    rows = tuple(tuple(row) for row in matrix)
    columns = len(rows[0]) if rows else 0
    if any(len(row) != columns for row in rows):
        raise AssertionError("independent modular-rank input must be rectangular")
    if any(type(value) is not Fraction or value.denominator != 1
           for row in rows for value in row):
        raise AssertionError("independent modular rank requires integral Fractions")
    values = [[value.numerator % prime for value in row] for row in rows]
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, len(values))
                      if values[row][column] % prime), None)
        if pivot is None:
            continue
        values[rank], values[pivot] = values[pivot], values[rank]
        inverse = pow(values[rank][column], -1, prime)
        values[rank] = [(value * inverse) % prime for value in values[rank]]
        for row in range(rank + 1, len(values)):
            factor = values[row][column] % prime
            if factor:
                values[row] = [
                    (value - factor * base) % prime
                    for value, base in zip(values[row], values[rank], strict=True)
                ]
        rank += 1
        if rank == min(len(values), columns):
            break
    return rank


def local_nonzero_scalar_multiple(left, right):
    if len(left) != len(right) or not any(right):
        return False
    pivot = next(index for index, value in enumerate(right) if value)
    scalar = left[pivot] / right[pivot]
    return scalar != 0 and all(a == scalar * b for a, b in zip(left, right, strict=True))


def local_partition_properties(matrix, partition, entrance, exit_state):
    equitable = True
    for cell in partition:
        signatures = {
            tuple(sum((matrix[vertex][target] for target in targets), Fraction(0))
                  for targets in partition)
            for vertex in cell
        }
        equitable &= len(signatures) == 1
    entrance_cell = next(cell for cell in partition if entrance in cell)
    exit_cell = next(cell for cell in partition if exit_state in cell)
    return {
        "cell_count": len(partition),
        "equitable": equitable,
        "endpoint_representing": entrance_cell == (entrance,) and exit_cell == (exit_state,),
        "endpoints_separate": entrance_cell != exit_cell,
        "strict_compression": len(partition) < len(matrix),
    }


def local_refinement(matrix, partition):
    current = tuple(tuple(cell) for cell in partition)
    while True:
        refined = []
        for cell in current:
            buckets = {}
            for vertex in cell:
                signature = tuple(sum((matrix[vertex][target] for target in targets), Fraction(0))
                                  for targets in current)
                buckets.setdefault(signature, []).append(vertex)
            refined.extend(tuple(value) for value in sorted(buckets.values(), key=lambda item: item[0]))
        result = tuple(refined)
        if result == current:
            return result
        current = result


def local_partitions(s: int, rows: int):
    entrance, exit_state, sources, destinations = local_roots(s, rows)
    row_cells = tuple(tuple(local_index(s, row, column) for column in range(s + 1))
                      for row in range(rows))
    column_cells = tuple(tuple(local_index(s, row, column) for row in range(rows))
                         for column in range(s + 1))
    overlap = ((entrance,), (exit_state,))
    overlap += tuple((sources[index], destinations[index]) for index in range(5))
    overlap += tuple(tuple(local_index(s, row, column) for row in range(rows))
                     for column in range(1, s))
    remaining = set(range(rows * (s + 1)))
    reflection = []
    while remaining:
        first = min(remaining)
        row, column = divmod(first, s + 1)
        image = local_index(s, rows - 1 - row, s - column)
        cell = tuple(sorted({first, image}))
        reflection.append(cell)
        remaining.difference_update(cell)
    seed = ((entrance,), (exit_state,), tuple(vertex for vertex in range(rows * (s + 1))
                                              if vertex not in (entrance, exit_state)))
    return row_cells, column_cells, overlap, tuple(reflection), seed


def local_bipartite(matrix):
    colours = [None] * len(matrix)
    for start in range(len(matrix)):
        if colours[start] is not None:
            continue
        colours[start] = 0
        pending = [start]
        while pending:
            vertex = pending.pop()
            for neighbour, weight in enumerate(matrix[vertex]):
                if not weight:
                    continue
                if colours[neighbour] is None:
                    colours[neighbour] = 1 - colours[vertex]
                    pending.append(neighbour)
                elif colours[neighbour] == colours[vertex]:
                    return False
    return True


def mutate_edge(matrix, left, right, value):
    changed = [list(row) for row in matrix]
    changed[left][right] = changed[right][left] = value
    return tuple(tuple(row) for row in changed)


class NativeRootedExactTests(unittest.TestCase):
    def test_fixed_grids_topology_endpoints_roots_and_identity_candidate_reconstruct(self):
        for s, rows in LOCAL_GRIDS:
            with self.subTest(s=s):
                seed = build_seed(s, rows)
                entrance, exit_state, sources, destinations = local_roots(s, rows)
                labels = tuple((row, column) for row in range(rows) for column in range(s + 1))
                self.assertEqual(seed.labels, labels)
                self.assertEqual((seed.entrance, seed.exit), (entrance, exit_state))
                self.assertEqual((seed.sources, seed.destinations), (sources, destinations))
                self.assertEqual(seed.native_edges, local_native_edges(s, rows))
                self.assertEqual(seed.adjacency, local_matrix(s, rows))
                self.assertEqual(len(seed.native_edges), 2 * len(labels))
                validate_seed(seed)

    def test_native_backbone_derives_exact_distinct_signatures_on_every_grid(self):
        expected_source = ((1, 1), (2, 2), (3, 3), (4, 2), (3, 1))
        expected_destination = ((1, 3), (2, 4), (3, 3), (2, 2), (1, 1))
        for s, rows in LOCAL_GRIDS:
            independent = local_signatures(s, rows)
            self.assertEqual(independent, (expected_source, expected_destination))
            self.assertEqual(endpoint_signatures(build_seed(s, rows)), independent)
            self.assertEqual(certify_native_rooted_types(build_seed(s, rows)), independent)
            self.assertEqual((len(set(independent[0])), len(set(independent[1]))), (5, 5))

    def test_endpoint_fixing_side_preserving_native_automorphisms_fix_roots(self):
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            self.assertTrue(certify_root_fixing_implication(seed))
            identity = tuple(range(seed.size))
            self.assertEqual(certify_root_fixing_automorphism(seed, identity), identity)

    def test_all_120_controls_all_grids_reconstruct_and_preserve_named_fairness(self):
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            candidate = local_matrix(s, rows)
            degrees = local_degrees(candidate)
            incident = local_channel_weights(s, rows)
            for permutation in LOCAL_PERMUTATIONS:
                control = local_matrix(s, rows, permutation)
                self.assertEqual(control_adjacency(seed, permutation), control)
                self.assertEqual(local_degrees(control), degrees)
                self.assertEqual(local_channel_weights(s, rows, permutation), incident)
                certificate = certify_control(seed, permutation, control)
                self.assertTrue(certificate.fair_weighted_degrees)
                self.assertTrue(certificate.fair_edge_weight_multisets)

    def test_direct_candidate_nonbipartite_with_exact_declared_witnesses(self):
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            matrix = local_matrix(s, rows)
            self.assertFalse(local_bipartite(matrix))
            witness = certify_candidate_nonbipartite(seed)
            if s in (2, 4):
                self.assertEqual(len(witness), s + 1)
                self.assertEqual(len(witness) % 2, 1)
                for left, right in zip(witness, witness[1:] + witness[:1], strict=True):
                    self.assertEqual(matrix[left][right], Fraction(1))
            else:
                left, right = witness
                self.assertEqual((sum(seed.labels[left]) - sum(seed.labels[right])) % 2, 0)
                self.assertEqual((left, right), (seed.sources[0], seed.destinations[0]))

    def test_endpoint_seeded_refinement_is_discrete_on_18_24_30_vertices(self):
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            matrix = local_matrix(s, rows)
            local_cells = local_partitions(s, rows)[-1]
            independent = local_refinement(matrix, local_cells)
            self.assertEqual(len(independent), rows * (s + 1))
            self.assertTrue(all(len(cell) == 1 for cell in independent))
            self.assertEqual(endpoint_seed_partition(seed), local_cells)
            self.assertEqual(equitable_refinement(seed.adjacency, local_cells), independent)
            self.assertEqual(certify_no_endpoint_compression(seed), independent)

    def test_natural_partitions_fail_combination_and_reflection_merges_endpoints(self):
        required = ("equitable", "endpoint_representing", "endpoints_separate", "strict_compression")
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            matrix = local_matrix(s, rows)
            independent = local_partitions(s, rows)
            production = (row_partition(seed), column_partition(seed), overlap_fiber_partition(seed),
                          reflection_partition(seed))
            self.assertEqual(production, independent[:4])
            for cells in independent[:3]:
                report = local_partition_properties(matrix, cells, seed.entrance, seed.exit)
                self.assertFalse(all(report[key] for key in required))
                self.assertEqual(partition_properties(seed, cells), report)
            reflected = independent[3]
            endpoint_cell = next(cell for cell in reflected if seed.entrance in cell)
            self.assertIn(seed.exit, endpoint_cell)
            self.assertFalse(local_partition_properties(
                matrix, reflected, seed.entrance, seed.exit)["endpoints_separate"])

    def test_modular_candidate_ranks_and_independent_s4_nullity_witness(self):
        self.assertTrue(local_is_prime(LOCAL_RANK_PRIME))
        with self.assertRaises(AssertionError):
            local_modular_rank(((Fraction(1, 2),),))
        expected_ranks = {2: 18, 3: 24, 4: 29}
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            matrix = local_matrix(s, rows)
            modular_rank = local_modular_rank(matrix)
            self.assertEqual(modular_rank, expected_ranks[s])
            self.assertEqual(exact_rank(seed.adjacency), expected_ranks[s])
            basis = candidate_nullspace(seed)
            self.assertEqual(len(basis), len(matrix) - expected_ranks[s])
            for vector in basis:
                self.assertEqual(local_product(matrix, vector), (Fraction(0),) * len(matrix))
            if s == 4:
                self.assertEqual(len(LOCAL_S4_NULL_VECTOR), len(matrix))
                self.assertTrue(any(LOCAL_S4_NULL_VECTOR))
                self.assertEqual(
                    local_product(matrix, LOCAL_S4_NULL_VECTOR),
                    (Fraction(0),) * len(matrix),
                )
                self.assertEqual(
                    (LOCAL_S4_NULL_VECTOR[seed.entrance], LOCAL_S4_NULL_VECTOR[seed.exit]),
                    (Fraction(0), Fraction(0)),
                )
                # Rank over Q is at least the modular rank 29 and at most 29
                # because this nonzero exact kernel witness exists: nullity is one.
                self.assertEqual(seed.size - modular_rank, 1)
                self.assertTrue(local_nonzero_scalar_multiple(basis[0], LOCAL_S4_NULL_VECTOR))

    def test_all_120_control_stack_has_full_rank_and_no_common_zero_mode(self):
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            stacked = tuple(row for permutation in LOCAL_PERMUTATIONS
                            for row in local_matrix(s, rows, permutation))
            independent_rank = local_modular_rank(stacked)
            self.assertEqual(independent_rank, seed.size)
            self.assertEqual(common_kernel_certificate(seed), (seed.size, 0))

    def test_common_kernel_difference_rows_force_each_side_constant(self):
        for s, rows in LOCAL_GRIDS:
            seed = build_seed(s, rows)
            constraints = common_kernel_difference_constraints(seed)
            self.assertEqual(len(constraints), 8)
            for side_index, roots in enumerate((seed.sources, seed.destinations)):
                for offset, vertex in enumerate(roots[1:]):
                    row = constraints[side_index * 4 + offset]
                    expected = [Fraction(0)] * seed.size
                    expected[vertex], expected[roots[0]] = Fraction(1), Fraction(-1)
                    self.assertEqual(row, tuple(expected))
            constrained = local_matrix(s, rows) + constraints
            self.assertEqual(local_modular_rank(constrained), seed.size)

            identity = local_matrix(s, rows)
            for index in range(1, 5):
                swap = list(LOCAL_IDENTITY)
                swap[0], swap[index] = swap[index], swap[0]
                changed = local_matrix(s, rows, tuple(swap))
                source_difference = tuple(identity[seed.sources[0]][column]
                                          - changed[seed.sources[0]][column]
                                          for column in range(seed.size))
                destination_difference = tuple(identity[seed.destinations[0]][column]
                                               - changed[seed.destinations[0]][column]
                                               for column in range(seed.size))
                self.assertEqual(source_difference,
                                 tuple(-value for value in constraints[4 + index - 1]))
                self.assertEqual(destination_difference,
                                 tuple(-value for value in constraints[index - 1]))

    def test_final_assessment_is_exactly_yes_incompatible_and_no_conclusion(self):
        for s, rows in LOCAL_GRIDS:
            result = assess_candidate(build_seed(s, rows))
            self.assertTrue(result.native_rooted_types)
            self.assertTrue(
                result.roots_fixed_by_endpoint_fixing_side_preserving_native_automorphisms
            )
            self.assertEqual(result.repeated_type_status, "obstruction absent / no conclusion")
            self.assertEqual(
                result.direct_bipartite_chiral_mechanism,
                "direct natural Candidate 3 bipartite/chiral mechanism incompatible",
            )
            self.assertEqual(result.separation, "separation no conclusion")
            self.assertEqual(result.common_kernel_dimension, 0)


class NativeRootedFailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = build_seed(2, 6)
        cls.swap = (1, 0, 2, 3, 4)

    def test_undeclared_grids_and_malformed_permutations_rejected(self):
        for args in ((1, 6), (5, 6), (2, 5), (2.0, 6)):
            with self.subTest(args=args), self.assertRaises(NativeRootedTypeError):
                build_seed(*args)
        for value in ((0, 1, 2, 3), (0, 1, 2, 3, 3), (0, 1, 2, 3, 5),
                      (0.0, 1, 2, 3, 4)):
            with self.subTest(value=value), self.assertRaises(NativeRootedTypeError):
                validate_permutation(value)

    def test_changed_labels_endpoints_root_sets_and_native_topology_rejected(self):
        labels = list(self.seed.labels)
        labels[1] = (99, 99)
        source = list(self.seed.sources)
        source[0] = source[1]
        edges = self.seed.native_edges[1:]
        mutations = (
            replace(self.seed, labels=tuple(labels)),
            replace(self.seed, entrance=self.seed.exit),
            replace(self.seed, exit=self.seed.entrance),
            replace(self.seed, sources=tuple(source)),
            replace(self.seed, destinations=tuple(reversed(self.seed.destinations))),
            replace(self.seed, native_edges=edges),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(NativeRootedTypeError):
                validate_seed(mutation)

    def test_omitted_native_edge_changed_weight_foreign_edge_and_nonidentity_candidate_rejected(self):
        left, right = self.seed.native_edges[0]
        omitted = mutate_edge(self.seed.adjacency, left, right, Fraction(0))
        changed = mutate_edge(self.seed.adjacency, left, right, Fraction(2))
        zero_pair = next((a, b) for a in range(self.seed.size) for b in range(a + 1, self.seed.size)
                         if not self.seed.adjacency[a][b])
        foreign = mutate_edge(self.seed.adjacency, *zero_pair, Fraction(1))
        nonidentity = control_adjacency(self.seed, self.swap)
        for matrix in (omitted, changed, foreign, nonidentity):
            with self.subTest(), self.assertRaises(NativeRootedTypeError):
                validate_seed(replace(self.seed, adjacency=matrix))

    def test_fake_type_metadata_and_endpoint_movement_rejected(self):
        real_source, real_destination = local_signatures(2, 6)
        fake_source = list(real_source)
        fake_source[0] = (9, 9)
        with self.assertRaises(NativeRootedTypeError):
            certify_native_rooted_types(self.seed, fake_source, real_destination)
        with self.assertRaises(NativeRootedTypeError):
            certify_native_rooted_types(self.seed, real_source, tuple(reversed(real_destination)))
        endpoint_moving = list(range(self.seed.size))
        endpoint_moving[self.seed.entrance], endpoint_moving[self.seed.exit] = (
            endpoint_moving[self.seed.exit], endpoint_moving[self.seed.entrance])
        with self.assertRaises(NativeRootedTypeError):
            certify_root_fixing_automorphism(self.seed, endpoint_moving)
        malformed = list(range(self.seed.size))
        malformed[-1] = malformed[-2]
        with self.assertRaises(NativeRootedTypeError):
            certify_root_fixing_automorphism(self.seed, malformed)

    def test_endpoint_fixed_side_preserving_bijection_that_is_not_native_automorphism_rejected(self):
        not_an_automorphism = list(range(self.seed.size))
        not_an_automorphism[1], not_an_automorphism[4] = (
            not_an_automorphism[4], not_an_automorphism[1]
        )
        self.assertEqual(not_an_automorphism[self.seed.entrance], self.seed.entrance)
        self.assertEqual(not_an_automorphism[self.seed.exit], self.seed.exit)
        self.assertEqual(
            {not_an_automorphism[item] for item in self.seed.sources}, set(self.seed.sources)
        )
        self.assertEqual(
            {not_an_automorphism[item] for item in self.seed.destinations},
            set(self.seed.destinations),
        )
        with self.assertRaisesRegex(NativeRootedTypeError, "not a native weighted automorphism"):
            certify_root_fixing_automorphism(self.seed, not_an_automorphism)

    def test_control_foreign_edges_changed_weights_and_wrong_matching_rejected(self):
        control = control_adjacency(self.seed, self.swap)
        left, right = self.seed.sources[0], self.seed.destinations[1]
        changed = mutate_edge(control, left, right, Fraction(2))
        zero_pair = next((a, b) for a in range(self.seed.size) for b in range(a + 1, self.seed.size)
                         if not control[a][b])
        foreign = mutate_edge(control, *zero_pair, Fraction(1))
        for matrix in (changed, foreign, self.seed.adjacency):
            with self.subTest(), self.assertRaises(NativeRootedTypeError):
                certify_control(self.seed, self.swap, matrix)

    def test_false_bipartite_compression_compatibility_and_separation_claims_rejected(self):
        with self.assertRaises(NativeRootedTypeError):
            certify_candidate_nonbipartite(self.seed, claimed_bipartite=True)
        with self.assertRaises(NativeRootedTypeError):
            certify_no_endpoint_compression(self.seed, claimed_compression=True)
        with self.assertRaisesRegex(
            NativeRootedTypeError,
            "^direct natural Candidate 3 bipartite/chiral mechanism incompatible$",
        ):
            assess_candidate(self.seed, claimed_direct_bipartite_chiral_compatible=True)
        with self.assertRaises(NativeRootedTypeError):
            assess_candidate(self.seed, claimed_separation=True)
        for permutation in (LOCAL_IDENTITY, self.swap):
            with self.subTest(permutation=permutation), self.assertRaises(NativeRootedTypeError):
                certify_control(self.seed, permutation, claimed_separation=True)
        with self.assertRaises(NativeRootedTypeError):
            certify_control(self.seed, self.swap, claimed_separation=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
