"""
EQCCM — Amplitude-Magnitude Pruning Experiment (EXPERIMENTAL, separate from
the exact control)
============================================================================
Standalone addition alongside banded_scaling.py. Does NOT modify it, does
NOT change its results, and is imported from it rather than duplicating its
code. banded_scaling.py remains the exact, verified control in every
comparison run here.

WHAT THIS TESTS
    Burhan's "vector zoom / four-triangle area" idea, reduced to a concrete,
    testable classical claim: in the active-frontier elimination table, most
    of the 2^w frontier configurations contribute very little to the final
    amplitude. If we drop ("prune") configurations whose magnitude is small
    relative to the largest one currently active, before they're carried
    into the next magnify step, do we still recover (approximately) the
    same answer, using less memory and less time?

This is the standard "amplitude truncation" idea from tensor-network /
MPS-style contraction, applied here to this project's specific banded
circuit family. Not a new algorithm — the novelty question, if any, is
whether THIS circuit family tolerates it well, not whether the technique
itself is new.

WHAT THIS DOES NOT CLAIM
    * No claim about physical electron capacity, physical position, or any
      real-world spatial area. The "distance"/"area" language that inspired
      this is a state-space intuition only. Coordinates here are abstract
      frontier-configuration magnitudes, nothing more, unless and until a
      real experimental mapping to physical position is established
      separately — which this script does not attempt.
    * No claim this beats the exact algorithm on correctness. Pruning is a
      controlled approximation. Every result below is checked against the
      exact `contract_frontier` in banded_scaling.py, which remains the
      ground truth.
    * No claim of novelty for the pruning technique itself (amplitude/SVD
      truncation is textbook tensor-network practice).

TWO-STAGE VERIFICATION (mirrors this project's own correction discipline —
check the mechanism before trusting the result)
    Stage 1 — sparse encoding sanity check: run the pruned contraction with
        threshold=0.0 (i.e., prune nothing). This MUST reproduce the exact
        dense result to numerical precision. If it doesn't, the sparse
        bookkeeping itself is wrong — fix that before ever turning pruning
        on. This isolates "is the new code mechanically correct" from "does
        pruning preserve accuracy."
    Stage 2 — threshold sweep: only once Stage 1 passes, sweep real
        thresholds > 0 and measure reconstruction error, configurations
        retained vs 2^w, wall-clock time, and estimated memory, all against
        the same exact reference.

WHY A DICT, NOT A DENSE ARRAY, FOR THE FRONTIER STATE
    The exact version's dense table has a fixed size once shape is decided
    — you cannot "prune" entries out of a numpy array and get a real memory
    saving; the array stays the same shape. To make pruning give an HONEST,
    measurable resource saving (not just zeroed floats sitting in the same
    memory), the active frontier state here is a dict: {frontier_config ->
    value_array_over_open_y_axes}. Pruning removes dict keys outright, which
    is a real, measurable reduction in both the entries carried forward and
    the work done on the next magnify step.

Run:
    python demo/eqccm/banded_scaling_pruned.py                 # default
    python demo/eqccm/banded_scaling_pruned.py --verify-only   # stage 1 only
    python demo/eqccm/banded_scaling_pruned.py --n 20 --w 14

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
import os
import statistics
import sys
import time
from typing import Dict, List, Sequence, Tuple

import numpy as np

# Import the existing, unmodified exact implementation rather than
# duplicating it. banded_scaling.py stays the untouched control.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banded_scaling import (  # noqa: E402
    banded_graph,
    contract_frontier,
    deterministic_angles,
    ry_matrix,
    site_factors,
    statevector_reference,
    verify_treewidth,
)

BYTES_PER_ELEM = 8  # float64


# ══════════════════════════════════════════════════════════════════
# 1. SPARSE, PRUNABLE ACTIVE-FRONTIER CONTRACTION
#    magnify -> use -> collapse -> PRUNE (new step)
# ══════════════════════════════════════════════════════════════════

def contract_frontier_pruned(
    n: int, w: int, alphas, betas,
    y_fixed: Dict[int, int],
    open_qubits: Sequence[int],
    threshold: float = 0.0,
) -> Tuple[np.ndarray, Dict]:
    """
    Approximate amplitude(s) by variable elimination with an active
    frontier held as a dict of {frontier_config: value_array}, pruning
    low-magnitude configurations after each collapse step.

    threshold=0.0 means "prune nothing" — this must reproduce the exact
    result (see verify_sparse_exact). threshold > 0.0 is a real
    approximation: configurations whose value's max magnitude is below
    threshold * (current max magnitude across the whole state) are dropped
    before the next magnify step.

    frontier_order: list of qubit indices currently active as x-variables,
    in a fixed order — a dict key is a tuple of 0/1 values aligned to this
    order.
    open_y_order: list of qubit indices whose y-axis is open (persists to
    the end); each value_array has ndim == len(open_y_order) at the point
    it is looked at (grows as more y's open along the sweep).
    """
    edges = set(banded_graph(n, w))
    adj = {i: set() for i in range(n)}
    for i, j in edges:
        adj[i].add(j)
        adj[j].add(i)

    frontier_order: List[int] = []
    open_y_order: List[int] = []
    state: Dict[Tuple[int, ...], np.ndarray] = {(): np.ones((), dtype=np.float64)}

    peak_configs = 1
    total_pruned = 0

    for i in range(n):
        factor, y_open = site_factors(alphas, betas, y_fixed, i)

        # ── magnify: every existing key splits into x_i=0 and x_i=1 ──
        new_state: Dict[Tuple[int, ...], np.ndarray] = {}
        if y_open:
            open_y_order.append(i)
            for key, val in state.items():
                for xi in (0, 1):
                    # factor[y_i, x_i] -> slice over y_i for this x_i,
                    # outer-product onto the existing value array
                    contrib = factor[:, xi]
                    new_val = np.multiply.outer(val, contrib)
                    new_state[key + (xi,)] = new_val
        else:
            for key, val in state.items():
                for xi in (0, 1):
                    new_state[key + (xi,)] = val * factor[xi]
        frontier_order.append(i)
        state = new_state
        peak_configs = max(peak_configs, len(state))

        # ── use: CZ phase between x_i and any active earlier x_j ─────
        xi_pos = frontier_order.index(i)
        for j in adj[i]:
            if j >= i or j not in frontier_order:
                continue
            xj_pos = frontier_order.index(j)
            for key in list(state.keys()):
                if key[xi_pos] == 1 and key[xj_pos] == 1:
                    state[key] = state[key] * -1.0

        # ── collapse: sum out any x_j with no neighbour beyond i ─────
        for j in list(frontier_order):
            if any(u > i for u in adj[j]):
                continue
            pos = frontier_order.index(j)
            collapsed: Dict[Tuple[int, ...], np.ndarray] = {}
            for key, val in state.items():
                reduced_key = key[:pos] + key[pos + 1:]
                if reduced_key in collapsed:
                    collapsed[reduced_key] = collapsed[reduced_key] + val
                else:
                    collapsed[reduced_key] = val
            state = collapsed
            frontier_order.remove(j)

        # ── PRUNE: drop low-magnitude configurations (the new step) ──
        if threshold > 0.0 and state:
            mags = {k: float(np.max(np.abs(v))) for k, v in state.items()}
            current_max = max(mags.values()) if mags else 0.0
            cutoff = threshold * current_max
            kept = {k: v for k, v in state.items() if mags[k] >= cutoff}
            total_pruned += len(state) - len(kept)
            state = kept

    # Exactly one key should remain: the empty tuple, value array shaped
    # over open_y_order (in that axis order).
    assert len(state) <= 1, (
        f"expected at most one surviving frontier config, got {len(state)} "
        "— sparse bookkeeping bug, not a pruning effect."
    )
    T = state.get((), np.zeros((2,) * len(open_qubits), dtype=np.float64))

    # Reorder axes from open_y_order to the caller's requested open_qubits
    # order, same convention as the exact contract_frontier.
    if open_y_order:
        order = [open_y_order.index(q) for q in open_qubits]
        T = np.transpose(T, axes=order)

    stats = {
        "peak_configs": peak_configs,
        "peak_bytes_approx": peak_configs * (2 ** len(open_qubits)) * BYTES_PER_ELEM,
        "total_pruned": total_pruned,
        "edges": len(edges),
    }
    return T, stats


# ══════════════════════════════════════════════════════════════════
# 2. STAGE 1 — sparse encoding sanity check (threshold = 0.0 only)
# ══════════════════════════════════════════════════════════════════

def verify_sparse_exact(n: int = 12, bands: Sequence[int] = (2, 3, 5, 7)) -> bool:
    """
    Confirms the sparse/dict re-implementation, with pruning OFF, exactly
    reproduces the existing exact contract_frontier from banded_scaling.py.

    This is a check on the NEW CODE, not on the pruning idea. If this
    fails, the bug is in the sparse magnify/use/collapse bookkeeping above
    — do not proceed to threshold sweeps until this passes.
    """
    print("=" * 78)
    print("STAGE 1 — sparse (unpruned) contraction vs exact contract_frontier")
    print("=" * 78)
    print("threshold=0.0 must match the exact dense result to ~1e-12.")
    print("This isolates 'is the sparse encoding correct' from 'does pruning")
    print("preserve accuracy' — the latter is Stage 2, not tested here.\n")

    alphas, betas = deterministic_angles(n)
    all_ok = True

    for w in bands:
        open_qubits = [n // 2 - 1, n // 2, n // 2 + 1]
        y_fixed = {q: (q % 2) for q in range(n) if q not in open_qubits}

        T_exact, _ = contract_frontier(n, w, alphas, betas, y_fixed, open_qubits)
        T_sparse, _ = contract_frontier_pruned(
            n, w, alphas, betas, y_fixed, open_qubits, threshold=0.0)

        err = float(np.max(np.abs(T_exact - T_sparse)))
        ok = err < 1e-12
        all_ok &= ok
        print(f"  n={n:2d} band={w:2d}  max_abs_err_vs_exact={err:.3e}  "
              f"{'OK' if ok else 'FAIL'}")

    print(f"\n{'PASS' if all_ok else 'FAIL'}: sparse encoding is mechanically "
          f"correct with pruning off.\n")
    return all_ok


# ══════════════════════════════════════════════════════════════════
# 3. STAGE 2 — threshold sweep (the actual pruning experiment)
# ══════════════════════════════════════════════════════════════════

def threshold_sweep(
    n: int, w: int, thresholds: Sequence[float], n_open: int = 5,
    repeats: int = 3,
) -> List[Dict]:
    alphas, betas = deterministic_angles(n)
    mid = n // 2
    open_qubits = list(range(mid - n_open // 2, mid - n_open // 2 + n_open))
    y_fixed = {q: (q % 2) for q in range(n) if q not in open_qubits}

    print("=" * 78)
    print(f"STAGE 2 — threshold sweep, n={n}, band={w}, "
          f"{n_open} open outputs ({2 ** n_open} amplitudes)")
    print("=" * 78)
    print("Ground truth is the exact contract_frontier from banded_scaling.py.")
    print("Comparing: reconstruction error, configs retained vs 2^w, time, "
          "approx. memory.\n")

    T_exact, exact_stats = contract_frontier(
        n, w, alphas, betas, y_fixed, open_qubits)
    exact_bytes = exact_stats["peak_bytes"]

    print(f"{'threshold':>10} {'max_abs_err':>12} {'peak_configs':>13} "
          f"{'vs_2^w':>8} {'time_s':>9} {'mem_ratio':>10}")
    print("-" * 78)

    rows: List[Dict] = []
    for thr in thresholds:
        samples = []
        T_pruned, stats = contract_frontier_pruned(
            n, w, alphas, betas, y_fixed, open_qubits, threshold=thr)
        for _ in range(repeats):
            t0 = time.perf_counter()
            contract_frontier_pruned(
                n, w, alphas, betas, y_fixed, open_qubits, threshold=thr)
            samples.append(time.perf_counter() - t0)
        t_med = statistics.median(samples)

        err = float(np.max(np.abs(T_exact - T_pruned)))
        vs_full = stats["peak_configs"] / float(2 ** w)
        mem_ratio = stats["peak_bytes_approx"] / float(exact_bytes)

        rows.append({
            "threshold": thr, "max_abs_err": err,
            "peak_configs": stats["peak_configs"], "vs_full": vs_full,
            "time_s": t_med, "mem_ratio": mem_ratio,
            "total_pruned": stats["total_pruned"],
        })
        print(f"{thr:>10.4f} {err:>12.3e} {stats['peak_configs']:>13d} "
              f"{vs_full:>8.3f} {t_med:>9.6f} {mem_ratio:>10.3f}")

    return rows


def interpret(rows: List[Dict]) -> None:
    print()
    print("=" * 78)
    print("INTERPRETATION")
    print("=" * 78)

    if not rows:
        print("No sweep rows to interpret.")
        return

    zero_row = next((r for r in rows if r["threshold"] == 0.0), None)
    if zero_row and zero_row["max_abs_err"] > 1e-10:
        print("WARNING: threshold=0.0 did not reproduce the exact result in")
        print("this sweep call. Re-run verify_sparse_exact() before trusting")
        print("anything else here — this indicates a bookkeeping bug, not a")
        print("pruning effect.\n")

    best_useful = [r for r in rows if r["threshold"] > 0.0 and r["max_abs_err"] < 1e-6]
    if best_useful:
        biggest = max(best_useful, key=lambda r: r["threshold"])
        print(f"Largest threshold tested that kept error < 1e-6: "
              f"{biggest['threshold']}")
        print(f"  -> retained {biggest['vs_full']:.1%} of the full 2^w frontier, "
              f"{biggest['time_s']:.6f}s, ~{biggest['mem_ratio']:.1%} of exact "
              f"memory.")
    else:
        print("No tested threshold kept error below 1e-6 on this circuit/width.")
        print("Either the thresholds tried were too aggressive, or this circuit")
        print("family does not tolerate amplitude pruning well at this width —")
        print("both are legitimate, useful outcomes, not failures of the code.")

    print()
    print("What this does NOT show, to keep the record honest:")
    print("  * no claim about physical electron capacity or physical position —")
    print("    every coordinate here is an abstract frontier-configuration")
    print("    magnitude in the algorithm's own state space, nothing more.")
    print("  * no claim of novelty for amplitude-magnitude pruning itself —")
    print("    this is standard tensor-network truncation practice; the open")
    print("    question is only whether THIS circuit family tolerates it.")
    print("  * memory figures are an approximation (dict entries vs a flat")
    print("    array) — real Python dict overhead is not fully modelled here.")
    print("  * this is unrelated to the exact contract_frontier() results")
    print("    already published; banded_scaling.py's own numbers are")
    print("    unaffected by anything in this file.")
    print()


def main():
    p = argparse.ArgumentParser(
        description="EQCCM amplitude-magnitude pruning experiment (separate "
                     "from the exact control in banded_scaling.py)")
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--w", type=int, default=14)
    p.add_argument("--open", dest="n_open", type=int, default=5)
    p.add_argument("--thresholds", type=float, nargs="+",
                   default=[0.0, 1e-6, 1e-4, 1e-3, 1e-2, 5e-2])
    p.add_argument("--verify-only", action="store_true",
                   help="run Stage 1 only, skip the threshold sweep")
    args = p.parse_args()

    print()
    print("#" * 78)
    print("# EQCCM — amplitude-magnitude pruning experiment (EXPERIMENTAL)")
    print("# Adds a pruning step to a separate copy of the elimination loop.")
    print("# banded_scaling.py's exact results are untouched by this file.")
    print("#" * 78)
    print()

    if not verify_sparse_exact():
        print("Stage 1 failed — not proceeding to the threshold sweep.")
        return
    if args.verify_only:
        return

    if args.w >= args.n:
        args.w = args.n - 2
        print(f"(clamped --w to {args.w}; band must be < n)\n")

    rows = threshold_sweep(args.n, args.w, args.thresholds, args.n_open)
    interpret(rows)


if __name__ == "__main__":
    main()
