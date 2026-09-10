"""
EQCCM — Heavy-Hex Layer Depth vs Optimised Contraction Width
=============================================================
Answers the question the banded scaling result left open.

WHERE THIS SITS
`banded_scaling.py` established the classical cost law empirically:
    T(w) ~ 2^w,  measured exponent 1.984 over ten doublings (n=30, band 12-22)
    anchor: width 22 -> 14.42 s, 537 MB peak
That closed §19's classical question. But banded graphs need degree ~2w and
heavy-hex is degree 3, so they are NOT executable on Fez. The remaining
question is therefore:

    what optimised contraction width is reachable in a circuit that IS
    heavy-hex-native, within a two-qubit gate budget where the hardware
    still returns usable signal?

MULTI-LAYER CIRCUIT FAMILY (§3 extended to depth d)
    |psi> = RY^(d+1) [CZ layer d] ... RY^(2) [CZ layer 1] RY^(1) |0>^n

A single CZ layer gives contraction width bounded by the interaction graph's
treewidth, which for a planar degree-3 lattice is O(sqrt(n)) — trivially
contractible. Width is bought by DEPTH, because the amplitude's tensor
network extends in time as well as space:

    variables x^(1) .. x^(d), one bitstring per layer boundary
    "space" factors  (-1)^{x^k_i x^k_j}   for each edge in layer k
    "time"  factors  <x^{k+1}_i| RY |x^k_i>  linking a qubit across layers

Each CZ layer is chosen as a MATCHING (no shared qubits) so it executes in
one physical timestep. Heavy-hex is degree 3, so Vizing gives an edge
colouring in 3-4 matchings; each colour class is one layer.

WHY COTENGRA AND NOT OUR OWN ORDERING
§13 is the cautionary case: a graph with custom frontier width 7 was
optimised by Quimb/Cotengra to actual contraction width 10. A chosen
elimination order gives an UPPER bound on cost and says nothing about what a
good optimiser will find. So widths here come from cotengra, not from us.

NO QUANTUM TIME IS USED. This is pure classical analysis of topology.

Run:
    python demo/eqccm/heavyhex_width_search.py
    python demo/eqccm/heavyhex_width_search.py --sizes 16 40 80 156 --max-layers 4

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
import json
import os
from collections import deque
from typing import Dict, List, Sequence, Set, Tuple

import networkx as nx

try:
    import cotengra as ctg
except ImportError:
    ctg = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
COUPLING_PATH = os.path.join(_REPO, "data", "fez_coupling.json")

# Empirical anchor from banded_scaling.py (n=30 sweep, band 22)
ANCHOR_WIDTH = 22
ANCHOR_SECONDS = 14.422307
ANCHOR_PEAK_BYTES = 536.87e6

# Effective two-qubit error, back-fitted from the record's own hardware runs:
#   F ~ 0.93 at 15 CZ gates, F ~ 0.75 at 30 CZ gates
# giving 0.48%-0.96% per gate versus a 0.278% nominal median.
EFF_ERR_OPTIMISTIC = 0.005
EFF_ERR_CONSERVATIVE = 0.010


# ══════════════════════════════════════════════════════════════════
# 1. DEVICE TOPOLOGY
# ══════════════════════════════════════════════════════════════════

def load_coupling() -> Tuple[nx.Graph, dict]:
    if not os.path.exists(COUPLING_PATH):
        raise SystemExit(
            f"Missing {COUPLING_PATH}\n"
            "Run: python demo/eqccm/fetch_fez_topology.py")
    with open(COUPLING_PATH) as f:
        payload = json.load(f)
    g = nx.Graph()
    g.add_nodes_from(range(payload["n_qubits"]))
    g.add_edges_from(tuple(e) for e in payload["edges"])
    return g, payload


def connected_subregion(g: nx.Graph, size: int, seed: int = 0) -> Set[int]:
    """BFS a connected region of `size` qubits — mirrors picking a good patch."""
    if size >= g.number_of_nodes():
        return set(g.nodes())
    start = seed if seed in g else next(iter(g.nodes()))
    seen, q = {start}, deque([start])
    while q and len(seen) < size:
        u = q.popleft()
        for v in g.neighbors(u):
            if v not in seen:
                seen.add(v)
                q.append(v)
                if len(seen) >= size:
                    break
    return seen


def edge_matchings(g: nx.Graph) -> List[List[Tuple[int, int]]]:
    """
    Decompose edges into matchings via greedy edge colouring (colour the line
    graph). Each colour class is a set of disjoint edges = one physical layer.
    """
    if g.number_of_edges() == 0:
        return []
    line = nx.line_graph(g)
    colouring = nx.coloring.greedy_color(line, strategy="largest_first")
    by_colour: Dict[int, List[Tuple[int, int]]] = {}
    for edge, c in colouring.items():
        by_colour.setdefault(c, []).append(tuple(sorted(edge)))
    # biggest matchings first: most gates per unit depth
    return [by_colour[c] for c in sorted(by_colour, key=lambda c: -len(by_colour[c]))]


# ══════════════════════════════════════════════════════════════════
# 2. AMPLITUDE TENSOR NETWORK FOR A d-LAYER CIRCUIT
# ══════════════════════════════════════════════════════════════════

def build_network(qubits: Sequence[int], layers: Sequence[Sequence[Tuple[int, int]]],
                  n_open: int) -> Tuple[List[Tuple[str, ...]], Tuple[str, ...], Dict[str, int]]:
    """
    Return (inputs, output, size_dict) describing the amplitude network.

    Index naming:
      x{k}_{q}  intermediate variable for qubit q at layer boundary k
      y_{q}     open output index (kept in `output`, so many amplitudes at once)
    """
    qubits = list(qubits)
    d = len(layers)
    inputs: List[Tuple[str, ...]] = []

    def x(k: int, q: int) -> str:
        return f"x{k}_{q}"

    # initial RY: |0> -> x1
    for q in qubits:
        inputs.append((x(1, q),))

    # per layer: CZ phase factors (space), then RY transition (time)
    for k, layer in enumerate(layers, start=1):
        for (i, j) in layer:
            if i in set(qubits) and j in set(qubits):
                inputs.append((x(k, i), x(k, j)))
        if k < d:
            for q in qubits:
                inputs.append((x(k, q), x(k + 1, q)))

    # final RY: xd -> y (open for the first n_open qubits, else summed out)
    open_qubits = qubits[:n_open]
    for q in qubits:
        if q in open_qubits:
            inputs.append((f"y_{q}", x(d, q)))
        else:
            inputs.append((x(d, q),))

    output = tuple(f"y_{q}" for q in open_qubits)
    size_dict = {ix: 2 for t in inputs for ix in t}
    for ix in output:
        size_dict[ix] = 2
    return inputs, output, size_dict


def optimise_width(inputs, output, size_dict, preset: str) -> Tuple[float, float]:
    """Return (contraction_width_log2, contraction_cost) from cotengra."""
    tree = ctg.array_contract_tree(inputs, output, size_dict, optimize=preset)
    return float(tree.contraction_width()), float(tree.contraction_cost())


# ══════════════════════════════════════════════════════════════════
# 3. COST / FEASIBILITY MODEL
# ══════════════════════════════════════════════════════════════════

def classical_estimate(width: float) -> Tuple[float, float]:
    """Extrapolate runtime and peak memory from the measured 2^w law."""
    factor = 2.0 ** (width - ANCHOR_WIDTH)
    return ANCHOR_SECONDS * factor, ANCHOR_PEAK_BYTES * factor


def fmt_time(s: float) -> str:
    if s < 1:
        return f"{s * 1000:.0f} ms"
    if s < 90:
        return f"{s:.1f} s"
    if s < 5400:
        return f"{s / 60:.1f} min"
    if s < 86400 * 2:
        return f"{s / 3600:.1f} hr"
    return f"{s / 86400:.0f} days"


def fmt_bytes(b: float) -> str:
    for unit, div in (("PB", 1e15), ("TB", 1e12), ("GB", 1e9), ("MB", 1e6)):
        if b >= div:
            return f"{b / div:.1f} {unit}"
    return f"{b / 1e3:.0f} kB"


def fidelity(gates: int, err: float) -> float:
    return (1.0 - err) ** gates


# ══════════════════════════════════════════════════════════════════
# 4. THE SEARCH
# ══════════════════════════════════════════════════════════════════

def run(sizes: Sequence[int], max_layers: int, n_open: int, preset: str) -> None:
    g, payload = load_coupling()
    print(f"Device: {payload['backend']} · {g.number_of_nodes()} qubits · "
          f"{g.number_of_edges()} edges · max degree "
          f"{max(d for _, d in g.degree())}")

    all_matchings = edge_matchings(g)
    print(f"Edge colouring: {len(all_matchings)} matchings, sizes "
          f"{[len(m) for m in all_matchings]}")
    print(f"Cotengra preset: {preset} · open outputs: {n_open} "
          f"({2 ** n_open} amplitudes)\n")

    print("=" * 92)
    print("OPTIMISED CONTRACTION WIDTH vs CIRCUIT DEPTH  (heavy-hex native)")
    print("=" * 92)
    print(f"{'n':>4} {'layers':>7} {'2q gates':>9} {'width':>7} "
          f"{'classical T':>12} {'classical mem':>14} "
          f"{'F@0.5%':>8} {'F@1.0%':>8}")
    print("-" * 92)

    results = []
    for n in sizes:
        region = connected_subregion(g, n)
        sub = g.subgraph(region).copy()
        matchings = edge_matchings(sub)
        qubits = sorted(region)

        for d in range(1, max_layers + 1):
            # Cycle through the colouring: layer k reuses matching k mod C.
            # Real circuits repeat a fixed set of gate layers; without this the
            # depth is capped at the chromatic number and the space-time network
            # never leaves the near-1D regime (width ~ min(n, d)).
            layers = [matchings[k % len(matchings)] for k in range(d)]
            gates = sum(len(m) for m in layers)

            inputs, output, size_dict = build_network(qubits, layers, n_open)
            try:
                width, cost = optimise_width(inputs, output, size_dict, preset)
            except Exception as e:
                print(f"{n:>4} {d:>7} {gates:>9}   optimiser failed: {e}")
                continue

            t_est, m_est = classical_estimate(width)
            f_opt = fidelity(gates, EFF_ERR_OPTIMISTIC)
            f_con = fidelity(gates, EFF_ERR_CONSERVATIVE)

            results.append({"n": n, "layers": d, "gates": gates,
                            "width": width, "cost": cost,
                            "t_est": t_est, "m_est": m_est,
                            "f_opt": f_opt, "f_con": f_con})

            print(f"{n:>4} {d:>7} {gates:>9} {width:>7.1f} "
                  f"{fmt_time(t_est):>12} {fmt_bytes(m_est):>14} "
                  f"{f_opt:>8.3f} {f_con:>8.3f}")

    interpret(results)


def interpret(results: List[dict]) -> None:
    print()
    print("=" * 92)
    print("INTERPRETATION")
    print("=" * 92)
    if not results:
        print("No results.")
        return

    # A candidate is interesting if it is expensive classically AND the
    # hardware can still return signal.
    HARD_SECONDS = 3600.0      # >= 1 hour classical is a meaningful cost
    MIN_FIDELITY = 0.05        # below this, shot cost becomes absurd

    viable = [r for r in results
              if r["t_est"] >= HARD_SECONDS and r["f_con"] >= MIN_FIDELITY]

    print("A candidate needs BOTH: expensive classically, and hardware signal")
    print(f"that survives (>= 1 hr classical, conservative F >= {MIN_FIDELITY}).\n")

    if viable:
        viable.sort(key=lambda r: (-r["f_con"], r["t_est"]))
        print(f"{len(viable)} candidate(s) satisfy both constraints:\n")
        for r in viable[:6]:
            shots = int(10_000 / max(r["f_con"], 1e-6) ** 2)
            print(f"  n={r['n']}, {r['layers']} layers, {r['gates']} CZ gates")
            print(f"    optimised width {r['width']:.1f}  ->  "
                  f"{fmt_time(r['t_est'])} classical, {fmt_bytes(r['m_est'])} peak")
            print(f"    predicted fidelity {r['f_con']:.3f} (conservative) / "
                  f"{r['f_opt']:.3f} (optimistic)")
            print(f"    shots for SNR parity with the record's 10k at F~0.93: "
                  f"~{shots:,}")
            print()
    else:
        print("NO candidate satisfies both constraints.")
        best_hard = max(results, key=lambda r: r["width"])
        best_live = max((r for r in results if r["f_con"] >= MIN_FIDELITY),
                        key=lambda r: r["width"], default=None)
        print(f"  Widest overall: n={best_hard['n']}, {best_hard['layers']} layers, "
              f"width {best_hard['width']:.1f}, but F={best_hard['f_con']:.4f} "
              f"({best_hard['gates']} gates) — hardware signal is gone.")
        if best_live:
            print(f"  Widest with usable fidelity: n={best_live['n']}, "
                  f"{best_live['layers']} layers, width {best_live['width']:.1f} "
                  f"-> only {fmt_time(best_live['t_est'])} classically.")
        print()
        print("  That gap IS the result: on heavy-hex, the depth needed to make")
        print("  contraction expensive costs more fidelity than the device has")
        print("  to spend. It is a quantitative statement of the wall, measured")
        print("  on the real coupling map rather than assumed.")

    print()
    print("Caveats kept explicit:")
    print("  * widths are cotengra's, not our elimination order (the §13 lesson)")
    print("  * classical T/memory extrapolate our own measured 2^w law from")
    print("    width 22; they assume no slicing. Slicing trades memory for time")
    print("    and is exactly how Cotengra won 3/5 in §7, so real classical cost")
    print("    at large width will be LOWER than these figures suggest")
    print("  * fidelity is a gate-count product, ignoring idle decoherence,")
    print("    crosstalk and readout — it is an upper bound on real fidelity")
    print("  * no quantum time was used to produce any of this")
    print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", type=int, nargs="+", default=[16, 40, 80, 156])
    p.add_argument("--max-layers", type=int, default=4)
    p.add_argument("--open", dest="n_open", type=int, default=3)
    p.add_argument("--preset", default="auto-hq",
                   help="cotengra preset: greedy | auto | auto-hq")
    args = p.parse_args()

    print()
    print("#" * 92)
    print("# EQCCM — heavy-hex depth vs optimised contraction width")
    print("# Does hardware-native structure ever get classically expensive?")
    print("#" * 92)
    print()

    if ctg is None:
        raise SystemExit("cotengra not installed. Run: pip install cotengra")

    run(args.sizes, args.max_layers, args.n_open, args.preset)


if __name__ == "__main__":
    main()
