#!/usr/bin/env python3
"""Bounded development-only screen of balanced pair-layer placement."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import candidate2_variant_screen as screen
import pair_scatter_development_selection as selection

VARIANTS = (
    "candidate1-reference",
    "all-alt-before-coin",
    "all-alt-after-coin",
    "all-alt-after-shift",
    "all-alt-symmetric-half",
    "outward-after-coin",
)


def _balanced(np: Any, state: Any, pairs: Any, theta: Any, phi: Any) -> Any:
    return screen._variant_layer(
        np, state, pairs, theta, phi, "all-directions-alternating-phase"
    )


def _outward(np: Any, state: Any, pairs: Any, theta: Any, phi: Any) -> Any:
    return screen._variant_layer(np, state, pairs, theta, phi, "outward-edge")


def _step(
    np: Any, kernels: Any, state: Any, terminal: Any, pairs: Any,
    theta: Any, phi: Any, variant: str,
) -> Any:
    if variant == "candidate1-reference":
        return kernels.candidate_step(state, terminal, pairs, theta, phi)
    state = kernels.terminal_phase_oracle(state, terminal)
    if variant == "all-alt-before-coin":
        state = _balanced(np, state, pairs, theta, phi)
        state = kernels.grover_coin(state)
        return kernels.periodic_flip_flop_shift(state)
    if variant == "all-alt-after-coin":
        state = kernels.grover_coin(state)
        state = _balanced(np, state, pairs, theta, phi)
        return kernels.periodic_flip_flop_shift(state)
    if variant == "all-alt-after-shift":
        state = kernels.grover_coin(state)
        state = kernels.periodic_flip_flop_shift(state)
        return _balanced(np, state, pairs, theta, phi)
    if variant == "all-alt-symmetric-half":
        half = np.float64(theta / np.float64(2.0))
        state = _balanced(np, state, pairs, half, phi)
        state = kernels.grover_coin(state)
        state = _balanced(np, state, pairs, half, phi)
        return kernels.periodic_flip_flop_shift(state)
    if variant == "outward-after-coin":
        state = kernels.grover_coin(state)
        state = _outward(np, state, pairs, theta, phi)
        return kernels.periodic_flip_flop_shift(state)
    raise selection.DevelopmentSelectionError("unknown placement variant")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    screen.VARIANTS = VARIANTS
    screen.SCHEMA_VERSION = "area-one-candidate2-placement-screen/1.0"
    screen.RESULT_FILENAME = "candidate2-placement-screen.json"
    screen._step = _step
    result = screen.run(args.selection, args.output, args.workers)
    for winner in result["winners"]:
        print("PLACEMENT_WINNER " + json.dumps(winner, sort_keys=True), flush=True)
    print(f"CANDIDATE2_PLACEMENT_SCREEN_PASS groups={result['group_count']}")
    print("no_lock=true heldout_executed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())