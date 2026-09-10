# We tried to find quantum advantage. Here are the six things we got wrong.

**A feasibility study of output-aware tensor-network contraction against real quantum hardware.**

Hardin AI Solutions · September 2026
IBM Quantum jobs `dadm3mjdd5gc73d7gvjg`, `dadm9qdnj4cs73ae2teg` · 2 jobs, 40,960 shots total

---

## Summary

We set out to test whether quantum circuits could be built where exact classical
simulation cost grows much faster than the physical circuit depth needed to run them.
The honest answer is no — not on any hardware available today. But getting to that
answer required correcting our own conclusions six times, and the corrections are more
useful than the result.

What we can now state with measurements behind it:

- Classical contraction cost scales as 2^w in practice, with a measured exponent of
  **1.984** over ten consecutive doublings of width.
- Effective two-qubit error on IBM's Heron architecture is **gate-local at 0.845%**,
  stable across an 11.6× span in gate count and reproducible across two independent
  jobs with different control settings.
- **Memory is not a constraint.** Slicing removes it for a 1.00–3.18× FLOP penalty,
  and slices parallelise perfectly.
- **Connectivity degree, not planarity, is the dominant topological lever.**
- Standard error suppression — dynamical decoupling plus twirling — **made things
  worse**, costing 8–14% net fidelity on this circuit class.
- Achievable hardness is capped by 2^n, so **qubit count is a hard ceiling** that no
  amount of circuit cleverness or gate quality can raise.

Three simultaneous hardware requirements follow from this, and no currently available
machine satisfies all three.

---

## What we were testing

The method began as an "elastic box" idea: expand only the part of a computation
currently needed, collapse what's finished. Formalised, that is variable elimination
with an active frontier — for a graph *G* and elimination order π, you carry only the
variables still connecting processed to unprocessed regions. A frontier of *w* binary
variables means at most 2^w table entries.

The circuit family was two layers of single-qubit RY rotations separated by a
graph-defined CZ layer, which gives a deliberately modifiable interaction graph while
remaining exactly simulable as a reference.

The hypothesis: find graphs where 2^w grows fast while physical depth stays shallow
enough to execute on real hardware.

---

## The six corrections

### 1. Our null result was a cache artifact

An early experiment increased the contraction-cost metric by 42× and measured only a
**3.5%** wall-clock change. We took that as evidence the cost model was wrong.

It wasn't. At 16 qubits with frontier width 5, the state table is a few hundred bytes
and lives entirely in L1 cache, so we were timing Python dispatch and memory setup,
not arithmetic. Re-running at 30 qubits across widths 12–22 produced clean scaling at
every step:

| band | peak table | median runtime | ratio |
|---|---|---|---|
| 12 | 0.52 MB | 0.0153 s | — |
| 14 | 2.10 MB | 0.0500 s | 1.87 |
| 16 | 8.39 MB | 0.2266 s | 2.11 |
| 18 | 33.55 MB | 1.1169 s | 2.06 |
| 20 | 134.22 MB | 4.1650 s | 1.73 |
| 22 | 536.87 MB | 14.4223 s | 1.81 |

945× growth over ten doublings — a fitted exponent of **1.984** against a theoretical
2.000. The knee is at band 13, around a 1 MB table. Below it, no performance claim
about this class of computation means anything.

**Lesson:** if your working set fits in cache, you are not measuring your algorithm.

### 2. There was no memory wall

From the table above we concluded memory was the binding constraint — band 27 on a
32 GB machine, and an absurd 37 exabytes at width 58.

Wrong, because it assumed dense unsliced contraction. Slicing fixes a subset of
indices and contracts each assignment separately, cutting peak memory by 2^k for k
sliced indices. Measured overhead across every case we tested: **1.00× to 3.18×
FLOPs**. One probe reduced width 19 → 12 for an 8% FLOP penalty.

Worse for the hardness case: slices are independent, so the computation is
embarrassingly parallel and a cluster attacks it near-linearly. This is exactly how
the classical rebuttals to Google's 53-qubit claim moved the estimate from 10,000
years to days.

**Lesson:** hardness must be quoted as total FLOPs against a named adversary. Width
and single-machine memory are not hardness measures.

### 3. We overstated a depth penalty by using the wrong metric

Doubling the entangling layer appeared to degrade agreement badly — up to 32% relative
error on one observable. But relative error on a Pauli expectation is misleading when
the ideal value is small. Converting to effective fidelity, ⟨P⟩measured / ⟨P⟩ideal:

| gates | X₀ | X₀X₁ | Z₀X₁ | F_eff |
|---|---|---|---|---|
| 15 | 0.923 | — | 0.933 | ≈0.93 |
| 30 | 0.822 | 0.434 | 0.681 | ≈0.75 |

The 0.434 outlier isn't decoherence at all. That observable had an ideal value of
0.0267 against a ±0.01 shot-noise floor at 10k shots — it was sampling-limited. Its
"57% error" was mostly statistics.

So the real cost was F 0.93 → 0.75, not a 4× collapse.

**Lesson:** under depolarizing-type noise, relative error on ⟨P⟩ is approximately
1−F regardless of the observable's magnitude. Report effective fidelity, and always
state the shot-noise floor beside it.

### 4. Apparent depth-dependent error growth didn't survive more data

Two data points suggested effective error grew with depth: 0.48% per gate at 15 gates,
0.96% at 30. If real, that would have killed any extrapolation to the several-hundred-gate
circuits we cared about.

It doesn't survive a five-point measurement on native edges with no SWAP routing. The
original two points were confounded by routing overhead and by correction #5 below.

### 5. Our own mirror-circuit fit was wrong

We measured fidelity using mirror circuits — apply U then U†, so the ideal output is
exactly |0…0⟩ with probability 1. No classical simulation needed at any size, and the
signal is maximal. Randomised RY angles between layers suppress coherent cancellation.

On a 20-qubit patch of `ibm_fez` chosen by following lowest-error edges (mean two-qubit
error 0.262%):

| 2q gates | P(0…0) | shot err |
|---|---|---|
| 18 | 0.6313 | 0.0075 |
| 34 | 0.5679 | 0.0077 |
| 56 | 0.4719 | 0.0078 |
| 110 | 0.2732 | 0.0070 |
| 208 | 0.1299 | 0.0053 |

Our first analysis fitted `P = (1−ε)^G` and reported ε *falling* from 2.52% to 0.98%,
then flagged it as unphysical and blamed coherent error cancellation.

The model was wrong, not the data. A mirror circuit carries a penalty independent of
gate count — readout error on every qubit, plus single-qubit gate error. Dividing a
constant penalty by a growing gate count manufactures exactly that spurious decline.

The correct two-parameter model separates them:

```
P(0…0) = A · (1 − ε)^G
```

Fitted: **A = 0.7409**, **ε = 0.845%**. Maximum residual 2.5σ across an 11.6× span
in gate count.

And the fit validates itself rather than merely fitting: A = 0.7409 over 20 qubits
implies per-qubit readout error of **1.49%**, against IBM Heron's published 1–2%. The
constant term recovered from the data independently matches the device specification.

**Lesson:** always separate state-prep-and-measurement error from gate-scaling error.
A one-parameter fit to mirror data will *always* appear to show error improving with
depth.

### 6. Error suppression made it worse

Effective error of 0.845% is 4.1× the device's own nominal best-quartile figure of
0.204%. We argued that gap was crosstalk, idle decoherence and readout — not gate
quality — and therefore fixable with control rather than new hardware.

We tested it: identical circuits, same seed, plus dynamical decoupling (XpXm), Pauli
gate twirling (32 randomizations), and measurement twirling.

Every point got worse.

| | baseline | suppressed | change |
|---|---|---|---|
| SPAM floor A | 0.7409 | 0.6792 | −8.3% |
| 2q error ε | 0.845% | 0.860% | +1.8% |

Net fidelity fell 1–14% across the sweep. Why: twirling *inserts* single-qubit gates
around every two-qubit gate — several hundred extra pulses at 208 gates, each with its
own error. Measurement twirling adds 20 X gates immediately before readout, directly
degrading A. And DD protects *idle* qubits, but these circuits keep nearly everything
busy, so its added pulses were mostly pure cost.

An honest caveat against ourselves: mirror circuits benefit from coherent cancellation
by construction, and twirling destroys coherence, so this benchmark is structurally
unfavourable to twirling. But ε moved only 1.8% — if coherent cancellation were a large
component of the baseline, removing it would have raised ε substantially. It didn't.

**Unintended benefit:** ε measured 0.845% and 0.860% in two independent jobs under very
different control settings. That stability validates the error model more strongly than
one job could. The number is robust; only our explanation was wrong.

---

## What we established

**Connectivity degree dominates planarity.** Measuring width bought per gate spent
(η = W/G) across topologies at n≈100:

| topology | degree | planar | η |
|---|---|---|---|
| degree-8 random | 8 | no | 0.2156 |
| random 4-regular | 4 | no | 0.1750 |
| random 3-regular | 3 | no | 0.1081 |
| heavy-hex (real Fez) | 3 | yes | 0.0732 |
| square grid | 4 | yes | 0.0667 |

We expected de-planarising at fixed degree to give ~4×. It gives 1.5×. Degree is the
lever.

**Heavy-hex cannot be simultaneously hard and executable.** On the real 156-qubit
coupling map, the deepest circuit that still returns signal (F ≥ 0.05) has optimised
contraction width 6 — under a millisecond of classical work. Reaching two hours of
classical cost takes 822 gates, where fidelity is 3×10⁻⁴.

**Qubit count is a hard ceiling.** Contraction width saturates at roughly n, so maximum
achievable classical cost is about G·2ⁿ regardless of connectivity or fidelity. Against
a 1000-GPU adversary at 30 days, that requires **n ≳ 65–70**.

---

## The three requirements, and the scorecard

1. **n ≥ 65–70 qubits** — sets the ceiling on achievable hardness
2. **degree ≥ 4, ideally all-to-all** — determines whether the ceiling is reachable at
   feasible gate count
3. **effective error ≤ 0.1% at ~1750 gates** — determines whether signal survives

| device | qubits | connectivity | gate error |
|---|---|---|---|
| IBM Fez | 156 ✓ | planar deg-3 ✗ | 0.845% measured ✗ |
| Quantinuum H2 | 56 ✗ | all-to-all ✓ | 0.06% ✓ |
| IonQ Forte | 36 ✗ | all-to-all ✓ | ~0.4% ~ |

IBM satisfies one. Quantinuum satisfies two and is short only on qubit count — which is
the quantity hardware roadmaps deliver, unlike topology, fixed at fabrication.

Note on vendor claims: 56 all-to-all qubits at 2000 gates is roughly four hours on a
serious cluster by the accounting above. "Beyond classical simulation" claims refer to
specific algorithms against specific classical methods, not to a general bound.

---

## What this does not show

- **No quantum advantage, and no claim to it.**
- **No novel algorithm.** Frontier contraction is variable elimination, which is
  textbook. Multi-amplitude reuse is established in the literature. The banded-graph
  treewidth result is standard graph theory.
- **No verified large-width result.** At width beyond ~50 the ideal amplitudes cannot
  be computed classically — that is the point of the regime. Any serious attempt needs
  a verification strategy (patch or elided circuits, extrapolated from verifiable
  sizes) designed in from the start.
- **All classical cost figures are upper bounds favourable to the quantum side.** We
  used cotengra's `greedy`, a weak optimiser. Stronger presets lower adversary cost
  further.

---

## Reproducing this

Scripts, with no IBM credentials required for the classical parts:

| script | what it does |
|---|---|
| `banded_scaling.py` | correctness vs statevector; the 2^w width sweep |
| `fetch_fez_topology.py` | device coupling map + calibration (metadata only) |
| `heavyhex_width_search.py` | depth vs optimised contraction width on real topology |
| `topology_comparison.py` | width-per-gate across seven topologies |
| `sliced_cost_model.py` | sliced FLOP cost vs four adversary models |
| `error_vs_depth.py` | mirror benchmark on hardware |
| `analyse_error_vs_depth.py` | the corrected two-parameter fit |
| `error_suppression_test.py` | DD + twirling comparison |

The banded family used throughout is `E(n,w) = {(i,j) : i < j ≤ min(n−1, i+w)}`, whose
treewidth is exactly *w* — provable in both directions, which is what makes width a
dial rather than a lottery.

---

## Closing

The programme's structural assumptions hold up. Classical cost scales as claimed, error
does not blow up with depth, and a concrete circuit exists — degree-8 connectivity,
depth 10, 395 gates, contraction width 108 — that would be classically intractable and
hardware-executable at roughly 8 million shots, which is fewer samples than Google used
for Sycamore.

What is missing is not theory. It is a device with ~70 all-to-all qubits at ~0.06%
error. That is a specification, not a research direction, and it is close enough to
current roadmaps to be worth writing down.

We also now know which plausible shortcut does not work, which has independent value:
you cannot close a 4× effective-error gap with dynamical decoupling and twirling on
this circuit class. That cost us one job to learn and might save someone else the same.

*Corrections welcome. Full technical record, including all raw data and the six
corrections in their original form, available on request.*
