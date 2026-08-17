#!/usr/bin/env python3
"""Exhaustive bounded parameter sweep for Area One invariants."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from eog_quantum_walk import EOGQuantumWalk
from operator_matrix_verification import build_operator_matrix, maximum_unitarity_error
from quantum_walk_baseline import WalkResult, verify_probability_accounting
from simulator import Position


@dataclass(frozen=True)
class SweepSummary:
    grids_checked: int
    operator_checks: int
    quantum_protocol_runs: int
    classical_runs: int
    overlap_identity_checks: int
    maximum_unitarity_error: float
    maximum_step_norm_error: float
    maximum_probability_error: float


def grid_positions(step: int, rows: int) -> tuple[Position, ...]:
    return tuple(
        Position(row, column)
        for row in range(rows)
        for column in range(step + 1)
    )


def probability_error(result: WalkResult) -> float:
    return abs(
        result.final_surviving_probability
        + result.cumulative_absorption
        - 1.0
    )


def run_parameter_sweep(
    maximum_step: int = 3,
    maximum_rows: int = 3,
    evolution_steps: int = 4,
    tolerance: float = 1e-12,
) -> SweepSummary:
    if maximum_step < 1 or maximum_rows < 1 or evolution_steps < 1:
        raise ValueError("maximum_step, maximum_rows and evolution_steps must be positive")

    intervals = tuple(sorted({1, 2, evolution_steps}))
    grids_checked = 0
    operator_checks = 0
    quantum_runs = 0
    classical_runs = 0
    overlap_checks = 0
    maximum_operator_error = 0.0
    maximum_norm_error = 0.0
    maximum_accounting_error = 0.0

    for step in range(1, maximum_step + 1):
        for rows in range(1, maximum_rows + 1):
            grids_checked += 1
            coordinate_model = EOGQuantumWalk(step, rows, set())
            matrix = build_operator_matrix(coordinate_model)
            operator_error = maximum_unitarity_error(matrix)
            maximum_operator_error = max(maximum_operator_error, operator_error)
            operator_checks += 1

            for row in range(rows - 1):
                endpoint = Position(row, step)
                next_row = Position(row + 1, 0)
                if endpoint == next_row:
                    raise RuntimeError("overlapping coordinates were merged")
                if coordinate_model.label(endpoint) != coordinate_model.label(next_row):
                    raise RuntimeError("expected overlapping labels do not match")
                overlap_checks += 1

            positions = grid_positions(step, rows)
            for terminal in positions:
                walk = EOGQuantumWalk(step, rows, {terminal})
                for start in positions:
                    classical = walk.run_classical(start, evolution_steps)
                    verify_probability_accounting(classical, tolerance)
                    maximum_accounting_error = max(
                        maximum_accounting_error, probability_error(classical)
                    )
                    classical_runs += 1

                    for interval in intervals:
                        quantum = walk.run_with_measurement_interval(
                            start, evolution_steps, interval
                        )
                        verify_probability_accounting(quantum, tolerance)
                        maximum_accounting_error = max(
                            maximum_accounting_error, probability_error(quantum)
                        )
                        maximum_norm_error = max(
                            maximum_norm_error,
                            max(
                                (
                                    metric.unitary_norm_error
                                    for metric in quantum.metrics
                                ),
                                default=0.0,
                            ),
                        )
                        quantum_runs += 1

    if maximum_operator_error > tolerance:
        raise RuntimeError("an operator failed the unitarity tolerance")
    if maximum_norm_error > tolerance or maximum_accounting_error > tolerance:
        raise RuntimeError("a walk failed numerical invariants")

    return SweepSummary(
        grids_checked=grids_checked,
        operator_checks=operator_checks,
        quantum_protocol_runs=quantum_runs,
        classical_runs=classical_runs,
        overlap_identity_checks=overlap_checks,
        maximum_unitarity_error=maximum_operator_error,
        maximum_step_norm_error=maximum_norm_error,
        maximum_probability_error=maximum_accounting_error,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exhaustively check bounded Area One parameter combinations."
    )
    parser.add_argument("--maximum-step", type=int, default=3)
    parser.add_argument("--maximum-rows", type=int, default=3)
    parser.add_argument("--evolution-steps", type=int, default=4)
    parser.add_argument("--tolerance", type=float, default=1e-12)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        summary = run_parameter_sweep(
            args.maximum_step,
            args.maximum_rows,
            args.evolution_steps,
            args.tolerance,
        )
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Area One exhaustive bounded parameter sweep")
    print(f"grids_checked={summary.grids_checked}")
    print(f"operator_checks={summary.operator_checks}")
    print(f"quantum_protocol_runs={summary.quantum_protocol_runs}")
    print(f"classical_runs={summary.classical_runs}")
    print(f"overlap_identity_checks={summary.overlap_identity_checks}")
    print(f"maximum_unitarity_error={summary.maximum_unitarity_error:.3e}")
    print(f"maximum_step_norm_error={summary.maximum_step_norm_error:.3e}")
    print(f"maximum_probability_error={summary.maximum_probability_error:.3e}")
    print("PASS all bounded parameter combinations satisfied their invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
