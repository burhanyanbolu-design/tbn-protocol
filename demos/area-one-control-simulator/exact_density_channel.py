#!/usr/bin/env python3
"""Exact density-matrix oracle for the toy independent phase-flip channel."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from coherence_analysis import run_coherence_ensemble
from eog_quantum_walk import DIRECTION_COUNT, EOGQuantumWalk
from noise_sensitivity import run_noisy_ensemble
from operator_matrix_verification import build_operator_matrix, ordered_basis
from simulator import Position, parse_position


DensityMatrix = list[list[complex]]


@dataclass(frozen=True)
class ExactDensityResult:
    absorbed_probability: float
    surviving_probability: float
    normalized_l1_coherence: float
    purity: float
    maximum_probability_error: float


def density_trace(density: DensityMatrix) -> float:
    return sum(density[index][index].real for index in range(len(density)))


def initial_density(walk: EOGQuantumWalk, start: Position) -> DensityMatrix:
    walk.require_valid(start, "start")
    basis = ordered_basis(walk)
    index = {state: position for position, state in enumerate(basis)}
    vector = [0j for _state in basis]
    for direction in range(DIRECTION_COUNT):
        vector[index[(start, direction)]] = 0.5 + 0j
    return [
        [left * right.conjugate() for right in vector]
        for left in vector
    ]


def evolve_density(density: DensityMatrix, operator: list[list[complex]]) -> DensityMatrix:
    """Apply U rho U-dagger while exploiting zeros in the walk operator."""
    dimension = len(operator)
    left_product = [[0j for _column in range(dimension)] for _row in range(dimension)]
    nonzero_rows = [
        [(column, value) for column, value in enumerate(row) if value != 0j]
        for row in operator
    ]
    for row in range(dimension):
        for source, coefficient in nonzero_rows[row]:
            for column in range(dimension):
                left_product[row][column] += coefficient * density[source][column]

    evolved = [[0j for _column in range(dimension)] for _row in range(dimension)]
    for row in range(dimension):
        for column in range(dimension):
            evolved[row][column] = sum(
                left_product[row][source] * coefficient.conjugate()
                for source, coefficient in nonzero_rows[column]
            )
    return evolved


def apply_exact_phase_channel(
    density: DensityMatrix,
    phase_flip_probability: float,
) -> DensityMatrix:
    if not 0.0 <= phase_flip_probability <= 1.0:
        raise ValueError("phase_flip_probability must be between 0 and 1")
    off_diagonal_factor = (1.0 - 2.0 * phase_flip_probability) ** 2
    return [
        [
            value if row == column else value * off_diagonal_factor
            for column, value in enumerate(values)
        ]
        for row, values in enumerate(density)
    ]


def project_terminals(
    density: DensityMatrix,
    terminal_indices: frozenset[int],
) -> tuple[DensityMatrix, float]:
    absorbed = sum(density[index][index].real for index in terminal_indices)
    projected = [
        [
            0j if row in terminal_indices or column in terminal_indices else value
            for column, value in enumerate(values)
        ]
        for row, values in enumerate(density)
    ]
    return projected, absorbed


def conditional_coherence_metrics(
    density: DensityMatrix,
    surviving_probability: float,
) -> tuple[float, float]:
    if surviving_probability <= 1e-15:
        return 0.0, 0.0
    dimension = len(density)
    normalized = [
        [value / surviving_probability for value in row]
        for row in density
    ]
    l1_coherence = sum(
        abs(value)
        for row_index, row in enumerate(normalized)
        for column_index, value in enumerate(row)
        if row_index != column_index
    )
    purity = sum(abs(value) ** 2 for row in normalized for value in row)
    return l1_coherence / (dimension - 1), purity


def run_exact_density_channel(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    phase_flip_probability: float,
    measurement_interval: int = 1,
) -> ExactDensityResult:
    if steps < 1 or measurement_interval < 1:
        raise ValueError("steps and measurement_interval must be positive")
    walk.require_valid(start, "start")
    if start in walk.terminals:
        return ExactDensityResult(1.0, 0.0, 0.0, 0.0, 0.0)

    basis = ordered_basis(walk)
    terminal_indices = frozenset(
        index for index, (position, _direction) in enumerate(basis)
        if position in walk.terminals
    )
    operator = build_operator_matrix(walk)
    density = initial_density(walk, start)
    cumulative_absorption = 0.0

    for step_number in range(1, steps + 1):
        density = evolve_density(density, operator)
        density = apply_exact_phase_channel(density, phase_flip_probability)
        should_measure = (
            step_number % measurement_interval == 0 or step_number == steps
        )
        if should_measure:
            density, absorbed = project_terminals(density, terminal_indices)
            cumulative_absorption += absorbed

    surviving = density_trace(density)
    probability_error = abs(cumulative_absorption + surviving - 1.0)
    coherence, purity = conditional_coherence_metrics(density, surviving)
    return ExactDensityResult(
        cumulative_absorption,
        surviving,
        coherence,
        purity,
        probability_error,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare exact and Monte Carlo toy phase-noise channels."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    parser.add_argument("--noise", type=float, default=0.1)
    parser.add_argument("--trajectories", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--measurement-interval", type=int, default=1)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, {args.terminal})
        exact = run_exact_density_channel(
            walk, args.start, args.steps, args.noise, args.measurement_interval
        )
        monte_carlo = run_noisy_ensemble(
            walk,
            args.start,
            args.steps,
            args.noise,
            args.trajectories,
            args.seed,
            args.measurement_interval,
        )
        coherence = run_coherence_ensemble(
            walk,
            args.start,
            args.steps,
            args.noise,
            args.trajectories,
            args.seed,
            args.measurement_interval,
        )
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Exact density channel versus Monte Carlo trajectories")
    print(f"noise={args.noise} trajectories={args.trajectories} steps={args.steps}")
    print(f"exact_absorption={exact.absorbed_probability:.6f}")
    print(f"monte_carlo_absorption={monte_carlo.mean_absorption:.6f}")
    print(f"absorption_difference={abs(exact.absorbed_probability - monte_carlo.mean_absorption):.6f}")
    print(f"exact_normalized_l1={exact.normalized_l1_coherence:.6f}")
    print(f"monte_carlo_normalized_l1={coherence.normalized_l1_coherence:.6f}")
    print(f"exact_purity={exact.purity:.6f}")
    print(f"monte_carlo_purity={coherence.purity:.6f}")
    print(f"exact_probability_error={exact.maximum_probability_error:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
