#!/usr/bin/env python3
"""Verification for seeded classical probabilistic movement."""

import unittest

from probabilistic_simulator import ProbabilisticControlSimulator
from simulator import DEFAULT_EVENTS, DeterministicControlSimulator, Position


class ProbabilisticControlSimulatorTests(unittest.TestCase):
    def test_same_seed_replays_identically(self) -> None:
        core = DeterministicControlSimulator(5, (Position(3, 4),), DEFAULT_EVENTS)
        weights = {"down-right": 1, "right": 1, "down-left": 1}
        first = ProbabilisticControlSimulator(core, weights, seed=7)
        second = ProbabilisticControlSimulator(core, weights, seed=7)
        self.assertEqual(first.run(Position(0, 0), 12), second.run(Position(0, 0), 12))

    def test_maximum_steps_is_a_hard_stop(self) -> None:
        core = DeterministicControlSimulator(5, (), DEFAULT_EVENTS)
        simulator = ProbabilisticControlSimulator(core, {"down": 1}, seed=1)
        result = simulator.run(Position(0, 0), 3)
        self.assertEqual(result.stop_reason, "MAX_STEPS_REACHED")
        self.assertEqual(result.final_position, Position(3, 0))
        self.assertEqual(len(result.transitions), 3)

    def test_selected_invalid_move_dispatches_no_event(self) -> None:
        core = DeterministicControlSimulator(5, (), DEFAULT_EVENTS)
        simulator = ProbabilisticControlSimulator(core, {"left": 1}, seed=1)
        result = simulator.run(Position(0, 0), 3)
        self.assertEqual(result.stop_reason, "BOUNDARY_REJECTED")
        self.assertEqual(result.transitions[0].event, "NOT_DISPATCHED")

    def test_invalid_weights_are_rejected(self) -> None:
        core = DeterministicControlSimulator(5, (), DEFAULT_EVENTS)
        with self.assertRaises(ValueError):
            ProbabilisticControlSimulator(core, {"right": -1}, seed=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
