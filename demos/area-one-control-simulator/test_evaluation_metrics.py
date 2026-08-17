#!/usr/bin/env python3
"""Verification for Area One evaluation metrics."""

import unittest

from eog_quantum_walk import EOGQuantumWalk
from evaluation_metrics import (
    conditional_mean_detection_step,
    evaluate_protocol,
    scheduled_measurement_steps,
)
from quantum_walk_baseline import WalkResult
from simulator import Position


class EvaluationMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walk = EOGQuantumWalk(3, 5, {Position(1, 0)})

    def test_measurement_schedule_includes_final_step(self) -> None:
        self.assertEqual(scheduled_measurement_steps(12, 1), tuple(range(1, 13)))
        self.assertEqual(scheduled_measurement_steps(12, 3), (3, 6, 9, 12))
        self.assertEqual(scheduled_measurement_steps(12, 5), (5, 10, 12))
        self.assertEqual(scheduled_measurement_steps(12, 12), (12,))

    def test_repeated_protocol_metrics(self) -> None:
        result = evaluate_protocol(self.walk, Position(0, 0), 12, 1, "repeated")
        self.assertEqual(result.measurement_checks, 12)
        self.assertEqual(result.logical_coin_applications, 12)
        self.assertEqual(result.logical_shift_applications, 12)
        self.assertGreater(result.terminal_probability, 0.0)
        self.assertLessEqual(result.maximum_unitary_norm_error, 1e-12)

    def test_final_only_detection_mean_is_final_step(self) -> None:
        result = evaluate_protocol(self.walk, Position(0, 0), 12, 12, "final-only")
        self.assertEqual(result.measurement_checks, 1)
        self.assertAlmostEqual(result.conditional_mean_detection_step, 12.0)

    def test_no_absorption_has_no_conditional_mean(self) -> None:
        result = WalkResult((), 1.0, 0.0)
        self.assertIsNone(conditional_mean_detection_step(result))

    def test_invalid_interval_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            scheduled_measurement_steps(12, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
