# Addendum VI — Amplitude-magnitude pruning, and a seventh correction

> # ⚠️ WITHDRAWN — 11 September 2026
>
> **Do not cite any accuracy figure in this document.** Read
> `EQCCM-addendum-VII-correction-2026-09-11.md` first.
>
> The accuracy result below is an **artefact of reporting absolute error
> only**. The quoted errors are approximately equal to the largest amplitude
> being computed — about **100% relative error**. The pruned computation
> returns essentially no signal. Specifically, the headline w=20 figure
> (1.459×10⁻⁴ on 104 of 1,048,576 configurations) reproduces exactly, but
> `max|exact|` at that point is 1.4685×10⁻⁴, making the relative error 99.4%.
>
> Consequently withdrawn: the "error improves monotonically with width"
> finding (absolute error was tracking the shrinking amplitude scale, not
> approximation quality), the "plateau not a cliff" reading (that plateau is
> the signature of total signal loss), and the seventh correction regarding
> the hardness argument.
>
> Still standing: the framing of the question, and the Stage 1 exactness
> check at threshold 0.0. The exact results in `banded_scaling.py` involve no
> pruning and are entirely unaffected.
>
> This document is preserved **unedited** so the original claim remains
> reproducible and the correction independently checkable:
> ```
> python addendum_vi_relative_error_audit.py
> ```

**A follow-up to "We tried to find quantum advantage. Here are the six things we got wrong."**

Hardin AI Solutions · 9 September 2026
Classical only. No quantum time used; programme total remains 2 jobs, 40,960 shots.

---

## Summary

The original study measured exact classical contraction cost scaling as 2^w
(fitted exponent 1.984 over ten doublings) and used that as the classical
hardness figure.

This addendum tests what happens when the frontier table is pruned — when
configurations whose amplitude magnitude is small relative to the largest
active one are dropped before the next expansion step. The result changes a
conclusion in the original study, and not in our favour:

- Error forms a **plateau, not a cliff** — reproduced independently at four widths.
- Error **improves monotonically as width grows**, by 24× from w=8 to w=20,
  while the retained fraction of configurations falls from 8.6% to 0.01%.
- At w=20, keeping **104 of 1,048,576 configurations (0.01%)** gave an answer
  accurate to **1.5×10⁻⁴**, in 0.009 s versus 129 s for the gentlest pruning level.

**The consequence, stated against our own case:** the 2^w figure describes the
*exact* regime only. An adversary willing to accept ~10⁻⁴ error does not pay
2^w for this circuit family. Hardness must therefore be quoted against a named
**accuracy target**, not only a width. This extends the original study's §23
lesson — that hardness must be quoted as FLOPs against a named adversary —
rather than contradicting it.

This brings the study's documented self-corrections to **seven**.

---

## Where this fits

The original writeup's "what this does not show" section stated that no
verified large-width result exists, because beyond width ~50 the ideal
amplitudes cannot be computed classically, and that any serious attempt needs a
verification strategy designed in from the start.

This addendum tests a candidate for that gap — and makes the requirement more
urgent rather than discharging it, since the approximate path now looks more
capable than the original study assumed.

## Origin of the idea

A geometric intuition: that a "zoom region" can be characterised by direction,
distance and area, and that regions falling outside a permitted boundary need
not be expanded further. Reduced to something testable against the existing
code, that becomes amplitude-magnitude truncation.

**The technique is not novel.** Amplitude and SVD truncation are standard
tensor-network and MPS/DMRG practice. The question addressed here is narrower:
does the banded family `E(n,w) = {(i,j) : i < j ≤ min(n−1, i+w)}` tolerate it,
and in which direction does that tolerance move with width?

## Method

`banded_scaling_pruned.py` is a separate module. `banded_scaling.py` is
imported, not modified — every exact result in the original study is unaffected.

The active frontier is held as a dictionary mapping frontier configuration to a
value array over the open output axes, rather than as a dense array. Pruning
removes dictionary keys outright. A dense array cannot demonstrate an honest
saving here, because zeroed floats still occupy the same allocation.

The contraction loop becomes: **magnify → use (CZ phases) → collapse → prune.**

### Two-stage verification

**Stage 1 — mechanism, not idea.** Run with threshold = 0.0, pruning nothing.
This isolates "is the sparse re-encoding correct" from "does pruning preserve
accuracy". Result: `max_abs_err` against the exact contraction was **0.000e+00**
at n=12, bands 2/3/5/7 — exact agreement, not merely within tolerance. Stage 2
proceeds only if Stage 1 passes.

**Stage 2 — the experiment.** Sweep thresholds above zero, comparing against
the exact contraction as ground truth on reconstruction error, retained
configurations versus 2^w, wall-clock time and approximate memory.

Fixed thresholds throughout. Level-dependent thresholding was deliberately
deferred so that any anomaly would have one cause rather than two.

## Results

Five open outputs throughout, so 32 amplitudes per run.

### At maximum tested pruning (threshold 0.9)

| width | error | configs kept | fraction of 2^w | wall-clock |
|---|---|---|---|---|
| w=8 | 3.550×10⁻³ | 22 | 8.6% | 0.0016 s |
| w=12 | 3.312×10⁻³ | 22 | 0.5% | 0.0010 s |
| w=16 | 7.188×10⁻⁴ | 74 | 0.1% | 0.0081 s |
| w=20 | 1.459×10⁻⁴ | 104 | 0.01% | 0.0092 s |

### Full w=20 sweep (n=26)

| threshold | error | configs kept | fraction | time | mem ratio |
|---|---|---|---|---|---|
| 0.05 | 5.212×10⁻⁵ | 1,432,558 | 136.6% | 128.93 s | 0.683 |
| 0.20 | 1.116×10⁻⁴ | 187,106 | 17.8% | 15.95 s | 0.089 |
| 0.50 | 1.472×10⁻⁴ | 14,260 | 1.4% | 0.90 s | 0.007 |
| 0.90 | 1.459×10⁻⁴ | 104 | 0.01% | 0.009 s | 0.000 |

Fractions above 100% are an artefact of measuring peak configurations
immediately after a magnify step, before the matching collapse — the same
transient doubling the exact algorithm's own peak accounting shows. Not a
pruning effect.

## What this does not show

- **No claim of novelty.** Amplitude truncation is textbook.
- **No verified result beyond w=20.** Every figure above is checked against the
  exact contraction, which is only possible where exact contraction is
  feasible. The monotone trend suggests continued improvement past w=20; that
  is extrapolation, not measurement.
- **One circuit family only.** Heavy-hex, random regular and the other
  topologies from the original study are untested under pruning.
- **No threshold at any width reached 10⁻⁶.** This is a ~10⁻⁴-accuracy method,
  not free precision.
- **Level-dependent thresholding untested** (deferred by design).
- **Memory figures are approximate.** Python dictionary overhead is not fully
  modelled, so the memory ratio column understates true overhead.
- **No physical interpretation.** The originating intuition used spatial
  language — area, distance, direction — but every coordinate here is an
  abstract frontier-configuration magnitude in the algorithm's own state space.
  Nothing in this addendum measures physical position, electron capacity, or
  any real-world area, and no experimental mapping to physical position was
  attempted.

## Worth testing next, not done

- Level-dependent thresholds, per the originating `A_{L+1} = A_L / s²` idea
- The same sweep on the original study's other topologies, especially real heavy-hex
- Whether the monotone trend survives an independent verification strategy
  (patch or elided circuits) at widths where exact contraction fails
- Error behaviour on observables rather than raw amplitudes, since the original
  study already showed relative error on small observables is misleading

## Reproducing

```
python banded_scaling_pruned.py --verify-only          # Stage 1 only
python banded_scaling_pruned.py --n 18 --w 12          # default sweep
python banded_scaling_pruned.py --n 26 --w 20 --thresholds 0.05 0.2 0.5 0.9
```

No IBM credentials required. `banded_scaling.py` must be in the same directory,
as it is imported for the exact reference implementation.

---

*Corrections welcome. This addendum documents a finding that weakens the
classical-hardness side of the original study's ledger, recorded for the same
reason the original six corrections were: the wrong turns are more useful than
a clean result.*
