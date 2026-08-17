#!/usr/bin/env python3
"""Verification for the independent Area One report-file verifier."""

import copy
import tempfile
import unittest
from pathlib import Path

from report_file_verifier import (
    ReportLoadError,
    calculate_report_hash,
    load_report,
    verify_report,
)


REPORT = Path(__file__).with_name("verification-report.json")


class ReportFileVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = load_report(REPORT)

    def test_generated_artifact_is_valid_and_passed(self) -> None:
        result = verify_report(self.report, self.report["report_hash"], True)
        self.assertTrue(result.valid)
        self.assertTrue(result.verdict_passed)

    def test_tampering_is_rejected(self) -> None:
        report = copy.deepcopy(self.report)
        report["configuration"]["seed"] += 1
        self.assertIn("report hash", " ".join(verify_report(report).errors))

    def test_rehashed_inconsistent_verdict_is_rejected(self) -> None:
        report = copy.deepcopy(self.report)
        report["verdict"]["passed"] = False
        report["report_hash"] = calculate_report_hash(report)
        result = verify_report(report)
        self.assertFalse(result.valid)
        self.assertIn("inconsistent", " ".join(result.errors))

    def test_unexpected_hash_is_rejected(self) -> None:
        expected = "sha256:" + "0" * 64
        self.assertFalse(verify_report(self.report, expected).valid)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":"a","schema_version":"b"}')
            with self.assertRaisesRegex(ReportLoadError, "duplicate JSON key"):
                load_report(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
