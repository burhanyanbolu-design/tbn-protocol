#!/usr/bin/env python3
"""Verification for Area One issuer trust, rotation, and revocation."""

import copy
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa

from issuer_trust import (
    calculate_trust_hash,
    create_registry,
    revoke_key,
    rotate_registry,
    verify_registry,
    verify_trusted_report,
)
from report_file_verifier import load_report
from report_signature import create_signature, key_id_for


REPORT = Path(__file__).with_name("verification-report.json")
ISSUER = "Area One Test Issuer"
T0 = "2026-08-15T09:00:00Z"
T1 = "2026-08-15T10:00:00Z"
T2 = "2026-08-15T11:00:00Z"
T3 = "2026-08-15T12:00:00Z"


class IssuerTrustTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = load_report(REPORT)
        cls.old_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.new_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def registry(self):
        return create_registry(ISSUER, self.old_private.public_key(), T0)

    def test_initial_registry_and_signature_are_trusted(self) -> None:
        registry = self.registry()
        self.assertTrue(verify_registry(registry, registry["trust_hash"]).valid)
        evidence = create_signature(self.report, self.old_private, ISSUER, T1)
        result = verify_trusted_report(
            self.report, evidence, registry, registry["trust_hash"], True
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.key_status, "active")

    def test_rotation_preserves_old_signatures_only_before_cutover(self) -> None:
        registry = self.registry()
        rotated = rotate_registry(
            registry,
            registry["trust_hash"],
            self.new_private.public_key(),
            T2,
        )
        before = create_signature(self.report, self.old_private, ISSUER, T1)
        after = create_signature(self.report, self.old_private, ISSUER, T3)
        new = create_signature(self.report, self.new_private, ISSUER, T3)
        self.assertTrue(
            verify_trusted_report(
                self.report, before, rotated, rotated["trust_hash"]
            ).valid
        )
        self.assertFalse(
            verify_trusted_report(
                self.report, after, rotated, rotated["trust_hash"]
            ).valid
        )
        new_result = verify_trusted_report(
            self.report, new, rotated, rotated["trust_hash"]
        )
        self.assertTrue(new_result.valid)
        self.assertEqual(new_result.key_status, "active")

    def test_revocation_fails_closed_for_prior_signatures(self) -> None:
        registry = self.registry()
        evidence = create_signature(self.report, self.old_private, ISSUER, T1)
        revoked = revoke_key(
            registry,
            registry["trust_hash"],
            key_id_for(self.old_private.public_key()),
            T2,
            "suspected compromise",
        )
        result = verify_trusted_report(
            self.report, evidence, revoked, revoked["trust_hash"]
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.key_status, "revoked")
        self.assertIn("fail closed", " ".join(result.errors))

    def test_independent_hash_rejects_rehashed_tampering(self) -> None:
        registry = self.registry()
        expected = registry["trust_hash"]
        tampered = copy.deepcopy(registry)
        tampered["issuer"] = "Impostor"
        tampered["trust_hash"] = calculate_trust_hash(tampered)
        result = verify_registry(tampered, expected)
        self.assertFalse(result.valid)
        self.assertIn("independently expected", " ".join(result.errors))

    def test_wrong_expected_hash_rejects_valid_registry(self) -> None:
        registry = self.registry()
        result = verify_registry(registry, "sha256:" + "0" * 64)
        self.assertFalse(result.valid)

    def test_signature_before_key_validity_is_rejected(self) -> None:
        registry = self.registry()
        evidence = create_signature(
            self.report,
            self.old_private,
            ISSUER,
            "2026-08-15T08:59:59Z",
        )
        result = verify_trusted_report(
            self.report, evidence, registry, registry["trust_hash"]
        )
        self.assertFalse(result.valid)
        self.assertIn("predates", " ".join(result.errors))

    def test_registry_rejects_duplicate_active_keys(self) -> None:
        registry = self.registry()
        duplicate = copy.deepcopy(registry["keys"][0])
        duplicate["key_id"] = key_id_for(self.new_private.public_key())
        registry["keys"].append(duplicate)
        registry["trust_hash"] = calculate_trust_hash(registry)
        result = verify_registry(registry, registry["trust_hash"])
        self.assertFalse(result.valid)
        self.assertIn("more than one active", " ".join(result.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
