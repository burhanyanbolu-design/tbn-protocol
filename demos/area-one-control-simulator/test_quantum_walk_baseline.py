#!/usr/bin/env python3
"""Verification for the standard quantum-walk baseline."""

import unittest

from quantum_walk_baseline import (
    amplitude_norm,
    classical_walk,
    hadamard_shift,
    quantum_walk,
    verify_probability_accounting,
)


class QuantumWalkBaselineTests(unittest.TestCase):
    def test_hadamard_shift_preserves_norm(self) -> None:
        state = {(0, 0): 1 / (2**0.5), (0, 1): 1j / (2**0.5)}
        evolved = hadamard_shift(state)
        self.assertAlmostEqual(amplitude_norm(state), amplitude_norm(evolved), places=12)

    def test_absorption_and_survival_account_for_all_probability(self) -> None:
        quantum = quantum_walk(steps=12, terminal=3)
        classical = classical_walk(steps=12, terminal=3)
        verify_probability_accounting(quantum)
        verify_probability_accounting(classical)
        self.assertGreater(quantum.cumulative_absorption, 0.0)
        self.assertGreater(classical.cumulative_absorption, 0.0)

    def test_terminal_projection_changes_the_walk(self) -> None:
        absorbing = quantum_walk(steps=12, terminal=3)
        unreachable = quantum_walk(steps=12, terminal=99)
        self.assertLess(
            absorbing.final_surviving_probability,
            unreachable.final_surviving_probability,
        )
        self.assertAlmostEqual(unreachable.cumulative_absorption, 0.0, places=12)

    def test_same_inputs_produce_same_numerical_result(self) -> None:
        self.assertEqual(quantum_walk(10, 3), quantum_walk(10, 3))

    def test_starting_at_terminal_is_immediately_absorbed(self) -> None:
        result = quantum_walk(steps=5, terminal=0, start=0)
        self.assertEqual(result.metrics, ())
        self.assertEqual(result.cumulative_absorption, 1.0)
        self.assertEqual(result.final_surviving_probability, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
