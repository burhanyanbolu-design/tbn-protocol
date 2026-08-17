#!/usr/bin/env python3
"""Verified deterministic demonstrations for the Area One prototype."""

from simulator import DEFAULT_EVENTS, DeterministicControlSimulator, Position


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    route = ("down-right", "right", "down-left", "down-right", "right")
    zigzag = DeterministicControlSimulator(5, (Position(3, 2),), DEFAULT_EVENTS)
    result = zigzag.run(Position(0, 0), route)
    labels = [0] + [
        transition.destination_label
        for transition in result.transitions
        if transition.destination_label is not None
    ]
    require(labels == [0, 6, 7, 11, 17], "unexpected zigzag labels")
    require(result.stop_reason == "TERMINAL_REACHED", "terminal was not reached")
    require(len(result.transitions) == 4, "route continued after terminal entry")
    print("PASS zigzag-terminal: 0 -> 6 -> 7 -> 11 -> 17; remaining move skipped")

    immediate = zigzag.run(Position(3, 2), ("right",))
    require(not immediate.transitions, "an event ran from an initial terminal")
    require(immediate.stop_reason == "TERMINAL_REACHED", "initial terminal ignored")
    print("PASS initial-terminal: zero transitions and zero dispatched events")

    overlap = DeterministicControlSimulator(5, (), DEFAULT_EVENTS)
    endpoint = Position(0, 5)
    next_row = Position(1, 0)
    require(overlap.label(endpoint) == overlap.label(next_row) == 5, "labels differ")
    endpoint_run = overlap.run(endpoint, ("right",))
    next_row_run = overlap.run(next_row, ("right",))
    require(endpoint_run.stop_reason == "BOUNDARY_REJECTED", "edge was not rejected")
    require(next_row_run.final_position == Position(1, 1), "next-row route was wrong")
    print("PASS overlap-identity: (0,5)[5] rejects right; (1,0)[5] reaches (1,1)[6]")

    replay = zigzag.run(Position(0, 0), route)
    require(replay == result, "identical replay produced different evidence")
    print("PASS deterministic-replay: complete transition evidence is identical")
    print("SUMMARY 4/4 deterministic demonstrations passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
