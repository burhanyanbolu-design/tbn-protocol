#!/usr/bin/env python3
"""Frozen T9 development-only parameter selection for Area One."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import multiprocessing
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import development_control_manifest as development_manifest
import independent_protocol_anchor
import matching_control_manifest
import pair_scatter_runtime as runtime
import protocol_approval_anchor

PROTOCOL_SHA256 = (
    "sha256:9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be"
)
SCHEMA_VERSION = "area-one-pair-development-selection/1.0"
BASELINE_SCHEMA_VERSION = "area-one-pair-development-baseline/1.0"
DEVELOPMENT_GRIDS = ((2, 6), (3, 6), (4, 6))
GRID_HORIZONS = {(2, 6): 9, (3, 6): 10, (4, 6): 11}
COIN_ORDER = ("uniform", "up", "right", "down", "left", "phase-balanced")
THETA_NUMERATORS = (1, 2, 3, 4, 6, 8)
PHI_NUMERATORS = (0, 1, 2, 3)
METHOD_ORDER = ("candidate",) + tuple(f"control-{i:03d}" for i in range(100))
WORKER_COUNT = 4
NORM_TOLERANCE = 1.0e-12
PROBABILITY_TOLERANCE = 1.0e-12
GRID_PAIR_COUNTS = {(2, 6): 306, (3, 6): 552, (4, 6): 870}
BASELINE_EVOLUTIONS = 1_728
PAIRED_EVOLUTIONS = 4_188_672
ACTUAL_EVOLUTIONS = 4_190_400
DECLARED_TRAJECTORIES = 25_132_032
MICRO_CASES_PER_PARAMETER_METHOD = 10_368
GROUP_TASK_COUNT = 7_272
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTOCOL_PATH = PROJECT_ROOT / "data" / protocol_approval_anchor.PROTOCOL_BASENAME
ANCHOR_PATH = PROTOCOL_PATH.with_name(PROTOCOL_PATH.name + ".sha256")
APPROVAL_PATH = PROJECT_ROOT / "data" / (
    "area-one-overlap-pair-scatterer-protocol-freeze-approval-2026-08-16.md"
)
FULL_MANIFEST_PATH = matching_control_manifest.DEFAULT_PATH
DEVELOPMENT_MANIFEST_PATH = development_manifest.DEFAULT_PATH
RESULT_FILENAME = "area-one-development-selection.json"
BASELINE_FILENAME = "area-one-development-baseline-table.json"
SCHEMA_PATH = Path(__file__).with_name("publication_schemas") / (
    "area-one-pair-development-selection-1.0.schema.json"
)


class DevelopmentSelectionError(ValueError):
    """Raised when T9 input, execution, or aggregation fails closed."""


@dataclass(frozen=True)
class GroupTask:
    ordinal: int
    family_id: str
    theta_index: int
    phi_index: int
    s: int
    rows: int
    horizon: int


def canonical_json_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError) as exc:
        raise DevelopmentSelectionError("value is not canonical JSON") from exc
    return encoded + b"\n"


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def development_plan() -> dict[str, int]:
    return {
        "development_grids": len(DEVELOPMENT_GRIDS),
        "parameters": len(THETA_NUMERATORS) * len(PHI_NUMERATORS),
        "families": len(METHOD_ORDER),
        "micro_cases_per_parameter_method": MICRO_CASES_PER_PARAMETER_METHOD,
        "declared_trajectories": DECLARED_TRAJECTORIES,
        "paired_four_column_evolutions": PAIRED_EVOLUTIONS,
        "shared_baseline_four_column_evolutions": BASELINE_EVOLUTIONS,
        "actual_four_column_evolutions": ACTUAL_EVOLUTIONS,
        "group_tasks": GROUP_TASK_COUNT,
        "workers": WORKER_COUNT,
        "heldout_accesses": 0,
        "lock_accesses": 0,
    }


def validate_plan(plan: dict[str, int]) -> None:
    expected = {
        "development_grids": 3,
        "parameters": 24,
        "families": 101,
        "micro_cases_per_parameter_method": 10_368,
        "declared_trajectories": 25_132_032,
        "paired_four_column_evolutions": 4_188_672,
        "shared_baseline_four_column_evolutions": 1_728,
        "actual_four_column_evolutions": 4_190_400,
        "group_tasks": 7_272,
        "workers": 4,
        "heldout_accesses": 0,
        "lock_accesses": 0,
    }
    if plan != expected:
        raise DevelopmentSelectionError("development workload plan changed")

def print_plan() -> None:
    plan = development_plan()
    validate_plan(plan)
    print("T9_PLAN_ONLY_PASS")
    for name, value in plan.items():
        print(f"{name}={value}")
    print("grid_order=(2,6),(3,6),(4,6)")
    print("method_order=candidate,control-000..control-099")
    print("outcome_access=NONE")


def build_group_tasks() -> tuple[GroupTask, ...]:
    tasks: list[GroupTask] = []
    ordinal = 0
    for family_id in METHOD_ORDER:
        for theta_index in range(6):
            for phi_index in range(4):
                for s, rows in DEVELOPMENT_GRIDS:
                    tasks.append(GroupTask(
                        ordinal, family_id, theta_index, phi_index, s, rows,
                        GRID_HORIZONS[(s, rows)],
                    ))
                    ordinal += 1
    result = tuple(tasks)
    if len(result) != GROUP_TASK_COUNT:
        raise DevelopmentSelectionError("group task count changed")
    if [task.ordinal for task in result] != list(range(GROUP_TASK_COUNT)):
        raise DevelopmentSelectionError("group task ordinals are not canonical")
    return result


def parameter_values(np: Any, theta_index: int, phi_index: int) -> tuple[Any, Any]:
    if type(theta_index) is not int or not 0 <= theta_index < 6:
        raise DevelopmentSelectionError("theta_index must be 0 through 5")
    if type(phi_index) is not int or not 0 <= phi_index < 4:
        raise DevelopmentSelectionError("phi_index must be 0 through 3")
    theta = np.float64(
        np.float64(THETA_NUMERATORS[theta_index]) * np.float64(math.pi)
        / np.float64(16.0)
    )
    phi = np.float64(
        np.float64(PHI_NUMERATORS[phi_index]) * np.float64(math.pi)
        / np.float64(2.0)
    )
    if not bool(np.isfinite(theta)) or not bool(np.isfinite(phi)):
        raise DevelopmentSelectionError("parameter construction was non-finite")
    return theta, phi


def micro_case_key(
    s: int, rows: int, start: tuple[int, int], terminal: tuple[int, int],
    coin: str,
) -> str:
    if coin not in COIN_ORDER:
        raise DevelopmentSelectionError("unknown coin key")
    return json.dumps(
        [s, rows, start[0], start[1], terminal[0], terminal[1], coin],
        separators=(",", ":"), ensure_ascii=False,
    )


def _load_numerical_modules() -> tuple[Any, Any, Any]:
    np = importlib.import_module("numpy")
    kernels = importlib.import_module("pair_scatter_kernels")
    numerics = importlib.import_module("research_numerics")
    if getattr(np, "__version__", None) != runtime.NUMPY_VERSION:
        raise DevelopmentSelectionError("NumPy version is not frozen")
    return np, kernels, numerics


def initial_columns(np: Any, s: int, rows: int, start: tuple[int, int]) -> Any:
    width = s + 1
    state = np.zeros((rows, width, 4, 4), dtype=np.complex128, order="C")
    for direction in range(4):
        state[start[0], start[1], direction, direction] = np.complex128(1.0)
    return state

def coin_states(np: Any, columns: Any) -> tuple[Any, ...]:
    directional = tuple(columns[:, :, :, index] for index in range(4))
    uniform = np.ascontiguousarray(
        (directional[0] + directional[1] + directional[2] + directional[3])
        * np.float64(0.5),
        dtype=np.complex128,
    )
    phase_balanced = np.ascontiguousarray(
        (directional[0] + np.complex128(1j) * directional[1]
         - directional[2] - np.complex128(1j) * directional[3])
        * np.float64(0.5),
        dtype=np.complex128,
    )
    return (uniform,) + tuple(
        np.ascontiguousarray(value, dtype=np.complex128)
        for value in directional
    ) + (phase_balanced,)


def coin_vectors(np: Any) -> tuple[Any, ...]:
    vectors = [
        np.array((0.5, 0.5, 0.5, 0.5), dtype=np.complex128)
    ]
    for direction in range(4):
        vector = np.zeros(4, dtype=np.complex128)
        vector[direction] = np.complex128(1.0)
        vectors.append(vector)
    vectors.append(np.array(
        (0.5, 0.5j, -0.5, -0.5j), dtype=np.complex128
    ))
    return tuple(vectors)


def initial_direct(
    np: Any, s: int, rows: int, start: tuple[int, int], vector: Any
) -> Any:
    state = np.zeros((rows, s + 1, 4), dtype=np.complex128, order="C")
    state[start[0], start[1], :] = vector
    return state


def _column_norm_drift(np: Any, columns: Any) -> Any:
    with np.errstate(over="raise", invalid="raise"):
        squared = columns.real * columns.real + columns.imag * columns.imag
        norms = np.sum(squared, axis=(0, 1, 2), dtype=np.float64)
        drift = np.max(np.abs(norms - np.float64(1.0)))
    value = np.float64(drift)
    if not bool(np.isfinite(value)):
        raise DevelopmentSelectionError("column norm drift is non-finite")
    if bool(value > np.float64(NORM_TOLERANCE)):
        raise DevelopmentSelectionError("column norm drift exceeded tolerance")
    return value


def _direct_norm_drift(np: Any, kernels: Any, state: Any) -> Any:
    drift = np.float64(abs(kernels.state_norm(state) - np.float64(1.0)))
    if not bool(np.isfinite(drift)) or bool(
        drift > np.float64(NORM_TOLERANCE)
    ):
        raise DevelopmentSelectionError("direct-state norm drift exceeded tolerance")
    return drift


def _evolve_columns(
    np: Any, kernels: Any, state: Any, terminal: tuple[int, int],
    horizon: int, pairs: tuple[Any, ...] | None, theta: Any | None,
    phi: Any | None,
) -> tuple[Any, Any]:
    maximum = np.float64(0.0)
    for _step in range(horizon):
        state = (
            kernels.baseline_step(state, terminal)
            if pairs is None
            else kernels.candidate_step(state, terminal, pairs, theta, phi)
        )
        maximum = np.maximum(maximum, _column_norm_drift(np, state))
    return state, np.float64(maximum)

def _pair_map(projection: dict[str, Any], s: int) -> dict[str, tuple[Any, ...]]:
    result: dict[str, tuple[Any, ...]] = {
        "candidate": tuple(((row, s), (row + 1, 0)) for row in range(5))
    }
    for family in projection["families"]:
        result[family["family_id"]] = tuple(
            ((source, s), (destination, 0))
            for source, destination in enumerate(
                family["member"]["destination_rows"]
            )
        )
    if tuple(result) != METHOD_ORDER:
        raise DevelopmentSelectionError("projected family order changed")
    return result


def verify_frozen_inputs() -> dict[str, Any]:
    producer_digest = protocol_approval_anchor.verify_candidate(
        PROTOCOL_PATH, ANCHOR_PATH
    )
    independent_digest = independent_protocol_anchor.verify(
        PROTOCOL_PATH, ANCHOR_PATH
    )
    if producer_digest != PROTOCOL_SHA256 or independent_digest != PROTOCOL_SHA256:
        raise DevelopmentSelectionError("frozen protocol digest mismatch")
    approval = APPROVAL_PATH.read_text(encoding="utf-8", errors="strict")
    if (
        "Status: **FROZEN**" not in approval
        or f"SHA-256: `{PROTOCOL_SHA256}`" not in approval
    ):
        raise DevelopmentSelectionError("explicit protocol approval record mismatch")
    full = matching_control_manifest.load_manifest(FULL_MANIFEST_PATH)
    matching_control_manifest.verify_independent_regeneration(full)
    if full["manifest_hash"] != development_manifest.SOURCE_MANIFEST_HASH:
        raise DevelopmentSelectionError("full control manifest hash mismatch")
    projection = development_manifest.load_projection(DEVELOPMENT_MANIFEST_PATH)
    if projection["source_manifest_hash"] != full["manifest_hash"]:
        raise DevelopmentSelectionError("development projection source mismatch")
    return projection


def _require_empty_output_directory(path: Path) -> Path:
    if path.is_symlink() or not path.exists() or not path.is_dir():
        raise DevelopmentSelectionError(
            "output must be an existing regular empty directory"
        )
    metadata = path.stat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise DevelopmentSelectionError("output is not a directory")
    if any(path.iterdir()):
        raise DevelopmentSelectionError("output directory must be empty")
    return path.resolve()


def _probabilities(
    np: Any, kernels: Any, columns: Any, terminal: tuple[int, int]
) -> tuple[tuple[Any, ...], Any]:
    values: list[Any] = []
    maximum_bound_error = np.float64(0.0)
    for state in coin_states(np, columns):
        probability = kernels.final_terminal_probability(
            state, terminal, np.float64(PROBABILITY_TOLERANCE)
        )
        if not bool(np.isfinite(probability)):
            raise DevelopmentSelectionError("terminal probability is non-finite")
        if bool(probability < np.float64(0.0)):
            bound_error = np.float64(-probability)
        elif bool(probability > np.float64(1.0)):
            bound_error = np.float64(probability - np.float64(1.0))
        else:
            bound_error = np.float64(0.0)
        if bool(np.signbit(bound_error)):
            raise DevelopmentSelectionError("probability bound error became negative zero")
        maximum_bound_error = np.maximum(maximum_bound_error, bound_error)
        values.append(np.float64(probability))
    return tuple(values), np.float64(maximum_bound_error)


def _positions(s: int, rows: int) -> tuple[tuple[int, int], ...]:
    return tuple((row, column) for row in range(rows) for column in range(s + 1))

def validate_direct_derived_sample(projection: dict[str, Any]) -> dict[str, Any]:
    """Run the immutable three-case, six-coin direct/derived T9 preflight."""
    np, kernels, _numerics = _load_numerical_modules()
    cases = (
        (2, 6, (0, 0), (0, 2)),
        (3, 6, (2, 1), (3, 0)),
        (4, 6, (5, 4), (4, 0)),
    )
    methods = ("candidate", "control-000", "control-004", "control-009", "control-099")
    vectors = coin_vectors(np)
    maximum_amplitude_error = np.float64(0.0)
    maximum_probability_error = np.float64(0.0)
    maximum_norm_drift = np.float64(0.0)
    comparison_count = 0
    for s, rows, start, terminal in cases:
        horizon = GRID_HORIZONS[(s, rows)]
        pairs_by_method = _pair_map(projection, s)
        definitions: list[tuple[str, int | None, int | None]] = [
            ("baseline", None, None)
        ]
        definitions.extend(
            (method, theta_index, phi_index)
            for method in methods
            for theta_index in range(6)
            for phi_index in range(4)
        )
        for method, theta_index, phi_index in definitions:
            pairs = None if method == "baseline" else pairs_by_method[method]
            theta, phi = (
                (None, None) if pairs is None
                else parameter_values(np, theta_index, phi_index)
            )
            columns, column_drift = _evolve_columns(
                np, kernels, initial_columns(np, s, rows, start), terminal,
                horizon, pairs, theta, phi,
            )
            maximum_norm_drift = np.maximum(maximum_norm_drift, column_drift)
            derived = coin_states(np, columns)
            for coin_index, vector in enumerate(vectors):
                direct = initial_direct(np, s, rows, start, vector)
                for _step in range(horizon):
                    direct = (
                        kernels.baseline_step(direct, terminal)
                        if pairs is None
                        else kernels.candidate_step(
                            direct, terminal, pairs, theta, phi
                        )
                    )
                    maximum_norm_drift = np.maximum(
                        maximum_norm_drift,
                        _direct_norm_drift(np, kernels, direct),
                    )
                error = np.float64(np.max(np.abs(direct - derived[coin_index])))
                if not bool(np.isfinite(error)) or bool(
                    error > np.float64(NORM_TOLERANCE)
                ):
                    raise DevelopmentSelectionError(
                        "direct/six-state amplitude validation failed"
                    )
                direct_probability = kernels.final_terminal_probability(
                    direct, terminal, np.float64(PROBABILITY_TOLERANCE)
                )
                derived_probability = kernels.final_terminal_probability(
                    derived[coin_index], terminal,
                    np.float64(PROBABILITY_TOLERANCE),
                )
                probability_error = np.float64(
                    abs(direct_probability - derived_probability)
                )
                if bool(probability_error > np.float64(NORM_TOLERANCE)):
                    raise DevelopmentSelectionError(
                        "direct/six-state probability validation failed"
                    )
                maximum_amplitude_error = np.maximum(
                    maximum_amplitude_error, error
                )
                maximum_probability_error = np.maximum(
                    maximum_probability_error, probability_error
                )
                comparison_count += 1
    return {
        "comparisons": comparison_count,
        "maximum_amplitude_error": np.float64(maximum_amplitude_error),
        "maximum_probability_error": np.float64(maximum_probability_error),
        "maximum_norm_drift": np.float64(maximum_norm_drift),
    }

def build_baseline_table() -> tuple[dict[str, Any], dict[str, Any]]:
    np, kernels, numerics = _load_numerical_modules()
    records: list[dict[str, Any]] = []
    maximum_norm_drift = np.float64(0.0)
    maximum_bound_error = np.float64(0.0)
    for s, rows in DEVELOPMENT_GRIDS:
        positions = _positions(s, rows)
        horizon = GRID_HORIZONS[(s, rows)]
        for start in positions:
            for terminal in positions:
                if terminal == start:
                    continue
                columns, drift = _evolve_columns(
                    np, kernels, initial_columns(np, s, rows, start), terminal,
                    horizon, None, None, None,
                )
                probabilities, bound_error = _probabilities(
                    np, kernels, columns, terminal
                )
                maximum_norm_drift = np.maximum(maximum_norm_drift, drift)
                maximum_bound_error = np.maximum(
                    maximum_bound_error, bound_error
                )
                records.append({
                    "R": rows,
                    "s": s,
                    "start": [start[0], start[1]],
                    "terminal": [terminal[0], terminal[1]],
                    "probabilities": [
                        numerics.canonical_float64(value)
                        for value in probabilities
                    ],
                })
    if len(records) != BASELINE_EVOLUTIONS:
        raise DevelopmentSelectionError("shared baseline count changed")
    table = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "dataset_kind": "development",
        "protocol_sha256": PROTOCOL_SHA256,
        "coin_order": list(COIN_ORDER),
        "grids": [
            {"s": s, "R": rows, "horizon": GRID_HORIZONS[(s, rows)]}
            for s, rows in DEVELOPMENT_GRIDS
        ],
        "record_count": len(records),
        "records": records,
    }
    invariants = {
        "maximum_norm_drift": np.float64(maximum_norm_drift),
        "maximum_probability_bound_error": np.float64(maximum_bound_error),
    }
    return table, invariants


def _load_baseline_lookup(path: Path) -> dict[tuple[int, int, int], tuple[Any, ...]]:
    np, _kernels, numerics = _load_numerical_modules()
    raw = path.read_bytes()
    try:
        table = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DevelopmentSelectionError("invalid baseline table") from exc
    if raw != canonical_json_bytes(table):
        raise DevelopmentSelectionError("baseline table is not canonical")
    if (
        table.get("schema_version") != BASELINE_SCHEMA_VERSION
        or table.get("dataset_kind") != "development"
        or table.get("protocol_sha256") != PROTOCOL_SHA256
        or table.get("coin_order") != list(COIN_ORDER)
        or table.get("record_count") != BASELINE_EVOLUTIONS
        or len(table.get("records", [])) != BASELINE_EVOLUTIONS
    ):
        raise DevelopmentSelectionError("baseline table metadata mismatch")
    result: dict[tuple[int, int, int], tuple[Any, ...]] = {}
    for record in table["records"]:
        if record["R"] != 6 or record["s"] not in (2, 3, 4):
            raise DevelopmentSelectionError("non-development baseline record")
        width = record["s"] + 1
        start_flat = record["start"][0] * width + record["start"][1]
        terminal_flat = record["terminal"][0] * width + record["terminal"][1]
        key = (record["s"], start_flat, terminal_flat)
        if key in result or start_flat == terminal_flat:
            raise DevelopmentSelectionError("duplicate or diagonal baseline record")
        probabilities = tuple(
            numerics.parse_canonical_float64(value)
            for value in record["probabilities"]
        )
        if len(probabilities) != len(COIN_ORDER):
            raise DevelopmentSelectionError("baseline coin count changed")
        result[key] = probabilities
    if len(result) != BASELINE_EVOLUTIONS:
        raise DevelopmentSelectionError("baseline lookup is incomplete")
    return result

def evaluate_group(
    task: GroupTask, projection: dict[str, Any],
    baseline: dict[tuple[int, int, int], tuple[Any, ...]],
) -> dict[str, Any]:
    np, kernels, numerics = _load_numerical_modules()
    if task.rows != 6 or (task.s, task.rows) not in DEVELOPMENT_GRIDS:
        raise DevelopmentSelectionError("group task is not development-only")
    theta, phi = parameter_values(np, task.theta_index, task.phi_index)
    pairs = _pair_map(projection, task.s)[task.family_id]
    positions = _positions(task.s, task.rows)
    width = task.s + 1
    lifts: list[Any] = []
    keys: list[str] = []
    maximum_norm_drift = np.float64(0.0)
    maximum_bound_error = np.float64(0.0)
    for start_flat, start in enumerate(positions):
        for terminal_flat, terminal in enumerate(positions):
            if terminal == start:
                continue
            baseline_probabilities = baseline.get(
                (task.s, start_flat, terminal_flat)
            )
            if baseline_probabilities is None:
                raise DevelopmentSelectionError("missing shared baseline record")
            columns, drift = _evolve_columns(
                np, kernels, initial_columns(np, task.s, task.rows, start),
                terminal, task.horizon, pairs, theta, phi,
            )
            probabilities, bound_error = _probabilities(
                np, kernels, columns, terminal
            )
            maximum_norm_drift = np.maximum(maximum_norm_drift, drift)
            maximum_bound_error = np.maximum(
                maximum_bound_error, bound_error
            )
            for coin, probability, baseline_probability in zip(
                COIN_ORDER, probabilities, baseline_probabilities
            ):
                lifts.append(numerics.subtract_float64(
                    probability, baseline_probability, "development lift"
                ))
                keys.append(micro_case_key(
                    task.s, task.rows, start, terminal, coin
                ))
    expected = GRID_PAIR_COUNTS[(task.s, task.rows)] * len(COIN_ORDER)
    if len(lifts) != expected or len(set(keys)) != expected:
        raise DevelopmentSelectionError("group micro-case coverage changed")
    median = numerics.frozen_median(lifts, keys)
    q10 = numerics.frozen_quantile_10(lifts, keys)
    return {
        "ordinal": task.ordinal,
        "family_id": task.family_id,
        "theta_index": task.theta_index,
        "phi_index": task.phi_index,
        "s": task.s,
        "R": task.rows,
        "horizon": task.horizon,
        "micro_case_count": expected,
        "median_lift": numerics.canonical_float64(median),
        "q10_lift": numerics.canonical_float64(q10),
        "maximum_norm_drift": numerics.canonical_float64(
            np.float64(maximum_norm_drift)
        ),
        "maximum_probability_bound_error": numerics.canonical_float64(
            np.float64(maximum_bound_error)
        ),
    }


def _worker_main(
    worker_id: int, tasks: tuple[GroupTask, ...], projection_path: str,
    baseline_path: str, readiness_directory: str, result_path: str,
) -> None:
    readiness = Path(readiness_directory)
    try:
        np, _kernels, _numerics = _load_numerical_modules()
        pools = runtime.inspect_thread_pools()
        projection = development_manifest.load_projection(projection_path)
        baseline = _load_baseline_lookup(Path(baseline_path))
        ready = readiness / f"worker-{worker_id}-{os.getpid()}.ready"
        ready.write_bytes(canonical_json_bytes({
            "worker": worker_id,
            "pid": os.getpid(),
            "numpy_version": np.__version__,
            "thread_pools": list(pools),
        }))
        deadline = time.monotonic() + 60.0
        while len(tuple(readiness.glob("*.ready"))) != WORKER_COUNT:
            if time.monotonic() >= deadline:
                raise DevelopmentSelectionError("four-worker readiness timed out")
            time.sleep(0.02)
        print(
            f"T9_WORKER_READY worker={worker_id} pid={os.getpid()} "
            f"groups={len(tasks)}", flush=True,
        )
        with Path(result_path).open("wb") as output:
            for index, task in enumerate(tasks, start=1):
                output.write(canonical_json_bytes(
                    evaluate_group(task, projection, baseline)
                ))
                if index % 100 == 0 or index == len(tasks):
                    output.flush()
                    print(
                        f"T9_WORKER_PROGRESS worker={worker_id} "
                        f"completed={index}/{len(tasks)}", flush=True,
                    )
    except BaseException:
        error_path = readiness / f"worker-{worker_id}.error"
        error_path.write_text(traceback.format_exc(), encoding="utf-8")
        traceback.print_exc()
        raise

def _decode_group_stream(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise DevelopmentSelectionError("worker stream lacks final LF")
    for line_number, line in enumerate(raw.splitlines(), start=1):
        try:
            record = json.loads(line.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DevelopmentSelectionError(
                f"invalid worker record at line {line_number}"
            ) from exc
        if canonical_json_bytes(record) != line + b"\n":
            raise DevelopmentSelectionError("worker record is not canonical")
        result.append(record)
    return result


def deterministic_group_bytes(records: Iterable[dict[str, Any]]) -> bytes:
    materialized = sorted(records, key=lambda record: record["ordinal"])
    if [record["ordinal"] for record in materialized] != list(
        range(len(materialized))
    ):
        raise DevelopmentSelectionError("group records are missing or duplicated")
    return b"".join(canonical_json_bytes(record) for record in materialized)


def run_workers(
    tasks: tuple[GroupTask, ...], projection_path: Path, baseline_path: Path,
    staging: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(tasks) != GROUP_TASK_COUNT:
        raise DevelopmentSelectionError("full T9 requires every group task")
    readiness = staging / "worker-status"
    readiness.mkdir()
    assignments = tuple(
        tuple(task for task in tasks if task.ordinal % WORKER_COUNT == worker)
        for worker in range(WORKER_COUNT)
    )
    result_paths = tuple(
        staging / f"worker-{worker}-groups.jsonl"
        for worker in range(WORKER_COUNT)
    )
    context = multiprocessing.get_context("spawn")
    processes = [
        context.Process(
            target=_worker_main,
            name=f"area-one-t9-worker-{worker}",
            args=(
                worker, assignments[worker], str(projection_path),
                str(baseline_path), str(readiness), str(result_paths[worker]),
            ),
        )
        for worker in range(WORKER_COUNT)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    failures = [
        f"{process.name}:{process.exitcode}"
        for process in processes if process.exitcode != 0
    ]
    if failures:
        details = []
        for path in sorted(readiness.glob("*.error")):
            details.append(path.read_text(encoding="utf-8", errors="replace"))
        raise DevelopmentSelectionError(
            "worker failure " + ",".join(failures) + "\n" + "\n".join(details)
        )
    ready_files = sorted(readiness.glob("*.ready"))
    if len(ready_files) != WORKER_COUNT:
        raise DevelopmentSelectionError("exactly four worker readiness records required")
    diagnostics = [json.loads(path.read_text(encoding="utf-8")) for path in ready_files]
    if len({item["pid"] for item in diagnostics}) != WORKER_COUNT:
        raise DevelopmentSelectionError("four distinct worker processes were not used")
    records: list[dict[str, Any]] = []
    for path in result_paths:
        records.extend(_decode_group_stream(path))
    records.sort(key=lambda record: record["ordinal"])
    deterministic_group_bytes(records)
    if len(records) != GROUP_TASK_COUNT:
        raise DevelopmentSelectionError("worker group result count mismatch")
    return records, diagnostics

def aggregate_group_records(
    records: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, dict[str, Any]]:
    np, _kernels, numerics = _load_numerical_modules()
    tasks = build_group_tasks()
    if len(records) != len(tasks):
        raise DevelopmentSelectionError("aggregation requires all 7,272 groups")
    parsed: dict[tuple[str, int, int, int, int], tuple[Any, Any]] = {}
    maximum_norm_drift = np.float64(0.0)
    maximum_bound_error = np.float64(0.0)
    expected_fields = {
        "ordinal", "family_id", "theta_index", "phi_index", "s", "R",
        "horizon", "micro_case_count", "median_lift", "q10_lift",
        "maximum_norm_drift", "maximum_probability_bound_error",
    }
    for expected, record in zip(tasks, records):
        if not isinstance(record, dict) or set(record) != expected_fields:
            raise DevelopmentSelectionError("group record fields changed")
        identity = (
            record["ordinal"], record["family_id"], record["theta_index"],
            record["phi_index"], record["s"], record["R"], record["horizon"],
        )
        expected_identity = (
            expected.ordinal, expected.family_id, expected.theta_index,
            expected.phi_index, expected.s, expected.rows, expected.horizon,
        )
        if identity != expected_identity:
            raise DevelopmentSelectionError("group record order or identity changed")
        expected_cases = GRID_PAIR_COUNTS[(expected.s, expected.rows)] * 6
        if record["micro_case_count"] != expected_cases:
            raise DevelopmentSelectionError("group micro-case count changed")
        median = numerics.parse_canonical_float64(record["median_lift"])
        q10 = numerics.parse_canonical_float64(record["q10_lift"])
        drift = numerics.parse_canonical_float64(record["maximum_norm_drift"])
        bound_error = numerics.parse_canonical_float64(
            record["maximum_probability_bound_error"]
        )
        if bool(drift > np.float64(NORM_TOLERANCE)) or bool(
            bound_error > np.float64(PROBABILITY_TOLERANCE)
        ):
            raise DevelopmentSelectionError("group invariant exceeded tolerance")
        maximum_norm_drift = np.maximum(maximum_norm_drift, drift)
        maximum_bound_error = np.maximum(maximum_bound_error, bound_error)
        key = (
            expected.family_id, expected.theta_index, expected.phi_index,
            expected.s, expected.rows,
        )
        if key in parsed:
            raise DevelopmentSelectionError("duplicate group result")
        parsed[key] = (median, q10)
    parameter_scores: list[dict[str, Any]] = []
    score_objects: dict[str, list[Any]] = {family_id: [] for family_id in METHOD_ORDER}
    for family_id in METHOD_ORDER:
        for theta_index in range(6):
            for phi_index in range(4):
                medians: list[Any] = []
                grid_keys: list[str] = []
                quantiles: dict[tuple[int, int], Any] = {}
                grid_metrics: list[dict[str, Any]] = []
                for s, rows in DEVELOPMENT_GRIDS:
                    median, q10 = parsed[
                        (family_id, theta_index, phi_index, s, rows)
                    ]
                    medians.append(median)
                    grid_keys.append(json.dumps([s, rows], separators=(",", ":")))
                    quantiles[(s, rows)] = q10
                    grid_metrics.append({
                        "s": s,
                        "R": rows,
                        "horizon": GRID_HORIZONS[(s, rows)],
                        "micro_case_count": GRID_PAIR_COUNTS[(s, rows)] * 6,
                        "median_lift": numerics.canonical_float64(median),
                        "q10_lift": numerics.canonical_float64(q10),
                    })
                aggregate = numerics.frozen_median(medians, grid_keys)
                score = numerics.ParameterScore(
                    quantiles, aggregate, theta_index, phi_index
                )
                score_objects[family_id].append(score)
                parameter_scores.append({
                    "family_id": family_id,
                    "theta_index": theta_index,
                    "phi_index": phi_index,
                    "theta_pi_numerator": THETA_NUMERATORS[theta_index],
                    "theta_pi_denominator": 16,
                    "phi_pi_numerator": PHI_NUMERATORS[phi_index],
                    "phi_pi_denominator": 2,
                    "grid_metrics": grid_metrics,
                    "aggregate_median": numerics.canonical_float64(aggregate),
                    "minimum_grid_q10": numerics.canonical_float64(
                        score.minimum_grid_quantile
                    ),
                    "feasible": score.feasible,
                })
    winners: list[dict[str, Any]] = []
    for family_id in METHOD_ORDER:
        winner = numerics.select_parameter(score_objects[family_id])
        winners.append({
            "family_id": family_id,
            "theta_index": winner.theta_index,
            "phi_index": winner.phi_index,
            "theta_pi_numerator": THETA_NUMERATORS[winner.theta_index],
            "theta_pi_denominator": 16,
            "phi_pi_numerator": PHI_NUMERATORS[winner.phi_index],
            "phi_pi_denominator": 2,
            "aggregate_median": numerics.canonical_float64(
                winner.aggregate_median
            ),
            "minimum_grid_q10": numerics.canonical_float64(
                winner.minimum_grid_quantile
            ),
            "feasible": winner.feasible,
        })
    candidate_status = "feasible" if winners[0]["feasible"] else "rejected"
    invariants = {
        "maximum_norm_drift": np.float64(maximum_norm_drift),
        "maximum_probability_bound_error": np.float64(maximum_bound_error),
    }
    if len(parameter_scores) != 2_424 or len(winners) != 101:
        raise DevelopmentSelectionError("selection completeness changed")
    return parameter_scores, winners, candidate_status, invariants


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return type(value) is int
    if expected == "boolean":
        return type(value) is bool
    if expected == "null":
        return value is None
    return False


def _validate_schema_node(
    value: Any, schema: dict[str, Any], root: dict[str, Any], location: str
) -> None:
    reference = schema.get("$ref")
    if reference is not None:
        if not isinstance(reference, str) or not reference.startswith("#/$defs/"):
            raise DevelopmentSelectionError("selection schema has an unsafe reference")
        name = reference.removeprefix("#/$defs/")
        target = root.get("$defs", {}).get(name)
        if not isinstance(target, dict):
            raise DevelopmentSelectionError("selection schema reference is missing")
        _validate_schema_node(value, target, root, location)
        return
    expected_type = schema.get("type")
    if expected_type is not None and not _schema_type_matches(value, expected_type):
        raise DevelopmentSelectionError(f"{location} has the wrong schema type")
    if "const" in schema and value != schema["const"]:
        raise DevelopmentSelectionError(f"{location} does not match schema const")
    if "enum" in schema and value not in schema["enum"]:
        raise DevelopmentSelectionError(f"{location} is outside schema enum")
    if isinstance(value, dict):
        required = schema.get("required", [])
        if any(not isinstance(name, str) for name in required):
            raise DevelopmentSelectionError("selection schema required list is invalid")
        missing = set(required) - set(value)
        if missing:
            raise DevelopmentSelectionError(
                f"{location} misses schema fields {sorted(missing)}"
            )
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                raise DevelopmentSelectionError(
                    f"{location} has unknown schema fields {sorted(unknown)}"
                )
        for name, child in value.items():
            child_schema = properties.get(name)
            if child_schema is not None:
                _validate_schema_node(
                    child, child_schema, root, f"{location}.{name}"
                )
    if isinstance(value, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if minimum is not None and len(value) < minimum:
            raise DevelopmentSelectionError(f"{location} has too few items")
        if maximum is not None and len(value) > maximum:
            raise DevelopmentSelectionError(f"{location} has too many items")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, child in enumerate(value):
                _validate_schema_node(
                    child, item_schema, root, f"{location}[{index}]"
                )
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise DevelopmentSelectionError(f"{location} is too short")
        pattern = schema.get("pattern")
        if pattern is not None and re.fullmatch(pattern, value) is None:
            raise DevelopmentSelectionError(f"{location} does not match schema pattern")
    if type(value) is int:
        if "minimum" in schema and value < schema["minimum"]:
            raise DevelopmentSelectionError(f"{location} is below schema minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise DevelopmentSelectionError(f"{location} is above schema maximum")


def _load_and_apply_selection_schema(artifact: dict[str, Any]) -> None:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DevelopmentSelectionError("development selection schema is unreadable") from exc
    if (
        not isinstance(schema, dict)
        or schema.get("$id") != SCHEMA_VERSION
        or schema.get("additionalProperties") is not False
    ):
        raise DevelopmentSelectionError("development selection schema identity changed")
    _validate_schema_node(artifact, schema, schema, "selection")


def _expected_parameter_order() -> list[dict[str, int]]:
    return [
        {
            "theta_index": theta_index,
            "phi_index": phi_index,
            "theta_pi_numerator": THETA_NUMERATORS[theta_index],
            "theta_pi_denominator": 16,
            "phi_pi_numerator": PHI_NUMERATORS[phi_index],
            "phi_pi_denominator": 2,
        }
        for theta_index in range(6)
        for phi_index in range(4)
    ]


def _expected_grid_records() -> list[dict[str, int]]:
    return [
        {
            "s": s,
            "R": rows,
            "positions": rows * (s + 1),
            "horizon": GRID_HORIZONS[(s, rows)],
            "ordered_pairs": GRID_PAIR_COUNTS[(s, rows)],
            "micro_cases": GRID_PAIR_COUNTS[(s, rows)] * 6,
        }
        for s, rows in DEVELOPMENT_GRIDS
    ]


def _validate_embedded_baseline(wrapper: dict[str, Any], numerics: Any) -> None:
    np = importlib.import_module("numpy")
    content = wrapper["content"]
    encoded = canonical_json_bytes(content)
    if wrapper["canonical_sha256"] != sha256_bytes(encoded):
        raise DevelopmentSelectionError("embedded baseline hash mismatch")
    if wrapper["canonical_byte_size"] != len(encoded):
        raise DevelopmentSelectionError("embedded baseline byte size mismatch")
    if set(content) != {
        "schema_version", "dataset_kind", "protocol_sha256", "coin_order",
        "grids", "record_count", "records",
    }:
        raise DevelopmentSelectionError("embedded baseline fields are not closed")
    if (
        content["schema_version"] != BASELINE_SCHEMA_VERSION
        or content["dataset_kind"] != "development"
        or content["protocol_sha256"] != PROTOCOL_SHA256
        or content["coin_order"] != list(COIN_ORDER)
        or content["grids"] != [
            {"s": s, "R": rows, "horizon": GRID_HORIZONS[(s, rows)]}
            for s, rows in DEVELOPMENT_GRIDS
        ]
        or content["record_count"] != BASELINE_EVOLUTIONS
        or len(content["records"]) != BASELINE_EVOLUTIONS
    ):
        raise DevelopmentSelectionError("embedded baseline metadata mismatch")
    expected_keys = []
    for s, rows in DEVELOPMENT_GRIDS:
        for start in _positions(s, rows):
            for terminal in _positions(s, rows):
                if terminal != start:
                    expected_keys.append((s, rows, start, terminal))
    np, kernels, _unused_numerics = _load_numerical_modules()
    maximum_reconstruction_drift = np.float64(0.0)
    for expected, record in zip(expected_keys, content["records"]):
        s, rows, start, terminal = expected
        if set(record) != {"s", "R", "start", "terminal", "probabilities"}:
            raise DevelopmentSelectionError("embedded baseline record is not closed")
        if (
            record["s"] != s or record["R"] != rows
            or record["start"] != [start[0], start[1]]
            or record["terminal"] != [terminal[0], terminal[1]]
            or len(record["probabilities"]) != 6
        ):
            raise DevelopmentSelectionError("embedded baseline record order changed")
        for text in record["probabilities"]:
            probability = numerics.parse_canonical_float64(text)
            if probability < np.float64(-PROBABILITY_TOLERANCE) or probability > np.float64(1.0 + PROBABILITY_TOLERANCE):
                raise DevelopmentSelectionError("embedded baseline probability is invalid")
        columns, drift = _evolve_columns(
            np, kernels, initial_columns(np, s, rows, start), terminal,
            GRID_HORIZONS[(s, rows)], None, None, None,
        )
        reconstructed, _bound_error = _probabilities(
            np, kernels, columns, terminal
        )
        expected_probabilities = [
            numerics.canonical_float64(value) for value in reconstructed
        ]
        if record["probabilities"] != expected_probabilities:
            raise DevelopmentSelectionError(
                "embedded baseline probability reconstruction mismatch"
            )
        maximum_reconstruction_drift = np.maximum(
            maximum_reconstruction_drift, drift
        )
    if bool(maximum_reconstruction_drift > np.float64(NORM_TOLERANCE)):
        raise DevelopmentSelectionError("baseline reconstruction norm drift failed")


def validate_selection_artifact(artifact: dict[str, Any]) -> None:
    _load_and_apply_selection_schema(artifact)
    np, _kernels, numerics = _load_numerical_modules()
    projection = development_manifest.load_projection(DEVELOPMENT_MANIFEST_PATH)
    if (
        artifact["schema_version"] != SCHEMA_VERSION
        or artifact["dataset_kind"] != "development"
        or artifact["protocol_sha256"] != PROTOCOL_SHA256
        or artifact["source_manifest_hash"] != development_manifest.SOURCE_MANIFEST_HASH
        or artifact["development_manifest_hash"] != projection["projection_hash"]
        or artifact["grids"] != _expected_grid_records()
        or artifact["coin_order"] != list(COIN_ORDER)
        or artifact["parameter_order"] != _expected_parameter_order()
        or artifact["method_order"] != list(METHOD_ORDER)
        or artifact["counts"] != development_plan()
    ):
        raise DevelopmentSelectionError("selection artifact semantic binding mismatch")
    runtime_record = artifact["runtime"]
    worker_records = runtime_record["worker_diagnostics"]
    if (
        sorted(record["worker"] for record in worker_records) != list(range(4))
        or len({record["pid"] for record in worker_records}) != 4
        or any(
            pool["num_threads"] != 1
            for record in worker_records for pool in record["thread_pools"]
        )
    ):
        raise DevelopmentSelectionError("worker runtime evidence is inconsistent")
    scores = artifact["parameter_scores"]
    expected_order = [
        (family_id, theta_index, phi_index)
        for family_id in METHOD_ORDER
        for theta_index in range(6)
        for phi_index in range(4)
    ]
    if [
        (record["family_id"], record["theta_index"], record["phi_index"])
        for record in scores
    ] != expected_order:
        raise DevelopmentSelectionError("parameter score order changed")
    score_objects: dict[str, list[Any]] = {family_id: [] for family_id in METHOD_ORDER}
    score_records: dict[tuple[str, int, int], dict[str, Any]] = {}
    for record in scores:
        family_id = record["family_id"]
        theta_index = record["theta_index"]
        phi_index = record["phi_index"]
        parameter = _expected_parameter_order()[theta_index * 4 + phi_index]
        if any(record[name] != value for name, value in parameter.items()):
            raise DevelopmentSelectionError("parameter score index encoding changed")
        expected_metrics = []
        medians = []
        median_keys = []
        quantiles = {}
        for metric, (s, rows) in zip(record["grid_metrics"], DEVELOPMENT_GRIDS):
            if (
                metric["s"] != s or metric["R"] != rows
                or metric["horizon"] != GRID_HORIZONS[(s, rows)]
                or metric["micro_case_count"] != GRID_PAIR_COUNTS[(s, rows)] * 6
            ):
                raise DevelopmentSelectionError("parameter grid metric order changed")
            median = numerics.parse_canonical_float64(metric["median_lift"])
            q10 = numerics.parse_canonical_float64(metric["q10_lift"])
            medians.append(median)
            median_keys.append(json.dumps([s, rows], separators=(",", ":")))
            quantiles[(s, rows)] = q10
            expected_metrics.append(metric)
        aggregate = numerics.frozen_median(medians, median_keys)
        score = numerics.ParameterScore(quantiles, aggregate, theta_index, phi_index)
        if (
            record["aggregate_median"] != numerics.canonical_float64(aggregate)
            or record["minimum_grid_q10"] != numerics.canonical_float64(score.minimum_grid_quantile)
            or record["feasible"] is not score.feasible
        ):
            raise DevelopmentSelectionError("parameter score was not reconstructed")
        score_objects[family_id].append(score)
        score_records[(family_id, theta_index, phi_index)] = record
    winners = artifact["winners"]
    if [record["family_id"] for record in winners] != list(METHOD_ORDER):
        raise DevelopmentSelectionError("winner order changed")
    for record in winners:
        family_id = record["family_id"]
        selected = numerics.select_parameter(score_objects[family_id])
        source = score_records[(family_id, selected.theta_index, selected.phi_index)]
        expected = {
            "family_id": family_id,
            "theta_index": selected.theta_index,
            "phi_index": selected.phi_index,
            "theta_pi_numerator": source["theta_pi_numerator"],
            "theta_pi_denominator": 16,
            "phi_pi_numerator": source["phi_pi_numerator"],
            "phi_pi_denominator": 2,
            "aggregate_median": source["aggregate_median"],
            "minimum_grid_q10": source["minimum_grid_q10"],
            "feasible": source["feasible"],
        }
        if record != expected:
            raise DevelopmentSelectionError("winner was not reconstructed")
    expected_status = "feasible" if winners[0]["feasible"] else "rejected"
    if artifact["candidate_status"] != expected_status:
        raise DevelopmentSelectionError("candidate status is inconsistent")
    invariants = artifact["invariants"]
    for name in (
        "maximum_norm_drift", "maximum_probability_bound_error",
        "maximum_direct_derived_amplitude_error",
        "maximum_direct_derived_probability_error",
    ):
        value = numerics.parse_canonical_float64(invariants[name])
        if value < np.float64(0.0) or value > np.float64(1.0e-12):
            raise DevelopmentSelectionError("selection invariant exceeded tolerance")
    if invariants["direct_derived_comparisons"] != 2_178:
        raise DevelopmentSelectionError("direct/derived coverage changed")
    _validate_embedded_baseline(artifact["baseline_table"], numerics)

def _durable_write(path: Path, data: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _sync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_publish(directory: Path, filename: str, data: bytes) -> Path:
    final = directory / filename
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{filename}.", suffix=".tmp", dir=directory
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, final)
        _sync_directory(directory)
        return final
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def run_development_selection(output_directory: Path, workers: int) -> dict[str, Any]:
    if type(workers) is not int or workers != WORKER_COUNT:
        raise DevelopmentSelectionError("T9 requires exactly four workers")
    output = _require_empty_output_directory(output_directory)
    expected_digest = os.environ.get("AREA_ONE_EXPECTED_OCI_DIGEST")
    actual_digest = os.environ.get("AREA_ONE_ACTUAL_OCI_DIGEST")
    if expected_digest is None or actual_digest is None:
        raise DevelopmentSelectionError(
            "AREA_ONE_EXPECTED_OCI_DIGEST and AREA_ONE_ACTUAL_OCI_DIGEST are required"
        )
    pre_numpy = runtime.bootstrap_runtime(
        expected_digest, actual_digest, workers
    )
    diagnostics = runtime.complete_diagnostics(pre_numpy)
    print("T9_START development_only=true", flush=True)
    projection = verify_frozen_inputs()
    print(
        f"T9_PREFLIGHT_PASS protocol={PROTOCOL_SHA256} "
        f"projection={projection['projection_hash']}", flush=True,
    )
    staging = Path(tempfile.mkdtemp(
        prefix=".area-one-t9-", dir=output.parent
    ))
    result_final = output / RESULT_FILENAME
    try:
        print("T9_DIRECT_DERIVED_START comparisons=2178", flush=True)
        direct_evidence = validate_direct_derived_sample(projection)
        print("T9_DIRECT_DERIVED_PASS comparisons=2178", flush=True)
        print(f"T9_BASELINE_START evolutions={BASELINE_EVOLUTIONS}", flush=True)
        baseline_table, baseline_invariants = build_baseline_table()
        baseline_bytes = canonical_json_bytes(baseline_table)
        baseline_stage = staging / BASELINE_FILENAME
        _durable_write(baseline_stage, baseline_bytes)
        baseline_hash = sha256_bytes(baseline_bytes)
        print(
            f"T9_BASELINE_PASS evolutions={BASELINE_EVOLUTIONS} "
            f"sha256={baseline_hash}", flush=True,
        )
        tasks = build_group_tasks()
        print(
            f"T9_WORKERS_START workers={WORKER_COUNT} groups={len(tasks)} "
            f"paired_evolutions={PAIRED_EVOLUTIONS}", flush=True,
        )
        records, worker_diagnostics = run_workers(
            tasks, DEVELOPMENT_MANIFEST_PATH, baseline_stage, staging
        )
        print("T9_WORKERS_PASS groups=7272", flush=True)
        scores, winners, candidate_status, worker_invariants = (
            aggregate_group_records(records)
        )
        np, _kernels, numerics = _load_numerical_modules()
        maximum_norm_drift = np.maximum.reduce(np.array((
            baseline_invariants["maximum_norm_drift"],
            direct_evidence["maximum_norm_drift"],
            worker_invariants["maximum_norm_drift"],
        ), dtype=np.float64))
        maximum_bound_error = np.maximum(
            baseline_invariants["maximum_probability_bound_error"],
            worker_invariants["maximum_probability_bound_error"],
        )
        parameter_order = _expected_parameter_order()
        artifact = {
            "schema_version": SCHEMA_VERSION,
            "dataset_kind": "development",
            "protocol_sha256": PROTOCOL_SHA256,
            "source_manifest_hash": development_manifest.SOURCE_MANIFEST_HASH,
            "development_manifest_hash": projection["projection_hash"],
            "runtime": {
                **diagnostics,
                "worker_diagnostics": worker_diagnostics,
            },
            "grids": _expected_grid_records(),
            "coin_order": list(COIN_ORDER),
            "parameter_order": parameter_order,
            "method_order": list(METHOD_ORDER),
            "counts": development_plan(),
            "parameter_scores": scores,
            "winners": winners,
            "candidate_status": candidate_status,
            "invariants": {
                "maximum_norm_drift": numerics.canonical_float64(
                    np.float64(maximum_norm_drift)
                ),
                "maximum_probability_bound_error": numerics.canonical_float64(
                    np.float64(maximum_bound_error)
                ),
                "maximum_direct_derived_amplitude_error": numerics.canonical_float64(
                    direct_evidence["maximum_amplitude_error"]
                ),
                "maximum_direct_derived_probability_error": numerics.canonical_float64(
                    direct_evidence["maximum_probability_error"]
                ),
                "direct_derived_comparisons": direct_evidence["comparisons"],
            },
            "baseline_table": {
                "canonical_sha256": baseline_hash,
                "canonical_byte_size": len(baseline_bytes),
                "content": baseline_table,
            },
        }
        validate_selection_artifact(artifact)
        result_bytes = canonical_json_bytes(artifact)
        _atomic_publish(output, RESULT_FILENAME, result_bytes)
        result_hash = sha256_bytes(result_bytes)
        print(
            f"T9_SELECTION_PASS scores={len(scores)} winners={len(winners)}",
            flush=True,
        )
        print(f"candidate_status={candidate_status}", flush=True)
        print(
            f"candidate_theta_index={winners[0]['theta_index']} "
            f"candidate_phi_index={winners[0]['phi_index']}", flush=True,
        )
        print(f"result_sha256={result_hash}", flush=True)
        print(f"baseline_sha256={baseline_hash}", flush=True)
        print("T9_COMPLETE no_lock=true heldout_executed=false", flush=True)
        return artifact
    except BaseException:
        try:
            result_final.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-only", action="store_true")
    mode.add_argument("--development-only", action="store_true")
    parser.add_argument("--workers", type=int)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.plan_only:
            if args.output is not None or args.workers is not None:
                raise DevelopmentSelectionError(
                    "--plan-only does not accept --output or --workers"
                )
            print_plan()
            return 0
        if args.workers is None or args.output is None:
            raise DevelopmentSelectionError(
                "--development-only requires --workers 4 and --output"
            )
        run_development_selection(args.output, args.workers)
        return 0
    except (
        OSError, RuntimeError, DevelopmentSelectionError,
        development_manifest.DevelopmentManifestError,
        matching_control_manifest.ManifestValidationError,
        protocol_approval_anchor.ProtocolAnchorError,
        independent_protocol_anchor.IndependentAnchorError,
    ) as exc:
        print(f"T9_FAILED error={exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
