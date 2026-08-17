#!/usr/bin/env python3
"""Focused T9 tests for development-only parameter selection."""

from __future__ import annotations

import copy
import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

import development_control_manifest
import pair_scatter_development_selection as selection
import pair_scatter_kernels as kernels


class PlanAndTaskTests(unittest.TestCase):
    def test_exact_frozen_plan_counts_and_order(self) -> None:
        plan = selection.development_plan()
        selection.validate_plan(plan)
        self.assertEqual(plan["development_grids"], 3)
        self.assertEqual(plan["parameters"], 24)
        self.assertEqual(plan["families"], 101)
        self.assertEqual(plan["declared_trajectories"], 25_132_032)
        self.assertEqual(plan["paired_four_column_evolutions"], 4_188_672)
        self.assertEqual(plan["shared_baseline_four_column_evolutions"], 1_728)
        self.assertEqual(plan["workers"], 4)
        self.assertEqual(plan["heldout_accesses"], 0)
        self.assertEqual(plan["lock_accesses"], 0)
        tasks = selection.build_group_tasks()
        self.assertEqual(len(tasks), 7_272)
        self.assertEqual(tasks[0], selection.GroupTask(0, "candidate", 0, 0, 2, 6, 9))
        self.assertEqual(tasks[-1].family_id, "control-099")
        self.assertEqual(tasks[-1].theta_index, 5)
        self.assertEqual(tasks[-1].phi_index, 3)
        self.assertEqual((tasks[-1].s, tasks[-1].rows), (4, 6))
        self.assertEqual({task.rows for task in tasks}, {6})

    def test_plan_only_reads_no_inputs_and_prints_zero_access(self) -> None:
        output = io.StringIO()
        with (
            mock.patch.object(Path, "read_bytes", side_effect=AssertionError),
            mock.patch.object(Path, "read_text", side_effect=AssertionError),
            redirect_stdout(output),
        ):
            self.assertEqual(selection.main(["--plan-only"]), 0)
        text = output.getvalue()
        self.assertIn("T9_PLAN_ONLY_PASS", text)
        self.assertIn("heldout_accesses=0", text)
        self.assertIn("lock_accesses=0", text)

    def test_parameter_grid_uses_frozen_ordinal_mapping(self) -> None:
        values = [
            selection.parameter_values(np, theta, phi)
            for theta in range(6) for phi in range(4)
        ]
        self.assertEqual(len(values), 24)
        self.assertEqual(values[0], (np.float64(np.pi / 16), np.float64(0.0)))
        self.assertEqual(values[-1], (np.float64(np.pi / 2), np.float64(3 * np.pi / 2)))
        with self.assertRaises(selection.DevelopmentSelectionError):
            selection.parameter_values(np, 6, 0)

    def test_source_has_no_forbidden_runtime_imports_or_heldout_grids(self) -> None:
        source = Path(selection.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import pair_scatter_capacity_benchmark", source)
        self.assertNotIn("import atomic_publication", source)
        self.assertNotIn("import publication_verifier", source)
        self.assertNotIn("(5, 7)", source)
        self.assertNotIn("(6, 8)", source)
        self.assertNotIn("(7, 9)", source)


class DirectDerivedTests(unittest.TestCase):
    def test_six_direct_states_match_four_column_derivation(self) -> None:
        projection = development_control_manifest.load_projection()
        s, rows = 2, 6
        start, terminal = (0, 0), (0, 2)
        theta, phi = selection.parameter_values(np, 2, 1)
        pairs = selection._pair_map(projection, s)["candidate"]
        columns = selection.initial_columns(np, s, rows, start)
        columns, _drift = selection._evolve_columns(
            np, kernels, columns, terminal, 9, pairs, theta, phi
        )
        derived = selection.coin_states(np, columns)
        for coin_index, vector in enumerate(selection.coin_vectors(np)):
            direct = selection.initial_direct(np, s, rows, start, vector)
            for _step in range(9):
                direct = kernels.candidate_step(
                    direct, terminal, pairs, theta, phi
                )
            np.testing.assert_allclose(
                direct, derived[coin_index], rtol=0.0, atol=1.0e-12
            )
            self.assertLessEqual(
                abs(
                    kernels.final_terminal_probability(direct, terminal)
                    - kernels.final_terminal_probability(
                        derived[coin_index], terminal
                    )
                ),
                1.0e-12,
            )

    def test_exact_zero_probability_has_positive_zero_bound_error(self) -> None:
        columns = selection.initial_columns(np, 2, 6, (0, 0))
        probabilities, bound_error = selection._probabilities(
            np, kernels, columns, (0, 1)
        )
        self.assertEqual(probabilities, (np.float64(0.0),) * 6)
        self.assertEqual(bound_error, np.float64(0.0))
        self.assertFalse(bool(np.signbit(bound_error)))
        self.assertEqual(
            __import__("research_numerics").canonical_float64(bound_error), "0"
        )

    def test_group_evaluation_rejects_non_development_grid(self) -> None:
        projection = development_control_manifest.load_projection()
        bad = selection.GroupTask(0, "candidate", 0, 0, 5, 7, 14)
        with self.assertRaisesRegex(
            selection.DevelopmentSelectionError, "development-only"
        ):
            selection.evaluate_group(bad, projection, {})


class AggregationTests(unittest.TestCase):
    @staticmethod
    def synthetic_records(
        *, candidate_q10: str = "0", nonfinite: bool = False
    ) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for task in selection.build_group_tasks():
            q10 = candidate_q10 if task.family_id == "candidate" else "0"
            median = "nan" if nonfinite and task.ordinal == 0 else "0"
            records.append({
                "ordinal": task.ordinal,
                "family_id": task.family_id,
                "theta_index": task.theta_index,
                "phi_index": task.phi_index,
                "s": task.s,
                "R": task.rows,
                "horizon": task.horizon,
                "micro_case_count": selection.GRID_PAIR_COUNTS[(task.s, task.rows)] * 6,
                "median_lift": median,
                "q10_lift": q10,
                "maximum_norm_drift": "0",
                "maximum_probability_bound_error": "0",
            })
        return records

    def test_complete_ties_select_lowest_indices_for_all_101_families(self) -> None:
        scores, winners, status, invariants = selection.aggregate_group_records(
            self.synthetic_records()
        )
        self.assertEqual(len(scores), 2_424)
        self.assertEqual(len(winners), 101)
        self.assertTrue(all(
            (winner["theta_index"], winner["phi_index"]) == (0, 0)
            for winner in winners
        ))
        self.assertEqual(status, "feasible")
        self.assertEqual(invariants["maximum_norm_drift"], np.float64(0.0))

    def test_infeasible_candidate_is_retained_and_rejected(self) -> None:
        scores, winners, status, _invariants = selection.aggregate_group_records(
            self.synthetic_records(candidate_q10="-0.029999999999999999")
        )
        self.assertEqual(len(scores), 2_424)
        self.assertFalse(winners[0]["feasible"])
        self.assertEqual(winners[0]["family_id"], "candidate")
        self.assertEqual(status, "rejected")
        self.assertEqual(len(winners[1:]), 100)

    def test_nonfinite_group_metric_fails_closed(self) -> None:
        with self.assertRaises(Exception):
            selection.aggregate_group_records(
                self.synthetic_records(nonfinite=True)
            )


class DeterminismAndSafetyTests(unittest.TestCase):
    def test_one_stream_and_four_partition_merge_have_identical_bytes(self) -> None:
        records = [
            {"ordinal": ordinal, "value": ordinal % 3}
            for ordinal in range(40)
        ]
        one = selection.deterministic_group_bytes(records)
        partitions = [
            [record for record in records if record["ordinal"] % 4 == worker]
            for worker in range(4)
        ]
        interleaved = [record for part in reversed(partitions) for record in part]
        four = selection.deterministic_group_bytes(interleaved)
        self.assertEqual(one, four)

    def test_frozen_preflight_verifies_both_anchor_paths_and_r6_projection(self) -> None:
        projection = selection.verify_frozen_inputs()
        self.assertEqual(projection["R"], 6)
        self.assertEqual(len(projection["families"]), 100)
        self.assertEqual(
            projection["source_manifest_hash"],
            development_control_manifest.SOURCE_MANIFEST_HASH,
        )

    def test_output_and_worker_guards(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nonempty = root / "nonempty"
            nonempty.mkdir()
            (nonempty / "x").write_text("x", encoding="ascii")
            with self.assertRaises(selection.DevelopmentSelectionError):
                selection._require_empty_output_directory(nonempty)
            empty = root / "empty"
            empty.mkdir()
            self.assertEqual(
                selection._require_empty_output_directory(empty), empty.resolve()
            )
            with self.assertRaises(selection.DevelopmentSelectionError):
                selection.run_development_selection(empty, 1)

    def test_failure_after_staging_cleans_output_and_temporary_tree(self) -> None:
        digest = "sha256:" + "1" * 64
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            output = parent / "output"
            output.mkdir()
            environment = {
                "AREA_ONE_EXPECTED_OCI_DIGEST": digest,
                "AREA_ONE_ACTUAL_OCI_DIGEST": digest,
            }
            with (
                mock.patch.dict(os.environ, environment, clear=False),
                mock.patch.object(
                    selection.runtime, "bootstrap_runtime", return_value={}
                ),
                mock.patch.object(
                    selection.runtime, "complete_diagnostics", return_value={}
                ),
                mock.patch.object(
                    selection, "verify_frozen_inputs",
                    return_value=development_control_manifest.load_projection(),
                ),
                mock.patch.object(
                    selection, "validate_direct_derived_sample",
                    side_effect=selection.DevelopmentSelectionError("injected crash"),
                ),
            ):
                with self.assertRaisesRegex(
                    selection.DevelopmentSelectionError, "injected crash"
                ):
                    selection.run_development_selection(output, 4)
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(parent.glob(".area-one-t9-*")), [])

    def test_schema_is_closed_and_contains_no_lock_or_holdout_fields(self) -> None:
        schema_path = Path(selection.__file__).with_name(
            "publication_schemas"
        ) / "area-one-pair-development-selection-1.0.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["$id"], selection.SCHEMA_VERSION)
        text = schema_path.read_text(encoding="utf-8")
        self.assertNotIn('"lock_hash"', text)
        self.assertNotIn('"holdout_hash"', text)
    @classmethod
    def valid_closed_artifact(cls) -> dict[str, object]:
        scores, winners, status, _invariants = selection.aggregate_group_records(
            AggregationTests.synthetic_records()
        )
        content, _baseline_invariants = selection.build_baseline_table()
        encoded = selection.canonical_json_bytes(content)
        projection = development_control_manifest.load_projection()
        thread_environment = {
            name: "1" for name in selection.runtime.THREAD_ENVIRONMENT
        }
        return {
            "schema_version": selection.SCHEMA_VERSION,
            "dataset_kind": "development",
            "protocol_sha256": selection.PROTOCOL_SHA256,
            "source_manifest_hash": development_control_manifest.SOURCE_MANIFEST_HASH,
            "development_manifest_hash": projection["projection_hash"],
            "runtime": {
                "cpu_flags": [],
                "cpu_model": "fixture",
                "machine": "x86_64",
                "oci_digest": "sha256:" + "1" * 64,
                "platform": "Linux",
                "python_build": ["fixture", "fixture"],
                "python_implementation": "CPython",
                "python_version": "3.13.7",
                "thread_environment": thread_environment,
                "worker_count": 4,
                "numpy_version": "2.4.2",
                "numpy_configuration": "fixture",
                "threadpoolctl_version": "3.6.0",
                "thread_pools": [],
                "worker_diagnostics": [
                    {
                        "worker": worker,
                        "pid": worker + 1,
                        "numpy_version": "2.4.2",
                        "thread_pools": [],
                    }
                    for worker in range(4)
                ],
            },
            "grids": selection._expected_grid_records(),
            "coin_order": list(selection.COIN_ORDER),
            "parameter_order": selection._expected_parameter_order(),
            "method_order": list(selection.METHOD_ORDER),
            "counts": selection.development_plan(),
            "parameter_scores": scores,
            "winners": winners,
            "candidate_status": status,
            "invariants": {
                "maximum_norm_drift": "0",
                "maximum_probability_bound_error": "0",
                "maximum_direct_derived_amplitude_error": "0",
                "maximum_direct_derived_probability_error": "0",
                "direct_derived_comparisons": 2_178,
            },
            "baseline_table": {
                "canonical_sha256": selection.sha256_bytes(encoded),
                "canonical_byte_size": len(encoded),
                "content": content,
            },
        }

    def test_closed_schema_and_semantic_reconstruction_reject_nested_tampering(self) -> None:
        artifact = self.valid_closed_artifact()
        selection.validate_selection_artifact(artifact)

        def alter_and_rehash_baseline(value) -> None:
            wrapper = value["baseline_table"]
            probabilities = wrapper["content"]["records"][0]["probabilities"]
            probabilities[0] = "0" if probabilities[0] != "0" else "0.5"
            encoded = selection.canonical_json_bytes(wrapper["content"])
            wrapper["canonical_sha256"] = selection.sha256_bytes(encoded)
            wrapper["canonical_byte_size"] = len(encoded)

        mutations = (
            lambda value: value["parameter_scores"][0].update({"unknown": True}),
            lambda value: value["winners"][0].update({"theta_index": 1}),
            lambda value: value["runtime"]["worker_diagnostics"][1].update({"pid": 1}),
            lambda value: value["grids"][0].update({"positions": 30}),
            lambda value: value["baseline_table"].update({"canonical_byte_size": 1}),
            alter_and_rehash_baseline,
        )
        for mutate in mutations:
            changed = copy.deepcopy(artifact)
            mutate(changed)
            with self.subTest(mutate=mutate), self.assertRaises(
                selection.DevelopmentSelectionError
            ):
                selection.validate_selection_artifact(changed)

    def test_final_publication_uses_same_directory_atomic_replace(self) -> None:
        digest = "sha256:" + "1" * 64
        winner = {"theta_index": 0, "phi_index": 0, "feasible": True}
        real_replace = os.replace
        replace_calls: list[tuple[Path, Path]] = []

        def require_same_directory(source, destination) -> None:
            source_path = Path(source)
            destination_path = Path(destination)
            if source_path.parent != destination_path.parent:
                raise OSError(18, "Invalid cross-device link")
            replace_calls.append((source_path, destination_path))
            real_replace(source_path, destination_path)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            output.mkdir()
            with (
                mock.patch.dict(os.environ, {
                    "AREA_ONE_EXPECTED_OCI_DIGEST": digest,
                    "AREA_ONE_ACTUAL_OCI_DIGEST": digest,
                }, clear=False),
                mock.patch.object(selection.runtime, "bootstrap_runtime", return_value={}),
                mock.patch.object(selection.runtime, "complete_diagnostics", return_value={}),
                mock.patch.object(selection, "verify_frozen_inputs", return_value=development_control_manifest.load_projection()),
                mock.patch.object(selection, "validate_direct_derived_sample", return_value={
                    "comparisons": 2_178,
                    "maximum_amplitude_error": np.float64(0.0),
                    "maximum_probability_error": np.float64(0.0),
                    "maximum_norm_drift": np.float64(0.0),
                }),
                mock.patch.object(selection, "build_baseline_table", return_value=({"fixture": True}, {
                    "maximum_norm_drift": np.float64(0.0),
                    "maximum_probability_bound_error": np.float64(0.0),
                })),
                mock.patch.object(selection, "run_workers", return_value=([], [])),
                mock.patch.object(selection, "aggregate_group_records", return_value=(
                    [{}] * 2_424, [winner] * 101, "feasible", {
                        "maximum_norm_drift": np.float64(0.0),
                        "maximum_probability_bound_error": np.float64(0.0),
                    },
                )),
                mock.patch.object(selection, "validate_selection_artifact"),
                mock.patch.object(selection, "_sync_directory"),
                mock.patch.object(selection.os, "replace", side_effect=require_same_directory),
            ):
                selection.run_development_selection(output, 4)
            self.assertEqual(len(replace_calls), 1)
            source, destination = replace_calls[0]
            self.assertTrue(source.parent.samefile(output))
            self.assertTrue(destination.parent.samefile(output))
            self.assertEqual(destination.name, selection.RESULT_FILENAME)
            self.assertEqual(
                [path.name for path in output.iterdir()],
                [selection.RESULT_FILENAME],
            )

    def test_atomic_publication_failure_removes_same_directory_temporary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with mock.patch.object(
                selection.os, "replace", side_effect=OSError(18, "injected")
            ):
                with self.assertRaises(OSError):
                    selection._atomic_publish(output, selection.RESULT_FILENAME, b"x\n")
            self.assertEqual(list(output.iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
