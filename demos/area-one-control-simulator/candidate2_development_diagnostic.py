#!/usr/bin/env python3
"""Development-only localization of Candidate 1's harmful lift tail."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pair_scatter_development_selection as selection

SCHEMA_VERSION = "area-one-candidate2-development-diagnostic/1.0"
METHODS = ("candidate", "control-004", "control-010")
RESULT_FILENAME = "candidate2-development-diagnostic.json"


def _role(position: tuple[int, int], s: int, rows: int) -> str:
    if position in tuple((row, s) for row in range(rows - 1)):
        return "genuine-left"
    if position in tuple((row + 1, 0) for row in range(rows - 1)):
        return "genuine-right"
    if position in ((0, 0), (rows - 1, s)):
        return "unpaired-boundary"
    return "interior"


def _same_candidate_pair(
    start: tuple[int, int], terminal: tuple[int, int], s: int, rows: int
) -> bool:
    return any(
        {start, terminal} == {(row, s), (row + 1, 0)}
        for row in range(rows - 1)
    )


def _load_baseline(artifact: dict[str, Any], numerics: Any) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for record in artifact["baseline_table"]["content"]["records"]:
        s, rows = record["s"], record["R"]
        index = {position: ordinal for ordinal, position in enumerate(selection._positions(s, rows))}
        key = (s, index[tuple(record["start"])], index[tuple(record["terminal"])])
        result[key] = tuple(numerics.parse_canonical_float64(x) for x in record["probabilities"])
    return result

def run(selection_path: Path, output_directory: Path) -> dict[str, Any]:
    raw = selection_path.read_bytes()
    artifact = json.loads(raw.decode("utf-8", errors="strict"))
    if raw != selection.canonical_json_bytes(artifact):
        raise selection.DevelopmentSelectionError("T9 artifact is not canonical")
    selection.validate_selection_artifact(artifact)
    if artifact["counts"]["heldout_accesses"] != 0 or artifact["counts"]["lock_accesses"] != 0:
        raise selection.DevelopmentSelectionError("T9 artifact crossed the development boundary")
    output = selection._require_empty_output_directory(output_directory)
    np, kernels, numerics = selection._load_numerical_modules()
    projection = selection.development_manifest.load_projection()
    pair_maps = {s: selection._pair_map(projection, s) for s, _rows in selection.DEVELOPMENT_GRIDS}
    winners = {record["family_id"]: record for record in artifact["winners"]}
    baseline = _load_baseline(artifact, numerics)
    records: list[dict[str, Any]] = []
    maximum_drift = np.float64(0.0)
    maximum_bound = np.float64(0.0)
    for method in METHODS:
        winner = winners[method]
        theta, phi = selection.parameter_values(np, winner["theta_index"], winner["phi_index"])
        for s, rows in selection.DEVELOPMENT_GRIDS:
            positions = selection._positions(s, rows)
            for start_flat, start in enumerate(positions):
                for terminal_flat, terminal in enumerate(positions):
                    if start == terminal:
                        continue
                    columns, drift = selection._evolve_columns(
                        np, kernels, selection.initial_columns(np, s, rows, start),
                        terminal, selection.GRID_HORIZONS[(s, rows)],
                        pair_maps[s][method], theta, phi,
                    )
                    probabilities, bound = selection._probabilities(np, kernels, columns, terminal)
                    maximum_drift = np.maximum(maximum_drift, drift)
                    maximum_bound = np.maximum(maximum_bound, bound)
                    for coin, probability, base in zip(
                        selection.COIN_ORDER, probabilities,
                        baseline[(s, start_flat, terminal_flat)],
                    ):
                        lift = numerics.subtract_float64(probability, base, "diagnostic lift")
                        records.append({
                            "method": method, "s": s, "R": rows,
                            "start": list(start), "terminal": list(terminal), "coin": coin,
                            "start_role": _role(start, s, rows),
                            "terminal_role": _role(terminal, s, rows),
                            "same_candidate_pair": _same_candidate_pair(start, terminal, s, rows),
                            "row_delta_mod_R": (terminal[0] - start[0]) % rows,
                            "column_delta_mod_width": (terminal[1] - start[1]) % (s + 1),
                            "lift": numerics.canonical_float64(lift),
                        })
    parameters = [{
        "family_id": method,
        "theta_index": winners[method]["theta_index"],
        "phi_index": winners[method]["phi_index"],
    } for method in METHODS]
    result = {
        "schema_version": SCHEMA_VERSION,
        "dataset_kind": "development-diagnostic",
        "source_t9_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "protocol_sha256": artifact["protocol_sha256"],
        "methods": list(METHODS), "parameters": parameters,
        "record_count": len(records), "records": records,
        "invariants": {
            "maximum_norm_drift": numerics.canonical_float64(np.float64(maximum_drift)),
            "maximum_probability_bound_error": numerics.canonical_float64(np.float64(maximum_bound)),
        },
        "lock_accesses": 0, "heldout_accesses": 0,
    }
    body = selection.canonical_json_bytes(result)
    selection._atomic_publish(output, RESULT_FILENAME, body)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.selection, args.output)
    print(f"CANDIDATE2_DIAGNOSTIC_PASS records={result['record_count']}")
    print(f"maximum_norm_drift={result['invariants']['maximum_norm_drift']}")
    print("no_lock=true heldout_executed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())