"""
EQCCM — Can the 4.1x nominal-to-effective error gap be closed? (§37)
====================================================================
§35 measured effective two-qubit error on ibm_fez at 0.845%, which is 4.1x the
device's own nominal best-quartile figure of 0.204%. §37 argued that gap is
crosstalk, idle decoherence and readout — NOT gate quality — and is therefore
addressable with known tools rather than new hardware.

This tests that claim directly.

WHY IT MATTERS (from §36)
For the degree-8 depth-10 candidate (395 gates, contraction width 108):
    eps = 0.845% (measured today)  ->  F = 0.035   ~8.2M shots
    eps = 0.500%                   ->  F = 0.137   ~530k shots
    eps = 0.300%                   ->  F = 0.306   ~107k shots
    eps = 0.204% (nominal)         ->  F = 0.446   ~50k shots
So closing the gap converts a marginal 8-million-shot experiment into a routine
one. It is the highest-value intervention available without new hardware.

METHOD
Re-run the EXACT circuits from §33 — same 20-qubit patch, same random seed, so
the same RY angles — but with the error-suppression stack enabled:

  * DYNAMICAL DECOUPLING: pulse sequences on idle qubits. Attacks the idle
    decoherence component, which the §33 run had no protection against.
  * GATE TWIRLING (Pauli): converts coherent/systematic gate error into
    stochastic error. Coherent errors can accumulate quadratically with depth;
    stochastic ones accumulate linearly, so twirling helps most at high gate
    count — exactly our regime.
  * MEASUREMENT TWIRLING: randomises readout bit assignment, converting
    correlated readout bias into unbiased noise. Attacks the SPAM floor A.

Then fit the same two-parameter model as §34 and compare:

    P(0...0) = A * (1 - eps)^G

A drop in eps means the gap was suppressible. A drop in A alone means only
readout improved, which helps small circuits but not the gate-count scaling
that decides §36.

BASELINE comes from data/eqccm_error_vs_depth.json (job dadm3mjdd5gc73d7gvjg),
so only ONE new job is needed and the comparison is like-for-like.

Safe by default — nothing submitted without --submit.

Run:
    python demo/eqccm/error_suppression_test.py            # dry run
    python demo/eqccm/error_suppression_test.py --submit   # ~20k shots

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
import json
import math
import os
from typing import Dict, List, Sequence, Tuple

import networkx as nx
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
COUPLING_PATH = os.path.join(_REPO, "data", "fez_coupling.json")
BASELINE_PATH = os.path.join(_REPO, "data", "eqccm_error_vs_depth.json")
RESULT_PATH = os.path.join(_REPO, "data", "eqccm_error_suppressed.json")

SEED = 20260905  # MUST match error_vs_depth.py for identical circuits


def load_device() -> Tuple[nx.Graph, Dict[Tuple[int, int], float]]:
    with open(COUPLING_PATH) as f:
        payload = json.load(f)
    g = nx.Graph()
    g.add_nodes_from(range(payload["n_qubits"]))
    g.add_edges_from(tuple(e) for e in payload["edges"])
    errs = {}
    for key, val in payload.get("two_qubit_errors", {}).items():
        try:
            a, b = key.split(":")[1].split("_")
            errs[tuple(sorted((int(a), int(b))))] = float(val)
        except Exception:
            continue
    return g, errs


def patch_matchings(g: nx.Graph, qubits: Sequence[int]) -> List[List[Tuple[int, int]]]:
    sub = g.subgraph(qubits)
    col = nx.coloring.greedy_color(nx.line_graph(sub), strategy="largest_first")
    by: Dict[int, List[Tuple[int, int]]] = {}
    for e, c in col.items():
        by.setdefault(c, []).append(tuple(sorted(e)))
    return [by[c] for c in sorted(by, key=lambda c: -len(by[c]))]


def build_mirror(qubits, matchings, depth, rng):
    """Identical construction to error_vs_depth.py — do not change."""
    from qiskit import QuantumCircuit
    qs = list(qubits)
    idx = {q: i for i, q in enumerate(qs)}
    qc = QuantumCircuit(len(qs), len(qs))
    layers = [matchings[k % len(matchings)] for k in range(depth)]
    angles = [rng.uniform(0.15, math.pi - 0.15, size=len(qs)) for _ in range(depth)]

    gates = 0
    for k, layer in enumerate(layers):
        for i, q in enumerate(qs):
            qc.ry(angles[k][i], idx[q])
        for (a, b) in layer:
            qc.cz(idx[a], idx[b]); gates += 1
        qc.barrier()
    for k in reversed(range(len(layers))):
        for (a, b) in reversed(layers[k]):
            qc.cz(idx[a], idx[b]); gates += 1
        for i, q in enumerate(qs):
            qc.ry(-angles[k][i], idx[q])
        qc.barrier()
    qc.measure(range(len(qs)), range(len(qs)))
    return qc, gates


def fit(G: np.ndarray, P: np.ndarray) -> Tuple[float, float]:
    """P = A (1-eps)^G  ->  returns (A, eps)."""
    slope, intercept = np.polyfit(G, np.log(P), 1)
    return math.exp(intercept), 1.0 - math.exp(slope)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--shots", type=int, default=4096)
    p.add_argument("--backend", default="ibm_fez")
    p.add_argument("--submit", action="store_true")
    args = p.parse_args()

    print()
    print("#" * 80)
    print("# EQCCM §37 — does error suppression close the 4.1x gap?")
    print("#" * 80)
    print()

    if not os.path.exists(BASELINE_PATH):
        raise SystemExit(f"Need baseline {BASELINE_PATH} (run error_vs_depth.py --submit)")
    with open(BASELINE_PATH) as f:
        base = json.load(f)

    qubits = base["qubits"]
    depths = [pt["depth"] for pt in base["points"]]
    g, _ = load_device()
    ms = patch_matchings(g, qubits)

    bG = np.array([pt.get("transpiled_2q") or pt["two_qubit_gates"]
                   for pt in base["points"]], dtype=float)
    bP = np.array([pt["p_zero"] for pt in base["points"]], dtype=float)
    A0, eps0 = fit(bG, bP)

    print(f"BASELINE (job {base.get('job_id','?')}, no suppression):")
    print(f"  A = {A0:.4f}   eps = {eps0:.3%}")
    print(f"  patch: {len(qubits)} qubits, depths {depths}\n")

    rng = np.random.default_rng(SEED)
    circuits, meta = [], []
    for d in depths:
        qc, gates = build_mirror(qubits, ms, d, rng)
        circuits.append(qc)
        meta.append({"depth": d, "two_qubit_gates": gates})

    print("Error-suppression stack to apply:")
    print("  dynamical decoupling  XpXm on idle qubits  -> idle decoherence")
    print("  Pauli gate twirling   32 randomizations    -> coherent gate error")
    print("  measurement twirling                       -> correlated readout")
    print(f"\nCost: {len(circuits)} circuits x {args.shots} shots "
          f"= {args.shots * len(circuits):,} shots (one job)")

    if not args.submit:
        print("\nDRY RUN — nothing submitted. To execute:")
        print("    python demo\\eqccm\\error_suppression_test.py --submit")
        print("\nOutcomes:")
        print("  eps DROPS      -> §37 confirmed; the gap is suppressible and")
        print("                    the §36 candidates get much cheaper")
        print("  only A drops   -> readout improved but gate scaling unchanged;")
        print("                    helps small circuits, not the §36 arithmetic")
        print("  nothing moves  -> the 0.845% is intrinsic gate error after all,")
        print("                    and §37's premise was wrong")
        return

    from qiskit import transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService()
    backend = service.backend(args.backend)
    print(f"\nSubmitting to {backend.name} ...")

    tqcs = [transpile(qc, backend=backend, initial_layout=qubits,
                      optimization_level=1) for qc in circuits]
    for m, tqc in zip(meta, tqcs):
        ops = tqc.count_ops()
        m["transpiled_2q"] = sum(v for k, v in ops.items()
                                 if k in ("cz", "ecr", "cx", "rzz"))

    sampler = SamplerV2(mode=backend)
    applied = []
    try:
        sampler.options.dynamical_decoupling.enable = True
        sampler.options.dynamical_decoupling.sequence_type = "XpXm"
        applied.append("dynamical_decoupling=XpXm")
    except Exception as e:
        print(f"  (DD unavailable: {e})")
    try:
        sampler.options.twirling.enable_gates = True
        sampler.options.twirling.enable_measure = True
        sampler.options.twirling.num_randomizations = 32
        applied.append("twirling(gates+measure, 32)")
    except Exception as e:
        print(f"  (twirling unavailable: {e})")
    print(f"  applied: {', '.join(applied) if applied else 'NOTHING'}")

    job = sampler.run(tqcs, shots=args.shots)
    print(f"Job ID: {job.job_id()}")
    res = job.result()

    zero = "0" * len(qubits)
    for m, r in zip(meta, res):
        counts = r.data.c.get_counts()
        p0 = counts.get(zero, 0) / args.shots
        m["p_zero"] = p0
        m["shot_err"] = math.sqrt(max(p0, 1e-12) * (1 - p0) / args.shots)

    nG = np.array([m["transpiled_2q"] or m["two_qubit_gates"] for m in meta], float)
    nP = np.array([m["p_zero"] for m in meta], float)
    ok = nP > 0
    A1, eps1 = fit(nG[ok], nP[ok])

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"{'2q gates':>9} {'P base':>9} {'P suppr':>9} {'change':>9}")
    print("-" * 80)
    for gg, pb, m in zip(bG, bP, meta):
        pn = m["p_zero"]
        print(f"{gg:>9.0f} {pb:>9.4f} {pn:>9.4f} "
              f"{(pn - pb) / max(pb, 1e-9):>+8.1%}")

    print()
    print(f"{'':>22}{'baseline':>12}{'suppressed':>12}{'change':>12}")
    print("-" * 80)
    print(f"{'SPAM floor A':>22}{A0:>12.4f}{A1:>12.4f}"
          f"{(A1 - A0) / A0:>+11.1%}")
    print(f"{'2q error eps':>22}{eps0:>11.3%}{eps1:>12.3%}"
          f"{(eps1 - eps0) / eps0:>+11.1%}")

    nominal = 0.00204
    print()
    print("=" * 80)
    print("VERDICT ON §37")
    print("=" * 80)
    print(f"eps: {eps0:.3%} -> {eps1:.3%}   "
          f"(nominal best-quartile is {nominal:.3%})")
    print(f"gap to nominal: {eps0 / nominal:.1f}x -> {eps1 / nominal:.1f}x\n")

    if eps1 < eps0 * 0.85:
        print("CONFIRMED — suppression materially reduced per-gate error.")
        print("The gap is not intrinsic gate quality. Repricing §36:")
        for name, gates in (("degree_8 d=6", 269), ("degree_8 d=10", 395)):
            f_old = (1 - eps0) ** gates
            f_new = (1 - eps1) ** gates
            print(f"  {name:>16} ({gates} gates): F {f_old:.4f} -> {f_new:.4f}, "
                  f"shots {10_000 / max(f_old,1e-9)**2:,.0f} -> "
                  f"{10_000 / max(f_new,1e-9)**2:,.0f}")
    elif A1 > A0 * 1.05:
        print("PARTIAL — the SPAM floor improved but per-gate error did not.")
        print("That helps shallow circuits, but §36's arithmetic is driven by")
        print("the gate-count exponent, so the candidates do not get cheaper.")
    else:
        print("NOT CONFIRMED — suppression did not move either parameter")
        print("materially. On this evidence the 0.845% is closer to intrinsic")
        print("gate error than §37 assumed, and the remaining path is better")
        print("hardware rather than better control.")

    with open(RESULT_PATH, "w") as f:
        json.dump({"backend": args.backend, "qubits": qubits,
                   "shots": args.shots, "job_id": job.job_id(),
                   "applied": applied, "points": meta,
                   "fit": {"A": A1, "eps": eps1},
                   "baseline_fit": {"A": A0, "eps": eps0}}, f, indent=2)
    print(f"\nSaved {RESULT_PATH}")


if __name__ == "__main__":
    main()
