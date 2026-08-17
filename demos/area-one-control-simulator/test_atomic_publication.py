from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import atomic_publication as ap

LOCK = "sha256:" + "1" * 64
HOLDOUT = "sha256:" + "2" * 64
ATTEMPT = "a" * 32
NAMES = ("rows.bin", "summary.json", "complete.json")
COMPLETE = b'{"kind":"complete"}\n'


def injected():
    return {
        "test_directory_sync": lambda path: None,
        "test_device_resolver": lambda path: 7,
    }


def valid_lock(*args):
    return True


def marker_bytes(**updates):
    document = {
        "schema_version": ap.ATTEMPT_SCHEMA,
        "dataset_kind": "development-fixture",
        "lock_hash": LOCK,
        "holdout_hash": HOLDOUT,
        "attempt_id": ATTEMPT,
    }
    document.update(updates)
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


class AtomicPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def args(self, **updates):
        values = dict(
            root=self.root,
            expected_lock_hash=LOCK,
            expected_holdout_hash=HOLDOUT,
            dataset_kind="development-fixture",
            completion_filename="complete.json",
            managed_artifact_names=NAMES,
            lock_verifier=valid_lock,
            producer=self.producer,
            staging_verifier=lambda path, plan: True,
            completion_validator=lambda path: path.read_bytes() == COMPLETE,
            attempt_id_factory=lambda: ATTEMPT,
            **injected(),
        )
        values.update(updates)
        return values

    @staticmethod
    def producer(writer):
        writer.write("complete.json", COMPLETE)
        writer.write("summary.json", b"opaque-summary")
        writer.write("rows.bin", b"opaque-rows")
        return ap.PublicationPlan(("rows.bin", "summary.json"), "complete.json")

    def recover(self, **updates):
        values = dict(
            root=self.root,
            expected_lock_hash=LOCK,
            expected_holdout_hash=HOLDOUT,
            dataset_kind="development-fixture",
            expected_attempt_id=ATTEMPT,
            completion_filename="complete.json",
            managed_artifact_names=NAMES,
            completion_validator=lambda path: path.read_bytes() == COMPLETE,
            **injected(),
        )
        values.update(updates)
        return ap.startup_recover(**values)

    def test_success_exact_states_order_and_completion_last(self):
        events = []
        result = ap.execute(**self.args(hook=events.append))
        states = [
            event.removeprefix("after:transition:")
            for event in events
            if event.startswith("after:transition:")
        ]
        self.assertEqual(states, [state.value for state in ap.PublicationState])
        renames = [e for e in events if e.startswith("before:rename:")]
        self.assertEqual(
            renames,
            ["before:rename:rows.bin", "before:rename:summary.json", "before:rename:complete.json"],
        )
        self.assertLess(
            events.index("after:transition:ARTIFACTS_COMMITTED"),
            events.index("before:completion-publication:complete.json"),
        )
        self.assertEqual(result.state, ap.PublicationState.COMPLETION_PUBLISHED)
        self.assertEqual((self.root / "complete.json").read_bytes(), COMPLETE)

    def test_marker_is_canonical_bound_and_durable_before_producer(self):
        events = []

        def producer(writer):
            marker = (self.root / ap.MARKER_NAME).read_bytes()
            document = json.loads(marker)
            self.assertEqual(marker, (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode())
            self.assertEqual(document["lock_hash"], LOCK)
            self.assertEqual(document["holdout_hash"], HOLDOUT)
            self.assertEqual(document["attempt_id"], ATTEMPT)
            self.assertIn("after:file-sync:attempt-consumed.json", events)
            self.assertIn("after:directory-sync:root", events)
            return self.producer(writer)

        ap.execute(**self.args(producer=producer, hook=events.append))

    def test_default_windows_fails_closed(self):
        if os.name == "posix":
            self.skipTest("Windows-only fail-closed assertion")
        values = self.args()
        values.pop("test_directory_sync")
        values.pop("test_device_resolver")
        with self.assertRaises(ap.DurabilityUnavailableError):
            ap.execute(**values)
        self.assertFalse((self.root / ap.MARKER_NAME).exists())

    def test_real_posix_directory_fsync_integration(self):
        if os.name != "posix":
            self.skipTest("requires POSIX directory fsync")
        values = self.args()
        values.pop("test_directory_sync")
        values.pop("test_device_resolver")
        result = ap.execute(**values)
        self.assertEqual(result.state, ap.PublicationState.COMPLETION_PUBLISHED)

    def test_root_and_component_symlinks_rejected(self):
        target = self.root / "target"
        target.mkdir()
        (target / "child").mkdir()
        link = self.root / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ap.UnsafePathError):
            ap.execute(**self.args(root=link))
        child = link / "child"
        with self.assertRaises(ap.UnsafePathError):
            ap.execute(**self.args(root=child))

    def test_cross_device_staging_rejected(self):
        def devices(path):
            return 8 if Path(path).name == ap.STAGING_NAME else 7

        with self.assertRaises(ap.CrossDeviceError):
            ap.execute(**self.args(test_device_resolver=devices))
        self.assertTrue((self.root / ap.MARKER_NAME).exists())

    def test_invalid_hash_attempt_id_dataset_and_filenames(self):
        cases = [
            {"expected_lock_hash": "sha256:" + "A" * 64},
            {"expected_holdout_hash": "2" * 64},
            {"dataset_kind": "production"},
            {"attempt_id_factory": lambda: "A" * 32},
            {"completion_filename": "../complete.json"},
            {"managed_artifact_names": ("rows.bin", "rows.bin", "complete.json")},
        ]
        for update in cases:
            with self.subTest(update=update), self.assertRaises(ap.ConfigurationError):
                ap.execute(**self.args(**update))
            self.assertFalse((self.root / ap.MARKER_NAME).exists())

    def test_writer_rejects_duplicate_unmanaged_and_nonbytes(self):
        producers = [
            lambda w: (w.write("rows.bin", b"x"), w.write("rows.bin", b"y")),
            lambda w: w.write("other.bin", b"x"),
            lambda w: w.write("rows.bin", bytearray(b"x")),
        ]
        for producer in producers:
            with self.subTest(producer=producer):
                with tempfile.TemporaryDirectory() as directory:
                    self.root = Path(directory)
                    with self.assertRaises(ap.StagingError):
                        ap.execute(**self.args(producer=producer))
                    self.assertTrue((self.root / ap.MARKER_NAME).exists())

    def test_two_concurrent_consumers_exactly_one_wins(self):
        barrier = threading.Barrier(2)
        winners = []
        failures = []

        local = threading.local()

        def lock(*args):
            if not getattr(local, "initial_verified", False):
                local.initial_verified = True
                barrier.wait(timeout=5)
            return True

        def run():
            try:
                winners.append(ap.execute(**self.args(lock_verifier=lock)))
            except Exception as exc:
                failures.append(exc)

        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], ap.AttemptConsumedError)

    def test_existing_valid_invalid_and_truncated_markers_refuse(self):
        valid = (
            json.dumps(
                {
                    "schema_version": ap.ATTEMPT_SCHEMA,
                    "dataset_kind": "development-fixture",
                    "lock_hash": LOCK,
                    "holdout_hash": HOLDOUT,
                    "attempt_id": ATTEMPT,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        for marker in (valid, b"not-json\n", b'{"torn":'):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                (self.root / ap.MARKER_NAME).write_bytes(marker)
                calls = []
                with self.assertRaises(ap.AttemptConsumedError):
                    ap.execute(**self.args(lock_verifier=lambda *args: calls.append(args)))
                self.assertEqual(calls, [])

    def test_pre_marker_fault_permits_retry(self):
        def fault(event):
            if event == "before:exclusive-create:attempt-consumed.json":
                raise RuntimeError("injected")

        with self.assertRaises(RuntimeError):
            ap.execute(**self.args(hook=fault))
        self.assertEqual(self.recover().classification, ap.StartupClassification.FRESH)
        self.assertEqual(ap.execute(**self.args()).state, ap.PublicationState.COMPLETION_PUBLISHED)

    def test_fault_matrix_every_success_event(self):
        successful_events = []
        ap.execute(**self.args(hook=successful_events.append))
        required = (
            "transition:",
            "verification:",
            "exclusive-create:",
            "write:",
            "file-sync:",
            "directory-sync:",
            "staging-create:",
            "rename:",
            "completion-publication:",
        )
        for boundary in required:
            self.assertTrue(any(boundary in event for event in successful_events), boundary)

        for fault_index, fault_event in enumerate(successful_events):
            with self.subTest(index=fault_index, event=fault_event), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                seen = 0

                def fault(event):
                    nonlocal seen
                    current = seen
                    seen += 1
                    if current == fault_index:
                        raise RuntimeError("fault")

                with self.assertRaises(RuntimeError):
                    ap.execute(**self.args(hook=fault))
                marker = self.root / ap.MARKER_NAME
                completion = self.root / "complete.json"
                classification = self.recover().classification
                if not marker.exists():
                    self.assertEqual(classification, ap.StartupClassification.FRESH)
                elif completion.exists():
                    self.assertEqual(classification, ap.StartupClassification.COMPLETED)
                else:
                    self.assertEqual(classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
                    with self.assertRaises(ap.AttemptConsumedError):
                        ap.execute(**self.args())

    def test_recovery_incomplete_invokes_zero_callbacks_and_cleans_by_name(self):
        (self.root / ap.MARKER_NAME).write_bytes(b"truncated")
        staging = self.root / ap.STAGING_NAME
        staging.mkdir()
        (staging / "opaque-secret.bin").write_bytes(b"do-not-read")
        (self.root / "rows.bin").write_bytes(b"partial")
        (self.root / "summary.json").write_bytes(b"partial")
        unrelated = self.root / "unmanaged.keep"
        unrelated.write_bytes(b"keep")
        callbacks = []
        result = self.recover(completion_validator=lambda path: callbacks.append(path))
        self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
        self.assertEqual(callbacks, [])
        self.assertFalse(staging.exists())
        self.assertFalse((self.root / "rows.bin").exists())
        self.assertFalse((self.root / "summary.json").exists())
        self.assertEqual(unrelated.read_bytes(), b"keep")
        self.assertTrue((self.root / ap.MARKER_NAME).exists())

    def test_recovery_valid_completion_accepted_invalid_and_missing_rejected(self):
        (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
        (self.root / "complete.json").write_bytes(COMPLETE)
        self.assertEqual(self.recover().classification, ap.StartupClassification.COMPLETED)
        (self.root / "complete.json").write_bytes(b"invalid")
        self.assertEqual(
            self.recover().classification, ap.StartupClassification.CONSUMED_INCOMPLETE
        )
        self.assertFalse((self.root / "complete.json").exists())
        self.assertEqual(
            self.recover().classification, ap.StartupClassification.CONSUMED_INCOMPLETE
        )

    def test_same_root_cannot_reuse_after_success(self):
        ap.execute(**self.args())
        lock_calls = []
        with self.assertRaises(ap.AttemptConsumedError):
            ap.execute(**self.args(lock_verifier=lambda *args: lock_calls.append(args)))
        self.assertEqual(lock_calls, [])

    def test_failure_document_closed_safe_exact_and_recovery_idempotent(self):
        marker = {
            "schema_version": ap.ATTEMPT_SCHEMA,
            "dataset_kind": "development-fixture",
            "lock_hash": LOCK,
            "holdout_hash": HOLDOUT,
            "attempt_id": ATTEMPT,
        }
        (self.root / ap.MARKER_NAME).write_bytes(
            (json.dumps(marker, sort_keys=True, separators=(",", ":")) + "\n").encode()
        )
        result = self.recover(
            managed_artifact_names=NAMES + ("failure.json",),
            failure_filename="failure.json",
        )
        self.assertTrue(result.failure_metadata_published)
        failure_bytes = (self.root / "failure.json").read_bytes()
        failure = json.loads(failure_bytes)
        self.assertEqual(
            set(failure),
            {
                "schema_version",
                "dataset_kind",
                "lock_hash",
                "holdout_hash",
                "attempt_id",
                "stage",
                "reason_code",
                "message",
            },
        )
        self.assertEqual(failure["schema_version"], "area-one-pair-results-failure/1.0")
        self.assertEqual(failure["stage"], "completion-publication")
        self.assertEqual(failure["reason_code"], "interrupted")
        self.assertEqual(failure["message"], "Publication attempt was consumed but did not complete.")
        forbidden = re.compile(r"probability|lift|rank|path", re.IGNORECASE)
        self.assertIsNone(forbidden.search(json.dumps(failure)))
        again = self.recover(
            managed_artifact_names=NAMES + ("failure.json",),
            failure_filename="failure.json",
        )
        self.assertFalse(again.failure_metadata_published)
        self.assertEqual((self.root / "failure.json").read_bytes(), failure_bytes)

    def test_malformed_or_mismatched_marker_gets_no_failure_metadata(self):
        for marker in (b"torn", b"{}\n"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                (self.root / ap.MARKER_NAME).write_bytes(marker)
                result = self.recover(
                    managed_artifact_names=NAMES + ("failure.json",),
                    failure_filename="failure.json",
                )
                self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
                self.assertFalse((self.root / "failure.json").exists())

    def test_plan_is_immutable_and_must_match_exact_names(self):
        plan = ap.PublicationPlan(("rows.bin",), "complete.json")
        with self.assertRaises((AttributeError, TypeError)):
            plan.completion_name = "other.json"

        def bad_plan(writer):
            self.producer(writer)
            return ap.PublicationPlan(("summary.json", "rows.bin"), "other.json")

        with self.assertRaises(ap.PlanError):
            ap.execute(**self.args(producer=bad_plan))

    def test_staging_and_completion_verification_precede_final_lock(self):
        calls = []

        def lock(*args):
            calls.append("lock")
            return True

        def staging(path, plan):
            calls.append("staging")
            return True

        def completion(path):
            calls.append("completion")
            return path.read_bytes() == COMPLETE

        ap.execute(
            **self.args(
                lock_verifier=lock,
                staging_verifier=staging,
                completion_validator=completion,
            )
        )
        self.assertEqual(calls, ["lock", "staging", "completion", "lock"])

    def test_verification_false_fails_closed_without_commit(self):
        with self.assertRaises(ap.VerificationError):
            ap.execute(**self.args(staging_verifier=lambda path, plan: False))
        self.assertTrue((self.root / ap.MARKER_NAME).exists())
        self.assertFalse((self.root / "rows.bin").exists())

    def test_verification_callback_exceptions_fail_closed(self):
        for verification in ("lock-initial", "lock-final", "staging", "completion-staged"):
            with self.subTest(verification=verification), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)

                def raises(*args):
                    raise RuntimeError("verification failed")

                updates = {}
                if verification == "lock-initial":
                    updates["lock_verifier"] = raises
                elif verification == "lock-final":
                    calls = 0

                    def final_lock(*args):
                        nonlocal calls
                        calls += 1
                        if calls == 2:
                            raise RuntimeError("verification failed")
                        return True

                    updates["lock_verifier"] = final_lock
                elif verification == "staging":
                    updates["staging_verifier"] = raises
                else:
                    updates["completion_validator"] = raises
                with self.assertRaises(RuntimeError):
                    ap.execute(**self.args(**updates))
                self.assertFalse((self.root / "complete.json").exists())

    def test_exact_true_required_for_all_execute_verifications(self):
        for rejected in (None, 1, "truthy"):
            for verification in ("lock-initial", "lock-final", "staging", "completion-staged"):
                with self.subTest(value=rejected, verification=verification), tempfile.TemporaryDirectory() as directory:
                    self.root = Path(directory)
                    updates = {}
                    if verification == "lock-initial":
                        updates["lock_verifier"] = lambda *args, value=rejected: value
                    elif verification == "lock-final":
                        calls = 0

                        def final_lock(*args, value=rejected):
                            nonlocal calls
                            calls += 1
                            return True if calls == 1 else value

                        updates["lock_verifier"] = final_lock
                    elif verification == "staging":
                        updates["staging_verifier"] = lambda *args, value=rejected: value
                    else:
                        updates["completion_validator"] = lambda *args, value=rejected: value
                    with self.assertRaises(ap.VerificationError):
                        ap.execute(**self.args(**updates))
                    self.assertFalse((self.root / "complete.json").exists())

    def test_final_completion_validator_requires_exact_true_and_rejects_exceptions(self):
        rejected_values = (False, None, 1, "truthy")
        for rejected in rejected_values:
            with self.subTest(value=rejected), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
                (self.root / "complete.json").write_bytes(COMPLETE)
                result = self.recover(completion_validator=lambda path, value=rejected: value)
                self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
                self.assertFalse((self.root / "complete.json").exists())
        with tempfile.TemporaryDirectory() as directory:
            self.root = Path(directory)
            (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
            (self.root / "complete.json").write_bytes(COMPLETE)

            def raises(path):
                raise RuntimeError("validator failed")

            self.assertEqual(
                self.recover(completion_validator=raises).classification,
                ap.StartupClassification.CONSUMED_INCOMPLETE,
            )

    def test_producer_and_plan_validation_have_deterministic_hooks_after_marker_durability(self):
        events = []
        ap.execute(**self.args(hook=events.append))
        producer_before = events.index("before:producer-execution")
        producer_after = events.index("after:producer-execution")
        plan_before = events.index("before:plan-validation")
        plan_after = events.index("after:plan-validation")
        marker_sync = events.index("after:file-sync:attempt-consumed.json")
        durable_root = next(
            index
            for index, event in enumerate(events)
            if index > marker_sync and event == "after:directory-sync:root"
        )
        self.assertLess(durable_root, producer_before)
        self.assertLess(producer_before, producer_after)
        self.assertLess(producer_after, plan_before)
        self.assertLess(plan_before, plan_after)

    def test_recovery_requires_closed_matching_marker_before_validator(self):
        marker_cases = {
            "malformed": b"not-json\n",
            "torn": b'{"schema_version":',
            "lock-mismatch": marker_bytes(lock_hash="sha256:" + "3" * 64),
            "holdout-mismatch": marker_bytes(holdout_hash="sha256:" + "3" * 64),
            "dataset-mismatch": marker_bytes(dataset_kind="holdout"),
            "attempt-mismatch": marker_bytes(attempt_id="b" * 32),
            "invalid-attempt": marker_bytes(attempt_id="A" * 32),
        }
        for label, payload in marker_cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                (self.root / ap.MARKER_NAME).write_bytes(payload)
                (self.root / "complete.json").write_bytes(COMPLETE)
                calls = []
                result = self.recover(completion_validator=lambda path: calls.append(path) or True)
                self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
                self.assertEqual(calls, [])
                self.assertTrue((self.root / ap.MARKER_NAME).exists())
                self.assertFalse((self.root / "complete.json").exists())

    def test_marker_reader_rejects_directory_and_symlink_without_validator(self):
        with tempfile.TemporaryDirectory() as directory:
            self.root = Path(directory)
            (self.root / ap.MARKER_NAME).mkdir()
            (self.root / "complete.json").write_bytes(COMPLETE)
            calls = []
            result = self.recover(completion_validator=lambda path: calls.append(path) or True)
            self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
            self.assertEqual(calls, [])
            self.assertTrue((self.root / ap.MARKER_NAME).is_dir())

        with tempfile.TemporaryDirectory() as directory:
            self.root = Path(directory)
            target = self.root / "marker-target.json"
            target.write_bytes(marker_bytes())
            try:
                (self.root / ap.MARKER_NAME).symlink_to(target)
            except (OSError, NotImplementedError):
                return
            (self.root / "complete.json").write_bytes(COMPLETE)
            calls = []
            result = self.recover(completion_validator=lambda path: calls.append(path) or True)
            self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
            self.assertEqual(calls, [])
            self.assertTrue((self.root / ap.MARKER_NAME).is_symlink())

    def test_no_completion_validator_disables_internal_fallback(self):
        old_fallback_document = {
            "schema_version": "area-one-pair-results-complete/1.0",
            "dataset_kind": "development-fixture",
            "lock_hash": LOCK,
            "holdout_hash": HOLDOUT,
        }
        (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
        (self.root / "complete.json").write_bytes(
            (json.dumps(old_fallback_document, sort_keys=True, separators=(",", ":")) + "\n").encode()
        )
        result = self.recover(completion_validator=None)
        self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
        self.assertFalse((self.root / "complete.json").exists())

    def test_expected_attempt_id_optional_but_matching_when_supplied(self):
        (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
        (self.root / "complete.json").write_bytes(COMPLETE)
        self.assertEqual(
            self.recover(expected_attempt_id=None).classification,
            ap.StartupClassification.COMPLETED,
        )

    def test_final_completion_must_be_regular_non_symlink(self):
        for kind in ("directory", "symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
                completion = self.root / "complete.json"
                if kind == "directory":
                    completion.mkdir()
                else:
                    target = self.root / "unmanaged.keep"
                    target.write_bytes(COMPLETE)
                    try:
                        completion.symlink_to(target)
                    except (OSError, NotImplementedError):
                        continue
                calls = []
                result = self.recover(completion_validator=lambda path: calls.append(path) or True)
                self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
                self.assertEqual(calls, [])
                self.assertFalse(completion.exists())

    def test_mountinfo_parser_selects_longest_decodes_escapes_and_rejects_remote(self):
        local = "\n".join(
            (
                "20 1 0:1 / / rw - ext4 /dev/root rw",
                "21 20 0:2 / /srv/data\\040set rw - xfs /dev/data rw",
            )
        )
        self.assertEqual(ap._mount_filesystem_type(Path("/srv/data set/job"), local), "xfs")
        for filesystem_type in ("nfs", "nfs4", "cifs", "smb3", "9p", "ceph", "glusterfs", "fuse.sshfs"):
            with self.subTest(filesystem_type=filesystem_type):
                mountinfo = f"20 1 0:1 / /srv rw - {filesystem_type} server:/share rw"
                self.assertEqual(
                    ap._mount_filesystem_type(Path("/srv/job"), mountinfo),
                    filesystem_type,
                )
        self.assertIsNone(ap._mount_filesystem_type(Path("/srv/job"), "malformed mountinfo"))

    def test_production_path_mechanically_rejects_non_linux_and_injection_bypasses(self):
        with mock.patch.object(ap.sys, "platform", "win32"):
            with self.assertRaises(ap.DurabilityUnavailableError):
                ap._require_pinned_linux_local_filesystem(self.root)
            result = ap.execute(**self.args())
            self.assertEqual(result.state, ap.PublicationState.COMPLETION_PUBLISHED)

    def test_commit_rejects_late_existing_or_symlink_final_without_overwrite(self):
        for kind in ("regular", "symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                lock_calls = 0
                unexpected = b"unexpected-final"

                def lock(*args):
                    nonlocal lock_calls
                    lock_calls += 1
                    if lock_calls == 2:
                        destination = self.root / "rows.bin"
                        if kind == "regular":
                            destination.write_bytes(unexpected)
                        else:
                            target = self.root / "unmanaged.keep"
                            target.write_bytes(unexpected)
                            try:
                                destination.symlink_to(target)
                            except (OSError, NotImplementedError):
                                raise unittest.SkipTest("symlinks unavailable")
                    return True

                with self.assertRaises(ap.UnsafePathError):
                    ap.execute(**self.args(lock_verifier=lock))
                destination = self.root / "rows.bin"
                if kind == "regular":
                    self.assertEqual(destination.read_bytes(), unexpected)
                else:
                    self.assertTrue(destination.is_symlink())
                self.assertFalse((self.root / "complete.json").exists())

    def test_generated_cleanup_fault_matrix_is_idempotent_and_never_reads_outcomes(self):
        def populate(root):
            (root / ap.MARKER_NAME).write_bytes(b"torn-marker")
            staging = root / ap.STAGING_NAME
            nested = staging / "nested"
            nested.mkdir(parents=True)
            (nested / "opaque-secret.bin").write_bytes(b"must-not-read")
            (staging / "other.bin").write_bytes(b"must-not-read")
            for name in NAMES:
                (root / name).write_bytes(b"must-not-read")
            (root / "unmanaged.keep").write_bytes(b"keep")

        with tempfile.TemporaryDirectory() as directory:
            self.root = Path(directory)
            populate(self.root)
            events = []
            self.recover(
                hook=events.append,
                completion_validator=lambda path: self.fail("validator must not run"),
            )
        cleanup_indices = [index for index, event in enumerate(events) if "cleanup-" in event]
        self.assertTrue(cleanup_indices)
        for index, event in enumerate(events):
            if event.startswith(("after:cleanup-unlink:", "after:cleanup-rmdir:")):
                self.assertTrue(
                    any(
                        later.startswith("before:directory-sync:cleanup-parent:")
                        for later in events[index + 1 :]
                    ),
                    event,
                )

        original_read_bytes = Path.read_bytes

        def guarded_read_bytes(path):
            if path.name != ap.MARKER_NAME:
                raise AssertionError(f"outcome bytes read during cleanup: {path.name}")
            return original_read_bytes(path)

        for fault_index in cleanup_indices:
            with self.subTest(index=fault_index, event=events[fault_index]), tempfile.TemporaryDirectory() as directory:
                self.root = Path(directory)
                populate(self.root)
                seen = 0

                def fault(event):
                    nonlocal seen
                    current = seen
                    seen += 1
                    if current == fault_index:
                        raise RuntimeError("cleanup fault")

                with mock.patch.object(Path, "read_bytes", guarded_read_bytes):
                    with self.assertRaises(RuntimeError):
                        self.recover(
                            hook=fault,
                            completion_validator=lambda path: self.fail("validator must not run"),
                        )
                    result = self.recover(
                        completion_validator=lambda path: self.fail("validator must not run")
                    )
                self.assertEqual(result.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
                self.assertTrue((self.root / ap.MARKER_NAME).exists())
                self.assertFalse((self.root / ap.STAGING_NAME).exists())
                for name in NAMES:
                    self.assertFalse((self.root / name).exists())
                self.assertEqual((self.root / "unmanaged.keep").read_bytes(), b"keep")

    def test_failure_filename_must_be_managed(self):
        with self.assertRaises(ap.ConfigurationError):
            self.recover(failure_filename="failure.json")

    def test_invalid_existing_failure_is_replaced_only_for_matching_marker(self):
        (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
        (self.root / "failure.json").write_bytes(b"outcome-bearing invalid bytes")
        result = self.recover(
            managed_artifact_names=NAMES + ("failure.json",),
            failure_filename="failure.json",
        )
        self.assertTrue(result.failure_metadata_published)
        failure = json.loads((self.root / "failure.json").read_bytes())
        self.assertEqual(failure["reason_code"], "interrupted")
        self.assertEqual(failure["message"], "Publication attempt was consumed but did not complete.")

        with tempfile.TemporaryDirectory() as directory:
            self.root = Path(directory)
            (self.root / ap.MARKER_NAME).write_bytes(b"torn")
            (self.root / "failure.json").write_bytes(b"invalid")
            result = self.recover(
                managed_artifact_names=NAMES + ("failure.json",),
                failure_filename="failure.json",
            )
            self.assertFalse(result.failure_metadata_published)
            self.assertFalse((self.root / "failure.json").exists())

    def test_completion_and_failure_metadata_cannot_both_be_accepted(self):
        (self.root / ap.MARKER_NAME).write_bytes(marker_bytes())
        first = self.recover(
            managed_artifact_names=NAMES + ("failure.json",),
            failure_filename="failure.json",
        )
        self.assertTrue(first.failure_metadata_published)
        (self.root / "complete.json").write_bytes(COMPLETE)
        calls = []
        second = self.recover(
            managed_artifact_names=NAMES + ("failure.json",),
            failure_filename="failure.json",
            completion_validator=lambda path: calls.append(path) or True,
        )
        self.assertEqual(second.classification, ap.StartupClassification.CONSUMED_INCOMPLETE)
        self.assertEqual(calls, [])
        self.assertFalse((self.root / "complete.json").exists())
        self.assertTrue((self.root / "failure.json").exists())

    def test_linux_mount_check_rejects_remote_and_undetermined_filesystems(self):
        with mock.patch.object(ap.sys, "platform", "linux"):
            with mock.patch.object(
                Path,
                "read_text",
                return_value="20 1 0:1 / / rw - nfs server:/share rw",
            ):
                with self.assertRaises(ap.DurabilityUnavailableError):
                    ap._require_pinned_linux_local_filesystem(Path("/work"))
            with mock.patch.object(Path, "read_text", return_value="malformed"):
                with self.assertRaises(ap.DurabilityUnavailableError):
                    ap._require_pinned_linux_local_filesystem(Path("/work"))

    def test_injected_sync_order_records_file_before_directory(self):
        events = []
        ap.execute(**self.args(hook=events.append))
        for name in (ap.MARKER_NAME, "complete.json", "summary.json", "rows.bin"):
            sync = events.index(f"after:file-sync:{name}")
            later_directory = next(
                index
                for index, event in enumerate(events)
                if index > sync and event.startswith("after:directory-sync:")
            )
            self.assertLess(sync, later_directory)


if __name__ == "__main__":
    unittest.main()
