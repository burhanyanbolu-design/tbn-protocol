#!/usr/bin/env python3
"""Verification for detached Area One issuer signatures."""

import copy
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa

from report_file_verifier import calculate_report_hash, load_report
from report_signature import (
    ALGORITHM,
    SignatureError,
    create_signature,
    key_id_for,
    verify_signature,
)


REPORT = Path(__file__).with_name("verification-report.json")
ISSUER = "Area One Test Issuer"


class ReportSignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = load_report(REPORT)
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = cls.private_key.public_key()

    def signed(self):
        return create_signature(self.report, self.private_key, ISSUER)

    def test_signature_verifies_with_expected_issuer(self) -> None:
        evidence = self.signed()
        result = verify_signature(
            self.report, evidence, self.public_key, ISSUER, require_passed=True
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.key_id, key_id_for(self.public_key))
        self.assertEqual(evidence["algorithm"], ALGORITHM)

    def test_modified_report_is_rejected_even_if_rehashed(self) -> None:
        report = copy.deepcopy(self.report)
        report["configuration"]["seed"] += 1
        report["report_hash"] = calculate_report_hash(report)
        result = verify_signature(report, self.signed(), self.public_key)
        self.assertFalse(result.valid)
        self.assertIn("does not match report", " ".join(result.errors))

    def test_modified_signature_metadata_is_rejected(self) -> None:
        evidence = self.signed()
        evidence["issuer"] = "Impostor"
        result = verify_signature(self.report, evidence, self.public_key, ISSUER)
        self.assertFalse(result.valid)
        self.assertIn("issuer", " ".join(result.errors))

    def test_wrong_public_key_is_rejected(self) -> None:
        wrong_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        ).public_key()
        result = verify_signature(self.report, self.signed(), wrong_key)
        self.assertFalse(result.valid)
        self.assertIn("key_id", " ".join(result.errors))

    def test_extra_unsigned_field_is_rejected(self) -> None:
        evidence = self.signed()
        evidence["comment"] = "not part of the signature schema"
        result = verify_signature(self.report, evidence, self.public_key)
        self.assertFalse(result.valid)
        self.assertIn("fields differ", " ".join(result.errors))

    def test_weak_private_key_is_rejected(self) -> None:
        weak_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        with self.assertRaisesRegex(SignatureError, "at least 2048 bits"):
            create_signature(self.report, weak_key, ISSUER)

    def test_empty_issuer_is_rejected(self) -> None:
        with self.assertRaisesRegex(SignatureError, "must not be empty"):
            create_signature(self.report, self.private_key, "   ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
