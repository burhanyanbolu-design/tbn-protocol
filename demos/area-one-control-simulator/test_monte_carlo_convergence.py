#!/usr/bin/env python3
"""Verification for Monte Carlo convergence reporting."""

import unittest

from eog_quantum_walk import EOGQuantumWalk
from monte_carlo_convergence import parse_sample_sizes, run_convergence_study
from simulator import Position


class MonteCarloConvergenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(2, 3, {Position(1, 0)})
        self.start = Position(0, 0)

    def test_sample_sizes_are_sorted_and_deduplicated(self) -> None:
        self.assertEqual(parse_sample_sizes("1000,100,500,100"), (100, 500, 1000))

    def test_larger_sample_has_smaller_standard_error(self) -> None:
        points = run_convergence_study(
            self.walk, self.start, 5, 0.1, (50, 200, 1000), 17
        )
        self.assertLess(points[-1].standard_error, points[0].standard_error)
        self.assertLess(points[-1].absolute_error, 0.03)

    def test_reported_interval_contains_estimate(self) -> None:
        points = run_convergence_study(
            self.walk, self.start, 5, 0.1, (100,), 17
        )
        point = points[0]
        self.assertLessEqual(point.confidence_low, point.estimated_absorption)
        self.assertGreaterEqual(point.confidence_high, point.estimated_absorption)

    def test_same_seed_reproduces_study(self) -> None:
        arguments = (self.walk, self.start, 4, 0.1, (50, 100), 9)
        self.assertEqual(run_convergence_study(*arguments), run_convergence_study(*arguments))

    def test_invalid_sample_size_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_convergence_study(self.walk, self.start, 2, 0.1, (1,), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
