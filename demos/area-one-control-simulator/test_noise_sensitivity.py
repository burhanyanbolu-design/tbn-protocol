#!/usr/bin/env python3
"""Verification for the toy phase-noise sensitivity experiment."""

import unittest

from eog_quantum_walk import EOGQuantumWalk
from noise_sensitivity import run_noisy_ensemble
from simulator import Position


class NoiseSensitivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(3, 5, {Position(1, 0)})

    def test_zero_noise_matches_exact_walk(self) -> None:
        exact = self.walk.run(Position(0, 0), 12)
        sampled = run_noisy_ensemble(self.walk, Position(0, 0), 12, 0.0, 5, 7)
        self.assertAlmostEqual(sampled.mean_absorption, exact.cumulative_absorption, places=12)
        self.assertAlmostEqual(sampled.absorption_standard_deviation, 0.0, places=12)

    def test_same_seed_reproduces_ensemble(self) -> None:
        first = run_noisy_ensemble(self.walk, Position(0, 0), 8, 0.1, 20, 11)
        second = run_noisy_ensemble(self.walk, Position(0, 0), 8, 0.1, 20, 11)
        self.assertEqual(first, second)

    def test_noise_trajectories_preserve_probability(self) -> None:
        result = run_noisy_ensemble(self.walk, Position(0, 0), 8, 0.1, 20, 11)
        self.assertLessEqual(result.maximum_norm_error, 1e-12)
        self.assertLessEqual(result.maximum_probability_error, 1e-12)
        self.assertAlmostEqual(result.mean_absorption + result.mean_survival, 1.0, places=12)

    def test_nonzero_noise_has_ensemble_spread(self) -> None:
        result = run_noisy_ensemble(self.walk, Position(0, 0), 8, 0.1, 40, 11)
        self.assertGreater(result.absorption_standard_deviation, 0.0)

    def test_invalid_noise_probability_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_noisy_ensemble(self.walk, Position(0, 0), 2, 1.1, 2, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
