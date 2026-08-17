"""Topology-only EOG hierarchical zero-mode discovery probe."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import platform
import stat
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

SCHEMA_VERSION = "area-one-eog-zero-mode-topology-probe/1.0"
EXPECTED_IMAGE = "sha256:96379ff14fb29df67b28c19102d93cb1cc912e23962e0c917b5209b605edb3f2"
EXPECTED_CONTAINER = "area-one-eog-zero-mode-topology-probe"
GRIDS = ((2, 6), (3, 6), (4, 6))
CLOSURE_TOLERANCE = 1.0e-12
ZERO_TOLERANCE = 1.0e-10
SUPPORT_TOLERANCE = 1.0e-12
RESULT_FILENAME = "eog-zero-mode-topology-probe.json"


class ProbeError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise ProbeError(message)


def _index(s: int, row: int, column: int) -> int:
    return row * (s + 1) + column


def _coordinate(s: int, index: int) -> tuple[int, int]:
    return divmod(index, s + 1)


def _add_edge(adjacency: Any, left: int, right: int, weight: int = 1) -> None:
    if left == right or weight <= 0:
        _fail("edges must be positive-weight and loop-free")
    adjacency[left, right] += weight
    adjacency[right, left] += weight


def _base_adjacency(np: Any, s: int, rows: int) -> Any:
    width = s + 1
    adjacency = np.zeros((rows * width, rows * width), dtype=np.int64)
    edges: set[tuple[int, int]] = set()
    for row in range(rows):
        for column in range(width):
            here = _index(s, row, column)
            for neighbour in (
                _index(s, (row + 1) % rows, column),
                _index(s, row, (column + 1) % width),
            ):
                edge = tuple(sorted((here, neighbour)))
                if edge not in edges:
                    edges.add(edge)
                    _add_edge(adjacency, *edge)
    return adjacency


def _matching_edges(s: int, destinations: Sequence[int]) -> tuple[tuple[int, int], ...]:
    if tuple(sorted(destinations)) != tuple(range(1, 6)):
        _fail("destinations must be a bijection of rows 1 through 5")
    return tuple(
        (_index(s, source, s), _index(s, destination, 0))
        for source, destination in enumerate(destinations)
    )


def _candidate_adjacency(np: Any, s: int, rows: int, destinations: Sequence[int]) -> Any:
    adjacency = _base_adjacency(np, s, rows)
    for left, right in _matching_edges(s, destinations):
        _add_edge(adjacency, left, right)
    return adjacency


def _row_partition(s: int, rows: int) -> list[list[int]]:
    return [[_index(s, row, column) for column in range(s + 1)] for row in range(rows)]


def _column_partition(s: int, rows: int) -> list[list[int]]:
    return [[_index(s, row, column) for row in range(rows)] for column in range(s + 1)]


def _overlap_fiber_partition(s: int, rows: int) -> list[list[int]]:
    cells = [[_index(s, 0, 0)], [_index(s, rows - 1, s)]]
    cells.extend([
        [_index(s, row, s), _index(s, row + 1, 0)]
        for row in range(rows - 1)
    ])
    cells.extend([
        [_index(s, row, column) for row in range(rows)]
        for column in range(1, s)
    ])
    return cells


def _reflection_partition(s: int, rows: int) -> list[list[int]]:
    remaining = set(range(rows * (s + 1)))
    cells: list[list[int]] = []
    while remaining:
        first = min(remaining)
        row, column = _coordinate(s, first)
        reflected = _index(s, rows - 1 - row, s - column)
        cell = sorted({first, reflected})
        cells.append(cell)
        remaining.difference_update(cell)
    return cells


def _seed_partition(s: int, rows: int) -> list[list[int]]:
    entrance = _index(s, 0, 0)
    exit_state = _index(s, rows - 1, s)
    left = [_index(s, row, 0) for row in range(1, rows)]
    right = [_index(s, row, s) for row in range(rows - 1)]
    interior = [
        _index(s, row, column)
        for row in range(rows) for column in range(1, s)
    ]
    return [[entrance], [exit_state], left, right, interior]


def _equitable_refinement(adjacency: Any, cells: list[list[int]]) -> list[list[int]]:
    current = [sorted(cell) for cell in cells if cell]
    while True:
        refined: list[list[int]] = []
        for cell in current:
            buckets: dict[tuple[int, ...], list[int]] = {}
            for vertex in cell:
                signature = tuple(
                    int(adjacency[vertex, target_cell].sum())
                    for target_cell in current
                )
                buckets.setdefault(signature, []).append(vertex)
            refined.extend(sorted(buckets.values(), key=lambda value: value[0]))
        if refined == current:
            return refined
        current = refined


def _partition_report(np: Any, adjacency: Any, cells: list[list[int]], s: int) -> dict[str, Any]:
    size = adjacency.shape[0]
    flattened = [vertex for cell in cells for vertex in cell]
    if sorted(flattened) != list(range(size)) or len(flattened) != len(set(flattened)):
        _fail("partition does not cover every vertex exactly once")
    discrepancies = 0
    for cell in cells:
        signatures = {
            tuple(int(adjacency[vertex, target].sum()) for target in cells)
            for vertex in cell
        }
        discrepancies = max(discrepancies, len(signatures) - 1)
    q = np.zeros((size, len(cells)), dtype=np.float64)
    for cell_index, cell in enumerate(cells):
        q[cell, cell_index] = 1.0 / math.sqrt(len(cell))
    quotient = q.T @ adjacency.astype(np.float64) @ q
    residual = adjacency.astype(np.float64) @ q - q @ quotient
    closure_error = float(np.max(np.abs(residual))) if residual.size else 0.0
    entrance = _index(s, 0, 0)
    exit_state = _index(s, 5, s)
    projection = q @ q.T
    entrance_error = float(np.max(np.abs(projection[:, entrance] - np.eye(size)[:, entrance])))
    exit_error = float(np.max(np.abs(projection[:, exit_state] - np.eye(size)[:, exit_state])))
    entrance_cell = next(index for index, cell in enumerate(cells) if entrance in cell)
    exit_cell = next(index for index, cell in enumerate(cells) if exit_state in cell)
    return {
        "cell_count": len(cells),
        "compression_ratio": len(cells) / size,
        "maximum_signature_discrepancy": discrepancies,
        "closure_error": closure_error,
        "exactly_equitable": discrepancies == 0 and closure_error <= CLOSURE_TOLERANCE,
        "entrance_projection_error": entrance_error,
        "exit_projection_error": exit_error,
        "endpoints_separate": entrance_cell != exit_cell,
        "endpoint_representing": entrance_error <= CLOSURE_TOLERANCE and exit_error <= CLOSURE_TOLERANCE,
    }


def _connected(adjacency: Any) -> bool:
    seen = {0}
    pending = [0]
    while pending:
        vertex = pending.pop()
        for neighbour in (adjacency[vertex] != 0).nonzero()[0].tolist():
            if neighbour not in seen:
                seen.add(neighbour)
                pending.append(neighbour)
    return len(seen) == adjacency.shape[0]


def _bipartite_report(np: Any, adjacency: Any) -> dict[str, Any]:
    colours: list[int | None] = [None] * adjacency.shape[0]
    conflict: tuple[int, int] | None = None
    for start in range(adjacency.shape[0]):
        if colours[start] is not None:
            continue
        colours[start] = 1
        pending = [start]
        while pending and conflict is None:
            vertex = pending.pop()
            for neighbour in (adjacency[vertex] != 0).nonzero()[0].tolist():
                if colours[neighbour] is None:
                    colours[neighbour] = -int(colours[vertex])
                    pending.append(neighbour)
                elif colours[neighbour] == colours[vertex]:
                    conflict = (vertex, neighbour)
                    break
    if conflict is not None:
        return {"bipartite": False, "conflict_edge": list(conflict), "chiral_residual": None}
    gamma = np.array([int(value) for value in colours], dtype=np.int64)
    residual = gamma[:, None] * adjacency * gamma[None, :] + adjacency
    return {
        "bipartite": True,
        "conflict_edge": None,
        "chiral_residual": int(np.max(np.abs(residual))),
    }


def _exact_rank(matrix: Any) -> int:
    values = [[Fraction(int(value)) for value in row] for row in matrix.tolist()]
    row_count = len(values)
    column_count = len(values[0]) if values else 0
    rank = 0
    for column in range(column_count):
        pivot = next((row for row in range(rank, row_count) if values[row][column]), None)
        if pivot is None:
            continue
        values[rank], values[pivot] = values[pivot], values[rank]
        pivot_value = values[rank][column]
        for index in range(column, column_count):
            values[rank][index] /= pivot_value
        for row in range(rank + 1, row_count):
            factor = values[row][column]
            if not factor:
                continue
            for index in range(column, column_count):
                values[row][index] -= factor * values[rank][index]
        rank += 1
        if rank == row_count:
            break
    return rank


def _spectral_report(np: Any, adjacency: Any, s: int) -> dict[str, Any]:
    size = adjacency.shape[0]
    exact_nullity = size - _exact_rank(adjacency)
    eigenvalues, eigenvectors = np.linalg.eigh(adjacency.astype(np.float64))
    order = np.argsort(np.abs(eigenvalues), kind="stable")
    zero_indices = order[:exact_nullity]
    nonzero_indices = order[exact_nullity:]
    numerical_zero_error = (
        float(np.max(np.abs(eigenvalues[zero_indices]))) if exact_nullity else 0.0
    )
    if numerical_zero_error > ZERO_TOLERANCE:
        _fail("exact nullity disagrees with numerical zero sector")
    projector = (
        eigenvectors[:, zero_indices] @ eigenvectors[:, zero_indices].T
        if exact_nullity else np.zeros_like(adjacency, dtype=np.float64)
    )
    entrance = _index(s, 0, 0)
    exit_state = _index(s, 5, s)
    entrance_weight = float(projector[entrance, entrance])
    exit_weight = float(projector[exit_state, exit_state])
    transfer = float(abs(projector[exit_state, entrance]))
    gap = float(abs(eigenvalues[nonzero_indices[0]])) if len(nonzero_indices) else 0.0
    score = transfer * math.sqrt(max(0.0, entrance_weight * exit_weight)) * gap
    return {
        "exact_nullity": exact_nullity,
        "numerical_zero_error": numerical_zero_error,
        "entrance_zero_weight": entrance_weight,
        "exit_zero_weight": exit_weight,
        "zero_sector_transfer": transfer,
        "nearest_nonzero_gap": gap,
        "preregistered_score": score,
    }


def _topology_counts(adjacency: Any) -> dict[str, Any]:
    upper = adjacency.copy()
    import numpy as np
    upper[np.tril_indices(adjacency.shape[0])] = 0
    return {
        "vertices": adjacency.shape[0],
        "unique_edges": int(np.count_nonzero(upper)),
        "weighted_edge_channels": int(upper.sum()),
        "minimum_weighted_degree": int(adjacency.sum(axis=1).min()),
        "maximum_weighted_degree": int(adjacency.sum(axis=1).max()),
        "connected": _connected(adjacency),
    }


def _analyse_candidate_grid(np: Any, s: int, rows: int) -> dict[str, Any]:
    destinations = tuple(range(1, rows))
    adjacency = _candidate_adjacency(np, s, rows, destinations)
    false_left = _index(s, rows - 1, s)
    false_right = _index(s, 0, 0)
    if (false_left, false_right) in _matching_edges(s, destinations):
        _fail("false periodic overlap edge was introduced")
    refined = _equitable_refinement(adjacency, _seed_partition(s, rows))
    partitions = {
        "rows": _row_partition(s, rows),
        "columns": _column_partition(s, rows),
        "overlap-fibers-and-interior-columns": _overlap_fiber_partition(s, rows),
        "reflection-orbits": _reflection_partition(s, rows),
        "endpoint-seeded-equitable-refinement": refined,
    }
    partition_reports = {
        name: _partition_report(np, adjacency, cells, s)
        for name, cells in partitions.items()
    }
    hierarchy_available = any(
        report["exactly_equitable"]
        and report["endpoint_representing"]
        and report["endpoints_separate"]
        and report["cell_count"] < adjacency.shape[0]
        for report in partition_reports.values()
    )
    bipartite = _bipartite_report(np, adjacency)
    spectral = _spectral_report(np, adjacency, s)
    structural_pass = (
        hierarchy_available
        and bipartite["bipartite"]
        and bipartite["chiral_residual"] == 0
        and spectral["exact_nullity"] >= 1
        and spectral["entrance_zero_weight"] > SUPPORT_TOLERANCE
        and spectral["exit_zero_weight"] > SUPPORT_TOLERANCE
        and spectral["zero_sector_transfer"] > SUPPORT_TOLERANCE
        and spectral["nearest_nonzero_gap"] > SUPPORT_TOLERANCE
    )
    return {
        "s": s,
        "R": rows,
        "entrance": [0, 0],
        "exit": [rows - 1, s],
        "genuine_overlap_edges": rows - 1,
        "false_periodic_overlap_edge": False,
        "topology": _topology_counts(adjacency),
        "partitions": partition_reports,
        "hierarchical_endpoint_quotient_available": hierarchy_available,
        "bipartite_chiral": bipartite,
        "spectrum": spectral,
        "structural_gate_pass": structural_pass,
    }


def _analyse_controls(np: Any, s: int, rows: int) -> list[dict[str, Any]]:
    identity = tuple(range(1, rows))
    records: list[dict[str, Any]] = []
    for destinations in itertools.permutations(range(1, rows)):
        if destinations == identity:
            continue
        adjacency = _candidate_adjacency(np, s, rows, destinations)
        records.append({
            "destinations": list(destinations),
            "topology": _topology_counts(adjacency),
            "bipartite_chiral": _bipartite_report(np, adjacency),
            "spectrum": _spectral_report(np, adjacency, s),
        })
    if len(records) != 119:
        _fail("matched control count changed")
    return records


def _percentile(candidate_score: float, controls: list[dict[str, Any]]) -> float:
    values = [candidate_score] + [record["spectrum"]["preregistered_score"] for record in controls]
    return sum(value <= candidate_score for value in values) / len(values)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _require_empty_directory(path: Path) -> Path:
    if path.is_symlink() or not path.exists() or not path.is_dir():
        _fail("output must be an existing non-symlink directory")
    if any(path.iterdir()):
        _fail("output directory must be empty")
    if not stat.S_ISDIR(path.stat().st_mode):
        _fail("output is not a regular directory")
    return path


def run(design_path: Path, output_directory: Path) -> dict[str, Any]:
    if not sys.platform.startswith("linux"):
        _fail("formal probe requires Linux")
    if os.environ.get("ZERO_MODE_IMAGE_DIGEST") != EXPECTED_IMAGE:
        _fail("exact image binding is missing or incorrect")
    if os.environ.get("ZERO_MODE_CONTAINER_NAME") != EXPECTED_CONTAINER:
        _fail("named container binding is missing or incorrect")
    simulator = Path(__file__).resolve().parent
    root = simulator.parents[1]
    expected_design = root / "data" / "area-one-eog-zero-mode-probe-design-2026-08-16.md"
    expected_output = simulator / "eog-zero-mode-topology-probe-output"
    if design_path.resolve() != expected_design.resolve():
        _fail("unexpected probe design path")
    if output_directory.resolve() != expected_output.resolve():
        _fail("unexpected probe output path")
    output = _require_empty_directory(output_directory)
    design_bytes = design_path.read_bytes()
    source_bytes = Path(__file__).read_bytes()

    import numpy as np
    if np.__version__ != "2.4.2":
        _fail("NumPy version is not the frozen research version")

    grids = []
    control_records: dict[str, Any] = {}
    for s, rows in GRIDS:
        candidate = _analyse_candidate_grid(np, s, rows)
        controls = _analyse_controls(np, s, rows)
        percentile = _percentile(candidate["spectrum"]["preregistered_score"], controls)
        candidate["matched_control_percentile"] = percentile
        candidate["grid_mechanism_pass"] = candidate["structural_gate_pass"] and percentile >= 0.95
        grids.append(candidate)
        control_records[f"s={s},R={rows}"] = controls

    mechanism_supported = all(record["grid_mechanism_pass"] for record in grids)
    result = {
        "schema_version": SCHEMA_VERSION,
        "dataset_kind": "pre-protocol-topology-only-discovery",
        "model": "natural-unweighted-continuous-time-position-adjacency-surrogate",
        "source_sha256": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
        "design_sha256": "sha256:" + hashlib.sha256(design_bytes).hexdigest(),
        "runtime": {
            "required_image": EXPECTED_IMAGE,
            "container_name": EXPECTED_CONTAINER,
            "container_id": os.environ.get("HOSTNAME", ""),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "tolerances": {
            "closure": CLOSURE_TOLERANCE,
            "numerical_zero_consistency": ZERO_TOLERANCE,
            "support_transfer_gap": SUPPORT_TOLERANCE,
        },
        "candidate_grids": grids,
        "matched_controls": control_records,
        "counts": {
            "development_grids": len(GRIDS),
            "matched_controls_per_grid": 119,
            "total_matched_controls": 357,
            "lock_accesses": 0,
            "heldout_accesses": 0,
            "t9_runs": 0,
        },
        "boundary_record": {
            "lock_access": "NONE",
            "heldout_access": "NONE",
            "heldout_execution": False,
            "new_t9_started": False,
            "outcome_artifact_read": False,
        },
        "mechanism_supported": mechanism_supported,
        "disposition": "supported-for-new-protocol-design" if mechanism_supported else "natural-zero-mode-mechanism-not-supported",
    }
    body = _canonical_bytes(result)
    destination = output / RESULT_FILENAME
    temporary = output / (RESULT_FILENAME + ".tmp")
    temporary.write_bytes(body)
    os.replace(temporary, destination)
    if destination.read_bytes() != body:
        _fail("published artifact verification failed")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args.design, args.output)
    print("EOG_ZERO_MODE_TOPOLOGY_PROBE_PASS", flush=True)
    print("mechanism_supported=" + str(result["mechanism_supported"]).lower(), flush=True)
    for record in result["candidate_grids"]:
        spectrum = record["spectrum"]
        print(
            "grid=" + json.dumps({
                "s": record["s"],
                "R": record["R"],
                "bipartite": record["bipartite_chiral"]["bipartite"],
                "nullity": spectrum["exact_nullity"],
                "entrance_weight": spectrum["entrance_zero_weight"],
                "exit_weight": spectrum["exit_zero_weight"],
                "transfer": spectrum["zero_sector_transfer"],
                "gap": spectrum["nearest_nonzero_gap"],
                "hierarchy": record["hierarchical_endpoint_quotient_available"],
                "percentile": record["matched_control_percentile"],
                "pass": record["grid_mechanism_pass"],
            }, sort_keys=True),
            flush=True,
        )
    print("no_lock=true heldout_executed=false new_t9_started=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())