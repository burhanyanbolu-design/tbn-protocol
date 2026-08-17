#!/usr/bin/env python3
"""Standard Grover quantum walk expressed with full EOG coordinates."""

from __future__ import annotations

import argparse
from collections import defaultdict

from quantum_walk_baseline import StepMetrics, WalkResult, verify_probability_accounting
from simulator import DeterministicControlSimulator, Position, parse_position


UP, RIGHT, DOWN, LEFT = range(4)
DIRECTION_COUNT = 4
SHIFT = {
    UP: (-1, 0, DOWN),
    RIGHT: (0, 1, LEFT),
    DOWN: (1, 0, UP),
    LEFT: (0, -1, RIGHT),
}
QuantumState = dict[tuple[Position, int], complex]
ClassicalState = dict[Position, float]


def state_norm(state: QuantumState) -> float:
    return sum(abs(amplitude) ** 2 for amplitude in state.values())


def grover_step(state: QuantumState, rows: int, width: int) -> QuantumState:
    """Apply the four-state Grover coin and a periodic flip-flop shift."""
    positions = {position for position, _direction in state}
    evolved: defaultdict[tuple[Position, int], complex] = defaultdict(complex)

    for position in positions:
        amplitudes = [state.get((position, direction), 0j) for direction in range(4)]
        mean_twice = sum(amplitudes) / 2.0
        for direction, amplitude in enumerate(amplitudes):
            coined = mean_twice - amplitude
            row_change, column_change, reverse = SHIFT[direction]
            destination = Position(
                (position.row + row_change) % rows,
                (position.column + column_change) % width,
            )
            evolved[(destination, reverse)] += coined

    return dict(evolved)


class EOGQuantumWalk:
    """A finite periodic Grover walk; EOG labels are display metadata only."""

    def __init__(self, step: int, rows: int, terminals: set[Position]) -> None:
        if step < 1:
            raise ValueError("step must be at least 1")
        if rows < 1:
            raise ValueError("rows must be at least 1")
        self.step = step
        self.rows = rows
        self.width = step + 1
        self.terminals = frozenset(terminals)
        for terminal in self.terminals:
            self.require_valid(terminal, "terminal")

    def require_valid(self, position: Position, name: str) -> None:
        if not (0 <= position.row < self.rows and 0 <= position.column < self.width):
            raise ValueError(f"{name} position {position} is outside the finite grid")

    def label(self, position: Position) -> int:
        return self.step * position.row + position.column

    def coordinates_for_label(self, label: int) -> tuple[Position, ...]:
        coordinate_model = DeterministicControlSimulator(self.step, ())
        return tuple(
            position
            for position in coordinate_model.positions_for_label(label)
            if position.row < self.rows
        )

    def run(self, start: Position, steps: int) -> WalkResult:
        """Measure and absorb terminal amplitude after every unitary step."""
        return self.run_with_measurement_interval(start, steps, 1)

    def run_with_measurement_interval(
        self,
        start: Position,
        steps: int,
        measurement_interval: int,
        initial_coin: tuple[complex, ...] | None = None,
    ) -> WalkResult:
        """Measure periodically and always once after the final unitary step."""
        if steps < 1:
            raise ValueError("steps must be at least 1")
        if measurement_interval < 1:
            raise ValueError("measurement_interval must be at least 1")
        self.require_valid(start, "start")
        if start in self.terminals:
            return WalkResult((), 0.0, 1.0)

        coin = initial_coin or tuple(
            0.5 + 0j for _direction in range(DIRECTION_COUNT)
        )
        if len(coin) != DIRECTION_COUNT:
            raise ValueError("initial_coin must contain four amplitudes")
        coin_norm = sum(abs(amplitude) ** 2 for amplitude in coin)
        if abs(coin_norm - 1.0) > 1e-12:
            raise ValueError("initial_coin amplitudes must have norm 1")
        state: QuantumState = {
            (start, direction): amplitude
            for direction, amplitude in enumerate(coin)
        }
        cumulative = 0.0
        history: list[StepMetrics] = []

        for step_number in range(1, steps + 1):
            norm_before = state_norm(state)
            evolved = grover_step(state, self.rows, self.width)
            norm_after_unitary = state_norm(evolved)
            should_measure = (
                step_number % measurement_interval == 0 or step_number == steps
            )
            absorbed = 0.0
            if should_measure:
                absorbed = sum(
                    abs(amplitude) ** 2
                    for (position, _direction), amplitude in evolved.items()
                    if position in self.terminals
                )
                evolved = {
                    key: amplitude
                    for key, amplitude in evolved.items()
                    if key[0] not in self.terminals
                }
            state = evolved
            cumulative += absorbed
            history.append(
                StepMetrics(
                    step=step_number,
                    absorbed_probability=absorbed,
                    cumulative_absorption=cumulative,
                    surviving_probability=state_norm(state),
                    unitary_norm_error=abs(norm_after_unitary - norm_before),
                )
            )

        return WalkResult(tuple(history), state_norm(state), cumulative)

    def run_classical(self, start: Position, steps: int) -> WalkResult:
        if steps < 1:
            raise ValueError("steps must be at least 1")
        self.require_valid(start, "start")
        if start in self.terminals:
            return WalkResult((), 0.0, 1.0)

        state: ClassicalState = {start: 1.0}
        cumulative = 0.0
        history: list[StepMetrics] = []

        for step_number in range(1, steps + 1):
            evolved: defaultdict[Position, float] = defaultdict(float)
            for position, probability in state.items():
                for row_change, column_change, _reverse in SHIFT.values():
                    destination = Position(
                        (position.row + row_change) % self.rows,
                        (position.column + column_change) % self.width,
                    )
                    evolved[destination] += probability / DIRECTION_COUNT

            absorbed = sum(evolved.pop(terminal, 0.0) for terminal in self.terminals)
            cumulative += absorbed
            state = dict(evolved)
            surviving = sum(state.values())
            history.append(
                StepMetrics(step_number, absorbed, cumulative, surviving, 0.0)
            )

        return WalkResult(tuple(history), sum(state.values()), cumulative)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a periodic Grover walk over finite EOG coordinates."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(1, 0))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        walk = EOGQuantumWalk(args.step, args.rows, {args.terminal})
        quantum = walk.run(args.start, args.steps)
        classical = walk.run_classical(args.start, args.steps)
        verify_probability_accounting(quantum)
        verify_probability_accounting(classical)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    label = walk.label(args.terminal)
    coordinates = ", ".join(str(item) for item in walk.coordinates_for_label(label))
    print("Periodic EOG-coordinate Grover walk (classical numerical simulation)")
    print(f"grid={args.rows}x{walk.width} step={args.step} steps={args.steps}")
    print(f"start={args.start} terminal={args.terminal}[{label}]")
    print(f"coordinates_with_terminal_label={coordinates}")
    print(f"quantum_absorbed={quantum.cumulative_absorption:.6f}")
    print(f"classical_absorbed={classical.cumulative_absorption:.6f}")
    maximum_error = max(
        (metric.unitary_norm_error for metric in quantum.metrics), default=0.0
    )
    print(f"maximum_unitary_norm_error={maximum_error:.3e}")
    print("ordinary_boundary=periodic terminal_operation=absorbing_projection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
