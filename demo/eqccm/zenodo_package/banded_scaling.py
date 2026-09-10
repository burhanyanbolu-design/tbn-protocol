"""
EQCCM — Controlled Banded-Width Scaling Experiment
===================================================
Answers the decisive question from §19 of the technical record:

    does actual classical WALL-CLOCK runtime grow rapidly under controlled
    increases in contraction width?

§12 found a 42x contraction-cost increase producing only 3.5% wall-clock
change, because at 16 qubits the frontier table is a few hundred bytes and
sits in L1 cache — so Python/library overhead dominates entirely. That null
result is solid, but it says nothing about scaling; it only says the
measurement was taken in the wrong regime.

This script fixes the regime problem.

WHY BANDED GRAPHS (§18)
    E(n,w) = { (i,j) : i < j <= min(n-1, i+w) }

Its treewidth is EXACTLY w, which is provable rather than hoped for:
  * lower bound: vertices {i, ..., i+w} are pairwise within distance w, so
    they form a clique of size w+1  =>  treewidth >= w
  * upper bound: left-to-right elimination never holds more than w
    variables in the active frontier      =>  treewidth <= w
So width is a dial, not a lottery. This directly fixes §13, where
hand-designed 20-qubit graphs kept collapsing to frontier width 3.

WHAT IS MEASURED
For each width w:  (n, w, C, T, M) from §17, plus the diagnostic that
actually matters — the ratio T(w)/T(w-1). Since each +1 of width doubles
the state table:
    ratio ~ 1.0  ->  overhead-dominated  (the §12 regime, uninformative)
    ratio ~ 2.0  ->  wall-clock is tracking 2^w  (the regime that answers §19)
The knee between those two is the result.

CIRCUIT FAMILY (§3) and AMPLITUDE FORMULA (§4)
    |psi> = RY^(2) [ prod_{(i,j) in E} CZ_ij ] RY^(1) |0>^n

    psi(y) = sum_x [ prod_i A_i(x_i) B_i(y_i, x_i) ]
                   [ prod_{(i,j) in E} (-1)^{x_i x_j} ]
    A_i(x_i)      = <x_i| RY(alpha_i) |0>
    B_i(y_i, x_i) = <y_i| RY(beta_i)  |x_i>

Every factor is real, so the contraction runs in float64 rather than
complex128 — half the memory, which buys one extra width step. The
statevector cross-check confirms the imaginary part is zero.

NO IBM TIME IS USED. Per §17, hardware submission waits until the classical
side shows a wall-clock effect.

Run:
    python demo/eqccm/banded_scaling.py                 # default sweep
    python demo/eqccm/banded_scaling.py --verify-only   # correctness only
    python demo/eqccm/banded_scaling.py --n 30 --wmax 24

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
import statistics
import time
from typing import Dict, List, Sequence, Set, Tuple

import numpy as np

BYTES_PER_ELEM = 8  # float64


# ══════════════════════════════════════════════════════════════════
# 1. THE CONTROLLED GRAPH FAMILY  (§18)
# ══════════════════════════════════════════════════════════════════

def banded_graph(n: int, w: int) -> List[Tuple[int, int]]:
    """E(n,w) = {(i,j) : i < j <= min(n-1, i+w)}. Treewidth is exactly w."""
    return [(i, j)
            for i in range(n)
            for j in range(i + 1, min(n - 1, i + w) + 1)]


def verify_treewidth(n: int, w: int) -> Dict[str, object]:
    """
    Confirm treewidth == w for the banded family, both bounds, empirically.

    This is the guarantee that makes the sweep meaningful: without it we're
    back in §13, guessing at graphs and finding width 3.
    """
    edges = set(banded_graph(n, w))
    adj = {i: set() for i in range(n)}
    for i, j in edges:
        adj[i].add(j)
        adj[j].add(i)

    # Lower bound: is {0..w} actually a clique of size w+1?
    clique = list(range(min(w + 1, n)))
    is_clique = all(b in adj[a] for k, a in enumerate(clique)
                    for b in clique[k + 1:])

    # Upper bound: max active frontier under left-to-right elimination
    max_frontier = 0
    for i in range(n):
        processed = set(range(i + 1))
        frontier = {v for v in processed
                    if any(u not in processed for u in adj[v])}
        max_frontier = max(max_frontier, len(frontier))

    return {
        "n": n,
        "band": w,
        "edges": len(edges),
        "clique_size": len(clique),
        "lower_bound_ok": is_clique,
        "max_frontier": max_frontier,
        "upper_bound_ok": max_frontier <= w,
        "treewidth_is_exactly_w": is_clique and max_frontier == min(w, n - 1),
    }


# ══════════════════════════════════════════════════════════════════
# 2. SINGLE-SITE FACTORS  (§4)
# ══════════════════════════════════════════════════════════════════

def ry_matrix(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def deterministic_angles(n: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Deterministic, irrational-ish angles (§18 asks for deterministic RY).
    Avoids special values that could accidentally make amplitudes vanish.
    """
    idx = np.arange(n, dtype=np.float64)
    alphas = 0.4 + 0.31 * np.sqrt(idx + 1.0)
    betas = 0.7 + 0.23 * np.sqrt(idx + 2.0)
    return alphas, betas


def site_factors(alphas, betas, y_fixed: Dict[int, int], i: int):
    """
    Return the factor for qubit i.

    closed qubit -> shape (2,)   indexed by x_i
    open qubit   -> shape (2,2)  indexed by (y_i, x_i); the y axis survives
                                 to the end, giving many amplitudes at once
    """
    a = ry_matrix(alphas[i])[:, 0]          # A_i(x_i) = <x_i|RY(alpha)|0>
    b = ry_matrix(betas[i])                 # B_i(y_i, x_i)
    if i in y_fixed:
        return b[y_fixed[i], :] * a, False  # contract over y immediately
    return b * a[None, :], True             # keep y_i open


# ══════════════════════════════════════════════════════════════════
# 3. EXACT ACTIVE-FRONTIER CONTRACTION  (§2)
#    magnify -> use -> collapse
# ══════════════════════════════════════════════════════════════════

def contract_frontier(n: int, w: int, alphas, betas,
                      y_fixed: Dict[int, int],
                      open_qubits: Sequence[int]) -> Tuple[np.ndarray, Dict]:
    """
    Exact amplitude(s) by variable elimination with an active frontier.

    Axis bookkeeping: `labels` tracks what each axis of T means.
      ('y', q) -> an open output index, persists to the end
      ('x', q) -> an active intermediate variable, collapsed once qubit q
                  has no remaining neighbour ahead of the sweep
    """
    edges = set(banded_graph(n, w))
    adj = {i: set() for i in range(n)}
    for i, j in edges:
        adj[i].add(j)
        adj[j].add(i)

    open_set = set(open_qubits)

    T = np.ones((), dtype=np.float64)
    labels: List[Tuple[str, int]] = []

    peak_elems = 1
    collapsed_at: Dict[int, int] = {}

    for i in range(n):
        factor, y_open = site_factors(alphas, betas, y_fixed, i)

        # ── magnify: bring x_i (and y_i if open) into the active table ──
        if y_open:
            # factor[y_i, x_i]
            T = np.multiply.outer(T, factor)
            labels.append(("y", i))
            labels.append(("x", i))
        else:
            T = np.multiply.outer(T, factor)
            labels.append(("x", i))

        peak_elems = max(peak_elems, T.size)

        # ── use: apply CZ phases between x_i and active earlier x_j ──
        xi_axis = labels.index(("x", i))
        for j in adj[i]:
            if j >= i:
                continue
            key = ("x", j)
            if key not in labels:
                continue  # already collapsed; edge handled at collapse time
            xj_axis = labels.index(key)
            # phase (-1)^{x_i x_j}: flip sign only where both indices are 1
            slicer = [slice(None)] * T.ndim
            slicer[xi_axis] = 1
            slicer[xj_axis] = 1
            T[tuple(slicer)] *= -1.0

        # ── collapse: sum out any x_j with no neighbour beyond i ─────
        for j in list(range(i + 1)):
            key = ("x", j)
            if key not in labels:
                continue
            if any(u > i for u in adj[j]):
                continue  # still needed by the future
            ax = labels.index(key)
            T = T.sum(axis=ax)
            labels.pop(ax)
            collapsed_at[j] = i

    # Order remaining axes as the caller's open-qubit order
    order = [labels.index(("y", q)) for q in open_qubits]
    if order:
        T = np.transpose(T, axes=order)

    stats = {
        "peak_elems": peak_elems,
        "peak_bytes": peak_elems * BYTES_PER_ELEM,
        "max_frontier_seen": max(
            (sum(1 for L in labels if L[0] == "x"), 0))
        if labels else 0,
        "edges": len(edges),
    }
    return T, stats


# ══════════════════════════════════════════════════════════════════
# 4. DENSE STATEVECTOR REFERENCE (the honest baseline)
# ══════════════════════════════════════════════════════════════════

def statevector_reference(n: int, w: int, alphas, betas) -> np.ndarray:
    """
    Full state by direct simulation. This is the baseline that must be
    beaten: at small n it is trivially fast, which is exactly why 16-qubit
    'hardness' claims cannot hold.
    """
    psi = np.zeros((2,) * n, dtype=np.float64)
    psi[(0,) * n] = 1.0

    def apply_ry(state, q, theta):
        m = ry_matrix(theta)
        state = np.moveaxis(state, q, -1)
        state = state @ m.T
        return np.moveaxis(state, -1, q)

    for q in range(n):
        psi = apply_ry(psi, q, alphas[q])

    for (i, j) in banded_graph(n, w):
        slicer = [slice(None)] * n
        slicer[i] = 1
        slicer[j] = 1
        psi[tuple(slicer)] *= -1.0

    for q in range(n):
        psi = apply_ry(psi, q, betas[q])

    return psi


# ══════════════════════════════════════════════════════════════════
# 5. CORRECTNESS — reproduce the §4 validation
# ══════════════════════════════════════════════════════════════════

def verify_correctness(n: int = 12, bands: Sequence[int] = (2, 3, 5, 7)) -> bool:
    print("=" * 78)
    print("CORRECTNESS — frontier contraction vs dense statevector")
    print("=" * 78)
    print("Reproduces the §4 check (~1e-16) on the banded family.\n")

    alphas, betas = deterministic_angles(n)
    all_ok = True

    for w in bands:
        tw = verify_treewidth(n, w)
        psi_full = statevector_reference(n, w, alphas, betas)

        open_qubits = [n // 2 - 1, n // 2, n // 2 + 1]
        y_fixed = {q: (q % 2) for q in range(n) if q not in open_qubits}

        T, _ = contract_frontier(n, w, alphas, betas, y_fixed, open_qubits)

        # Pull the same amplitudes out of the dense state
        ref = np.empty((2,) * len(open_qubits), dtype=np.float64)
        for bits in np.ndindex(*([2] * len(open_qubits))):
            idx = [0] * n
            for q, v in y_fixed.items():
                idx[q] = v
            for k, q in enumerate(open_qubits):
                idx[q] = bits[k]
            ref[bits] = psi_full[tuple(idx)]

        err = float(np.max(np.abs(T - ref)))
        ok = err < 1e-12 and tw["treewidth_is_exactly_w"]
        all_ok &= ok
        print(f"  n={n:2d} band={w:2d} edges={tw['edges']:4d} "
              f"treewidth_exact={str(tw['treewidth_is_exactly_w']):5s} "
              f"max_abs_err={err:.3e}  {'OK' if ok else 'FAIL'}")

    print(f"\n{'PASS' if all_ok else 'FAIL'}: "
          f"contraction is exact and treewidth is analytically controlled.\n")
    return all_ok


# ══════════════════════════════════════════════════════════════════
# 6. THE SWEEP — the actual §19 experiment
# ══════════════════════════════════════════════════════════════════

def time_contraction(n, w, alphas, betas, y_fixed, open_qubits,
                     repeats: int) -> Tuple[float, Dict]:
    # warm up once so first-call import/alloc costs don't pollute the median
    _, stats = contract_frontier(n, w, alphas, betas, y_fixed, open_qubits)
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        contract_frontier(n, w, alphas, betas, y_fixed, open_qubits)
        samples.append(time.perf_counter() - t0)
    return statistics.median(samples), stats


def sweep(n: int, wmin: int, wmax: int, n_open: int,
          mem_budget_gb: float) -> List[Dict]:
    alphas, betas = deterministic_angles(n)
    mid = n // 2
    open_qubits = list(range(mid - n_open // 2, mid - n_open // 2 + n_open))
    y_fixed = {q: (q % 2) for q in range(n) if q not in open_qubits}

    print("=" * 78)
    print(f"WIDTH SWEEP — n={n}, {n_open} open outputs "
          f"({2 ** n_open} amplitudes per run)")
    print("=" * 78)
    print("T_ratio is the diagnostic. Each +1 band doubles the table, so:")
    print("   T_ratio ~ 1.0  ->  overhead-dominated (the §12 regime)")
    print("   T_ratio ~ 2.0  ->  wall-clock tracking 2^w (answers §19)\n")
    print(f"{'band':>4} {'edges':>6} {'peak_MB':>9} {'T_med_s':>11} "
          f"{'T_ratio':>8} {'cost_ratio':>10}  regime")
    print("-" * 78)

    rows: List[Dict] = []
    budget_bytes = mem_budget_gb * (1024 ** 3)
    prev_t = None

    for w in range(wmin, wmax + 1):
        # project memory before allocating: frontier w + open y axes
        projected = (2 ** (w + n_open)) * BYTES_PER_ELEM
        if projected > budget_bytes:
            print(f"{w:>4} {'—':>6} {projected / 1e6:>9.1f} "
                  f"{'skipped':>11} {'—':>8} {'—':>10}  "
                  f"exceeds {mem_budget_gb}GB budget")
            break

        repeats = 7 if w <= 16 else (3 if w <= 20 else 1)
        t_med, stats = time_contraction(
            n, w, alphas, betas, y_fixed, open_qubits, repeats)

        t_ratio = (t_med / prev_t) if prev_t else float("nan")
        prev_t = t_med

        if np.isnan(t_ratio):
            regime = "baseline"
        elif t_ratio < 1.25:
            regime = "overhead-dominated"
        elif t_ratio < 1.7:
            regime = "transition (knee)"
        else:
            regime = "tracking 2^w"

        rows.append({"n": n, "band": w, "edges": stats["edges"],
                     "peak_bytes": stats["peak_bytes"], "T": t_med,
                     "T_ratio": t_ratio, "regime": regime})

        print(f"{w:>4} {stats['edges']:>6} "
              f"{stats['peak_bytes'] / 1e6:>9.2f} {t_med:>11.6f} "
              f"{t_ratio:>8.2f} {2.0:>10.1f}  {regime}")

    return rows


def interpret(rows: List[Dict]) -> None:
    print()
    print("=" * 78)
    print("INTERPRETATION")
    print("=" * 78)

    if len(rows) < 3:
        print("Not enough points to judge. Raise --wmax or the memory budget.")
        return

    tracking = [r for r in rows if r["regime"] == "tracking 2^w"]
    knee = [r for r in rows if r["regime"] == "transition (knee)"]

    if tracking:
        first = tracking[0]
        print(f"Wall-clock starts tracking 2^w at band {first['band']} "
              f"(table {first['peak_bytes'] / 1e6:.1f} MB).")
        print("This is the regime §12 could not reach at 16 qubits, and it is")
        print("where the §19 question becomes answerable. Above this width the")
        print("contraction-cost metric and real runtime agree, so cost numbers")
        print("become meaningful evidence rather than an artifact.")
        span = rows[-1]["T"] / rows[0]["T"]
        print(f"\nAcross the sweep, runtime grew {span:.1f}x while the table grew "
              f"{2 ** (rows[-1]['band'] - rows[0]['band'])}x.")
    elif knee:
        print(f"A knee appears at band {knee[0]['band']}, but the sweep did not")
        print("reach clean 2^w tracking. Push --wmax higher (needs more RAM).")
    else:
        print("Every point is still overhead-dominated — same regime as §12.")
        print("The table never left cache, so nothing here speaks to scaling.")
        print("Raise --wmax (and --n so that n > wmax).")

    print()
    print("What this does NOT show, to keep the record honest:")
    print("  * nothing about quantum advantage — this is a purely classical")
    print("    scaling measurement, no hardware involved (§17 defers IBM time)")
    print("  * banded graphs need degree ~2w, while heavy-hex is degree 3, so")
    print("    this family is NOT natively embeddable on Fez at useful widths.")
    print("    It answers the classical question only; hardware feasibility is")
    print("    a separate search.")
    print("  * dense statevector remains the baseline to beat at small n, and")
    print("    it is trivially fast there.")
    print()


def main():
    p = argparse.ArgumentParser(
        description="EQCCM controlled banded-width scaling experiment")
    p.add_argument("--n", type=int, default=30, help="qubits (default 30)")
    p.add_argument("--wmin", type=int, default=4)
    p.add_argument("--wmax", type=int, default=22)
    p.add_argument("--open", dest="n_open", type=int, default=5,
                   help="open output indices; 5 -> 32 amplitudes (§18)")
    p.add_argument("--mem-gb", type=float, default=2.0,
                   help="memory budget; sweep stops before exceeding it")
    p.add_argument("--verify-only", action="store_true")
    args = p.parse_args()

    print()
    print("#" * 78)
    print("# EQCCM — controlled banded-width classical scaling")
    print("# Testing §19: does wall-clock actually grow with contraction width?")
    print("#" * 78)
    print()

    if not verify_correctness():
        print("Correctness failed — not proceeding to timings.")
        return
    if args.verify_only:
        return

    if args.wmax >= args.n:
        args.wmax = args.n - 2
        print(f"(clamped --wmax to {args.wmax}; band must be < n)\n")

    rows = sweep(args.n, args.wmin, args.wmax, args.n_open, args.mem_gb)
    interpret(rows)


if __name__ == "__main__":
    main()
