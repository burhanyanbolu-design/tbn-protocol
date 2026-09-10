"""
EQCCM — Fetch ibm_fez topology + calibration (METADATA ONLY)
=============================================================
Reads the device coupling map and error rates so the heavy-hex embedding
search can run against the real machine instead of a synthetic lattice.

IMPORTANT — this submits NO job and consumes NO quantum time. It only reads
backend metadata, which is free. This respects §17 of the technical record:
no further IBM job until the classical side shows a wall-clock effect.

It also never prints or stores your credentials — it uses the account already
saved locally by qiskit-ibm-runtime.

WHY THE CALIBRATION DATA MATTERS
The open question is "what contraction width is reachable at a depth where
the hardware still returns usable signal?" With real per-gate error rates we
can predict usable depth directly from the device instead of guessing:

    F(circuit) ~ prod over gates (1 - error_gate)

Measured anchors from the record, to sanity-check any prediction:
    depth 19      -> 2.1% to 7.7% observable error   (usable)
    depth 22-23   -> up to 32% observable error      (degraded)

Run this in the environment that has qiskit-ibm-runtime (C:\\qiskit):

    python demo/eqccm/fetch_fez_topology.py

Writes: data/fez_coupling.json

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

import json
import os
import statistics
import sys

BACKEND_NAME = os.environ.get("EQCCM_BACKEND", "ibm_fez")

# Resolve repo-root/data regardless of where this is run from
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
OUT_PATH = os.path.join(_REPO, "data", "fez_coupling.json")


def main() -> int:
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError:
        print("ERROR: qiskit-ibm-runtime not found in this environment.")
        print("Run this from the env that has it (per the record: C:\\qiskit).")
        return 1

    print(f"Connecting (metadata only, no job submitted)...")
    try:
        service = QiskitRuntimeService()
        backend = service.backend(BACKEND_NAME)
    except Exception as e:
        print(f"ERROR: could not reach backend '{BACKEND_NAME}': {e}")
        print("Check the saved account, or set EQCCM_BACKEND to another device.")
        return 1

    n_qubits = backend.num_qubits
    print(f"Connected: {BACKEND_NAME}, {n_qubits} qubits")

    # ── Coupling map (undirected, deduplicated) ──────────────────────
    try:
        raw_edges = backend.coupling_map.get_edges()
    except Exception as e:
        print(f"ERROR: no coupling map available: {e}")
        return 1

    edges = sorted({tuple(sorted(map(int, e))) for e in raw_edges})
    degrees = {q: 0 for q in range(n_qubits)}
    for a, b in edges:
        degrees[a] += 1
        degrees[b] += 1
    deg_vals = list(degrees.values())

    print(f"Coupling map: {len(edges)} undirected edges, "
          f"max degree {max(deg_vals)}, mean degree {statistics.mean(deg_vals):.2f}")

    # ── Calibration: per-gate errors, T1/T2, readout ─────────────────
    two_q_errors = {}
    one_q_errors = {}
    readout_errors = {}
    t1s, t2s = {}, {}

    # qiskit 1.x/2.x: prefer Target, fall back to properties()
    try:
        target = backend.target
        for op_name in target.operation_names:
            try:
                props = target[op_name]
            except Exception:
                continue
            for qargs, inst in (props or {}).items():
                if inst is None or qargs is None:
                    continue
                err = getattr(inst, "error", None)
                if err is None:
                    continue
                if len(qargs) == 2:
                    two_q_errors[f"{op_name}:{qargs[0]}_{qargs[1]}"] = float(err)
                elif len(qargs) == 1:
                    if op_name == "measure":
                        readout_errors[str(qargs[0])] = float(err)
                    else:
                        one_q_errors[f"{op_name}:{qargs[0]}"] = float(err)
    except Exception as e:
        print(f"(target read partial: {e})")

    try:
        for q in range(n_qubits):
            qp = backend.qubit_properties(q)
            if getattr(qp, "t1", None):
                t1s[str(q)] = float(qp.t1)
            if getattr(qp, "t2", None):
                t2s[str(q)] = float(qp.t2)
    except Exception as e:
        print(f"(qubit properties unavailable: {e})")

    # ── Report + predicted usable depth ──────────────────────────────
    payload = {
        "backend": BACKEND_NAME,
        "n_qubits": n_qubits,
        "edges": [list(e) for e in edges],
        "degree_histogram": {str(d): deg_vals.count(d) for d in sorted(set(deg_vals))},
        "two_qubit_errors": two_q_errors,
        "one_qubit_errors": one_q_errors,
        "readout_errors": readout_errors,
        "t1_seconds": t1s,
        "t2_seconds": t2s,
        "note": "Metadata only. No job was submitted and no quantum time used.",
    }

    if two_q_errors:
        vals = sorted(two_q_errors.values())
        med = statistics.median(vals)
        best = statistics.median(vals[: max(1, len(vals) // 4)])
        payload["two_qubit_error_median"] = med
        payload["two_qubit_error_best_quartile_median"] = best
        print(f"\nTwo-qubit gate error: median {med:.4%}, "
              f"best-quartile median {best:.4%}")

        print("\nPredicted circuit fidelity vs two-qubit gate count")
        print("(median-error qubits, then best-quartile — pick good qubits!)")
        print(f"{'2q gates':>9} {'F(median)':>11} {'F(best q1)':>11}")
        for g in (15, 30, 45, 60, 90, 120):
            f_med = (1.0 - med) ** g
            f_best = (1.0 - best) ** g
            print(f"{g:>9} {f_med:>11.3f} {f_best:>11.3f}")
        print("\nRecord anchors: 15 CZ gates at depth ~19 gave 2-8% observable")
        print("error; 30 CZ gates at depth ~22-23 degraded to ~32%. Use those")
        print("to calibrate which predicted fidelity is actually 'usable'.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\nWrote {OUT_PATH}")
    print("No job submitted. No quantum time consumed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
