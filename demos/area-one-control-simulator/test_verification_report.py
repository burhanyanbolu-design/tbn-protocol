#!/usr/bin/env python3
"""Verification for deterministic Area One evidence reports."""

import copy
import json
import unittest

from simulator import Position
from verification_report import (
    LIMITATIONS,
    build_verification_report,
    verify_report_hash,
)


class VerificationReportTests(unittest.TestCase):
    def build_small_report(self):
        return build_verification_report(
            step=2,
            rows=3,
            evolution_steps=4,
            start=Position(0, 0),
            terminal=Position(1, 0),
            trajectories=100,
            seed=17,
        )

    def test_generated_report_passes_and_hash_verifies(self) -> None:
        report = self.build_small_report()
        self.assertTrue(report["verdict"]["passed"])
        self.assertTrue(verify_report_hash(report))

    def test_tampering_invalidates_hash(self) -> None:
        report = self.build_small_report()
        tampered = copy.deepcopy(report)
        tampered["configuration"]["seed"] = 18
        self.assertFalse(verify_report_hash(tampered))

    def test_same_configuration_produces_identical_report(self) -> None:
        self.assertEqual(self.build_small_report(), self.build_small_report())

    def test_limitations_are_embedded_in_verdict(self) -> None:
        report = self.build_small_report()
        self.assertEqual(report["verdict"]["not_supported"], list(LIMITATIONS))

    def test_report_is_json_serializable(self) -> None:
        encoded = json.dumps(self.build_small_report(), sort_keys=True)
        self.assertIn("area-one-verification-report/1.0", encoded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
