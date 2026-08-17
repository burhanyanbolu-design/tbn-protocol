#!/usr/bin/env python3
"""Verification for quantum boundary policy classification."""

import unittest

from boundary_policies import evaluate_boundary, grover_boundary_step
from eog_quantum_walk import EOGQuantumWalk, grover_step
from simulator import Position


class BoundaryPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(2, 3, set())
        self.start = Position(0, 0)

    def test_periodic_policy_matches_existing_operator(self) -> None:
        state = {(self.start, direction): 0.5 + 0j for direction in range(4)}
        self.assertEqual(
            grover_boundary_step(state, 3, 3, "periodic"),
            grover_step(state, 3, 3),
        )

    def test_periodic_boundary_is_unitary(self) -> None:
        result = evaluate_boundary(self.walk, "periodic", self.start, 6)
        self.assertEqual(result.classification, "unitary")
        self.assertAlmostEqual(result.final_norm, 1.0, places=12)

    def test_reflective_boundary_is_unitary(self) -> None:
        result = evaluate_boundary(self.walk, "reflective", self.start, 6)
        self.assertEqual(result.classification, "unitary")
        self.assertAlmostEqual(result.final_norm, 1.0, places=12)

    def test_absorbing_boundary_is_non_unitary_and_loses_norm(self) -> None:
        result = evaluate_boundary(self.walk, "absorbing", self.start, 6)
        self.assertEqual(result.classification, "non-unitary")
        self.assertGreater(result.maximum_unitarity_error, 1e-12)
        self.assertGreater(result.boundary_loss, 0.0)

    def test_unknown_policy_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            grover_boundary_step({}, 3, 3, "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
