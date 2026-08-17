from __future__ import annotations

import hashlib
import inspect
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import independent_protocol_anchor as independent
import protocol_approval_anchor as producer


class ProtocolApprovalAnchorTests(unittest.TestCase):
    def test_normalization_contract_and_idempotence(self) -> None:
        source = b"\xef\xbb\xbf# Caf\xc3\xa9  \r\n\r\ntext\r\n\r\n"
        expected = "# Café  \n\ntext\n".encode("utf-8")
        actual = producer.normalize_protocol_bytes(source)
        self.assertEqual(actual, expected)
        self.assertEqual(producer.normalize_protocol_bytes(actual), actual)

    def test_unicode_is_nfc_and_wording_is_preserved(self) -> None:
        source = "Cafe\u0301\rline with spaces  \r".encode("utf-8")
        self.assertEqual(
            producer.normalize_protocol_bytes(source),
            "Café\nline with spaces  \n".encode("utf-8"),
        )

    def test_invalid_utf8_controls_empty_and_bom_edges_fail(self) -> None:
        values = (
            b"", b"\xff", b"valid\x00text", b"\xef\xbb\xbf",
            b"\xef\xbb\xbf\xef\xbb\xbftext",
        )
        for value in values:
            with self.assertRaises(producer.ProtocolAnchorError):
                producer.normalize_protocol_bytes(value)
            with self.assertRaises(independent.IndependentAnchorError):
                independent._independent_normalize(value)

    def test_size_boundary_is_exact_and_shared(self) -> None:
        accepted = b"a" * (producer.MAX_PROTOCOL_BYTES - 1)
        self.assertEqual(len(producer.normalize_protocol_bytes(accepted)),
                         producer.MAX_PROTOCOL_BYTES)
        self.assertEqual(producer.normalize_protocol_bytes(accepted),
                         independent._independent_normalize(accepted))
        rejected = accepted + b"b"
        with self.assertRaises(producer.ProtocolAnchorError):
            producer.normalize_protocol_bytes(rejected)
        with self.assertRaises(independent.IndependentAnchorError):
            independent._independent_normalize(rejected)

    def test_anchor_is_exact_standard_sha256_sidecar(self) -> None:
        protocol = b"protocol\n"
        digest = hashlib.sha256(protocol).hexdigest()
        expected = f"{digest}  {producer.PROTOCOL_BASENAME}\n".encode("ascii")
        self.assertEqual(producer.canonical_anchor_bytes(protocol), expected)
        self.assertEqual(producer.parse_anchor_bytes(expected),
                         (digest, producer.PROTOCOL_BASENAME))

    def test_write_and_both_verifiers_agree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            protocol = Path(directory) / producer.PROTOCOL_BASENAME
            anchor = protocol.with_name(protocol.name + ".sha256")
            protocol.write_bytes(b"# Protocol\r\n\r\nExact words.\r\n")
            digest = producer.write_candidate(protocol, anchor)
            self.assertEqual(protocol.read_bytes(), b"# Protocol\n\nExact words.\n")
            self.assertEqual(producer.verify_candidate(protocol, anchor), digest)
            self.assertEqual(independent.verify(protocol, anchor), digest)
    def test_tampering_and_noncanonical_files_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            protocol = Path(directory) / producer.PROTOCOL_BASENAME
            anchor = protocol.with_name(protocol.name + ".sha256")
            protocol.write_bytes(b"fixed\n")
            producer.write_candidate(protocol, anchor)
            original_anchor = anchor.read_bytes()
            protocol.write_bytes(b"tampered\n")
            with self.assertRaises(producer.ProtocolAnchorError):
                producer.verify_candidate(protocol, anchor)
            with self.assertRaises(independent.IndependentAnchorError):
                independent.verify(protocol, anchor)
            protocol.write_bytes(b"fixed\n")
            for malformed in (
                original_anchor.upper(),
                original_anchor.replace(b"  ", b" "),
                original_anchor.rstrip(b"\n"),
                b"0" * 64 + b"  wrong.md\n",
            ):
                anchor.write_bytes(malformed)
                with self.assertRaises(producer.ProtocolAnchorError):
                    producer.verify_candidate(protocol, anchor)
                with self.assertRaises(independent.IndependentAnchorError):
                    independent.verify(protocol, anchor)

    def test_noncanonical_protocol_is_rejected_before_hash_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            protocol = Path(directory) / producer.PROTOCOL_BASENAME
            anchor = protocol.with_name(protocol.name + ".sha256")
            raw = b"line\r\n"
            protocol.write_bytes(raw)
            anchor.write_bytes(producer.canonical_anchor_bytes(raw, protocol.name))
            with self.assertRaises(producer.ProtocolAnchorError):
                producer.verify_candidate(protocol, anchor)
            with self.assertRaises(independent.IndependentAnchorError):
                independent.verify(protocol, anchor)

    def test_write_rejects_alias_non_sibling_and_nonregular_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            protocol = Path(directory) / producer.PROTOCOL_BASENAME
            protocol.write_bytes(b"protocol\n")
            sibling = protocol.with_name(protocol.name + ".sha256")
            other = protocol.with_name("other.sha256")
            for anchor in (protocol, other):
                with self.assertRaises(producer.ProtocolAnchorError):
                    producer.write_candidate(protocol, anchor)
                with self.assertRaises(independent.IndependentAnchorError):
                    independent.verify(protocol, anchor)
            sibling.mkdir()
            with self.assertRaises(producer.ProtocolAnchorError):
                producer.write_candidate(protocol, sibling)

    def test_symlink_inputs_fail_closed_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_protocol = root / producer.PROTOCOL_BASENAME
            real_protocol.write_bytes(b"protocol\n")
            protocol = root / "linked.md"
            try:
                protocol.symlink_to(real_protocol)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            anchor = protocol.with_name(protocol.name + ".sha256")
            anchor.write_bytes(producer.canonical_anchor_bytes(
                real_protocol.read_bytes(), protocol.name
            ))
            with self.assertRaises(producer.ProtocolAnchorError):
                producer.verify_candidate(protocol, anchor)
            with self.assertRaises(independent.IndependentAnchorError):
                independent.verify(protocol, anchor)

    def test_fault_boundaries_leave_no_false_candidate(self) -> None:
        fault_events = (
            "before_protocol_replace", "after_protocol_replace",
            "before_anchor_replace", "after_anchor_replace",
        )
        for fault_event in fault_events:
            with self.subTest(fault_event=fault_event), tempfile.TemporaryDirectory() as directory:
                protocol = Path(directory) / producer.PROTOCOL_BASENAME
                anchor = protocol.with_name(protocol.name + ".sha256")
                original = b"protocol\r\n"
                protocol.write_bytes(original)
                anchor.write_bytes(producer.canonical_anchor_bytes(original, protocol.name))

                def fail(name: str) -> None:
                    if name == fault_event:
                        raise RuntimeError(name)

                with self.assertRaises(RuntimeError):
                    producer.write_candidate(protocol, anchor, fail)
                if fault_event == "after_anchor_replace":
                    producer.verify_candidate(protocol, anchor)
                    independent.verify(protocol, anchor)
                else:
                    with self.assertRaises(producer.ProtocolAnchorError):
                        producer.verify_candidate(protocol, anchor)
                    with self.assertRaises(independent.IndependentAnchorError):
                        independent.verify(protocol, anchor)

    def test_independent_verifier_imports_no_producer_module(self) -> None:
        source = inspect.getsource(independent)
        self.assertNotIn("import protocol_approval_anchor", source)
        self.assertNotIn("from protocol_approval_anchor", source)

    def test_checked_protocol_and_anchor_are_exactly_verified(self) -> None:
        expected = producer.verify_candidate(
            producer.DEFAULT_PROTOCOL_PATH, producer.DEFAULT_ANCHOR_PATH
        )
        self.assertEqual(
            independent.verify(producer.DEFAULT_PROTOCOL_PATH,
                               producer.DEFAULT_ANCHOR_PATH),
            expected,
        )
        self.assertEqual(
            producer.DEFAULT_ANCHOR_PATH.read_bytes(),
            producer.canonical_anchor_bytes(
                producer.DEFAULT_PROTOCOL_PATH.read_bytes(),
                producer.DEFAULT_PROTOCOL_PATH.name,
            ),
        )

    def test_both_clis_never_claim_freeze_approval(self) -> None:
        producer_output = io.StringIO()
        with redirect_stdout(producer_output):
            producer_status = producer.main([])
        self.assertEqual(producer_status, 0)
        self.assertIn("freeze_status=AWAITING_EXPLICIT_APPROVAL",
                      producer_output.getvalue())
        self.assertIn("independent_verification=REQUIRED",
                      producer_output.getvalue())
        independent_output = io.StringIO()
        with redirect_stdout(independent_output):
            independent_status = independent.main([])
        self.assertEqual(independent_status, 0)
        self.assertIn("freeze_status=AWAITING_EXPLICIT_APPROVAL",
                      independent_output.getvalue())
        self.assertIn("independent_verification=PASS",
                      independent_output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)