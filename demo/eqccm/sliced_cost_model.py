"""
EQCCM — Sliced Contraction Cost: does the memory wall actually exist?
=====================================================================
banded_scaling.py measured T ~ 2^w and concluded memory was the binding
constraint (band 27 on a 32 GB machine, 37 exabytes at width 58). That
conclusion assumed DENSE UNSLICED contraction. It is wrong.

Slicing fixes a subset of indices and contracts each assignment separately.
Fixing k indices cuts peak memory by 2^k while total FLOPs rise only slightly.
A probe on a random 4-regular network measured:

    width 19 -> 12  (7 indices sliced, 128 slices)  FLOP overhead 1.08x

So memory can be traded away for ~8% extra compute. Two consequences:

  1. THERE IS NO MEMORY WALL. Any width is reachable given enough time.
     The only real cost is total FLOPs.
  2. SLICES ARE INDEPENDENT — embarrassingly parallel. A cluster attacks the
     problem with near-linear speedup. This is precisely how the classical
     rebuttals to Google's 53-qubit claim worked, taking an estimate from
     10,000 years down to days.

Therefore any hardness claim must be stated in TOTAL FLOPs against a realistic
adversary's throughput, not in width or single-machine memory.

This script recomputes the feasibility verdict on that honest basis.

No quantum time used.

Run:
    python demo/eqccm/sliced_cost_model.py

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import json
import math
import os
from typing import Dict, List, Sequence, Tuple

import networkx as nx

try:
    import cotengra as ctg
except ImportError:
    ctg = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
COUPLING_PATH = os.path.join(_REPO, "data", "fez_coupling.json")

SEED = 20260905

# Adversary models: (label, sustained FLOP/s for float64 tensor work)
ADVERSARIES = [
    ("laptop, 1 core", 5e9),
    ("workstation, 32 cores", 1.5e11),
    ("1x A100 GPU (fp64)", 1.0e13),
    ("1000-GPU cluster", 1.0e16),
]

# Memory budget to slice down to (elements, float64)
TARGET_ELEMS = 2 ** 27          # 1 GiB of float64

# Effective two-qubit error, back-fitted from the record's §9/§10 runs
EFF_ERR_LO = 0.005
EFF_ERR_HI = 0.010


def load_fez() -> nx.Graph:
    with open(COUPLING_PATH) as f:
        p = json.load(f)
    g = nx.Graph()
    g.add_nodes_from(range(p["n_qubits"]))
    g.add_edges_from(tuple(e) for e in p["edges"])
    return g


def matchings_of(g: nx.Graph) -> List[List[Tuple[int, int]]]:
    col = nx.coloring.greedy_color(nx.line_graph(g), strategy="largest_first")
    by: Dict[int, List[Tuple[int, int]]] = {}
    for e, c in col.items():
        by.setdefault(c, []).append(tuple(sorted(e)))
    return [by[c] for c in sorted(by, key=lambda c: -len(by[c]))]


def build_network(qubits: Sequence[int],
                  layers: Sequence[Sequence[Tuple[int, int]]],
                  n_open: int):
    qs = list(qubits)
    qset = set(qs)
    d = len(layers)
    inputs: List[Tuple[str, ...]] = []

    def x(k, q):
        return f"x{k}_{q}"

    for q in qs:
        inputs.append((x(1, q),))
    for k, layer in enumerate(layers, start=1):
        for (i, j) in layer:
            if i in qset and j in qset:
                inputs.append((x(k, i), x(k, j)))
        if k < d:
            for q in qs:
                inputs.append((x(k, q), x(k + 1, q)))
    open_q = qs[:n_open]
    for q in qs:
        inputs.append((f"y_{q}", x(d, q)) if q in open_q else (x(d, q),))

    output = tuple(f"y_{q}" for q in open_q)
    sd = {ix: 2 for t in inputs for ix in t}
    for ix in output:
        sd[ix] = 2
    return inputs, output, sd


def fmt_time(s: float) -> str:
    if s < 1e-3:
        return f"{s * 1e6:.0f} us"
    if s < 1:
        return f"{s * 1e3:.0f} ms"
    if s < 90:
        return f"{s:.1f} s"
    if s < 5400:
        return f"{s / 60:.1f} min"
    if s < 172800:
        return f"{s / 3600:.1f} hr"
    if s < 3.15e9:
        return f"{s / 86400:.0f} days"
    return f"{s / 3.156e7:.2g} yr"


def fmt_flops(c: float) -> str:
    for u, d in (("Z", 1e21), ("E", 1e18), ("P", 1e15),
                 ("T", 1e12), ("G", 1e9), ("M", 1e6)):
        if c >= d:
            return f"{c / d:.2f}{u}"
    return f"{c:.0f}"


def analyse_case(label: str, g: nx.Graph, depth: int, n_open: int = 3) -> dict:
    ms = matchings_of(g)
    layers = [ms[k % len(ms)] for k in range(depth)]
    gates = sum(len(m) for m in layers)
    qubits = sorted(g.nodes())

    inputs, output, sd = build_network(qubits, layers, n_open)
    tree = ctg.array_contract_tree(inputs, output, sd, optimize="greedy")

    w_unsliced = float(tree.contraction_width())
    c_unsliced = float(tree.contraction_cost())

    sliced = tree.copy()
    try:
        sliced.slice_(target_size=TARGET_ELEMS)
    except Exception:
        pass

    return {
        "label": label,
        "depth": depth,
        "gates": gates,
        "width_unsliced": w_unsliced,
        "mem_unsliced_bytes": (2.0 ** w_unsliced) * 8,
        "cost_unsliced": c_unsliced,
        "width_sliced": float(sliced.contraction_width()),
        "nslices": int(sliced.nslices),
        "cost_sliced": float(sliced.contraction_cost()),
        "overhead": (float(sliced.contraction_cost()) / c_unsliced
                     if c_unsliced else 1.0),
        "f_lo": (1 - EFF_ERR_HI) ** gates,   # pessimistic error -> low fidelity
        "f_hi": (1 - EFF_ERR_LO) ** gates,
    }


def main():
    if ctg is None:
        raise SystemExit("cotengra not installed.")

    print()
    print("#" * 96)
    print("# EQCCM — sliced contraction cost: restating hardness in FLOPs")
    print("#" * 96)
    print()

    fez = load_fez()
    n = 100

    # Matched-size patch of the real device
    from collections import deque
    seen, q = {0}, deque([0])
    while q and len(seen) < n:
        u = q.popleft()
        for v in fez.neighbors(u):
            if v not in seen:
                seen.add(v)
                q.append(v)
                if len(seen) >= n:
                    break
    fez_patch = nx.convert_node_labels_to_integers(fez.subgraph(seen).copy())

    cases = [
        ("heavy_hex_fez d=6", fez_patch, 6),
        ("heavy_hex_fez d=12", fez_patch, 12),
        ("heavy_hex_fez d=18", fez_patch, 18),
        ("random_4_regular d=6", nx.random_regular_graph(4, n, seed=SEED), 6),
        ("random_4_regular d=10", nx.random_regular_graph(4, n, seed=SEED), 10),
        ("degree_8 d=6", nx.random_regular_graph(8, n, seed=SEED), 6),
        ("degree_8 d=10", nx.random_regular_graph(8, n, seed=SEED), 10),
    ]

    results = []
    for label, g, d in cases:
        print(f"  analysing {label} ...")
        try:
            results.append(analyse_case(label, g, d))
        except Exception as e:
            print(f"    failed: {e}")

    print()
    print("=" * 96)
    print("SLICING: MEMORY IS NOT THE CONSTRAINT")
    print("=" * 96)
    print(f"Sliced down to {TARGET_ELEMS * 8 / 1e9:.1f} GB peak "
          f"({TARGET_ELEMS:,} float64 elements)\n")
    print(f"{'case':>22} {'gates':>6} {'w_un':>5} {'mem_un':>10} "
          f"{'w_sl':>5} {'slices':>8} {'FLOPs':>9} {'ovh':>6}")
    print("-" * 96)
    for r in results:
        mem = r["mem_unsliced_bytes"]
        mem_s = (f"{mem / 1e18:.1f}EB" if mem >= 1e18 else
                 f"{mem / 1e12:.1f}TB" if mem >= 1e12 else
                 f"{mem / 1e9:.1f}GB" if mem >= 1e9 else
                 f"{mem / 1e6:.0f}MB")
        print(f"{r['label']:>22} {r['gates']:>6} {r['width_unsliced']:>5.0f} "
              f"{mem_s:>10} {r['width_sliced']:>5.0f} {r['nslices']:>8,} "
              f"{fmt_flops(r['cost_sliced']):>9} {r['overhead']:>6.2f}x")

    print()
    print("=" * 96)
    print("WALL-CLOCK vs ADVERSARY  (sliced, embarrassingly parallel)")
    print("=" * 96)
    hdr = f"{'case':>22}" + "".join(f"{lab.split(',')[0][:11]:>13}"
                                    for lab, _ in ADVERSARIES)
    print(hdr)
    print("-" * 96)
    for r in results:
        row = f"{r['label']:>22}"
        for _, fl in ADVERSARIES:
            row += f"{fmt_time(r['cost_sliced'] / fl):>13}"
        print(row)

    print()
    print("=" * 96)
    print("FEASIBILITY: classically expensive AND hardware-executable?")
    print("=" * 96)
    print("'Expensive' = >30 days on a 1000-GPU cluster (a serious adversary).")
    print("'Executable' = predicted fidelity >= 0.05 at back-fitted error.\n")
    print(f"{'case':>22} {'cluster time':>14} {'F(0.5%)':>9} {'F(1.0%)':>9}  verdict")
    print("-" * 96)

    CLUSTER = ADVERSARIES[-1][1]
    THIRTY_DAYS = 30 * 86400
    winners = []
    for r in results:
        t = r["cost_sliced"] / CLUSTER
        hard = t >= THIRTY_DAYS
        live = r["f_lo"] >= 0.05
        verdict = ("BOTH — candidate" if hard and live else
                   "hard, no signal" if hard else
                   "signal, too easy" if live else "neither")
        if hard and live:
            winners.append(r)
        print(f"{r['label']:>22} {fmt_time(t):>14} "
              f"{r['f_hi']:>9.3f} {r['f_lo']:>9.3f}  {verdict}")

    print()
    print("=" * 96)
    print("INTERPRETATION")
    print("=" * 96)
    ovh = [r["overhead"] for r in results if r["overhead"] > 0]
    if ovh:
        print(f"Slicing overhead across all cases: "
              f"{min(ovh):.2f}x to {max(ovh):.2f}x FLOPs.")
        print("Memory therefore costs almost nothing to eliminate. The 'memory")
        print("wall at band 27' from the banded study was an artifact of dense")
        print("unsliced contraction and should be retracted.\n")

    if winners:
        print(f"{len(winners)} case(s) are both classically expensive and")
        print("hardware-executable:")
        for r in winners:
            print(f"  {r['label']}: {r['gates']} gates, "
                  f"width {r['width_unsliced']:.0f}, "
                  f"{fmt_flops(r['cost_sliced'])} FLOPs, "
                  f"F={r['f_lo']:.3f}-{r['f_hi']:.3f}")
    else:
        print("NO case is both. Against a 1000-GPU adversary every circuit")
        print("that the hardware can still execute is classically cheap.")
        print("Stated plainly: at this scale, a serious classical opponent wins")
        print("on every executable circuit tested — which is the honest")
        print("position, and matches how the Sycamore claims were answered.")

    print()
    print("Caveats:")
    print("  * cotengra 'greedy' is a weak optimiser; better presets and")
    print("    hyper-optimisation lower FLOPs further, favouring the classical")
    print("    side even more than shown here")
    print("  * FLOP counts are cotengra's scalar-op counts; real throughput")
    print("    depends on reaching peak BLAS efficiency, rarely achieved")
    print("  * fidelity ignores idle decoherence, crosstalk and readout, so it")
    print("    is an upper bound — real signal is worse")
    print("  * no quantum time was used")
    print()


if __name__ == "__main__":
    main()
