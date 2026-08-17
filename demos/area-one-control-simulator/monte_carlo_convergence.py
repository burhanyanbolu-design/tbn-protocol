#!/usr/bin/env python3
"""Monte Carlo convergence study against the exact phase-noise oracle."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from eog_quantum_walk import EOGQuantumWalk
from exact_density_channel import run_exact_density_channel
from noise_sensitivity import run_noisy_ensemble
from simulator import Position, parse_position


@dataclass(frozen=True)
class ConvergencePoint:
    trajectories: int
    estimated_absorption: float
    exact_absorption: float
    absolute_error: float
    standard_error: float
    confidence_low: float
    confidence_high: float
    exact_inside_95_percent_interval: bool


def parse_sample_sizes(text: str) -> tuple[int, ...]:
    try:
        values = tuple(sorted({int(item.strip()) for item in text.split(",")}))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "sample sizes must be comma-separated integers"
        ) from exc
    if not values or any(value < 2 for value in values):
        raise argparse.ArgumentTypeError("every sample size must be at least 2")
    return values


def run_convergence_study(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    phase_flip_probability: float,
    sample_sizes: tuple[int, ...],
    seed: int,
    measurement_interval: int = 1,
) -> tuple[ConvergencePoint, ...]:
    if not sample_sizes or any(size < 2 for size in sample_sizes):
        raise ValueError("sample_sizes must contain values of at least 2")
    exact = run_exact_density_channel(
        walk, start, steps, phase_flip_probability, measurement_interval
    )
    points: list[ConvergencePoint] = []

    for trajectories in sorted(set(sample_sizes)):
        sampled = run_noisy_ensemble(
            walk,
            start,
            steps,
            phase_flip_probability,
            trajectories,
            seed,
            measurement_interval,
        )
        sample_standard_deviation = sampled.absorption_standard_deviation * math.sqrt(
            trajectories / (trajectories - 1)
        )
        standard_error = sample_standard_deviation / math.sqrt(trajectories)
        margin = 1.96 * standard_error
        confidence_low = max(0.0, sampled.mean_absorption - margin)
        confidence_high = min(1.0, sampled.mean_absorption + margin)

        points.append(
            ConvergencePoint(
                trajectories=trajectories,
                estimated_absorption=sampled.mean_absorption,
                exact_absorption=exact.absorbed_probability,
                absolute_error=abs(
                    sampled.mean_absorption - exact.absorbed_probability
                ),
                standard_error=standard_error,
                confidence_low=confidence_low,
                confidence_high=confidence_high,
                exact_inside_95_percent_interval=(
                    confidence_low
                    <= exact.absorbed_probability
                    <= confidence_high
                ),
            )
        )
    return tuple(points)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure Monte Carlo convergence against exact density evolution."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    parser.add_argument("--noise", type=float, default=0.1)
    parser.add_argument(
        "--sample-sizes",
        type=parse_sample_sizes,
        default=(100, 500, 1000, 5000),
    )
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--measurement-interval", type=int, default=1)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, {args.terminal})
        points = run_convergence_study(
            walk,
            args.start,
            args.steps,
            args.noise,
            args.sample_sizes,
            args.seed,
            args.measurement_interval,
        )
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Area One Monte Carlo convergence against exact density oracle")
    print(f"noise={args.noise} seed={args.seed} exact={points[0].exact_absorption:.6f}")
    print("samples | estimate | abs_error | std_error | 95% interval | contains_exact")
    for point in points:
        print(
            f"{point.trajectories:>7} | {point.estimated_absorption:.6f} | "
            f"{point.absolute_error:.6f} | {point.standard_error:.6f} | "
            f"[{point.confidence_low:.6f}, {point.confidence_high:.6f}] | "
            f"{point.exact_inside_95_percent_interval}"
        )
    print("Intervals use a normal approximation and nested seeded trajectories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
