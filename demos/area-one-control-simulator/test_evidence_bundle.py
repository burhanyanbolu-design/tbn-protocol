#!/usr/bin/env python3
"""Verification for portable Area One evidence bundles."""

import copy
import io
import json
import unittest
import warnings
import zipfile
from pathlib import Path

from evidence_bundle import (
    BundleError,
    MANIFEST_NAME,
    calculate_bundle_hash,
    read_bundle,
    verify_bundle,
)


DIRECTORY = Path(__file__).parent
BUNDLE_PATH = DIRECTORY / "area-one-evidence-bundle-fixture.zip"
ANCHORS_PATH = DIRECTORY / "area-one-evidence-bundle-fixture-anchors.json"


class EvidenceBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.anchors = json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
        cls.bundle_bytes = BUNDLE_PATH.read_bytes()

    def verify(self, source=None, **overrides):
        values = {
            "expected_issuer_trust_hash": self.anchors["expected_issuer_trust_hash"],
            "expected_witness_policy_hash": self.anchors["expected_witness_policy_hash"],
            "expected_checkpoint_hash": self.anchors["expected_checkpoint_hash"],
            "expected_tsa_root_fingerprints": [self.anchors["expected_tsa_root_sha256"]],
            "expected_report_hash": self.anchors["expected_report_hash"],
        }
        values.update(overrides)
        return verify_bundle(source or self.bundle_bytes, **values)

    @staticmethod
    def zip_bytes(files):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in files:
                archive.writestr(name, data)
        return output.getvalue()

    def test_complete_fixture_passes_one_command_verification(self) -> None:
        result = self.verify()
        self.assertTrue(result.valid)
        self.assertEqual(len(result.accepted_witnesses), 2)
        self.assertEqual(result.granted_at, self.anchors["rfc3161_granted_at"])

    def test_wrong_independent_report_hash_is_rejected(self) -> None:
        result = self.verify(expected_report_hash="sha256:" + "0" * 64)
        self.assertFalse(result.valid)
        self.assertIn("expected hash", " ".join(result.errors))

    def test_wrong_tsa_root_fingerprint_is_rejected(self) -> None:
        result = self.verify(
            expected_tsa_root_fingerprints=["sha256:" + "0" * 64]
        )
        self.assertFalse(result.valid)
        self.assertIn("TSA roots", " ".join(result.errors))

    def test_artifact_byte_tampering_is_rejected_before_semantics(self) -> None:
        manifest, files = read_bundle(self.bundle_bytes)
        report_name = manifest["artifacts"]["report"]
        files[report_name] += b" "
        members = [(MANIFEST_NAME, json.dumps(manifest).encode())]
        members.extend(
            sorted(
                (name, data)
                for name, data in files.items()
                if name != MANIFEST_NAME
            )
        )
        with self.assertRaisesRegex(BundleError, "artifact hash mismatch"):
            self.verify(self.zip_bytes(members))

    def test_rehashed_report_forgery_fails_issuer_signature(self) -> None:
        manifest, files = read_bundle(self.bundle_bytes)
        report_name = manifest["artifacts"]["report"]
        report = json.loads(files[report_name])
        report["configuration"]["seed"] += 1
        files[report_name] = json.dumps(report, sort_keys=True).encode()
        manifest = copy.deepcopy(manifest)
        import hashlib
        manifest["files"][report_name] = "sha256:" + hashlib.sha256(files[report_name]).hexdigest()
        manifest["bundle_hash"] = calculate_bundle_hash(manifest)
        members = [(MANIFEST_NAME, json.dumps(manifest).encode())]
        members.extend(
            sorted(
                (name, data)
                for name, data in files.items()
                if name != MANIFEST_NAME
            )
        )
        result = self.verify(self.zip_bytes(members), expected_report_hash=None)
        self.assertFalse(result.valid)
        self.assertIn("report hash", " ".join(result.errors))

    def test_path_traversal_entry_is_rejected(self) -> None:
        malicious = self.zip_bytes(
            [(MANIFEST_NAME, b"{}"), ("../escape.json", b"{}")]
        )
        with self.assertRaisesRegex(BundleError, "unsafe ZIP entry"):
            read_bundle(malicious)

    def test_duplicate_zip_names_are_rejected(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            duplicate = self.zip_bytes(
                [(MANIFEST_NAME, b"{}"), (MANIFEST_NAME, b"{}")]
            )
        with self.assertRaisesRegex(BundleError, "duplicate file names"):
            read_bundle(duplicate)

    def test_unlisted_extra_file_is_rejected(self) -> None:
        with zipfile.ZipFile(io.BytesIO(self.bundle_bytes), "r") as archive:
            members = [(info.filename, archive.read(info)) for info in archive.infolist()]
        members.append(("hidden.json", b"{}"))
        with self.assertRaisesRegex(BundleError, "do not exactly match"):
            read_bundle(self.zip_bytes(members))

    def test_wrong_checkpoint_anchor_is_rejected(self) -> None:
        result = self.verify(expected_checkpoint_hash="sha256:" + "0" * 64)
        self.assertFalse(result.valid)
        joined = " ".join(result.errors)
        self.assertTrue("checkpoint" in joined or "log" in joined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
