#!/usr/bin/env python3
"""Compare terminal-measurement schedules for the EOG Grover walk."""

from __future__ import annotations

import argparse

from eog_quantum_walk import EOGQuantumWalk
from quantum_walk_baseline import WalkResult, verify_probability_accounting
from simulator import Position, parse_position


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare repeated, periodic, and final-only measurement."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--interval", type=int, default=3)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    return parser


def measured_steps(result: WalkResult) -> tuple[int, ...]:
    return tuple(
        metric.step for metric in result.metrics if metric.absorbed_probability > 0.0
    )


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, {args.terminal})
        protocols = (
            ("repeated", 1),
            (f"periodic-{args.interval}", args.interval),
            ("final-only", args.steps),
        )
        results = {
            name: walk.run_with_measurement_interval(
                args.start, args.steps, interval
            )
            for name, interval in protocols
        }
        for result in results.values():
            verify_probability_accounting(result)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("EOG terminal-measurement protocol comparison")
    print(f"start={args.start} terminal={args.terminal} steps={args.steps}")
    for name, result in results.items():
        print(
            f"{name}: absorbed={result.cumulative_absorption:.6f} "
            f"surviving={result.final_surviving_probability:.6f} "
            f"nonzero_detection_steps={measured_steps(result)}"
        )
    difference = (
        results["repeated"].cumulative_absorption
        - results["final-only"].cumulative_absorption
    )
    print(f"repeated_minus_final_absorption={difference:.6f}")
    print("Measurement schedule is part of the model and changes its dynamics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
