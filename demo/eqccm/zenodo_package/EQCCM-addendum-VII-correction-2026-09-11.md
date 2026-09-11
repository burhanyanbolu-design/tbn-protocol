# Addendum VII — Addendum VI is withdrawn: an absolute-error artefact

**A correction to "Addendum VI — Amplitude-magnitude pruning, and a seventh correction" (v2, 9 September 2026)**

Hardin AI Solutions · 11 September 2026
Classical only. No quantum time used; programme total remains 2 jobs, 40,960 shots.

---

## Summary

Addendum VI reported that amplitude-magnitude pruning reached ~10⁻⁴ accuracy
while keeping 0.01% of frontier configurations, roughly 14,000× faster than
exact contraction, and that accuracy *improved* as width grew.

**That result is withdrawn.** It is an artefact of reporting absolute error
without reference to the scale of the amplitudes being computed.

The pruned computation was not producing an approximate answer. It was
producing **essentially no answer at all** — and because the true amplitudes
are of order 10⁻⁴, an output of ~zero registers as a small *absolute* error.

Three specific claims fall:

- **"Accuracy ~1.5×10⁻⁴ at w=20 on 0.01% of configurations."** The figure
  reproduces exactly, but `max|exact|` at that point is 1.4685×10⁻⁴. Relative
  error is **99.4%**.
- **"Error improves monotonically with width, 24× from w=8 to w=20."** Absolute
  error was tracking the *amplitude scale*, which shrinks as width grows. It
  was never a measurement of approximation quality. Relative error is ~99% at
  every width tested.
- **"Error forms a plateau, not a cliff."** The plateau sits exactly at
  `abs_err = max|exact|` because the answer is ~0. It is the signature of total
  signal loss, not graceful degradation.

The Addendum VI consequence for the hardness argument is withdrawn with them.
Note the direction of that: the withdrawn addendum argued *against* this
programme's own hardness claim, so retracting it **restores** the 2^w position
rather than weakening it.

---

## How the error was found

Not by re-reading Addendum VI. It surfaced while doing the very thing Addendum
VI listed as most worth doing next: running the same sweep on the real
heavy-hex topology.

The heavy-hex sweep produced an error curve that flattened at 5.933×10⁻³ across
thresholds 0.1 to 0.9 — the same plateau shape Addendum VI had interpreted as
graceful degradation. Instead of accepting the plateau, its value was compared
against the amplitude scale:

```
max|reference|      = 5.932987e-03
"saturated error"   = 5.933e-03
```

Identical. The pruned computation was returning **exactly zero**. Addendum VI's
amplitudes are of order 10⁻⁴ and its quoted errors are of order 10⁻⁴ to
3×10⁻³ — the same order of magnitude. That prompted a direct audit.

---

## The audit

`addendum_vi_relative_error_audit.py` is **read-only**: it imports
`banded_scaling.py` and `banded_scaling_pruned.py` without modifying them, so
the published numbers remain reproducible exactly as published and this
correction can be checked independently against them.

Reproducing the published configuration (n=26, 5 open outputs, threshold 0.9):

| w | max\|exact\| | max\|pruned\| | abs_err | published | rel_err | verdict |
|---|---|---|---|---|---|---|
| 8 | 2.5561e-04 | 3.7253e-06 | 2.572e-04 | 3.550e-03 | 1.0061 | NO SIGNAL |
| 12 | 2.0784e-04 | 9.7074e-07 | 2.070e-04 | 3.312e-03 | 0.9959 | NO SIGNAL |
| 16 | 6.1955e-05 | 5.4330e-06 | 5.902e-05 | 7.188e-04 | 0.9527 | NO SIGNAL |
| **20** | **1.4685e-04** | **5.4330e-06** | **1.459e-04** | **1.459e-04** | **0.9938** | **NO SIGNAL** |

The w=20 row reproduces the published figure **exactly** — abs_err 1.459×10⁻⁴
with 104 configurations retained. This is the same computation, newly measured
against the amplitude scale.

Note that `abs_err ≈ max|exact|` on every row (ratios 1.006, 0.996, 0.953,
0.994). That is the arithmetic signature of an output near zero, and it is the
entire explanation of the withdrawn finding.

*(The w=8/12/16 rows do not reproduce the published absolute errors at n=26,
which means those rows used a different n that was not recorded. A parameter
specification gap, noted for completeness. It does not affect the conclusion:
every configuration tested, at n=20 and n=26, shows ~100% relative error.)*

### There is no usable operating point

The decisive check. Sweeping thresholds at n=26, w=12 (2^w = 4,096):

| threshold | abs_err | rel_err | kept | kept/2^w | verdict |
|---|---|---|---|---|---|
| 0.0 | 0.000e+00 | 0.0000 | 8,192 | 2.0000 | faithful |
| 1e-06 | 0.000e+00 | 0.0000 | 8,192 | 2.0000 | faithful |
| 1e-05 | 0.000e+00 | 0.0000 | 8,192 | 2.0000 | faithful |
| 1e-04 | 1.432e-09 | 0.0000 | 8,192 | 2.0000 | usable |
| 1e-03 | 9.851e-08 | 0.0005 | 8,192 | 2.0000 | usable |
| 1e-02 | 4.693e-06 | 0.0226 | 8,192 | 2.0000 | badly degraded |
| 0.05 | 4.859e-05 | 0.2338 | 8,190 | 1.9995 | badly degraded |
| 0.20 | 2.230e-04 | 1.0730 | 4,202 | 1.0259 | NO SIGNAL |
| 0.50 | 2.134e-04 | 1.0268 | 686 | 0.1675 | NO SIGNAL |
| 0.90 | 2.070e-04 | 0.9959 | 72 | 0.0176 | NO SIGNAL |

Every faithful row retains ~2.0 × 2^w — the full frontier plus the transient
doubling already documented in Addendum VI. **Pruning removes nothing there.**
Every row that removes a meaningful number of configurations has ~100% relative
error. The two regions do not overlap. Reproduced at w=16 with the same
structure.

The published "0.01% of configurations, ~14,000× faster" belongs entirely to
the no-signal region. **The speed/accuracy pairing does not exist.**

---

## The same test on real heavy-hex — an independent null result

`heavyhex_pruned.py`, on the cached real `ibm_fez` coupling map (156 qubits, 176
edges, metadata only, no quantum time).

Because heavy-hex is degree-3 and planar, a single CZ layer has trivial
treewidth; width is bought by **depth**. So the state carried is a *space-time*
frontier rather than a spatial cut — which is why the banded elimination order
does not transfer directly.

**Stage 1** (mechanism, threshold 0.0): exact against a dense statevector
reference at n=8/10/12 and depths 1/2/3 — `max_abs_err` from 6.9×10⁻¹⁸ to
4.9×10⁻¹⁷, five orders inside the 10⁻¹² bar. The mechanism is correct.

**Stage 2** (12 qubits/depth 3, and 16 qubits/depth 6/30 CZ gates): pruning
yields nothing.

- **Pruning does not compound.** After each prune, the single-qubit rotations
  regenerate the configurations just dropped — measured refill factor up to
  **2048×**. Peak memory stays at the full space regardless of threshold.
- At thresholds preserving any signal it is **slower** than not pruning
  (12.99 s vs 11.36 s baseline at n=16) — bookkeeping paid on a state that
  never shrinks.
- Signal destroyed outright at threshold ≥ 0.1 (output exactly zero).

**Structural reason, and the contrast with the banded family:** there, the
frontier *grew* incrementally and pruning suppressed its growth. Here every
qubit is rotated every layer, so the frontier is the full patch width at every
time boundary by construction. There is no growth for pruning to suppress.

A further cause, applicable to both families: readout fixes most qubits to a
specific output pattern, and a **global** magnitude cutoff is blind to which
configurations the caller actually needs. It will happily delete the entire set
matching the requested pattern.

---

## What stands, what falls

**Withdrawn**

- Addendum VI's accuracy figures and the monotone-improvement-with-width finding
- Addendum VI's consequence for the hardness argument, and its seventh
  correction. Approximate classical cost is **not** shown to be below 2^w by
  this evidence.

**Stands unchanged**

- **All exact results.** `banded_scaling.py` involves no pruning and is
  untouched. The 2^w scaling and measured exponent 1.984 are unaffected.
- Addendum VI's framing of the question, and its Stage 1 exactness check at
  threshold 0.0 (0.000e+00 agreement). The two-stage discipline worked as
  designed — it simply cannot catch an error in the *metric* used at Stage 2.

**Newly established, and narrow**

- Naive amplitude-magnitude pruning fails on **both** the banded family and
  real heavy-hex, destroying the answer wherever it saves work. The most
  obvious cheap classical attack on the 2^w figure is now tested and closed,
  with a reproducible script.
- **Scope limit, stated plainly:** only the *naive global-magnitude cutoff* was
  tested. Proper SVD / bond-dimension truncation is far stronger and remains
  **untested**. The honest claim is "the naive shortcut fails", **not** "no
  shortcut exists".

---

## The methodological lesson — now the actual result of this line of work

An accuracy claim must be quoted **relative** to the scale of the quantity being
computed, and an approximation must be shown to return a **non-zero** answer.

Reporting absolute error alone allowed an output of exactly zero to be published
as a 10⁻⁴ accuracy, and allowed shrinking amplitudes to be read as improving
precision.

This was foreseeable from inside the study. Addendum VI's own closing notes
observed that the original writeup had already shown *relative error on small
observables is misleading*. The risk was known, and applied in one direction but
not the other. It was not carried into the metric used to judge the result.

Both pruning scripts now report relative error alongside absolute, and raise an
explicit `DEAD` flag when the returned amplitudes are identically zero, so this
class of error cannot recur silently.

Corrections and self-limiting findings across the programme now total **eight**.

---

## Worth testing next (not done)

- **SVD / bond-dimension truncation** — the real adversary this line of work has
  not yet faced. Until it is tested, no hardness claim should treat the
  approximate regime as closed.
- Error behaviour on **observables** rather than raw amplitudes.
- A **readout-aware** pruning rule, since a global cutoff is provably blind to
  which configurations the caller needs.
- Level-dependent thresholds — still deferred, and now lower priority: the
  fixed-threshold result shows the failure is structural, not a matter of
  tuning.

---

## Reproducing this correction

```bash
python addendum_vi_relative_error_audit.py          # the correction
python addendum_vi_relative_error_audit.py --full   # adds the w=16 sweep
python heavyhex_pruned.py --verify-only             # Stage 1 on real heavy-hex
python heavyhex_pruned.py --n 12 --layers 3         # the null result
```

No IBM credentials required. No quantum time used.

---

*Hardin AI Solutions · AGPL-3.0 · Corrections to this record are published as
they are found, including when they withdraw our own results.*
