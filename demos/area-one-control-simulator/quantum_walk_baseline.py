#!/usr/bin/env python3
"""Standard coined quantum-walk baseline simulated on a classical computer."""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from dataclasses import dataclass


LEFT = 0
RIGHT = 1
AmplitudeState = dict[tuple[int, int], complex]
ProbabilityState = dict[int, float]


@dataclass(frozen=True)
class StepMetrics:
    step: int
    absorbed_probability: float
    cumulative_absorption: float
    surviving_probability: float
    unitary_norm_error: float


@dataclass(frozen=True)
class WalkResult:
    metrics: tuple[StepMetrics, ...]
    final_surviving_probability: float
    cumulative_absorption: float


def amplitude_norm(state: AmplitudeState) -> float:
    return sum(abs(amplitude) ** 2 for amplitude in state.values())


def hadamard_shift(state: AmplitudeState) -> AmplitudeState:
    """Apply a Hadamard coin and conditional shift on the integer line."""
    positions = {position for position, _coin in state}
    shifted: defaultdict[tuple[int, int], complex] = defaultdict(complex)
    scale = 1.0 / math.sqrt(2.0)

    for position in positions:
        left = state.get((position, LEFT), 0j)
        right = state.get((position, RIGHT), 0j)
        outgoing_left = (left + right) * scale
        outgoing_right = (left - right) * scale
        shifted[(position - 1, LEFT)] += outgoing_left
        shifted[(position + 1, RIGHT)] += outgoing_right

    return dict(shifted)


def quantum_walk(steps: int, terminal: int, start: int = 0) -> WalkResult:
    """Run unitary steps followed by terminal projection into an absorbing sink."""
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if start == terminal:
        return WalkResult((), 0.0, 1.0)

    scale = 1.0 / math.sqrt(2.0)
    state: AmplitudeState = {
        (start, LEFT): complex(scale, 0.0),
        (start, RIGHT): complex(0.0, scale),
    }
    cumulative = 0.0
    history: list[StepMetrics] = []

    for step in range(1, steps + 1):
        norm_before = amplitude_norm(state)
        evolved = hadamard_shift(state)
        norm_after_unitary = amplitude_norm(evolved)
        norm_error = abs(norm_after_unitary - norm_before)

        absorbed = sum(
            abs(amplitude) ** 2
            for (position, _coin), amplitude in evolved.items()
            if position == terminal
        )
        state = {
            key: amplitude
            for key, amplitude in evolved.items()
            if key[0] != terminal
        }
        cumulative += absorbed
        surviving = amplitude_norm(state)
        history.append(
            StepMetrics(step, absorbed, cumulative, surviving, norm_error)
        )

    return WalkResult(tuple(history), amplitude_norm(state), cumulative)


def classical_walk(steps: int, terminal: int, start: int = 0) -> WalkResult:
    """Run a symmetric classical random-walk distribution with the same sink."""
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if start == terminal:
        return WalkResult((), 0.0, 1.0)

    state: ProbabilityState = {start: 1.0}
    cumulative = 0.0
    history: list[StepMetrics] = []

    for step in range(1, steps + 1):
        evolved: defaultdict[int, float] = defaultdict(float)
        for position, probability in state.items():
            evolved[position - 1] += probability * 0.5
            evolved[position + 1] += probability * 0.5

        absorbed = evolved.pop(terminal, 0.0)
        cumulative += absorbed
        state = dict(evolved)
        surviving = sum(state.values())
        history.append(StepMetrics(step, absorbed, cumulative, surviving, 0.0))

    return WalkResult(tuple(history), sum(state.values()), cumulative)


def verify_probability_accounting(result: WalkResult, tolerance: float = 1e-12) -> None:
    total = result.final_surviving_probability + result.cumulative_absorption
    if not math.isclose(total, 1.0, abs_tol=tolerance):
        raise RuntimeError(f"probability accounting failed: total={total:.16f}")
    if any(metric.unitary_norm_error > tolerance for metric in result.metrics):
        raise RuntimeError("ordinary quantum evolution did not preserve norm")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare standard quantum and classical absorbing walks."
    )
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--terminal", type=int, default=3)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        quantum = quantum_walk(args.steps, args.terminal, args.start)
        classical = classical_walk(args.steps, args.terminal, args.start)
        verify_probability_accounting(quantum)
        verify_probability_accounting(classical)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Standard absorbing-walk baseline (classical numerical simulation)")
    print(f"start={args.start} terminal={args.terminal} steps={args.steps}")
    print("step | quantum absorbed/cumulative | classical absorbed/cumulative")
    for quantum_step, classical_step in zip(quantum.metrics, classical.metrics):
        print(
            f"{quantum_step.step:>4} | "
            f"{quantum_step.absorbed_probability:.6f}/"
            f"{quantum_step.cumulative_absorption:.6f} | "
            f"{classical_step.absorbed_probability:.6f}/"
            f"{classical_step.cumulative_absorption:.6f}"
        )
    maximum_error = max(
        (metric.unitary_norm_error for metric in quantum.metrics), default=0.0
    )
    print(f"quantum_surviving={quantum.final_surviving_probability:.6f}")
    print(f"quantum_absorbed={quantum.cumulative_absorption:.6f}")
    print(f"classical_absorbed={classical.cumulative_absorption:.6f}")
    print(f"maximum_unitary_norm_error={maximum_error:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
