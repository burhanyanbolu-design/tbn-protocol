#!/usr/bin/env python3
"""Verification for surviving-state coherence analysis."""

import unittest

from coherence_analysis import basis_index, run_coherence_ensemble
from eog_quantum_walk import EOGQuantumWalk
from simulator import Position


class CoherenceAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(3, 5, {Position(1, 0)})

    def test_basis_uses_every_coordinate_direction_state(self) -> None:
        self.assertEqual(len(basis_index(self.walk)), 5 * 4 * 4)

    def test_zero_noise_surviving_ensemble_is_pure(self) -> None:
        result = run_coherence_ensemble(self.walk, Position(0, 0), 8, 0.0, 10, 7)
        self.assertAlmostEqual(result.purity, 1.0, places=12)
        self.assertGreater(result.normalized_l1_coherence, 0.0)
        self.assertLessEqual(result.normalized_l1_coherence, 1.0)

    def test_phase_noise_reduces_ensemble_purity(self) -> None:
        clean = run_coherence_ensemble(self.walk, Position(0, 0), 8, 0.0, 100, 7)
        noisy = run_coherence_ensemble(self.walk, Position(0, 0), 8, 0.1, 100, 7)
        self.assertLess(noisy.purity, clean.purity)

    def test_same_seed_reproduces_coherence_summary(self) -> None:
        first = run_coherence_ensemble(self.walk, Position(0, 0), 6, 0.1, 20, 5)
        second = run_coherence_ensemble(self.walk, Position(0, 0), 6, 0.1, 20, 5)
        self.assertEqual(first, second)

    def test_no_surviving_probability_has_no_coherence(self) -> None:
        with self.assertRaises(RuntimeError):
            run_coherence_ensemble(self.walk, Position(1, 0), 2, 0.0, 2, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
