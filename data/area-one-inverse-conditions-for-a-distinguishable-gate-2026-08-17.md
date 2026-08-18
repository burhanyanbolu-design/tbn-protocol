# Area One Inverse Analysis: What Would a Distinguishable Double Gate Require?

Date: 2026-08-17  
Status: **INVERSE CONDITIONS DERIVED / ONE FAILURE CAUSE NEWLY IDENTIFIED**

## Why this document exists

Burhan asked the question that should have been asked first: instead of proposing constructions and testing them, derive the conditions a rewiring-plus-gate mechanism **must** satisfy to be dynamically distinguishable, then check whether EOG can satisfy them.

Candidates 1 through 6 were all forward attempts: propose, test, fail, propose again. The inverse problem was never stated. This document states it.

Development-only structural reasoning. No held-out access, no tuning, no new candidate, no simulation of outcomes. The verification script was temporary and deleted.

## Does the quantum walk need the double gate at all?

No. A discrete-time quantum walk is a coin plus a shift. Ballistic spreading and the two-horned distribution appear with no extra gate. Grover-style spatial search needs only coin, shift and oracle.

The pair layer `P` was an addition, proposed by Kiro, intended to inject EOG structure into machinery that did not require it. This matters: an optional additive term must earn its place by producing a measurable difference, and the burden of proof was always on `P`.

## The four necessary conditions

Let `a` be the entrance, `b` the exit, `H_id` the genuine matching and `H_pi` a control. The observable is marked-terminal probability at a declared horizon.

### N1 — Non-isomorphism

If there is an endpoint-fixing isomorphism `P` with `P^T H_id P = H_pi`, then for **every** analytic function `f`,

`<b|f(H_id)|a> = <b|f(H_pi)|a>`.

That includes every walk-step count and every evolution time. The dynamics are provably identical, not merely similar.

- Candidate 3 balanced weight: **failed**. Every matching permutation was endpoint-fixing isomorphic.
- Candidate 5: **passed** for all 119 controls on all three grids.

Status: achievable, and achieved.

### N2 — The discriminator must not be shared

Any structural quantity common to the candidate and all controls carries zero discriminating information.

- Candidate 3 balanced and Candidate 5 both built zero modes that were common to all 120 matchings by construction, via the universal identity `c=B1`.

Status: repeatedly violated, and each violation was avoidable by inspection.

### N3 — The rewired edges must be load-bearing

The pair edges must carry a non-vanishing fraction of the `a`-to-`b` amplitude. If an alternative route bypasses them, their contribution is diluted and any pairing-dependent difference is suppressed.

**This condition fails, and the reason was never checked until now.** Exact combinatorial verification on the declared family:

| grid | width | native wraparound edges `(r,0)--(r,w-1)` present | `a`-to-`b` reachable with **all** pair edges removed |
|---|---:|---:|---|
| `s=2` | 3 | 6 of 6 | **yes** |
| `s=3` | 4 | 6 of 6 | **yes** |
| `s=4` | 5 | 6 of 6 | **yes** |

The native torus `C_6 square C_w` wraps in the column direction, so it **already** joins column `0` to column `w-1` at every one of the six rows, independently of any matching. The five overlap-pair edges are therefore parallel in function to connectivity the graph already had. They are distinct edges — none coincides exactly with a native edge — but they are redundant as a route.

Deleting every pair edge leaves the entrance connected to the exit on all three grids. The mechanism under test was never on the critical path.

Short-walk counts are consistent with dilution but are not comparable across grids because the horizons differ, so they are recorded as suggestive only: the share of length-`k` walks that depend on a pair edge was `28.1%` at `s=2` and `k=6`, `15.5%` at `s=3` and `k=6`, and `86.0%` at `s=4` and `k=7`.

Status: **failed by construction of the declared topology.**

### N4 — The advantage must be quantum, not merely topological

Even if N1 to N3 hold, the difference must be larger for the quantum walk than for a classical random walk on the identical graph. Otherwise the finding is a graph-connectivity effect that any classical algorithm also sees.

Status: **never tested.** No classical comparator was ever run; the frozen protocol explicitly deferred it, stating that no unique classical transition kernel follows from the phased coined operator.

## What this implies

The deep cause of the null result is not only that five edges are a small perturbation. It is that **the overlap seam was redundant with the torus wraparound**, so no choice of pairing could be load-bearing. Any mechanism placed there was pre-emptively diluted, whatever gate was applied.

This is a more precise and more useful failure explanation than "the effect was small", and it was cheap to check. It was not checked for six candidates.

## Could the math be made to work?

Yes, for N3, and the fix is specific: **make the overlap seam a genuine cut.** Remove the column wraparound so the grid is a cylinder or a strip rather than a torus. Then every entrance-to-exit route must cross the pair edges, the pairing determines the path structure, and different pairings produce genuinely different reachability and path lengths rather than a 0.1% perturbation.

This would not be a gadget added after a kill gate. It removes a redundancy that masks the mechanism, rather than adding structure to force a result.

**The honest catch.** Satisfying N3 this way makes the *pairing* matter. It does not make *quantum* matter. On a cut graph, a classical random walk would also register the pairing change, possibly by a larger relative margin. So the likely outcome is a real, measurable, and genuinely EOG-dependent effect that is **not** a quantum advantage.

That distinction is the whole game, and it is what N4 tests.

## Ordered next steps, if this is ever resumed

1. State one EOG query that is expensive classically. Quantum search buys `sqrt(N)` against `N`; if the classical operation is already `O(1)` or `O(log N)`, no quantum mechanism can help and the line ends here.
2. Build the cylinder or strip variant and confirm N3 holds, i.e. that removing pair edges disconnects or materially lengthens `a` to `b`.
3. Run a classical comparator on the identical graph before any quantum claim, to separate a topological effect from a quantum one. This is N4 and it must precede any advantage language.
4. Only if N4 shows a quantum-specific margin does a new protocol become justified.

## Boundary

This derives necessary conditions and identifies a previously unnoticed redundancy in the declared topology. It does not revive Candidate 1, does not establish any transport effect, separation or advantage, and does not overturn the falsification: the genuine matching ranked 95 of 101 on the declared family, and that result stands for that family. The frozen protocol and the `-0.02` floor are unchanged. No source or test file was added, and no staging, commit or push occurred.
