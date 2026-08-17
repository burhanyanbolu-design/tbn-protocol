#!/usr/bin/env python3
"""Verification for Area One append-only transparency evidence."""

import copy
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa

from issuer_trust import create_registry
from report_file_verifier import load_report
from report_signature import create_signature
from transparency_log import (
    TransparencyError,
    append_trusted_entry,
    calculate_checkpoint_hash,
    create_inclusion_proof,
    create_log,
    verify_extension,
    verify_inclusion_proof,
    verify_log,
)


REPORT = Path(__file__).with_name("verification-report.json")
ISSUER = "Area One Test Issuer"
T0 = "2026-08-15T09:00:00Z"
TIMES = (
    ("2026-08-15T10:00:00Z", "2026-08-15T10:01:00Z"),
    ("2026-08-15T11:00:00Z", "2026-08-15T11:01:00Z"),
    ("2026-08-15T12:00:00Z", "2026-08-15T12:01:00Z"),
)


class TransparencyLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = load_report(REPORT)
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.registry = create_registry(ISSUER, cls.private_key.public_key(), T0)

    def append(self, log, number):
        issued_at, logged_at = TIMES[number]
        evidence = create_signature(self.report, self.private_key, ISSUER, issued_at)
        expected = log["checkpoints"][-1]["checkpoint_hash"] if log["checkpoints"] else None
        return append_trusted_entry(
            log,
            self.report,
            evidence,
            self.registry,
            self.registry["trust_hash"],
            expected,
            logged_at,
        )

    def three_entry_log(self):
        log = create_log("area-one-test")
        for number in range(3):
            log = self.append(log, number)
        return log

    def test_trusted_entries_create_valid_checkpoint_chain(self) -> None:
        log = self.three_entry_log()
        final = log["checkpoints"][-1]["checkpoint_hash"]
        result = verify_log(log, final)
        self.assertTrue(result.valid)
        self.assertEqual(result.tree_size, 3)

    def test_non_empty_append_requires_pinned_checkpoint(self) -> None:
        log = self.append(create_log("area-one-test"), 0)
        evidence = create_signature(self.report, self.private_key, ISSUER, TIMES[1][0])
        with self.assertRaisesRegex(TransparencyError, "requires expected"):
            append_trusted_entry(
                log,
                self.report,
                evidence,
                self.registry,
                self.registry["trust_hash"],
                logged_at=TIMES[1][1],
            )

    def test_valid_new_log_extends_pinned_old_log(self) -> None:
        old = self.append(create_log("area-one-test"), 0)
        new = self.append(old, 1)
        result = verify_extension(
            old,
            new,
            old["checkpoints"][-1]["checkpoint_hash"],
            new["checkpoints"][-1]["checkpoint_hash"],
        )
        self.assertTrue(result.valid)
        self.assertEqual((result.old_size, result.new_size), (1, 2))

    def test_alternate_valid_history_is_not_an_extension(self) -> None:
        old = self.append(create_log("area-one-test"), 0)
        alternate = self.append(create_log("area-one-test"), 1)
        result = verify_extension(
            old, alternate, old["checkpoints"][-1]["checkpoint_hash"]
        )
        self.assertFalse(result.valid)
        self.assertIn("not an exact prefix", " ".join(result.errors))

    def test_rewritten_log_id_fails_pinned_checkpoint(self) -> None:
        log = self.append(create_log("area-one-test"), 0)
        pinned = log["checkpoints"][-1]["checkpoint_hash"]
        rewritten = copy.deepcopy(log)
        rewritten["log_id"] = "replacement"
        rewritten["checkpoints"][0]["log_id"] = "replacement"
        rewritten["checkpoints"][0]["checkpoint_hash"] = calculate_checkpoint_hash(
            rewritten["checkpoints"][0]
        )
        result = verify_log(rewritten, pinned)
        self.assertFalse(result.valid)
        self.assertIn("independently expected", " ".join(result.errors))

    def test_inclusion_proofs_cover_odd_sized_tree(self) -> None:
        log = self.three_entry_log()
        expected_root = log["checkpoints"][-1]["root_hash"]
        for index in range(3):
            with self.subTest(index=index):
                proof = create_inclusion_proof(log, index)
                self.assertTrue(verify_inclusion_proof(proof, expected_root).valid)

    def test_tampered_inclusion_proof_is_rejected(self) -> None:
        log = self.three_entry_log()
        proof = create_inclusion_proof(log, 0)
        proof["entry_hash"] = "sha256:" + "0" * 64
        result = verify_inclusion_proof(
            proof, log["checkpoints"][-1]["root_hash"]
        )
        self.assertFalse(result.valid)

    def test_log_time_cannot_precede_signed_issuance(self) -> None:
        evidence = create_signature(self.report, self.private_key, ISSUER, TIMES[1][0])
        with self.assertRaisesRegex(TransparencyError, "cannot precede"):
            append_trusted_entry(
                create_log("area-one-test"),
                self.report,
                evidence,
                self.registry,
                self.registry["trust_hash"],
                logged_at=TIMES[0][1],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
