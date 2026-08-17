#!/usr/bin/env python3
"""Initial-state and terminal-position sensitivity sweep for Area One."""

from __future__ import annotations

import argparse
import statistics
from dataclasses import dataclass

from eog_quantum_walk import EOGQuantumWalk
from evaluation_metrics import parse_intervals
from simulator import Position, parse_position


INITIAL_COINS: dict[str, tuple[complex, ...]] = {
    "uniform": (0.5 + 0j, 0.5 + 0j, 0.5 + 0j, 0.5 + 0j),
    "right-directed": (0j, 1.0 + 0j, 0j, 0j),
    "balanced-phase": (0.5 + 0j, 0.5j, -0.5 + 0j, -0.5j),
}


@dataclass(frozen=True)
class SensitivitySummary:
    initial_coin: str
    measurement_interval: int
    terminals_checked: int
    minimum_absorption: float
    maximum_absorption: float
    mean_absorption: float
    spread: float
    minimum_terminal: Position
    maximum_terminal: Position


def all_positions(step: int, rows: int) -> tuple[Position, ...]:
    return tuple(
        Position(row, column)
        for row in range(rows)
        for column in range(step + 1)
    )


def run_sensitivity_sweep(
    step: int,
    rows: int,
    start: Position,
    evolution_steps: int,
    intervals: tuple[int, ...],
) -> tuple[SensitivitySummary, ...]:
    if step < 1 or rows < 1 or evolution_steps < 1:
        raise ValueError("step, rows and evolution_steps must be positive")
    if not intervals or any(interval < 1 for interval in intervals):
        raise ValueError("intervals must contain positive values")
    positions = all_positions(step, rows)
    if start not in positions:
        raise ValueError("start is outside the finite grid")
    terminals = tuple(position for position in positions if position != start)
    summaries: list[SensitivitySummary] = []

    for coin_name, coin in INITIAL_COINS.items():
        for interval in intervals:
            results: list[tuple[Position, float]] = []
            for terminal in terminals:
                walk = EOGQuantumWalk(step, rows, {terminal})
                result = walk.run_with_measurement_interval(
                    start,
                    evolution_steps,
                    interval,
                    initial_coin=coin,
                )
                results.append((terminal, result.cumulative_absorption))

            minimum_terminal, minimum = min(results, key=lambda item: item[1])
            maximum_terminal, maximum = max(results, key=lambda item: item[1])
            values = [value for _terminal, value in results]
            summaries.append(
                SensitivitySummary(
                    initial_coin=coin_name,
                    measurement_interval=interval,
                    terminals_checked=len(terminals),
                    minimum_absorption=minimum,
                    maximum_absorption=maximum,
                    mean_absorption=statistics.fmean(values),
                    spread=maximum - minimum,
                    minimum_terminal=minimum_terminal,
                    maximum_terminal=maximum_terminal,
                )
            )
    return tuple(summaries)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sweep initial coin states, terminals and measurement schedules."
    )
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--intervals", type=parse_intervals, default=(1, 3, 12))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        summaries = run_sensitivity_sweep(
            args.step, args.rows, args.start, args.steps, args.intervals
        )
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Area One initial-state and terminal sensitivity sweep")
    print(f"grid={args.rows}x{args.step + 1} start={args.start} steps={args.steps}")
    print("coin | interval | terminals | min | mean | max | spread | min/max terminal")
    for item in summaries:
        print(
            f"{item.initial_coin:>14} | {item.measurement_interval:>8} | "
            f"{item.terminals_checked:>9} | {item.minimum_absorption:.4f} | "
            f"{item.mean_absorption:.4f} | {item.maximum_absorption:.4f} | "
            f"{item.spread:.4f} | {item.minimum_terminal}/{item.maximum_terminal}"
        )
    print("Large spreads show configuration sensitivity and must not be hidden by best-case selection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
