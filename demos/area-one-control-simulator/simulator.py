#!/usr/bin/env python3
"""Minimal deterministic simulator for EOG Area One control routes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable


MOVES: dict[str, tuple[int, int]] = {
    "up-left": (-1, -1),
    "up": (-1, 0),
    "up-right": (-1, 1),
    "left": (0, -1),
    "right": (0, 1),
    "down-left": (1, -1),
    "down": (1, 0),
    "down-right": (1, 1),
}

DEFAULT_EVENTS = {
    "down-right": "SIMULATED_SET_HIGH",
    "right": "SIMULATED_HOLD",
    "down-left": "SIMULATED_SET_LOW",
}


@dataclass(frozen=True, order=True)
class Position:
    row: int
    column: int


@dataclass(frozen=True)
class Transition:
    index: int
    move: str
    source: Position
    destination: Position | None
    source_label: int
    destination_label: int | None
    event: str
    accepted: bool
    reason: str


@dataclass(frozen=True)
class SimulationResult:
    transitions: tuple[Transition, ...]
    final_position: Position
    stop_reason: str


class DeterministicControlSimulator:
    """Execute one declared route with no random choices or hardware effects."""

    def __init__(
        self,
        step: int,
        terminal_positions: Iterable[Position],
        event_map: dict[str, str] | None = None,
    ) -> None:
        if step < 1:
            raise ValueError("step must be at least 1")
        self.step = step
        self.terminals = frozenset(terminal_positions)
        self.event_map = dict(event_map or {})
        for terminal in self.terminals:
            self._require_valid(terminal, "terminal")

    def label(self, position: Position) -> int:
        return self.step * position.row + position.column

    def positions_for_label(self, label: int) -> tuple[Position, ...]:
        """Return every valid coordinate represented by a displayed label."""
        if label < 0:
            raise ValueError("label must be non-negative")

        row, column = divmod(label, self.step)
        canonical = Position(row, column)
        if label > 0 and column == 0:
            previous_endpoint = Position(row - 1, self.step)
            return previous_endpoint, canonical
        return (canonical,)

    def is_valid(self, position: Position) -> bool:
        return position.row >= 0 and 0 <= position.column <= self.step

    def _require_valid(self, position: Position, name: str) -> None:
        if not self.is_valid(position):
            raise ValueError(
                f"{name} position ({position.row},{position.column}) is outside "
                f"row >= 0 and 0 <= column <= {self.step}"
            )

    def run(self, start: Position, route: Iterable[str]) -> SimulationResult:
        self._require_valid(start, "start")
        current = start
        trace: list[Transition] = []

        if current in self.terminals:
            return SimulationResult((), current, "TERMINAL_REACHED")

        for index, move in enumerate(route, start=1):
            if move not in MOVES:
                choices = ", ".join(sorted(MOVES))
                raise ValueError(f"unknown move {move!r}; choose from: {choices}")

            row_change, column_change = MOVES[move]
            candidate = Position(
                current.row + row_change,
                current.column + column_change,
            )
            event = self.event_map.get(move, "SIMULATED_NO_OP")

            if not self.is_valid(candidate):
                trace.append(
                    Transition(
                        index=index,
                        move=move,
                        source=current,
                        destination=None,
                        source_label=self.label(current),
                        destination_label=None,
                        event="NOT_DISPATCHED",
                        accepted=False,
                        reason="BOUNDARY_REJECTED",
                    )
                )
                return SimulationResult(tuple(trace), current, "BOUNDARY_REJECTED")

            transition = Transition(
                index=index,
                move=move,
                source=current,
                destination=candidate,
                source_label=self.label(current),
                destination_label=self.label(candidate),
                event=event,
                accepted=True,
                reason="ACCEPTED",
            )
            trace.append(transition)
            current = candidate

            if current in self.terminals:
                return SimulationResult(tuple(trace), current, "TERMINAL_REACHED")

        return SimulationResult(tuple(trace), current, "ROUTE_COMPLETE")


def parse_position(text: str) -> Position:
    try:
        row_text, column_text = text.split(",", maxsplit=1)
        return Position(int(row_text), int(column_text))
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("position must use ROW,COLUMN") from exc


def parse_route(text: str) -> tuple[str, ...]:
    route = tuple(part.strip().lower() for part in text.split(",") if part.strip())
    if not route:
        raise argparse.ArgumentTypeError("route must contain at least one move")
    unknown = [move for move in route if move not in MOVES]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown move(s): {', '.join(unknown)}")
    return route


def format_position(position: Position, label: int) -> str:
    return f"({position.row},{position.column})[{label}]"


def print_result(
    simulator: DeterministicControlSimulator,
    start: Position,
    result: SimulationResult,
    title: str = "EOG Area One deterministic control simulator",
) -> None:
    terminal_text = ", ".join(
        format_position(position, simulator.label(position))
        for position in sorted(simulator.terminals)
    ) or "none"
    print(title)
    print(f"step={simulator.step} boundary=reject")
    print(f"start={format_position(start, simulator.label(start))}")
    print(f"terminals={terminal_text}")

    for transition in result.transitions:
        source = format_position(transition.source, transition.source_label)
        if transition.destination is None:
            destination = "INVALID"
        else:
            destination = format_position(
                transition.destination, transition.destination_label  # type: ignore[arg-type]
            )
        status = "ACCEPT" if transition.accepted else "REJECT"
        print(
            f"{transition.index:02d} {status} {transition.move}: "
            f"{source} -> {destination} event={transition.event}"
        )

    final_label = simulator.label(result.final_position)
    print(
        f"stop={result.stop_reason} "
        f"final={format_position(result.final_position, final_label)}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic EOG Area One control route."
    )
    parser.add_argument("--step", type=int, default=5)
    parser.add_argument("--start", type=parse_position, default=Position(0, 0))
    parser.add_argument("--terminal", type=parse_position, default=Position(3, 2))
    parser.add_argument(
        "--route",
        type=parse_route,
        default=parse_route(
            "down-right,right,down-left,down-right,right,down-left"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        simulator = DeterministicControlSimulator(
            step=args.step,
            terminal_positions=(args.terminal,),
            event_map=DEFAULT_EVENTS,
        )
        result = simulator.run(args.start, args.route)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc

    print_result(simulator, args.start, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
