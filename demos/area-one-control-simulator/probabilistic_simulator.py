#!/usr/bin/env python3
"""Seeded classical probabilistic movement for the EOG Area One prototype."""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import replace

from simulator import (
    DEFAULT_EVENTS,
    MOVES,
    DeterministicControlSimulator,
    Position,
    SimulationResult,
    Transition,
    parse_position,
    print_result,
)


class ProbabilisticControlSimulator:
    """Choose classical moves by weight and execute them through the core."""

    def __init__(
        self,
        core: DeterministicControlSimulator,
        move_weights: dict[str, float],
        seed: int,
    ) -> None:
        if not move_weights:
            raise ValueError("at least one move weight is required")
        unknown = [move for move in move_weights if move not in MOVES]
        if unknown:
            raise ValueError(f"unknown move(s): {', '.join(unknown)}")
        if any(weight < 0 or not math.isfinite(weight) for weight in move_weights.values()):
            raise ValueError("move weights must be finite and non-negative")
        if not any(weight > 0 for weight in move_weights.values()):
            raise ValueError("at least one move weight must be positive")

        self.core = core
        self.moves = tuple(move_weights)
        self.weights = tuple(move_weights.values())
        self.seed = seed

    def run(self, start: Position, max_steps: int) -> SimulationResult:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.core._require_valid(start, "start")
        if start in self.core.terminals:
            return SimulationResult((), start, "TERMINAL_REACHED")

        random_source = random.Random(self.seed)
        current = start
        trace: list[Transition] = []

        for index in range(1, max_steps + 1):
            move = random_source.choices(self.moves, weights=self.weights, k=1)[0]
            one_step = self.core.run(current, (move,))
            transition = replace(one_step.transitions[0], index=index)
            trace.append(transition)
            current = one_step.final_position

            if one_step.stop_reason != "ROUTE_COMPLETE":
                return SimulationResult(tuple(trace), current, one_step.stop_reason)

        return SimulationResult(tuple(trace), current, "MAX_STEPS_REACHED")


def parse_weights(text: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    try:
        for item in text.split(","):
            move, value = item.split("=", maxsplit=1)
            move = move.strip().lower()
            if not move or move in weights:
                raise ValueError
            weights[move] = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "weights must use MOVE=WEIGHT pairs separated by commas"
        ) from exc
    return weights


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a seeded classical probabilistic EOG control route."
    )
    parser.add_argument("--step", type=int, default=5)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(3, 4))
    parser.add_argument(
        "--weights",
        type=parse_weights,
        default=parse_weights("down-right=1,right=1,down-left=1"),
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-steps", type=int, default=12)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        core = DeterministicControlSimulator(
            step=args.step,
            terminal_positions=(args.terminal,),
            event_map=DEFAULT_EVENTS,
        )
        simulator = ProbabilisticControlSimulator(core, args.weights, args.seed)
        result = simulator.run(args.start, args.max_steps)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc

    print(f"seed={args.seed} weights={args.weights}")
    print_result(
        core,
        args.start,
        result,
        title="EOG Area One classical probabilistic simulator",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
