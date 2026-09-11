"""
AUDIT — Addendum VI reported ABSOLUTE error only. This recomputes it RELATIVE
to the amplitude scale, and finds the published headline does not survive.
==============================================================================

STATUS: this script CORRECTS a published result (Zenodo v2, technical record
§45-46). It is read-only: banded_scaling.py and banded_scaling_pruned.py are
imported, never modified, so the original numbers remain reproducible exactly
as published and this audit can be checked against them independently.

HOW THE ERROR WAS FOUND
While testing whether the Addendum VI pruning result transfers to the real
heavy-hex topology (heavyhex_pruned.py), the heavy-hex sweep produced an error
"plateau" that turned out to be the computed amplitudes coming out EXACTLY
ZERO. A zero answer registers as a small ABSOLUTE error whenever the true
amplitudes are themselves small. Addendum VI reported a plateau of exactly the
same shape, on amplitudes of order 1e-04. That prompted this audit.

WHAT THE AUDIT SHOWS

  1. The published w=20 datapoint reproduces EXACTLY: abs_err = 1.459e-04
     with 104 configurations retained, at n=26, 5 open outputs, threshold 0.9.
     So this is not a discrepancy in setup — it is the same computation, newly
     measured against the amplitude scale.

  2. max|exact| at that point is 1.4685e-04. The "error" of 1.459e-04 is
     therefore 99.4% of the largest amplitude being computed. The pruned
     output's own scale is 5.43e-06, about 3.7% of truth. The result carries
     no usable signal.

  3. This holds at every width tested: abs_err / max|exact| =
     1.006 (w=8), 0.996 (w=12), 0.953 (w=16), 0.994 (w=20).
     In other words abs_err ~= max|exact| always, which is the arithmetic
     signature of an output near zero.

  4. Therefore the published claim "error IMPROVES monotonically with width,
     24x from w=8 to w=20" is an ARTEFACT. Absolute error tracked the
     amplitude scale, and the amplitude scale shrinks as width grows. It was
     never a statement about approximation quality.

  5. Likewise the published "error curve is a PLATEAU, not a cliff" is the
     signature of total signal loss, not of graceful degradation. The plateau
     sits at abs_err = max|exact| because the answer is ~0.

  6. Fatally, there is NO threshold that both saves work and stays correct:
       * faithful region (threshold <= 1e-3): retained configurations stay at
         2.0 x 2^w, i.e. the full frontier — pruning removes NOTHING.
       * saving region (threshold >= 0.05): relative error ~ 1.0 — no signal.
     The two regions do not overlap. The "0.01% of configurations, ~14,000x
     faster" figure belongs entirely to the second region.

CONSEQUENCE
The Addendum VI headline ("amplitude pruning reaches 1.5e-04 accuracy on 0.01%
of configurations, and gets more accurate as the problem gets harder") is
withdrawn. The §46 sub-claim that this weakens the 2^w hardness argument is
also withdrawn: it was derived from the same numbers, so approximate classical
cost is NOT shown to be below 2^w by this evidence.

What genuinely survives:
  * Stage 1 is unaffected: the sparse re-encoding is exact at threshold 0.0
    (0.000e+00 agreement). That was a test of the mechanism and it stands.
  * banded_scaling.py's EXACT results are untouched and unaffected — no
    pruning is involved in them.
  * The methodological lesson, which is now the actual result: an accuracy
    claim must be quoted RELATIVE to the scale of the quantity computed, and
    an approximation must be shown to return a non-zero answer. Reporting
    absolute error alone let a zero output look like a 1e-04 accuracy.

Run:
    python demo/eqccm/addendum_vi_relative_error_audit.py
    python demo/eqccm/addendum_vi_relative_error_audit.py --full

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banded_scaling import contract_frontier, deterministic_angles
from banded_scaling_pruned import contract_frontier_pruned

# Exactly as printed in EQCCM-technical-record-extracted.txt §46
PUBLISHED = {8: (3.550e-03, 22), 12: (3.312e-03, 22),
             16: (7.188e-04, 74), 20: (1.459e-04, 104)}

N, N_OPEN = 26, 5   # §46: "Full w=20 sweep (n=26)", "5 open outputs throughout"


def setup(n, n_open):
    alphas, betas = deterministic_angles(n)
    mid = n // 2
    open_qubits = list(range(mid - n_open // 2, mid - n_open // 2 + n_open))
    y_fixed = {q: (q % 2) for q in range(n) if q not in open_qubits}
    return alphas, betas, open_qubits, y_fixed


def verdict_for(rel):
    if rel < 1e-6:
        return "faithful"
    if rel < 1e-3:
        return "usable (<0.1%)"
    if rel < 1e-2:
        return "marginal (<1%)"
    if rel < 0.5:
        return "badly degraded"
    return "NO SIGNAL"


def audit_published():
    print("=" * 88)
    print("PART 1 — the published threshold-0.9 table, with relative error added")
    print("=" * 88)
    print(f"n={N}, {N_OPEN} open outputs, threshold 0.9 (as published)\n")
    print(f"{'w':>4} {'max|exact|':>12} {'max|pruned|':>12} {'abs_err':>11} "
          f"{'published':>11} {'repro':>6} {'kept':>6} {'pub':>5} "
          f"{'REL_ERR':>9}  verdict")
    print("-" * 100)

    for w in (8, 12, 16, 20):
        alphas, betas, open_qubits, y_fixed = setup(N, N_OPEN)
        T_exact, _ = contract_frontier(N, w, alphas, betas, y_fixed, open_qubits)
        ex_scale = float(np.max(np.abs(T_exact)))
        T_p, stats = contract_frontier_pruned(
            N, w, alphas, betas, y_fixed, open_qubits, threshold=0.9)
        pr_scale = float(np.max(np.abs(T_p)))
        abs_err = float(np.max(np.abs(T_exact - T_p)))
        rel = abs_err / ex_scale if ex_scale > 0 else float("nan")
        pub_err, pub_cfg = PUBLISHED[w]
        repro = "EXACT" if abs(abs_err - pub_err) / pub_err < 0.05 else "-"
        print(f"{w:>4} {ex_scale:>12.4e} {pr_scale:>12.4e} {abs_err:>11.3e} "
              f"{pub_err:>11.3e} {repro:>6} {stats['peak_configs']:>6d} "
              f"{pub_cfg:>5d} {rel:>9.4f}  {verdict_for(rel)}")

    print()
    print("The w=20 row reproduces the published figure exactly, so this is the")
    print("same computation. Its relative error is 99.4%: the answer is gone.")
    print("Note abs_err ~= max|exact| on every row — the signature of a ~zero")
    print("output, and the reason absolute error appeared to improve with width.")
    print()


def audit_salvage(widths=(12, 16)):
    print("=" * 88)
    print("PART 2 — is there ANY threshold that is both faithful and cheaper?")
    print("=" * 88)
    thresholds = [0.0, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.05, 0.2, 0.5, 0.9]

    for w in widths:
        alphas, betas, open_qubits, y_fixed = setup(N, N_OPEN)
        T_exact, _ = contract_frontier(N, w, alphas, betas, y_fixed, open_qubits)
        ex_scale = float(np.max(np.abs(T_exact)))
        print(f"\nn={N}, w={w}, max|exact| = {ex_scale:.4e}, full 2^w = {2**w:,}")
        print(f"{'threshold':>10} {'abs_err':>11} {'REL_ERR':>10} {'kept':>9} "
              f"{'kept/2^w':>9}  verdict")
        print("-" * 88)
        for thr in thresholds:
            T_p, stats = contract_frontier_pruned(
                N, w, alphas, betas, y_fixed, open_qubits, threshold=thr)
            abs_err = float(np.max(np.abs(T_exact - T_p)))
            rel = abs_err / ex_scale if ex_scale > 0 else float("nan")
            kept = stats["peak_configs"]
            print(f"{thr:>10.6f} {abs_err:>11.3e} {rel:>10.4f} {kept:>9,} "
                  f"{kept / float(2 ** w):>9.4f}  {verdict_for(rel)}")

    print()
    print("Result: the faithful rows retain ~2.0 x 2^w (the full frontier plus")
    print("the known transient doubling) — pruning removes nothing there. Every")
    print("row that removes a meaningful number of configurations is NO SIGNAL.")
    print("The regions do not overlap, so the published speed/accuracy pairing")
    print("does not exist.")
    print()


def main():
    p = argparse.ArgumentParser(description="Relative-error audit of Addendum VI")
    p.add_argument("--full", action="store_true",
                   help="also sweep w=16 in Part 2 (slower)")
    args = p.parse_args()

    print()
    print("#" * 88)
    print("# AUDIT — Addendum VI relative-error correction")
    print("# Read-only: banded_scaling*.py are imported, never modified.")
    print("#" * 88)
    print()
    audit_published()
    audit_salvage((12, 16) if args.full else (12,))
    print("=" * 88)
    print("CONCLUSION: the Addendum VI accuracy headline is withdrawn. What")
    print("stands is Stage 1 (exact at threshold 0.0), the untouched exact")
    print("results in banded_scaling.py, and the methodological lesson that")
    print("accuracy must be reported relative to the computed scale.")
    print("=" * 88)
    print()


if __name__ == "__main__":
    main()
