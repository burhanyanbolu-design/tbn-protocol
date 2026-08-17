#!/usr/bin/env python3
"""Independent theorem and mutation tests for coordinate fingerprints."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import permutations
import math
import unittest

from candidate3_coordinate_fingerprint_lift import (
    CoordinateFingerprintError,
    GRIDS,
    all_genuine_permutations,
    build_seed,
    candidate_zero_vector,
    control_adjacency,
    control_certificate,
    edge_degree_profile,
    edge_weight_multiset,
    endpoint_moment,
    exact_rank,
    matrix_vector,
    quotient_matrix,
    require_positive_ldlt,
    validate_candidate,
    validate_chiral,
    validate_permutation,
    validate_quotient,
    validate_seed,
    validate_seed_shape,
    weighted_degrees,
)

LOCAL_Q = (2, 3, 4, 5, 6)


def local_index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def local_cells(s: int, rows: int) -> tuple[tuple[int, ...], ...]:
    count = rows * (s + 1)
    entrance = local_index(s, 0, 0)
    exit_state = local_index(s, rows - 1, s)
    sources = tuple(local_index(s, row, s) for row in range(rows - 1))
    destinations = tuple(local_index(s, row + 1, 0) for row in range(rows - 1))
    reserved = {entrance, exit_state, *sources, *destinations}
    unused = tuple(index for index in range(count) if index not in reserved)

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


def local_rank(matrix: tuple[tuple[Fraction, ...], ...]) -> int:
    values = [list(row) for row in matrix]
    columns = len(values[0]) if values else 0
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
    return rank


def local_sources(seed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[2:7]) + seed.cells[7]


def local_destinations(seed) -> tuple[int, ...]:
    return tuple(cell[0] for cell in seed.cells[8:13]) + seed.cells[13]


def local_factor(position: int) -> int:
    return LOCAL_Q[position] if position < 5 else 1


def local_adjacency(seed, permutation: tuple[int, ...]) -> tuple[tuple[Fraction, ...], ...]:
    matrix = [[Fraction(0) for _ in range(seed.size)] for _ in range(seed.size)]
    sources = local_sources(seed)
    destinations = local_destinations(seed)
    full_matching = permutation + tuple(range(5, seed.p))

    def add(left: int, right: int, weight: int) -> None:
        matrix[left][right] = Fraction(weight)
        matrix[right][left] = Fraction(weight)

    add(seed.entrance, seed.cells[1][0], 1)
    for position, source in enumerate(sources):
        add(seed.cells[1][0], source, local_factor(position))
    for source_position, destination_position in enumerate(full_matching):
        add(sources[source_position], destinations[destination_position], seed.matched_weight)
    for position, destination in enumerate(destinations):
        add(destination, seed.exit, local_factor(position))
    return tuple(tuple(row) for row in matrix)


def local_vector_product(matrix, vector) -> tuple[Fraction, ...]:
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def local_moment(matrix, entrance: int, exit_state: int, power: int) -> Fraction:
    state = tuple(Fraction(1) if vertex == entrance else Fraction(0) for vertex in range(len(matrix)))
    for _ in range(power):
        state = local_vector_product(matrix, state)
    return state[exit_state]


def local_edge_weights(matrix) -> tuple[Fraction, ...]:
    return tuple(sorted(
        matrix[left][right]
        for left in range(len(matrix))
        for right in range(left + 1, len(matrix))
        if matrix[left][right]
    ))


def local_degrees(matrix) -> tuple[Fraction, ...]:
    return tuple(sum(row, Fraction(0)) for row in matrix)


def local_profile(matrix) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    degrees = local_degrees(matrix)
    return tuple(sorted(
        (matrix[left][right], min(degrees[left], degrees[right]), max(degrees[left], degrees[right]))
        for left in range(len(matrix))
        for right in range(left + 1, len(matrix))
        if matrix[left][right]
    ))


def local_ldlt(matrix) -> tuple[Fraction, ...]:
    size = len(matrix)
    lower = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    pivots = [Fraction(0) for _ in range(size)]
    for row in range(size):
        lower[row][row] = Fraction(1)
        pivots[row] = matrix[row][row] - sum(
            (lower[row][index] ** 2 * pivots[index] for index in range(row)), Fraction(0)
        )
        if pivots[row] == 0:
            raise ArithmeticError("zero pivot")
        for target in range(row + 1, size):
            lower[target][row] = (
                matrix[target][row]
                - sum(
                    (lower[target][index] * lower[row][index] * pivots[index] for index in range(row)),
                    Fraction(0),
                )
            ) / pivots[row]
    return tuple(pivots)


def changed_seed(seed, left: int, right: int, value: Fraction):
    matrix = [list(row) for row in seed.adjacency]
    matrix[left][right] = value
    matrix[right][left] = value
    return replace(seed, adjacency=tuple(tuple(row) for row in matrix))



class CoordinateFingerprintPositiveTests(unittest.TestCase):
    def test_declared_candidates_pass_independent_exact_certificates(self) -> None:
        for s, rows in GRIDS:
            with self.subTest(s=s):
                seed = build_seed(s, rows)
                certificate = validate_seed(seed)
                p = rows * (s + 1) // 2 - 1
                h = p - 5
                weight = h + sum(value * value for value in LOCAL_Q)
                self.assertEqual(seed.cells, local_cells(s, rows))
                self.assertEqual((seed.p, seed.h, seed.matched_weight), (p, h, weight))
                self.assertEqual(seed.adjacency, local_adjacency(seed, tuple(range(5))))
                self.assertEqual(certificate.controls_checked, 119)

                expected_pairs = tuple(
                    (local_index(s, row, s), local_index(s, row + 1, 0))
                    for row in range(rows - 1)
                )
                self.assertEqual(seed.genuine_pairs, expected_pairs)
                self.assertEqual(seed.adjacency[seed.exit][seed.entrance], 0)

                quotient = quotient_matrix(seed)
                cell_of = {vertex: index for index, cell in enumerate(seed.cells) for vertex in cell}
                for vertex in range(seed.size):
                    for target_cell, targets in enumerate(seed.cells):
                        self.assertEqual(
                            sum((seed.adjacency[vertex][target] for target in targets), Fraction(0)),
                            quotient[cell_of[vertex]][target_cell],
                        )

                positive = (seed.entrance,) + local_sources(seed) + (seed.exit,)
                negative = (seed.cells[1][0],) + local_destinations(seed)
                self.assertEqual(len(positive) - len(negative), 1)
                for left in range(seed.size):
                    for right in range(left + 1, seed.size):
                        if seed.adjacency[left][right]:
                            self.assertNotEqual(left in positive, right in positive)

                local_zero = [Fraction(0) for _ in range(seed.size)]
                local_zero[seed.entrance] = local_zero[seed.exit] = -Fraction(weight)
                for position, source in enumerate(local_sources(seed)):
                    local_zero[source] = Fraction(local_factor(position))
                vector = tuple(local_zero)
                self.assertEqual(candidate_zero_vector(seed), vector)
                self.assertEqual(local_vector_product(seed.adjacency, vector), (Fraction(0),) * seed.size)
                self.assertEqual(local_rank(seed.adjacency), seed.size - 1)
                self.assertEqual(exact_rank(seed.adjacency), seed.size - 1)

                block = tuple(tuple(seed.adjacency[left][right] for right in negative) for left in positive)
                self.assertEqual(local_rank(block), p + 1)
                gram = tuple(tuple(
                    sum((block[row][left] * block[row][right] for row in range(len(block))), Fraction(0))
                    for right in range(len(negative))
                ) for left in range(len(negative)))
                shifted = tuple(tuple(
                    gram[row][column] - (Fraction(1) if row == column else Fraction(0))
                    for column in range(len(gram))
                ) for row in range(len(gram)))
                pivots = local_ldlt(shifted)
                self.assertTrue(all(pivot > 0 for pivot in pivots))
                self.assertEqual(certificate.ldlt_pivots, pivots)

                norm = sum((value * value for value in vector), Fraction(0))
                projector = abs(vector[seed.entrance] * vector[seed.exit]) / norm
                self.assertEqual(norm, Fraction(weight * (2 * weight + 1)))
                self.assertEqual(projector, Fraction(weight, 2 * weight + 1))
                self.assertEqual(certificate.endpoint_weight, projector)
                self.assertEqual(certificate.zero_projector_endpoint_element, projector)
                self.assertEqual(local_moment(seed.adjacency, seed.entrance, seed.exit, 4), Fraction(weight * weight))
                self.assertEqual(certificate.candidate_fourth_moment, Fraction(weight * weight))
                self.assertGreater(certificate.numerical_gap, 1.0)
                self.assertTrue(math.isfinite(certificate.numerical_gap))

    def test_all_119_genuine_controls_are_pointwise_fair_and_separated(self) -> None:
        local_controls = tuple(value for value in permutations(range(5)) if value != tuple(range(5)))
        self.assertEqual(len(local_controls), 119)
        self.assertEqual(all_genuine_permutations(), local_controls)
        for s, rows in GRIDS:
            seed = build_seed(s, rows)
            candidate_weights = local_edge_weights(seed.adjacency)
            candidate_degrees = local_degrees(seed.adjacency)
            candidate_profile = local_profile(seed.adjacency)
            for permutation in local_controls:
                with self.subTest(s=s, permutation=permutation):
                    control = local_adjacency(seed, permutation)
                    self.assertEqual(control_adjacency(seed, permutation), control)
                    self.assertEqual(local_edge_weights(control), candidate_weights)
                    self.assertEqual(local_degrees(control), candidate_degrees)
                    self.assertNotEqual(local_profile(control), candidate_profile)
                    self.assertEqual(local_rank(control), seed.size - 1)
                    quotient_matrix(seed, control)

                    correlation = Fraction(seed.h + sum(
                        LOCAL_Q[index] * LOCAL_Q[permutation[index]] for index in range(5)
                    ))
                    displacement = Fraction(sum(
                        (LOCAL_Q[index] - LOCAL_Q[permutation[index]]) ** 2 for index in range(5)
                    ), 2)
                    self.assertEqual(Fraction(seed.matched_weight) - correlation, displacement)
                    moment = local_moment(control, seed.entrance, seed.exit, 4)
                    self.assertEqual(moment, Fraction(seed.matched_weight) * correlation)
                    self.assertEqual(
                        Fraction(seed.matched_weight ** 2) - moment,
                        Fraction(seed.matched_weight) * displacement,
                    )
                    certificate = control_certificate(seed, permutation, control, moment)
                    self.assertTrue(certificate.fair_weight_multiset)
                    self.assertTrue(certificate.fair_vertex_weighted_degrees)
                    self.assertTrue(certificate.edge_degree_profile_differs)
                    self.assertEqual(certificate.correlation, correlation)
                    self.assertEqual(certificate.displacement_energy, displacement)
                    self.assertEqual(certificate.control_fourth_moment, moment)

                    zero = [Fraction(0) for _ in range(seed.size)]
                    zero[seed.entrance] = -correlation
                    zero[seed.exit] = -Fraction(seed.matched_weight)
                    full_matching = permutation + tuple(range(5, seed.p))
                    for source_position, destination_position in enumerate(full_matching):
                        zero[local_sources(seed)[source_position]] = Fraction(local_factor(destination_position))
                    zero_vector = tuple(zero)
                    self.assertEqual(local_vector_product(control, zero_vector), (Fraction(0),) * seed.size)
                    norm = correlation ** 2 + seed.matched_weight + seed.matched_weight ** 2
                    self.assertEqual(certificate.zero_norm_squared, norm)
                    self.assertEqual(certificate.entrance_weight, correlation ** 2 / norm)
                    self.assertEqual(certificate.exit_weight, Fraction(seed.matched_weight ** 2, 1) / norm)
                    self.assertEqual(
                        certificate.zero_projector_endpoint_element,
                        Fraction(seed.matched_weight) * correlation / norm,
                    )

    def test_undeclared_grids_are_rejected(self) -> None:
        for args in ((1, 6), (2, 5), (5, 6), (2.0, 6)):
            with self.subTest(args=args), self.assertRaises(CoordinateFingerprintError):
                build_seed(*args)  # type: ignore[arg-type]



class CoordinateFingerprintMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = build_seed(2, 6)
        self.permutation = (1, 0, 2, 3, 4)

    def test_malformed_partition_is_rejected(self) -> None:
        cells = [list(cell) for cell in self.seed.cells]
        cells[7][-1] = cells[7][0]
        malformed = replace(self.seed, cells=tuple(tuple(cell) for cell in cells))
        with self.assertRaises(CoordinateFingerprintError):
            validate_seed_shape(malformed)

    def test_wrong_candidate_weight_and_false_periodic_edge_are_rejected(self) -> None:
        source, destination = self.seed.genuine_pairs[0]
        malformed = changed_seed(self.seed, source, destination, Fraction(self.seed.matched_weight + 1))
        with self.assertRaises(CoordinateFingerprintError):
            validate_candidate(malformed)
        periodic = changed_seed(self.seed, self.seed.exit, self.seed.entrance, Fraction(1))
        with self.assertRaises(CoordinateFingerprintError):
            validate_candidate(periodic)

    def test_quotient_and_chiral_breaks_are_rejected(self) -> None:
        hub, source = self.seed.cells[1][0], self.seed.cells[2][0]
        closure_break = changed_seed(self.seed, hub, source, Fraction(99))
        with self.assertRaises(CoordinateFingerprintError):
            validate_quotient(closure_break)
        same_sublattice = changed_seed(self.seed, self.seed.entrance, source, Fraction(1))
        with self.assertRaises(CoordinateFingerprintError):
            validate_chiral(same_sublattice)

    def test_invalid_or_identity_permutations_are_rejected(self) -> None:
        bad = ((0, 1, 2, 3), (0, 1, 2, 3, 3), (0, 1, 2, 3, 5), (0.0, 1, 2, 3, 4))
        for permutation in bad:
            with self.subTest(permutation=permutation), self.assertRaises(CoordinateFingerprintError):
                validate_permutation(permutation)  # type: ignore[arg-type]
        with self.assertRaises(CoordinateFingerprintError):
            control_certificate(self.seed, tuple(range(5)))
        with self.assertRaises(CoordinateFingerprintError):
            all_genuine_permutations(1)  # type: ignore[arg-type]

    def test_unfair_override_and_false_moment_claim_fail_closed(self) -> None:
        control = control_adjacency(self.seed, self.permutation)
        matrix = [list(row) for row in control]
        left, right = next(
            (left, right)
            for left in range(self.seed.size)
            for right in range(left + 1, self.seed.size)
            if matrix[left][right]
        )
        matrix[left][right] += 1
        matrix[right][left] += 1
        unfair = tuple(tuple(row) for row in matrix)
        with self.assertRaises(CoordinateFingerprintError):
            control_certificate(self.seed, self.permutation, unfair)
        actual = endpoint_moment(control, self.seed.entrance, self.seed.exit, 4)
        with self.assertRaises(CoordinateFingerprintError):
            control_certificate(self.seed, self.permutation, control, actual + 1)
        with self.assertRaises(CoordinateFingerprintError):
            control_certificate(self.seed, self.permutation, control, int(actual))  # type: ignore[arg-type]

    def test_extra_nullity_and_nonpositive_ldlt_fail_closed(self) -> None:
        source = local_sources(self.seed)[0]
        destination = local_destinations(self.seed)[0]
        disconnected = changed_seed(self.seed, source, destination, Fraction(0))
        disconnected = changed_seed(disconnected, destination, self.seed.exit, Fraction(0))
        self.assertLess(local_rank(disconnected.adjacency), disconnected.size - 1)
        with self.assertRaises(CoordinateFingerprintError):
            validate_seed(disconnected)
        with self.assertRaises(CoordinateFingerprintError):
            require_positive_ldlt(((Fraction(0), Fraction(0)), (Fraction(0), Fraction(1))))
        with self.assertRaises(CoordinateFingerprintError):
            require_positive_ldlt(((Fraction(-1),),))

    def test_public_helpers_match_independent_values(self) -> None:
        control = local_adjacency(self.seed, self.permutation)
        self.assertEqual(edge_weight_multiset(control), local_edge_weights(control))
        self.assertEqual(weighted_degrees(control), local_degrees(control))
        self.assertEqual(edge_degree_profile(control), local_profile(control))
        vector = candidate_zero_vector(self.seed)
        self.assertEqual(matrix_vector(self.seed.adjacency, vector), local_vector_product(self.seed.adjacency, vector))


if __name__ == "__main__":
    unittest.main(verbosity=2)