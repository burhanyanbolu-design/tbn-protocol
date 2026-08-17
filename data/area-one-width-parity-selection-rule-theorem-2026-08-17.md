# Area One Position-Parity Selection Rule and Unsatisfiable Held-Out Criteria

Date: 2026-08-17  
Status: **CONFIRMED / EXPLAINS THE EXACT-ZERO s=3 MEDIAN / TWO FROZEN CRITERIA UNSATISFIABLE**

## Scope and boundary

This tests the width-parity hypothesis recorded in `data/area-one-research-direction-evaluation-transport-versus-zero-mode-2026-08-17.md`, which was ranked first before choosing any new candidate.

This is a support and selection-rule theorem about the declared operators. It is development-only structural verification. It reads no held-out outcomes, performs no tuning or parameter selection, selects or promotes no candidate, and produces no experiment artifact. Reading declared grid, horizon and control configuration is configuration inspection, not held-out access.

It does not overturn the Candidate 1 rejection and does not lower, edit or reinterpret the frozen `-0.02` floor.

## Declared structure used

From the frozen protocol: basis `|r,c,d>`, rows `R`, width `w=s+1`, directions `(UP,RIGHT,DOWN,LEFT)`, Grover coin `C_G`, periodic flip-flop shift `S`, marked-terminal phase oracle `O_t`, and pair layer `P` coupling the `R-1` genuine pairs `(r,w-1) <-> (r+1,0)` within each direction. Candidate iteration is `S C_G P O_t`; baseline is `S C_G O_t`. Initial states are `|start> tensor |coin>`, localized at one position. Development grids are `s in {2,3,4}`, `R=6`, with declared horizons `9,10,11`. Held-out grids are `s in {5,6,7}`, `R in {7,8,9}`. A control is a bijection `f:{0..R-2}->{1..R-1}` coupling `(r,w-1)` to `(f(r),0)`; the candidate is `f(r)=r+1`.

## Theorem: position parity is conserved exactly iff both `R` and `w` are even

Colour positions by `(r+c) mod 2`. Work in residues mod 2, since all moves are modular.

A row move sends `r` to `(r+-1) mod R`. This flips the colour for every `r` if and only if `R` is even; if `R` is odd the wrap `R-1 -> 0` preserves colour. A column move sends `c` to `(c+-1) mod w`, flipping colour for every `c` if and only if `w` is even. Therefore `S` flips position colour on every basis state exactly when both `R` and `w` are even, which is also exactly when `C_R square C_w` is bipartite.

`O_t` is diagonal in position and `C_G` acts only on direction, so both preserve position colour. For the candidate map `f(r)=r+1`, the pair layer connects colours `r+w-1` and `r+1`, which are equal if and only if `w` is even, so `P` preserves colour for even `w`. The general condition for an arbitrary control map is derived in Consequence 2.

Hence when `R` and `w` are both even, `U_A` and `U_G` each flip position colour exactly once per step. From a localized start of colour `gamma`, after `k` steps all amplitude lies on colour `(gamma+k) mod 2`, and the complementary colour has amplitude exactly zero.

If `R` or `w` is odd the graph contains an odd cycle, no global 2-colouring exists, and no such invariant holds. For odd `w` the pair-layer edges join opposite colours, but that relation is local and moot once the graph is non-bipartite.

## Exact verification against the real operators

Independent standard-library construction of `S`, `C_G`, `P`, `O_t` at `R=6`, start `(0,0)`, terminal `(5,s)`, uniform coin, `theta=pi/16`, `phi=pi/2`, evolving `k=1..6`:

| grid | `w` | `R,w` both even | bipartite | pair edges same colour | rule, baseline | rule, candidate |
|---|---:|---|---|---|---|---|
| `s=2` | 3 | no | no | no | absent | absent |
| `s=3` | 4 | **yes** | **yes** | **yes** | **holds every step** | **holds every step** |
| `s=4` | 5 | no | no | no | absent | absent |

"Absent" means measured support on both colours. The rule held identically with and without `P`, confirming independence from the pair layer and from `(theta,phi)`.

Reproducibility gap, recorded honestly: this construction was run in a temporary script that was deleted, so no hashed artifact reproduces the table. The parameters above are sufficient to rebuild it, and the theorem above is a proof rather than a measurement.

## Consequence 1: the exact-zero `s=3` median is an artifact, not a result

Let `N=R(s+1)`. For a doubly even grid the colour classes have `N/2` each, and there are `N(N-1)` ordered start/terminal pairs with distinct coordinates. Forced-zero fractions are

- even horizon, terminal must match start colour: opposite-colour cases forced zero, fraction `(N/2)/(N-1)`;
- odd horizon: same-colour cases forced zero, fraction `(N/2-1)/(N-1)`.

When the terminal has the inadmissible colour, its probability is exactly zero for **both** candidate and baseline, so the lift is exactly `0`. No floating-point cancellation is involved: the inadmissible fibres are never populated, `P` mixes only same-colour positions, `O_t` is diagonal, and `S` is a permutation.

For `s=3,R=6`: `N=24`, classes `12/12`, `552` ordered pairs, `3312` micro-cases over six coin states. The declared horizon is `10`, which is even, so forced zeros are `288/552 = 12/23 = 52.1739%`, a strict majority. The median lift is therefore exactly `0` regardless of `theta`, `phi`, coin state or pair layer.

Since `(N/2)/(N-1) > 1/2` for every `N`, this median pinning occurs on every doubly even grid at an even horizon.

This explains the exact-zero `(s=3,R=6)` median recorded for **both** Candidate 1 and Candidate 2. It was never evidence that the mechanism does nothing there. Those micro-cases carry no candidate-versus-baseline lift information.

Preconditions, stated explicitly: localized `|start> tensor |coin>` initial states, no intermediate projection or measurement, strict positivity `delta > epsilon`, and distinct start/terminal coordinates.

## Consequence 2: the parity-protected cases handicap the candidate

The candidate `f(r)=r+1` always satisfies `f(r) != r (mod 2)`, so it preserves colour and is parity-protected. Controls need not be. Colour preservation requires `f(r) != r (mod 2)` for all `r`; verified examples at `R=6` and `R=8`:

- candidate `f(r)=r+1`: preserves colour;
- `control-000`, rotation by one: **does not** preserve colour;
- `control-004`, reversed list: preserves colour.

A parity-breaking control leaks amplitude across colours and can therefore score a strictly positive lift on exactly the micro-cases where the candidate is pinned to zero. So on doubly even grids the selection rule does not merely add neutral zeros; it can systematically disadvantage the candidate against parity-breaking controls in the named-control comparison. This is the opposite of a hidden advantage.

## Consequence 3: two frozen held-out criteria are unsatisfiable on two of the nine grids

Held-out grids are `s in {5,6,7}` by `R in {7,8,9}`. Both `R` and `w=s+1` are even only for

- `(s=5,R=8)`: `N=48`;
- `(s=7,R=8)`: `N=64`.

The other seven grids have odd `R` or odd `w` and are unaffected.

Maximum attainable positive fraction on a doubly even grid is `(N/2-1)/(N-1)` at even horizon and `(N/2)/(N-1)` at odd horizon. Both are at most `3/5`, with equality only at `N=6`, which is unattainable because a doubly even `N` is a multiple of four; they are strictly below `3/5` for every doubly even `N>=8`. Concretely, `23/47 = 0.4894` and `31/63 = 0.4921` at even horizon; `24/47 = 0.5106` and `32/63 = 0.5079` at odd horizon.

Therefore **success criterion 3, requiring every grid to satisfy `positive_count/total_count > 3/5`, cannot be satisfied on `(s=5,R=8)` or `(s=7,R=8)` at any horizon parity, at any parameter value, by the candidate or by any control.** This is unsatisfiable by construction, not by performance.

**Success criterion 2, requiring `m[0,g] > epsilon` on every held-out grid, additionally fails at even horizon**, because the median is pinned to exactly zero. The declared development horizons `9,10,11` for `N=18,24,30` match `ceil(2*sqrt(N))`, which would give `14` and `16` for `N=48,64`, both even. That horizon formula is inferred from the development values and must be confirmed against the declared held-out horizon table; criterion 3 fails either way, so only the criterion 2 claim depends on it.

## Consequence 4: the declared family mixes two incomparable regimes

`s=3` is parity-protected; `s=2` and `s=4` are not. Taking an unweighted median across one protected and two unprotected grids averages structurally different objects, biases aggregates toward zero, and concentrates variance in the unprotected grids. The tail that actually rejected Candidate 1, min q10 `-0.020494795710597848` on `(s=2,R=6)`, comes from an unprotected grid and remains a genuine failure.

## Levers that would weaken the defect claim

The defect is definitional, and exactly two changes would dissolve it:

1. defining `total_count[g]` over parity-admissible micro-cases only;
2. counting non-negative rather than strictly positive lifts, which would instead turn the cap into a floor.

Horizon choice and allowing `start=terminal` do not rescue criterion 3.

Any such amendment is itself a preregistration-integrity event. It must be drafted from structure alone, without reference to measured performance, and requires explicit re-approval. The frozen protocol states that outcome-dependent change invalidates the held-out set.

## What this does and does not establish

Establishes: an exact parity selection rule and the precise condition for it; the structural cause of the exact-zero `s=3` median; that the rule can disadvantage the candidate against parity-breaking controls; and that frozen criteria 3 and, at even horizon, 2 are unsatisfiable on two of nine held-out grids.

Does not establish: any transport effect, candidate/control separation, advantage, that Candidate 1 should be un-rejected, or that the `s=2` tail is an artifact.

## Required next actions

1. Confirm the declared held-out horizons for `(s=5,R=8)` and `(s=7,R=8)` from declared configuration only.
2. Do not execute held out under the current frozen success rule; criteria 3 and probably 2 are unsatisfiable there irrespective of mechanism quality.
3. Draft any successor protocol to handle parity explicitly: restrict to one parity class, or report per-parity results separately, or define positivity over admissible micro-cases only. Structure-motivated, with explicit re-approval.
4. Quote `(s=3,R=6)` as parity-protected wherever it appears; never present its exact-zero median as mechanism evidence.
5. Re-examine the `(s=2,R=6)` tail against the diagnosed uniform-coin, same-column, displacement-three subpopulation, which remains the real open failure.

No held-out execution, tuning, parameter selection, candidate promotion, T9, lock, protocol edit, hardware run, grant claim, artifact, staging, commit or push is authorized by this theorem.
