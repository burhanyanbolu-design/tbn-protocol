#!/usr/bin/env python3
"""Evaluation metrics for EOG terminal-measurement protocols."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from eog_quantum_walk import EOGQuantumWalk
from quantum_walk_baseline import WalkResult, verify_probability_accounting
from simulator import Position, parse_position


@dataclass(frozen=True)
class ProtocolEvaluation:
    name: str
    measurement_interval: int
    terminal_probability: float
    conditional_mean_detection_step: float | None
    measurement_checks: int
    logical_coin_applications: int
    logical_shift_applications: int
    maximum_unitary_norm_error: float


def scheduled_measurement_steps(steps: int, interval: int) -> tuple[int, ...]:
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if interval < 1:
        raise ValueError("interval must be at least 1")
    scheduled = set(range(interval, steps + 1, interval))
    scheduled.add(steps)
    return tuple(sorted(scheduled))


def conditional_mean_detection_step(result: WalkResult) -> float | None:
    total = result.cumulative_absorption
    if math.isclose(total, 0.0, abs_tol=1e-15):
        return None
    weighted = sum(
        metric.step * metric.absorbed_probability for metric in result.metrics
    )
    return weighted / total


def evaluate_protocol(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    interval: int,
    name: str,
) -> ProtocolEvaluation:
    result = walk.run_with_measurement_interval(start, steps, interval)
    verify_probability_accounting(result)
    maximum_error = max(
        (metric.unitary_norm_error for metric in result.metrics), default=0.0
    )
    return ProtocolEvaluation(
        name=name,
        measurement_interval=interval,
        terminal_probability=result.cumulative_absorption,
        conditional_mean_detection_step=conditional_mean_detection_step(result),
        measurement_checks=len(scheduled_measurement_steps(steps, interval)),
        logical_coin_applications=steps,
        logical_shift_applications=steps,
        maximum_unitary_norm_error=maximum_error,
    )


def parse_intervals(text: str) -> tuple[int, ...]:
    try:
        intervals = tuple(int(item.strip()) for item in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("intervals must be comma-separated integers") from exc
    if not intervals or any(interval < 1 for interval in intervals):
        raise argparse.ArgumentTypeError("intervals must contain positive integers")
    return intervals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report measurement and detection metrics for EOG protocols."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--intervals", type=parse_intervals, default=(1, 3, 12))
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, {args.terminal})
        evaluations = tuple(
            evaluate_protocol(
                walk,
                args.start,
                args.steps,
                interval,
                "repeated" if interval == 1 else (
                    "final-only" if interval >= args.steps else f"every-{interval}"
                ),
            )
            for interval in args.intervals
        )
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Area One measurement and termination evaluation")
    print(f"grid={args.rows}x{walk.width} steps={args.steps} terminal={args.terminal}")
    print("protocol | terminal_p | mean_detection_step | checks | coin_ops | shift_ops")
    for item in evaluations:
        mean_step = (
            "none"
            if item.conditional_mean_detection_step is None
            else f"{item.conditional_mean_detection_step:.3f}"
        )
        print(
            f"{item.name:>10} | {item.terminal_probability:>10.6f} | "
            f"{mean_step:>19} | {item.measurement_checks:>6} | "
            f"{item.logical_coin_applications:>8} | {item.logical_shift_applications:>9}"
        )
    print("Checks and operator applications are logical counts, not hardware gate costs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
