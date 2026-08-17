#!/usr/bin/env python3
"""Verification for Area One multi-witness quorum policies."""

import copy
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa

from checkpoint_witness import create_attestation
from issuer_trust import create_registry
from report_file_verifier import load_report
from report_signature import create_signature
from transparency_log import append_trusted_entry, create_log
from witness_quorum import (
    QuorumError,
    calculate_policy_hash,
    create_policy,
    verify_policy,
    verify_quorum,
)


REPORT = Path(__file__).with_name("verification-report.json")
ISSUER = "Area One Test Issuer"
T0 = "2026-08-15T09:00:00Z"
ISSUED = "2026-08-15T10:00:00Z"
LOGGED = "2026-08-15T10:01:00Z"
WITNESSED = "2026-08-15T10:02:00Z"


class WitnessQuorumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = load_report(REPORT)
        cls.issuer_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        registry = create_registry(ISSUER, cls.issuer_private.public_key(), T0)
        signature = create_signature(cls.report, cls.issuer_private, ISSUER, ISSUED)
        cls.log = append_trusted_entry(
            create_log("area-one-test"),
            cls.report,
            signature,
            registry,
            registry["trust_hash"],
            logged_at=LOGGED,
        )
        cls.checkpoint = cls.log["checkpoints"][-1]["checkpoint_hash"]
        cls.keys = [
            rsa.generate_private_key(public_exponent=65537, key_size=2048)
            for _ in range(3)
        ]
        cls.names = ["Witness A", "Witness B", "Witness C"]
        cls.policy = create_policy(
            "area-one-2-of-3",
            2,
            [(name, key.public_key()) for name, key in zip(cls.names, cls.keys)],
        )

    @classmethod
    def attest(cls, index):
        return create_attestation(
            cls.log,
            cls.checkpoint,
            cls.keys[index],
            cls.names[index],
            WITNESSED,
        )

    def verify(self, attestations, policy=None, expected_hash=None):
        selected = policy or self.policy
        return verify_quorum(
            self.log,
            attestations,
            selected,
            expected_hash or selected["policy_hash"],
        )

    def test_two_distinct_witnesses_meet_quorum(self) -> None:
        result = self.verify([self.attest(0), self.attest(1)])
        self.assertTrue(result.valid)
        self.assertEqual(result.accepted_witnesses, ("Witness A", "Witness B"))

    def test_one_witness_does_not_meet_quorum(self) -> None:
        result = self.verify([self.attest(0)])
        self.assertFalse(result.valid)
        self.assertEqual(len(result.accepted_witnesses), 1)

    def test_duplicate_attestation_does_not_count_twice(self) -> None:
        attestation = self.attest(0)
        result = self.verify([attestation, copy.deepcopy(attestation)])
        self.assertFalse(result.valid)
        self.assertEqual(len(result.accepted_witnesses), 1)
        self.assertIn("duplicate", " ".join(result.rejected_evidence))

    def test_unknown_witness_does_not_count(self) -> None:
        unknown_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        unknown = create_attestation(
            self.log, self.checkpoint, unknown_key, "Unknown", WITNESSED
        )
        result = self.verify([self.attest(0), unknown])
        self.assertFalse(result.valid)
        self.assertIn("unknown", " ".join(result.rejected_evidence))

    def test_invalid_extra_evidence_does_not_block_real_quorum(self) -> None:
        invalid = self.attest(2)
        invalid["root_hash"] = "sha256:" + "0" * 64
        result = self.verify([invalid, self.attest(0), self.attest(1)])
        self.assertTrue(result.valid)
        self.assertEqual(len(result.accepted_witnesses), 2)
        self.assertEqual(len(result.rejected_evidence), 1)

    def test_rehashed_policy_tampering_fails_old_pinned_hash(self) -> None:
        original_hash = self.policy["policy_hash"]
        tampered = copy.deepcopy(self.policy)
        tampered["policy_id"] = "replacement"
        tampered["policy_hash"] = calculate_policy_hash(tampered)
        result = self.verify(
            [self.attest(0), self.attest(1)], tampered, original_hash
        )
        self.assertFalse(result.valid)
        self.assertIn("independently expected", " ".join(result.rejected_evidence))

    def test_revoked_member_does_not_count(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["witnesses"][2]["status"] = "revoked"
        policy["policy_hash"] = calculate_policy_hash(policy)
        self.assertTrue(verify_policy(policy, policy["policy_hash"]).valid)
        result = self.verify([self.attest(0), self.attest(2)], policy)
        self.assertFalse(result.valid)
        self.assertIn("revoked", " ".join(result.rejected_evidence))

    def test_duplicate_policy_member_is_rejected(self) -> None:
        with self.assertRaisesRegex(QuorumError, "duplicated"):
            create_policy(
                "bad-policy",
                2,
                [
                    ("Witness A", self.keys[0].public_key()),
                    ("Witness A", self.keys[1].public_key()),
                ],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
