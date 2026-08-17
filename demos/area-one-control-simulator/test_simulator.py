#!/usr/bin/env python3
"""Focused verification for deterministic Area One behavior."""

import unittest

from simulator import DEFAULT_EVENTS, DeterministicControlSimulator, Position


class DeterministicControlSimulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.simulator = DeterministicControlSimulator(
            step=5,
            terminal_positions=(Position(3, 2),),
            event_map=DEFAULT_EVENTS,
        )

    def test_same_input_replays_identically(self) -> None:
        route = ("down-right", "right", "down-left", "down-right")
        first = self.simulator.run(Position(0, 0), route)
        second = self.simulator.run(Position(0, 0), route)
        self.assertEqual(first, second)

    def test_overlapping_label_preserves_both_coordinates(self) -> None:
        endpoint = Position(0, 5)
        next_row = Position(1, 0)
        self.assertNotEqual(endpoint, next_row)
        self.assertEqual(self.simulator.label(endpoint), 5)
        self.assertEqual(self.simulator.label(next_row), 5)
        self.assertEqual(
            self.simulator.positions_for_label(5), (endpoint, next_row)
        )
        self.assertEqual(
            self.simulator.positions_for_label(7), (Position(1, 2),)
        )

    def test_boundary_rejection_dispatches_no_event(self) -> None:
        result = self.simulator.run(Position(0, 0), ("left",))
        self.assertEqual(result.stop_reason, "BOUNDARY_REJECTED")
        self.assertEqual(result.final_position, Position(0, 0))
        self.assertEqual(result.transitions[0].event, "NOT_DISPATCHED")

    def test_terminal_halts_before_remaining_route(self) -> None:
        route = ("down-right", "right", "down-left", "down-right", "right")
        result = self.simulator.run(Position(0, 0), route)
        self.assertEqual(result.stop_reason, "TERMINAL_REACHED")
        self.assertEqual(result.final_position, Position(3, 2))
        self.assertEqual(len(result.transitions), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
