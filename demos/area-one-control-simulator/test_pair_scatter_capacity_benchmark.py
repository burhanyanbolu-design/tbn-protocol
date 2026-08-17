#!/usr/bin/env python3
"""Focused tests for the representative T7 capacity benchmark."""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pair_scatter_capacity_benchmark as capacity
import pair_scatter_pipeline_benchmark as benchmark

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "pair_scatter_capacity_benchmark.py"


class CapacityDefinitionTests(unittest.TestCase):
    def test_exact_frozen_totals_and_all_strata(self) -> None:
        self.assertEqual(len(capacity.STRATA), 54)
        self.assertEqual(sum(item.holdout_evolutions for item in capacity.STRATA), 3_010_612)
        self.assertEqual(capacity.HOLDOUT_ROWS, 18_063_672)
        self.assertEqual(capacity.HOLDOUT_WORK_UNITS, 44_330_911_616)
        self.assertEqual(sum(item.sample_evolutions for item in capacity.STRATA), 8_192)
        self.assertEqual(capacity.BENCHMARK_ROWS, 49_152)
        self.assertEqual(capacity.BENCHMARK_WORK_UNITS, 120_634_400)
        self.assertTrue(all(item.sample_evolutions > 0 for item in capacity.STRATA))

    def test_apportionment_is_deterministic_and_closed(self) -> None:
        first = capacity.build_strata()
        self.assertEqual(first, capacity.build_strata())
        with self.assertRaises(ValueError):
            capacity.build_strata(53)
        with self.assertRaises(TypeError):
            capacity.build_strata(True)

    def test_tasks_cover_candidate_and_every_control(self) -> None:
        self.assertEqual(len(capacity.TASKS), capacity.SAMPLE_EVOLUTIONS)
        self.assertEqual(tuple(task.ordinal for task in capacity.TASKS), tuple(range(8_192)))
        primary_pair_families = {
            task.family_id for task in capacity.TASKS
            if task.family_id != "baseline" and task.horizon == capacity._horizons(task.s, task.rows)[1]
        }
        self.assertEqual(
            primary_pair_families,
            {"candidate"} | {f"control-{index:03d}" for index in range(100)},
        )

    def test_import_is_pre_numpy_and_independent_of_verifiers(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        roots: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".", 1)[0])
        allowed = set(sys.stdlib_module_names) | {"__future__", "pair_scatter_runtime"}
        self.assertEqual(roots - allowed, set())
        self.assertNotIn("publication_verifier", MODULE_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("pair_scatter_verification", MODULE_PATH.read_text(encoding="utf-8"))

    def test_evidence_never_claims_holdout_execution_or_records_outcomes(self) -> None:
        repetitions = tuple(
            benchmark.Repetition(index, {stage: 0.1 for stage in benchmark.STAGES},
                                 0.8, 100, 200, 50)
            for index in range(3)
        )
        projection = benchmark.Projection(100, 200, 300, 400, 1_800,
                                          True, True, True, True, True)
        report = benchmark.BenchmarkReport(
            capacity.BENCHMARK_ROWS, capacity.BENCHMARK_WORK_UNITS,
            capacity.HOLDOUT_ROWS, capacity.HOLDOUT_WORK_UNITS,
            4, repetitions, projection,
        )
        payload = json.loads(capacity.serialize_evidence({"runtime": "test"}, report))
        self.assertFalse(payload["holdout_execution_performed"])
        self.assertFalse(payload["outcome_data_recorded"])
        self.assertTrue(payload["projection_authorizes_holdout"])
        self.assertTrue(payload["bounded_memory_pipeline"])
        self.assertEqual(
            payload["synthetic_initial_state"],
            "dense-fourier-orthonormal-not-declared-input",
        )
        worker_source = inspect.getsource(capacity._evolution_worker)
        row_source = inspect.getsource(capacity._benchmark_row)
        self.assertNotIn('"probability"', worker_source)
        self.assertIn('"probability": _PLACEHOLDER', row_source)
        self.assertIn('importlib.import_module("resource")', worker_source)
        self.assertNotIn("resource.getrusage", worker_source)

    def test_pipeline_state_and_artifacts_are_streaming_not_row_resident(self) -> None:
        state_fields = {field.name for field in dataclasses.fields(capacity._RepetitionState)}
        self.assertNotIn("rows", state_fields)
        self.assertNotIn("encoded_rows", state_fields)
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("merge_production_shards", source)
        self.assertNotIn("deterministic_gzip", source)
        self.assertIn("shutil.copyfileobj", source)
        self.assertIn("_process_tree_current_rss_bytes", source)
        self.assertIn("runtime.inspect_thread_pools()", source)

    def test_synthetic_columns_are_dense_orthonormal_and_not_declared_inputs(self) -> None:
        import numpy as np

        state = capacity._synthetic_state(np, 9, 8)
        flat = state.reshape(-1, 4)
        self.assertTrue(all(np.count_nonzero(flat[:, index]) == flat.shape[0] for index in range(4)))
        for left in range(4):
            for right in range(4):
                inner = np.sum(np.conjugate(flat[:, left]) * flat[:, right])
                self.assertAlmostEqual(float(inner.real), 1.0 if left == right else 0.0, places=12)
                self.assertAlmostEqual(float(inner.imag), 0.0, places=12)

    def test_direct_six_coin_states_match_four_column_derivation(self) -> None:
        import numpy as np
        import pair_scatter_kernels as kernels

        destinations = capacity._manifest_destinations()
        theta_values = (1 / 16, 1 / 8, 3 / 16, 1 / 4, 3 / 8, 1 / 2)
        phi_values = (0.0, 0.5, 1.0, 1.5)
        cases = ((2, 6, (0, 0), (0, 2)),
                 (3, 6, (2, 1), (3, 0)),
                 (4, 6, (5, 4), (4, 0)))
        families = ("candidate", "control-000", "control-004", "control-009", "control-099")
        coefficients = (
            np.array([0.5, 0.5, 0.5, 0.5], dtype=np.complex128),
            np.array([1, 0, 0, 0], dtype=np.complex128),
            np.array([0, 1, 0, 0], dtype=np.complex128),
            np.array([0, 0, 1, 0], dtype=np.complex128),
            np.array([0, 0, 0, 1], dtype=np.complex128),
            np.array([0.5, 0.5j, -0.5, -0.5j], dtype=np.complex128),
        )

        def initial_columns(s: int, rows: int, start: tuple[int, int]):
            state = np.zeros((rows, s + 1, 4, 4), dtype=np.complex128)
            for basis in range(4):
                state[start[0], start[1], basis, basis] = np.complex128(1.0)
            return state

        for s, rows, start, terminal in cases:
            # One production step is sufficient: each frozen operator is linear,
            # so equality of the six inputs is preserved under every horizon.
            horizon = 1
            baseline_columns = initial_columns(s, rows, start)
            for _ in range(horizon):
                baseline_columns = kernels.baseline_step(baseline_columns, terminal)
            for coefficient, derived in zip(
                coefficients, capacity._coin_states(np, baseline_columns), strict=True
            ):
                direct = np.zeros((rows, s + 1, 4), dtype=np.complex128)
                direct[start[0], start[1], :] = coefficient
                for _ in range(horizon):
                    direct = kernels.baseline_step(direct, terminal)
                np.testing.assert_allclose(direct, derived, rtol=0.0, atol=1e-12)

            for family in families:
                task = capacity.EvolutionTask(0, s, rows, horizon, family, 1)
                pairs = capacity._pairs_for(task, destinations)
                for theta_pi in theta_values:
                    for phi_pi in phi_values:
                        theta = np.float64(np.pi * theta_pi)
                        phi = np.float64(np.pi * phi_pi)
                        columns = initial_columns(s, rows, start)
                        for _ in range(horizon):
                            columns = kernels.candidate_step(columns, terminal, pairs, theta, phi)
                        for coefficient, derived in zip(
                            coefficients, capacity._coin_states(np, columns), strict=True
                        ):
                            direct = np.zeros((rows, s + 1, 4), dtype=np.complex128)
                            direct[start[0], start[1], :] = coefficient
                            for _ in range(horizon):
                                direct = kernels.candidate_step(direct, terminal, pairs, theta, phi)
                            np.testing.assert_allclose(direct, derived, rtol=0.0, atol=1e-12)

    def test_vectorized_pair_layer_matches_explicit_disjoint_blocks(self) -> None:
        import numpy as np
        import pair_scatter_kernels as kernels

        rng = np.random.default_rng(20260816)
        state = np.ascontiguousarray(
            rng.normal(size=(9, 8, 4, 4)) + 1j * rng.normal(size=(9, 8, 4, 4)),
            dtype=np.complex128,
        )
        pairs = tuple(((row, 7), (row + 1, 0)) for row in range(8))
        theta = np.float64(np.pi / np.float64(4.0))
        phi = np.float64(np.pi / np.float64(2.0))
        expected = state.copy(order="C")
        cosine, sine = np.cos(theta), np.sin(theta)
        phase = np.complex128(np.cos(phi) + np.complex128(1j) * np.sin(phi))
        for left, right in pairs:
            left_value = state[left[0], left[1], ...]
            right_value = state[right[0], right[1], ...]
            expected[left[0], left[1], ...] = cosine * left_value - np.conjugate(phase) * sine * right_value
            expected[right[0], right[1], ...] = phase * sine * left_value + cosine * right_value
        actual = kernels.pair_scatter(state, pairs, theta, phi)
        np.testing.assert_array_equal(actual, expected)

    def test_mocked_stage_order_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipeline = capacity.CapacityPipeline(directory)
            calls: list[tuple[int, str]] = []
            patchers = []
            for stage in capacity.STAGES[:-1]:
                replacement = mock.Mock(
                    side_effect=lambda repetition, name=stage: calls.append((repetition, name))
                )
                patchers.append(mock.patch.object(pipeline, stage, replacement))
            for patcher in patchers:
                patcher.start()
            try:
                for stage in capacity.STAGES[:-1]:
                    pipeline(0, stage)
                temp_path = pipeline.repetition_temp_path(0)
                final_path = pipeline.repetition_final_path(0)
                temp_path.mkdir(parents=True, exist_ok=True)
                final_path.mkdir(parents=True, exist_ok=True)
                (temp_path / "temp.bin").write_bytes(b"temp")
                (final_path / "final.bin").write_bytes(b"final")
                pipeline(0, "cleanup")
            finally:
                for patcher in reversed(patchers):
                    patcher.stop()
            self.assertEqual(calls, [(0, stage) for stage in capacity.STAGES[:-1]])
            self.assertFalse(temp_path.exists())
            self.assertFalse(final_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
