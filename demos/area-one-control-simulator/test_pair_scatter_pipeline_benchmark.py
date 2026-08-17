#!/usr/bin/env python3
"""Focused tests for the complete Area One pipeline benchmark."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pair_scatter_pipeline_benchmark as benchmark


class RecordingCallback:
    def __init__(self, result=None) -> None:
        self.result = result
        self.calls: list[tuple[int, str]] = []

    def __call__(self, repetition: int, stage: str):
        self.calls.append((repetition, stage))
        return self.result


class DurationTimer:
    def __init__(self, durations) -> None:
        current = 10.0
        self.values = []
        for duration in durations:
            self.values.extend((current, current + duration))
            current += duration
        self._iterator = iter(self.values)

    def __call__(self) -> float:
        return next(self._iterator)


class SequenceTimer:
    def __init__(self, values) -> None:
        self._iterator = iter(values)

    def __call__(self) -> float:
        return next(self._iterator)


class RecordingProbe:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str]] = []

    def __call__(self, repetition: int, stage: str) -> benchmark.ResourceSnapshot:
        self.calls.append((repetition, stage))
        stage_index = benchmark.STAGES.index(stage)
        return benchmark.ResourceSnapshot(
            process_tree_rss_bytes=100 + repetition * 10 + stage_index,
            temp_bytes=0 if stage == "cleanup" else 200 + repetition,
            final_bytes=(50 + repetition) if stage in {"gzip", "hashes"} else 0,
        )


class FreeDiskProvider:
    def __init__(self, value: int = 10_000) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> int:
        self.calls += 1
        return self.value


class PipelineBenchmarkTests(unittest.TestCase):
    def run_report(self, callback=None, **overrides):
        arguments = dict(
            callback=callback if callback is not None else RecordingCallback(),
            benchmark_rows=10,
            benchmark_work_units=10,
            holdout_rows=20,
            holdout_work_units=20,
            worker_count=4,
            resource_probe=RecordingProbe(),
            free_disk_provider=FreeDiskProvider(),
            timer=DurationTimer([0.25] * (3 * len(benchmark.STAGES))),
        )
        arguments.update(overrides)
        return benchmark.run_pipeline_benchmark(**arguments)

    def test_exactly_three_repetitions_and_every_stage_are_measured(self) -> None:
        callback = RecordingCallback()
        probe = RecordingProbe()
        free_disk = FreeDiskProvider()
        report = self.run_report(
            callback, resource_probe=probe, free_disk_provider=free_disk
        )
        expected_calls = [
            (repetition, stage)
            for repetition in range(3)
            for stage in benchmark.STAGES
        ]
        self.assertEqual(len(report.repetitions), 3)
        self.assertEqual(callback.calls, expected_calls)
        self.assertEqual(probe.calls, expected_calls)
        self.assertEqual(free_disk.calls, 1)
        self.assertEqual(report.worker_count, 4)
        for repetition in report.repetitions:
            self.assertEqual(tuple(repetition.stage_seconds), benchmark.STAGES)
            self.assertEqual(set(repetition.stage_seconds.values()), {0.25})
            self.assertEqual(repetition.total_seconds, 2.0)

    def test_zero_stage_duration_is_allowed_when_total_is_positive(self) -> None:
        durations = ([0.0] + [0.25] * 7) * 3
        report = self.run_report(timer=DurationTimer(durations))
        self.assertEqual(report.repetitions[0].stage_seconds["evolution"], 0.0)
        self.assertGreater(report.repetitions[0].total_seconds, 0.0)

    def test_resource_maxima_survive_cleanup(self) -> None:
        report = self.run_report()
        first = report.repetitions[0]
        self.assertEqual(first.process_tree_rss_bytes, 107)
        self.assertEqual(first.temp_bytes, 200)
        self.assertEqual(first.final_bytes, 50)

    def test_projection_formulas_use_maxima_safety_factor_and_ceil(self) -> None:
        projection = benchmark.project_resources(
            repetition_seconds=(3.0, 4.0, 3.5), final_bytes=(10, 11, 12),
            process_tree_rss_bytes=(100, 101, 102), temp_bytes=(20, 21, 22),
            benchmark_rows=10, benchmark_work_units=8,
            holdout_rows=21, holdout_work_units=17, free_disk_bytes=10_000,
        )
        self.assertEqual(projection.projected_wall_seconds, 17)
        self.assertEqual(projection.projected_final_bytes, 51)
        self.assertEqual(projection.projected_peak_ram_bytes, 204)
        self.assertEqual(projection.projected_temp_bytes, 93)
        self.assertEqual(projection.required_free_disk_bytes, 432)

    def test_exact_resource_boundaries_pass(self) -> None:
        projection = benchmark.project_resources(
            repetition_seconds=(14_400.0,) * 3,
            final_bytes=(5 * 1024**3,) * 3,
            process_tree_rss_bytes=(4 * 1024**3,) * 3,
            temp_bytes=(1,) * 3,
            benchmark_rows=1, benchmark_work_units=1,
            holdout_rows=1, holdout_work_units=1,
            free_disk_bytes=3 * (2 + 10 * 1024**3),
        )
        self.assertEqual(projection.projected_wall_seconds, benchmark.MAX_WALL_SECONDS)
        self.assertEqual(projection.projected_peak_ram_bytes, benchmark.MAX_PEAK_RAM_BYTES)
        self.assertEqual(projection.projected_final_bytes, benchmark.MAX_FINAL_BYTES)
        self.assertTrue(projection.holdout_allowed)

    def test_insufficient_disk_and_over_limit_are_blocked(self) -> None:
        base = dict(
            repetition_seconds=(1.0,) * 3, final_bytes=(1,) * 3,
            process_tree_rss_bytes=(1,) * 3, temp_bytes=(1,) * 3,
            benchmark_rows=1, benchmark_work_units=1,
            holdout_rows=1, holdout_work_units=1,
        )
        disk = benchmark.project_resources(**base, free_disk_bytes=11)
        self.assertEqual(disk.required_free_disk_bytes, 12)
        self.assertFalse(disk.disk_gate_passed)
        wall = benchmark.project_resources(
            **{**base, "repetition_seconds": (14_400.5,) * 3}, free_disk_bytes=12
        )
        self.assertFalse(wall.wall_gate_passed)
        self.assertFalse(wall.holdout_allowed)

    def test_callback_returned_value_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            self.run_report(callback=RecordingCallback(0.25))

    def test_negative_decreasing_and_zero_total_timers_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.run_report(timer=SequenceTimer([-1.0]))
        with self.assertRaises(ValueError):
            self.run_report(timer=SequenceTimer([2.0, 1.0]))
        with self.assertRaises(ValueError):
            self.run_report(timer=SequenceTimer([1.0, 2.0, 1.5]))
        with self.assertRaises(ValueError):
            self.run_report(timer=DurationTimer([0.0] * 8))

    def test_worker_count_must_be_exactly_four(self) -> None:
        for value in (3, 5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_report(worker_count=value)
        with self.assertRaises(TypeError):
            self.run_report(worker_count=True)

    def test_malformed_snapshots_are_rejected(self) -> None:
        invalid_snapshots = (
            None,
            (1, 2, 3),
            benchmark.ResourceSnapshot(-1, 2, 3),
            benchmark.ResourceSnapshot(1, True, 3),
            benchmark.ResourceSnapshot(1, 2, -3),
        )
        for snapshot in invalid_snapshots:
            with self.subTest(snapshot=snapshot), self.assertRaises((TypeError, ValueError)):
                self.run_report(resource_probe=lambda repetition, stage, value=snapshot: value)

    def test_each_repetition_requires_positive_rss_and_final_maxima(self) -> None:
        for snapshot in (
            benchmark.ResourceSnapshot(0, 1, 1),
            benchmark.ResourceSnapshot(1, 1, 0),
        ):
            with self.subTest(snapshot=snapshot), self.assertRaises(ValueError):
                self.run_report(
                    resource_probe=lambda repetition, stage, value=snapshot: value
                )

    def test_invalid_counts_free_disk_and_direct_measurements_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            self.run_report(benchmark_rows=1.5)
        with self.assertRaises(ValueError):
            self.run_report(holdout_rows=0)
        with self.assertRaises(ValueError):
            self.run_report(free_disk_provider=FreeDiskProvider(0))
        with self.assertRaises(TypeError):
            benchmark.project_resources(
                repetition_seconds=(1.0,) * 3, final_bytes=(1,) * 3,
                process_tree_rss_bytes=(1,) * 3, temp_bytes=(0, True, 0),
                benchmark_rows=1, benchmark_work_units=1,
                holdout_rows=1, holdout_work_units=1, free_disk_bytes=1,
            )

    def test_recursive_size_and_path_probe_use_actual_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temp_root = root / "temp"
            final_root = root / "final"
            (temp_root / "nested").mkdir(parents=True)
            final_root.mkdir()
            (temp_root / "a.bin").write_bytes(b"abc")
            (temp_root / "nested" / "b.bin").write_bytes(b"12345")
            (final_root / "result.gz").write_bytes(b"1234567")
            self.assertEqual(
                benchmark.recursive_filesystem_size_bytes(temp_root), 8
            )
            self.assertEqual(
                benchmark.recursive_filesystem_size_bytes(root / "missing"), 0
            )
            with mock.patch.object(
                benchmark, "linux_process_tree_peak_rss_bytes", return_value=321
            ):
                snapshot = benchmark.make_path_resource_probe(
                    temp_root, final_root
                )(0, "gzip")
            self.assertEqual(snapshot, benchmark.ResourceSnapshot(321, 8, 7))

    def test_report_serialization_is_deterministic(self) -> None:
        report = self.run_report()
        first = benchmark.serialize_report(report)
        self.assertEqual(first, benchmark.serialize_report(report))
        self.assertTrue(first.endswith(b"\n"))
        decoded = json.loads(first)
        self.assertEqual(decoded["benchmark_rows"], 10)
        self.assertEqual(decoded["worker_count"], 4)
        self.assertEqual(len(decoded["repetitions"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
