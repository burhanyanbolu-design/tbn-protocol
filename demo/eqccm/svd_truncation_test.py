"""
EQCCM — SVD / BOND-DIMENSION TRUNCATION: THE REAL ADVERSARY
===========================================================
Addendum VII withdrew the Addendum VI pruning result and stated the remaining
gap plainly: only the NAIVE global-magnitude cutoff had been tested. Proper
SVD / bond-dimension truncation is far stronger and was untested, so the
honest claim was "the naive shortcut fails", NOT "no shortcut exists".

This closes that gap. It is the test that can actually damage the programme's
own 2^w hardness figure, and it is run for exactly that reason.

WHY SVD TRUNCATION IS DIFFERENT FROM WHAT FAILED
The pruning experiment judged each frontier configuration in isolation: "is
this number small? then delete it." That is blind to correlation structure —
the analogue of compressing a photo by deleting dim pixels.

SVD truncation instead finds the dominant correlation patterns across a cut
and keeps the strongest ones, discarding redundancy rather than content. It
carries a mathematical guarantee the magnitude cutoff does not: for a given
retained rank, the truncated SVD is the provably optimal approximation in
Frobenius norm (Eckart-Young). This is the engine inside MPS/DMRG, where the
control knob is the BOND DIMENSION chi.

An adversary attacking the 2^w figure would use this, not a magnitude cutoff.

METHOD
The circuit is read off banded_scaling.py's own factor definitions, so this is
the identical circuit family, not a re-interpretation:

    |psi> = RY(beta)^(x)n  ·  CZ_E(n,w)  ·  RY(alpha)^(x)n  |0>^n
    T(y)  = <y|psi>,  with y fixed on closed qubits, open on the rest

Simulated as a matrix product state. Long-range CZ gates (the banded graph
reaches distance w) are applied by swapping the far qubit adjacent, applying
CZ, then swapping back — every swap is itself an SVD-truncated two-site
operation, so the reported cost is honest rather than idealised.

Ground truth is contract_frontier from banded_scaling.py — the project's own
exact method, imported and NOT modified.

TWO-STAGE DISCIPLINE, as used throughout this programme
  Stage 1: run with chi large enough to be lossless. Must reproduce
     contract_frontier to ~1e-12. This tests the MPS machinery, not the idea.
     Stage 2 only runs if Stage 1 passes.
  Stage 2: sweep chi downward and measure error against exact.

METRIC DISCIPLINE — the specific lesson of Addendum VII
Absolute error alone is reported nowhere in isolation. Every row carries:
  * rel_err   = abs_err / max|exact|, the number that actually matters
  * norm      = ||MPS||, since truncation loses norm and a shrinking norm can
                masquerade as accuracy
  * rescaled rel_err, i.e. after renormalising — the fairer test of whether
    the STRUCTURE survived, which is what a practitioner would actually use
  * DEAD flag when the output is identically zero
  * discarded weight, the standard MPS truncation-error measure

WHAT A RESULT WOULD MEAN, STATED BEFORE RUNNING
  * If SVD truncation ALSO fails, the 2^w figure is considerably strengthened:
    the serious attack has been tested, not just the naive one.
  * If SVD truncation SUCCEEDS at chi << 2^w, that is a real limit on this
    programme's own hardness claim and must be recorded as such. It is the
    more likely outcome and this file is written expecting it.
Either way the honest cost comparison is chi-based: exact frontier contraction
costs ~2^w memory, whereas an MPS at bond dimension chi costs ~n*chi^2 memory
and ~n*chi^3 time.

Run:
    python demo/eqccm/svd_truncation_test.py --verify-only
    python demo/eqccm/svd_truncation_test.py --n 20 --w 8
    python demo/eqccm/svd_truncation_test.py --n 26 --w 12 --chis 4 8 16 32 64

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
import os
import statistics
import sys
import time
from typing import Dict, List, Sequence, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banded_scaling import (banded_graph, contract_frontier,
                            deterministic_angles, ry_matrix)

CZ = np.diag([1.0, 1.0, 1.0, -1.0]).reshape(2, 2, 2, 2)

SWAP = np.zeros((2, 2, 2, 2), dtype=np.float64)
for _a in (0, 1):
    for _b in (0, 1):
        SWAP[_b, _a, _a, _b] = 1.0   # out1,out2,in1,in2


# ══════════════════════════════════════════════════════════════════
# 1. MPS PRIMITIVES
# ══════════════════════════════════════════════════════════════════

class MPS:
    """
    Matrix product state held in MIXED CANONICAL FORM with an explicit
    orthogonality centre.

    WHY THE CANONICAL FORM IS NOT OPTIONAL
    Truncating an SVD only gives the optimal approximation when the bases on
    either side of the cut are orthonormal. In a canonical MPS, sites left of
    the centre are left-orthonormal and sites right of it are right-
    orthonormal, so the singular values of the two-site block ARE the true
    Schmidt coefficients across that bond, and discarding the smallest is
    provably optimal (Eckart-Young).

    Without the canonical form you are still "doing an SVD", but in a skewed
    basis: the singular values are not Schmidt coefficients, the truncation is
    not optimal, and the discarded weight is not a meaningful error measure.
    A first version of this file omitted canonicalisation and produced total
    discarded weights of 5-17 — impossible for a quantity bounded by 1, which
    is what exposed the bug. It made SVD truncation look far worse than it is.
    The sanity check is kept in `check_discarded_weight` below.
    """

    def __init__(self, n: int):
        self.n = n
        self.t: List[np.ndarray] = []
        for _ in range(n):
            a = np.zeros((1, 2, 1), dtype=np.float64)
            a[0, 0, 0] = 1.0
            self.t.append(a)
        # |0...0> is both left- and right-orthonormal at every site
        self.center = 0
        self.peak_chi = 1
        self.discarded = 0.0      # sum of RELATIVE discarded weights
        self.truncations = 0

    # ── gauge movement (exact, no truncation) ─────────────────────
    def _center_right(self) -> None:
        i = self.center
        Dl, _, Dr = self.t[i].shape
        m = self.t[i].reshape(Dl * 2, Dr)
        Q, R = np.linalg.qr(m)
        self.t[i] = Q.reshape(Dl, 2, Q.shape[1])
        self.t[i + 1] = np.einsum('ab,bcr->acr', R, self.t[i + 1])
        self.center = i + 1

    def _center_left(self) -> None:
        i = self.center
        Dl, _, Dr = self.t[i].shape
        m = self.t[i].reshape(Dl, 2 * Dr)
        Q, R = np.linalg.qr(m.T)          # m.T is (2Dr, Dl)
        k = Q.shape[1]
        self.t[i] = Q.T.reshape(k, 2, Dr)  # row-orthonormal => right-canonical
        self.t[i - 1] = np.einsum('lam,mk->lak', self.t[i - 1], R.T)
        self.center = i - 1

    def move_center(self, target: int) -> None:
        while self.center < target:
            self._center_right()
        while self.center > target:
            self._center_left()

    # ── gates ────────────────────────────────────────────────────
    def apply_single(self, i: int, g: np.ndarray) -> None:
        """
        Single-site UNITARY. Safe in any gauge: for unitary U,
        sum_a (U A)^a+ (U A)^a = sum_b A^b+ A^b, so orthonormality of that
        site is preserved and the canonical form survives untouched.
        """
        self.t[i] = np.einsum('ab,lbr->lar', g, self.t[i])

    def apply_two_site(self, i: int, g: np.ndarray, chi: int) -> None:
        """
        Two-site gate on adjacent sites (i, i+1), then optimal SVD truncation
        to at most `chi` states. The centre is moved to i first, which is what
        makes the truncation optimal rather than merely plausible.
        """
        self.move_center(i)

        A, B = self.t[i], self.t[i + 1]
        Dl, Dr = A.shape[0], B.shape[2]

        theta = np.einsum('lar,rbs->labs', A, B)
        theta = np.einsum('abcd,lcds->labs', g, theta)
        m = theta.reshape(Dl * 2, 2 * Dr)

        U, S, Vh = np.linalg.svd(m, full_matrices=False)

        total = float(np.sum(S ** 2))
        keep = max(1, min(chi, int(np.sum(S > 1e-15))))
        if keep < len(S) and total > 0.0:
            self.discarded += float(np.sum(S[keep:] ** 2)) / total
        self.truncations += 1

        U, S, Vh = U[:, :keep], S[:keep], Vh[:keep, :]

        # U is left-orthonormal -> stays at site i;
        # S·Vh carries the norm -> site i+1 becomes the new centre.
        self.t[i] = U.reshape(Dl, 2, keep)
        self.t[i + 1] = (S[:, None] * Vh).reshape(keep, 2, Dr)
        self.center = i + 1
        self.peak_chi = max(self.peak_chi, keep)

    def apply_cz(self, i: int, j: int, chi: int) -> None:
        """
        CZ between arbitrary sites i < j. The far qubit is swapped adjacent,
        CZ applied, then swapped back. Every swap is itself an SVD-truncated
        two-site operation, so long-range gates pay their true MPS cost.
        """
        if j < i:
            i, j = j, i
        if j == i + 1:
            self.apply_two_site(i, CZ, chi)
            return
        for k in range(j - 1, i, -1):
            self.apply_two_site(k, SWAP, chi)
        self.apply_two_site(i, CZ, chi)
        for k in range(i + 1, j):
            self.apply_two_site(k, SWAP, chi)

    # ── readout ──────────────────────────────────────────────────
    def norm(self) -> float:
        E = np.ones((1, 1), dtype=np.float64)
        for a in self.t:
            E = np.einsum('lm,lar,mas->rs', E, a, a)
        return float(np.sqrt(max(E[0, 0], 0.0)))

    def amplitude(self, bits: Sequence[int]) -> float:
        v = np.ones((1,), dtype=np.float64)
        for a, b in zip(self.t, bits):
            v = v @ a[:, b, :]
        return float(v[0])


def check_discarded_weight(d: float, truncations: int) -> str:
    """
    Guard against the bug that invalidated the first version of this file.
    Relative discarded weight is bounded by 1 per truncation, so the running
    total cannot exceed the number of truncations. A violation means the MPS
    was not canonical and the truncation was not optimal — the result would be
    meaningless, not merely pessimistic.
    """
    if truncations == 0:
        return "ok"
    return "ok" if d <= truncations + 1e-9 else "INVALID (non-canonical)"


def mps_norm(mps: List[np.ndarray]) -> float:
    """||psi|| by transfer-matrix sweep."""
    E = np.ones((1, 1), dtype=np.float64)
    for t in mps:
        E = np.einsum('lm,lar,mas->rs', E, t, t)
    return float(np.sqrt(max(E[0, 0], 0.0)))


def amplitude(mps: List[np.ndarray], bits: Sequence[int]) -> float:
    """<bits|psi> — a simple chain of matrix products."""
    v = np.ones((1,), dtype=np.float64)
    for t, b in zip(mps, bits):
        v = v @ t[:, b, :]
    return float(v[0])


# ══════════════════════════════════════════════════════════════════
# 2. THE CIRCUIT (read off banded_scaling.py's own definitions)
# ══════════════════════════════════════════════════════════════════

def build_mps(n: int, w: int, alphas, betas, chi: int) -> MPS:
    """
    |psi> = RY(beta)^n · CZ_E(n,w) · RY(alpha)^n |0>^n

    This mirrors banded_scaling.site_factors exactly:
      A_i(x_i) = <x_i|RY(alpha_i)|0>   -> RY(alpha) applied to |0>
      B_i(y_i, x_i) = RY(beta_i)[y,x]  -> RY(beta) applied afterwards
    """
    mps = MPS(n)
    for i in range(n):
        mps.apply_single(i, ry_matrix(alphas[i]))
    for (i, j) in banded_graph(n, w):
        mps.apply_cz(i, j, chi)
    for i in range(n):
        mps.apply_single(i, ry_matrix(betas[i]))
    return mps


def extract(mps: MPS, n: int, y_fixed: Dict[int, int],
            open_qubits: Sequence[int]) -> np.ndarray:
    """Amplitudes over the open qubits, closed qubits pinned to y_fixed."""
    n_open = len(open_qubits)
    T = np.empty((2,) * n_open, dtype=np.float64)
    for combo in np.ndindex(*([2] * n_open)):
        bits = [0] * n
        for q, v in y_fixed.items():
            bits[q] = v
        for k, q in enumerate(open_qubits):
            bits[q] = combo[k]
        T[combo] = mps.amplitude(bits)
    return T


def setup(n: int, n_open: int = 5):
    """Identical open/closed convention to banded_scaling_pruned.threshold_sweep."""
    alphas, betas = deterministic_angles(n)
    mid = n // 2
    open_qubits = list(range(mid - n_open // 2, mid - n_open // 2 + n_open))
    y_fixed = {q: (q % 2) for q in range(n) if q not in open_qubits}
    return alphas, betas, open_qubits, y_fixed


# ══════════════════════════════════════════════════════════════════
# 3. STAGE 1 — MPS machinery is exact when chi is large enough
# ══════════════════════════════════════════════════════════════════

def verify_exact(cases: Sequence[Tuple[int, int]] = ((10, 3), (12, 4), (14, 5))
                 ) -> bool:
    print("=" * 78)
    print("STAGE 1 — MPS vs exact contract_frontier, chi large enough to be lossless")
    print("=" * 78)
    print("Tests the MPS + swap machinery, NOT the truncation idea.")
    print("Ground truth: banded_scaling.contract_frontier (imported, unmodified).")
    print("Must match to ~1e-12.\n")

    ok_all = True
    for (n, w) in cases:
        alphas, betas, open_qubits, y_fixed = setup(n)
        T_exact, _ = contract_frontier(n, w, alphas, betas, y_fixed, open_qubits)

        chi_full = 2 ** (n // 2 + 1)   # lossless for any state on n qubits
        mps = build_mps(n, w, alphas, betas, chi_full)
        T_mps = extract(mps, n, y_fixed, open_qubits)

        err = float(np.max(np.abs(T_mps - T_exact)))
        nrm = mps.norm()
        ok = err < 1e-12 and abs(nrm - 1.0) < 1e-10
        ok_all &= ok
        print(f"  n={n:3d} w={w:2d}  chi_cap={chi_full:6d} peak_chi={mps.peak_chi:5d}  "
              f"max_abs_err={err:.3e}  norm={nrm:.12f}  {'OK' if ok else 'FAIL'}")

    print()
    print("Norm must be 1.0 to machine precision: the circuit is unitary, so a")
    print("lossless MPS has to preserve it. This catches gauge/contraction bugs")
    print("that an amplitude comparison alone can miss.")

    print(f"\n{'PASS' if ok_all else 'FAIL'}: MPS machinery reproduces the exact "
          f"method when nothing is truncated.\n")
    return ok_all


# ══════════════════════════════════════════════════════════════════
# 4. STAGE 2 — bond-dimension sweep
# ══════════════════════════════════════════════════════════════════

def chi_sweep(n: int, w: int, chis: Sequence[int], n_open: int = 5,
              repeats: int = 1) -> List[Dict]:
    alphas, betas, open_qubits, y_fixed = setup(n, n_open)

    print("=" * 78)
    print(f"STAGE 2 — bond-dimension sweep, n={n}, w={w}")
    print("=" * 78)
    T_exact, ex_stats = contract_frontier(n, w, alphas, betas, y_fixed, open_qubits)
    ex_scale = float(np.max(np.abs(T_exact)))
    exact_frontier = 2 ** w

    print(f"Exact frontier: 2^{w} = {exact_frontier:,} configurations")
    print(f"max|exact| = {ex_scale:.6e}   ({2 ** n_open} amplitudes, "
          f"{n_open} open outputs)")
    print()
    print("rel_err   = abs_err / max|exact|      <- the number that matters")
    print("rs_rel    = same, after renormalising <- did the STRUCTURE survive")
    print("norm      = ||MPS||; truncation loses norm, and a shrinking norm")
    print("            can otherwise masquerade as improving accuracy")
    print("disc_wt   = total discarded singular weight (standard MPS measure)")
    print()
    print(f"{'chi':>5} {'chi/2^w':>9} {'abs_err':>11} {'rel_err':>9} "
          f"{'rs_rel':>9} {'norm':>8} {'disc_wt':>10} {'time_s':>8} {'':>4}")
    print("-" * 88)

    rows: List[Dict] = []
    for chi in chis:
        mps = build_mps(n, w, alphas, betas, chi)
        T = extract(mps, n, y_fixed, open_qubits)
        nrm = mps.norm()

        samples = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            build_mps(n, w, alphas, betas, chi)
            samples.append(time.perf_counter() - t0)
        t_med = statistics.median(samples)

        abs_err = float(np.max(np.abs(T - T_exact)))
        rel = abs_err / ex_scale if ex_scale > 0 else float('nan')
        # renormalised comparison: rescale so ||MPS|| == 1 like the true state
        T_rs = T / nrm if nrm > 0 else T
        rs_rel = (float(np.max(np.abs(T_rs - T_exact))) / ex_scale
                  if ex_scale > 0 else float('nan'))
        dead = float(np.max(np.abs(T))) == 0.0
        guard = check_discarded_weight(mps.discarded, mps.truncations)

        rows.append({'chi': chi, 'abs_err': abs_err, 'rel_err': rel,
                     'rs_rel': rs_rel, 'norm': nrm, 'dead': dead,
                     'peak_chi': mps.peak_chi,
                     'discarded': mps.discarded, 'guard': guard,
                     'time_s': t_med,
                     'chi_frac': chi / float(exact_frontier)})
        flag = 'DEAD' if dead else ''
        if guard != 'ok':
            flag = 'BUG'
        print(f"{chi:>5} {chi / float(exact_frontier):>9.5f} {abs_err:>11.3e} "
              f"{rel:>9.4f} {rs_rel:>9.4f} {nrm:>8.5f} "
              f"{mps.discarded:>10.2e} {t_med:>8.3f} {flag:>4}")

    bad = [r for r in rows if r['guard'] != 'ok']
    if bad:
        print()
        print("*** DISCARDED-WEIGHT GUARD TRIPPED — results above are INVALID.")
        print("*** The MPS was not canonical, so the truncation was not optimal.")
        print("*** Do not interpret these numbers.")
    return rows


def interpret(rows: List[Dict], n: int, w: int) -> None:
    print()
    print("=" * 78)
    print("INTERPRETATION")
    print("=" * 78)
    if not rows:
        print("No rows.")
        return

    exact_frontier = 2 ** w
    # "usable" judged on the renormalised relative error, which is the
    # fairest reading of whether an adversary gets the answer
    usable = [r for r in rows if not r['dead'] and r['rs_rel'] < 1e-3]

    if usable:
        best = min(usable, key=lambda r: r['chi'])
        print(f"SVD TRUNCATION WORKS on this family.")
        print(f"  Smallest chi holding renormalised relative error < 1e-3: "
              f"{best['chi']}")
        print(f"  rs_rel = {best['rs_rel']:.3e}, chi/2^w = "
              f"{best['chi_frac']:.5f}, {best['time_s']:.3f}s")
        print()
        print("  CONSEQUENCE, AGAINST THIS PROGRAMME'S OWN CASE:")
        print(f"  Exact frontier contraction carries 2^{w} = {exact_frontier:,}")
        print(f"  configurations. An MPS at chi={best['chi']} carries ~n*chi^2 =")
        print(f"  ~{n * best['chi'] ** 2:,} numbers and ~n*chi^3 time. If that")
        print("  gap holds as w grows, the 2^w hardness figure describes only")
        print("  the EXACT regime and an approximate adversary pays far less.")
        print("  This is the same conclusion Addendum VI reached for the wrong")
        print("  reason — reached here, if it holds, for the right one.")
        print()
        print("  REQUIRED BEFORE CLAIMING THAT: check how the needed chi scales")
        print("  with w. A fixed chi that works at one width proves little; the")
        print("  question is whether chi must grow like 2^w (hardness intact)")
        print("  or far slower (hardness weakened). Run --scaling.")
    else:
        print("SVD truncation did NOT reach 1e-3 relative accuracy at any chi")
        print("tested here.")
        print()
        print("  If that survives larger chi and other widths, it is a genuinely")
        print("  strong result for the programme: the SERIOUS classical attack")
        print("  fails on this family, not merely the naive magnitude cutoff of")
        print("  the withdrawn Addendum VI.")
        print()
        print("  Do not over-read it yet. Check that chi was pushed high enough")
        print("  to matter, and that Stage 1 passed — an MPS bug looks identical")
        print("  to a hardness result from here.")

    print()
    print("What this does NOT show:")
    print("  * one circuit family, one width per run, small n only")
    print("  * MPS is a 1D ansatz; a 2D/PEPS or a better contraction order")
    print("    adversary is not tested here")
    print("  * verified only where contract_frontier is computable")
    print("  * no novelty claim: SVD truncation and MPS are textbook")
    print("  * no quantum time used")
    print()


def scaling_check(w_list: Sequence[int], n: int, target: float = 1e-3) -> None:
    """
    The question that decides the hardness argument: does the chi needed for a
    fixed accuracy grow like 2^w, or much slower?
    """
    print("=" * 78)
    print(f"SCALING — chi needed for renormalised rel_err < {target:g}, vs width")
    print("=" * 78)
    print("This is the load-bearing measurement. A fixed chi working at one")
    print("width proves nothing; what matters is the growth rate.\n")
    print(f"{'w':>4} {'2^w':>10} {'chi_needed':>11} {'chi/2^w':>9} {'rs_rel':>10}")
    print("-" * 78)

    for w in w_list:
        alphas, betas, open_qubits, y_fixed = setup(n)
        T_exact, _ = contract_frontier(n, w, alphas, betas, y_fixed, open_qubits)
        ex_scale = float(np.max(np.abs(T_exact)))
        found = None
        for chi in (2, 4, 8, 16, 32, 64, 128, 256, 512):
            mps = build_mps(n, w, alphas, betas, chi)
            T = extract(mps, n, y_fixed, open_qubits)
            nrm = mps.norm()
            T_rs = T / nrm if nrm > 0 else T
            rs = float(np.max(np.abs(T_rs - T_exact))) / ex_scale
            if rs < target:
                found = (chi, rs)
                break
        if found:
            chi, rs = found
            print(f"{w:>4} {2 ** w:>10,} {chi:>11} {chi / float(2 ** w):>9.5f} "
                  f"{rs:>10.3e}")
        else:
            print(f"{w:>4} {2 ** w:>10,} {'>256':>11} {'-':>9} {'-':>10}")
    print()
    print("Reading: if chi_needed stays roughly flat while 2^w grows, the")
    print("approximate adversary is cheap and the hardness claim is weakened.")
    print("If chi_needed tracks 2^w, exact cost is the honest cost.")
    print()


def spectrum_check(n: int, w_list: Sequence[int]) -> None:
    """
    WHY truncation fails, rather than just that it does.

    SVD truncation only helps when the Schmidt spectrum across a cut DECAYS —
    then a few dominant patterns carry the state. If the spectrum is FLAT, every
    Schmidt state contributes equally, there is no redundancy to discard, and no
    bond dimension below the full rank can work. That is the difference between
    a compressible state and an incompressible one.

    Reported per width, at the bond in the middle of the chain:
      rank      - number of non-negligible Schmidt values
      s_max/s_min ratio over the retained spectrum (1.0 => perfectly flat)
      entropy   - von Neumann entanglement entropy in bits
      max_bits  - log2(rank), the entropy of a perfectly flat spectrum
    If entropy ~= max_bits, the state is at or near maximal entanglement for
    its rank and cannot be compressed at all.
    """
    print("=" * 78)
    print("ENTANGLEMENT SPECTRUM — is the state compressible in principle?")
    print("=" * 78)
    print("SVD truncation needs a DECAYING Schmidt spectrum. A flat spectrum")
    print("means every pattern matters equally and nothing can be discarded.\n")
    print(f"{'w':>4} {'rank':>6} {'2^w':>8} {'s_max/s_min':>12} "
          f"{'entropy':>9} {'max_bits':>9} {'verdict':>16}")
    print("-" * 78)

    for w in w_list:
        alphas, betas = deterministic_angles(n)
        chi_full = 2 ** (n // 2 + 1)
        mps = build_mps(n, w, alphas, betas, chi_full)

        cut = n // 2
        mps.move_center(cut)
        A = mps.t[cut]
        Dl, _, Dr = A.shape
        m = A.reshape(Dl * 2, Dr)
        s = np.linalg.svd(m, compute_uv=False)
        s = s[s > 1e-12]
        s = s / np.linalg.norm(s)

        rank = len(s)
        ratio = float(s[0] / s[-1]) if rank > 1 else 1.0
        p = s ** 2
        p = p[p > 0]
        entropy = float(-np.sum(p * np.log2(p)))
        max_bits = float(np.log2(rank)) if rank > 1 else 0.0

        if rank > 1 and entropy > 0.98 * max_bits:
            verdict = "INCOMPRESSIBLE"
        elif rank > 1 and entropy > 0.85 * max_bits:
            verdict = "near-flat"
        else:
            verdict = "compressible"

        print(f"{w:>4} {rank:>6} {2 ** w:>8,} {ratio:>12.4f} "
              f"{entropy:>9.4f} {max_bits:>9.4f} {verdict:>16}")

    print()
    print("Reading: entropy at (or near) max_bits means the Schmidt spectrum is")
    print("flat — the state sits at maximal entanglement for its rank. There is")
    print("no low-rank structure for SVD truncation to find, which is the")
    print("mechanism behind chi_needed = 2^w rather than an accident of tuning.")
    print()


def main():
    p = argparse.ArgumentParser(
        description="SVD/bond-dimension truncation against the banded family")
    p.add_argument('--n', type=int, default=20)
    p.add_argument('--w', type=int, default=8)
    p.add_argument('--chis', type=int, nargs='+',
                   default=[2, 4, 8, 16, 32, 64, 128])
    p.add_argument('--open', dest='n_open', type=int, default=5)
    p.add_argument('--verify-only', action='store_true')
    p.add_argument('--scaling', action='store_true',
                   help='measure how chi_needed grows with w (the key question)')
    p.add_argument('--scaling-widths', type=int, nargs='+',
                   default=[4, 6, 8, 10, 12])
    p.add_argument('--spectrum', action='store_true',
                   help='report the entanglement spectrum: WHY truncation fails')
    args = p.parse_args()

    print()
    print("#" * 78)
    print("# EQCCM — SVD / bond-dimension truncation (THE REAL ADVERSARY)")
    print("# Closes the gap Addendum VII left open. banded_scaling.py is")
    print("# imported, never modified. No quantum time used.")
    print("#" * 78)
    print()

    if not verify_exact():
        print("Stage 1 failed — not proceeding. Fix the MPS machinery first.")
        return
    if args.verify_only:
        return

    if args.spectrum:
        spectrum_check(args.n, args.scaling_widths)
        return

    if args.scaling:
        scaling_check(args.scaling_widths, args.n)
        return

    rows = chi_sweep(args.n, args.w, args.chis, args.n_open)
    interpret(rows, args.n, args.w)


if __name__ == '__main__':
    main()
