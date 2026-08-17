#!/usr/bin/env python3
"""Complete-pipeline callback benchmark and frozen holdout projections."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypeAlias

try:
    import resource
except ImportError:  # pragma: no cover - exercised only on non-POSIX systems
    resource = None  # type: ignore[assignment]

REPETITIONS = 3
WORKER_COUNT = 4
SAFETY_FACTOR = 2.0
MAX_WALL_SECONDS = 8 * 60 * 60
MAX_PEAK_RAM_BYTES = 8 * 1024**3
MAX_FINAL_BYTES = 10 * 1024**3
STAGES = (
    "evolution",
    "invariants",
    "encoding",
    "shard_write",
    "merge",
    "gzip",
    "hashes",
    "cleanup",
)

PathValue: TypeAlias = str | os.PathLike[str]


@dataclass(frozen=True)
class ResourceSnapshot:
    process_tree_rss_bytes: int
    temp_bytes: int
    final_bytes: int


@dataclass(frozen=True)
class Repetition:
    repetition: int
    stage_seconds: dict[str, float]
    total_seconds: float
    process_tree_rss_bytes: int
    temp_bytes: int
    final_bytes: int


@dataclass(frozen=True)
class Projection:
    projected_wall_seconds: int
    projected_final_bytes: int
    projected_peak_ram_bytes: int
    projected_temp_bytes: int
    required_free_disk_bytes: int
    wall_gate_passed: bool
    ram_gate_passed: bool
    final_gate_passed: bool
    disk_gate_passed: bool
    holdout_allowed: bool


@dataclass(frozen=True)
class BenchmarkReport:
    benchmark_rows: int
    benchmark_work_units: int
    holdout_rows: int
    holdout_work_units: int
    worker_count: int
    repetitions: tuple[Repetition, ...]
    projection: Projection


def _integer(value: object, name: str, *, positive: bool) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if not positive and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _positive_int(value: object, name: str) -> int:
    return _integer(value, name, positive=True)


def _nonnegative_int(value: object, name: str) -> int:
    return _integer(value, name, positive=False)


def _measurement_series(
    values: Sequence[int], name: str, *, positive: bool
) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must contain integer measurements")
    materialized = tuple(values)
    if len(materialized) != REPETITIONS:
        raise ValueError(f"{name} must contain exactly {REPETITIONS} measurements")
    validator = _positive_int if positive else _nonnegative_int
    return tuple(validator(value, f"{name}[{index}]") for index, value in enumerate(materialized))


def _numeric_time(value: object, name: str, *, positive: bool) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0.0 or (positive and result == 0.0):
        requirement = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be {requirement} and finite")
    return result


def _timer_reading(timer: Callable[[], float], point: str) -> float:
    return _numeric_time(timer(), f"timer reading for {point}", positive=False)


def _validated_snapshot(value: object, repetition: int, stage: str) -> ResourceSnapshot:
    if not isinstance(value, ResourceSnapshot):
        raise TypeError(
            f"resource_probe repetition {repetition} stage {stage} must return ResourceSnapshot"
        )
    return ResourceSnapshot(
        _nonnegative_int(value.process_tree_rss_bytes, "process_tree_rss_bytes"),
        _nonnegative_int(value.temp_bytes, "temp_bytes"),
        _nonnegative_int(value.final_bytes, "final_bytes"),
    )


def linux_process_tree_peak_rss_bytes() -> int:
    """Return Linux peak RSS for this process plus terminated children, in bytes."""
    if resource is None or not hasattr(resource, "RUSAGE_SELF"):
        raise RuntimeError("process-tree peak RSS measurement requires Linux resource support")
    self_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children_rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return _nonnegative_int(int((self_rss + children_rss) * 1024), "process-tree peak RSS")


def recursive_filesystem_size_bytes(path: PathValue) -> int:
    """Return the logical byte size of regular files at or below path."""
    root = Path(path)
    try:
        metadata = root.stat(follow_symlinks=False)
    except FileNotFoundError:
        return 0
    if root.is_symlink():
        return 0
    if root.is_file():
        return _nonnegative_int(metadata.st_size, f"size of {root}")
    if not root.is_dir():
        return 0

    total = 0
    try:
        entries = os.scandir(root)
    except FileNotFoundError:
        return 0
    with entries:
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    total += recursive_filesystem_size_bytes(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
            except FileNotFoundError:
                continue
    return _nonnegative_int(total, f"recursive size of {root}")


def make_path_resource_probe(
    temp_path: PathValue, final_path: PathValue
) -> Callable[[int, str], ResourceSnapshot]:
    """Create a probe for process-tree peak RSS and actual temp/final paths."""
    temp_root = Path(temp_path)
    final_root = Path(final_path)

    def probe(repetition: int, stage: str) -> ResourceSnapshot:
        del repetition, stage
        return ResourceSnapshot(
            process_tree_rss_bytes=linux_process_tree_peak_rss_bytes(),
            temp_bytes=recursive_filesystem_size_bytes(temp_root),
            final_bytes=recursive_filesystem_size_bytes(final_root),
        )

    return probe


# Explicit aliases keep the helper names convenient without changing behavior.
process_tree_peak_rss_bytes = linux_process_tree_peak_rss_bytes
filesystem_size_bytes = recursive_filesystem_size_bytes
make_filesystem_resource_probe = make_path_resource_probe


def project_resources(
    *,
    repetition_seconds: Sequence[float],
    final_bytes: Sequence[int],
    process_tree_rss_bytes: Sequence[int],
    temp_bytes: Sequence[int],
    benchmark_rows: int,
    benchmark_work_units: int,
    holdout_rows: int,
    holdout_work_units: int,
    free_disk_bytes: int,
) -> Projection:
    """Apply the four normative projection formulas and mechanical gates."""
    benchmark_rows = _positive_int(benchmark_rows, "benchmark_rows")
    benchmark_work_units = _positive_int(benchmark_work_units, "benchmark_work_units")
    holdout_rows = _positive_int(holdout_rows, "holdout_rows")
    holdout_work_units = _positive_int(holdout_work_units, "holdout_work_units")
    free_disk_bytes = _positive_int(free_disk_bytes, "free_disk_bytes")
    times = tuple(
        _numeric_time(value, f"pipeline repetition {index} time", positive=True)
        for index, value in enumerate(repetition_seconds)
    )
    if len(times) != REPETITIONS:
        raise ValueError(f"repetition_seconds must contain exactly {REPETITIONS} values")
    finals = _measurement_series(final_bytes, "final_bytes", positive=True)
    rss = _measurement_series(process_tree_rss_bytes, "process_tree_rss_bytes", positive=True)
    temps = _measurement_series(temp_bytes, "temp_bytes", positive=False)
    rate = max(times) / benchmark_work_units
    bytes_per_row = max(finals) / benchmark_rows
    projected_wall = math.ceil(SAFETY_FACTOR * rate * holdout_work_units)
    projected_final = math.ceil(SAFETY_FACTOR * bytes_per_row * holdout_rows)
    projected_ram = math.ceil(SAFETY_FACTOR * max(rss))
    projected_temp = math.ceil(SAFETY_FACTOR * max(temps) * holdout_rows / benchmark_rows)
    required_disk = 3 * (projected_temp + projected_final)
    wall_ok = projected_wall <= MAX_WALL_SECONDS
    ram_ok = projected_ram <= MAX_PEAK_RAM_BYTES
    final_ok = projected_final <= MAX_FINAL_BYTES
    disk_ok = free_disk_bytes >= required_disk
    return Projection(
        projected_wall, projected_final, projected_ram, projected_temp,
        required_disk, wall_ok, ram_ok, final_ok, disk_ok,
        wall_ok and ram_ok and final_ok and disk_ok,
    )


def run_pipeline_benchmark(
    callback: Callable[[int, str], None],
    *,
    benchmark_rows: int,
    benchmark_work_units: int,
    holdout_rows: int,
    holdout_work_units: int,
    worker_count: int,
    resource_probe: Callable[[int, str], ResourceSnapshot],
    free_disk_provider: Callable[[], int],
    timer: Callable[[], float] = time.perf_counter,
) -> BenchmarkReport:
    """Run exactly three measured callback pipelines; never run a holdout."""
    if not callable(callback):
        raise TypeError("callback must be callable")
    if not callable(resource_probe):
        raise TypeError("resource_probe must be callable")
    if not callable(free_disk_provider):
        raise TypeError("free_disk_provider must be callable")
    if not callable(timer):
        raise TypeError("timer must be callable")
    worker_count = _positive_int(worker_count, "worker_count")
    if worker_count != WORKER_COUNT:
        raise ValueError(f"worker_count must be exactly {WORKER_COUNT}")
    benchmark_rows = _positive_int(benchmark_rows, "benchmark_rows")
    benchmark_work_units = _positive_int(benchmark_work_units, "benchmark_work_units")
    holdout_rows = _positive_int(holdout_rows, "holdout_rows")
    holdout_work_units = _positive_int(holdout_work_units, "holdout_work_units")

    repetitions: list[Repetition] = []
    previous_timer_reading: float | None = None
    for repetition in range(REPETITIONS):
        stage_seconds: dict[str, float] = {}
        peak_rss = 0
        peak_temp = 0
        peak_final = 0
        for stage in STAGES:
            start = _timer_reading(timer, f"{stage} repetition {repetition} start")
            if previous_timer_reading is not None and start < previous_timer_reading:
                raise ValueError(f"timer decreased before {stage} repetition {repetition}")
            callback_result = callback(repetition, stage)
            end = _timer_reading(timer, f"{stage} repetition {repetition} end")
            snapshot_result = resource_probe(repetition, stage)
            if callback_result is not None:
                raise TypeError(
                    f"callback repetition {repetition} stage {stage} must return None"
                )
            if end < start:
                raise ValueError(
                    f"timer decreased during {stage} repetition {repetition}"
                )
            previous_timer_reading = end
            stage_seconds[stage] = end - start
            snapshot = _validated_snapshot(snapshot_result, repetition, stage)
            peak_rss = max(peak_rss, snapshot.process_tree_rss_bytes)
            peak_temp = max(peak_temp, snapshot.temp_bytes)
            peak_final = max(peak_final, snapshot.final_bytes)

        total = math.fsum(stage_seconds[stage] for stage in STAGES)
        if not math.isfinite(total) or total <= 0.0:
            raise ValueError(f"repetition {repetition} total time must be positive and finite")
        if peak_rss <= 0:
            raise ValueError(f"repetition {repetition} maximum process-tree RSS must be positive")
        if peak_final <= 0:
            raise ValueError(f"repetition {repetition} maximum final bytes must be positive")
        repetitions.append(
            Repetition(
                repetition, stage_seconds, total, peak_rss, peak_temp, peak_final
            )
        )

    measured_free_disk = _positive_int(free_disk_provider(), "measured free disk")
    projection = project_resources(
        repetition_seconds=tuple(item.total_seconds for item in repetitions),
        final_bytes=tuple(item.final_bytes for item in repetitions),
        process_tree_rss_bytes=tuple(
            item.process_tree_rss_bytes for item in repetitions
        ),
        temp_bytes=tuple(item.temp_bytes for item in repetitions),
        benchmark_rows=benchmark_rows,
        benchmark_work_units=benchmark_work_units,
        holdout_rows=holdout_rows,
        holdout_work_units=holdout_work_units,
        free_disk_bytes=measured_free_disk,
    )
    return BenchmarkReport(
        benchmark_rows, benchmark_work_units, holdout_rows, holdout_work_units,
        worker_count, tuple(repetitions), projection,
    )


def serialize_report(report: BenchmarkReport) -> bytes:
    """Serialize a benchmark report deterministically as canonical JSON plus LF."""
    if not isinstance(report, BenchmarkReport):
        raise TypeError("report must be a BenchmarkReport")
    try:
        data = json.dumps(
            asdict(report), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("benchmark report is not deterministic JSON") from exc
    return data + b"\n"
