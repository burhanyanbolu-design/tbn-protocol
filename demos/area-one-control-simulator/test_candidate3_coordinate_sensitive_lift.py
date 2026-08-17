#!/usr/bin/env python3
"""Independent theorem and mutation tests for the coordinate-sensitive lift."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import math
import unittest

from candidate3_coordinate_sensitive_lift import (
    CoordinateSensitiveError,
    CoordinateSensitiveSeed,
    GRIDS,
    canonical_cross_permutation,
    control_adjacency,
    control_certificate,
    edge_degree_profile,
    edge_weight_multiset,
    endpoint_moment,
    exact_rank,
    expected_candidate_fourth_moment,
    matrix_vector,
    quotient_matrix,
    require_positive_ldlt,
    validate_chiral,
    validate_coordinates_and_cells,
    validate_declared_candidate,
    validate_permutation,
    validate_quotient,
    validate_seed,
    validate_zero_rank_and_gap,
    weighted_degrees,
    zero_vector,
    build_seed,
)


def local_index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def local_rank(matrix: tuple[tuple[Fraction, ...], ...]) -> int:
    values = [list(row) for row in matrix]
    rank = 0
    columns = len(values[0]) if values else 0
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
        sources,
        unused[:half],
        destinations,
        unused[half:],
        (exit_state,),
    )


def local_quotient(g: int, h: int, balance: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(Fraction(value) for value in row) for row in (
        (0, 1, 0, 0, 0, 0, 0),
        (1, 0, 2 * g, h, 0, 0, 0),
        (0, 2, 0, 0, balance, 0, 0),
        (0, 1, 0, 0, 0, balance, 0),
        (0, 0, balance, 0, 0, 0, 2),
        (0, 0, 0, balance, 0, 0, 1),
        (0, 0, 0, 0, 2 * g, h, 0),
    ))


def local_cross_permutation(p: int, g: int, cross_count: int) -> tuple[int, ...]:
    permutation = list(range(p))
    for offset in range(cross_count):
        permutation[offset], permutation[g + offset] = g + offset, offset
    return tuple(permutation)


def local_adjacency(
    seed: CoordinateSensitiveSeed, permutation: tuple[int, ...],
) -> tuple[tuple[Fraction, ...], ...]:
    matrix = [[Fraction(0) for _ in range(seed.size)] for _ in range(seed.size)]
    sources = seed.cells[2] + seed.cells[3]
    destinations = seed.cells[4] + seed.cells[5]

    def add(left: int, right: int, weight: int) -> None:
        matrix[left][right] = Fraction(weight)
        matrix[right][left] = Fraction(weight)

    add(seed.entrance, seed.cells[1][0], 1)
    for position, vertex in enumerate(sources):
        add(seed.cells[1][0], vertex, 2 if position < seed.g else 1)
    for source_position, destination_position in enumerate(permutation):
        add(sources[source_position], destinations[destination_position], seed.balance)
    for position, vertex in enumerate(destinations):
        add(vertex, seed.exit, 2 if position < seed.g else 1)
    return tuple(tuple(row) for row in matrix)


def local_matrix_vector(
    matrix: tuple[tuple[Fraction, ...], ...], vector: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def local_moment(
    matrix: tuple[tuple[Fraction, ...], ...], entrance: int, exit_state: int, power: int,
) -> Fraction:
    state = tuple(
        Fraction(1) if vertex == entrance else Fraction(0)
        for vertex in range(len(matrix))
    )
    for _ in range(power):
        state = local_matrix_vector(matrix, state)
    return state[exit_state]


def local_ldlt_pivots(
    matrix: tuple[tuple[Fraction, ...], ...],
) -> tuple[Fraction, ...]:
    size = len(matrix)
    lower = [[Fraction(0) for _ in range(size)] for _ in range(size)]
    pivots = [Fraction(0) for _ in range(size)]
    for row in range(size):
        lower[row][row] = Fraction(1)
        pivots[row] = matrix[row][row] - sum(
            (lower[row][index] ** 2 * pivots[index] for index in range(row)),
            Fraction(0),
        )
        if pivots[row] == 0:
            raise ArithmeticError("zero pivot")
        for target in range(row + 1, size):
            lower[target][row] = (
                matrix[target][row]
                - sum(
                    (
                        lower[target][index]
                        * lower[row][index]
                        * pivots[index]
                        for index in range(row)
                    ),
                    Fraction(0),
                )
            ) / pivots[row]
    return tuple(pivots)


def changed_adjacency(
    seed: CoordinateSensitiveSeed,
    changes: tuple[tuple[int, int, Fraction], ...],
) -> CoordinateSensitiveSeed:
    matrix = [list(row) for row in seed.adjacency]
    for left, right, value in changes:
        matrix[left][right] = value
    return replace(seed, adjacency=tuple(tuple(row) for row in matrix))


def symmetric_changes(
    *changes: tuple[int, int, Fraction],
) -> tuple[tuple[int, int, Fraction], ...]:
    result: list[tuple[int, int, Fraction]] = []
    for left, right, value in changes:
        result.extend(((left, right, value), (right, left, value)))
    return tuple(result)


class CoordinateSensitivePositiveTests(unittest.TestCase):
    def test_declared_grids_pass_independent_exact_certificates(self) -> None:
        for s, rows in GRIDS:
            with self.subTest(s=s, rows=rows):
                seed = build_seed(s, rows)
                certificate = validate_seed(seed)
                p = rows * (s + 1) // 2 - 1
                g = rows - 1
                h = p - g
                balance = 4 * g + h
                self.assertEqual(seed.cells, local_cells(s, rows))
                self.assertEqual((seed.p, seed.g, seed.h, seed.balance), (p, g, h, balance))
                self.assertEqual(tuple(map(len, seed.cells)), (1, 1, g, h, g, h, 1))
                self.assertEqual(seed.adjacency, local_adjacency(seed, tuple(range(p))))

                genuine_pairs = tuple(
                    (local_index(s, row, s), local_index(s, row + 1, 0))
                    for row in range(rows - 1)
                )
                self.assertEqual(seed.genuine_pairs, genuine_pairs)
                for left, right in genuine_pairs:
                    self.assertEqual(seed.adjacency[left][right], Fraction(balance))
                self.assertEqual(seed.adjacency[seed.exit][seed.entrance], Fraction(0))

                quotient = quotient_matrix(seed)
                self.assertEqual(quotient, local_quotient(g, h, balance))
                cell_of = {
                    vertex: cell_index
                    for cell_index, cell in enumerate(seed.cells)
                    for vertex in cell
                }
                for vertex in range(seed.size):
                    for target_cell, targets in enumerate(seed.cells):
                        hp = sum(
                            (seed.adjacency[vertex][target] for target in targets),
                            Fraction(0),
                        )
                        self.assertEqual(hp, quotient[cell_of[vertex]][target_cell])

                positive = seed.cells[0] + seed.cells[2] + seed.cells[3] + seed.cells[6]
                negative = seed.cells[1] + seed.cells[4] + seed.cells[5]
                self.assertEqual(len(positive) - len(negative), 1)
                for left in range(seed.size):
                    for right in range(left + 1, seed.size):
                        if seed.adjacency[left][right]:
                            self.assertNotEqual(left in positive, right in positive)

                local_zero = [Fraction(0) for _ in range(seed.size)]
                for cell, value in zip(
                    seed.cells,
                    (-Fraction(balance), Fraction(0), Fraction(2), Fraction(1), Fraction(0), Fraction(0), -Fraction(balance)),
                    strict=True,
                ):
                    for vertex in cell:
                        local_zero[vertex] = value
                vector = tuple(local_zero)
                self.assertEqual(zero_vector(seed), vector)
                self.assertEqual(local_matrix_vector(seed.adjacency, vector), (Fraction(0),) * seed.size)
                self.assertEqual(local_rank(seed.adjacency), seed.size - 1)
                self.assertEqual(exact_rank(seed.adjacency), seed.size - 1)

                off_diagonal = tuple(
                    tuple(seed.adjacency[vertex][neighbour] for neighbour in negative)
                    for vertex in positive
                )
                self.assertEqual(local_rank(off_diagonal), p + 1)
                gram = tuple(tuple(
                    sum(
                        (off_diagonal[row][left] * off_diagonal[row][right] for row in range(len(positive))),
                        Fraction(0),
                    )
                    for right in range(len(negative))
                ) for left in range(len(negative)))
                shifted = tuple(tuple(
                    gram[row][column] - (Fraction(1) if row == column else Fraction(0))
                    for column in range(len(gram))
                ) for row in range(len(gram)))
                pivots = local_ldlt_pivots(shifted)
                self.assertTrue(all(pivot > 0 for pivot in pivots))
                self.assertEqual(certificate.ldlt_pivots, pivots)

                norm = sum((value * value for value in vector), Fraction(0))
                support = abs(vector[seed.entrance] * vector[seed.exit]) / norm
                self.assertEqual(norm, Fraction(balance * (2 * balance + 1)))
                self.assertEqual(support, Fraction(balance, 2 * balance + 1))
                self.assertEqual(certificate.endpoint_weight, support)
                self.assertEqual(certificate.zero_projector_endpoint_element, support)
                self.assertGreater(certificate.numerical_gap, 1.0)
                self.assertTrue(math.isfinite(certificate.numerical_gap))

                for power in range(4):
                    self.assertEqual(local_moment(seed.adjacency, seed.entrance, seed.exit, power), 0)
                candidate_moment = local_moment(seed.adjacency, seed.entrance, seed.exit, 4)
                self.assertEqual(candidate_moment, Fraction(balance * balance))
                self.assertEqual(certificate.candidate_fourth_moment, candidate_moment)
                self.assertEqual(endpoint_moment(seed.adjacency, seed.entrance, seed.exit, 4), candidate_moment)
                self.assertEqual(expected_candidate_fourth_moment(seed), candidate_moment)

    def test_all_declared_cross_counts_are_fair_nonisomorphic_and_separated(self) -> None:
        for s, rows in GRIDS:
            seed = build_seed(s, rows)
            candidate_weights = tuple(sorted(
                seed.adjacency[left][right]
                for left in range(seed.size)
                for right in range(left + 1, seed.size)
                if seed.adjacency[left][right]
            ))
            candidate_degrees = tuple(sum(row, Fraction(0)) for row in seed.adjacency)
            candidate_profile = edge_degree_profile(seed.adjacency)
            candidate_moment = local_moment(seed.adjacency, seed.entrance, seed.exit, 4)
            for cross_count in range(1, min(seed.g, seed.h) + 1):
                with self.subTest(s=s, cross_count=cross_count):
                    permutation = local_cross_permutation(seed.p, seed.g, cross_count)
                    self.assertEqual(canonical_cross_permutation(seed, cross_count), permutation)
                    control = local_adjacency(seed, permutation)
                    self.assertEqual(control_adjacency(seed, permutation), control)
                    control_weights = tuple(sorted(
                        control[left][right]
                        for left in range(seed.size)
                        for right in range(left + 1, seed.size)
                        if control[left][right]
                    ))
                    control_degrees = tuple(sum(row, Fraction(0)) for row in control)
                    self.assertEqual(control_weights, candidate_weights)
                    self.assertEqual(control_degrees, candidate_degrees)
                    control_profile = edge_degree_profile(control)
                    self.assertNotEqual(control_profile, candidate_profile)
                    self.assertIn(
                        (Fraction(seed.balance), Fraction(seed.balance + 1), Fraction(seed.balance + 2)),
                        control_profile,
                    )
                    control_moment = local_moment(control, seed.entrance, seed.exit, 4)
                    self.assertEqual(
                        control_moment,
                        Fraction(seed.balance * (seed.balance - cross_count)),
                    )
                    self.assertEqual(candidate_moment - control_moment, Fraction(cross_count * seed.balance))
                    certificate = control_certificate(seed, permutation)
                    self.assertEqual(certificate.cross_count, cross_count)
                    self.assertTrue(certificate.fair_weight_multiset)
                    self.assertTrue(certificate.fair_vertex_weighted_degrees)
                    self.assertTrue(certificate.edge_degree_profile_differs)
                    self.assertEqual(certificate.moment_difference, Fraction(cross_count * seed.balance))

    def test_undeclared_grids_are_rejected(self) -> None:
        for args in ((1, 6), (2, 5), (5, 6), (2.0, 6)):
            with self.subTest(args=args), self.assertRaises(CoordinateSensitiveError):
                build_seed(*args)  # type: ignore[arg-type]


class CoordinateSensitiveMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = build_seed(2, 6)

    def test_invalid_role_coverage_is_rejected(self) -> None:
        cells = [list(cell) for cell in self.seed.cells]
        cells[3][-1] = cells[3][0]
        malformed = replace(self.seed, cells=tuple(tuple(cell) for cell in cells))
        with self.assertRaises(CoordinateSensitiveError):
            validate_coordinates_and_cells(malformed)

    def test_wrong_zero_and_negative_weights_are_rejected(self) -> None:
        left, right = self.seed.cells[2][0], self.seed.cells[4][0]
        for weight in (Fraction(1), Fraction(0), Fraction(-1)):
            malformed = changed_adjacency(
                self.seed, symmetric_changes((left, right, weight))
            )
            with self.subTest(weight=weight), self.assertRaises(CoordinateSensitiveError):
                validate_declared_candidate(malformed)

    def test_quotient_and_chiral_breaks_are_rejected(self) -> None:
        hub, genuine_source = self.seed.cells[1][0], self.seed.cells[2][0]
        closure_break = changed_adjacency(
            self.seed, symmetric_changes((hub, genuine_source, Fraction(3)))
        )
        with self.assertRaises(CoordinateSensitiveError):
            validate_quotient(closure_break)
        same_sublattice = changed_adjacency(
            self.seed,
            symmetric_changes((self.seed.cells[0][0], genuine_source, Fraction(1))),
        )
        with self.assertRaises(CoordinateSensitiveError):
            validate_chiral(same_sublattice)

    def test_false_periodic_edge_is_rejected(self) -> None:
        malformed = changed_adjacency(
            self.seed,
            symmetric_changes((self.seed.exit, self.seed.entrance, Fraction(1))),
        )
        with self.assertRaises(CoordinateSensitiveError):
            validate_declared_candidate(malformed)

    def test_endpoint_imbalance_and_extra_nullity_are_rejected(self) -> None:
        vector = list(zero_vector(self.seed))
        vector[self.seed.exit] += 1
        with self.assertRaises(CoordinateSensitiveError):
            validate_zero_rank_and_gap(self.seed, tuple(vector))
        source, destination = self.seed.cells[2][0], self.seed.cells[4][0]
        disconnected = changed_adjacency(
            self.seed,
            symmetric_changes(
                (source, destination, Fraction(0)),
                (destination, self.seed.exit, Fraction(0)),
            ),
        )
        self.assertLess(local_rank(disconnected.adjacency), disconnected.size - 1)
        with self.assertRaises(CoordinateSensitiveError):
            validate_zero_rank_and_gap(disconnected)

    def test_nonpositive_ldlt_certificate_is_rejected(self) -> None:
        with self.assertRaises(CoordinateSensitiveError):
            require_positive_ldlt(((Fraction(0), Fraction(0)), (Fraction(0), Fraction(1))))
        with self.assertRaises(CoordinateSensitiveError):
            require_positive_ldlt(((Fraction(-1),),))

    def test_invalid_cross_controls_are_rejected(self) -> None:
        for cross_count in (0, min(self.seed.g, self.seed.h) + 1, -1, 1.0):
            with self.subTest(cross_count=cross_count), self.assertRaises(CoordinateSensitiveError):
                canonical_cross_permutation(self.seed, cross_count)  # type: ignore[arg-type]
        bad_permutation = tuple(range(self.seed.p - 1)) + (self.seed.p - 2,)
        with self.assertRaises(CoordinateSensitiveError):
            validate_permutation(self.seed, bad_permutation)
        with self.assertRaises(CoordinateSensitiveError):
            control_certificate(self.seed, tuple(range(self.seed.p)))

    def test_fairness_helpers_detect_weight_and_degree_changes(self) -> None:
        permutation = canonical_cross_permutation(self.seed, 1)
        control = control_adjacency(self.seed, permutation)
        self.assertEqual(edge_weight_multiset(self.seed.adjacency), edge_weight_multiset(control))
        self.assertEqual(weighted_degrees(self.seed.adjacency), weighted_degrees(control))
        self.assertNotEqual(edge_degree_profile(self.seed.adjacency), edge_degree_profile(control))
        matrix = [list(row) for row in control]
        left, right = self.seed.cells[2][0], self.seed.cells[5][0]
        if matrix[left][right] == 0:
            left, right = next(
                (i, j)
                for i in range(self.seed.size)
                for j in range(i + 1, self.seed.size)
                if matrix[i][j] != 0
            )
        matrix[left][right] += 1
        matrix[right][left] += 1
        unfair = tuple(tuple(row) for row in matrix)
        self.assertNotEqual(edge_weight_multiset(self.seed.adjacency), edge_weight_multiset(unfair))
        with self.assertRaises(CoordinateSensitiveError):
            control_certificate(self.seed, permutation, unfair, None)

    def test_false_or_inexact_fourth_moment_claim_is_rejected(self) -> None:
        permutation = canonical_cross_permutation(self.seed, 1)
        control = control_adjacency(self.seed, permutation)
        actual = endpoint_moment(control, self.seed.entrance, self.seed.exit, 4)
        accepted = control_certificate(self.seed, permutation, control, actual)
        self.assertEqual(accepted.control_fourth_moment, actual)
        with self.assertRaises(CoordinateSensitiveError):
            control_certificate(self.seed, permutation, control, actual + 1)
        with self.assertRaises(CoordinateSensitiveError):
            control_certificate(self.seed, permutation, control, int(actual))  # type: ignore[arg-type]

    def test_matrix_vector_and_moment_dimension_rules_fail_closed(self) -> None:
        with self.assertRaises(CoordinateSensitiveError):
            matrix_vector(self.seed.adjacency, (Fraction(1),))
        with self.assertRaises(CoordinateSensitiveError):
            endpoint_moment(self.seed.adjacency, self.seed.entrance, self.seed.exit, -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
