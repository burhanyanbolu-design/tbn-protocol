#!/usr/bin/env python3
"""Verification for independent Area One checkpoint witnesses."""

import copy
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa

from checkpoint_witness import (
    WitnessError,
    create_attestation,
    verify_attestation,
    witness_key_id_for,
)
from issuer_trust import create_registry
from report_file_verifier import load_report
from report_signature import create_signature
from transparency_log import append_trusted_entry, create_log


REPORT = Path(__file__).with_name("verification-report.json")
ISSUER = "Area One Test Issuer"
WITNESS = "Independent Test Witness"
T0 = "2026-08-15T09:00:00Z"
ISSUED = "2026-08-15T10:00:00Z"
LOGGED = "2026-08-15T10:01:00Z"
WITNESSED = "2026-08-15T10:02:00Z"


class CheckpointWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = load_report(REPORT)
        cls.issuer_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.witness_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.registry = create_registry(ISSUER, cls.issuer_private.public_key(), T0)
        evidence = create_signature(cls.report, cls.issuer_private, ISSUER, ISSUED)
        cls.log = append_trusted_entry(
            create_log("area-one-test"),
            cls.report,
            evidence,
            cls.registry,
            cls.registry["trust_hash"],
            logged_at=LOGGED,
        )
        cls.checkpoint = cls.log["checkpoints"][-1]["checkpoint_hash"]

    def attestation(self):
        return create_attestation(
            self.log,
            self.checkpoint,
            self.witness_private,
            WITNESS,
            WITNESSED,
        )

    def test_independent_witness_attestation_verifies(self) -> None:
        result = verify_attestation(
            self.log,
            self.attestation(),
            self.witness_private.public_key(),
            WITNESS,
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.witness_key_id,
            witness_key_id_for(self.witness_private.public_key()),
        )

    def test_issuer_key_cannot_impersonate_witness(self) -> None:
        result = verify_attestation(
            self.log,
            self.attestation(),
            self.issuer_private.public_key(),
            WITNESS,
        )
        self.assertFalse(result.valid)
        self.assertIn("witness_key_id", " ".join(result.errors))

    def test_modified_witness_identity_is_rejected(self) -> None:
        attestation = self.attestation()
        attestation["witness"] = "Impostor"
        result = verify_attestation(
            self.log, attestation, self.witness_private.public_key(), WITNESS
        )
        self.assertFalse(result.valid)
        self.assertIn("expected witness", " ".join(result.errors))

    def test_modified_checkpoint_is_rejected(self) -> None:
        attestation = self.attestation()
        attestation["root_hash"] = "sha256:" + "0" * 64
        result = verify_attestation(
            self.log, attestation, self.witness_private.public_key()
        )
        self.assertFalse(result.valid)
        self.assertIn("root_hash", " ".join(result.errors))

    def test_witness_time_cannot_precede_checkpoint(self) -> None:
        with self.assertRaisesRegex(WitnessError, "cannot precede"):
            create_attestation(
                self.log,
                self.checkpoint,
                self.witness_private,
                WITNESS,
                ISSUED,
            )

    def test_empty_log_cannot_be_witnessed(self) -> None:
        with self.assertRaisesRegex(WitnessError, "empty logs"):
            create_attestation(
                create_log("area-one-test"),
                self.checkpoint,
                self.witness_private,
                WITNESS,
                WITNESSED,
            )

    def test_weak_witness_key_is_rejected(self) -> None:
        weak_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        with self.assertRaisesRegex(WitnessError, "at least 2048 bits"):
            create_attestation(
                self.log,
                self.checkpoint,
                weak_key,
                WITNESS,
                WITNESSED,
            )

    def test_alternate_valid_log_does_not_match_attestation(self) -> None:
        alternate = copy.deepcopy(self.log)
        alternate["log_id"] = "alternate"
        result = verify_attestation(
            alternate, self.attestation(), self.witness_private.public_key()
        )
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
