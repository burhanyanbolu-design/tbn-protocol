#!/usr/bin/env python3
"""Bounded local scaling benchmark for the Area One simulator."""

from __future__ import annotations

import argparse
import statistics
import time
import tracemalloc
from dataclasses import dataclass

from eog_quantum_walk import DIRECTION_COUNT, EOGQuantumWalk
from simulator import Position


@dataclass(frozen=True)
class ScalingResult:
    step: int
    rows: int
    width: int
    hilbert_dimension: int
    density_matrix_entries: int
    minimum_numeric_density_bytes: int
    evolution_steps: int
    repeats: int
    median_runtime_seconds: float
    peak_python_bytes: int


def parse_configurations(text: str) -> tuple[tuple[int, int], ...]:
    configurations: list[tuple[int, int]] = []
    try:
        for item in text.split(","):
            step_text, rows_text = item.strip().split(":", maxsplit=1)
            configuration = (int(step_text), int(rows_text))
            if configuration[0] < 1 or configuration[1] < 1:
                raise ValueError
            configurations.append(configuration)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "configurations must use positive STEP:ROWS pairs"
        ) from exc
    if not configurations:
        raise argparse.ArgumentTypeError("at least one configuration is required")
    return tuple(configurations)


def benchmark_configuration(
    step: int,
    rows: int,
    evolution_steps: int,
    repeats: int,
) -> ScalingResult:
    if step < 1 or rows < 1 or evolution_steps < 1 or repeats < 1:
        raise ValueError("all benchmark parameters must be positive")
    width = step + 1
    walk = EOGQuantumWalk(step, rows, set())
    start = Position(0, 0)
    timings: list[float] = []

    tracemalloc.start()
    for _repeat in range(repeats):
        started = time.perf_counter()
        walk.run(start, evolution_steps)
        timings.append(time.perf_counter() - started)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    dimension = rows * width * DIRECTION_COUNT
    entries = dimension * dimension
    return ScalingResult(
        step=step,
        rows=rows,
        width=width,
        hilbert_dimension=dimension,
        density_matrix_entries=entries,
        minimum_numeric_density_bytes=entries * 16,
        evolution_steps=evolution_steps,
        repeats=repeats,
        median_runtime_seconds=statistics.median(timings),
        peak_python_bytes=peak,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark local Area One simulation scaling."
    )
    parser.add_argument(
        "--configurations",
        type=parse_configurations,
        default=((2, 3), (3, 5), (5, 8)),
        help="comma-separated STEP:ROWS pairs",
    )
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=5)
    return parser


def format_bytes(value: int) -> str:
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.2f} MiB"
    if value >= 1024:
        return f"{value / 1024:.2f} KiB"
    return f"{value} B"


def main() -> int:
    args = build_parser().parse_args()
    try:
        results = tuple(
            benchmark_configuration(
                step, rows, args.steps, args.repeats
            )
            for step, rows in args.configurations
        )
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc

    print("Area One local software scaling benchmark")
    print(f"evolution_steps={args.steps} repeats={args.repeats}")
    print("grid | dimension | median_runtime | peak_python | dense_entries | numeric_min")
    for item in results:
        print(
            f"{item.rows}x{item.width} | {item.hilbert_dimension:>9} | "
            f"{item.median_runtime_seconds:>14.6f}s | "
            f"{format_bytes(item.peak_python_bytes):>11} | "
            f"{item.density_matrix_entries:>13} | "
            f"{format_bytes(item.minimum_numeric_density_bytes):>11}"
        )
    print("Runtime and peak allocation describe this Python process on this machine.")
    print("Numeric minimum excludes Python object and container overhead.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
