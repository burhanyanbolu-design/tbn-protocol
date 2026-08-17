#!/usr/bin/env python3
"""Generate a deterministic, integrity-hashed Area One verification report."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from boundary_policies import BOUNDARY_POLICIES, evaluate_boundary
from eog_quantum_walk import EOGQuantumWalk
from evaluation_metrics import evaluate_protocol
from exact_density_channel import run_exact_density_channel
from monte_carlo_convergence import run_convergence_study
from operator_matrix_verification import build_operator_matrix, maximum_unitarity_error
from simulator import Position, parse_position
from topology_baseline import compare_topologies


SCHEMA_VERSION = "area-one-verification-report/1.0"
LIMITATIONS = (
    "This is a classical software simulation, not execution on quantum hardware.",
    "The Grover walk and phase-noise channel are established baseline models.",
    "EOG display labels are metadata and do not change the quantum dynamics.",
    "Logical operation counts are not compiled device gate counts.",
    "The toy phase-noise model is not calibrated to a physical device.",
    "Passing checks does not establish quantum advantage, novelty or market demand.",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def report_digest(report_without_hash: dict[str, Any]) -> str:
    payload = canonical_json(report_without_hash).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def verify_report_hash(report: dict[str, Any]) -> bool:
    claimed = report.get("report_hash")
    body = copy.deepcopy(report)
    body.pop("report_hash", None)
    return isinstance(claimed, str) and claimed == report_digest(body)


def position_data(position: Position) -> dict[str, int]:
    return {"row": position.row, "column": position.column}


def build_verification_report(
    step: int = 3,
    rows: int = 5,
    evolution_steps: int = 12,
    start: Position = Position(0, 0),
    terminal: Position = Position(1, 0),
    noise_probability: float = 0.1,
    trajectories: int = 1000,
    seed: int = 20260815,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    walk = EOGQuantumWalk(step, rows, {terminal})
    walk.require_valid(start, "start")
    operator_error = maximum_unitarity_error(build_operator_matrix(walk))
    topology = compare_topologies(walk, start, evolution_steps)

    boundaries = {
        policy: evaluate_boundary(walk, policy, start, evolution_steps, tolerance)
        for policy in BOUNDARY_POLICIES
    }
    intervals = (1, 3, evolution_steps)
    protocols = [
        evaluate_protocol(
            walk,
            start,
            evolution_steps,
            interval,
            "repeated" if interval == 1 else (
                "final-only" if interval == evolution_steps else f"every-{interval}"
            ),
        )
        for interval in intervals
    ]
    exact_noise = run_exact_density_channel(
        walk, start, evolution_steps, noise_probability
    )
    convergence = run_convergence_study(
        walk,
        start,
        evolution_steps,
        noise_probability,
        (trajectories,),
        seed,
    )[0]
    sampling_passed = convergence.absolute_error <= 3.0 * convergence.standard_error
    checks = {
        "operator_unitary": operator_error <= tolerance,
        "topology_amplitudes_match": topology.maximum_amplitude_difference <= tolerance,
        "topology_absorption_matches": abs(
            topology.eog_absorption - topology.indexed_absorption
        ) <= tolerance,
        "periodic_boundary_unitary": boundaries["periodic"].classification == "unitary",
        "reflective_boundary_unitary": boundaries["reflective"].classification == "unitary",
        "absorbing_boundary_declared_non_unitary": (
            boundaries["absorbing"].classification == "non-unitary"
        ),
        "exact_probability_accounting": (
            exact_noise.maximum_probability_error <= tolerance
        ),
        "monte_carlo_within_three_standard_errors": sampling_passed,
    }

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "configuration": {
            "step": step,
            "rows": rows,
            "width": step + 1,
            "evolution_steps": evolution_steps,
            "start": position_data(start),
            "terminal": position_data(terminal),
            "noise_probability": noise_probability,
            "trajectories": trajectories,
            "seed": seed,
            "tolerance": tolerance,
        },
        "checks": checks,
        "results": {
            "coordinate_identity": {
                "full_coordinate_states": topology.coordinate_states,
                "unique_display_labels": topology.unique_display_labels,
                "ordinary_indexed_nodes": topology.indexed_nodes,
            },
            "operator": {
                "hilbert_dimension": rows * (step + 1) * 4,
                "maximum_u_dagger_u_error": operator_error,
            },
            "topology_baseline": {
                "maximum_amplitude_difference": topology.maximum_amplitude_difference,
                "eog_absorption": topology.eog_absorption,
                "indexed_absorption": topology.indexed_absorption,
            },
            "boundaries": {
                policy: {
                    "classification": result.classification,
                    "maximum_u_dagger_u_error": result.maximum_unitarity_error,
                    "final_norm": result.final_norm,
                    "boundary_loss": result.boundary_loss,
                }
                for policy, result in boundaries.items()
            },
            "measurement_protocols": [
                {
                    "name": protocol.name,
                    "interval": protocol.measurement_interval,
                    "terminal_probability": protocol.terminal_probability,
                    "conditional_mean_detection_step": (
                        protocol.conditional_mean_detection_step
                    ),
                    "measurement_checks": protocol.measurement_checks,
                }
                for protocol in protocols
            ],
            "phase_noise": {
                "exact_absorption": exact_noise.absorbed_probability,
                "exact_survival": exact_noise.surviving_probability,
                "exact_normalized_l1_coherence": (
                    exact_noise.normalized_l1_coherence
                ),
                "exact_purity": exact_noise.purity,
                "monte_carlo_absorption": convergence.estimated_absorption,
                "absolute_sampling_error": convergence.absolute_error,
                "standard_error": convergence.standard_error,
                "confidence_95": [
                    convergence.confidence_low,
                    convergence.confidence_high,
                ],
            },
        },
        "verdict": {
            "passed": all(checks.values()),
            "supported": [
                "The configured software operator satisfies the numerical checks.",
                "The declared measurement and boundary semantics are reproducible.",
                "The Monte Carlo sampler agrees with its exact toy-channel oracle.",
            ],
            "not_supported": list(LIMITATIONS),
        },
    }
    report = copy.deepcopy(body)
    report["report_hash"] = report_digest(body)
    return report


def write_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an integrity-hashed Area One verification report."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    parser.add_argument("--noise", type=float, default=0.1)
    parser.add_argument("--trajectories", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--tolerance", type=float, default=1e-12)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = build_verification_report(
            args.step,
            args.rows,
            args.steps,
            args.start,
            args.terminal,
            args.noise,
            args.trajectories,
            args.seed,
            args.tolerance,
        )
        if not verify_report_hash(report):
            raise RuntimeError("generated report hash failed verification")
        if args.output:
            write_report(report, args.output)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    if args.output:
        print(f"report_written={args.output}")
        print(f"report_hash={report['report_hash']}")
        print(f"verdict_passed={report['verdict']['passed']}")
    else:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["verdict"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
