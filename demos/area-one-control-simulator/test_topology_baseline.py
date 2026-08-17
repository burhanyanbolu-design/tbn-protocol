#!/usr/bin/env python3
"""Verification for the ordinary topology-matched index baseline."""

import unittest

from eog_quantum_walk import EOGQuantumWalk
from simulator import Position
from topology_baseline import (
    compare_topologies,
    coordinate_to_node,
    node_to_coordinate,
)


class TopologyBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(2, 3, {Position(1, 0)})

    def test_coordinate_node_mapping_round_trips(self) -> None:
        for row in range(3):
            for column in range(3):
                position = Position(row, column)
                node = coordinate_to_node(position, 3)
                self.assertEqual(node_to_coordinate(node, 3, 3), position)

    def test_full_coordinates_match_unique_index_evolution(self) -> None:
        result = compare_topologies(self.walk, Position(0, 0), 8)
        self.assertLessEqual(result.maximum_amplitude_difference, 1e-12)
        self.assertAlmostEqual(result.eog_absorption, result.indexed_absorption, places=12)

    def test_display_labels_are_not_unique_state_ids(self) -> None:
        result = compare_topologies(self.walk, Position(0, 0), 4)
        self.assertEqual(result.coordinate_states, 9)
        self.assertEqual(result.indexed_nodes, 9)
        self.assertEqual(result.unique_display_labels, 7)

    def test_periodic_measurement_schedule_also_matches(self) -> None:
        result = compare_topologies(
            self.walk, Position(0, 0), 8, measurement_interval=3
        )
        self.assertLessEqual(result.maximum_amplitude_difference, 1e-12)
        self.assertAlmostEqual(result.eog_absorption, result.indexed_absorption, places=12)

    def test_invalid_node_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            node_to_coordinate(9, 3, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
