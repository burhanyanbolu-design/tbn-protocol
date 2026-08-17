#!/usr/bin/env python3
"""Independent theorem and mutation tests for the balanced-weight lift."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import math
import unittest

from candidate3_balanced_weight_lift import (
    BalancedSeed,
    BalancedWeightError,
    GRIDS,
    balanced_zero_vector,
    build_seed,
    control_adjacency,
    exact_rank,
    permutation_certificate,
    quotient_matrix,
    spectral_certificate,
    unit_weight_endpoint_metrics,
    validate_chiral,
    validate_coordinates_and_partition,
    validate_declared_weights,
    validate_numerical_spectrum,
    validate_permutation,
    validate_quotient,
    validate_seed,
    validate_zero_mode,
)


def local_index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def local_rank(matrix: tuple[tuple[Fraction, ...], ...]) -> int:
    values = [list(row) for row in matrix]
    rank = 0
    for column in range(len(values[0])):
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


def local_expected_cells(s: int, rows: int) -> tuple[tuple[int, ...], ...]:
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
        sources + unused[:half],
        destinations + unused[half:],
        (exit_state,),
    )


def local_quotient(p: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(Fraction(value) for value in row) for row in (
        (0, 1, 0, 0, 0),
        (1, 0, p, 0, 0),
        (0, 1, 0, p, 0),
        (0, 0, p, 0, 1),
        (0, 0, 0, p, 0),
    ))


def local_negative_gram(seed: BalancedSeed) -> tuple[tuple[Fraction, ...], ...]:
    positive = seed.cells[0] + seed.cells[2] + seed.cells[4]
    negative = seed.cells[1] + seed.cells[3]
    return tuple(tuple(
        sum(
            (seed.adjacency[vertex][left] * seed.adjacency[vertex][right] for vertex in positive),
            Fraction(0),
        )
        for right in negative
    ) for left in negative)


def local_control_adjacency(
    seed: BalancedSeed, permutation: tuple[int, ...],
) -> tuple[tuple[Fraction, ...], ...]:
    matrix = [[Fraction(0) for _ in range(seed.size)] for _ in range(seed.size)]

    def add(left: int, right: int, weight: Fraction) -> None:
        matrix[left][right] = weight
        matrix[right][left] = weight

    add(seed.cells[0][0], seed.cells[1][0], Fraction(1))
    for vertex in seed.cells[2]:
        add(seed.cells[1][0], vertex, Fraction(1))
    for source_position, destination_position in enumerate(permutation):
        add(seed.cells[2][source_position], seed.cells[3][destination_position], Fraction(seed.p))
    for vertex in seed.cells[3]:
        add(vertex, seed.cells[4][0], Fraction(1))
    return tuple(tuple(row) for row in matrix)


def local_vertex_map(seed: BalancedSeed, permutation: tuple[int, ...]) -> tuple[int, ...]:
    mapping = list(range(seed.size))
    for source_position, destination_position in enumerate(permutation):
        mapping[seed.cells[3][source_position]] = seed.cells[3][destination_position]
    return tuple(mapping)


def local_permutations(p: int) -> tuple[tuple[int, ...], ...]:
    values: set[tuple[int, ...]] = {
        tuple(range(p)),
        tuple(reversed(range(p))),
    }
    values.update(tuple((index + shift) % p for index in range(p)) for shift in range(p))
    identity = list(range(p))
    for left in range(p):
        for right in range(left + 1, p):
            swapped = list(identity)
            swapped[left], swapped[right] = swapped[right], swapped[left]
            values.add(tuple(swapped))
    return tuple(sorted(values))


def local_matrix_vector(
    matrix: tuple[tuple[Fraction, ...], ...], vector: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    return tuple(
        sum((weight * value for weight, value in zip(row, vector, strict=True)), Fraction(0))
        for row in matrix
    )


def changed_adjacency(
    seed: BalancedSeed,
    changes: tuple[tuple[int, int, Fraction], ...],
) -> BalancedSeed:
    matrix = [list(row) for row in seed.adjacency]
    for left, right, weight in changes:
        matrix[left][right] = weight
    return replace(seed, adjacency=tuple(tuple(row) for row in matrix))


def symmetric_changes(
    *changes: tuple[int, int, Fraction],
) -> tuple[tuple[int, int, Fraction], ...]:
    result: list[tuple[int, int, Fraction]] = []
    for left, right, weight in changes:
        result.extend(((left, right, weight), (right, left, weight)))
    return tuple(result)


class BalancedWeightPositiveTests(unittest.TestCase):
    def test_all_grids_satisfy_independent_exact_theorems(self) -> None:
        for s, rows in GRIDS:
            with self.subTest(s=s, rows=rows):
                seed = build_seed(s, rows)
                certificate = validate_seed(seed)
                p = rows * (s + 1) // 2 - 1
                self.assertEqual(seed.p, p)
                self.assertEqual(seed.cells, local_expected_cells(s, rows))
                self.assertEqual(seed.size, 2 * p + 3)

                expected_pairs = tuple(
                    (local_index(s, row, s), local_index(s, row + 1, 0))
                    for row in range(rows - 1)
                )
                self.assertEqual(seed.genuine_pairs, expected_pairs)
                self.assertEqual(seed.cells[2][:5], tuple(left for left, _ in expected_pairs))
                self.assertEqual(seed.cells[3][:5], tuple(right for _, right in expected_pairs))
                for left, right in expected_pairs:
                    self.assertEqual(seed.adjacency[left][right], Fraction(p))
                self.assertEqual(seed.adjacency[seed.exit][seed.entrance], Fraction(0))

                quotient = quotient_matrix(seed)
                self.assertEqual(quotient, local_quotient(p))
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

                positive = set(seed.cells[0] + seed.cells[2] + seed.cells[4])
                self.assertEqual(len(positive), p + 2)
                for left in range(seed.size):
                    for right in range(left + 1, seed.size):
                        if seed.adjacency[left][right]:
                            self.assertNotEqual(left in positive, right in positive)

                vector = balanced_zero_vector(seed)
                local_vector = [Fraction(0) for _ in range(seed.size)]
                for cell, value in zip(
                    seed.cells,
                    (-Fraction(p), Fraction(0), Fraction(1), Fraction(0), -Fraction(p)),
                    strict=True,
                ):
                    for vertex in cell:
                        local_vector[vertex] = value
                self.assertEqual(vector, tuple(local_vector))
                product = tuple(
                    sum(
                        (seed.adjacency[row][column] * vector[column] for column in range(seed.size)),
                        Fraction(0),
                    )
                    for row in range(seed.size)
                )
                self.assertEqual(product, (Fraction(0),) * seed.size)
                rank = local_rank(seed.adjacency)
                self.assertEqual(rank, seed.size - 1)
                self.assertEqual(exact_rank(seed.adjacency), rank)
                positive_order = seed.cells[0] + seed.cells[2] + seed.cells[4]
                negative_order = seed.cells[1] + seed.cells[3]
                off_diagonal = tuple(
                    tuple(seed.adjacency[vertex][neighbour] for neighbour in negative_order)
                    for vertex in positive_order
                )
                self.assertEqual(local_rank(off_diagonal), p + 1)

                gram = local_negative_gram(seed)
                for index in range(p - 1):
                    difference = [Fraction(0) for _ in range(p + 1)]
                    difference[index + 1] = Fraction(1)
                    difference[-1] = Fraction(-1)
                    product = tuple(
                        sum((gram[row][column] * difference[column] for column in range(p + 1)), Fraction(0))
                        for row in range(p + 1)
                    )
                    self.assertEqual(product, tuple(Fraction(p * p) * value for value in difference))
                hub = (Fraction(1),) + (Fraction(0),) * p
                symmetric = (Fraction(0),) + (Fraction(1),) * p
                gram_hub = tuple(
                    sum((gram[row][column] * hub[column] for column in range(p + 1)), Fraction(0))
                    for row in range(p + 1)
                )
                gram_symmetric = tuple(
                    sum((gram[row][column] * symmetric[column] for column in range(p + 1)), Fraction(0))
                    for row in range(p + 1)
                )
                self.assertEqual(gram_hub[0], Fraction(p + 1))
                self.assertTrue(all(value == Fraction(p) for value in gram_hub[1:]))
                self.assertEqual(gram_symmetric[0], Fraction(p * p))
                self.assertTrue(all(value == Fraction(p * p + p) for value in gram_symmetric[1:]))
                local_trace = gram_hub[0] + gram_symmetric[1]
                local_determinant = (
                    gram_hub[0] * gram_symmetric[1]
                    - gram_symmetric[0] * gram_hub[1]
                )

                expected_support = Fraction(p, 2 * p + 1)
                local_norm = sum((value * value for value in vector), Fraction(0))
                local_transfer = abs(vector[seed.entrance] * vector[seed.exit]) / local_norm
                self.assertEqual(certificate.off_diagonal_rank, p + 1)
                self.assertEqual(certificate.norm_squared, local_norm)
                self.assertEqual(certificate.norm_squared, Fraction(p * (2 * p + 1)))
                self.assertEqual(certificate.entrance_weight, expected_support)
                self.assertEqual(certificate.exit_weight, expected_support)
                self.assertEqual(certificate.endpoint_transfer, local_transfer)
                self.assertEqual(certificate.endpoint_transfer, expected_support)
                self.assertGreaterEqual(expected_support, Fraction(8, 17))
                self.assertEqual(certificate.repeated_singular_square, Fraction(p * p))
                self.assertEqual(certificate.repeated_multiplicity, p - 1)
                self.assertEqual(certificate.quadratic_trace, local_trace)
                self.assertEqual(certificate.quadratic_trace, Fraction((p + 1) ** 2))
                self.assertEqual(certificate.quadratic_determinant, local_determinant)
                self.assertEqual(certificate.quadratic_determinant, Fraction(p * (2 * p + 1)))
                self.assertEqual(certificate.polynomial_at_one, Fraction(p * (p - 1)))
                self.assertEqual(certificate.polynomial_at_two, Fraction(2 - 3 * p))
                self.assertGreater(certificate.numerical_gap, 1.0)
                self.assertLess(certificate.numerical_gap, math.sqrt(2.0))

    def test_balancing_repairs_exit_support_and_transfer_scaling(self) -> None:
        previous = Fraction(0)
        for p in (8, 11, 14, 100):
            balanced = Fraction(p, 2 * p + 1)
            unit_entrance, unit_exit, unit_transfer = unit_weight_endpoint_metrics(p)
            self.assertEqual(unit_entrance, Fraction(p * p, p * p + p + 1))
            self.assertGreater(balanced, unit_exit)
            self.assertGreater(balanced, unit_transfer)
            self.assertGreater(balanced, previous)
            previous = balanced
        self.assertLess(Fraction(100, 201), Fraction(1, 2))

    def test_matching_permutations_are_endpoint_fixing_isomorphisms(self) -> None:
        for s, rows in GRIDS:
            seed = build_seed(s, rows)
            for permutation in local_permutations(seed.p):
                with self.subTest(s=s, permutation=permutation[:3]):
                    local_control = local_control_adjacency(seed, permutation)
                    mapping = local_vertex_map(seed, permutation)
                    self.assertEqual(len(set(mapping)), seed.size)
                    self.assertEqual(mapping[seed.entrance], seed.entrance)
                    self.assertEqual(mapping[seed.exit], seed.exit)
                    for left in range(seed.size):
                        for right in range(seed.size):
                            self.assertEqual(
                                seed.adjacency[left][right],
                                local_control[mapping[left]][mapping[right]],
                            )
                    production = permutation_certificate(seed, permutation)
                    self.assertEqual(production.vertex_map, mapping)
                    self.assertEqual(control_adjacency(seed, permutation), local_control)

            reverse = tuple(reversed(range(seed.p)))
            control = local_control_adjacency(seed, reverse)
            candidate_state = tuple(
                Fraction(1) if vertex == seed.entrance else Fraction(0)
                for vertex in range(seed.size)
            )
            control_state = candidate_state
            for _power in range(seed.size + 1):
                self.assertEqual(candidate_state[seed.exit], control_state[seed.exit])
                candidate_state = local_matrix_vector(seed.adjacency, candidate_state)
                control_state = local_matrix_vector(control, control_state)

    def test_undeclared_grids_are_rejected(self) -> None:
        for args in ((1, 6), (2, 5), (5, 6), (2.0, 6)):
            with self.subTest(args=args), self.assertRaises(BalancedWeightError):
                build_seed(*args)  # type: ignore[arg-type]


class BalancedWeightMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = build_seed(2, 6)

    def test_malformed_partition_is_rejected(self) -> None:
        cells = [list(cell) for cell in self.seed.cells]
        cells[2][-1] = cells[2][0]
        malformed = replace(self.seed, cells=tuple(tuple(cell) for cell in cells))
        with self.assertRaises(BalancedWeightError):
            validate_coordinates_and_partition(malformed)

    def test_wrong_zero_or_negative_declared_weight_is_rejected(self) -> None:
        left, right = self.seed.cells[2][0], self.seed.cells[3][0]
        for weight in (Fraction(self.seed.p + 1), Fraction(0), Fraction(-1)):
            malformed = changed_adjacency(
                self.seed, symmetric_changes((left, right, weight))
            )
            with self.subTest(weight=weight), self.assertRaises(BalancedWeightError):
                validate_declared_weights(malformed)

    def test_quotient_closure_break_is_rejected(self) -> None:
        left, right = self.seed.cells[1][0], self.seed.cells[2][0]
        malformed = changed_adjacency(
            self.seed, symmetric_changes((left, right, Fraction(2)))
        )
        with self.assertRaises(BalancedWeightError):
            validate_quotient(malformed)

    def test_same_sublattice_edge_breaks_chiral_symmetry(self) -> None:
        left, right = self.seed.cells[0][0], self.seed.cells[2][0]
        malformed = changed_adjacency(
            self.seed, symmetric_changes((left, right, Fraction(1)))
        )
        with self.assertRaises(BalancedWeightError):
            validate_chiral(malformed)

    def test_false_periodic_edge_is_rejected(self) -> None:
        malformed = changed_adjacency(
            self.seed,
            symmetric_changes((self.seed.exit, self.seed.entrance, Fraction(1))),
        )
        with self.assertRaises(BalancedWeightError):
            validate_declared_weights(malformed)

    def test_endpoint_zero_or_imbalance_is_rejected(self) -> None:
        zero = (Fraction(0),) * self.seed.size
        with self.assertRaises(BalancedWeightError):
            validate_zero_mode(self.seed, zero)
        vector = list(balanced_zero_vector(self.seed))
        vector[self.seed.exit] += 1
        with self.assertRaises(BalancedWeightError):
            validate_zero_mode(self.seed, tuple(vector))

    def test_additional_nullity_is_rejected(self) -> None:
        c2, c3 = self.seed.cells[2][0], self.seed.cells[3][0]
        malformed = changed_adjacency(
            self.seed,
            symmetric_changes(
                (c2, c3, Fraction(0)),
                (c3, self.seed.exit, Fraction(0)),
            ),
        )
        self.assertLess(local_rank(malformed.adjacency), malformed.size - 1)
        with self.assertRaises(BalancedWeightError):
            validate_zero_mode(malformed)

    def test_invalid_numerical_spectra_are_rejected(self) -> None:
        self.assertEqual(
            validate_numerical_spectrum((-2.0, -1.25, 0.0, 1.25, 2.0), 1, 1.25),
            1.25,
        )
        cases = (
            ((-1.0, 0.0, float("nan")), 1, 1.0),
            ((0.0, 0.0, 1.0), 1, 1.0),
            ((-1.0, 0.0, 1.0), 1, 0.0),
            ((-1.0, 0.0, 1.0), 1, 1.1),
            ((-1.0, 0.0, 1.0), 2, 1.0),
        )
        for eigenvalues, nullity, expected in cases:
            with self.subTest(eigenvalues=eigenvalues), self.assertRaises(BalancedWeightError):
                validate_numerical_spectrum(eigenvalues, nullity, expected)

    def test_invalid_matching_permutations_are_rejected(self) -> None:
        bad = (
            tuple(range(self.seed.p - 1)),
            tuple(range(self.seed.p - 1)) + (self.seed.p - 2,),
            tuple(range(self.seed.p - 1)) + (self.seed.p,),
            tuple(float(value) for value in range(self.seed.p)),
        )
        for permutation in bad:
            with self.subTest(permutation=permutation[-2:]), self.assertRaises(BalancedWeightError):
                validate_permutation(permutation, self.seed.p)

    def test_full_validator_and_certificate_agree(self) -> None:
        self.assertEqual(validate_seed(self.seed), spectral_certificate(self.seed))
        self.assertEqual(quotient_matrix(self.seed), validate_quotient(self.seed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
