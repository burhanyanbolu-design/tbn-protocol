#!/usr/bin/env python3
"""Verification for the periodic EOG-coordinate Grover walk."""

import unittest

from eog_quantum_walk import EOGQuantumWalk, grover_step, state_norm
from quantum_walk_baseline import verify_probability_accounting
from simulator import Position


class EOGQuantumWalkTests(unittest.TestCase):
    def test_grover_coin_and_shift_preserve_norm(self) -> None:
        state = {(Position(0, 0), direction): 0.5 + 0j for direction in range(4)}
        evolved = grover_step(state, rows=5, width=4)
        self.assertAlmostEqual(state_norm(state), state_norm(evolved), places=12)

    def test_quantum_and_classical_probability_accounting(self) -> None:
        walk = EOGQuantumWalk(3, 5, {Position(1, 0)})
        verify_probability_accounting(walk.run(Position(0, 0), 12))
        verify_probability_accounting(walk.run_classical(Position(0, 0), 12))

    def test_overlapping_label_does_not_merge_states(self) -> None:
        walk = EOGQuantumWalk(3, 5, {Position(1, 0)})
        endpoint = Position(0, 3)
        terminal = Position(1, 0)
        self.assertEqual(walk.label(endpoint), walk.label(terminal))
        self.assertEqual(walk.coordinates_for_label(3), (endpoint, terminal))
        self.assertEqual(walk.run(terminal, 2).metrics, ())
        self.assertEqual(len(walk.run(endpoint, 2).metrics), 2)

    def test_periodic_boundary_is_deterministic(self) -> None:
        walk = EOGQuantumWalk(3, 5, {Position(1, 0)})
        self.assertEqual(walk.run(Position(0, 0), 8), walk.run(Position(0, 0), 8))

    def test_repeated_protocol_matches_default_run(self) -> None:
        walk = EOGQuantumWalk(3, 5, {Position(1, 0)})
        self.assertEqual(
            walk.run(Position(0, 0), 8),
            walk.run_with_measurement_interval(Position(0, 0), 8, 1),
        )

    def test_final_only_measurement_occurs_at_last_step(self) -> None:
        walk = EOGQuantumWalk(3, 5, {Position(1, 0)})
        result = walk.run_with_measurement_interval(Position(0, 0), 8, 8)
        self.assertTrue(all(item.absorbed_probability == 0 for item in result.metrics[:-1]))
        self.assertGreater(result.metrics[-1].absorbed_probability, 0)
        verify_probability_accounting(result)

    def test_measurement_schedule_changes_absorption(self) -> None:
        walk = EOGQuantumWalk(3, 5, {Position(1, 0)})
        repeated = walk.run_with_measurement_interval(Position(0, 0), 12, 1)
        final_only = walk.run_with_measurement_interval(Position(0, 0), 12, 12)
        self.assertNotAlmostEqual(
            repeated.cumulative_absorption,
            final_only.cumulative_absorption,
            places=12,
        )

    def test_invalid_measurement_interval_is_rejected(self) -> None:
        walk = EOGQuantumWalk(3, 5, set())
        with self.assertRaises(ValueError):
            walk.run_with_measurement_interval(Position(0, 0), 2, 0)

    def test_invalid_coordinate_is_rejected(self) -> None:
        walk = EOGQuantumWalk(3, 5, set())
        with self.assertRaises(ValueError):
            walk.run(Position(5, 0), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
