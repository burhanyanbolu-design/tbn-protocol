#!/usr/bin/env python3
"""Representative, outcome-free, bounded-memory T7 capacity benchmark."""

from __future__ import annotations

import concurrent.futures
import dataclasses
import gzip
import hashlib
import heapq
import importlib
import json
import math
import multiprocessing
import os
import shutil
import sys
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Iterator, TextIO

import pair_scatter_runtime as runtime

if any(name == "numpy" or name.startswith("numpy.") for name in sys.modules):
    mismatches = {
        name: os.environ.get(name)
        for name in runtime.THREAD_ENVIRONMENT
        if os.environ.get(name) != "1"
    }
    if mismatches:
        raise RuntimeError(f"thread environment mismatch after NumPy import: {mismatches}")
    _THREAD_ENVIRONMENT = {name: "1" for name in runtime.THREAD_ENVIRONMENT}
else:
    _THREAD_ENVIRONMENT = runtime.configure_thread_environment()

PURPOSE = "t7-representative-capacity-benchmark"
BENCHMARK_DEFINITION_VERSION = "area-one-capacity-benchmark/1.1"
WORKER_COUNT = 4
SAMPLE_EVOLUTIONS = 8_192
COINS_PER_EVOLUTION = 6
BENCHMARK_ROWS = SAMPLE_EVOLUTIONS * COINS_PER_EVOLUTION
HOLDOUT_ROWS = 18_063_672
HOLDOUT_EVOLUTIONS = HOLDOUT_ROWS // COINS_PER_EVOLUTION
HOLDOUT_WORK_UNITS = 44_330_911_616
NORM_DRIFT_TOLERANCE = 1e-12
SHARD_ROWS = 100_000
GRIDS = tuple((s, rows) for s in (5, 6, 7) for rows in (7, 8, 9))
COINS = ("uniform", "up", "right", "down", "left", "phase-balanced")
STAGES = ("evolution", "invariants", "encoding", "shard_write",
          "merge", "gzip", "hashes", "cleanup")
_HASH = "sha256:" + "0" * 64
_PLACEHOLDER = "0.12345678901234566"


@dataclasses.dataclass(frozen=True)
class Stratum:
    s: int
    rows: int
    horizon: int
    family_count: int
    paired: bool
    holdout_evolutions: int
    work_units_per_evolution: int
    sample_evolutions: int = 0


@dataclasses.dataclass(frozen=True)
class EvolutionTask:
    ordinal: int
    s: int
    rows: int
    horizon: int
    family_id: str
    work_units: int


@dataclasses.dataclass
class _RepetitionState:
    tasks: tuple[EvolutionTask, ...]
    worker_pids: set[int] = dataclasses.field(default_factory=set)
    worker_result_paths: tuple[Path, ...] = ()
    process_tree_peak_rss_bytes: int = 0
    encoded_path: Path | None = None
    shard_paths: tuple[Path, ...] = ()
    merged_path: Path | None = None
    compressed_path: Path | None = None
    encoded_row_count: int = 0


def _horizons(s: int, rows: int) -> tuple[int, int, int]:
    root = math.sqrt(rows * (s + 1))
    return math.ceil(root), math.ceil(2.0 * root), math.ceil(4.0 * root)


def _base_strata() -> tuple[Stratum, ...]:
    result: list[Stratum] = []
    for s, rows in GRIDS:
        positions = rows * (s + 1)
        coordinate_pairs = positions * (positions - 1)
        short, primary, long = _horizons(s, rows)
        definitions = (
            (short, 1, False), (short, 1, True),
            (primary, 1, False), (primary, 101, True),
            (long, 1, False), (long, 1, True),
        )
        for horizon, family_count, paired in definitions:
            result.append(Stratum(
                s, rows, horizon, family_count, paired,
                coordinate_pairs * family_count,
                positions * 4 * 4 * horizon,
            ))
    return tuple(result)


def build_strata(sample_evolutions: int = SAMPLE_EVOLUTIONS) -> tuple[Stratum, ...]:
    """Hamilton-apportion the sample by exact declared evolution counts."""
    if not isinstance(sample_evolutions, int) or isinstance(sample_evolutions, bool):
        raise TypeError("sample_evolutions must be an integer")
    base = _base_strata()
    if sample_evolutions < len(base):
        raise ValueError("sample_evolutions must cover every frozen stratum")
    total = sum(item.holdout_evolutions for item in base)
    numerators = [sample_evolutions * item.holdout_evolutions for item in base]
    allocations = [value // total for value in numerators]
    remaining = sample_evolutions - sum(allocations)
    order = sorted(range(len(base)), key=lambda i: (-(numerators[i] % total), i))
    for index in order[:remaining]:
        allocations[index] += 1
    if any(value <= 0 for value in allocations):
        raise RuntimeError("representative sample omitted a frozen stratum")
    return tuple(
        dataclasses.replace(item, sample_evolutions=count)
        for item, count in zip(base, allocations, strict=True)
    )


STRATA = build_strata()
BENCHMARK_WORK_UNITS = sum(
    item.sample_evolutions * item.work_units_per_evolution for item in STRATA
)


def build_tasks(strata: tuple[Stratum, ...] = STRATA) -> tuple[EvolutionTask, ...]:
    tasks: list[EvolutionTask] = []
    for stratum in strata:
        for local_index in range(stratum.sample_evolutions):
            if not stratum.paired:
                family_id = "baseline"
            elif stratum.family_count == 1:
                family_id = "candidate"
            else:
                family_index = local_index % stratum.family_count
                family_id = "candidate" if family_index == 0 else f"control-{family_index - 1:03d}"
            tasks.append(EvolutionTask(
                len(tasks), stratum.s, stratum.rows, stratum.horizon,
                family_id, stratum.work_units_per_evolution,
            ))
    return tuple(tasks)


TASKS = build_tasks()
if (sum(item.holdout_evolutions for item in STRATA) != HOLDOUT_EVOLUTIONS
        or len(TASKS) != SAMPLE_EVOLUTIONS):
    raise RuntimeError("frozen workload totals are inconsistent")


def _canonical_float(value: float) -> str:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("benchmark invariant must be finite and nonnegative")
    return "0" if value == 0.0 else format(value, ".17g")


def _manifest_destinations() -> dict[tuple[str, int], tuple[int, ...]]:
    data = json.loads(Path(__file__).with_name("control-family-manifest.json").read_text(
        encoding="utf-8"
    ))
    return {
        (family["family_id"], member["R"]): tuple(member["destination_rows"])
        for family in data["families"] for member in family["members"]
    }


def _pairs_for(task: EvolutionTask, destinations: dict[tuple[str, int], tuple[int, ...]]) -> tuple[Any, ...]:
    if task.family_id == "baseline":
        return ()
    if task.family_id == "candidate":
        return tuple(((row, task.s), (row + 1, 0)) for row in range(task.rows - 1))
    return tuple(
        ((source, task.s), (destination, 0))
        for source, destination in enumerate(destinations[(task.family_id, task.rows)])
    )


def _synthetic_state(np: Any, rows: int, width: int) -> Any:
    """Return four dense orthonormal columns outside declared localized inputs."""
    dimension = rows * width * 4
    flat = np.empty((dimension, 4), dtype=np.complex128, order="C")
    scale = np.float64(1.0 / math.sqrt(dimension))
    indices = np.arange(dimension, dtype=np.float64)
    for basis in range(4):
        angles = np.float64(2.0 * math.pi * basis / dimension) * indices
        flat[:, basis] = np.ascontiguousarray(
            (np.cos(angles) + np.complex128(1j) * np.sin(angles)) * scale,
            dtype=np.complex128,
        )
    state = np.ascontiguousarray(flat.reshape(rows, width, 4, 4))
    for left in range(4):
        for right in range(4):
            inner = np.sum(
                np.conjugate(flat[:, left]) * flat[:, right],
                dtype=np.complex128,
            )
            expected = np.complex128(1.0 if left == right else 0.0)
            if abs(complex(inner - expected)) > 1e-12:
                raise RuntimeError("synthetic benchmark columns are not orthonormal")
    return state


def _coin_states(np: Any, state: Any) -> tuple[Any, ...]:
    columns = tuple(state[:, :, :, index] for index in range(4))
    uniform = np.ascontiguousarray(
        (columns[0] + columns[1] + columns[2] + columns[3]) * np.float64(0.5),
        dtype=np.complex128,
    )
    phase_balanced = np.ascontiguousarray(
        (columns[0] + np.complex128(1j) * columns[1]
         - columns[2] - np.complex128(1j) * columns[3]) * np.float64(0.5),
        dtype=np.complex128,
    )
    return (uniform,) + tuple(
        np.ascontiguousarray(column, dtype=np.complex128) for column in columns
    ) + (phase_balanced,)


def _proc_rss_bytes(pid: int) -> int:
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="ascii").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return 0
    return 0


def _child_pids(pid: int) -> tuple[int, ...]:
    try:
        text = Path(f"/proc/{pid}/task/{pid}/children").read_text(encoding="ascii")
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return ()
    return tuple(int(value) for value in text.split())


def _process_tree_current_rss_bytes(root_pid: int) -> int:
    pending = [root_pid]
    seen: set[int] = set()
    total = 0
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += _proc_rss_bytes(pid)
        pending.extend(_child_pids(pid))
    return total


def _evolution_worker(
    worker: int,
    tasks: tuple[EvolutionTask, ...],
    readiness_path: str,
    result_path: str,
) -> tuple[int, int, int, str, tuple[dict[str, object], ...]]:
    readiness = Path(readiness_path)
    pid = os.getpid()
    (readiness / f"{worker}-{pid}.ready").write_text(str(pid), encoding="ascii")
    deadline = time.monotonic() + 30.0
    while len(tuple(readiness.glob("*.ready"))) != WORKER_COUNT:
        if time.monotonic() >= deadline:
            raise RuntimeError("four-worker readiness gate timed out")
        time.sleep(0.01)

    np = importlib.import_module("numpy")
    kernels = importlib.import_module("pair_scatter_kernels")
    thread_pools = runtime.inspect_thread_pools()
    destinations = _manifest_destinations()
    theta = np.float64(np.pi / np.float64(4.0))
    phi = np.float64(np.pi / np.float64(2.0))
    templates = {
        (rows, s + 1): _synthetic_state(np, rows, s + 1)
        for s, rows in GRIDS
    }
    count = 0
    with Path(result_path).open("w", encoding="utf-8", newline="\n") as output:
        for task in tasks:
            width = task.s + 1
            positions = task.rows * width
            terminal_flat = (task.ordinal * 29 + 1) % positions
            terminal = divmod(terminal_flat, width)
            state = templates[(task.rows, width)].copy(order="C")
            pairs = _pairs_for(task, destinations)
            maximum_drift = 0.0
            for _step in range(task.horizon):
                if task.family_id == "baseline":
                    state = kernels.baseline_step(state, terminal)
                else:
                    state = kernels.candidate_step(state, terminal, pairs, theta, phi)
                drift = abs(float(kernels.state_norm(state)) - 4.0)
                if not math.isfinite(drift) or drift > NORM_DRIFT_TOLERANCE:
                    raise RuntimeError("four-column norm drift exceeded tolerance")
                maximum_drift = max(maximum_drift, drift)
            probabilities = tuple(
                float(kernels.final_terminal_probability(value, terminal))
                for value in _coin_states(np, state)
            )
            if not all(
                math.isfinite(value)
                and -NORM_DRIFT_TOLERANCE <= value <= 1.0 + NORM_DRIFT_TOLERANCE
                for value in probabilities
            ):
                raise RuntimeError("synthetic probability invariant failed")
            bound_error = max(
                (max(0.0, -value, value - 1.0) for value in probabilities),
                default=0.0,
            )
            record = {
                "family_id": task.family_id,
                "horizon": task.horizon,
                "max_norm_drift": _canonical_float(maximum_drift),
                "max_probability_bound_error": _canonical_float(bound_error),
                "ordinal": task.ordinal,
                "R": task.rows,
                "s": task.s,
                "work_units": task.work_units,
            }
            output.write(json.dumps(
                record, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ) + "\n")
            count += 1
    resource_module = importlib.import_module("resource")
    peak_rss = int(
        resource_module.getrusage(resource_module.RUSAGE_SELF).ru_maxrss * 1024
    )
    return pid, peak_rss, count, result_path, thread_pools


def _next_record(handle: TextIO) -> dict[str, object] | None:
    line = handle.readline()
    if not line:
        return None
    value = json.loads(line)
    if not isinstance(value, dict):
        raise RuntimeError("worker result record is not an object")
    return value


def _merged_worker_records(paths: tuple[Path, ...]) -> Iterator[dict[str, object]]:
    with ExitStack() as stack:
        handles = [
            stack.enter_context(path.open("r", encoding="utf-8", newline=""))
            for path in paths
        ]
        heap: list[tuple[int, int, dict[str, object]]] = []
        for index, handle in enumerate(handles):
            record = _next_record(handle)
            if record is not None:
                heapq.heappush(heap, (int(record["ordinal"]), index, record))
        expected = 0
        while heap:
            ordinal, index, record = heapq.heappop(heap)
            if ordinal != expected:
                raise RuntimeError("worker result ordinals are not contiguous")
            expected += 1
            yield record
            following = _next_record(handles[index])
            if following is not None:
                heapq.heappush(heap, (int(following["ordinal"]), index, following))


def _benchmark_row(record: dict[str, object], coin_index: int) -> dict[str, object]:
    task_ordinal = int(record["ordinal"])
    s, rows = int(record["s"]), int(record["R"])
    width = s + 1
    terminal = divmod((task_ordinal * 29 + 1) % (rows * width), width)
    family = str(record["family_id"])
    paired = family != "baseline"
    ordinal = task_ordinal * COINS_PER_EVOLUTION + coin_index
    micro_key = f"capacity-synthetic-v1:{task_ordinal}:{COINS[coin_index]}"
    row_key = f"{micro_key}:{record['horizon']}:{family}"
    return {
        "schema_version": "area-one-pair-row/1.0",
        "ordinal": ordinal, "shard_id": ordinal // SHARD_ROWS,
        "s": s, "R": rows,
        "start_row": 0, "start_column": 0,
        "terminal_row": terminal[0], "terminal_column": terminal[1],
        "coin": COINS[coin_index], "horizon": int(record["horizon"]),
        "method_kind": "baseline" if not paired else (
            "candidate" if family == "candidate" else "control"
        ),
        "family_id": family,
        "theta_index": 3 if paired else -1, "phi_index": 1 if paired else -1,
        "theta_pi": "0.25" if paired else "0", "phi_pi": "0.5" if paired else "0",
        "micro_case_key": micro_key, "row_key": row_key,
        "lock_hash": _HASH, "family_manifest_hash": _HASH, "holdout_hash": _HASH,
        "probability": _PLACEHOLDER,
        "max_norm_drift": record["max_norm_drift"],
        "max_probability_bound_error": record["max_probability_bound_error"],
        "operations": {
            "oracle_calls": int(record["horizon"]),
            "coin_applications": int(record["horizon"]),
            "shifts": int(record["horizon"]),
            "pair_rotations": (
                4 * (rows - 1) * int(record["horizon"]) if paired else 0
            ),
            "final_measurements": 1,
            "hilbert_dimension": rows * width * 4,
        },
    }


def _hash_file(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    size = 0
    lines = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
            lines += chunk.count(b"\n")
    return digest.hexdigest(), size, lines


class CapacityPipeline:
    """Eight-stage pipeline with memory bounded independently of row count."""

    def __init__(self, benchmark_root: str | os.PathLike[str]) -> None:
        self.root = Path(benchmark_root)
        self.temp_root = self.root / "temporary"
        self.final_root = self.root / "final"
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self.final_root.mkdir(parents=True, exist_ok=True)
        self._states: dict[int, _RepetitionState] = {}
        self._next_stage: dict[int, int] = {}

    def _state(self, repetition: int) -> _RepetitionState:
        return self._states.setdefault(repetition, _RepetitionState(TASKS))

    def repetition_temp_path(self, repetition: int) -> Path:
        return self.temp_root / f"repetition-{repetition}"

    def repetition_final_path(self, repetition: int) -> Path:
        return self.final_root / f"repetition-{repetition}"

    def __call__(self, repetition: int, stage: str) -> None:
        if stage not in STAGES:
            raise ValueError(f"unknown pipeline stage: {stage}")
        expected = self._next_stage.get(repetition, 0)
        if stage != STAGES[expected]:
            raise RuntimeError(
                f"repetition {repetition} expected {STAGES[expected]}, received {stage}"
            )
        getattr(self, stage)(repetition)
        self._next_stage[repetition] = expected + 1

    def evolution(self, repetition: int) -> None:
        state = self._state(repetition)
        repetition_temp = self.repetition_temp_path(repetition)
        shutil.rmtree(repetition_temp, ignore_errors=True)
        readiness = repetition_temp / "readiness"
        results_directory = repetition_temp / "worker-results"
        readiness.mkdir(parents=True)
        results_directory.mkdir()
        chunks = tuple(
            tuple(task for task in state.tasks if task.ordinal % WORKER_COUNT == worker)
            for worker in range(WORKER_COUNT)
        )
        context = multiprocessing.get_context("spawn")
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=WORKER_COUNT, mp_context=context
        ) as executor:
            futures = [
                executor.submit(
                    _evolution_worker, worker, chunks[worker], str(readiness),
                    str(results_directory / f"worker-{worker}.jsonl"),
                )
                for worker in range(WORKER_COUNT)
            ]
            while not all(future.done() for future in futures):
                state.process_tree_peak_rss_bytes = max(
                    state.process_tree_peak_rss_bytes,
                    _process_tree_current_rss_bytes(os.getpid()),
                )
                time.sleep(0.01)
            results = [future.result() for future in futures]
        state.worker_pids = {pid for pid, _rss, _count, _path, _pools in results}
        if len(state.worker_pids) != WORKER_COUNT:
            raise RuntimeError("capacity evolution requires four distinct worker PIDs")
        if sum(count for _pid, _rss, count, _path, _pools in results) != SAMPLE_EVOLUTIONS:
            raise RuntimeError("worker evolution count mismatch")
        if any(not pools for _pid, _rss, _count, _path, pools in results):
            raise RuntimeError("worker thread-pool diagnostics are empty")
        state.worker_result_paths = tuple(Path(path) for _pid, _rss, _count, path, _pools in results)
        resource_module = importlib.import_module("resource")
        parent_peak = int(
            resource_module.getrusage(resource_module.RUSAGE_SELF).ru_maxrss * 1024
        )
        conservative_peak = parent_peak + sum(
            rss for _pid, rss, _count, _path, _pools in results
        )
        state.process_tree_peak_rss_bytes = max(
            state.process_tree_peak_rss_bytes, conservative_peak
        )

    def invariants(self, repetition: int) -> None:
        state = self._state(repetition)
        count = 0
        work_units = 0
        for record in _merged_worker_records(state.worker_result_paths):
            count += 1
            work_units += int(record["work_units"])
            if float(str(record["max_norm_drift"])) > NORM_DRIFT_TOLERANCE:
                raise RuntimeError("capacity invariant drift exceeded tolerance")
        if count != SAMPLE_EVOLUTIONS or work_units != BENCHMARK_WORK_UNITS:
            raise RuntimeError("capacity evolution totals changed")
        if state.process_tree_peak_rss_bytes <= 0:
            raise RuntimeError("process-tree RSS evidence is missing")

    def encoding(self, repetition: int) -> None:
        state = self._state(repetition)
        shards = importlib.import_module("pair_scatter_shards")
        path = self.repetition_temp_path(repetition) / "encoded.jsonl"
        count = 0
        with path.open("wb") as output:
            for record in _merged_worker_records(state.worker_result_paths):
                for coin_index in range(COINS_PER_EVOLUTION):
                    output.write(shards.encode_canonical_row(
                        _benchmark_row(record, coin_index)
                    ))
                    count += 1
        if count != BENCHMARK_ROWS:
            raise RuntimeError("capacity encoded row count mismatch")
        state.encoded_path = path
        state.encoded_row_count = count

    def shard_write(self, repetition: int) -> None:
        state = self._state(repetition)
        if state.encoded_path is None:
            raise RuntimeError("encoding artifact is missing")
        directory = self.repetition_temp_path(repetition) / "shards"
        directory.mkdir()
        paths: list[Path] = []
        current: Any = None
        count = 0
        try:
            with state.encoded_path.open("rb") as source:
                for line in source:
                    if count % SHARD_ROWS == 0:
                        if current is not None:
                            current.close()
                        path = directory / f"shard-{len(paths):08d}.jsonl"
                        paths.append(path)
                        current = path.open("wb")
                    current.write(line)
                    count += 1
        finally:
            if current is not None:
                current.close()
        if count != BENCHMARK_ROWS or not paths:
            raise RuntimeError("capacity shard-write count mismatch")
        state.shard_paths = tuple(paths)

    def merge(self, repetition: int) -> None:
        state = self._state(repetition)
        merged = self.repetition_temp_path(repetition) / "merged.jsonl"
        total = 0
        with merged.open("wb") as output:
            for index, path in enumerate(state.shard_paths):
                _digest, _size, rows = _hash_file(path)
                if index < len(state.shard_paths) - 1 and rows != SHARD_ROWS:
                    raise RuntimeError("non-final capacity shard is not full")
                if index == len(state.shard_paths) - 1 and not 1 <= rows <= SHARD_ROWS:
                    raise RuntimeError("final capacity shard has invalid size")
                total += rows
                with path.open("rb") as source:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
        if total != BENCHMARK_ROWS:
            raise RuntimeError("capacity merge row count mismatch")
        state.merged_path = merged

    def gzip(self, repetition: int) -> None:
        state = self._state(repetition)
        if state.merged_path is None:
            raise RuntimeError("merged artifact is missing")
        directory = self.repetition_final_path(repetition)
        directory.mkdir(parents=True, exist_ok=True)
        compressed = directory / "rows.jsonl.gz"
        with state.merged_path.open("rb") as source, compressed.open("wb") as raw:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0
            ) as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
        state.compressed_path = compressed

    def hashes(self, repetition: int) -> None:
        state = self._state(repetition)
        if state.merged_path is None or state.compressed_path is None:
            raise RuntimeError("capacity hash inputs are missing")
        merged_digest, _merged_size, merged_rows = _hash_file(state.merged_path)
        if merged_rows != BENCHMARK_ROWS:
            raise RuntimeError("capacity merged hash row count mismatch")
        compressed_digest, compressed_size, _compressed_lines = _hash_file(
            state.compressed_path
        )
        if compressed_size <= 0 or not merged_digest or not compressed_digest:
            raise RuntimeError("capacity artifact hash is missing")
        decompressed_digest = hashlib.sha256()
        decompressed_rows = 0
        with gzip.open(state.compressed_path, "rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                decompressed_digest.update(chunk)
                decompressed_rows += chunk.count(b"\n")
        if decompressed_digest.hexdigest() != merged_digest:
            raise RuntimeError("capacity gzip content hash mismatch")
        if decompressed_rows != BENCHMARK_ROWS:
            raise RuntimeError("capacity gzip row count mismatch")

    def cleanup(self, repetition: int) -> None:
        shutil.rmtree(self.repetition_temp_path(repetition), ignore_errors=True)
        shutil.rmtree(self.repetition_final_path(repetition), ignore_errors=True)
        if (self.repetition_temp_path(repetition).exists()
                or self.repetition_final_path(repetition).exists()):
            raise RuntimeError("capacity cleanup left artifacts")
        self._states.pop(repetition, None)

    def resource_probe(self, repetition: int, stage: str) -> Any:
        del stage
        benchmark = importlib.import_module("pair_scatter_pipeline_benchmark")
        state = self._state(repetition)
        resource_module = importlib.import_module("resource")
        parent_peak = int(
            resource_module.getrusage(resource_module.RUSAGE_SELF).ru_maxrss * 1024
        )
        return benchmark.ResourceSnapshot(
            process_tree_rss_bytes=max(parent_peak, state.process_tree_peak_rss_bytes),
            temp_bytes=benchmark.recursive_filesystem_size_bytes(
                self.repetition_temp_path(repetition)
            ),
            final_bytes=benchmark.recursive_filesystem_size_bytes(
                self.repetition_final_path(repetition)
            ),
        )

    def free_disk_bytes(self) -> int:
        return shutil.disk_usage(self.root).free


def run_capacity_benchmark(benchmark_root: str | os.PathLike[str]) -> Any:
    benchmark = importlib.import_module("pair_scatter_pipeline_benchmark")
    pipeline = CapacityPipeline(benchmark_root)
    return benchmark.run_pipeline_benchmark(
        pipeline,
        benchmark_rows=BENCHMARK_ROWS,
        benchmark_work_units=BENCHMARK_WORK_UNITS,
        holdout_rows=HOLDOUT_ROWS,
        holdout_work_units=HOLDOUT_WORK_UNITS,
        worker_count=WORKER_COUNT,
        resource_probe=pipeline.resource_probe,
        free_disk_provider=pipeline.free_disk_bytes,
    )


def serialize_evidence(diagnostics: dict[str, object], report: Any) -> bytes:
    payload = {
        "benchmark": dataclasses.asdict(report),
        "benchmark_definition_version": BENCHMARK_DEFINITION_VERSION,
        "bounded_memory_pipeline": True,
        "diagnostics": diagnostics,
        "holdout_execution_performed": False,
        "outcome_data_recorded": False,
        "projection_authorizes_holdout": report.projection.holdout_allowed,
        "purpose": PURPOSE,
        "sample_evolutions": SAMPLE_EVOLUTIONS,
        "synthetic_initial_state": "dense-fourier-orthonormal-not-declared-input",
        "strata": [dataclasses.asdict(item) for item in STRATA],
    }
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8") + b"\n"


def main() -> int:
    expected_digest = os.environ["AREA_ONE_EXPECTED_OCI_DIGEST"]
    actual_digest = os.environ["AREA_ONE_ACTUAL_OCI_DIGEST"]
    pre_numpy = runtime.bootstrap_runtime(expected_digest, actual_digest, WORKER_COUNT)
    diagnostics = runtime.complete_diagnostics(pre_numpy)
    with tempfile.TemporaryDirectory(prefix="pair-scatter-capacity-") as directory:
        report = run_capacity_benchmark(directory)
        output = serialize_evidence(diagnostics, report)
    sys.stdout.buffer.write(output)
    return 0 if report.projection.holdout_allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
