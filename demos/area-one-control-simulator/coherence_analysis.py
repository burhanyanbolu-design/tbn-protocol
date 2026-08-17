#!/usr/bin/env python3
"""Estimate surviving-state coherence for the toy phase-noise ensemble."""

from __future__ import annotations

import argparse
import random
from collections import defaultdict
from dataclasses import dataclass

from eog_quantum_walk import DIRECTION_COUNT, EOGQuantumWalk
from noise_sensitivity import parse_probabilities, run_noisy_trajectory
from simulator import Position, parse_position


@dataclass(frozen=True)
class CoherenceSummary:
    phase_flip_probability: float
    trajectories: int
    mean_survival: float
    l1_coherence: float
    normalized_l1_coherence: float
    purity: float


def basis_index(walk: EOGQuantumWalk) -> dict[tuple[Position, int], int]:
    return {
        (Position(row, column), direction): (
            (row * walk.width + column) * DIRECTION_COUNT + direction
        )
        for row in range(walk.rows)
        for column in range(walk.width)
        for direction in range(DIRECTION_COUNT)
    }


def run_coherence_ensemble(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    phase_flip_probability: float,
    trajectories: int,
    seed: int,
    measurement_interval: int = 1,
) -> CoherenceSummary:
    if trajectories < 1:
        raise ValueError("trajectories must be at least 1")

    index = basis_index(walk)
    dimension = len(index)
    density: defaultdict[tuple[int, int], complex] = defaultdict(complex)
    random_source = random.Random(seed)
    survival_total = 0.0

    for _trajectory in range(trajectories):
        result = run_noisy_trajectory(
            walk,
            start,
            steps,
            phase_flip_probability,
            random_source,
            measurement_interval,
        )
        state = result.final_state
        survival_total += sum(abs(amplitude) ** 2 for amplitude in state.values())
        ordered = sorted(
            state.items(),
            key=lambda item: index[item[0]],
        )
        for left_key, left_amplitude in ordered:
            left_index = index[left_key]
            for right_key, right_amplitude in ordered:
                density[(left_index, index[right_key])] += (
                    left_amplitude * right_amplitude.conjugate() / trajectories
                )

    trace = sum(
        value.real for (row, column), value in density.items() if row == column
    )
    if trace <= 1e-15:
        raise RuntimeError("coherence is undefined because no probability survived")

    normalized_density = {key: value / trace for key, value in density.items()}
    l1_coherence = sum(
        abs(value)
        for (row, column), value in normalized_density.items()
        if row != column
    )
    purity = sum(abs(value) ** 2 for value in normalized_density.values())
    return CoherenceSummary(
        phase_flip_probability=phase_flip_probability,
        trajectories=trajectories,
        mean_survival=survival_total / trajectories,
        l1_coherence=l1_coherence,
        normalized_l1_coherence=l1_coherence / (dimension - 1),
        purity=purity,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estimate coherence after toy phase noise and absorption."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    parser.add_argument("--noise", type=parse_probabilities, default=(0.0, 0.01, 0.05, 0.1))
    parser.add_argument("--trajectories", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--measurement-interval", type=int, default=1)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, {args.terminal})
        summaries = tuple(
            run_coherence_ensemble(
                walk,
                args.start,
                args.steps,
                probability,
                args.trajectories,
                args.seed,
                args.measurement_interval,
            )
            for probability in args.noise
        )
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    dimension = args.rows * (args.step + 1) * DIRECTION_COUNT
    print("EOG surviving-state coherence under toy phase noise")
    print(f"basis_dimension={dimension} trajectories={args.trajectories}")
    print("phase_flip | survival | normalized_l1 | purity")
    for summary in summaries:
        print(
            f"{summary.phase_flip_probability:>10.3f} | "
            f"{summary.mean_survival:>8.6f} | "
            f"{summary.normalized_l1_coherence:>13.6f} | "
            f"{summary.purity:>6.6f}"
        )
    print("Metrics condition on survival and describe only the toy ensemble channel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
