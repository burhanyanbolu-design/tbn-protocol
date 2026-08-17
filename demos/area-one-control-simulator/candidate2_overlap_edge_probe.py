#!/usr/bin/env python3
"""Development-only Candidate 2 dedicated overlap-edge discovery probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing
import os
import platform
import sys
from pathlib import Path
from typing import Any, Sequence

import pair_scatter_development_selection as selection

SCHEMA_VERSION = "area-one-candidate2-overlap-edge-probe/1.0"
RESULT_FILENAME = "candidate2-overlap-edge-probe.json"
EXPECTED_IMAGE = "sha256:96379ff14fb29df67b28c19102d93cb1cc912e23962e0c917b5209b605edb3f2"
EXPECTED_CONTAINER = "area-one-candidate2-overlap-edge-probe"
WORKERS = 4
TOLERANCE = 1.0e-12
OVERLAP = 4
_BASELINE: dict[tuple[int, int, int], tuple[Any, ...]] = {}
_READY_QUEUE: Any = None


def _fail(message: str) -> None:
    raise selection.DevelopmentSelectionError(message)


def _require_finite(np: Any, value: Any, name: str) -> None:
    if not bool(np.isfinite(value).all()):
        _fail(f"{name} became non-finite")


def _pairs(s: int, rows: int) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    return tuple(((row, s), (row + 1, 0)) for row in range(rows - 1))

def _initial_columns(np: Any, s: int, rows: int, start: tuple[int, int]) -> Any:
    state = np.zeros((rows, s + 1, 5, 4), dtype=np.complex128, order="C")
    for direction in range(4):
        state[start[0], start[1], direction, direction] = np.complex128(1.0)
    return state


def _coin_vectors(np: Any) -> tuple[Any, ...]:
    vectors = [np.array((0.5, 0.5, 0.5, 0.5, 0.0), dtype=np.complex128)]
    for direction in range(4):
        vector = np.zeros(5, dtype=np.complex128)
        vector[direction] = np.complex128(1.0)
        vectors.append(vector)
    vectors.append(np.array((0.5, 0.5j, -0.5, -0.5j, 0.0), dtype=np.complex128))
    return tuple(vectors)


def _initial_direct(
    np: Any, s: int, rows: int, start: tuple[int, int], vector: Any
) -> Any:
    state = np.zeros((rows, s + 1, 5), dtype=np.complex128, order="C")
    state[start[0], start[1], :] = vector
    return state


def _coin_states(np: Any, columns: Any) -> tuple[Any, ...]:
    directional = tuple(columns[:, :, :, index] for index in range(4))
    uniform = np.ascontiguousarray(sum(directional) * np.float64(0.5), dtype=np.complex128)
    phase_balanced = np.ascontiguousarray(
        (directional[0] + np.complex128(1j) * directional[1]
         - directional[2] - np.complex128(1j) * directional[3]) * np.float64(0.5),
        dtype=np.complex128,
    )
    return (uniform,) + tuple(
        np.ascontiguousarray(value, dtype=np.complex128) for value in directional
    ) + (phase_balanced,)


def _oracle(np: Any, state: Any, terminal: tuple[int, int]) -> Any:
    result = state.copy(order="C")
    result[terminal[0], terminal[1], ...] *= np.complex128(-1.0)
    _require_finite(np, result, "five-state oracle")
    return result


def _c0(np: Any, kernels: Any, state: Any) -> Any:
    ordinary = kernels.grover_coin(np.ascontiguousarray(state[:, :, :4, ...]))
    result = state.copy(order="C")
    result[:, :, :4, ...] = ordinary
    _require_finite(np, result, "C_0")
    return result


def _local_rotation(
    np: Any, state: Any, pairs: tuple[Any, ...], alpha: Any, beta: Any
) -> Any:
    endpoints = tuple(position for pair in pairs for position in pair)
    if len(endpoints) != 2 * len(pairs) or len(set(endpoints)) != len(endpoints):
        _fail("overlap rotation endpoints are not disjoint")
    cosine = np.float64(np.cos(np.float64(alpha)))
    sine = np.float64(np.sin(np.float64(alpha)))
    phase = np.complex128(
        np.float64(np.cos(np.float64(beta)))
        + np.complex128(1j) * np.float64(np.sin(np.float64(beta)))
    )
    result = state.copy(order="C")
    for row, column in endpoints:
        ordinary = state[row, column, :4, ...]
        overlap = state[row, column, OVERLAP, ...]
        u_coefficient = np.sum(ordinary, axis=0, dtype=np.complex128) * np.float64(0.5)
        new_u = cosine * u_coefficient - np.conjugate(phase) * sine * overlap
        new_overlap = phase * sine * u_coefficient + cosine * overlap
        result[row, column, :4, ...] = ordinary + (new_u - u_coefficient) * np.float64(0.5)
        result[row, column, OVERLAP, ...] = new_overlap
    _require_finite(np, result, "R_X")
    return result

def _shift(np: Any, kernels: Any, state: Any, pairs: tuple[Any, ...]) -> Any:
    ordinary = kernels.periodic_flip_flop_shift(
        np.ascontiguousarray(state[:, :, :4, ...], dtype=np.complex128)
    )
    result = state.copy(order="C")
    result[:, :, :4, ...] = ordinary
    for left, right in pairs:
        result[left[0], left[1], OVERLAP, ...] = state[right[0], right[1], OVERLAP, ...]
        result[right[0], right[1], OVERLAP, ...] = state[left[0], left[1], OVERLAP, ...]
    _require_finite(np, result, "S_X")
    return result


def _step(
    np: Any, kernels: Any, state: Any, terminal: tuple[int, int],
    pairs: tuple[Any, ...], alpha: Any, beta: Any,
) -> Any:
    # Operators act right-to-left: S_X R_X C_0 O_t.
    state = _oracle(np, state, terminal)
    state = _c0(np, kernels, state)
    state = _local_rotation(np, state, pairs, alpha, beta)
    return _shift(np, kernels, state, pairs)


def _norm_drift(np: Any, state: Any) -> Any:
    _require_finite(np, state, "trajectory")
    squared = state.real * state.real + state.imag * state.imag
    if state.ndim == 4:
        norms = np.sum(squared, axis=(0, 1, 2), dtype=np.float64)
        drift = np.float64(np.max(np.abs(norms - np.float64(1.0))))
    else:
        drift = np.float64(abs(np.sum(squared, dtype=np.float64) - np.float64(1.0)))
    if not bool(np.isfinite(drift)) or bool(drift > np.float64(TOLERANCE)):
        _fail("trajectory norm drift exceeded 1e-12")
    return drift


def _probability(np: Any, state: Any, terminal: tuple[int, int]) -> tuple[Any, Any]:
    amplitudes = state[terminal[0], terminal[1], ...]
    probability = np.float64(np.sum(
        amplitudes.real * amplitudes.real + amplitudes.imag * amplitudes.imag,
        dtype=np.float64,
    ))
    if not bool(np.isfinite(probability)):
        _fail("terminal probability became non-finite")
    bound_error = np.float64(max(0.0, -float(probability), float(probability - 1.0)))
    if bool(bound_error > np.float64(TOLERANCE)):
        _fail("terminal probability exceeded physical tolerance")
    return probability, bound_error


def _probabilities(np: Any, columns: Any, terminal: tuple[int, int]) -> tuple[Any, Any]:
    values = []
    maximum_bound = np.float64(0.0)
    for state in _coin_states(np, columns):
        probability, bound = _probability(np, state, terminal)
        values.append(probability)
        maximum_bound = np.maximum(maximum_bound, bound)
    return tuple(values), np.float64(maximum_bound)


def _evolve(
    np: Any, kernels: Any, state: Any, terminal: tuple[int, int], horizon: int,
    pairs: tuple[Any, ...], alpha: Any, beta: Any,
) -> tuple[Any, Any]:
    maximum_drift = np.float64(0.0)
    for _ in range(horizon):
        state = _step(np, kernels, state, terminal, pairs, alpha, beta)
        maximum_drift = np.maximum(maximum_drift, _norm_drift(np, state))
    return state, np.float64(maximum_drift)


def _load_baseline(artifact: dict[str, Any], numerics: Any) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for record in artifact["baseline_table"]["content"]["records"]:
        s = record["s"]
        width = s + 1
        start_flat = record["start"][0] * width + record["start"][1]
        terminal_flat = record["terminal"][0] * width + record["terminal"][1]
        key = (s, start_flat, terminal_flat)
        result[key] = tuple(
            numerics.parse_canonical_float64(value) for value in record["probabilities"]
        )
    if len(result) != selection.BASELINE_EVOLUTIONS:
        _fail("validated T9 embedded baseline is incomplete")
    return result

def _verify_shift(np: Any, kernels: Any) -> dict[str, Any]:
    checked_basis_states = 0
    for s, rows in selection.DEVELOPMENT_GRIDS:
        width = s + 1
        pairs = _pairs(s, rows)
        endpoints = {position for pair in pairs for position in pair}
        if len(pairs) != rows - 1 or len(endpoints) != 2 * (rows - 1):
            _fail("genuine overlap pair cardinality changed")
        if ((rows - 1, s), (0, 0)) in pairs or ((0, 0), (rows - 1, s)) in pairs:
            _fail("false periodic overlap edge exists")
        mapping = {(row, column): (row, column) for row in range(rows) for column in range(width)}
        for left, right in pairs:
            mapping[left], mapping[right] = right, left
        if len(set(mapping.values())) != rows * width:
            _fail("overlap shift is not bijective")
        for position, destination in mapping.items():
            if position in endpoints:
                if mapping.get(destination) != position or destination == position:
                    _fail("genuine overlap pair is not an exact swap")
            elif destination != position:
                _fail("unpaired overlap component is not a self-loop")
        marker = np.arange(rows * width * 5, dtype=np.float64).reshape(rows, width, 5)
        state = np.ascontiguousarray(marker.astype(np.complex128))
        shifted = _shift(np, kernels, state, pairs)
        expected_ordinary = kernels.periodic_flip_flop_shift(
            np.ascontiguousarray(state[:, :, :4])
        )
        if not bool(np.array_equal(shifted[:, :, :4], expected_ordinary)):
            _fail("ordinary periodic flip-flop shift changed")
        for source, destination in mapping.items():
            if shifted[destination[0], destination[1], OVERLAP] != state[source[0], source[1], OVERLAP]:
                _fail("overlap shift mapping mismatch")
        checked_basis_states += rows * width * 5
    return {
        "grids_checked": len(selection.DEVELOPMENT_GRIDS),
        "genuine_swaps_per_grid": 5,
        "endpoints_per_grid": 10,
        "checked_basis_states": checked_basis_states,
        "bijection": True,
        "unpaired_self_loops": True,
        "false_periodic_edge": False,
        "ordinary_periodic_flip_flop_unchanged": True,
    }


def _verify_embedded_baseline(
    artifact: dict[str, Any], baseline: dict[Any, Any]
) -> dict[str, Any]:
    np, kernels, _numerics = selection._load_numerical_modules()
    maximum_probability_error = np.float64(0.0)
    maximum_amplitude_error = np.float64(0.0)
    maximum_norm_drift = np.float64(0.0)
    maximum_bound = np.float64(0.0)
    records = 0
    comparisons = 0
    for s, rows in selection.DEVELOPMENT_GRIDS:
        positions = selection._positions(s, rows)
        pairs = _pairs(s, rows)
        horizon = selection.GRID_HORIZONS[(s, rows)]
        for start_flat, start in enumerate(positions):
            for terminal_flat, terminal in enumerate(positions):
                if start == terminal:
                    continue
                embedded, drift = _evolve(
                    np, kernels, _initial_columns(np, s, rows, start), terminal,
                    horizon, pairs, np.float64(0.0), np.float64(0.0),
                )
                ordinary, ordinary_drift = selection._evolve_columns(
                    np, kernels, selection.initial_columns(np, s, rows, start),
                    terminal, horizon, None, None, None,
                )
                amplitude_error = np.float64(np.max(np.abs(embedded[:, :, :4, :] - ordinary)))
                overlap_error = np.float64(np.max(np.abs(embedded[:, :, OVERLAP, :])))
                maximum_amplitude_error = np.maximum(
                    maximum_amplitude_error, np.maximum(amplitude_error, overlap_error)
                )
                maximum_norm_drift = np.maximum(maximum_norm_drift, np.maximum(drift, ordinary_drift))
                probabilities, bound = _probabilities(np, embedded, terminal)
                maximum_bound = np.maximum(maximum_bound, bound)
                expected = baseline[(s, start_flat, terminal_flat)]
                for observed, reference in zip(probabilities, expected):
                    error = np.float64(abs(observed - reference))
                    maximum_probability_error = np.maximum(maximum_probability_error, error)
                    comparisons += 1
                records += 1
    if records != 1728 or comparisons != 10368:
        _fail("embedded alpha=0 baseline coverage changed")
    if bool(maximum_amplitude_error > np.float64(TOLERANCE)):
        _fail("embedded alpha=0 amplitude baseline mismatch")
    if bool(maximum_probability_error > np.float64(TOLERANCE)):
        _fail("embedded alpha=0 T9 probability baseline mismatch")
    return {
        "records": records,
        "probability_comparisons": comparisons,
        "maximum_amplitude_error": maximum_amplitude_error,
        "maximum_probability_error": maximum_probability_error,
        "maximum_norm_drift": maximum_norm_drift,
        "maximum_probability_bound_error": maximum_bound,
    }

def _verify_direct_derived() -> dict[str, Any]:
    np, kernels, _numerics = selection._load_numerical_modules()
    cases = (
        (2, 6, (0, 0), (0, 2)),
        (3, 6, (2, 1), (3, 0)),
        (4, 6, (5, 4), (4, 0)),
    )
    maximum_amplitude_error = np.float64(0.0)
    maximum_probability_error = np.float64(0.0)
    maximum_norm_drift = np.float64(0.0)
    maximum_bound = np.float64(0.0)
    comparisons = 0
    vectors = _coin_vectors(np)
    for s, rows, start, terminal in cases:
        pairs = _pairs(s, rows)
        horizon = selection.GRID_HORIZONS[(s, rows)]
        for alpha_index in range(6):
            for beta_index in range(4):
                alpha, beta = selection.parameter_values(np, alpha_index, beta_index)
                columns, drift = _evolve(
                    np, kernels, _initial_columns(np, s, rows, start), terminal,
                    horizon, pairs, alpha, beta,
                )
                maximum_norm_drift = np.maximum(maximum_norm_drift, drift)
                derived = _coin_states(np, columns)
                for vector, derived_state in zip(vectors, derived):
                    direct, direct_drift = _evolve(
                        np, kernels, _initial_direct(np, s, rows, start, vector),
                        terminal, horizon, pairs, alpha, beta,
                    )
                    maximum_norm_drift = np.maximum(maximum_norm_drift, direct_drift)
                    amplitude_error = np.float64(np.max(np.abs(direct - derived_state)))
                    direct_probability, direct_bound = _probability(np, direct, terminal)
                    derived_probability, derived_bound = _probability(np, derived_state, terminal)
                    probability_error = np.float64(abs(direct_probability - derived_probability))
                    maximum_amplitude_error = np.maximum(maximum_amplitude_error, amplitude_error)
                    maximum_probability_error = np.maximum(maximum_probability_error, probability_error)
                    maximum_bound = np.maximum(maximum_bound, np.maximum(direct_bound, derived_bound))
                    comparisons += 1
    if comparisons != 432:
        _fail("direct/derived fixed-sample coverage changed")
    if bool(maximum_amplitude_error > np.float64(TOLERANCE)):
        _fail("direct six-state/four-column amplitude mismatch")
    if bool(maximum_probability_error > np.float64(TOLERANCE)):
        _fail("direct six-state/four-column probability mismatch")
    return {
        "fixed_cases": len(cases),
        "parameter_indices": 24,
        "comparisons": comparisons,
        "maximum_amplitude_error": maximum_amplitude_error,
        "maximum_probability_error": maximum_probability_error,
        "maximum_norm_drift": maximum_norm_drift,
        "maximum_probability_bound_error": maximum_bound,
    }


def _worker_ready(queue: Any) -> None:
    global _READY_QUEUE
    _READY_QUEUE = queue
    queue.put({"pid": os.getpid(), "start_method": multiprocessing.get_start_method()})


def _evaluate(task: tuple[int, int, int, int]) -> dict[str, Any]:
    alpha_index, beta_index, s, rows = task
    np, kernels, numerics = selection._load_numerical_modules()
    alpha, beta = selection.parameter_values(np, alpha_index, beta_index)
    pairs = _pairs(s, rows)
    positions = selection._positions(s, rows)
    horizon = selection.GRID_HORIZONS[(s, rows)]
    lifts: list[Any] = []
    keys: list[str] = []
    maximum_drift = np.float64(0.0)
    maximum_bound = np.float64(0.0)
    for start_flat, start in enumerate(positions):
        for terminal_flat, terminal in enumerate(positions):
            if start == terminal:
                continue
            columns, drift = _evolve(
                np, kernels, _initial_columns(np, s, rows, start), terminal,
                horizon, pairs, alpha, beta,
            )
            probabilities, bound = _probabilities(np, columns, terminal)
            maximum_drift = np.maximum(maximum_drift, drift)
            maximum_bound = np.maximum(maximum_bound, bound)
            baseline = _BASELINE[(s, start_flat, terminal_flat)]
            for coin, probability, reference in zip(selection.COIN_ORDER, probabilities, baseline):
                lifts.append(numerics.subtract_float64(probability, reference, "overlap-edge lift"))
                keys.append(selection.micro_case_key(s, rows, start, terminal, coin))
    expected = selection.GRID_PAIR_COUNTS[(s, rows)] * 6
    if len(lifts) != expected or len(set(keys)) != expected:
        _fail("screen micro-case coverage changed")
    return {
        "pid": os.getpid(),
        "alpha_index": alpha_index,
        "beta_index": beta_index,
        "s": s,
        "R": rows,
        "horizon": horizon,
        "micro_case_count": expected,
        "median_lift": numerics.canonical_float64(numerics.frozen_median(lifts, keys)),
        "q10_lift": numerics.canonical_float64(numerics.frozen_quantile_10(lifts, keys)),
        "positive_count": sum(bool(value > numerics.EPSILON) for value in lifts),
        "maximum_norm_drift": numerics.canonical_float64(maximum_drift),
        "maximum_probability_bound_error": numerics.canonical_float64(maximum_bound),
    }

def _screen() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not sys.platform.startswith("linux"):
        _fail("full discovery screen requires Linux")
    if "fork" not in multiprocessing.get_all_start_methods():
        _fail("Linux fork start method is unavailable")
    tasks = tuple(
        (alpha_index, beta_index, s, rows)
        for alpha_index in range(6)
        for beta_index in range(4)
        for s, rows in selection.DEVELOPMENT_GRIDS
    )
    if len(tasks) != 72:
        _fail("screen task count changed")
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    with context.Pool(processes=WORKERS, initializer=_worker_ready, initargs=(queue,)) as pool:
        diagnostics = [queue.get(timeout=30.0) for _ in range(WORKERS)]
        groups = pool.map(_evaluate, tasks, chunksize=1)
    pids = {record["pid"] for record in diagnostics}
    if len(pids) != WORKERS or any(record["start_method"] != "fork" for record in diagnostics):
        _fail("exactly four distinct Linux fork workers were not started")
    if {record["pid"] for record in groups} != pids:
        _fail("every fork worker must execute at least one screen group")
    return groups, sorted(diagnostics, key=lambda record: record["pid"])


def _aggregate(groups: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    np, _kernels, numerics = selection._load_numerical_modules()
    scores: list[dict[str, Any]] = []
    score_objects = []
    maximum_drift = np.float64(0.0)
    maximum_bound = np.float64(0.0)
    for alpha_index in range(6):
        for beta_index in range(4):
            metrics = [record for record in groups if (
                record["alpha_index"], record["beta_index"]
            ) == (alpha_index, beta_index)]
            if [(record["s"], record["R"]) for record in metrics] != list(selection.DEVELOPMENT_GRIDS):
                _fail("screen grid order or coverage changed")
            medians = [numerics.parse_canonical_float64(record["median_lift"]) for record in metrics]
            grid_keys = [json.dumps([record["s"], record["R"]], separators=(",", ":")) for record in metrics]
            quantiles = {
                (record["s"], record["R"]): numerics.parse_canonical_float64(record["q10_lift"])
                for record in metrics
            }
            for record in metrics:
                drift = numerics.parse_canonical_float64(record["maximum_norm_drift"])
                bound = numerics.parse_canonical_float64(record["maximum_probability_bound_error"])
                if bool(drift > np.float64(TOLERANCE)) or bool(bound > np.float64(TOLERANCE)):
                    _fail("screen invariant exceeded 1e-12")
                maximum_drift = np.maximum(maximum_drift, drift)
                maximum_bound = np.maximum(maximum_bound, bound)
            aggregate = numerics.frozen_median(medians, grid_keys)
            score = numerics.ParameterScore(quantiles, aggregate, alpha_index, beta_index)
            score_objects.append(score)
            scores.append({
                "alpha_index": alpha_index,
                "beta_index": beta_index,
                "alpha_pi_numerator": selection.THETA_NUMERATORS[alpha_index],
                "alpha_pi_denominator": 16,
                "beta_pi_numerator": selection.PHI_NUMERATORS[beta_index],
                "beta_pi_denominator": 2,
                "grid_metrics": [{key: value for key, value in metric.items() if key != "pid"} for metric in metrics],
                "aggregate_median": numerics.canonical_float64(aggregate),
                "minimum_grid_q10": numerics.canonical_float64(score.minimum_grid_quantile),
                "feasible_old_q10_floor": score.feasible,
            })
    if len(scores) != 24:
        _fail("exactly 24 parameter indices are required")
    winner = numerics.select_parameter(score_objects)
    source = scores[winner.theta_index * 4 + winner.phi_index]
    winner_record = {
        key: source[key] for key in (
            "alpha_index", "beta_index", "alpha_pi_numerator", "alpha_pi_denominator",
            "beta_pi_numerator", "beta_pi_denominator", "aggregate_median",
            "minimum_grid_q10", "feasible_old_q10_floor",
        )
    }
    invariants = {
        "maximum_norm_drift": maximum_drift,
        "maximum_probability_bound_error": maximum_bound,
    }
    return scores, winner_record, invariants

def _canonical_invariant_record(numerics: Any, record: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in record.items():
        if key.startswith("maximum_"):
            result[key] = numerics.canonical_float64(value)
        else:
            result[key] = value
    return result


def run(selection_path: Path, output_directory: Path, workers: int) -> dict[str, Any]:
    global _BASELINE
    if workers != WORKERS:
        _fail("the discovery screen requires exactly four workers")
    simulator = Path(__file__).resolve().parent
    expected_selection = simulator / "t9-development-output" / "area-one-development-selection.json"
    expected_output = simulator / "candidate2-overlap-edge-probe-output"
    if selection_path.resolve() != expected_selection.resolve():
        _fail("only the validated T9 development artifact may be read")
    if output_directory.resolve() != expected_output.resolve():
        _fail("output directory is not the dedicated overlap-edge location")
    if os.environ.get("CANDIDATE2_IMAGE_DIGEST") != EXPECTED_IMAGE:
        _fail("full screen image digest binding is missing or incorrect")
    if os.environ.get("CANDIDATE2_CONTAINER_NAME") != EXPECTED_CONTAINER:
        _fail("full screen named-container binding is missing or incorrect")

    raw = selection_path.read_bytes()
    try:
        artifact = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise selection.DevelopmentSelectionError("invalid T9 development artifact") from exc
    if raw != selection.canonical_json_bytes(artifact):
        _fail("T9 development artifact is not canonical")
    selection.validate_selection_artifact(artifact)
    if artifact["counts"]["heldout_accesses"] != 0 or artifact["counts"]["lock_accesses"] != 0:
        _fail("source T9 artifact crossed the development boundary")
    output = selection._require_empty_output_directory(output_directory)
    np, kernels, numerics = selection._load_numerical_modules()
    _BASELINE = _load_baseline(artifact, numerics)

    # These gates complete before _screen starts any worker.
    shift_verification = _verify_shift(np, kernels)
    baseline_verification = _verify_embedded_baseline(artifact, _BASELINE)
    direct_verification = _verify_direct_derived()
    groups, worker_diagnostics = _screen()
    scores, winner, screen_invariants = _aggregate(groups)

    all_invariants = (
        baseline_verification["maximum_norm_drift"],
        baseline_verification["maximum_probability_bound_error"],
        baseline_verification["maximum_amplitude_error"],
        baseline_verification["maximum_probability_error"],
        direct_verification["maximum_norm_drift"],
        direct_verification["maximum_probability_bound_error"],
        direct_verification["maximum_amplitude_error"],
        direct_verification["maximum_probability_error"],
        screen_invariants["maximum_norm_drift"],
        screen_invariants["maximum_probability_bound_error"],
    )
    if any(not bool(np.isfinite(value)) or bool(value > np.float64(TOLERANCE)) for value in all_invariants):
        _fail("global finite/tolerance gate failed")

    source_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
    result = {
        "schema_version": SCHEMA_VERSION,
        "dataset_kind": "pre-protocol-development-discovery",
        "candidate": "dedicated-overlap-edge",
        "operator": "S_X R_X C_0 O_t",
        "coin_basis": ["UP", "RIGHT", "DOWN", "LEFT", "OVERLAP"],
        "source_t9_sha256": source_hash,
        "candidate1_t9_artifact_binding": {
            "path": "t9-development-output/area-one-development-selection.json",
            "sha256": source_hash,
            "embedded_baseline_sha256": artifact["baseline_table"]["canonical_sha256"],
        },
        "development_grids": [
            {"s": s, "R": rows, "horizon": selection.GRID_HORIZONS[(s, rows)]}
            for s, rows in selection.DEVELOPMENT_GRIDS
        ],
        "parameter_order": [
            {
                "alpha_index": alpha_index,
                "beta_index": beta_index,
                "alpha_pi_numerator": selection.THETA_NUMERATORS[alpha_index],
                "alpha_pi_denominator": 16,
                "beta_pi_numerator": selection.PHI_NUMERATORS[beta_index],
                "beta_pi_denominator": 2,
            }
            for alpha_index in range(6) for beta_index in range(4)
        ],
        "pre_screen_verification": {
            "completed_before_screen": True,
            "shift": shift_verification,
            "embedded_alpha_zero_baseline": _canonical_invariant_record(numerics, baseline_verification),
            "direct_six_state_vs_four_column": _canonical_invariant_record(numerics, direct_verification),
        },
        "scores": scores,
        "winner": winner,
        "screen_invariants": _canonical_invariant_record(numerics, screen_invariants),
        "runtime": {
            "required_image": EXPECTED_IMAGE,
            "container_name": EXPECTED_CONTAINER,
            "container_id": os.environ.get("HOSTNAME", ""),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "multiprocessing_start_method": "fork",
            "workers": WORKERS,
            "worker_diagnostics": worker_diagnostics,
        },
        "counts": {
            "parameters": 24,
            "screen_groups": 72,
            "screen_micro_cases": 24 * selection.MICRO_CASES_PER_PARAMETER_METHOD,
            "baseline_records_verified": 1728,
            "baseline_probabilities_verified": 10368,
            "direct_derived_comparisons": 432,
            "lock_accesses": 0,
            "heldout_accesses": 0,
        },
        "boundary_record": {
            "lock_access": "NONE",
            "heldout_access": "NONE",
            "heldout_execution": False,
            "new_t9_started": False,
        },
        "promotion_status": "pre-protocol-discovery-only",
    }
    body = selection.canonical_json_bytes(result)
    selection._atomic_publish(output, RESULT_FILENAME, body)
    if (output / RESULT_FILENAME).read_bytes() != body:
        _fail("atomic publication verification failed")
    return result

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workers", required=True, type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args.selection, args.output, args.workers)
    print("CANDIDATE2_OVERLAP_EDGE_PROBE_PASS", flush=True)
    print("winner=" + json.dumps(result["winner"], sort_keys=True), flush=True)
    print("source_t9_sha256=" + result["source_t9_sha256"], flush=True)
    print("workers=4 start_method=fork", flush=True)
    print("no_lock=true heldout_executed=false new_t9_started=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
