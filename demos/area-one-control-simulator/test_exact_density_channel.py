#!/usr/bin/env python3
"""Verification for the exact toy phase-noise density channel."""

import unittest

from eog_quantum_walk import EOGQuantumWalk
from exact_density_channel import run_exact_density_channel
from noise_sensitivity import run_noisy_ensemble
from simulator import Position


class ExactDensityChannelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(2, 3, {Position(1, 0)})
        self.start = Position(0, 0)

    def test_zero_noise_matches_pure_state_walk(self) -> None:
        pure = self.walk.run(self.start, 6)
        exact = run_exact_density_channel(self.walk, self.start, 6, 0.0)
        self.assertAlmostEqual(exact.absorbed_probability, pure.cumulative_absorption, places=12)
        self.assertAlmostEqual(exact.purity, 1.0, places=12)

    def test_probability_accounting_is_exact(self) -> None:
        result = run_exact_density_channel(self.walk, self.start, 6, 0.1)
        self.assertAlmostEqual(
            result.absorbed_probability + result.surviving_probability,
            1.0,
            places=12,
        )
        self.assertLessEqual(result.maximum_probability_error, 1e-12)

    def test_half_probability_fully_dephases_each_step(self) -> None:
        result = run_exact_density_channel(self.walk, self.start, 4, 0.5)
        self.assertAlmostEqual(result.normalized_l1_coherence, 0.0, places=12)

    def test_monte_carlo_converges_toward_exact_absorption(self) -> None:
        exact = run_exact_density_channel(self.walk, self.start, 5, 0.1)
        sampled = run_noisy_ensemble(self.walk, self.start, 5, 0.1, 1000, 17)
        self.assertLess(abs(exact.absorbed_probability - sampled.mean_absorption), 0.03)

    def test_invalid_noise_probability_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_exact_density_channel(self.walk, self.start, 2, -0.1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
