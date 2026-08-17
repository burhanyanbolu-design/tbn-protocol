#!/usr/bin/env python3
"""Compare periodic, reflective and absorbing quantum boundary policies."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass

from eog_quantum_walk import DIRECTION_COUNT, SHIFT, EOGQuantumWalk, QuantumState, state_norm
from operator_matrix_verification import Matrix, maximum_unitarity_error, ordered_basis
from simulator import Position, parse_position


BOUNDARY_POLICIES = ("periodic", "reflective", "absorbing")


@dataclass(frozen=True)
class BoundaryEvaluation:
    policy: str
    maximum_unitarity_error: float
    final_norm: float
    boundary_loss: float
    classification: str


def grover_boundary_step(
    state: QuantumState,
    rows: int,
    width: int,
    policy: str,
) -> QuantumState:
    if policy not in BOUNDARY_POLICIES:
        raise ValueError(f"unknown boundary policy: {policy}")
    positions = {position for position, _direction in state}
    evolved: defaultdict[tuple[Position, int], complex] = defaultdict(complex)

    for position in positions:
        amplitudes = [
            state.get((position, direction), 0j)
            for direction in range(DIRECTION_COUNT)
        ]
        mean_twice = sum(amplitudes) / 2.0
        for direction, amplitude in enumerate(amplitudes):
            coined = mean_twice - amplitude
            row_change, column_change, reverse = SHIFT[direction]
            candidate_row = position.row + row_change
            candidate_column = position.column + column_change
            valid = 0 <= candidate_row < rows and 0 <= candidate_column < width

            if policy == "periodic":
                destination = Position(candidate_row % rows, candidate_column % width)
                destination_direction = reverse
            elif valid:
                destination = Position(candidate_row, candidate_column)
                destination_direction = reverse
            elif policy == "reflective":
                destination = position
                destination_direction = direction
            else:
                continue
            evolved[(destination, destination_direction)] += coined

    return dict(evolved)


def build_boundary_operator(walk: EOGQuantumWalk, policy: str) -> Matrix:
    basis = ordered_basis(walk)
    index = {state: position for position, state in enumerate(basis)}
    dimension = len(basis)
    matrix = [[0j for _column in basis] for _row in basis]
    for column, basis_state in enumerate(basis):
        evolved = grover_boundary_step(
            {basis_state: 1.0 + 0j}, walk.rows, walk.width, policy
        )
        for destination, amplitude in evolved.items():
            matrix[index[destination]][column] = amplitude
    return matrix


def evaluate_boundary(
    walk: EOGQuantumWalk,
    policy: str,
    start: Position,
    steps: int,
    tolerance: float = 1e-12,
) -> BoundaryEvaluation:
    if steps < 1:
        raise ValueError("steps must be at least 1")
    walk.require_valid(start, "start")
    operator = build_boundary_operator(walk, policy)
    unitarity_error = maximum_unitarity_error(operator)
    state: QuantumState = {
        (start, direction): 0.5 + 0j
        for direction in range(DIRECTION_COUNT)
    }
    for _step in range(steps):
        state = grover_boundary_step(state, walk.rows, walk.width, policy)
    final_norm = state_norm(state)
    classification = "unitary" if unitarity_error <= tolerance else "non-unitary"
    return BoundaryEvaluation(
        policy=policy,
        maximum_unitarity_error=unitarity_error,
        final_norm=final_norm,
        boundary_loss=max(0.0, 1.0 - final_norm),
        classification=classification,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare finite-grid quantum boundary policies."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--tolerance", type=float, default=1e-12)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, set())
        evaluations = tuple(
            evaluate_boundary(
                walk, policy, args.start, args.steps, args.tolerance
            )
            for policy in BOUNDARY_POLICIES
        )
        by_policy = {item.policy: item for item in evaluations}
        if by_policy["periodic"].classification != "unitary":
            raise RuntimeError("periodic boundary unexpectedly failed unitarity")
        if by_policy["reflective"].classification != "unitary":
            raise RuntimeError("reflective boundary unexpectedly failed unitarity")
        if by_policy["absorbing"].classification != "non-unitary":
            raise RuntimeError("absorbing boundary unexpectedly appeared unitary")
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Area One ordinary-boundary policy comparison")
    print(f"grid={args.rows}x{walk.width} start={args.start} steps={args.steps}")
    print("policy | classification | U-dagger-U error | final_norm | boundary_loss")
    for item in evaluations:
        print(
            f"{item.policy:>10} | {item.classification:>14} | "
            f"{item.maximum_unitarity_error:>16.3e} | "
            f"{item.final_norm:>10.6f} | {item.boundary_loss:>13.6f}"
        )
    print("Absorbing loss is an open-system operation, not ordinary unitary evolution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
