#!/usr/bin/env python3
"""Independent matrix verification of the EOG Grover walk operator."""

from __future__ import annotations

import argparse

from eog_quantum_walk import DIRECTION_COUNT, EOGQuantumWalk, QuantumState, grover_step
from simulator import Position, parse_position


BasisState = tuple[Position, int]
Matrix = list[list[complex]]
Vector = list[complex]


def ordered_basis(walk: EOGQuantumWalk) -> tuple[BasisState, ...]:
    return tuple(
        (Position(row, column), direction)
        for row in range(walk.rows)
        for column in range(walk.width)
        for direction in range(DIRECTION_COUNT)
    )


def build_operator_matrix(walk: EOGQuantumWalk) -> Matrix:
    """Construct U column-by-column from independently evolved basis states."""
    basis = ordered_basis(walk)
    index = {state: position for position, state in enumerate(basis)}
    dimension = len(basis)
    matrix = [[0j for _column in range(dimension)] for _row in range(dimension)]

    for column, basis_state in enumerate(basis):
        evolved = grover_step({basis_state: 1.0 + 0j}, walk.rows, walk.width)
        for destination, amplitude in evolved.items():
            matrix[index[destination]][column] = amplitude
    return matrix


def maximum_unitarity_error(matrix: Matrix) -> float:
    """Return max absolute entry error in U-dagger U against identity."""
    dimension = len(matrix)
    maximum = 0.0
    for left_column in range(dimension):
        for right_column in range(dimension):
            inner_product = sum(
                matrix[row][left_column].conjugate() * matrix[row][right_column]
                for row in range(dimension)
            )
            expected = 1.0 if left_column == right_column else 0.0
            maximum = max(maximum, abs(inner_product - expected))
    return maximum


def apply_matrix(matrix: Matrix, vector: Vector) -> Vector:
    if len(matrix) != len(vector):
        raise ValueError("matrix and vector dimensions differ")
    return [
        sum(coefficient * amplitude for coefficient, amplitude in zip(row, vector))
        for row in matrix
    ]


def state_to_vector(state: QuantumState, basis: tuple[BasisState, ...]) -> Vector:
    return [state.get(basis_state, 0j) for basis_state in basis]


def vector_to_state(vector: Vector, basis: tuple[BasisState, ...]) -> QuantumState:
    return {
        basis_state: amplitude
        for basis_state, amplitude in zip(basis, vector)
        if abs(amplitude) > 0.0
    }


def maximum_evolution_difference(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    matrix: Matrix,
) -> float:
    if steps < 1:
        raise ValueError("steps must be at least 1")
    walk.require_valid(start, "start")
    basis = ordered_basis(walk)
    dictionary_state: QuantumState = {
        (start, direction): 0.5 + 0j for direction in range(DIRECTION_COUNT)
    }
    matrix_vector = state_to_vector(dictionary_state, basis)
    maximum = 0.0

    for _step in range(steps):
        dictionary_state = grover_step(
            dictionary_state, walk.rows, walk.width
        )
        matrix_vector = apply_matrix(matrix, matrix_vector)
        dictionary_vector = state_to_vector(dictionary_state, basis)
        maximum = max(
            maximum,
            max(
                abs(from_dictionary - from_matrix)
                for from_dictionary, from_matrix in zip(
                    dictionary_vector, matrix_vector
                )
            ),
        )
    return maximum


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the full EOG Grover operator matrix."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--tolerance", type=float, default=1e-12)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, set())
        matrix = build_operator_matrix(walk)
        unitarity_error = maximum_unitarity_error(matrix)
        evolution_error = maximum_evolution_difference(
            walk, args.start, args.steps, matrix
        )
        if unitarity_error > args.tolerance:
            raise RuntimeError("operator failed U-dagger U identity check")
        if evolution_error > args.tolerance:
            raise RuntimeError("matrix and dictionary evolution disagree")
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    dimension = len(matrix)
    print("Independent EOG Grover operator-matrix verification")
    print(f"grid={args.rows}x{walk.width} hilbert_dimension={dimension}")
    print(f"matrix_shape={dimension}x{dimension} compared_steps={args.steps}")
    print(f"maximum_U_dagger_U_error={unitarity_error:.3e}")
    print(f"maximum_evolution_difference={evolution_error:.3e}")
    print("PASS operator is unitary and both implementations agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
