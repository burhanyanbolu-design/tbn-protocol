#!/usr/bin/env python3
"""Verification for initial-state and terminal sensitivity sweeps."""

import unittest

from eog_quantum_walk import EOGQuantumWalk
from sensitivity_sweep import INITIAL_COINS, run_sensitivity_sweep
from simulator import Position


class SensitivitySweepTests(unittest.TestCase):
    def test_explicit_uniform_coin_matches_default(self) -> None:
        walk = EOGQuantumWalk(2, 3, {Position(1, 0)})
        default = walk.run_with_measurement_interval(Position(0, 0), 6, 1)
        explicit = walk.run_with_measurement_interval(
            Position(0, 0), 6, 1, INITIAL_COINS["uniform"]
        )
        self.assertEqual(default, explicit)

    def test_invalid_initial_coin_is_rejected(self) -> None:
        walk = EOGQuantumWalk(2, 3, set())
        with self.assertRaises(ValueError):
            walk.run_with_measurement_interval(Position(0, 0), 2, 1, (1j,))
        with self.assertRaises(ValueError):
            walk.run_with_measurement_interval(Position(0, 0), 2, 1, (1j, 1j, 1j, 1j))

    def test_sweep_covers_every_non_start_terminal(self) -> None:
        summaries = run_sensitivity_sweep(2, 3, Position(0, 0), 6, (1, 3))
        self.assertEqual(len(summaries), len(INITIAL_COINS) * 2)
        self.assertTrue(all(item.terminals_checked == 8 for item in summaries))

    def test_terminal_position_changes_absorption(self) -> None:
        summaries = run_sensitivity_sweep(2, 3, Position(0, 0), 6, (1,))
        self.assertTrue(all(item.spread > 0.0 for item in summaries))

    def test_sweep_is_reproducible(self) -> None:
        arguments = (2, 3, Position(0, 0), 4, (1, 4))
        self.assertEqual(run_sensitivity_sweep(*arguments), run_sensitivity_sweep(*arguments))


if __name__ == "__main__":
    unittest.main(verbosity=2)
