#!/usr/bin/env python3
"""Verification for the installable Area One verifier metadata."""

import tomllib
import unittest
from pathlib import Path

from evidence_bundle import VERSION


PYPROJECT = Path(__file__).with_name("pyproject.toml")
EXPECTED_MODULES = {
    "checkpoint_witness",
    "evidence_bundle",
    "issuer_trust",
    "report_file_verifier",
    "report_signature",
    "rfc3161_timestamp",
    "transparency_log",
    "witness_quorum",
}


class PackageMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    def test_distribution_version_matches_cli_version(self) -> None:
        self.assertEqual(self.metadata["project"]["version"], VERSION)

    def test_runtime_dependencies_are_exactly_pinned(self) -> None:
        self.assertEqual(
            self.metadata["project"]["dependencies"],
            ["cryptography==46.0.6", "rfc3161ng==2.1.3"],
        )

    def test_console_command_targets_bundle_verifier(self) -> None:
        self.assertEqual(
            self.metadata["project"]["scripts"]["area-one-verify"],
            "evidence_bundle:main",
        )

    def test_all_verifier_modules_are_packaged(self) -> None:
        self.assertEqual(set(self.metadata["tool"]["setuptools"]["py-modules"]), EXPECTED_MODULES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
