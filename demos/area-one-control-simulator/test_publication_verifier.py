#!/usr/bin/env python3
"""Development-fixture and synthetic tests for publication_verifier."""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import publication_verifier as pv

HERE = Path(__file__).parent
HASH0 = "sha256:" + "0" * 64


def encoded(value: object) -> bytes:
    return (pv.canonical_json(value) + "\n").encode("utf-8")


def write_json(path: Path, value: dict[str, object]) -> bytes:
    data = encoded(value)
    path.write_bytes(data)
    return data


def deterministic_gzip(data: bytes) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=output,
                       compresslevel=9, mtime=0) as handle:
        handle.write(data)
    return output.getvalue()


def write_failure_state(root: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    marker: dict[str, object] = {
        "schema_version": "area-one-attempt-consumed/1.0",
        "dataset_kind": "development-fixture", "lock_hash": HASH0,
        "holdout_hash": HASH0, "attempt_id": "1" * 32,
    }
    failure: dict[str, object] = {
        "schema_version": "area-one-pair-results-failure/1.0",
        "dataset_kind": marker["dataset_kind"], "lock_hash": marker["lock_hash"],
        "holdout_hash": marker["holdout_hash"], "attempt_id": marker["attempt_id"],
        "stage": "completion-publication", "reason_code": "interrupted",
        "message": pv.FAILURE_MESSAGE,
    }
    write_json(root / pv.MARKER_NAME, marker)
    path = root / "failure.json"
    write_json(path, failure)
    return path, marker, failure


def make_lock(manifest_hash: str) -> dict[str, object]:
    parameters = [{"family_id": family, "theta_index": 0, "phi_index": 0}
                  for family in ("candidate",) + pv.CONTROL_IDS]
    source_files = [
        {"path": "publication_verifier.py", "sha256": HASH0},
        {"path": "test_publication_verifier.py", "sha256": HASH0},
    ]
    lock: dict[str, object] = {
        "schema_version": "area-one-pair-lock/1.0", "dataset_kind": "development-fixture",
        "protocol_hash": HASH0, "protocol_anchor_hash": HASH0, "git_head": "0" * 40,
        "git_diff_hash": HASH0, "source_files": source_files,
        "source_tree_hash": pv._sha256(pv.canonical_json(source_files).encode("utf-8")),
        "family_manifest_hash": manifest_hash, "holdout_hash": HASH0,
        "selection_code_hash": HASH0, "aggregation_code_hash": HASH0,
        "quantile_code_hash": HASH0,
        "grids": [{"s": s, "R": 6} for s in (2, 3, 4)], "coins": list(pv.COINS),
        "horizons": {"short": "ceil(sqrt(N))", "primary": "ceil(2*sqrt(N))", "long": "ceil(4*sqrt(N))"},
        "worker_count": 4, "shard_rows": 100000,
        "epsilon": pv.scalar_string(float(1e-12)),
        "thresholds": {
            "overall_median": pv.scalar_string(float(0.05)), "grid_median": "0",
            "overall_positive": "7/10", "grid_positive": "3/5",
            "grid_q10": pv.scalar_string(float(-0.02)), "control_q90": "0",
            "control_rank": 10, "control_advantage": pv.scalar_string(float(0.02)),
            "strongest_grid_wins": 7,
        },
        "selected_parameters": parameters,
        "runtime": {
            "image_digest": HASH0,
            "python_implementation": "CPython", "python_version": "3.13.7",
            "python_build": ["main", "Aug 15 2026 00:00:00"],
            "numpy_version": "2.4.2", "numpy_configuration": "synthetic-openblas",
            "threadpoolctl_version": "3.6.0", "platform": "linux-x86_64",
            "cpu_model": "synthetic x86_64", "cpu_flags": ["avx2", "sse2"],
            "thread_environment": dict(pv.THREAD_ENVIRONMENT),
            "thread_pools": [{
                "filepath": "/usr/lib/libopenblas.so", "internal_api": "openblas",
                "num_threads": 1, "prefix": "libopenblas", "user_api": "blas",
                "version": "0.3.30",
            }],
            "packages": [dict(item) for item in pv.EXPECTED_PACKAGES],
            "dependency_lock_hash": pv._sha256(
                (HERE / "requirements-research.lock").read_bytes()),
        },
    }
    lock["lock_hash"] = pv.document_hash(lock, "lock_hash")
    return lock


def row_for(lock: dict[str, object], ordinal: int, s: int, family: str,
            probability: float, *, coin: str = "uniform") -> dict[str, object]:
    horizon = pv._horizons(s, 6)[1]
    method = "baseline" if family == "baseline" else "candidate" if family == "candidate" else "control"
    theta = -1 if family == "baseline" else 0
    phi = -1 if family == "baseline" else 0
    row: dict[str, object] = {
        "schema_version": "area-one-pair-row/1.0", "ordinal": ordinal, "shard_id": 0,
        "s": s, "R": 6, "start_row": 0, "start_column": 0,
        "terminal_row": 0, "terminal_column": 1, "coin": coin, "horizon": horizon,
        "method_kind": method, "family_id": family, "theta_index": theta, "phi_index": phi,
        "theta_pi": "0" if family == "baseline" else pv.THETA_PI[0],
        "phi_pi": "0", "lock_hash": lock["lock_hash"],
        "family_manifest_hash": lock["family_manifest_hash"], "holdout_hash": lock["holdout_hash"],
        "probability": pv.scalar_string(float(probability)), "max_norm_drift": "0",
        "max_probability_bound_error": "0",
        "operations": {
            "oracle_calls": horizon, "coin_applications": horizon, "shifts": horizon,
            "pair_rotations": 0 if family == "baseline" else 4 * 5 * horizon,
            "final_measurements": 1, "hilbert_dimension": 6 * (s + 1) * 4,
        },
    }
    row["micro_case_key"] = pv.micro_case_key(row)
    row["row_key"] = pv.row_key(row)
    return row


def synthetic_rows(lock: dict[str, object], *, flat: bool = False) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    ordinal = 0
    for s in (2, 3, 4):
        values = {"baseline": 0.1, "candidate": 0.1 if flat else 0.2}
        values.update({family: 0.1 if flat else 0.11 for family in pv.CONTROL_IDS})
        if not flat:
            values["control-000"] = values["control-001"] = 0.15
        for family in ("baseline", "candidate") + pv.CONTROL_IDS:
            result.append(row_for(lock, ordinal, s, family, values[family]))
            ordinal += 1
    return result


def reconstruct(lock: dict[str, object], rows: list[dict[str, object]]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        with pv.Reconstructor(Path(directory) / "lifts.sqlite3", lock) as reconstructor:
            for row in rows:
                probability, invariant = pv._verify_row(row, lock, pv._verify_lock(lock), row["ordinal"])
                reconstructor.add(row, probability, invariant)
            return reconstructor.finish()


def make_publication(root: Path) -> tuple[Path, list[tuple[object, ...]]]:
    manifest_bytes = (HERE / "control-family-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    lock = make_lock(manifest["manifest_hash"])
    rows = synthetic_rows(lock)
    summary = reconstruct(lock, rows)
    write_json(root / "lock.json", lock)
    (root / "control-family-manifest.json").write_bytes(manifest_bytes)
    summary_bytes = write_json(root / "summary.json", summary)
    jsonl = b"".join(encoded(row) for row in rows)
    compressed = deterministic_gzip(jsonl)
    (root / "rows-000000.jsonl.gz").write_bytes(compressed)
    metadata = {
        "schema_version": "area-one-pair-shard/1.0", "shard_id": 0,
        "gzip_file": "rows-000000.jsonl.gz", "first_ordinal": 0,
        "expected_count": len(rows), "actual_count": len(rows),
        "decompressed_bytes": len(jsonl), "decompressed_hash": pv._sha256(jsonl),
        "compressed_bytes": len(compressed), "compressed_hash": pv._sha256(compressed),
        "first_row_key": rows[0]["row_key"], "last_row_key": rows[-1]["row_key"],
        "lock_hash": lock["lock_hash"],
    }
    write_json(root / "shard-000000.json", metadata)
    completion: dict[str, object] = {
        "schema_version": "area-one-pair-results-complete/1.0",
        "dataset_kind": "development-fixture",
        "schemas": {"lock": "area-one-pair-lock/1.0",
                    "family_manifest": "area-one-control-family-manifest/1.0",
                    "row": "area-one-pair-row/1.0", "shard": "area-one-pair-shard/1.0",
                    "summary": "area-one-pair-summary/1.0",
                    "completion": "area-one-pair-results-complete/1.0",
                    "failure": "area-one-pair-results-failure/1.0"},
        "lock_file": "lock.json", "lock_hash": lock["lock_hash"],
        "family_manifest_file": "control-family-manifest.json",
        "family_manifest_hash": manifest["manifest_hash"], "holdout_hash": HASH0,
        "summary_file": "summary.json", "summary_hash": pv._sha256(summary_bytes),
        "shards": [{"shard_id": 0, "metadata_file": "shard-000000.json",
                    "gzip_file": "rows-000000.jsonl.gz", "expected_count": len(rows),
                    "actual_count": len(rows), "decompressed_hash": pv._sha256(jsonl),
                    "compressed_hash": pv._sha256(compressed)}],
        "global_expected_count": len(rows), "global_actual_count": len(rows),
        "canonical_jsonl_hash": pv._sha256(jsonl),
    }
    completion["completion_hash"] = pv.document_hash(completion, "completion_hash")
    completion_path = root / "synthetic-completion.json"
    write_json(completion_path, completion)
    marker = {"schema_version": "area-one-attempt-consumed/1.0",
              "dataset_kind": "development-fixture", "lock_hash": lock["lock_hash"],
              "holdout_hash": HASH0, "attempt_id": "1" * 32}
    write_json(root / pv.MARKER_NAME, marker)
    expected = [pv._row_tuple(row) for row in rows]
    return completion_path, expected


class ScalarQuantileTests(unittest.TestCase):
    def test_scalar_canonical_and_nonfinite_rules(self) -> None:
        self.assertEqual(pv.parse_scalar("0", "x"), 0.0)
        for text in ("-0", "1.0", "01", "nan", "inf", "1e-12"):
            with self.assertRaises(pv.PublicationError, msg=text):
                pv.parse_scalar(text, "x")
        self.assertEqual(pv.parse_scalar(pv.scalar_string(float(1e-12)), "x"), float(1e-12))

    def test_frozen_quantile_orders_by_value_then_key(self) -> None:
        self.assertEqual(pv.frozen_quantile([(3.0, "c"), (1.0, "b"), (1.0, "a")], 1, 2), 1.0)
        self.assertEqual(pv.frozen_quantile([(0.0, "a"), (10.0, "b")], 1, 10), 1.0)
        with self.assertRaises(pv.PublicationError):
            pv.frozen_quantile([(1.0, "a"), (2.0, "a")], 1, 2)


class LockEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manifest = json.loads((HERE / "control-family-manifest.json").read_bytes())
        cls.manifest_hash = manifest["manifest_hash"]
        cls.schema = pv.load_schemas()["area-one-pair-lock/1.0"]

    def lock(self) -> dict[str, object]:
        return make_lock(self.manifest_hash)

    def refresh_source_tree(self, lock: dict[str, object]) -> None:
        lock["source_tree_hash"] = pv._sha256(
            pv.canonical_json(lock["source_files"]).encode("utf-8"))

    def assert_semantic_rejection(self, lock: dict[str, object], pattern: str) -> None:
        lock["lock_hash"] = pv.document_hash(lock, "lock_hash")
        with self.assertRaisesRegex(pv.PublicationError, pattern):
            pv._verify_lock(lock)

    def test_lock_schema_rejects_each_omitted_evidence_field(self) -> None:
        fields = [
            (None, "source_files"),
            ("runtime", "image_digest"), ("runtime", "python_implementation"),
            ("runtime", "python_version"), ("runtime", "python_build"),
            ("runtime", "numpy_version"), ("runtime", "numpy_configuration"),
            ("runtime", "threadpoolctl_version"), ("runtime", "platform"),
            ("runtime", "cpu_model"), ("runtime", "cpu_flags"),
            ("runtime", "thread_environment"), ("runtime", "thread_pools"),
            ("runtime", "packages"), ("runtime", "dependency_lock_hash"),
        ]
        for parent, field in fields:
            with self.subTest(field=field):
                lock = self.lock()
                if parent is None:
                    del lock[field]
                else:
                    del lock[parent][field]
                with self.assertRaisesRegex(pv.PublicationError, "missing fields"):
                    pv.validate_schema(lock, self.schema, "lock")

    def test_source_paths_reject_unsafe_unsorted_and_duplicate_values(self) -> None:
        unsafe = ("/absolute.py", "dir\\file.py", "dir//file.py", "./file.py",
                  "dir/../file.py", "C:/absolute.py")
        for path in unsafe:
            with self.subTest(path=path):
                lock = self.lock()
                lock["source_files"][0]["path"] = path
                self.refresh_source_tree(lock)
                self.assert_semantic_rejection(lock, "unsafe source path")
        lock = self.lock()
        lock["source_files"].reverse()
        self.refresh_source_tree(lock)
        self.assert_semantic_rejection(lock, "canonical path order")
        lock = self.lock()
        lock["source_files"][1] = copy.deepcopy(lock["source_files"][0])
        self.refresh_source_tree(lock)
        self.assert_semantic_rejection(lock, "duplicated")

    def test_source_tree_hash_must_bind_canonical_compact_source_array(self) -> None:
        lock = self.lock()
        lock["source_tree_hash"] = HASH0
        self.assert_semantic_rejection(lock, "source_tree_hash")

    def test_python_and_frozen_runtime_mismatches_are_rejected(self) -> None:
        mutations = (
            ("python_implementation", "PyPy"), ("python_version", "3.13.6"),
            ("python_build", ["one"]), ("numpy_version", "2.4.1"),
            ("threadpoolctl_version", "3.5.0"), ("platform", "windows-x86_64"),
            ("numpy_configuration", ""), ("cpu_model", ""),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                lock = self.lock()
                lock["runtime"][field] = value
                self.assert_semantic_rejection(lock, "runtime")
        lock = self.lock()
        lock["runtime"]["thread_environment"]["OMP_NUM_THREADS"] = "2"
        self.assert_semantic_rejection(lock, "thread environment")

    def test_flags_and_thread_pools_must_be_canonical_and_single_threaded(self) -> None:
        for flags in (["sse2", "avx2"], ["avx2", "avx2"], ["AVX2"]):
            with self.subTest(flags=flags):
                lock = self.lock()
                lock["runtime"]["cpu_flags"] = flags
                self.assert_semantic_rejection(lock, "CPU flags")
        lock = self.lock()
        first = copy.deepcopy(lock["runtime"]["thread_pools"][0])
        second = copy.deepcopy(first)
        first["internal_api"] = "a"
        second["internal_api"] = "z"
        lock["runtime"]["thread_pools"] = [second, first]
        self.assert_semantic_rejection(lock, "canonically sorted")
        lock = self.lock()
        lock["runtime"]["thread_pools"][0]["num_threads"] = 2
        self.assert_semantic_rejection(lock, "exactly one thread")

    def test_packages_and_dependency_lock_hash_are_exact(self) -> None:
        lock = self.lock()
        lock["runtime"]["packages"].reverse()
        self.assert_semantic_rejection(lock, "frozen wheel records")
        lock = self.lock()
        lock["runtime"]["packages"][0]["filename"] = "numpy-fake.whl"
        self.assert_semantic_rejection(lock, "frozen wheel records")
        lock = self.lock()
        lock["runtime"]["dependency_lock_hash"] = HASH0
        self.assert_semantic_rejection(lock, "requirements-research.lock")


class ReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manifest = json.loads((HERE / "control-family-manifest.json").read_bytes())
        cls.lock = make_lock(manifest["manifest_hash"])

    def test_rank_structured_tie_q90_and_operations(self) -> None:
        rows = synthetic_rows(self.lock)
        summary = reconstruct(self.lock, rows)
        self.assertEqual(summary["candidate_rank"], 1)
        self.assertEqual(summary["strongest_control_id"], "control-000")
        self.assertEqual(summary["control_quantile_90"],
                         pv.scalar_string(float(float(0.11) - float(0.1))))
        self.assertEqual(summary["operations"]["records"], len(rows))
        self.assertTrue(summary["checks"]["operation_consistency"])

    def test_conservative_rank_counts_epsilon_ties(self) -> None:
        rows = synthetic_rows(self.lock)
        for row in rows:
            if row["family_id"] == "control-002":
                row["probability"] = row["probability"] = pv.scalar_string(float(0.2 - 1e-12))
        summary = reconstruct(self.lock, rows)
        self.assertEqual(summary["candidate_rank"], 2)

    def test_fixed_failure_order_and_outcome(self) -> None:
        summary = reconstruct(self.lock, synthetic_rows(self.lock, flat=True))
        self.assertEqual(summary["verdict"]["outcome"], "outcome-0")
        self.assertEqual(summary["failure_reasons"], [
            "overall-median", "grid-median", "overall-positive", "grid-positive",
            "control-quantile", "control-rank", "control-advantage", "strongest-grid-wins"])

    def test_exact_group_membership_and_primary_only(self) -> None:
        rows = synthetic_rows(self.lock)
        with tempfile.TemporaryDirectory() as directory:
            reconstructor = pv.Reconstructor(Path(directory) / "x.sqlite3", self.lock)
            for row in rows[:-1]:
                reconstructor.add(row, pv.parse_scalar(row["probability"], "p"), True)
            with self.assertRaisesRegex(pv.PublicationError, "group membership"):
                reconstructor.finish()
            reconstructor.close()

    def test_row_operation_and_invariant_rejection(self) -> None:
        row = synthetic_rows(self.lock)[0]
        row["operations"]["oracle_calls"] += 1
        with self.assertRaisesRegex(pv.PublicationError, "operation counts"):
            pv._verify_row(row, self.lock, pv._verify_lock(self.lock), 0)
        row = synthetic_rows(self.lock)[0]
        row["max_norm_drift"] = pv.scalar_string(float(2e-12))
        with self.assertRaisesRegex(pv.PublicationError, "invariant"):
            pv._verify_row(row, self.lock, pv._verify_lock(self.lock), 0)


class GzipAndJsonTests(unittest.TestCase):
    def verify_bytes(self, data: bytes) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.gz"
            path.write_bytes(data)
            lines: list[bytes] = []
            result = pv._verify_gzip(path, lines.append)
            result["lines"] = lines
            return result

    def test_valid_deterministic_gzip(self) -> None:
        payload = b"".join(f'{{"a":{index}}}\n'.encode() for index in range(20000))
        data = deterministic_gzip(payload)
        result = self.verify_bytes(data)
        self.assertEqual(len(result["lines"]), 20000)
        self.assertEqual(result["lines"][0], b'{"a":0}')

    def test_header_truncation_concatenation_trailing_and_crc(self) -> None:
        valid = deterministic_gzip(b'{"a":1}\n')
        cases = [b"x" + valid[1:], valid[:-3], valid + valid, valid + b"x",
                 valid[:-8] + bytes([valid[-8] ^ 1]) + valid[-7:]]
        for case in cases:
            with self.subTest(length=len(case)):
                with self.assertRaises(pv.PublicationError):
                    self.verify_bytes(case)

    def test_corrupt_raw_deflate_raises_publication_error(self) -> None:
        valid = deterministic_gzip(b'{"a":1}\n')
        corrupt = valid[:10] + b"\x06" + valid[-8:]
        with self.assertRaises(pv.PublicationError):
            self.verify_bytes(corrupt)

    def test_symlinked_gzip_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.gz"
            target.write_bytes(deterministic_gzip(b'{"a":1}\n'))
            path = root / "rows.gz"
            try:
                path.symlink_to(target)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with self.assertRaises(pv.PublicationError):
                pv._verify_gzip(path, lambda _line: None)

    def test_jsonl_crlf_missing_lf_duplicate_and_noncanonical(self) -> None:
        bad = [b'{"a":1}\r\n', b'{"a":1}', b'{"a":1,"a":2}\n', b'{"b":1,"a":2}\n']
        for payload in bad:
            with self.subTest(payload=payload):
                data = deterministic_gzip(payload)
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "rows.gz"; path.write_bytes(data)
                    def canonical(line: bytes) -> None:
                        value = pv.strict_json(line, "row")
                        if line != pv.canonical_json(value).encode():
                            raise pv.PublicationError("noncanonical")
                    with self.assertRaises(pv.PublicationError):
                        pv._verify_gzip(path, canonical)

    def test_strict_json_duplicate_unknown_and_utf8(self) -> None:
        with self.assertRaises(pv.PublicationError):
            pv.strict_json(b'{"a":1,"a":2}', "x")
        with self.assertRaises(pv.PublicationError):
            pv.strict_json(b'"\xff"', "x")
        with self.assertRaisesRegex(pv.PublicationError, "unknown fields"):
            pv.validate_schema({"a": 1}, {"type": "object", "additionalProperties": False,
                                          "properties": {}}, "x")


class EndToEndTests(unittest.TestCase):
    def test_failure_verification_uses_marker_without_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failure_path, _, _ = write_failure_state(root)
            self.assertFalse((root / "lock.json").exists())
            self.assertTrue(pv.verify_failure_document(root, failure_path.name).valid)

    def test_failure_rejects_mismatch_unsafe_staging_and_completion(self) -> None:
        for case in ("mismatch", "staging-file", "staging-nonempty", "completion"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                failure_path, _, failure = write_failure_state(root)
                if case == "mismatch":
                    failure["attempt_id"] = "2" * 32
                    write_json(failure_path, failure)
                elif case == "staging-file":
                    (root / pv.STAGING_NAME).write_text("unsafe", encoding="utf-8")
                elif case == "staging-nonempty":
                    staging = root / pv.STAGING_NAME
                    staging.mkdir()
                    (staging / "residual").write_text("unsafe", encoding="utf-8")
                else:
                    write_json(root / "completion.json", {
                        "schema_version": "area-one-pair-results-complete/1.0"})
                self.assertFalse(pv.verify_failure_document(root, failure_path.name).valid)

    def test_failure_rejects_malformed_marker_and_free_form_content(self) -> None:
        for case in ("marker", "failure"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                failure_path, marker, failure = write_failure_state(root)
                if case == "marker":
                    marker["attempt_id"] = "not-an-attempt"
                    write_json(root / pv.MARKER_NAME, marker)
                else:
                    failure["message"] = "candidate outcome and score were unavailable"
                    write_json(failure_path, failure)
                self.assertFalse(pv.verify_failure_document(root, failure_path.name).valid)

    def test_completion_callback_staged_final_and_missing_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            staging = base / pv.STAGING_NAME
            staging.mkdir()
            staged_completion, staged_expected = make_publication(staging)
            (staging / pv.MARKER_NAME).unlink()
            with patch.object(pv, "expected_rows", return_value=iter(staged_expected)):
                self.assertTrue(pv.completion_verification_callback(staged_completion))
            plan = type("Plan", (), {"completion_name": staged_completion.name})()
            with patch.object(pv, "expected_rows", return_value=iter(staged_expected)):
                self.assertTrue(pv.staged_verification_callback(staging, plan))

            final = base / "final"
            final.mkdir()
            final_completion, final_expected = make_publication(final)
            with patch.object(pv, "expected_rows", return_value=iter(final_expected)):
                self.assertTrue(pv.completion_verification_callback(final_completion))
            (final / pv.MARKER_NAME).unlink()
            with patch.object(pv, "expected_rows", return_value=iter(final_expected)):
                self.assertFalse(pv.completion_verification_callback(final_completion))

    def test_symlinked_completion_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            completion, expected = make_publication(root)
            target = root / "completion-target.json"
            completion.rename(target)
            try:
                completion.symlink_to(target)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with patch.object(pv, "expected_rows", return_value=iter(expected)):
                self.assertFalse(pv.verify_publication(root, completion.name).valid)

    def test_tiny_synthetic_publication_and_staged_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); completion, expected = make_publication(root)
            with patch.object(pv, "expected_rows", return_value=iter(expected)):
                result = pv.verify_publication(root, completion.name)
            self.assertTrue(result.valid, result.errors)
            self.assertEqual(result.rows, 306)
            (root / pv.MARKER_NAME).unlink()
            with patch.object(pv, "expected_rows", return_value=iter(expected)):
                self.assertFalse(pv.verify_publication(root, completion.name).valid)
            with patch.object(pv, "expected_rows", return_value=iter(expected)):
                self.assertTrue(pv.verify_staged_publication(root, completion.name).valid)

    def test_completion_requirement_and_path_confinement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(pv.verify_publication(root, "missing.json").valid)
            outside = root.parent / "outside.json"; outside.write_text("{}\n", encoding="utf-8")
            try:
                self.assertFalse(pv.verify_publication(root, outside).valid)
            finally:
                outside.unlink(missing_ok=True)

    def test_marker_staging_and_failure_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); completion, expected = make_publication(root)
            staging = root / pv.STAGING_NAME; staging.mkdir()
            with patch.object(pv, "expected_rows", return_value=iter(expected)):
                self.assertTrue(pv.verify_publication(root, completion.name).valid)
            (staging / "residual").write_text("x")
            self.assertFalse(pv.verify_publication(root, completion.name).valid)
            (staging / "residual").unlink(); staging.rmdir()
            lock = json.loads((root / "lock.json").read_bytes())
            failure = {"schema_version": "area-one-pair-results-failure/1.0",
                       "dataset_kind": "development-fixture", "lock_hash": lock["lock_hash"],
                       "holdout_hash": HASH0, "attempt_id": "1" * 32,
                       "stage": "completion-publication", "reason_code": "interrupted",
                       "message": pv.FAILURE_MESSAGE}
            write_json(root / "failure.json", failure)
            self.assertFalse(pv.verify_publication(root, completion.name).valid)
            self.assertFalse(pv.verify_failure_document(root, "failure.json").valid)
            completion.unlink()
            self.assertTrue(pv.verify_failure_document(root, "failure.json").valid)

    def test_row_order_count_hash_and_binding_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); completion_path, expected = make_publication(root)
            completion = json.loads(completion_path.read_bytes())
            completion["holdout_hash"] = "sha256:" + "f" * 64
            completion["completion_hash"] = pv.document_hash(completion, "completion_hash")
            write_json(completion_path, completion)
            with patch.object(pv, "expected_rows", return_value=iter(expected)):
                result = pv.verify_publication(root, completion_path.name)
            self.assertFalse(result.valid)
            self.assertTrue(any("binding" in error for error in result.errors), result.errors)

    def test_expected_row_order_and_count_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); completion_path, expected = make_publication(root)
            wrong_order = list(expected)
            wrong_order[0], wrong_order[1] = wrong_order[1], wrong_order[0]
            with patch.object(pv, "expected_rows", return_value=iter(wrong_order)):
                order_result = pv.verify_publication(root, completion_path.name)
            self.assertFalse(order_result.valid)
            self.assertTrue(any("canonical order" in error for error in order_result.errors))
            with patch.object(pv, "expected_rows", return_value=iter(expected[:-1])):
                count_result = pv.verify_publication(root, completion_path.name)
            self.assertFalse(count_result.valid)
            self.assertTrue(any("extra row" in error for error in count_result.errors))

    def test_metadata_hash_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); completion_path, expected = make_publication(root)
            metadata_path = root / "shard-000000.json"
            metadata = json.loads(metadata_path.read_bytes())
            metadata["compressed_hash"] = HASH0
            write_json(metadata_path, metadata)
            with patch.object(pv, "expected_rows", return_value=iter(expected)):
                result = pv.verify_publication(root, completion_path.name)
            self.assertFalse(result.valid)
            self.assertTrue(any("metadata" in error for error in result.errors), result.errors)

    def test_cli_nonzero_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(HERE / "publication_verifier.py"), directory, "missing.json"],
                capture_output=True, text=True, check=False)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('"valid":false', completed.stderr)


if __name__ == "__main__":
    unittest.main()
