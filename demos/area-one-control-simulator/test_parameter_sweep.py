#!/usr/bin/env python3
"""Verification for the exhaustive bounded parameter sweep."""

import unittest

from parameter_sweep import grid_positions, run_parameter_sweep
from simulator import Position


class ParameterSweepTests(unittest.TestCase):
    def test_grid_positions_cover_full_coordinate_domain(self) -> None:
        self.assertEqual(
            grid_positions(2, 2),
            (
                Position(0, 0),
                Position(0, 1),
                Position(0, 2),
                Position(1, 0),
                Position(1, 1),
                Position(1, 2),
            ),
        )

    def test_small_sweep_checks_every_pair_and_protocol(self) -> None:
        summary = run_parameter_sweep(2, 2, 4)
        self.assertEqual(summary.grids_checked, 4)
        self.assertEqual(summary.operator_checks, 4)
        self.assertEqual(summary.classical_runs, 65)
        self.assertEqual(summary.quantum_protocol_runs, 195)
        self.assertEqual(summary.overlap_identity_checks, 2)
        self.assertLessEqual(summary.maximum_unitarity_error, 1e-12)
        self.assertLessEqual(summary.maximum_probability_error, 1e-12)

    def test_sweep_is_reproducible(self) -> None:
        self.assertEqual(
            run_parameter_sweep(1, 2, 3),
            run_parameter_sweep(1, 2, 3),
        )

    def test_invalid_bounds_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_parameter_sweep(maximum_step=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
