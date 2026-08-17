#!/usr/bin/env python3
"""Screen pre-protocol Candidate 2 mechanisms on development data only."""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
from pathlib import Path
from typing import Any

import pair_scatter_development_selection as selection

SCHEMA_VERSION = "area-one-candidate2-variant-screen/1.0"
VARIANTS = (
    "candidate1-reference",
    "outward-edge",
    "outward-edge-alternating-phase",
    "horizontal-directions",
    "all-directions-alternating-phase",
)
RESULT_FILENAME = "candidate2-variant-screen.json"
_BASELINE: dict[Any, Any] = {}
_PROJECTION: dict[str, Any] = {}


def _load_baseline(artifact: dict[str, Any], numerics: Any) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    index_maps = {
        (s, rows): {p: i for i, p in enumerate(selection._positions(s, rows))}
        for s, rows in selection.DEVELOPMENT_GRIDS
    }
    for record in artifact["baseline_table"]["content"]["records"]:
        s, rows = record["s"], record["R"]
        indices = index_maps[(s, rows)]
        key = (s, indices[tuple(record["start"])], indices[tuple(record["terminal"])])
        result[key] = tuple(numerics.parse_canonical_float64(x) for x in record["probabilities"])
    return result


def _rotate(np: Any, left: Any, right: Any, theta: Any, phi: Any) -> tuple[Any, Any]:
    cosine, sine = np.cos(theta), np.sin(theta)
    phase = np.complex128(np.cos(phi) + 1j * np.sin(phi))
    return (
        np.ascontiguousarray(cosine * left - np.conjugate(phase) * sine * right),
        np.ascontiguousarray(phase * sine * left + cosine * right),
    )

def _variant_layer(np: Any, state: Any, pairs: tuple[Any, ...], theta: Any, phi: Any, variant: str) -> Any:
    result = state.copy(order="C")
    if variant == "candidate1-reference":
        return selection._load_numerical_modules()[1].pair_scatter(state, pairs, theta, phi)
    for pair_index, (left, right) in enumerate(pairs):
        local_phi = -phi if "alternating-phase" in variant and pair_index % 2 else phi
        if variant == "horizontal-directions":
            directions: tuple[int | None, ...] = (1, 3)
        elif variant == "all-directions-alternating-phase":
            directions = (0, 1, 2, 3)
        else:
            directions = (None,)
        for direction in directions:
            if direction is None:
                left_index = (left[0], left[1], 1)
                right_index = (right[0], right[1], 3)
            else:
                left_index = (left[0], left[1], direction)
                right_index = (right[0], right[1], direction)
            new_left, new_right = _rotate(
                np, state[left_index], state[right_index], theta, local_phi
            )
            result[left_index] = new_left
            result[right_index] = new_right
    if not np.isfinite(result).all():
        raise selection.DevelopmentSelectionError("variant layer became non-finite")
    return result


def _step(np: Any, kernels: Any, state: Any, terminal: Any, pairs: Any, theta: Any, phi: Any, variant: str) -> Any:
    if variant == "candidate1-reference":
        return kernels.candidate_step(state, terminal, pairs, theta, phi)
    state = kernels.terminal_phase_oracle(state, terminal)
    state = _variant_layer(np, state, pairs, theta, phi, variant)
    state = kernels.grover_coin(state)
    return kernels.periodic_flip_flop_shift(state)


def _evaluate(task: tuple[str, int, int, int, int]) -> dict[str, Any]:
    variant, theta_index, phi_index, s, rows = task
    np, kernels, numerics = selection._load_numerical_modules()
    theta, phi = selection.parameter_values(np, theta_index, phi_index)
    pairs = selection._pair_map(_PROJECTION, s)["candidate"]
    lifts: list[Any] = []
    keys: list[str] = []
    maximum_drift = np.float64(0.0)
    positions = selection._positions(s, rows)
    for start_flat, start in enumerate(positions):
        for terminal_flat, terminal in enumerate(positions):
            if start == terminal:
                continue
            columns = selection.initial_columns(np, s, rows, start)
            for _step_index in range(selection.GRID_HORIZONS[(s, rows)]):
                columns = _step(np, kernels, columns, terminal, pairs, theta, phi, variant)
                maximum_drift = np.maximum(maximum_drift, selection._column_norm_drift(np, columns))
            probabilities, _bound = selection._probabilities(np, kernels, columns, terminal)
            for coin, probability, base in zip(
                selection.COIN_ORDER, probabilities,
                _BASELINE[(s, start_flat, terminal_flat)],
            ):
                lifts.append(numerics.subtract_float64(probability, base, "variant lift"))
                keys.append(selection.micro_case_key(s, rows, start, terminal, coin))
    return {
        "variant": variant, "theta_index": theta_index, "phi_index": phi_index,
        "s": s, "R": rows,
        "median_lift": numerics.canonical_float64(numerics.frozen_median(lifts, keys)),
        "q10_lift": numerics.canonical_float64(numerics.frozen_quantile_10(lifts, keys)),
        "maximum_norm_drift": numerics.canonical_float64(maximum_drift),
    }

def run(selection_path: Path, output_directory: Path, workers: int) -> dict[str, Any]:
    global _BASELINE, _PROJECTION
    raw = selection_path.read_bytes()
    artifact = json.loads(raw.decode("utf-8", errors="strict"))
    if raw != selection.canonical_json_bytes(artifact):
        raise selection.DevelopmentSelectionError("T9 artifact is not canonical")
    selection.validate_selection_artifact(artifact)
    if artifact["counts"]["heldout_accesses"] or artifact["counts"]["lock_accesses"]:
        raise selection.DevelopmentSelectionError("development boundary was crossed")
    output = selection._require_empty_output_directory(output_directory)
    np, _kernels, numerics = selection._load_numerical_modules()
    _PROJECTION = selection.development_manifest.load_projection()
    _BASELINE = _load_baseline(artifact, numerics)
    tasks = tuple(
        (variant, theta_index, phi_index, s, rows)
        for variant in VARIANTS
        for theta_index in range(6)
        for phi_index in range(4)
        for s, rows in selection.DEVELOPMENT_GRIDS
    )
    with multiprocessing.get_context("fork").Pool(processes=workers) as pool:
        groups = pool.map(_evaluate, tasks)
    score_records: list[dict[str, Any]] = []
    winners: list[dict[str, Any]] = []
    for variant in VARIANTS:
        scores = []
        for theta_index in range(6):
            for phi_index in range(4):
                metrics = [g for g in groups if (
                    g["variant"], g["theta_index"], g["phi_index"]
                ) == (variant, theta_index, phi_index)]
                medians = [numerics.parse_canonical_float64(x["median_lift"]) for x in metrics]
                quantiles = {
                    (x["s"], x["R"]): numerics.parse_canonical_float64(x["q10_lift"])
                    for x in metrics
                }
                aggregate = numerics.frozen_median(medians, [json.dumps([x["s"], x["R"]], separators=(",", ":")) for x in metrics])
                score = numerics.ParameterScore(quantiles, aggregate, theta_index, phi_index)
                scores.append(score)
                score_records.append({
                    "variant": variant, "theta_index": theta_index, "phi_index": phi_index,
                    "grid_metrics": metrics,
                    "aggregate_median": numerics.canonical_float64(aggregate),
                    "minimum_grid_q10": numerics.canonical_float64(score.minimum_grid_quantile),
                    "feasible": score.feasible,
                })
        winner = numerics.select_parameter(scores)
        winners.append({
            "variant": variant, "theta_index": winner.theta_index,
            "phi_index": winner.phi_index,
            "aggregate_median": numerics.canonical_float64(winner.aggregate_median),
            "minimum_grid_q10": numerics.canonical_float64(winner.minimum_grid_quantile),
            "feasible": winner.feasible,
        })
    expected = artifact["parameter_scores"][:24]
    observed = [x for x in score_records if x["variant"] == "candidate1-reference"]
    for source, replay in zip(expected, observed):
        if any(source[name] != replay[name] for name in (
            "theta_index", "phi_index", "aggregate_median", "minimum_grid_q10", "feasible"
        )):
            raise selection.DevelopmentSelectionError("Candidate 1 replay mismatch")
    result = {
        "schema_version": SCHEMA_VERSION, "dataset_kind": "development-discovery",
        "source_t9_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "variants": list(VARIANTS), "group_count": len(groups),
        "scores": score_records, "winners": winners,
        "lock_accesses": 0, "heldout_accesses": 0,
    }
    selection._atomic_publish(output, RESULT_FILENAME, selection.canonical_json_bytes(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    result = run(args.selection, args.output, args.workers)
    for winner in result["winners"]:
        print("VARIANT_WINNER " + json.dumps(winner, sort_keys=True), flush=True)
    print(f"CANDIDATE2_SCREEN_PASS groups={result['group_count']}", flush=True)
    print("no_lock=true heldout_executed=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())