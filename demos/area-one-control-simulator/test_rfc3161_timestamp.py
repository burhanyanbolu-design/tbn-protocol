#!/usr/bin/env python3
"""Offline verification for the live Area One RFC 3161 fixture."""

import base64
import copy
import json
import unittest
from pathlib import Path

from evidence_bundle import read_bundle
from rfc3161_timestamp import (
    calculate_evidence_hash,
    load_certificates,
    verify_evidence,
)


DIRECTORY = Path(__file__).parent
BUNDLE_PATH = DIRECTORY / "area-one-evidence-bundle-fixture.zip"
ROOT_PATH = DIRECTORY / "freetsa-root.pem"


class RFC3161TimestampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manifest, files = read_bundle(BUNDLE_PATH)
        artifacts = manifest["artifacts"]
        cls.log = json.loads(files[artifacts["transparency_log"]])
        cls.evidence = json.loads(files[artifacts["rfc3161"]])
        cls.roots = load_certificates(ROOT_PATH)

    def test_live_fixture_verifies_offline(self) -> None:
        result = verify_evidence(self.log, self.evidence, self.roots)
        self.assertTrue(result.valid)
        self.assertEqual(result.granted_at, "2026-08-15T03:33:25Z")
        self.assertIn("Free TSA", result.tsa_subject)

    def test_evidence_metadata_tampering_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["granted_at"] = "2026-08-15T03:26:44Z"
        result = verify_evidence(self.log, evidence, self.roots)
        self.assertFalse(result.valid)
        self.assertIn("evidence_hash", " ".join(result.errors))

    def test_rehashed_nonce_tampering_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["nonce"] = "1"
        evidence["evidence_hash"] = calculate_evidence_hash(evidence)
        result = verify_evidence(self.log, evidence, self.roots)
        self.assertFalse(result.valid)
        self.assertIn("nonce", " ".join(result.errors))

    def test_rehashed_response_tampering_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        response = bytearray(base64.b64decode(evidence["response_der"]))
        response[-1] ^= 1
        evidence["response_der"] = base64.b64encode(response).decode("ascii")
        evidence["evidence_hash"] = calculate_evidence_hash(evidence)
        result = verify_evidence(self.log, evidence, self.roots)
        self.assertFalse(result.valid)
        self.assertIn("RFC 3161 verification failed", " ".join(result.errors))

    def test_rehashed_checkpoint_substitution_is_rejected(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["checkpoint_hash"] = "sha256:" + "0" * 64
        evidence["evidence_hash"] = calculate_evidence_hash(evidence)
        result = verify_evidence(self.log, evidence, self.roots)
        self.assertFalse(result.valid)
        joined = " ".join(result.errors)
        self.assertTrue("checkpoint" in joined or "imprint" in joined)

    def test_missing_explicit_trust_root_is_rejected(self) -> None:
        result = verify_evidence(self.log, self.evidence, [])
        self.assertFalse(result.valid)
        self.assertIn("trust root", " ".join(result.errors))

    def test_alternate_log_is_rejected(self) -> None:
        log = copy.deepcopy(self.log)
        log["log_id"] = "alternate"
        result = verify_evidence(log, self.evidence, self.roots)
        self.assertFalse(result.valid)
        self.assertIn("log_id", " ".join(result.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
