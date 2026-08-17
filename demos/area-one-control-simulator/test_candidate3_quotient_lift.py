#!/usr/bin/env python3
"""Independent exact and mutation tests for the Candidate 3 structural seed."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import math
import unittest

from candidate3_quotient_lift import (
    Candidate3Error,
    Candidate3Seed,
    GRIDS,
    build_seed,
    candidate_zero_vector,
    exact_nullspace,
    exact_rank,
    quotient_matrix,
    validate_adjacency,
    validate_chiral,
    validate_declared_edges,
    validate_numerical_spectrum,
    validate_overlap_edges,
    validate_partition,
    validate_quotient,
    validate_quotient_structure,
    validate_seed,
    validate_zero_mode,
)


def local_index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def local_expected_quotient(p: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(Fraction(value) for value in row) for row in (
        (0, 1, 0, 0, 0),
        (1, 0, p, 0, 0),
        (0, 1, 0, 1, 0),
        (0, 0, 1, 0, 1),
        (0, 0, 0, p, 0),
    ))


def independent_rank(matrix: tuple[tuple[Fraction, ...], ...]) -> int:
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


def changed_adjacency(
    seed: Candidate3Seed,
    changes: tuple[tuple[int, int, Fraction], ...],
) -> Candidate3Seed:
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


class Candidate3PositiveTests(unittest.TestCase):
    def test_all_declared_grids_have_independently_verified_structure(self) -> None:
        for s, rows in GRIDS:
            with self.subTest(s=s, rows=rows):
                seed = build_seed(s, rows)
                certificate = validate_seed(seed)
                coordinate_count = rows * (s + 1)
                p = coordinate_count // 2 - 1
                expected_labels = tuple(
                    (row, column)
                    for row in range(rows)
                    for column in range(s + 1)
                ) + ("auxiliary-hub",)
                self.assertEqual(seed.labels, expected_labels)
                self.assertEqual(seed.size, coordinate_count + 1)
                self.assertEqual(tuple(map(len, seed.cells)), (1, 1, p, p, 1))
                flattened = [vertex for cell in seed.cells for vertex in cell]
                self.assertEqual(sorted(flattened), list(range(seed.size)))
                self.assertEqual(len(flattened), len(set(flattened)))

                genuine = tuple(
                    (local_index(s, row, s), local_index(s, row + 1, 0))
                    for row in range(rows - 1)
                )
                self.assertEqual(seed.genuine_pairs, genuine)
                self.assertEqual(seed.cells[2][:5], tuple(left for left, _right in genuine))
                self.assertEqual(seed.cells[3][:5], tuple(right for _left, right in genuine))
                for left, right in genuine:
                    self.assertEqual(seed.adjacency[left][right], Fraction(1))
                self.assertEqual(seed.adjacency[seed.exit][seed.entrance], Fraction(0))

                quotient = certificate.quotient
                self.assertEqual(quotient, local_expected_quotient(p))
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
                negative = set(seed.cells[1] + seed.cells[3])
                self.assertEqual(len(positive) - len(negative), 1)
                for left in range(seed.size):
                    for right in range(left + 1, seed.size):
                        if seed.adjacency[left][right]:
                            self.assertNotEqual(left in positive, right in positive)

                vector = candidate_zero_vector(seed)
                expected_values = (-Fraction(p), Fraction(0), Fraction(1), Fraction(0), Fraction(-1))
                for cell, value in zip(seed.cells, expected_values, strict=True):
                    self.assertTrue(all(vector[vertex] == value for vertex in cell))
                product = tuple(
                    sum(
                        (seed.adjacency[row][column] * vector[column] for column in range(seed.size)),
                        Fraction(0),
                    )
                    for row in range(seed.size)
                )
                self.assertEqual(product, (Fraction(0),) * seed.size)
                self.assertNotEqual(vector[seed.entrance], 0)
                self.assertNotEqual(vector[seed.exit], 0)
                rank = independent_rank(seed.adjacency)
                self.assertEqual(rank, seed.size - 1)
                self.assertEqual(exact_rank(seed.adjacency), rank)
                self.assertEqual(len(exact_nullspace(seed.adjacency)), 1)
                self.assertEqual(certificate.exact_nullity, 1)
                self.assertTrue(math.isfinite(certificate.numerical_gap))
                self.assertGreater(certificate.numerical_gap, 1.0e-12)

    def test_build_rejects_undeclared_grids(self) -> None:
        for args in ((1, 6), (2, 5), (5, 6), (2.0, 6)):
            with self.subTest(args=args), self.assertRaises(Candidate3Error):
                build_seed(*args)  # type: ignore[arg-type]


class Candidate3MutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed = build_seed(2, 6)

    def test_duplicate_and_missing_partition_vertex_are_rejected(self) -> None:
        cells = [list(cell) for cell in self.seed.cells]
        cells[2][-1] = cells[2][0]
        malformed = replace(self.seed, cells=tuple(tuple(cell) for cell in cells))
        with self.assertRaises(Candidate3Error):
            validate_partition(malformed)

    def test_asymmetric_adjacency_is_rejected(self) -> None:
        left, right = self.seed.cells[0][0], self.seed.cells[1][0]
        malformed = changed_adjacency(self.seed, ((left, right, Fraction(2)),))
        with self.assertRaises(Candidate3Error):
            validate_adjacency(malformed)

    def test_self_loop_is_rejected(self) -> None:
        vertex = self.seed.cells[2][0]
        malformed = changed_adjacency(self.seed, ((vertex, vertex, Fraction(1)),))
        with self.assertRaises(Candidate3Error):
            validate_adjacency(malformed)

    def test_negative_and_zero_declared_edge_weights_are_rejected(self) -> None:
        left, right = self.seed.cells[0][0], self.seed.cells[1][0]
        negative = changed_adjacency(
            self.seed, symmetric_changes((left, right, Fraction(-1)))
        )
        with self.assertRaises(Candidate3Error):
            validate_adjacency(negative)
        zeroed = changed_adjacency(
            self.seed, symmetric_changes((left, right, Fraction(0)))
        )
        with self.assertRaises(Candidate3Error):
            validate_declared_edges(zeroed)

    def test_quotient_closure_break_is_rejected(self) -> None:
        left, right = self.seed.cells[0][0], self.seed.cells[3][0]
        malformed = changed_adjacency(
            self.seed, symmetric_changes((left, right, Fraction(1)))
        )
        with self.assertRaises(Candidate3Error):
            validate_quotient(malformed)

    def test_same_sublattice_edge_breaks_chiral_symmetry(self) -> None:
        left, right = self.seed.cells[0][0], self.seed.cells[2][0]
        malformed = changed_adjacency(
            self.seed, symmetric_changes((left, right, Fraction(1)))
        )
        with self.assertRaises(Candidate3Error):
            validate_chiral(malformed)

    def test_false_periodic_overlap_edge_is_rejected(self) -> None:
        malformed = changed_adjacency(
            self.seed,
            symmetric_changes((self.seed.exit, self.seed.entrance, Fraction(1))),
        )
        with self.assertRaises(Candidate3Error):
            validate_overlap_edges(malformed)

    def test_endpoint_zero_candidate_is_rejected(self) -> None:
        vector = list(candidate_zero_vector(self.seed))
        vector[self.seed.entrance] = Fraction(0)
        vector[self.seed.exit] = Fraction(0)
        with self.assertRaises(Candidate3Error):
            validate_zero_mode(self.seed, tuple(vector))

    def test_additional_exact_nullity_is_rejected(self) -> None:
        c2 = self.seed.cells[2][0]
        c3 = self.seed.cells[3][0]
        malformed = changed_adjacency(
            self.seed,
            symmetric_changes(
                (c2, c3, Fraction(0)),
                (c3, self.seed.exit, Fraction(0)),
            ),
        )
        self.assertGreater(len(exact_nullspace(malformed.adjacency)), 1)
        with self.assertRaises(Candidate3Error):
            validate_zero_mode(malformed)

    def test_nonfinite_and_zero_gap_diagnostics_are_rejected(self) -> None:
        for eigenvalues in ((-1.0, 0.0, float("nan")), (0.0, 0.0, 1.0), (0.0,)):
            with self.subTest(eigenvalues=eigenvalues), self.assertRaises(Candidate3Error):
                validate_numerical_spectrum(eigenvalues, 1)
        with self.assertRaises(Candidate3Error):
            validate_numerical_spectrum((-1.0, 0.0, 1.0), 2)

    def test_even_and_noncompressing_quotients_are_rejected(self) -> None:
        even = replace(self.seed, cells=self.seed.cells[:3] + (self.seed.cells[3] + self.seed.cells[4],))
        with self.assertRaises(Candidate3Error):
            validate_quotient_structure(even)
        singleton_cells = tuple((vertex,) for vertex in range(self.seed.size))
        noncompressing = replace(self.seed, cells=singleton_cells)
        with self.assertRaises(Candidate3Error):
            validate_quotient_structure(noncompressing)

    def test_wrong_genuine_pair_metadata_is_rejected(self) -> None:
        malformed = replace(self.seed, genuine_pairs=self.seed.genuine_pairs[:-1])
        with self.assertRaises(Candidate3Error):
            validate_overlap_edges(malformed)

    def test_full_validator_rejects_an_extra_unit_edge(self) -> None:
        left, right = self.seed.cells[0][0], self.seed.cells[3][0]
        malformed = changed_adjacency(
            self.seed, symmetric_changes((left, right, Fraction(1)))
        )
        with self.assertRaises(Candidate3Error):
            validate_seed(malformed)

    def test_public_quotient_constructor_matches_validator(self) -> None:
        self.assertEqual(quotient_matrix(self.seed), validate_quotient(self.seed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
