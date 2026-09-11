# We tried to find quantum advantage. Here are the eight things we got wrong.

A feasibility study of output-aware tensor-network contraction against real
quantum hardware.

**Author:** Burhan Yanbolu, Hardin AI Solutions
**Date:** September 2026 (v3 — withdraws Addendum VI, adds Addendum VII, 11 September 2026)
**IBM Quantum jobs:** `dadm3mjdd5gc73d7gvjg`, `dadm9qdnj4cs73ae2teg` (2 jobs, 40,960 shots total)

## ⚠️ What changed in v3 — Addendum VI is withdrawn

**If you read v2, the headline result in Addendum VI was wrong and is now
withdrawn. Read `EQCCM-addendum-VII-correction-2026-09-11.md`.**

Addendum VI (v2) claimed amplitude pruning reached ~10⁻⁴ accuracy while keeping
0.01% of configurations, ~14,000× faster, and that accuracy *improved* with
width. That was an artefact of reporting **absolute** error only.

The pruned computation was not approximating the answer — it was returning
essentially **no** answer. Because the true amplitudes are of order 10⁻⁴, an
output of ~zero registers as a small absolute error. The headline w=20 figure
reproduces exactly (1.459×10⁻⁴, 104 of 1,048,576 configurations), but
`max|exact|` at that point is 1.4685×10⁻⁴ — a relative error of **99.4%**.

Decisively: there is **no threshold that both saves work and stays correct**.
Where pruning is faithful it retains the full frontier and removes nothing;
where it removes anything meaningful the relative error is ~100%. The two
regions do not overlap.

The same test on real heavy-hex is an independent null result: pruning does not
compound there (the rotations regenerate what was dropped, refill up to 2048×),
and at usable thresholds it is *slower* than not pruning.

**Direction of the correction, worth being clear about:** Addendum VI argued
*against* this study's own hardness claim. Withdrawing it **restores** the 2^w
position rather than weakening it. What is newly established is narrow but real
— the naive magnitude cutoff fails on both topologies tested, so the most
obvious cheap classical attack on 2^w is now closed with a reproducible script.

**Scope limit:** only the *naive global-magnitude* cutoff was tested. Proper
SVD / bond-dimension truncation is far stronger and remains **untested**. The
honest claim is "the naive shortcut fails", not "no shortcut exists".

## Contents

**Read in this order:**

- `EQCCM-feasibility-writeup-2026-09-05.md` — the full study (start here)
- `EQCCM-addendum-VII-correction-2026-09-11.md` — **new in v3**: the correction; read before Addendum VI
- `EQCCM-addendum-VI-pruning-2026-09-09.md` — **WITHDRAWN**, preserved unedited so the original claim stays reproducible and the correction independently checkable

**Code:**

- `banded_scaling.py` — correctness vs statevector; the 2^w width sweep (no pruning; unaffected by the correction)
- `banded_scaling_pruned.py` — pruned contraction (imports the above; does not modify it)
- `addendum_vi_relative_error_audit.py` — **new in v3**: the correction, read-only against the two files above
- `heavyhex_pruned.py` — **new in v3**: the same test on real heavy-hex; space-time frontier contraction
- `fez_coupling.json` — **new in v3**: cached `ibm_fez` coupling map so the above runs offline
- `fetch_fez_topology.py` — device coupling map + calibration (metadata only, no IBM credentials required)
- `heavyhex_width_search.py` — depth vs optimised contraction width on real topology
- `topology_comparison.py` — width-per-gate across seven topologies
- `sliced_cost_model.py` — sliced FLOP cost vs four adversary models
- `error_vs_depth.py` — mirror benchmark on hardware
- `analyse_error_vs_depth.py` — the corrected two-parameter fit
- `error_suppression_test.py` — dynamical decoupling + twirling comparison

## What this is

An honest, evidence-backed feasibility study testing whether quantum circuits
can be built where exact classical simulation cost grows much faster than the
physical circuit depth needed to run them. The answer, on hardware available
today, is no — and reaching that answer required correcting our own conclusions
eight times, including withdrawing an entire addendum three days after
publishing it.

## What this is NOT

- **No quantum advantage, and no claim to it.**
- **No novel algorithm.** Frontier contraction is variable elimination, which is
  textbook. Multi-amplitude reuse is established in the literature.
  Amplitude-magnitude pruning is standard tensor-network practice — and as of
  v3, it is also shown not to work on these families.
- **No verified large-width result.** Any serious attempt at widths beyond ~50
  needs a verification strategy designed in from the start.
- **No physical interpretation of the pruning geometry.** The coordinates are
  abstract state-space magnitudes, not physical positions.
- All *exact* classical cost figures are upper bounds favourable to the quantum
  side. v2 claimed the approximate cost was far lower; **v3 withdraws that.**

## The methodological lesson

An accuracy claim must be quoted **relative** to the scale of the quantity being
computed, and an approximation must be shown to return a **non-zero** answer.
Absolute error alone let an output of exactly zero be published as a 10⁻⁴
accuracy, and let shrinking amplitudes be read as improving precision.

Both pruning scripts now report relative error alongside absolute and raise an
explicit `DEAD` flag when the output is identically zero.

## Reproducing this

```bash
python addendum_vi_relative_error_audit.py          # the v3 correction
python addendum_vi_relative_error_audit.py --full   # adds the w=16 sweep
python heavyhex_pruned.py --verify-only             # Stage 1 on real heavy-hex
python heavyhex_pruned.py --n 12 --layers 3         # the heavy-hex null result
python banded_scaling.py                            # the unaffected exact results
```

These require only `numpy` and run offline — no IBM credentials, no quantum time.

Scripts that touch hardware (`error_vs_depth.py`, `error_suppression_test.py`)
require your own IBM Quantum credentials and will submit real jobs — do not run
these without understanding the cost and quota implications.

## License

AGPL-3.0. Released for reproducibility and citation. See the writeup for full
technical detail and methodology, and Addendum VII for the correction history.
