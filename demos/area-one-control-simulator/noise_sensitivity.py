#!/usr/bin/env python3
"""Toy phase-noise sensitivity experiment for the EOG Grover walk."""

from __future__ import annotations

import argparse
import math
import random
import statistics
from dataclasses import dataclass

from eog_quantum_walk import DIRECTION_COUNT, EOGQuantumWalk, QuantumState, grover_step, state_norm
from simulator import Position, parse_position


@dataclass(frozen=True)
class NoiseSummary:
    phase_flip_probability: float
    trajectories: int
    mean_absorption: float
    absorption_standard_deviation: float
    mean_survival: float
    maximum_norm_error: float
    maximum_probability_error: float


@dataclass(frozen=True)
class NoisyTrajectory:
    final_state: QuantumState
    absorbed_probability: float
    maximum_norm_error: float


def apply_phase_noise(
    state: QuantumState,
    probability: float,
    random_source: random.Random,
) -> QuantumState:
    """Apply independent random pi phase flips to basis amplitudes."""
    noisy: QuantumState = {}
    ordered_keys = sorted(
        state,
        key=lambda item: (item[0].row, item[0].column, item[1]),
    )
    for key in ordered_keys:
        amplitude = state[key]
        noisy[key] = -amplitude if random_source.random() < probability else amplitude
    return noisy


def run_noisy_trajectory(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    phase_flip_probability: float,
    random_source: random.Random,
    measurement_interval: int = 1,
) -> NoisyTrajectory:
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if not 0.0 <= phase_flip_probability <= 1.0:
        raise ValueError("phase_flip_probability must be between 0 and 1")
    if measurement_interval < 1:
        raise ValueError("measurement_interval must be at least 1")
    walk.require_valid(start, "start")
    if start in walk.terminals:
        return NoisyTrajectory({}, 1.0, 0.0)

    state: QuantumState = {
        (start, direction): 0.5 + 0j for direction in range(DIRECTION_COUNT)
    }
    cumulative = 0.0
    maximum_norm_error = 0.0

    for step_number in range(1, steps + 1):
        norm_before = state_norm(state)
        evolved = grover_step(state, walk.rows, walk.width)
        norm_after_unitary = state_norm(evolved)
        noisy = apply_phase_noise(evolved, phase_flip_probability, random_source)
        norm_after_noise = state_norm(noisy)
        maximum_norm_error = max(
            maximum_norm_error,
            abs(norm_after_unitary - norm_before),
            abs(norm_after_noise - norm_after_unitary),
        )
        should_measure = (
            step_number % measurement_interval == 0 or step_number == steps
        )
        if should_measure:
            absorbed = sum(
                abs(amplitude) ** 2
                for (position, _direction), amplitude in noisy.items()
                if position in walk.terminals
            )
            cumulative += absorbed
            noisy = {
                key: amplitude
                for key, amplitude in noisy.items()
                if key[0] not in walk.terminals
            }
        state = noisy

    return NoisyTrajectory(state, cumulative, maximum_norm_error)


def run_noisy_ensemble(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    phase_flip_probability: float,
    trajectories: int,
    seed: int,
    measurement_interval: int = 1,
) -> NoiseSummary:
    if trajectories < 1:
        raise ValueError("trajectories must be at least 1")

    random_source = random.Random(seed)
    results = [
        run_noisy_trajectory(
            walk,
            start,
            steps,
            phase_flip_probability,
            random_source,
            measurement_interval,
        )
        for _trajectory in range(trajectories)
    ]
    absorptions = [result.absorbed_probability for result in results]
    survivals = [state_norm(result.final_state) for result in results]
    maximum_norm_error = max(result.maximum_norm_error for result in results)
    maximum_probability_error = max(
        abs(absorbed + surviving - 1.0)
        for absorbed, surviving in zip(absorptions, survivals)
    )

    return NoiseSummary(
        phase_flip_probability=phase_flip_probability,
        trajectories=trajectories,
        mean_absorption=statistics.fmean(absorptions),
        absorption_standard_deviation=statistics.pstdev(absorptions),
        mean_survival=statistics.fmean(survivals),
        maximum_norm_error=maximum_norm_error,
        maximum_probability_error=maximum_probability_error,
    )


def parse_probabilities(text: str) -> tuple[float, ...]:
    try:
        values = tuple(float(item.strip()) for item in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("noise values must be comma-separated numbers") from exc
    if not values or any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise argparse.ArgumentTypeError("noise values must be finite numbers from 0 to 1")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure sensitivity to a toy random phase-flip channel."
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
            run_noisy_ensemble(
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
        if any(
            summary.maximum_norm_error > 1e-12
            or summary.maximum_probability_error > 1e-12
            for summary in summaries
        ):
            raise RuntimeError("noise experiment failed numerical accounting")
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("EOG toy phase-noise sensitivity (classical Monte Carlo simulation)")
    print(f"trajectories={args.trajectories} seed={args.seed} steps={args.steps}")
    print("phase_flip | mean_absorbed | stddev | mean_surviving")
    for summary in summaries:
        print(
            f"{summary.phase_flip_probability:>10.3f} | "
            f"{summary.mean_absorption:>13.6f} | "
            f"{summary.absorption_standard_deviation:>6.6f} | "
            f"{summary.mean_survival:>14.6f}"
        )
    print("Noise model is uncalibrated and results are not hardware predictions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
