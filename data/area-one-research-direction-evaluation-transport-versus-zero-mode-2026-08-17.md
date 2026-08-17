# Area One Research Direction Evaluation: Transport Line vs Zero-Mode Line

Date: 2026-08-17  
Status: **STRATEGY EVALUATION / NO NEW ARCHITECTURE AUTHORIZED**

## Question

Burhan asked whether the Aram-Harrow-inspired zero-mode framing has helped or distorted Area One, measured against the original T9-compatible transport candidate, and what the recorded numbers actually support.

This document evaluates existing recorded evidence only. It runs no simulation, proposes no new candidate, and creates no source, test, protocol, lock, held-out access or claim.

## The two lines are not measuring the same thing

**Transport line (Candidate 1, Candidate 2).** Discrete-time coined walk, candidate step `U_A=S C_G P O_t` against baseline `U_G=S C_G O_t`, equal oracle-query and iteration budgets, outcome = final-only marked-terminal probability lift, with a preregistered feasibility floor. This is an observable quantity and it is falsifiable.

**Zero-mode line (Candidates 3-6).** Continuous-time position-only surrogates. Outcomes = nullity, endpoint zero-projector elements, spectral gap bounds, equitable partitions, isomorphism classes. These are structural invariants. None of them is a transport probability.

Three consequences follow, and they are the core of the evaluation:

1. The zero-mode surrogate `H=A_torus+M` has **no coin space and no oracle**. Candidate 1's diagnosed harm lived specifically in the uniform coin and same-column geometry. A position-only Hamiltonian cannot represent a coin at all, so Candidates 3-6 were not studying the operator that actually failed.
2. Candidates 3-6 are **not executable by the validated T9 laboratory**. The frozen protocol, 210-test suite, pinned image, sharding, atomic publication and reconstructing verifier are all built around the coined-walk transport metric. Four candidates produced zero output that pipeline can consume.
3. In every case where the zero-mode line actually produced a zero mode, that mode was **common to the candidate and all controls by construction**. A quantity identical across candidate and controls cannot separate them under any analytic function of `H`. Candidate 3's balanced theorem proved this explicitly; Candidate 5's `c=B1` mode repeated it.

Point 3 is the most serious. The object we spent four candidates protecting was structurally incapable of being the source of a candidate/control effect.

## What the recorded transport numbers actually say

Candidate 1 T9, frozen protocol, development-only:

| grid | median lift | q10 |
|---|---:|---:|
| `s=2,R=6` | `+0.0019860027525655712` | `-0.020494795710597848` |
| `s=3,R=6` | `0` (exact) | `-0.016710087449200477` |
| `s=4,R=6` | `+0.00060741042468487674` | `-0.0096326823534248138` |

Aggregate median lift was **positive** at `+0.00060741042468487674`. The rejection was caused solely by the worst grid tail: min q10 `-0.020494795710597848` against the frozen floor `-0.02`.

- Shortfall: `0.000494795710597848`
- That is **2.47%** of the floor magnitude.

Candidate 1 was not falsified in direction. It failed a tail-risk gate by roughly two and a half percent, on one of three grids.
## Candidate 2 was quantitatively better and was stopped for method, not for effect

The Candidate 2 alternating-phase discovery point at `theta=pi/8`, `phi=pi/2` recorded:

- aggregate median lift `0.0011123773263897116`, which is **1.83x** Candidate 1's aggregate median;
- minimum q10 `-0.019471881637683139`, which is **inside** the `-0.02` floor with margin `0.000528118362316861`.

A later placement screen reached aggregate median `0.0011645284495637345`, **1.92x** Candidate 1.

So the strongest transport result on record both beats Candidate 1 and clears the floor that rejected Candidate 1. It was correctly not promoted, but the reasons were methodological, not evidential:

1. it was found on the same development cases used for the screen, so promoting it would be selection on discovery data;
2. `(s=3,R=6)` stayed at exact median zero;
3. the absolute effect is tiny, about `0.12` percentage points of probability;
4. it lacked matched controls and freshly predeclared validation configurations.

That decision was right. But it means the transport line was paused while *ahead*, not while failing.

## The harm is localized, which makes it a real target

The 31,104-record diagnostic on the failing `(s,R)=(2,6)` tail found:

- uniform coin states: `100/184` bottom-decile cases while being one sixth of the population, an enrichment of about **3.26x**;
- same-column journeys: `110/184`, about `59.8%`;
- row displacement three: `54/184`, about `29.3%`;
- the triple intersection: `18` cases, **zero** positive, median `-0.03971415772844654`, which is about **1.99x** the floor magnitude.

The failure is not diffuse noise. It is concentrated in an identifiable subpopulation. That is the most actionable single fact in the entire Area One record, and we left it unaddressed for four candidates.

## A cross-line structural signal nobody has tested

Width is `w=s+1`, so the declared grids are `w=3,4,5`.

- Transport line: median lift is exactly zero on `s=3`, i.e. `w=4`, in **both** Candidate 1 and Candidate 2.
- Zero-mode line: `w=4` is exactly the grid where the native torus `C_6 square C_4` is **bipartite**, since both factors are even. For `w=3` and `w=5` the row-zero horizontal cycle is odd. Native nullities also split as `0,0,1`.

So the one grid where the mechanism produces no median effect is the one grid whose native torus is bipartite. Two independent research lines flagged the same grid for different stated reasons.

This is a hypothesis consistent with recorded data, not a theorem: **the mechanism's median effect may vanish on even-width (bipartite) grids.** It is cheap to test and, if true, it explains the persistent zero and tells us the declared grid family itself is mixing two different regimes. Averaging across a bipartite and two non-bipartite grids would then be aggregating incomparable cases, which would also inflate the tail spread that rejected Candidate 1.

## Why the zero-mode gates kept failing: a genuine tension

The four no-gos are not four accidents. Candidates 3-6 demanded all of the following at once:

natural EOG structure, exact chirality, a unique endpoint-supported zero mode, a strict endpoint-representing quotient, fair but distinguishable controls, and no artificial gadgets.

Two of these pull against each other directly:

- a strict **equitable quotient** with both endpoints as distinct singletons needs many vertices to share identical weighted neighbourhoods, i.e. coarse local symmetry;
- **control distinguishability** needs the graph to be rigid, which generically drives endpoint-seeded refinement to discrete.

The recorded outcomes are exactly what that tension predicts:

- Candidate 3 obtained the quotient by *building the graph as a quotient lift* with large symmetric support cells, and then every matching permutation was endpoint-fixing isomorphic (label-degenerate). Breaking that required fingerprints `q_r=r+2` or pendant anchors, which are artificial by our own rule.
- Candidate 5 obtained rigidity and genuine separation of all 119 controls, and its refinement went fully discrete: no quotient.
- Candidate 6 obtained naturality and chirality, and native topology supplied `beta_1=7`: too many zero modes.

So "no gadgets" forbids the only route we have ever found to hold compressibility and distinguishability simultaneously. That is a structural reason to stop generating candidates in this family, not a reason to try Candidate 7.

## Verdict on the Harrow framing

Net effect on the T9 objective: **negative**, though not worthless.

Harmful:
- it substituted structural invariants for the measurable transport outcome;
- it discarded the coin and oracle, i.e. exactly where the recorded harm lives;
- it produced work the validated laboratory cannot run;
- it repeatedly protected a zero mode that is provably common to candidate and controls and therefore cannot separate them;
- it consumed the entire post-rejection effort while the diagnosed `(2,6)` tail cause went untouched.

Genuinely valuable:
- four rigorous no-go theorems that prevent wasted QPU time and would survive external scrutiny;
- proof that the direct natural EOG graph has no protected hierarchical zero-mode mechanism;
- the quotient/rigidity tension above, which is a reusable design filter;
- the held-out data remains completely untouched, with `lock_accesses=0` and `heldout_accesses=0`.

The framing was not stupid. It was a legitimate attempt to find a provable mechanism instead of a marginal numerical effect. But it answered a different question than the one T9 asks, and it was allowed to run for four candidates without that being stated plainly.

## Recommended direction

Return to the T9-compatible transport line. Reasons: it measures the actual objective, the validated laboratory already exists and only fits this metric, the failure margin is 2.47% on one tail, the cause is diagnosed and localized, and the holdout is intact.

Ordered and bounded:

1. **Test the width-parity hypothesis first.** It is cheap, uses development data only, and may explain both the exact-zero `s=3` median and the tail spread. If confirmed, the grid family and aggregation rule need revising before any new candidate is chosen.
2. **Target the diagnosed harm directly**, i.e. the uniform-coin plus same-column plus displacement-three subpopulation, rather than searching parameters globally.
3. **Apply one cheap universal filter to any future candidate before building it:** does the proposed discriminating quantity actually differ between candidate and controls? Candidate 3-balanced and Candidate 5 both failed this and were built anyway.
4. **Use fresh predeclared development configurations and matched controls.** Do not promote any point selected on the existing discovery cases, including the `1.83x` and `1.92x` alternating-phase points.
5. **Any redesigned operator needs a new protocol.** The frozen Candidate 1 protocol and its `-0.02` floor must not be edited, reinterpreted or lowered.
6. If the zero-mode idea is ever revived, it must be applied to the **actual coined operator including coin space and oracle**, not to a position-only surrogate, and it must state up front how the candidate and controls differ.

## Boundary

This document evaluates recorded results only. It establishes no transport effect, no separation, no advantage and no grant claim. Candidates 1 and 3-6 remain closed at their recorded dispositions; Candidate 2 remains unpromoted. Nothing here authorizes simulation, parameter search, tuning, T9, protocol change, lock finalization, held-out access, hardware execution, staging, commit or push.
