# Area One Research Design: Overlap-Pair Scatterer

Generated: 2026-08-15  
Status: APPROVED WITH MANDATORY BLOCKERS  
Mode: Research  
Area: One only  

## Decision summary

Area One verifier work is frozen at version 0.1.0 while this scientific question is investigated. The selected direction is an abstract quantum transition operator, not hardware. Its primary outcome is final-only marked-terminal probability under a fixed outer-iteration and oracle-query budget.

The candidate is a minimal two-state unitary coupling between the `R-1` genuine EOG coordinate pairs that share a displayed label at adjacent non-wrapping row boundaries. The experiment is designed to reject the mechanism if any gain is absent, concentrated in selected grids, or explained equally well by preregistered cardinality- and tuning-matched controls.

## Problem statement

The existing Area One Grover walk is mathematically valid but contains no EOG-specific dynamics. Full EOG coordinates are exactly isomorphic to ordinary unique node IDs, and displayed labels are metadata. A scientific contribution therefore requires an explicit operator term whose behavior can be tested independently of the notation.

The research question is:

> With identical marked-terminal information, oracle-query count, initial states, measurement schedule, base grid, and outer-iteration count, does a fixed overlap-pair scattering layer improve final-only terminal probability over standard Grover spatial search on held-out configurations?

This is a performance ablation, not an efficiency comparison: the candidate adds pair rotations that the Grover comparator does not execute. A second question separates the declared adjacent overlap matching from other cardinality-matched pairings:

> At the same development-only tuning budget and logical pair-rotation count, does the declared EOG-derived matching outperform the exact preregistered matching-control set?

## Locked premises

1. This is an abstract quantum-algorithm experiment. It makes no electrical-device, pulse, gate-hardware, or electron-control claim.
2. The primary outcome is terminal probability after one final measurement and a fixed number of unitary steps.
3. The terminal is supplied through the same phase oracle to every quantum comparator.
4. Starts, terminals, grid sizes, initial coin states, horizons, candidate parameters, controls, and success thresholds are declared before held-out evaluation.
5. Ordinary indexing can represent every tested operator exactly. Any contribution must come from interaction structure or measured performance, never from labels themselves.
6. Logical pair rotations, oracle calls, coin applications, and shifts are reported separately. They are not physical gate counts.
## Mathematical definition

For step size `s >= 1` and `R >= 2` rows, define width `W=s+1`, position set

```text
V = {(r,c) : 0 <= r < R, 0 <= c <= s},
```

and direction order `(UP, RIGHT, DOWN, LEFT)=(0,1,2,3)`. The Hilbert basis is `|r,c,d>`. The displayed label `G_s(r,c)=sr+c` is metadata, not state identity.

The normalized Grover coin state and coin are

```text
|u> = (|UP>+|RIGHT>+|DOWN>+|LEFT>)/2,
C_G = 2|u><u| - I.
```

The periodic flip-flop shift is executable as

```text
S|r,c,UP>    = |(r-1) mod R,c,DOWN>
S|r,c,RIGHT> = |r,(c+1) mod W,LEFT>
S|r,c,DOWN>  = |(r+1) mod R,c,UP>
S|r,c,LEFT>  = |r,(c-1) mod W,RIGHT>.
```

Only genuine non-wrapping EOG overlaps are coupled. For `r=0,...,R-2`, define

```text
p_r = (r,s),
q_r = (r+1,0),
G_s(p_r)=G_s(q_r)=s(r+1).
```

There is no pair between `(R-1,s)` and `(0,0)` because their ordinary EOG labels differ. The `R-1` declared pairs are disjoint and cover `2(R-1)` position states.

For each direction `d`, the pair layer acts as

```text
P(θ,φ)|p_r,d> = cos(θ)|p_r,d> + exp(iφ)sin(θ)|q_r,d>
P(θ,φ)|q_r,d> = -exp(-iφ)sin(θ)|p_r,d> + cos(θ)|q_r,d>.
```

In ordered basis `(|p_r,d>,|q_r,d>)`, its block is

```text
[[cos(θ), -exp(-iφ)sin(θ)],
 [exp(iφ)sin(θ), cos(θ)]].
```

All other basis states are unchanged. Each block is unitary; disjoint block composition makes the complete `P(θ,φ)` unitary. `θ=0` is identity.

For marked terminal coordinate `t`, define

```text
O_t = I - 2Π_t,
Π_t = sum_d |t,d><t,d|.
```

The candidate and baseline steps are

```text
U_A(θ,φ,t) = S C_G P(θ,φ) O_t,
U_G(t)     = S C_G O_t.
```

Operators act right-to-left. One candidate iteration executes exactly:

```text
state = terminal_phase_oracle(state, t)
state = overlap_pair_scatter(state, θ, φ)
state = grover_coin(state)
state = periodic_flip_flop_shift(state)
```

Because `P` and `O_t` need not commute when `t` is paired, this order is immutable. Sequential application must match an independently constructed complete matrix on random normalized states and on terminals at `p_r`, `q_r`, and an unpaired interior coordinate.

For micro-case `x=(s,R,start,t,coin)`, initialize

```text
|ψ_0(x)> = |start> tensor |coin>.
```

After `T(N)` iterations, with no intermediate projection, terminal probability is

```text
P_t(T|x) = sum_d |<t,d|ψ_T(x)>|^2,
N = R(s+1),
T(N) = ceil(2 sqrt(N)).
```

Secondary sensitivity is reported at `ceil(sqrt(N))` and `ceil(4 sqrt(N))`; it cannot replace the primary result.

## Candidate parameters and lock discipline

The complete parameter grid is

```text
θ in {π/16, π/8, 3π/16, π/4, 3π/8, π/2}
φ in {0, π/2, π, 3π/2}.
```

`θ=0` is an identity pair layer, not a candidate. For method family `j` (candidate or control), parameter `a=(θ,φ)`, development grid `g`, and its micro-cases `x`, define

```text
δ[j,a,g,x] = P[j,a](T|g,x) - P_G(T|g,x)
m[j,a,g]   = median_x δ[j,a,g,x]
q[j,a,g]   = quantile_0.10_x δ[j,a,g,x]
A[j,a]     = median_g m[j,a,g]
F[j,a]     = 1 if every q[j,a,g] >= -0.02, otherwise 0.
```

Every method family selects one parameter by descending lexicographic order of

```text
(F[j,a], min_g q[j,a,g], A[j,a], -θ, -φ).
```

This total ordering always selects a parameter and gives every family the same 24-choice development budget against the same Grover baseline. If the candidate’s winner has `F=0`, the candidate is rejected before lock and no held-out outcomes are computed. Infeasible controls remain in the fixed 100-control set with their best ordered parameter; they are never dropped. A conditional same-parameter control analysis is out of scope for this stage.

Before held-out execution, one canonical lock manifest records and hashes:

- this protocol file and its independently copied `.sha256` approval anchor;
- Git `HEAD`, complete `git diff` hash, and SHA-256 for every transitive source file, all mandatory;
- parameter grid, selection code hash, and every selected parameter pair;
- exact matching-control generator version and generated manifests;
- aggregation and quantile code hashes;
- thresholds, tolerances, horizons, initial states, and decision epsilon;
- runtime, interpreter, research-dependency lock, platform, and numerical-backend metadata;
- the one permitted basis-column linearity reduction described below.

Held-out code must refuse to expose results unless the lock verifies. Any outcome-dependent change invalidates the held-out set; continuing requires a newly declared holdout rather than rerunning this one.

## Configuration sets

### Development configurations

```text
s in {2,3,4}
R = 6
```

### Held-out configurations

```text
s in {5,6,7}
R in {7,8,9}
```

For every grid, evaluation covers every ordered `(start,terminal)` pair with distinct coordinates and these six initial coin states in direction order `(UP,RIGHT,DOWN,LEFT)`:

```text
uniform       = (1, 1, 1, 1) / 2
up            = (1, 0, 0, 0)
right         = (0, 1, 0, 0)
down          = (0, 0, 1, 0)
left          = (0, 0, 0, 1)
phase-balanced = (1, i, -1, -i) / 2.
```

A micro-case is exactly `x=(s,R,start,terminal,coin)`. Larger grids must not silently receive more weight. Within each grid, sort micro-case lifts and compute quantiles by linear interpolation at index `(n-1)p`; the median is the `p=0.5` case. Overall summaries are the unweighted median or mean of the nine held-out grid-level summaries. Micro-case-weighted results are secondary and separately labeled.

No micro-case, grid, state, or declared horizon may be excluded because it performs poorly. This is exhaustive case enumeration over the named configurations; matching controls are a fixed sampled set, not exhaustive matching enumeration.

## Matching-control manifest

For each row count `R`, source rows are `A={0,...,R-2}` and destination rows are `B={1,...,R-1}`. A control is a bijection `f:A→B` coupling `(r,s)` to `(f(r),0)`. Every control uses exactly `R-1` disjoint position pairs and leaves the same two endpoint states unpaired. The candidate `f(r)=r+1` is always excluded.

The single cross-row manifest contains exactly 100 immutable families:

1. `control-000` through `control-003`: cyclic destination-list rotations 1 through 4;
2. `control-004` through `control-008`: rotations 0 through 4 of the reversed destination list;
3. `control-009` through `control-099`: ranks 0 through 90 after candidate and all cyclic/reflected permutations are removed and remaining permutations are sorted by `(SHA-256(UTF8("area-one-control-random-v1|R|" + canonical)),canonical)`.

Every family record binds its exact canonical permutation for each `R in {6,7,8,9}` and one immutable kind/subkind. It also records displacement vectors, retained genuine-edge counts, cardinality, and disjointness. The generator rejects non-bijections, duplicates, missing row counts, candidate inclusion, and kind changes. Development selects one parameter using the `R=6` member; that parameter follows the same `family_id` to its `R=7,8,9` members. `j` denotes the numeric `family_id` ordinal everywhere and never a separately generated per-row index.

The complete manifest is generated before evolution, stored verbatim, independently regenerated byte-for-byte, and bound into the lock. The generator may enumerate at most `8!=40,320` permutations per row count; only the selected 100 families are evolved. Claims are limited to this named set.

## Comparators

1. **Standard marked Grover search:** `U_G(t)` on the original periodic grid.
2. **EOG-derived candidate:** `U_A(theta,phi,t)` using the development-locked candidate parameter indices.
3. **Ordinary-index oracle:** bounded exact candidate cases under row-major node IDs; amplitudes must match within tolerance.
4. **Tuning-matched controls:** the exact 100 immutable cross-row families using each family’s development-locked parameter indices.

The classical comparator is deferred because no unique classical transition kernel follows from the phased coined operator.

## Primary metric and success rule

For each held-out micro-case `x`, calculate

```text
delta_G(x) = P_A(T|x) - P_G(T|x).
```

All evolution and scalar statistics use the binary64 and non-finite rules in Resolution 2. `epsilon=float64(1e-12)`. A lift is positive only if `delta>epsilon`, negative only if `delta<-epsilon`, and otherwise zero. There is no human exception at a threshold.

For grid `g`, let `positive_count[g]` be the exact integer count of positive candidate lifts and `total_count[g]` the exact number of declared micro-cases. Calculate median lift `m[0,g]` and 10th-percentile lift `q[0,g]` with the frozen interpolation order.

The candidate passes the Grover performance ablation only if all conditions hold:

1. `A[0]=median_g m[0,g] > float64(0.05)+epsilon` across the nine equally weighted grids.
2. Every held-out grid has `m[0,g] > epsilon`.
3. `sum(Fraction(positive_count[g],total_count[g]) for g)/9 > Fraction(7,10)`, and every grid has `Fraction(positive_count[g],total_count[g]) > Fraction(3,5)`.
4. Every held-out grid has `q[0,g] > float64(-0.02)+epsilon`.
5. Candidate and Grover use identical terminals, starts, coin states, oracle calls, outer iterations, and final measurement count.
6. Every numerical invariant passes without clipping or renormalization.

This comparison is not resource-equivalent: each candidate iteration contains extra pair rotations. Passing establishes a finite performance effect, not computational efficiency.

For control family ordinal `j=1,...,100`, define

```text
m[j,g] = median_x(P_j(T|g,x)-P_G(T|g,x))
A[j]   = median_g m[j,g]
c[g]   = median_j m[j,g]
h[g]   = m[0,g]-c[g]
```

The control-score 90th percentile uses the frozen interpolation rule. Candidate rank is `1 + count_j(A[j] >= A[0]-epsilon)`, so ties conservatively rank controls ahead. The strongest structured control has maximum held-out `A[j]`; exact ties resolve by lower `family_id`.

The candidate passes the named-control criterion only if:

1. `A[0] > control_quantile_0.90+epsilon`;
2. candidate rank is at most 10;
3. `median_g h[g] > float64(0.02)+epsilon`; and
4. `m[0,g] > m[j_star,g]+epsilon` for the strongest structured family on at least seven of nine grids.

All samples sort by numeric value followed by canonical micro-case key. Parameters use integer indices. Exact control-score ties resolve by lower `family_id`. Parallel partitions cannot alter sample order or reductions. These are engineering thresholds over the declared finite set, not population-level statistical claims.
## Falsification ladder and permitted claims

### Outcome 0: no held-out Grover improvement

Reject the overlap-pair scatterer as useful under the declared protocol. Do not retune on held-out configurations or replace the primary horizon with a better-looking secondary horizon.

### Outcome 1: improves Grover but not the named controls

Conclude that pair-layer augmentation can improve the tested walk, but the declared adjacent overlap matching has not outperformed the preregistered control class. The result is generic graph/operator engineering, not evidence of a special overlap relation.

### Outcome 2: passes Grover and named-control criteria

Conclude only that the fixed EOG-derived matching and pair rotation improved final-only marked-terminal probability and ranked above the declared cardinality- and tuning-matched controls in the finite held-out regime. This supports deeper mathematical and resource analysis; it does not establish causality from displayed labels, novelty, asymptotic quantum advantage, or hardware value.

### Outcome 3: later resource-adjusted and scaling evidence

Only a later study with compiled circuits, asymptotic analysis, stronger graph controls, and named noise/device assumptions could support a broader efficiency or physical-control claim.

## Required invariants and numerical rules

Analytic composition establishes unitarity from unitary blocks. The dense verifier must be a direct index/formula construction of `O_t`, `P`, `C_G`, and `S`; it may not call production evolution functions.

Dense verification uses `(s,R)=(2,6)`, dimension 72, all 24 candidate parameters, and one identity case `(θ,φ)=(0,0)`. Terminals are all five `p_r`, all five `q_r`, and interior coordinate `(2,1)`. For each operator, compare one-step and seven-step sequential evolution with matrix evolution on every basis vector and 32 random normalized complex vectors generated by Python MT19937 seed `20260815`, with real and imaginary components independently uniform on `[-1,1)`. The same exact cases receive coordinate/index comparison.

The executable checks are:

- maximum entrywise error `max|P†P-I| <= 1e-12`;
- maximum entrywise error `max|U†U-I| <= 1e-12` on bounded dense cases;
- maximum per-iteration absolute norm drift `<= 1e-12` on every production trajectory;
- amplitude-wise coordinate/index `L∞` difference `<= 1e-12` on bounded oracle cases;
- `θ=0` amplitude-wise agreement with `U_G` within `1e-12`;
- sequential operator application agrees with complete-matrix multiplication within `1e-12`;
- candidate only: exactly `R-1` disjoint genuine-overlap pairs covering `2(R-1)` positions; controls require cardinality and disjointness but not genuine-label overlap;
- terminal oracle changes phase only and preserves norm;
- final probability is in `[0,1]` up to `1e-12` numerical tolerance.

No state clipping or renormalization is allowed before validation. Values outside physical bounds beyond tolerance fail the run rather than being silently corrected.

## Resource accounting

Each candidate iteration adds `4(R-1)` logical two-state pair rotations. Candidate and Grover are matched on oracle queries, outer iterations, and final measurements, but not on total non-oracle operations. Reports separately show:

- marked-terminal oracle calls;
- Grover coin applications;
- flip-flop shifts;
- logical pair rotations;
- final terminal measurements;
- Hilbert-space dimension;
- simulation runtime and peak memory.

No performance result may be called an efficiency, gate-count, or hardware advantage. No logical count may be called a physical gate count until a target gate set and compiler are declared.

## Execution and artifact plan

Declared workload before algebraic batching is:

```text
development micro-cases per parameter/method = 10,368
development tuning trajectories              = 25,132,032
held-out primary micro-cases                  = 170,412
held-out primary method records               = 17,382,024
secondary-horizon candidate/Grover records    = 681,648
```

Secondary horizons apply only to candidate and Grover. The ordinary-index oracle is bounded to the dense cases. Conditional controls are not run.

Production uses a separate research dependency lock containing `numpy==2.4.2`; this does not change the frozen verifier package. For fixed `(grid,start,terminal,method,parameter)`, linearity permits evolving the four directional basis columns once and deriving uniform, directional, and phase-balanced outputs by exact linear combination. This is the only allowed workload reduction. Direct six-state evolution and derived evolution must agree within `1e-12` on every dense case and a fixed development sample.

A representative development benchmark must include evolution, invariant checks, JSON serialization, gzip compression, deterministic shard merge, and peak memory/disk measurement. Projected held-out limits are eight wall-clock hours, 8 GiB peak RAM, and 10 GiB final compressed artifacts, with free disk at least three times projected temporary plus final usage. If any limit fails, no held-out run occurs; this protocol must be amended and re-approved before a new holdout is declared.

Development and held-out execution use separate entry points. The held-out worker verifies the canonical lock and independent protocol-hash anchor before evolution, prints no probabilities, writes shards only inside a quarantined temporary directory, and atomically publishes after every expected record, invariant, count, and hash verifies. On timeout or failure it deletes partial outcome shards and publishes only non-outcome failure metadata. This is procedural leakage resistance, not cryptographic blindness; a machine administrator could inspect temporary data.

Production evolution uses NumPy local tensor operations and deterministic partitions. Dense matrices are prohibited in production sweeps. Shards merge in this row order:

```text
(s,R,start_row,start_column,terminal_row,terminal_column,coin,horizon,
 method_kind,control_id,theta_index,phi_index)
```

Micro-case schema `area-one-pair-results/1.0` contains that key plus matching-manifest hash, decimal `θ/π` and `φ/π` indices, terminal probability encoded with `format(value,'.17g')`, invariant maxima, operation counts, and lock hash. UTF-8 JSON uses sorted keys, compact separators, and LF. Deterministic gzip uses compression level 9, `mtime=0`, and blank embedded filename.

The final publication contains:

- canonical uncompressed JSONL SHA-256;
- compressed artifact SHA-256;
- expected and actual record counts per shard;
- lock and matching-manifest hashes;
- completion marker `area-one-pair-results-complete/1.0` written atomically;
- summary schema `area-one-pair-summary/1.0` with grid metrics, ranks, thresholds, and every failure reason.

A failed run instead writes `area-one-pair-results-failure/1.0` containing no probabilities. Full matching-space evolution is out of scope; manifest construction may enumerate permutations as declared above.

## Existing components to reuse

- `eog_quantum_walk.py`: state representation, Grover coin, shift, norms, and final-only schedule.
- `topology_baseline.py`: coordinate-to-ordinary-index equivalence pattern.
- `operator_matrix_verification.py`: complete matrix construction and unitarity oracle.
- `parameter_sweep.py`: exhaustive bounded enumeration pattern.
- `sensitivity_sweep.py`: declared initial-state and terminal aggregation.
- `evaluation_metrics.py`: transparent logical-operation accounting.
- `verification_report.py`: deterministic evidence report pattern.

The installable evidence verifier remains frozen and is not part of the scientific implementation scope.
## Approaches considered

### A. Overlap-pair scatterer — selected

A fixed `2 × 2` unitary on each duplicate-label boundary pair and coin direction. It is minimal, exactly unitary, contains the Grover baseline at `θ=0`, and has one interpretable mechanism.

### B. Joint overlap-aware coin — deferred

An `8 × 8` joint coin across both coordinates and four directions. It is more expressive but introduces parameter and interpretation risk before the minimal mechanism has been tested.

### C. Coherent multi-scale register — deferred

A scale register `|s>` with inter-scale mixing among equal displayed labels. It is closer to the full elastic-grid idea but materially increases Hilbert dimension, oracle ambiguity, and resource-accounting difficulty.

## Implementation sequence after approval

1. Freeze this protocol and calculate its SHA-256 hash.
2. Add the pair operator and marked-terminal oracle without changing existing Grover behavior.
3. Independently construct bounded complete matrices and verify all declared invariants and operator order.
4. Generate and preserve the exact development and held-out matching manifests before evolution.
5. Run development configurations only, benchmark the projected held-out cost, and select parameters for candidate and controls.
6. Write the complete lock manifest and confirm held-out code cannot expose results unless it verifies.
7. Run the held-out configurations once within the approved resource budget.
8. Produce the deterministic compressed micro-case artifact and compact result report with full grid-balanced summaries, control ranks, failures, and permitted claim text.

## Success criteria for the research stage

The stage is complete when either:

- the mechanism is rejected under the declared tests with a reproducible negative report; or
- it passes every primary and specificity threshold, with all invariants and controls passing.

A negative result is a successful research outcome because it eliminates a precise candidate without expanding the claim after failure.

## Non-goals

- No production signing or further verifier work.
- No quantum-hardware implementation.
- No calibrated device-noise claim.
- No patent or novelty claim from simulation alone.
- No claim that EOG labels create new physics.
- No optimization against held-out results.

## Open questions deliberately deferred

- Hardware gate decomposition and target device.
- Calibrated noise channels.
- Asymptotic behavior beyond the declared finite grids.
- Multi-terminal or dynamic-terminal oracles.
- Multi-scale EOG evolution.

## What was decided in this session

- The user selected the abstract operator path rather than open-system or hardware work.
- The user selected final-only terminal probability as the primary outcome.
- The user accepted ordinary-index equivalence as a permanent fairness condition.
- The user selected equal marked-terminal phase-oracle access.
- The user selected the minimal overlap-pair scatterer before more expressive operators.

## Engineering review resolution

Engineering review completed on 2026-08-15. The user accepted the complete recommended resolution for each of the six blockers. This section is normative and supersedes any conflicting earlier wording in this document. It closes the **protocol-definition decisions**; implementation evidence remains required before freeze readiness.

### Resolution 1 — immutable cross-row control families

The control manifest contains exactly 100 family records with IDs `control-000` through `control-099`. Every record has one immutable `kind`, one optional immutable `structured_subkind`, and exact canonical destination-row permutations for all `R in {6,7,8,9}`.

- `control-000` through `control-003` are `structured/cyclic`, using destination-list left rotations by offsets 1 through 4 at every `R`.
- `control-004` through `control-008` are `structured/reflected`, using left rotations by offsets 0 through 4 of the reversed destination list at every `R`.
- `control-009` through `control-099` are `random`. For each `R`, exclude the candidate and every cyclic or reflected permutation; encode each remaining permutation canonically; calculate `SHA-256(UTF8("area-one-control-random-v1|R|" + canonical))`; sort by `(digest_hex,canonical)`; and bind ranks 0 through 90 to those family IDs.

Each family record includes, for every row count, the canonical permutation, displacement vector, retained genuine-edge count, cardinality, and disjointness result. The manifest rejects duplicate families or per-row permutations, non-bijections, candidate inclusion, kind changes, missing row counts, and fewer than 91 eligible random controls. SHA-256 ties resolve by canonical string.

Development parameter selection uses only the `R=6` member. The selected parameter follows the same `family_id` to its `R=7,8,9` members. In all formulas, `j` now means the integer ordinal encoded by `family_id`, never a separately generated per-row index. The complete canonical manifest is generated before any evolution, checked in, independently regenerated byte-for-byte, and bound into the later lock.

### Resolution 2 — binary64 and exact decision semantics

Production states are IEEE-754 binary64 complex values (`numpy.complex128`); scalar calculations are `numpy.float64`. Float32, extended-precision decision paths, fast-math, clipping, and renormalization are prohibited. Every input and intermediate probability, lift, invariant, interpolation, aggregate, and serialized scalar receives an `isfinite` check. Any NaN or infinity fails the run.

`epsilon` is the binary64 value produced by the source literal `1e-12`. A lift is positive only when `delta > epsilon`, negative only when `delta < -epsilon`, and otherwise zero. The phrase “clearly on the passing side” is deleted: equality at any epsilon-adjusted threshold fails unless the rule explicitly states an inclusive comparison and the binary64 value satisfies it.

Positive fractions are represented as exact integer pairs `(positive_count,total_count)`. The overall positive condition is

```text
sum(Fraction(positive_count[g],total_count[g]) for g in canonical_grid_order) / 9 > 7/10
```

and every grid requires `positive_count[g]/total_count[g] > 3/5`. Floating fractions are display-only and cannot decide a verdict.

For a sorted binary64 sample of length `n`, quantile `p=a/b` uses `divmod((n-1)*a,b)=(lo,rem)`, `hi=min(lo+1,n-1)`, then exactly:

```text
w      = float64(rem) / float64(b)
result = float64(x[lo] + float64(w * float64(x[hi] - x[lo])))
```

The median uses `(a,b)=(1,2)` and the 10th percentile uses `(1,10)`. Sorting uses numeric value followed by canonical micro-case key. Parameter selection compares the declared lexicographic fields as binary64 values, then lower integer `theta_index`, then lower integer `phi_index`. Parameters are identified by indices, not transcendental float encodings. Control-rank ties remain conservatively ahead of the candidate; other exact control ties resolve by lower `family_id`.

Serialized zero is `"0"`; negative zero is rejected. Every other scalar string must be finite and equal to `format(parsed_value,'.17g')`. Threshold tests include equality and adjacent `numpy.nextafter` values.

### Resolution 3 — frozen runtime, tensor layout, sharding, and projection

The development benchmark and holdout run use one digest-pinned Linux x86-64 OCI image, exact CPython and dependency locks, `numpy==2.4.2`, and `threadpoolctl==3.6.0`. The lock records the image digest, CPU model/flags, Python build, NumPy configuration, and all package hashes. No Windows or macOS holdout execution is permitted.

Before NumPy import, set `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `VECLIB_MAXIMUM_THREADS=1`, and `NUMEXPR_NUM_THREADS=1`. Runtime thread-pool inspection must report one thread per pool or the run fails. Exactly four worker processes are used; numerical kernels remain single-threaded.

The permitted four-column production state is C-contiguous `complex128` with axes `(row,column,direction,input_coin_basis)` and shape `(R,s+1,4,4)`. Direct six-state validation uses C-contiguous shape `(R,s+1,4)`. Every kernel validates dtype, shape, strides, and finiteness. Oracle, pair layer, coin, and shift execute in the immutable right-to-left order already declared. Production sweeps use local tensor operations, not dense matrices or BLAS matrix multiplication.

A global ordinal follows the canonical row key. `shard_id = ordinal // 100000`; every non-final shard has exactly 100,000 rows. Worker ownership is `shard_id mod 4`. Workers may finish in any order, but each shard and the final merge use canonical ordinal order; all aggregate reductions run in one process.

The immutable direct-versus-derived validation sample is:

```text
(2,6,start=(0,0),terminal=(0,2))
(3,6,start=(2,1),terminal=(3,0))
(4,6,start=(5,4),terminal=(4,0))
```

It covers all six coin states, baseline, candidate, `control-000`, `control-004`, `control-009`, and `control-099`, and all 24 parameter indices where applicable. Direct six-state and four-column-derived amplitudes must agree within `1e-12` for every case.

The end-to-end development benchmark runs three repetitions with the frozen four-worker topology and includes evolution, invariants, row encoding, shard writes, deterministic merge, gzip level 9 with `mtime=0` and blank filename, hashes, peak process-tree RSS, temporary/final disk, and cleanup. Define work units as the canonical sum of `R*(s+1)*4*4*T` for every evolved four-column method/parameter record. Let `rate` be the maximum repetition seconds per work unit and let `bytes_per_row` be the maximum repetition output bytes per row. With fixed safety factor `2.0`:

```text
projected_wall_seconds = ceil(2.0 * rate * declared_holdout_work_units)
projected_final_bytes  = ceil(2.0 * bytes_per_row * declared_holdout_rows)
projected_peak_ram     = ceil(2.0 * maximum_measured_process_tree_RSS)
projected_temp_bytes   = ceil(2.0 * maximum_measured_temp_bytes
                              * declared_holdout_rows / benchmark_rows)
```

The holdout is prohibited unless all existing 8-hour, 8-GiB, 10-GiB, and three-times-free-disk conditions pass mechanically. No projection input or safety factor may change after benchmark output without amendment and re-approval.

### Resolution 4 — independent direct-formula verifier

The new direct verifier may reuse basis-order data but may not import or call production oracle, pair, coin, shift, evolution, aggregation, or selection functions. It constructs `O_t`, candidate/control `P`, `C_G`, and `S` directly by formulas and composes `S @ C_G @ P @ O_t`.

At each `R in {6,7,8,9}` with `s=2`, it verifies the candidate plus `control-000`, `control-004`, `control-009`, and `control-099`, all 24 parameter indices, `theta=0`, paired `p_r` and `q_r` terminals, and one unpaired interior terminal. Candidate verification also retains the original complete `(s,R)=(2,6)` terminal set. Checks cover `P-dagger P`, `U-dagger U`, pair counts/disjointness, phase-only oracle behavior, theta-zero Grover equivalence, coordinate/index equivalence, and one- and seven-step sequential-versus-matrix amplitudes on every basis vector.

Random vectors use one `random.Random(20260815)` instance. Dimensions are processed in ascending order. For each dimension, generate exactly 32 vectors; for every basis index draw real then imaginary as `2.0*rng.random()-1.0`. Compute squared norm with `math.fsum(re*re+im*im in basis order)`, take `math.sqrt`, and divide components in basis order. Zero or non-finite norm is a hard failure with no redraw. A dimension’s 32 vectors are reused across all operator cases of that dimension. Parallel execution may not alter generation order.

### Resolution 5 — consumed-attempt state machine

The holdout root must be a dedicated local directory on one filesystem with no symlink components. State transitions are:

```text
LOCK_VERIFIED
  -> ATTEMPT_CONSUMED
  -> STAGING
  -> STAGING_VERIFIED
  -> LOCK_REVERIFIED
  -> ARTIFACTS_COMMITTED
  -> COMPLETION_PUBLISHED
```

After initial lock and independent approval-anchor verification, but before the first outcome-producing operation, exclusively create `attempt-consumed.json` bound to the lock hash, holdout-set hash, and random attempt ID. Flush and `fsync` the file and parent directory. Existing marker means unconditional refusal. Staging is created only after that durable transition.

On startup, a consumed marker without a valid completion marker prohibits resume, outcome reads, or commit. Residual staging is invalidated and deleted; only `area-one-pair-results-failure/1.0` non-outcome metadata may be published. It must not contain probabilities, lifts, ranks, selected summaries, or outcome-bearing paths. No second attempt may use the same lock or holdout.

After all expected rows, invariants, schemas, counts, hashes, and reconstructed summaries verify, re-read and fully reverify the protocol anchor, Git/source hashes, dependency/image lock, family manifest, and holdout-set hash. Commit files with same-filesystem atomic replacements, flush each file, and `fsync` affected directories. Publish `area-one-pair-results-complete/1.0` last and sync its directory. Consumers reject all artifact sets lacking valid completion. Fault injection is required before and after every filesystem transition, write, sync, verification, and rename.

### Resolution 6 — normative schemas and reconstructing verifier

Publish closed JSON Schema Draft 2020-12 documents with `additionalProperties:false` for:

- `area-one-pair-lock/1.0`
- `area-one-control-family-manifest/1.0`
- `area-one-pair-row/1.0`
- `area-one-pair-shard/1.0`
- `area-one-pair-summary/1.0`
- `area-one-pair-results-complete/1.0`
- `area-one-pair-results-failure/1.0`

Each schema defines exact fields, types, enums, ranges, patterns, multiplicities, hashes, referential constraints, and canonical scalar-string rules. Completion binds schema versions, lock/family/holdout hashes, canonical decompressed JSONL hash, compressed-byte hash, exact per-shard/global counts, and summary hash. Failure forbids every outcome field.

A separate standard-library `publication_verifier.py` requires completion; validates strict UTF-8 LF JSONL, duplicate keys, closed fields, canonical scalar strings, deterministic gzip headers, bounded decompression, hashes, counts, shard membership, and canonical row order; and detects missing or duplicate micro-case keys. It joins baseline, candidate, and control records by canonical key and independently reconstructs every lift, quantile, exact positive count, grid-balanced aggregate, control percentile/rank, strongest structured control, threshold decision, failure reason, and operation count. It independently checks locked parameters against cross-row `family_id` mappings and compares the reconstructed canonical summary byte-for-byte with the publication.

The publication verifier may share schemas and strict parsing only. It may not share evolution, aggregation, ranking, selection, or summary-generation implementations with the producer. It remains separate from frozen `area-one-evidence-verifier==0.1.0`.

## Code-quality review

No additional decisions remain. Implementation must use explicit small modules for operator/oracle kernels, family generation, numerical rules, runtime/sharding, atomic state transitions, schemas/writers, direct verification, and publication verification. The old `operator_matrix_verification.py` remains a baseline consistency checker and must no longer be described as the independent oracle for this study. Production and independent paths may share immutable schema data and basis-order constants only.

## Test review

The executable coverage plan is `data/area-one-overlap-pair-scatterer-eng-review-test-plan-2026-08-15.md`. Every branch in family generation, finite-value validation, threshold/tie handling, tensor validation, direct-matrix comparison, shard merge, schema validation, summary reconstruction, and crash recovery requires positive and negative tests. No held-out outcome may appear in a fixture.

```text
CONTROL IDENTITY             NUMERICS                    OPERATOR
family -> R6/R7/R8/R9        value -> finite?            input -> O -> P -> C -> S
  | invalid => fail            | no => fail                | invariant failure => fail
  +-> stable parameter         +-> exact count/quantile     +-> direct oracle comparison

PUBLICATION                  ONE-SHOT STATE
rows -> shards -> merge      lock -> consumed -> staging -> verify -> commit -> complete
  | missing/tampered => fail   | crash after consumed => invalidate; never resume
  +-> reconstruct summary      +-> completion absent => reject
```

## Performance review

No unresolved performance decision remains. The workload is intentionally large, so implementation must benchmark the complete pipeline rather than only evolution. Four process workers, one numerical thread each, fixed shards, single-process reductions, a 2.0 safety factor, and hard resource gates are mandatory. Failing any projection is a protocol failure requiring amendment; it is not permission to silently reduce controls, cases, states, or horizons.

## Failure modes

| Failure | Required response | Required evidence |
|---|---|---|
| Family changes meaning across `R` | Refuse manifest | Independent regeneration mismatch |
| NaN, infinity, tie ambiguity, or negative zero | Fail run | Exact reason and location |
| Axis, dtype, stride, or hidden-thread mismatch | Fail before evolution | Frozen runtime diagnostics |
| Production/direct amplitudes diverge | Fail invariant stage | Maximum error and case key |
| Crash after attempt consumption | Never resume or rerun | Non-outcome failure marker |
| Partial, reordered, or tampered publication | Reject publication | Reconstructing verifier errors |
| Benchmark exceeds a resource gate | Do not run holdout | Signed benchmark/projection report |

## What already exists

- `eog_quantum_walk.py` supplies the established Grover coin and periodic flip-flop shift formulas, but its absorbing measurement runner is not the candidate search.
- `topology_baseline.py` supplies the row-major equivalence pattern.
- `operator_matrix_verification.py` supplies basis and matrix helpers, but its matrix builder calls production `grover_step` and is not independent.
- `report_file_verifier.py` supplies strict JSON and hash patterns, but it cannot reconstruct research summaries.
- `scaling_benchmark.py` supplies timing structure only; it does not benchmark the complete research pipeline.

## NOT in scope

- Parameter tuning, development outcomes, and every held-out probability remain blocked until implementation verification and explicit freeze approval.
- Quantum-circuit compilation, QPU execution, device noise, and hardware claims belong to a later stage after a scientific result.
- Production signing, commercial verifier changes, PyPI publication, and verifier version `0.1.0` changes are excluded.
- Full matching-space evolution, alternate operators, new horizons, and post-result threshold changes are excluded.

## Parallel implementation strategy

| Lane | Work | Depends on |
|---|---|---|
| A | Candidate/oracle tensor kernels and direct-formula verifier | Revised protocol |
| B | Family manifest and numerical semantics | Revised protocol |
| C | Normative schemas and reconstructing publication verifier | Revised protocol, numeric rules |
| D | Runtime/shards, benchmark, lock, and atomic state machine | B and C contracts |

Lanes A and B can start in parallel. Lane C can start with B but consumes its final numeric and family contracts. Lane D follows those contracts. Integration, complete tests, and freeze review are sequential. Shared edits to the protocol or schema directory must not occur concurrently.

## Implementation Tasks

- [x] **T1 (P1)** — Generate and independently verify the immutable 100-family cross-row manifest.
- [x] **T2 (P1)** — Implement binary64 kernels, exact numerical decisions, and boundary/tie tests.
- [x] **T3 (P1)** — Implement the frozen tensor/runtime/shard contract and complete-pipeline benchmark.
- [x] **T4 (P1)** — Implement candidate/oracle production kernels and the separate direct-formula verifier.
- [x] **T5 (P1)** — Implement and fault-test the consumed-attempt atomic publication state machine.
- [x] **T6 (P1)** — Publish closed schemas and implement the streaming reconstructing publication verifier.
- [x] **T7 (P1)** — Run the complete blocker test plan in the pinned Linux image and obtain a clean engineering re-review.
- [x] **T8 (P1)** — Normalize the protocol text, calculate a candidate approval hash, independently verify it, and request explicit freeze approval.

## T8 normalization and candidate-anchor contract

The authoritative protocol is nonempty and at most 1,000,000 input and canonical-output bytes. Preparation may remove exactly one leading UTF-8 BOM, then requires nonempty strict UTF-8, applies Unicode NFC, converts CRLF and bare CR to LF, rejects C0 controls other than tab/LF and rejects DEL, removes terminal LF characters, and appends exactly one final LF. Every other character, including trailing horizontal whitespace, is preserved. Canonical output contains no BOM. BOM-only and multiple-BOM inputs fail.

The candidate sidecar is the exact sibling `<protocol-basename>.sha256` and contains lowercase 64-hex SHA-256, two ASCII spaces, the protocol basename, and one LF. Producer and standalone verifier must agree on the exact normalized protocol bytes and sidecar. Both paths must be distinct regular non-symlink files and remain identity-stable while read. Candidate writes use unique same-directory temporary files, file fsync, atomic per-file replacement, and parent-directory fsync where supported. Cross-file replacement is deliberately fail-closed rather than falsely described as atomic: interruption between protocol and sidecar replacement leaves an unverifiable, unapproved pair that must be regenerated before review.

The sidecar digest is external to this document to avoid self-reference. A self-consistent protocol/sidecar pair proves integrity only, not approver identity or approval. Freeze requires a separate explicit human decision naming the exact `sha256:<64-hex>` digest. Coordinated replacement of both files before that decision remains merely a new candidate and invalidates any earlier approval request.

## Approval and freeze status

T1–T7 passed their implementation and capacity gates. T8 has prepared an independently verified candidate approval anchor and has requested a separate explicit freeze decision. The protocol is **awaiting explicit freeze approval**; sidecar existence is not approval.

Until that explicit decision is recorded against the exact digest, parameter tuning, development result selection, lock finalization, and held-out execution remain unauthorized. Even after a protocol freeze, those downstream actions require their separately declared gates and may not be inferred from the anchor alone. Adversarial review history remains round 1 `5/10`, round 2 `7/10`, and round 3 `6/10`; the completed engineering blocker review and T7 evidence supersede the earlier implementation-gate status without establishing any scientific outcome.

## Sources for engineering constraints

The single-thread policy follows NumPy’s documented use of potentially multithreaded BLAS backends and environment controls: [NumPy global configuration](https://numpy.org/doc/stable/reference/global_state.html). The random-vector contract pins Python’s documented Mersenne Twister API: [Python `random`](https://docs.python.org/3/library/random.html). Artifact contracts use the published [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12).

Internet-source content was rephrased for compliance with licensing restrictions.

## Immediate assignment

Implement T1 through T7 without tuning or held-out execution. After all tests and independent reconstruction checks pass, run a second engineering review. Only then may the normalized protocol receive a SHA-256 approval anchor and explicit freeze decision.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope and strategy | 0 | — | Not run |
| Codex Review | `/codex review` | Independent second opinion | 0 | — | Three earlier adversarial rounds were not a freeze approval |
| Eng Review | `/plan-eng-review` | Architecture and tests | 1 | CLEAR FOR IMPLEMENTATION | Six blockers resolved; implementation gates remain |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | N/A | No UI scope |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | Deferred until a research CLI exists |

**VERDICT:** ENGINEERING PLAN CLEARED FOR BLOCKER IMPLEMENTATION; NOT FREEZE-READY AND NO HOLDOUT AUTHORIZED.

NO UNRESOLVED DECISIONS
