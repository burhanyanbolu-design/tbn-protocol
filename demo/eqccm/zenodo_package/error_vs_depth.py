"""
EQCCM — Effective Two-Qubit Error vs Gate Count (mirror benchmarking)
=====================================================================
Measures THE decisive unknown from §31: does effective per-gate error stay
near 0.5% as gate count grows into the hundreds, or does it degrade?

WHY THIS MATTERS
§30/§31 showed the whole programme reduces to this one number:
  * at 0.5% effective error, degree-8 / random-4-regular circuits at depth 10
    (~400 gates) are BOTH classically intractable AND hardware-executable
  * at 1.0%, fidelity falls to ~0.02 and there is no experiment
§24's back-fit from the record's own runs shows error GROWING with depth
(0.48% per gate at 15 gates, 0.96% at 30). If that trend continues to 400
gates the programme is dead. If it flattens, it is alive. Two data points
cannot distinguish a trend from noise, so this measures five.

WHY MIRROR CIRCUITS RATHER THAN EXPECTATION VALUES
The record compared <P> against exact simulation. That has two problems, both
visible in §10: small ideal values inflate relative error (X0X1 had ideal
0.0267 against a +/-0.01 shot-noise floor, so its "57% error" was mostly
sampling), and it needs exact simulation, which caps the circuit size.

A mirror circuit applies U then U-dagger. The ideal output is exactly |0...0>
with probability 1. So:
  * no classical simulation is required at any size
  * the signal is maximal, so shot noise is minimal
  * P(all zeros) is a direct fidelity proxy

Randomised RY angles are inserted between entangling layers so that coherent
errors do not systematically cancel in the mirror — without this, mirror
circuits flatter the device.

MODEL FITTED
    P(0...0) ~ (1 - eps_eff) ^ G      G = total two-qubit gate count
so eps_eff = 1 - P^(1/G). If eps_eff is flat in G, error is gate-local. If it
rises with G, depth-dependent mechanisms (crosstalk, idle decoherence) dominate
and extrapolation to 400 gates is unsafe.

QUANTUM TIME: five small circuits. Native edges only, so no SWAP routing.
Default 4096 shots each — well under a minute of QPU time. It is SAFE BY
DEFAULT: nothing is submitted without --submit.

Run:
    python demo/eqccm/error_vs_depth.py               # build + cost, no submit
    python demo/eqccm/error_vs_depth.py --submit      # actually run on Fez

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
RESULT_PATH = os.path.join(_REPO, "data", "eqccm_error_vs_depth.json")

SEED = 20260905


# ══════════════════════════════════════════════════════════════════
# PICK THE BEST-CALIBRATED CONNECTED PATCH
# ══════════════════════════════════════════════════════════════════

def load_device() -> Tuple[nx.Graph, Dict[Tuple[int, int], float]]:
    if not os.path.exists(COUPLING_PATH):
        raise SystemExit(f"Missing {COUPLING_PATH}\n"
                         "Run: python demo/eqccm/fetch_fez_topology.py")
    with open(COUPLING_PATH) as f:
        payload = json.load(f)

    g = nx.Graph()
    g.add_nodes_from(range(payload["n_qubits"]))
    g.add_edges_from(tuple(e) for e in payload["edges"])

    # keys look like "cz:12_13" from fetch_fez_topology.py
    errs: Dict[Tuple[int, int], float] = {}
    for key, val in payload.get("two_qubit_errors", {}).items():
        try:
            pair = key.split(":")[1]
            a, b = pair.split("_")
            errs[tuple(sorted((int(a), int(b))))] = float(val)
        except Exception:
            continue
    return g, errs


def best_patch(g: nx.Graph, errs: Dict[Tuple[int, int], float],
               size: int) -> List[int]:
    """
    Grow a connected patch that keeps mean edge error low. Greedy: start from
    the lowest-error edge, then repeatedly add the neighbour reachable by the
    cheapest edge. This is what "pick good qubits" means in practice.
    """
    if not errs:
        return sorted(list(g.nodes())[:size])

    seed_edge = min(errs, key=errs.get)
    chosen = {seed_edge[0], seed_edge[1]}

    while len(chosen) < size:
        best, best_err = None, float("inf")
        for u in chosen:
            for v in g.neighbors(u):
                if v in chosen:
                    continue
                e = errs.get(tuple(sorted((u, v))), 1.0)
                if e < best_err:
                    best, best_err = v, e
        if best is None:
            break
        chosen.add(best)
    return sorted(chosen)


def patch_matchings(g: nx.Graph, qubits: Sequence[int]
                    ) -> List[List[Tuple[int, int]]]:
    sub = g.subgraph(qubits)
    if sub.number_of_edges() == 0:
        raise SystemExit("Chosen patch has no edges.")
    col = nx.coloring.greedy_color(nx.line_graph(sub), strategy="largest_first")
    by: Dict[int, List[Tuple[int, int]]] = {}
    for e, c in col.items():
        by.setdefault(c, []).append(tuple(sorted(e)))
    return [by[c] for c in sorted(by, key=lambda c: -len(by[c]))]


# ══════════════════════════════════════════════════════════════════
# MIRROR CIRCUIT
# ══════════════════════════════════════════════════════════════════

def build_mirror(qubits: Sequence[int],
                 matchings: List[List[Tuple[int, int]]],
                 depth: int, rng: np.random.Generator):
    """
    U then U-dagger, with randomised RY angles between entangling layers.
    Ideal output is |0...0> exactly. Returns (circuit, two_qubit_gate_count).
    """
    from qiskit import QuantumCircuit

    qs = list(qubits)
    index = {q: i for i, q in enumerate(qs)}
    qc = QuantumCircuit(len(qs), len(qs))

    layers = [matchings[k % len(matchings)] for k in range(depth)]
    angles = [rng.uniform(0.15, math.pi - 0.15, size=len(qs))
              for _ in range(depth)]

    gates = 0
    # ── forward ──
    for k, layer in enumerate(layers):
        for i, q in enumerate(qs):
            qc.ry(angles[k][i], index[q])
        for (a, b) in layer:
            qc.cz(index[a], index[b])
            gates += 1
        qc.barrier()

    # ── inverse: undo in reverse order ──
    for k in reversed(range(len(layers))):
        for (a, b) in reversed(layers[k]):
            qc.cz(index[a], index[b])   # CZ is self-inverse
            gates += 1
        for i, q in enumerate(qs):
            qc.ry(-angles[k][i], index[q])
        qc.barrier()

    qc.measure(range(len(qs)), range(len(qs)))
    return qc, gates


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--qubits", type=int, default=20,
                   help="patch size (default 20; keeps QPU time small)")
    p.add_argument("--depths", type=int, nargs="+", default=[1, 2, 4, 8, 16])
    p.add_argument("--shots", type=int, default=4096)
    p.add_argument("--backend", default="ibm_fez")
    p.add_argument("--submit", action="store_true",
                   help="actually run on hardware (spends QPU quota)")
    args = p.parse_args()

    print()
    print("#" * 84)
    print("# EQCCM — effective two-qubit error vs gate count (mirror benchmark)")
    print("# Tests §31: does eps_eff stay ~0.5% at high gate count, or grow?")
    print("#" * 84)
    print()

    g, errs = load_device()
    qubits = best_patch(g, errs, args.qubits)
    ms = patch_matchings(g, qubits)

    sub = g.subgraph(qubits)
    patch_errs = [errs.get(tuple(sorted(e)), float("nan")) for e in sub.edges()]
    patch_errs = [e for e in patch_errs if not math.isnan(e)]

    print(f"Patch: {len(qubits)} qubits, {sub.number_of_edges()} edges, "
          f"{len(ms)} matchings {[len(m) for m in ms]}")
    print(f"Qubits: {qubits}")
    if patch_errs:
        print(f"Patch two-qubit error: mean {np.mean(patch_errs):.3%}, "
              f"max {np.max(patch_errs):.3%}")
        print(f"(device-wide median is 0.278%, best-quartile 0.204%)")
    print()

    rng = np.random.default_rng(SEED)
    circuits, meta = [], []
    for d in args.depths:
        qc, gates = build_mirror(qubits, ms, d, rng)
        circuits.append(qc)
        meta.append({"depth": d, "two_qubit_gates": gates})

    print(f"{'depth':>6} {'2q gates':>9} {'circuit depth':>14} "
          f"{'predicted P@0.5%':>17} {'@1.0%':>8}")
    print("-" * 62)
    for qc, m in zip(circuits, meta):
        gt = m["two_qubit_gates"]
        print(f"{m['depth']:>6} {gt:>9} {qc.depth():>14} "
              f"{(1 - 0.005) ** gt:>17.3f} {(1 - 0.010) ** gt:>8.3f}")

    total_shots = args.shots * len(circuits)
    print(f"\nTotal: {len(circuits)} circuits x {args.shots} shots "
          f"= {total_shots:,} shots. Native edges only, so no SWAP routing.")

    if not args.submit:
        print("\nDRY RUN — nothing submitted. Re-run with --submit to execute:")
        print(f"    python demo\\eqccm\\error_vs_depth.py --submit")
        print("\nWhat the result will tell you:")
        print("  eps_eff FLAT in gate count  -> error is gate-local; the §30")
        print("     degree-8 depth-10 candidate is live at ~400 gates")
        print("  eps_eff RISING in gate count -> depth-dependent mechanisms")
        print("     dominate; extrapolation to 400 gates is unsafe and the")
        print("     advantage regime is out of reach on this hardware class")
        return

    # ── submit ────────────────────────────────────────────────────
    from qiskit import transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService()
    backend = service.backend(args.backend)
    print(f"\nSubmitting to {backend.name} ...")

    tqcs = [transpile(qc, backend=backend, initial_layout=qubits,
                      optimization_level=1) for qc in circuits]
    for m, tqc in zip(meta, tqcs):
        m["transpiled_depth"] = tqc.depth()
        ops = tqc.count_ops()
        m["transpiled_2q"] = sum(v for k, v in ops.items()
                                 if k in ("cz", "ecr", "cx", "rzz"))

    sampler = SamplerV2(mode=backend)
    job = sampler.run(tqcs, shots=args.shots)
    print(f"Job ID: {job.job_id()}")
    res = job.result()

    print()
    print("=" * 84)
    print("RESULT — effective per-gate error vs gate count")
    print("=" * 84)
    print(f"{'depth':>6} {'2q gates':>9} {'P(0...0)':>10} "
          f"{'eps_eff':>9} {'shot err':>9}")
    print("-" * 84)

    zero_key = "0" * len(qubits)
    for m, r in zip(meta, res):
        counts = r.data.c.get_counts()
        p0 = counts.get(zero_key, 0) / args.shots
        gt = m["transpiled_2q"] or m["two_qubit_gates"]
        eps = 1 - p0 ** (1.0 / gt) if p0 > 0 else float("nan")
        shot_err = math.sqrt(max(p0, 1e-12) * (1 - p0) / args.shots)
        m.update({"p_zero": p0, "eps_eff": eps, "shot_err": shot_err})
        print(f"{m['depth']:>6} {gt:>9} {p0:>10.4f} "
              f"{eps:>9.3%} {shot_err:>9.4f}")

    valid = [m for m in meta if m.get("eps_eff") and
             not math.isnan(m["eps_eff"]) and m["p_zero"] > 3 * m["shot_err"]]

    print()
    print("=" * 84)
    print("VERDICT")
    print("=" * 84)
    if len(valid) >= 3:
        gates = np.array([m["transpiled_2q"] or m["two_qubit_gates"]
                          for m in valid], dtype=float)
        eps = np.array([m["eps_eff"] for m in valid], dtype=float)
        slope, intercept = np.polyfit(np.log(gates), eps, 1)
        print(f"eps_eff at fewest gates ({gates[0]:.0f}): {eps[0]:.3%}")
        print(f"eps_eff at most gates   ({gates[-1]:.0f}): {eps[-1]:.3%}")
        print(f"trend: {slope:+.4%} per e-fold in gate count\n")

        if abs(slope) < 0.001:
            print("FLAT — error is gate-local. Extrapolation to ~400 gates is")
            print("  justified. The §30 degree-8 depth-10 candidate stays live,")
            print("  subject to obtaining degree>=4 non-planar connectivity.")
        elif slope > 0:
            eps400 = intercept + slope * math.log(400)
            print(f"RISING — projected eps_eff at 400 gates: {eps400:.3%}")
            if eps400 > 0.01:
                print("  Above 1%. §31's pessimistic column applies and the")
                print("  advantage regime is out of reach for this hardware")
                print("  class. This is the falsification the record asked for.")
            else:
                print("  Still under 1%. Marginal but not fatal.")
        else:
            print("FALLING — error improves with depth, which is unphysical.")
            print("  Suspect coherent-error cancellation in the mirror despite")
            print("  angle randomisation. Re-run with fresh random angles.")
    else:
        print("Too few usable points — deeper circuits decayed into the shot")
        print("noise floor. Reduce --depths or raise --shots.")

    with open(RESULT_PATH, "w") as f:
        json.dump({"backend": args.backend, "qubits": qubits,
                   "shots": args.shots, "job_id": job.job_id(),
                   "points": meta}, f, indent=2)
    print(f"\nSaved {RESULT_PATH}")


if __name__ == "__main__":
    main()
