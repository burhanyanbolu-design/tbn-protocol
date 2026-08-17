#!/usr/bin/env python3
"""T3 implementation smoke for the Area One pair-scatter pipeline."""

from __future__ import annotations

import concurrent.futures
import dataclasses
import gzip
import hashlib
import importlib
import json
import math
import multiprocessing
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import pair_scatter_runtime as runtime

# This must execute while importing this module, before any lazy numerical import.
_THREAD_ENVIRONMENT = runtime.configure_thread_environment()

PURPOSE = "t3-implementation-smoke-not-capacity-approval"
WORKER_COUNT = 4
BENCHMARK_ROWS = 4
WORK_UNITS_PER_ROW = 6 * 3 * 4 * 4 * 1
BENCHMARK_WORK_UNITS = BENCHMARK_ROWS * WORK_UNITS_PER_ROW
PRIMARY_ROWS = 17_382_024
SECONDARY_ROWS = 681_648
TOTAL_ROWS = PRIMARY_ROWS + SECONDARY_ROWS
PRIMARY_FOUR_COLUMN_WORK_UNITS = 42_245_038_080
SECONDARY_FOUR_COLUMN_WORK_UNITS = 2_085_873_536
TOTAL_FOUR_COLUMN_WORK_UNITS = (
    PRIMARY_FOUR_COLUMN_WORK_UNITS + SECONDARY_FOUR_COLUMN_WORK_UNITS
)
DECLARED_HOLDOUT_ROWS = TOTAL_ROWS
DECLARED_HOLDOUT_WORK_UNITS = TOTAL_FOUR_COLUMN_WORK_UNITS
NORM_DRIFT_TOLERANCE = 1e-12
GENUINE_PAIRS = tuple(((row, 2), (row + 1, 0)) for row in range(5))
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


@dataclasses.dataclass
class _RepetitionState:
    rows: list[dict[str, object]] = dataclasses.field(default_factory=list)
    encoded_rows: list[bytes] = dataclasses.field(default_factory=list)
    worker_pids: set[int] = dataclasses.field(default_factory=set)
    shards: tuple[Any, ...] = ()
    shard_paths: tuple[Path, ...] = ()
    merged: Any = None
    compressed: Any = None


def _canonical_float(value: float) -> str:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("norm drift must be finite and nonnegative")
    return "0" if value == 0.0 else format(value, ".17g")


def _ready_files(readiness_directory: Path) -> tuple[Path, ...]:
    return tuple(readiness_directory.glob("*.ready"))


def _evolution_worker(ordinal: int, readiness_path: str) -> tuple[int, dict[str, object]]:
    """Run one fixed candidate step after all four spawned workers are resident."""
    readiness_directory = Path(readiness_path)
    pid = os.getpid()
    marker = readiness_directory / f"{ordinal}-{pid}.ready"
    marker.write_text(str(pid), encoding="ascii")
    deadline = time.monotonic() + 30.0
    while len(_ready_files(readiness_directory)) != WORKER_COUNT:
        if time.monotonic() >= deadline:
            raise RuntimeError("four-worker filesystem readiness gate timed out")
        time.sleep(0.01)

    np = importlib.import_module("numpy")
    kernels = importlib.import_module("pair_scatter_kernels")
    state = np.zeros((6, 3, 4, 4), dtype=np.complex128, order="C")
    for basis_column in range(4):
        state[0, 0, basis_column, basis_column] = np.complex128(1.0)
    if state.shape != (6, 3, 4, 4) or not state.flags.c_contiguous:
        raise RuntimeError("worker state layout is not canonical")

    evolved = kernels.candidate_step(
        state,
        (5, 1),
        GENUINE_PAIRS,
        np.float64(np.pi / np.float64(16.0)),
        np.float64(0.0),
    )
    drift = np.float64(abs(kernels.state_norm(evolved) - np.float64(4.0)))
    if not bool(np.isfinite(drift)) or drift > np.float64(NORM_DRIFT_TOLERANCE):
        raise RuntimeError("four-column total squared norm drift exceeded tolerance")
    row: dict[str, object] = {
        "norm_drift": _canonical_float(float(drift)),
        "ordinal": ordinal,
        "state_sha256": hashlib.sha256(evolved.tobytes(order="C")).hexdigest(),
        "work_units": WORK_UNITS_PER_ROW,
    }
    return pid, row


def _load_pipeline_modules() -> tuple[Any, Any]:
    return (
        importlib.import_module("pair_scatter_pipeline_benchmark"),
        importlib.import_module("pair_scatter_shards"),
    )


class DevelopmentSmokePipeline:
    """Concrete callback implementing all eight measured pipeline stages."""

    def __init__(self, benchmark_root: str | os.PathLike[str]) -> None:
        self.root = Path(benchmark_root)
        self.temp_root = self.root / "temporary"
        self.final_root = self.root / "final"
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self.final_root.mkdir(parents=True, exist_ok=True)
        self._states: dict[int, _RepetitionState] = {}
        self._next_stage: dict[int, int] = {}

    def _state(self, repetition: int) -> _RepetitionState:
        return self._states.setdefault(repetition, _RepetitionState())

    def repetition_temp_path(self, repetition: int) -> Path:
        return self.temp_root / f"repetition-{repetition}"

    def repetition_final_path(self, repetition: int) -> Path:
        return self.final_root / f"repetition-{repetition}"

    def __call__(self, repetition: int, stage: str) -> None:
        if stage not in STAGES:
            raise ValueError(f"unknown pipeline stage: {stage}")
        expected_index = self._next_stage.get(repetition, 0)
        if stage != STAGES[expected_index]:
            raise RuntimeError(
                f"repetition {repetition} expected {STAGES[expected_index]}, received {stage}"
            )
        getattr(self, stage)(repetition)
        self._next_stage[repetition] = expected_index + 1

    def evolution(self, repetition: int) -> None:
        state = self._state(repetition)
        repetition_temp = self.repetition_temp_path(repetition)
        shutil.rmtree(repetition_temp, ignore_errors=True)
        readiness = repetition_temp / "readiness"
        readiness.mkdir(parents=True)
        context = multiprocessing.get_context("spawn")
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=4, mp_context=context
        ) as executor:
            futures = [
                executor.submit(_evolution_worker, ordinal, str(readiness))
                for ordinal in range(BENCHMARK_ROWS)
            ]
            results = [future.result() for future in futures]
        state.worker_pids = {pid for pid, _row in results}
        if len(state.worker_pids) != WORKER_COUNT:
            raise RuntimeError("evolution requires four distinct worker PIDs")
        state.rows = sorted((row for _pid, row in results), key=lambda row: row["ordinal"])

    def invariants(self, repetition: int) -> None:
        state = self._state(repetition)
        if len(state.rows) != BENCHMARK_ROWS:
            raise RuntimeError("evolution did not produce exactly four rows")
        if {row.get("ordinal") for row in state.rows} != set(range(BENCHMARK_ROWS)):
            raise RuntimeError("row ordinals are not exactly zero through three")
        if len(state.worker_pids) != WORKER_COUNT:
            raise RuntimeError("worker PID cardinality changed")
        total_work_units = 0
        expected_keys = {"ordinal", "state_sha256", "norm_drift", "work_units"}
        for row in state.rows:
            if set(row) != expected_keys:
                raise RuntimeError("row schema is not the outcome-free smoke schema")
            digest = row["state_sha256"]
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise RuntimeError("state SHA-256 is malformed")
            drift_text = row["norm_drift"]
            if not isinstance(drift_text, str):
                raise RuntimeError("norm drift must be a canonical string")
            drift = float(drift_text)
            if _canonical_float(drift) != drift_text or drift > NORM_DRIFT_TOLERANCE:
                raise RuntimeError("norm drift is not canonical or exceeds tolerance")
            if row["work_units"] != WORK_UNITS_PER_ROW:
                raise RuntimeError("row work-unit count is incorrect")
            total_work_units += int(row["work_units"])
        if total_work_units != BENCHMARK_WORK_UNITS:
            raise RuntimeError("invariant work-unit total must be exactly 1152")

    def encoding(self, repetition: int) -> None:
        state = self._state(repetition)
        _benchmark, shards = _load_pipeline_modules()
        state.encoded_rows = [shards.encode_canonical_row(row) for row in state.rows]
        if any(not encoded.endswith(b"\n") for encoded in state.encoded_rows):
            raise RuntimeError("canonical row encoding lacks LF")

    def shard_write(self, repetition: int) -> None:
        state = self._state(repetition)
        _benchmark, shards = _load_pipeline_modules()
        records = tuple((int(row["ordinal"]), row) for row in state.rows)
        state.shards = shards.build_production_shards(records)
        if b"".join(item.data for item in state.shards) != b"".join(state.encoded_rows):
            raise RuntimeError("production sharding changed canonical row bytes")
        shard_directory = self.repetition_temp_path(repetition) / "shards"
        shard_directory.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for shard in state.shards:
            path = shard_directory / f"shard-{shard.shard_id:08d}.jsonl"
            path.write_bytes(shard.data)
            paths.append(path)
        state.shard_paths = tuple(paths)

    def merge(self, repetition: int) -> None:
        state = self._state(repetition)
        _benchmark, shards = _load_pipeline_modules()
        disk_shards = tuple(
            dataclasses.replace(shard, data=path.read_bytes())
            for shard, path in zip(state.shards, state.shard_paths, strict=True)
        )
        state.merged = shards.merge_production_shards(disk_shards)
        if state.merged.row_count != BENCHMARK_ROWS:
            raise RuntimeError("merged artifact row count is not four")
        (self.repetition_temp_path(repetition) / "merged.jsonl").write_bytes(
            state.merged.data
        )

    def gzip(self, repetition: int) -> None:
        state = self._state(repetition)
        _benchmark, shards = _load_pipeline_modules()
        state.compressed = shards.deterministic_gzip(
            state.merged.data, row_count=state.merged.row_count
        )
        final_directory = self.repetition_final_path(repetition)
        final_directory.mkdir(parents=True, exist_ok=True)
        (final_directory / "rows.jsonl.gz").write_bytes(state.compressed.data)

    def hashes(self, repetition: int) -> None:
        state = self._state(repetition)
        for shard, path in zip(state.shards, state.shard_paths, strict=True):
            disk_data = path.read_bytes()
            if hashlib.sha256(disk_data).hexdigest() != shard.sha256:
                raise RuntimeError("on-disk shard hash mismatch")
            if disk_data.count(b"\n") != shard.row_count:
                raise RuntimeError("on-disk shard row-count mismatch")
        merged_data = (self.repetition_temp_path(repetition) / "merged.jsonl").read_bytes()
        if hashlib.sha256(merged_data).hexdigest() != state.merged.sha256:
            raise RuntimeError("on-disk merged hash mismatch")
        if merged_data.count(b"\n") != state.merged.row_count:
            raise RuntimeError("on-disk merged row-count mismatch")
        compressed_data = (
            self.repetition_final_path(repetition) / "rows.jsonl.gz"
        ).read_bytes()
        if hashlib.sha256(compressed_data).hexdigest() != state.compressed.sha256:
            raise RuntimeError("on-disk gzip hash mismatch")
        decompressed = gzip.decompress(compressed_data)
        if decompressed != merged_data or decompressed.count(b"\n") != BENCHMARK_ROWS:
            raise RuntimeError("gzip decompression or row-count verification failed")

    def cleanup(self, repetition: int) -> None:
        shutil.rmtree(self.repetition_temp_path(repetition), ignore_errors=True)
        shutil.rmtree(self.repetition_final_path(repetition), ignore_errors=True)
        if self.repetition_temp_path(repetition).exists():
            raise RuntimeError("temporary repetition artifacts remain after cleanup")
        if self.repetition_final_path(repetition).exists():
            raise RuntimeError("final repetition artifacts remain after cleanup")
        self._states.pop(repetition, None)

    def resource_probe(self, repetition: int, stage: str) -> Any:
        del stage
        benchmark, _shards = _load_pipeline_modules()
        return benchmark.ResourceSnapshot(
            process_tree_rss_bytes=benchmark.linux_process_tree_peak_rss_bytes(),
            temp_bytes=benchmark.recursive_filesystem_size_bytes(
                self.repetition_temp_path(repetition)
            ),
            final_bytes=benchmark.recursive_filesystem_size_bytes(
                self.repetition_final_path(repetition)
            ),
        )

    def free_disk_bytes(self) -> int:
        return shutil.disk_usage(self.root).free


def run_development_smoke(benchmark_root: str | os.PathLike[str]) -> Any:
    """Run one three-repetition T3 smoke; the declared holdout is never executed."""
    benchmark, _shards = _load_pipeline_modules()
    pipeline = DevelopmentSmokePipeline(benchmark_root)
    return benchmark.run_pipeline_benchmark(
        pipeline,
        benchmark_rows=BENCHMARK_ROWS,
        benchmark_work_units=BENCHMARK_WORK_UNITS,
        holdout_rows=TOTAL_ROWS,
        holdout_work_units=TOTAL_FOUR_COLUMN_WORK_UNITS,
        worker_count=WORKER_COUNT,
        resource_probe=pipeline.resource_probe,
        free_disk_provider=pipeline.free_disk_bytes,
    )


def serialize_evidence(diagnostics: dict[str, object], report: Any) -> bytes:
    """Serialize diagnostics and a non-authorizing projection as evidence only."""
    report_data = dataclasses.asdict(report)
    report_data["projection"]["holdout_allowed"] = False
    report_data["projection"]["evidence_only"] = True
    payload = {
        "benchmark": report_data,
        "diagnostics": diagnostics,
        "holdout_execution_performed": False,
        "projection_authorizes_holdout": False,
        "purpose": PURPOSE,
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def main() -> int:
    expected_digest = os.environ["AREA_ONE_EXPECTED_OCI_DIGEST"]
    actual_digest = os.environ["AREA_ONE_ACTUAL_OCI_DIGEST"]
    pre_numpy = runtime.bootstrap_runtime(
        expected_digest, actual_digest, WORKER_COUNT
    )
    diagnostics = runtime.complete_diagnostics(pre_numpy)
    with tempfile.TemporaryDirectory(prefix="pair-scatter-t3-smoke-") as directory:
        report = run_development_smoke(directory)
        output = serialize_evidence(diagnostics, report)
    import sys

    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
