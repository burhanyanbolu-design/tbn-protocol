#!/usr/bin/env python3
"""Topology-matched ordinary-index baseline for the EOG Grover walk."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass

from eog_quantum_walk import (
    DIRECTION_COUNT,
    SHIFT,
    EOGQuantumWalk,
    QuantumState,
    grover_step,
)
from simulator import Position, parse_position


IndexedState = dict[tuple[int, int], complex]


@dataclass(frozen=True)
class TopologyComparison:
    coordinate_states: int
    unique_display_labels: int
    indexed_nodes: int
    maximum_amplitude_difference: float
    eog_absorption: float
    indexed_absorption: float


def coordinate_to_node(position: Position, width: int) -> int:
    if position.row < 0 or not 0 <= position.column < width:
        raise ValueError("coordinate is outside the indexed grid")
    return position.row * width + position.column


def node_to_coordinate(node: int, rows: int, width: int) -> Position:
    if not 0 <= node < rows * width:
        raise ValueError("node is outside the indexed grid")
    row, column = divmod(node, width)
    return Position(row, column)


def indexed_grover_step(
    state: IndexedState,
    rows: int,
    width: int,
) -> IndexedState:
    nodes = {node for node, _direction in state}
    evolved: defaultdict[tuple[int, int], complex] = defaultdict(complex)
    for node in nodes:
        position = node_to_coordinate(node, rows, width)
        amplitudes = [
            state.get((node, direction), 0j)
            for direction in range(DIRECTION_COUNT)
        ]
        mean_twice = sum(amplitudes) / 2.0
        for direction, amplitude in enumerate(amplitudes):
            row_change, column_change, reverse = SHIFT[direction]
            destination = Position(
                (position.row + row_change) % rows,
                (position.column + column_change) % width,
            )
            destination_node = coordinate_to_node(destination, width)
            evolved[(destination_node, reverse)] += mean_twice - amplitude
    return dict(evolved)


def compare_topologies(
    walk: EOGQuantumWalk,
    start: Position,
    steps: int,
    measurement_interval: int = 1,
) -> TopologyComparison:
    if steps < 1 or measurement_interval < 1:
        raise ValueError("steps and measurement_interval must be positive")
    walk.require_valid(start, "start")
    indexed_start = coordinate_to_node(start, walk.width)
    terminal_nodes = {
        coordinate_to_node(position, walk.width)
        for position in walk.terminals
    }
    coordinate_state: QuantumState = {
        (start, direction): 0.5 + 0j
        for direction in range(DIRECTION_COUNT)
    }
    indexed_state: IndexedState = {
        (indexed_start, direction): 0.5 + 0j
        for direction in range(DIRECTION_COUNT)
    }
    indexed_absorption = 0.0
    maximum_difference = 0.0

    for step_number in range(1, steps + 1):
        coordinate_state = grover_step(
            coordinate_state, walk.rows, walk.width
        )
        indexed_state = indexed_grover_step(
            indexed_state, walk.rows, walk.width
        )
        should_measure = (
            step_number % measurement_interval == 0 or step_number == steps
        )
        if should_measure:
            indexed_absorption += sum(
                abs(amplitude) ** 2
                for (node, _direction), amplitude in indexed_state.items()
                if node in terminal_nodes
            )
            indexed_state = {
                key: amplitude
                for key, amplitude in indexed_state.items()
                if key[0] not in terminal_nodes
            }
            coordinate_state = {
                key: amplitude
                for key, amplitude in coordinate_state.items()
                if key[0] not in walk.terminals
            }

        for position in (
            Position(row, column)
            for row in range(walk.rows)
            for column in range(walk.width)
        ):
            node = coordinate_to_node(position, walk.width)
            for direction in range(DIRECTION_COUNT):
                maximum_difference = max(
                    maximum_difference,
                    abs(
                        coordinate_state.get((position, direction), 0j)
                        - indexed_state.get((node, direction), 0j)
                    ),
                )

    eog_result = walk.run_with_measurement_interval(
        start, steps, measurement_interval
    )
    positions = tuple(
        Position(row, column)
        for row in range(walk.rows)
        for column in range(walk.width)
    )
    return TopologyComparison(
        coordinate_states=len(positions),
        unique_display_labels=len({walk.label(position) for position in positions}),
        indexed_nodes=walk.rows * walk.width,
        maximum_amplitude_difference=maximum_difference,
        eog_absorption=eog_result.cumulative_absorption,
        indexed_absorption=indexed_absorption,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare EOG coordinates with ordinary unique node indices."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    parser.add_argument("--measurement-interval", type=int, default=1)
    parser.add_argument("--tolerance", type=float, default=1e-12)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, {args.terminal})
        comparison = compare_topologies(
            walk, args.start, args.steps, args.measurement_interval
        )
        if comparison.maximum_amplitude_difference > args.tolerance:
            raise RuntimeError("coordinate and indexed evolution disagree")
        if abs(comparison.eog_absorption - comparison.indexed_absorption) > args.tolerance:
            raise RuntimeError("coordinate and indexed absorption disagree")
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("EOG versus ordinary topology-matched index baseline")
    print(f"coordinate_states={comparison.coordinate_states}")
    print(f"unique_display_labels={comparison.unique_display_labels}")
    print(f"ordinary_indexed_nodes={comparison.indexed_nodes}")
    print(f"maximum_amplitude_difference={comparison.maximum_amplitude_difference:.3e}")
    print(f"eog_absorption={comparison.eog_absorption:.6f}")
    print(f"indexed_absorption={comparison.indexed_absorption:.6f}")
    print("PASS full coordinates are isomorphic to ordinary unique node indices")
    print("Displayed EOG labels are metadata and do not alter the dynamics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
