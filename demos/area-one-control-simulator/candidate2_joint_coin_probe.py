#!/usr/bin/env python3
"""Probe a joint eight-state Grover coin on genuine EOG pairs, development only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
import pair_scatter_development_selection as selection

RESULT_FILENAME = "candidate2-joint-coin-probe.json"


def _baseline(artifact: dict[str, Any], numerics: Any) -> dict[Any, Any]:
    result = {}
    for record in artifact["baseline_table"]["content"]["records"]:
        s, rows = record["s"], record["R"]
        positions = selection._positions(s, rows)
        indices = {position: index for index, position in enumerate(positions)}
        key = (s, indices[tuple(record["start"])], indices[tuple(record["terminal"])])
        result[key] = tuple(numerics.parse_canonical_float64(x) for x in record["probabilities"])
    return result


def _joint_coin(np: Any, kernels: Any, state: Any, pairs: tuple[Any, ...]) -> Any:
    result = kernels.grover_coin(state)
    for left, right in pairs:
        block = np.concatenate((state[left[0], left[1]], state[right[0], right[1]]), axis=0)
        transformed = np.float64(0.25) * np.sum(block, axis=0, dtype=np.complex128) - block
        result[left[0], left[1]] = transformed[:4]
        result[right[0], right[1]] = transformed[4:]
    if not np.isfinite(result).all():
        raise selection.DevelopmentSelectionError("joint coin became non-finite")
    return np.ascontiguousarray(result, dtype=np.complex128)


def run(selection_path: Path, output_directory: Path) -> dict[str, Any]:
    raw = selection_path.read_bytes()
    artifact = json.loads(raw.decode("utf-8", errors="strict"))
    selection.validate_selection_artifact(artifact)
    if artifact["counts"]["heldout_accesses"] or artifact["counts"]["lock_accesses"]:
        raise selection.DevelopmentSelectionError("development boundary was crossed")
    output = selection._require_empty_output_directory(output_directory)
    np, kernels, numerics = selection._load_numerical_modules()
    baseline = _baseline(artifact, numerics)
    projection = selection.development_manifest.load_projection()
    metrics = []
    maximum_drift = np.float64(0.0)
    for s, rows in selection.DEVELOPMENT_GRIDS:
        positions = selection._positions(s, rows)
        pairs = selection._pair_map(projection, s)["candidate"]
        lifts, keys = [], []
        for start_flat, start in enumerate(positions):
            for terminal_flat, terminal in enumerate(positions):
                if start == terminal:
                    continue
                columns = selection.initial_columns(np, s, rows, start)
                for _step in range(selection.GRID_HORIZONS[(s, rows)]):
                    columns = kernels.terminal_phase_oracle(columns, terminal)
                    columns = _joint_coin(np, kernels, columns, pairs)
                    columns = kernels.periodic_flip_flop_shift(columns)
                    maximum_drift = np.maximum(maximum_drift, selection._column_norm_drift(np, columns))
                probabilities, _bound = selection._probabilities(np, kernels, columns, terminal)
                for coin, probability, base in zip(
                    selection.COIN_ORDER, probabilities,
                    baseline[(s, start_flat, terminal_flat)],
                ):
                    lifts.append(numerics.subtract_float64(probability, base, "joint coin lift"))
                    keys.append(selection.micro_case_key(s, rows, start, terminal, coin))
        metrics.append({
            "s": s, "R": rows,
            "median_lift": numerics.canonical_float64(numerics.frozen_median(lifts, keys)),
            "q10_lift": numerics.canonical_float64(numerics.frozen_quantile_10(lifts, keys)),
            "positive_count": sum(bool(x > numerics.EPSILON) for x in lifts),
            "case_count": len(lifts),
        })
    aggregate = numerics.frozen_median(
        [numerics.parse_canonical_float64(x["median_lift"]) for x in metrics],
        [json.dumps([x["s"], x["R"]], separators=(",", ":")) for x in metrics],
    )
    result = {
        "schema_version": "area-one-candidate2-joint-coin-probe/1.0",
        "dataset_kind": "development-discovery",
        "source_t9_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "operator": "S C_joint O_t",
        "grid_metrics": metrics,
        "aggregate_median": numerics.canonical_float64(aggregate),
        "maximum_norm_drift": numerics.canonical_float64(maximum_drift),
        "lock_accesses": 0, "heldout_accesses": 0,
    }
    selection._atomic_publish(output, RESULT_FILENAME, selection.canonical_json_bytes(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.selection, args.output)
    print(json.dumps(result, sort_keys=True))
    print("no_lock=true heldout_executed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())