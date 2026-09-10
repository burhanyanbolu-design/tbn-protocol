"""
EQCCM — Is the wall heavy-hex's fault, or fundamental?
======================================================
heavyhex_width_search.py produced a negative result on ibm_fez: reaching
optimised contraction width 31 took 822 two-qubit gates, by which point
predicted fidelity was ~3e-4. The stated conclusion was "needs 6-12x better
gates."

That conclusion assumed the topology was fixed. This script tests the
assumption, because there is a second variable: HOW MANY GATES IT COSTS TO BUY
WIDTH depends on the coupling graph, and heavy-hex is planar and degree-3 —
close to the worst case for treewidth growth.

FIGURE OF MERIT
Fidelity is governed by gate count G. Classical hardness is governed by
contraction width W. So the quantity that decides feasibility is

    eta = W / G          "width bought per gate spent"

Given a target width W and a fidelity floor F, the required per-gate error is

    eps <= 1 - F^(1/G)  =  1 - F^(eta/W)

so a topology with larger eta needs WORSE gates to hit the same target. This
converts "which topology" into a single comparable number, and then into a
hardware requirement that can be checked against Fez's real calibration.

WHY THIS MIGHT OVERTURN THE CONCLUSION
Planar graphs on n vertices have treewidth O(sqrt(n)). Random regular graphs
of the SAME degree are expanders, with treewidth Theta(n). So heavy-hex and a
random 3-regular graph have identical degree and similar edge counts, but very
different width growth. If that difference is large, the binding constraint is
planarity, not gate error — a materially different engineering conclusion.

Topologies compared, all at matched qubit count:
    heavy_hex_fez     the real device (planar, degree 3)
    square_grid       planar, degree 4
    hex_lattice       planar, degree 3, for a planar-vs-planar control
    random_3_regular  non-planar, degree 3 — same degree as Fez
    random_4_regular  non-planar, degree 4
    small_world       ring + random shortcuts (few long-range couplers)
    all_to_all_sparse degree 8, models reconfigurable connectivity

No quantum time used. Pure classical topology analysis.

Run:
    python demo/eqccm/topology_comparison.py
    python demo/eqccm/topology_comparison.py --n 100 --max-layers 6

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
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

# Fez's real numbers, for the feasibility verdict
FEZ_ERR_NOMINAL_BEST = 0.00204   # best-quartile median, measured
FEZ_ERR_EFFECTIVE_LO = 0.005     # back-fitted from record §9  (15 gates)
FEZ_ERR_EFFECTIVE_HI = 0.010     # back-fitted from record §10 (30 gates)

# Width worth reaching. From banded_scaling.py's measured 2^w law:
#   width 22 -> 14.4 s,  width 31 -> 2.1 hr,  width 35 -> 33 hr
TARGET_WIDTHS = (22, 31, 35)
FIDELITY_FLOOR = 0.5


# ══════════════════════════════════════════════════════════════════
# TOPOLOGIES
# ══════════════════════════════════════════════════════════════════

def load_fez() -> nx.Graph:
    if not os.path.exists(COUPLING_PATH):
        raise SystemExit(f"Missing {COUPLING_PATH}\n"
                         "Run: python demo/eqccm/fetch_fez_topology.py")
    with open(COUPLING_PATH) as f:
        payload = json.load(f)
    g = nx.Graph()
    g.add_nodes_from(range(payload["n_qubits"]))
    g.add_edges_from(tuple(e) for e in payload["edges"])
    return g


def build_topologies(n: int) -> Dict[str, nx.Graph]:
    tops: Dict[str, nx.Graph] = {}

    fez = load_fez()
    if n < fez.number_of_nodes():
        # connected patch, same way a real experiment would pick qubits
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
        fez = fez.subgraph(seen).copy()
    tops["heavy_hex_fez"] = nx.convert_node_labels_to_integers(fez)

    side = int(math.isqrt(n))
    tops["square_grid"] = nx.convert_node_labels_to_integers(
        nx.grid_2d_graph(side, max(1, n // side)))

    tops["hex_lattice"] = nx.convert_node_labels_to_integers(
        nx.hexagonal_lattice_graph(max(2, side // 2), max(2, side // 2)))

    for deg in (3, 4):
        m = n if (n * deg) % 2 == 0 else n - 1
        tops[f"random_{deg}_regular"] = nx.random_regular_graph(
            deg, m, seed=SEED)

    tops["small_world"] = nx.connected_watts_strogatz_graph(
        n, 4, 0.15, seed=SEED)

    tops["all_to_all_sparse"] = nx.random_regular_graph(
        8, n if (n * 8) % 2 == 0 else n - 1, seed=SEED)

    return tops


def matchings_of(g: nx.Graph) -> List[List[Tuple[int, int]]]:
    """Edge-colour so each colour class is a set of disjoint (parallel) gates."""
    if g.number_of_edges() == 0:
        return []
    colouring = nx.coloring.greedy_color(nx.line_graph(g),
                                         strategy="largest_first")
    by_colour: Dict[int, List[Tuple[int, int]]] = {}
    for edge, c in colouring.items():
        by_colour.setdefault(c, []).append(tuple(sorted(edge)))
    return [by_colour[c] for c in sorted(by_colour, key=lambda c: -len(by_colour[c]))]


# ══════════════════════════════════════════════════════════════════
# NETWORK + WIDTH  (same construction as heavyhex_width_search.py)
# ══════════════════════════════════════════════════════════════════

def contraction_width(qubits: Sequence[int],
                      layers: Sequence[Sequence[Tuple[int, int]]],
                      n_open: int, preset: str) -> float:
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
    open_qubits = qs[:n_open]
    for q in qs:
        inputs.append((f"y_{q}", x(d, q)) if q in open_qubits else (x(d, q),))

    output = tuple(f"y_{q}" for q in open_qubits)
    size_dict = {ix: 2 for t in inputs for ix in t}
    for ix in output:
        size_dict[ix] = 2

    tree = ctg.array_contract_tree(inputs, output, size_dict, optimize=preset)
    return float(tree.contraction_width())


# ══════════════════════════════════════════════════════════════════
# ANALYSIS
# ══════════════════════════════════════════════════════════════════

def required_error(target_width: float, eta: float, floor: float) -> float:
    """Per-gate error needed to hold fidelity >= floor at the target width."""
    if eta <= 0:
        return 0.0
    gates = target_width / eta
    return 1.0 - floor ** (1.0 / gates)


def analyse(name: str, g: nx.Graph, max_layers: int, n_open: int,
            preset: str) -> dict:
    ms = matchings_of(g)
    qubits = sorted(g.nodes())
    rows = []
    best_eta, best = 0.0, None

    for d in range(1, max_layers + 1):
        layers = [ms[k % len(ms)] for k in range(d)]
        gates = sum(len(m) for m in layers)
        try:
            w = contraction_width(qubits, layers, n_open, preset)
        except Exception:
            continue
        eta = w / gates if gates else 0.0
        rows.append({"d": d, "gates": gates, "width": w, "eta": eta})
        if eta > best_eta:
            best_eta, best = eta, rows[-1]

    return {
        "name": name,
        "n": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "max_degree": max((d for _, d in g.degree()), default=0),
        "planar": nx.check_planarity(g)[0],
        "rows": rows,
        "best": best,
        "best_eta": best_eta,
    }


def report(results: List[dict]) -> None:
    print("=" * 100)
    print("WIDTH PER GATE  (eta = width / two-qubit gate count; higher is better)")
    print("=" * 100)
    print(f"{'topology':>18} {'n':>4} {'edges':>6} {'deg':>4} {'planar':>7} "
          f"{'best eta':>9} {'at width':>9} {'gates':>7}")
    print("-" * 100)

    for r in sorted(results, key=lambda r: -r["best_eta"]):
        b = r["best"]
        if not b:
            continue
        print(f"{r['name']:>18} {r['n']:>4} {r['edges']:>6} "
              f"{r['max_degree']:>4} {str(r['planar']):>7} "
              f"{r['best_eta']:>9.4f} {b['width']:>9.1f} {b['gates']:>7}")

    print()
    print("=" * 100)
    print("REQUIRED GATE ERROR to hold fidelity >= 0.5 at a target width")
    print("=" * 100)
    print(f"Compare against ibm_fez: best-quartile NOMINAL "
          f"{FEZ_ERR_NOMINAL_BEST:.3%}, "
          f"EFFECTIVE {FEZ_ERR_EFFECTIVE_LO:.1%}-{FEZ_ERR_EFFECTIVE_HI:.1%}")
    print("(effective is back-fitted from the record's own hardware runs)\n")

    hdr = f"{'topology':>18}" + "".join(f"{'W=' + str(w):>14}" for w in TARGET_WIDTHS)
    print(hdr)
    print("-" * 100)

    feasible_now = []
    for r in sorted(results, key=lambda r: -r["best_eta"]):
        if not r["best"]:
            continue
        cells = ""
        for tw in TARGET_WIDTHS:
            eps = required_error(tw, r["best_eta"], FIDELITY_FLOOR)
            mark = ""
            if eps >= FEZ_ERR_EFFECTIVE_HI:
                mark = " **"
                feasible_now.append((r["name"], tw, eps))
            elif eps >= FEZ_ERR_EFFECTIVE_LO:
                mark = " *"
                feasible_now.append((r["name"], tw, eps))
            cells += f"{eps:>11.3%}{mark:>3}"
        print(f"{r['name']:>18}{cells}")

    print("\n  ** achievable at Fez's WORST effective error (>=1.0%)")
    print("   * achievable at Fez's BEST effective error (>=0.5%)")
    print()

    print("=" * 100)
    print("INTERPRETATION")
    print("=" * 100)

    by_name = {r["name"]: r for r in results}
    hh = by_name.get("heavy_hex_fez")
    r3 = by_name.get("random_3_regular")

    if hh and r3 and hh["best_eta"] > 0:
        ratio = r3["best_eta"] / hh["best_eta"]
        print(f"Same degree, opposite structure:")
        print(f"  heavy_hex_fez     planar,     eta = {hh['best_eta']:.4f}")
        print(f"  random_3_regular  non-planar, eta = {r3['best_eta']:.4f}")
        print(f"  -> random wiring buys width {ratio:.1f}x more cheaply at "
              f"IDENTICAL degree.\n")
        if ratio > 2:
            print("  That isolates the cause: the binding constraint is")
            print("  PLANARITY, not gate error and not degree. Heavy-hex is")
            print("  planar, so its treewidth grows as O(sqrt(n)) and width has")
            print("  to be bought with depth. A non-planar graph of the same")
            print("  degree is an expander, treewidth Theta(n), so width comes")
            print("  almost for free.\n")

    if feasible_now:
        print("Reachable with gate quality that EXISTS TODAY:")
        seen = set()
        for name, tw, eps in feasible_now:
            if (name, tw) in seen:
                continue
            seen.add((name, tw))
            print(f"  {name:>18}  width {tw}  needs <= {eps:.3%} per gate")
        print()
        print("  This changes the engineering conclusion. The earlier '6-12x")
        print("  better gates' requirement was a consequence of heavy-hex's")
        print("  planarity, not a fundamental limit. Architectures with")
        print("  non-local connectivity — trapped ion, neutral atom with")
        print("  reconfigurable couplers, photonic — would clear the bar at")
        print("  today's error rates.")
    else:
        print("No topology tested clears the bar at current error rates.")
        print("That would make the limit fundamental rather than architectural.")

    print()
    print("Caveats:")
    print("  * these are IDEALISED coupling graphs. You cannot rewire a")
    print("    fabricated chip; SWAP-embedding a random graph into heavy-hex")
    print("    reintroduces the depth cost this analysis avoids.")
    print("  * widths come from cotengra's chosen preset and are upper bounds")
    print("    on optimal; a stronger optimiser lowers them (§13 lesson).")
    print("  * fidelity is a gate-count product, ignoring idle decoherence,")
    print("    crosstalk and readout — an upper bound on real fidelity.")
    print("  * eta is measured over the depths swept here; it is not proven")
    print("    to be the asymptotic optimum for any topology.")
    print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=156)
    p.add_argument("--max-layers", type=int, default=8)
    p.add_argument("--open", dest="n_open", type=int, default=3)
    p.add_argument("--preset", default="greedy")
    args = p.parse_args()

    print()
    print("#" * 100)
    print("# EQCCM — topology comparison: is the heavy-hex wall architectural?")
    print("#" * 100)
    print()

    if ctg is None:
        raise SystemExit("cotengra not installed. Run: pip install cotengra")

    tops = build_topologies(args.n)
    print(f"Comparing {len(tops)} topologies at n~{args.n}, "
          f"depths 1-{args.max_layers}, preset {args.preset}\n")

    results = []
    for name, g in tops.items():
        print(f"  analysing {name} "
              f"(n={g.number_of_nodes()}, e={g.number_of_edges()}, "
              f"deg={max((d for _, d in g.degree()), default=0)})...")
        results.append(analyse(name, g, args.max_layers, args.n_open, args.preset))

    print()
    report(results)


if __name__ == "__main__":
    main()
