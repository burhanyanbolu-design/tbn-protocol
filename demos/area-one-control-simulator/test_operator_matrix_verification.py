#!/usr/bin/env python3
"""Verification for the independent Grover operator matrix."""

import unittest

from eog_quantum_walk import EOGQuantumWalk
from operator_matrix_verification import (
    apply_matrix,
    build_operator_matrix,
    maximum_evolution_difference,
    maximum_unitarity_error,
    ordered_basis,
)
from simulator import Position


class OperatorMatrixVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(2, 3, set())
        self.matrix = build_operator_matrix(self.walk)

    def test_basis_dimension_matches_full_hilbert_space(self) -> None:
        self.assertEqual(len(ordered_basis(self.walk)), 3 * 3 * 4)
        self.assertEqual(len(self.matrix), 36)
        self.assertTrue(all(len(row) == 36 for row in self.matrix))

    def test_operator_is_unitary(self) -> None:
        self.assertLessEqual(maximum_unitarity_error(self.matrix), 1e-12)

    def test_matrix_matches_dictionary_for_multiple_steps(self) -> None:
        difference = maximum_evolution_difference(
            self.walk, Position(0, 0), 8, self.matrix
        )
        self.assertLessEqual(difference, 1e-12)

    def test_overlapping_label_states_have_distinct_basis_columns(self) -> None:
        basis = ordered_basis(self.walk)
        endpoint = basis.index((Position(0, 2), 0))
        next_row = basis.index((Position(1, 0), 0))
        self.assertNotEqual(endpoint, next_row)
        self.assertNotEqual(
            [row[endpoint] for row in self.matrix],
            [row[next_row] for row in self.matrix],
        )

    def test_dimension_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            apply_matrix(self.matrix, [1j])


if __name__ == "__main__":
    unittest.main(verbosity=2)
