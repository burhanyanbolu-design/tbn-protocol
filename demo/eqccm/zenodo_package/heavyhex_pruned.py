"""
EQCCM — Amplitude-Magnitude Pruning on the REAL Heavy-Hex Topology
==================================================================
Follow-up to Addendum VI, which tested pruning only on the synthetic banded
family E(n,w). This tests the open question that addendum left explicitly
listed as "worth testing next": does the pruning result hold on the actual
hardware topology, or was it specific to the banded family?

WHAT'S DIFFERENT FROM banded_scaling_pruned.py
Two structural differences, both forced by the topology being real:

  1. The graph is NOT synthetic. Edges come from data/fez_coupling.json —
     the real 156-qubit ibm_fez coupling map already fetched (metadata only,
     no quantum time) by fetch_fez_topology.py.

  2. The circuit is MULTI-LAYER, not single-layer. This matters: heavy-hex
     is degree-3 and planar, so ONE CZ layer has tiny treewidth and is
     trivially contractible — there would be nothing to prune. Width on
     heavy-hex is bought by DEPTH, because the amplitude's tensor network
     extends in time as well as space (this is the same reasoning already
     documented in heavyhex_width_search.py). So the state carried here is
     the frontier across a space-time lattice, not a single spatial cut.

     Circuit family, matching heavyhex_width_search.py:
        |psi> = RY^(d+1) [CZ layer d] ... RY^(2) [CZ layer 1] RY^(1) |0>^n
     Each CZ layer is a MATCHING (disjoint edges), so it executes in one
     physical timestep. Heavy-hex being degree-3, greedy edge colouring
     gives 3-4 matchings; layer k reuses matching (k mod C), same as the
     width-search script, so depth isn't capped at the chromatic number.

HONEST EXPECTATION, STATED BEFORE RUNNING
heavyhex_width_search.py already established that on the real coupling map,
optimised contraction width stays SMALL at any depth where the hardware
still returns signal. So the exact problem may already be cheap here, in
which case pruning will have little or nothing to trim. That is a legitimate
and useful outcome — it would mean the Addendum VI result is specific to
high-treewidth families and does not transfer to hardware-native topology.
Recording that expectation up front so a null result can't be quietly
reframed later as a surprise.

METHOD — same two-stage discipline as Addendum VI
  Stage 1 (mechanism, not idea): run with threshold=0.0, pruning nothing.
     Must reproduce a dense statevector reference exactly. This isolates
     "is the space-time sparse bookkeeping correct" from "does pruning
     preserve accuracy". Stage 2 only runs if Stage 1 passes.
  Stage 2 (the experiment): sweep thresholds > 0, measuring reconstruction
     error, configurations retained, wall-clock, and approximate memory,
     all against the exact reference.

WHAT THIS DOES NOT CLAIM
  * No novelty. Amplitude truncation is textbook tensor-network practice.
  * No physical interpretation. Coordinates here are abstract space-time
    frontier-configuration magnitudes, not physical positions.
  * No quantum time used. Topology is read from a cached metadata file.
  * Does not modify banded_scaling.py or banded_scaling_pruned.py; every
    result already published stands unchanged.

Run:
    python demo/eqccm/heavyhex_pruned.py --verify-only        # Stage 1 only
    python demo/eqccm/heavyhex_pruned.py --n 12 --layers 3
    python demo/eqccm/heavyhex_pruned.py --n 14 --layers 4 \
        --thresholds 0.0 0.01 0.1 0.3 0.5 0.9

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import argparse
import json
import os
import statistics
import time
from collections import deque
from typing import Dict, List, Sequence, Set, Tuple

import numpy as np

BYTES_PER_ELEM = 8  # float64

_HERE = os.path.dirname(os.path.abspath(__file__))

# Search several locations so this runs both inside the repo and standalone
# from the Zenodo package directory, where there is no ../../data.
_CANDIDATES = [
    os.path.join(_HERE, "fez_coupling.json"),
    os.path.join(_HERE, "data", "fez_coupling.json"),
    os.path.abspath(os.path.join(_HERE, "..", "..", "data", "fez_coupling.json")),
    os.path.abspath(os.path.join(_HERE, "..", "data", "fez_coupling.json")),
]


def coupling_path() -> str:
    for c in _CANDIDATES:
        if os.path.exists(c):
            return c
    raise SystemExit(
        "Could not find fez_coupling.json. Looked in:\n  "
        + "\n  ".join(_CANDIDATES)
        + "\nRegenerate it with: python fetch_fez_topology.py  (metadata only)")


# ══════════════════════════════════════════════════════════════════
# 1. REAL DEVICE TOPOLOGY (cached metadata, no quantum time)
# ══════════════════════════════════════════════════════════════════

def load_coupling() -> Tuple[Dict[int, Set[int]], dict]:
    """Load the real ibm_fez coupling map as an adjacency dict."""
    with open(coupling_path()) as f:
        payload = json.load(f)
    adj: Dict[int, Set[int]] = {q: set() for q in range(payload["n_qubits"])}
    for a, b in payload["edges"]:
        adj[int(a)].add(int(b))
        adj[int(b)].add(int(a))
    return adj, payload


def connected_subregion(adj: Dict[int, Set[int]], size: int, start: int = 0) -> List[int]:
    """BFS a connected patch of `size` qubits — mirrors picking a real patch
    on the device rather than an arbitrary scatter of disconnected qubits."""
    if size >= len(adj):
        return sorted(adj.keys())
    seen, queue = {start}, deque([start])
    while queue and len(seen) < size:
        u = queue.popleft()
        for v in sorted(adj[u]):
            if v not in seen:
                seen.add(v)
                queue.append(v)
                if len(seen) >= size:
                    break
    return sorted(seen)


def edge_matchings(qubits: Sequence[int], adj: Dict[int, Set[int]]) -> List[List[Tuple[int, int]]]:
    """
    Greedy edge colouring restricted to `qubits`. Each colour class is a set
    of disjoint edges = one physical CZ layer executable in one timestep.
    Pure-stdlib greedy (no networkx dependency): repeatedly take the largest
    set of edges that share no qubit.
    """
    qset = set(qubits)
    edges = sorted({tuple(sorted((a, b)))
                    for a in qubits for b in adj[a] if b in qset})
    remaining = list(edges)
    matchings: List[List[Tuple[int, int]]] = []
    while remaining:
        used: Set[int] = set()
        layer: List[Tuple[int, int]] = []
        leftover: List[Tuple[int, int]] = []
        for (a, b) in remaining:
            if a not in used and b not in used:
                layer.append((a, b))
                used.add(a)
                used.add(b)
            else:
                leftover.append((a, b))
        matchings.append(layer)
        remaining = leftover
    # biggest matchings first: most gates per unit of depth
    matchings.sort(key=len, reverse=True)
    return matchings


def build_layers(matchings: List[List[Tuple[int, int]]], depth: int
                 ) -> List[List[Tuple[int, int]]]:
    """Layer k reuses matching (k mod C), same convention as
    heavyhex_width_search.py — otherwise depth is capped at the chromatic
    number and the space-time network never leaves the near-1D regime."""
    if not matchings:
        return []
    return [matchings[k % len(matchings)] for k in range(depth)]


# ══════════════════════════════════════════════════════════════════
# 2. CIRCUIT FACTORS  (same RY + CZ family as the rest of the study)
# ══════════════════════════════════════════════════════════════════

def ry_matrix(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def deterministic_angles(n_layers_plus_one: int, qubits: Sequence[int]
                         ) -> Dict[Tuple[int, int], float]:
    """
    Deterministic, irrational-ish angles per (layer, qubit), same spirit as
    banded_scaling.deterministic_angles: avoid special values that could
    accidentally zero out amplitudes, and stay reproducible run to run.
    """
    angles: Dict[Tuple[int, int], float] = {}
    for li in range(n_layers_plus_one):
        for qi, q in enumerate(qubits):
            angles[(li, q)] = 0.4 + 0.31 * np.sqrt(qi + 1.0) + 0.17 * np.sqrt(li + 1.0)
    return angles


# ══════════════════════════════════════════════════════════════════
# 3. DENSE STATEVECTOR REFERENCE (ground truth, small n only)
# ══════════════════════════════════════════════════════════════════

def statevector_reference(qubits: Sequence[int],
                          layers: List[List[Tuple[int, int]]],
                          angles: Dict[Tuple[int, int], float]) -> np.ndarray:
    """
    Full state by direct simulation of the multi-layer circuit. Only feasible
    for small patches — this is the honest baseline Stage 1 checks against.
    Qubit q of the device maps to axis index qubits.index(q).
    """
    n = len(qubits)
    idx = {q: i for i, q in enumerate(qubits)}
    psi = np.zeros((2,) * n, dtype=np.float64)
    psi[(0,) * n] = 1.0

    def apply_ry(state, axis, theta):
        m = ry_matrix(theta)
        state = np.moveaxis(state, axis, -1)
        state = state @ m.T
        return np.moveaxis(state, -1, axis)

    # initial RY layer
    for q in qubits:
        psi = apply_ry(psi, idx[q], angles[(0, q)])

    # each CZ layer, then the RY layer after it
    for li, layer in enumerate(layers, start=1):
        for (a, b) in layer:
            slicer = [slice(None)] * n
            slicer[idx[a]] = 1
            slicer[idx[b]] = 1
            psi[tuple(slicer)] *= -1.0
        for q in qubits:
            psi = apply_ry(psi, idx[q], angles[(li, q)])

    return psi


# ══════════════════════════════════════════════════════════════════
# 4. SPACE-TIME FRONTIER CONTRACTION, WITH PRUNING
# ══════════════════════════════════════════════════════════════════

def contract_heavyhex_pruned(
    qubits: Sequence[int],
    layers: List[List[Tuple[int, int]]],
    angles: Dict[Tuple[int, int], float],
    y_fixed: Dict[int, int],
    open_qubits: Sequence[int],
    threshold: float = 0.0,
) -> Tuple[np.ndarray, Dict]:
    """
    Amplitude(s) by sweeping the circuit LAYER BY LAYER, holding the state of
    all n qubits at the current layer boundary as a dict:
        {frontier_config (tuple of n bits) -> value_array over open y axes}

    This is the space-time frontier: unlike the banded single-layer case
    (where the frontier was a spatial cut that grew and shrank), here the
    frontier is the full width of the patch at each time boundary, and depth
    is what makes the state space large. That's the correct structure for a
    shallow planar topology — and it's why the banded elimination order does
    not transfer directly.

    threshold=0.0 prunes nothing and must match the dense reference exactly.
    threshold > 0.0 drops configurations whose value magnitude is below
    threshold * (current max magnitude), after each layer.
    """
    qubits = list(qubits)
    n = len(qubits)
    idx = {q: i for i, q in enumerate(qubits)}
    open_list = list(open_qubits)

    # ── initial RY layer: build the full 2^n distribution over bit configs ──
    # Start from |0...0> and apply RY to each qubit: amplitude for config c is
    # the product over qubits of <c_q| RY(theta) |0>.
    a_cols = {q: ry_matrix(angles[(0, q)])[:, 0] for q in qubits}  # [<0|..|0>, <1|..|0>]

    state: Dict[Tuple[int, ...], np.ndarray] = {}
    scalar_one = np.ones((), dtype=np.float64)
    # iterate all 2^n configs — fine at the small n where a dense reference
    # is also computable, which is exactly the regime Stage 1 needs
    for config in np.ndindex(*([2] * n)):
        amp = 1.0
        for i, q in enumerate(qubits):
            amp *= a_cols[q][config[i]]
        state[tuple(int(b) for b in config)] = scalar_one * amp

    peak_configs = len(state)
    total_pruned = 0
    gates_applied = 0
    # Post-prune sizes are the number that actually answers the research
    # question. peak_configs is dominated by the dense initial layer, so it
    # can never show a pruning benefit — see the note in stats below.
    post_prune_sizes: List[int] = []
    pre_prune_sizes: List[int] = []

    # ── per layer: CZ phases (space), then RY transition (time) ──
    for li, layer in enumerate(layers, start=1):
        # CZ: sign flip where both endpoints are 1
        for (a, b) in layer:
            ia, ib = idx[a], idx[b]
            for key in list(state.keys()):
                if key[ia] == 1 and key[ib] == 1:
                    state[key] = state[key] * -1.0
            gates_applied += 1

        # RY transition on every qubit: this MIXES configs, so it's a full
        # transfer step — new_config accumulates contributions from old ones.
        ry_mats = {q: ry_matrix(angles[(li, q)]) for q in qubits}
        for i, q in enumerate(qubits):
            m = ry_mats[q]  # m[new_bit, old_bit]
            mixed: Dict[Tuple[int, ...], np.ndarray] = {}
            for key, val in state.items():
                old = key[i]
                for new in (0, 1):
                    coeff = m[new, old]
                    if coeff == 0.0:
                        continue
                    nk = key[:i] + (new,) + key[i + 1:]
                    contrib = val * coeff
                    if nk in mixed:
                        mixed[nk] = mixed[nk] + contrib
                    else:
                        mixed[nk] = contrib
            state = mixed

        peak_configs = max(peak_configs, len(state))

        # ── PRUNE: drop low-magnitude configurations ──
        pre_prune_sizes.append(len(state))
        if threshold > 0.0 and state:
            mags = {k: float(np.max(np.abs(v))) for k, v in state.items()}
            current_max = max(mags.values()) if mags else 0.0
            if current_max > 0.0:
                cutoff = threshold * current_max
                kept = {k: v for k, v in state.items() if mags[k] >= cutoff}
                total_pruned += len(state) - len(kept)
                state = kept
        post_prune_sizes.append(len(state))

    # ── read out: fix the closed qubits, keep the open ones as axes ──
    out_shape = (2,) * len(open_list)
    T = np.zeros(out_shape, dtype=np.float64)
    open_idx = [idx[q] for q in open_list]
    for key, val in state.items():
        # skip configs that disagree with the fixed (closed) outputs
        ok = True
        for q, want in y_fixed.items():
            if q in idx and key[idx[q]] != want:
                ok = False
                break
        if not ok:
            continue
        pos = tuple(key[i] for i in open_idx)
        T[pos] += float(val)

    # Does the state re-expand after pruning? If pruning is to compound into
    # a real memory saving, a layer's PRE-prune size must stay near the
    # PREVIOUS layer's POST-prune size. If instead it jumps back to the full
    # space, the single-qubit rotations are regenerating everything that was
    # dropped and pruning buys nothing in memory, whatever the retained count.
    refill = None
    if len(post_prune_sizes) >= 2:
        ratios = [pre_prune_sizes[k + 1] / max(1, post_prune_sizes[k])
                  for k in range(len(post_prune_sizes) - 1)]
        refill = max(ratios) if ratios else None

    stats = {
        "peak_configs": peak_configs,
        "peak_bytes_approx": peak_configs * BYTES_PER_ELEM,
        "total_pruned": total_pruned,
        "gates": gates_applied,
        "full_space": 2 ** n,
        "n": n,
        "depth": len(layers),
        # the honest memory-relevant numbers
        "peak_post_prune": max(post_prune_sizes) if post_prune_sizes else len(state),
        "post_prune_sizes": post_prune_sizes,
        "pre_prune_sizes": pre_prune_sizes,
        "max_refill_factor": refill,
    }
    return T, stats


# ══════════════════════════════════════════════════════════════════
# 5. STAGE 1 — mechanism check (threshold = 0.0 only)
# ══════════════════════════════════════════════════════════════════

def verify_exact(sizes: Sequence[int] = (8, 10, 12),
                 depths: Sequence[int] = (1, 2, 3)) -> bool:
    """
    Confirm the space-time sparse contraction, with pruning OFF, reproduces
    the dense statevector reference on small REAL heavy-hex patches.

    This checks the NEW CODE, not the pruning idea. If this fails, the bug is
    in the layer-sweep bookkeeping above — do not proceed to Stage 2.
    """
    print("=" * 78)
    print("STAGE 1 — sparse space-time contraction vs dense statevector")
    print("=" * 78)
    print("Real ibm_fez patches, pruning OFF (threshold=0.0).")
    print("Must match to ~1e-12. Isolates 'is the mechanism correct' from")
    print("'does pruning preserve accuracy' — the latter is Stage 2.\n")

    adj, payload = load_coupling()
    print(f"Device: {payload['backend']} · {payload['n_qubits']} qubits · "
          f"{len(payload['edges'])} edges\n")

    all_ok = True
    for n in sizes:
        qubits = connected_subregion(adj, n)
        matchings = edge_matchings(qubits, adj)
        for d in depths:
            layers = build_layers(matchings, d)
            angles = deterministic_angles(d + 1, qubits)

            n_open = min(3, n)
            open_qubits = qubits[:n_open]
            y_fixed = {q: (i % 2) for i, q in enumerate(qubits) if q not in open_qubits}

            psi = statevector_reference(qubits, layers, angles)
            T, stats = contract_heavyhex_pruned(
                qubits, layers, angles, y_fixed, open_qubits, threshold=0.0)

            # pull the same amplitudes out of the dense state
            idx = {q: i for i, q in enumerate(qubits)}
            ref = np.empty((2,) * n_open, dtype=np.float64)
            for bits in np.ndindex(*([2] * n_open)):
                sel = [0] * n
                for q, v in y_fixed.items():
                    sel[idx[q]] = v
                for k, q in enumerate(open_qubits):
                    sel[idx[q]] = bits[k]
                ref[bits] = psi[tuple(sel)]

            err = float(np.max(np.abs(T - ref)))
            ok = err < 1e-12
            all_ok &= ok
            print(f"  n={n:3d} depth={d} gates={stats['gates']:3d}  "
                  f"max_abs_err={err:.3e}  {'OK' if ok else 'FAIL'}")

    print(f"\n{'PASS' if all_ok else 'FAIL'}: space-time contraction is exact "
          f"with pruning off.\n")
    return all_ok


# ══════════════════════════════════════════════════════════════════
# 6. STAGE 2 — threshold sweep on the real topology
# ══════════════════════════════════════════════════════════════════

def threshold_sweep(n: int, depth: int, thresholds: Sequence[float],
                    repeats: int = 3) -> List[Dict]:
    adj, payload = load_coupling()
    qubits = connected_subregion(adj, n)
    matchings = edge_matchings(qubits, adj)
    layers = build_layers(matchings, depth)
    angles = deterministic_angles(depth + 1, qubits)

    n_open = min(3, n)
    open_qubits = qubits[:n_open]
    y_fixed = {q: (i % 2) for i, q in enumerate(qubits) if q not in open_qubits}

    print("=" * 78)
    print(f"STAGE 2 — threshold sweep on real heavy-hex")
    print("=" * 78)
    print(f"Patch: {n} qubits from {payload['backend']}, depth {depth}, "
          f"{sum(len(l) for l in layers)} CZ gates")
    print(f"Full config space: 2^{n} = {2 ** n:,}")
    print(f"Open outputs: {n_open} ({2 ** n_open} amplitudes)")
    print("Ground truth: dense statevector reference.\n")

    psi = statevector_reference(qubits, layers, angles)
    idx = {q: i for i, q in enumerate(qubits)}
    ref = np.empty((2,) * n_open, dtype=np.float64)
    for bits in np.ndindex(*([2] * n_open)):
        sel = [0] * n
        for q, v in y_fixed.items():
            sel[idx[q]] = v
        for k, q in enumerate(open_qubits):
            sel[idx[q]] = bits[k]
        ref[bits] = psi[tuple(sel)]

    ref_scale = float(np.max(np.abs(ref)))
    print(f"Reference scale max|ref| = {ref_scale:.6e}")
    print("Columns: 'kept' = peak configs surviving AFTER a prune (the")
    print("memory-relevant number). 'refill' = how far the state re-expands")
    print("on the next layer; refill >> 1 means pruning does not compound.")
    print("'rel_err' = abs_err / max|ref|. rel_err ~ 1.0 with DEAD flag means")
    print("the amplitudes came out exactly zero: the answer was destroyed, not")
    print("approximated. Absolute error alone would hide that.")
    print()
    print(f"{'threshold':>10} {'abs_err':>11} {'rel_err':>9} {'kept':>8} "
          f"{'kept/2^n':>9} {'refill':>7} {'time_s':>8} {'':>4}")
    print("-" * 78)

    rows: List[Dict] = []
    for thr in thresholds:
        T, stats = contract_heavyhex_pruned(
            qubits, layers, angles, y_fixed, open_qubits, threshold=thr)
        samples = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            contract_heavyhex_pruned(
                qubits, layers, angles, y_fixed, open_qubits, threshold=thr)
            samples.append(time.perf_counter() - t0)
        t_med = statistics.median(samples)

        err = float(np.max(np.abs(T - ref)))
        rel = err / ref_scale if ref_scale > 0 else float("nan")
        out_scale = float(np.max(np.abs(T)))
        dead = out_scale == 0.0
        kept = stats["peak_post_prune"]
        vs_full = kept / float(2 ** n)
        refill = stats["max_refill_factor"]

        rows.append({"threshold": thr, "max_abs_err": err, "rel_err": rel,
                     "out_scale": out_scale, "dead": dead,
                     "peak_configs": stats["peak_configs"],
                     "kept": kept, "vs_full": vs_full, "time_s": t_med,
                     "refill": refill,
                     "total_pruned": stats["total_pruned"]})
        rs = "    n/a" if refill is None else f"{refill:>7.1f}"
        flag = "DEAD" if dead else ""
        print(f"{thr:>10.4f} {err:>11.3e} {rel:>9.4f} {kept:>8,} "
              f"{vs_full:>9.5f} {rs} {t_med:>8.5f} {flag:>4}")

    return rows


def interpret(rows: List[Dict], n: int) -> None:
    print()
    print("=" * 78)
    print("INTERPRETATION")
    print("=" * 78)
    if not rows:
        print("No rows.")
        return

    zero = next((r for r in rows if r["threshold"] == 0.0), None)
    if zero and zero["max_abs_err"] > 1e-10:
        print("WARNING: threshold=0.0 did not reproduce the exact result.")
        print("Re-run verify_exact() — this is a bookkeeping bug, not pruning.\n")

    pruning_rows = [r for r in rows if r["threshold"] > 0.0]
    any_pruned = [r for r in pruning_rows if r["total_pruned"] > 0]

    # The refill check comes first: it decides whether ANY retained-count
    # number in the table can be read as a memory saving.
    refills = [r["refill"] for r in pruning_rows if r.get("refill") is not None]
    if refills and max(refills) > 2.0:
        print("PRUNING DOES NOT COMPOUND ON THIS TOPOLOGY.")
        print(f"  max refill factor {max(refills):.1f}x — after each prune the")
        print("  single-qubit rotations regenerate the configurations that were")
        print("  just dropped, so the state returns to (near) full support on")
        print("  the following layer. The 'kept' column is therefore NOT a")
        print("  memory saving: peak memory stays at the full space regardless")
        print("  of threshold. Any speedup below is arithmetic saved inside a")
        print("  layer, not a smaller state.")
        print()
        print("  Why this differs from the banded family: there the frontier")
        print("  GREW incrementally and pruning suppressed its growth. Here")
        print("  every qubit is rotated every layer, so the frontier is the")
        print("  full patch width at every time boundary by construction, and")
        print("  there is no growth for pruning to suppress.")
        print()

    dead_rows = [r for r in pruning_rows if r.get("dead")]
    if dead_rows:
        lo = min(r["threshold"] for r in dead_rows)
        print(f"SIGNAL DESTROYED at threshold >= {lo}.")
        print("  The requested amplitudes came out EXACTLY zero, so the")
        print("  apparent error plateau is 100% relative error, not an")
        print("  accuracy floor. Reporting absolute error alone here would be")
        print("  misleading, which is why rel_err and the DEAD flag exist.")
        print("  Cause: the readout fixes most qubits to a specific output")
        print("  pattern, and every configuration matching that pattern was")
        print("  below the cutoff. A global magnitude cutoff is blind to which")
        print("  configurations the caller actually needs.")
        print()

    if not any_pruned:
        print("NOTHING WAS PRUNED at any tested threshold.")
        print()
        print("This is the expected-and-stated-up-front outcome for heavy-hex:")
        print("the topology is degree-3 and planar, so at these depths the")
        print("amplitude distribution has no long tail of negligible")
        print("configurations for a magnitude cutoff to exploit. It means the")
        print("Addendum VI result does NOT transfer to hardware-native")
        print("topology on this evidence — a real boundary on that finding,")
        print("not a failure of this test.")
    else:
        useful = [r for r in any_pruned
                  if not r.get("dead") and r["rel_err"] < 1e-3]
        if useful:
            best = max(useful, key=lambda r: r["threshold"])
            print(f"Largest threshold keeping RELATIVE error < 1e-3: "
                  f"{best['threshold']}")
            print(f"  rel_err {best['rel_err']:.3e}, retained "
                  f"{best['vs_full']:.2%} of the 2^{n} space, "
                  f"{best['time_s']:.6f}s")
            if best["vs_full"] > 0.5:
                print("  Retention above 50% — this is not a useful saving.")
        else:
            print("Pruning occurred, but NO threshold kept relative error")
            print("below 1e-3 while still returning a non-zero answer.")
            print("On this evidence the Addendum VI trade-off does not")
            print("reproduce on hardware-native topology.")

    print()
    print("What this does NOT show:")
    print("  * no novelty claim — amplitude truncation is textbook")
    print("  * one device topology, one circuit family, small patches only")
    print("  * verified only where a dense reference is computable")
    print("  * no physical interpretation of the pruned coordinates")
    print("  * no quantum time used (topology read from cached metadata)")
    print()


def main():
    p = argparse.ArgumentParser(
        description="Amplitude-magnitude pruning on the real heavy-hex topology")
    p.add_argument("--n", type=int, default=12, help="qubits in the patch")
    p.add_argument("--layers", type=int, default=3, help="CZ layer depth")
    p.add_argument("--thresholds", type=float, nargs="+",
                   default=[0.0, 0.001, 0.01, 0.1, 0.3, 0.5, 0.9])
    p.add_argument("--verify-only", action="store_true",
                   help="run Stage 1 only, skip the sweep")
    p.add_argument("--repeats", type=int, default=3,
                   help="timing repeats per threshold (lower for big patches)")
    args = p.parse_args()

    print()
    print("#" * 78)
    print("# EQCCM — pruning on the REAL heavy-hex topology (EXPERIMENTAL)")
    print("# Tests whether Addendum VI's result transfers off the banded family.")
    print("# banded_scaling*.py are untouched; no quantum time used.")
    print("#" * 78)
    print()

    if not verify_exact():
        print("Stage 1 failed — not proceeding to the threshold sweep.")
        return
    if args.verify_only:
        return

    rows = threshold_sweep(args.n, args.layers, args.thresholds,
                           repeats=args.repeats)
    interpret(rows, args.n)


if __name__ == "__main__":
    main()
