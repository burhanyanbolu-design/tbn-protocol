# Area One Candidate 5 Endpoint-Fixed Aggregate Isomorphism Theorem

Date: 2026-08-17  
Status: **ALL 119 CONTROLS SEPARATED ON ALL THREE GRIDS / NO DYNAMICS AUTHORIZED**

## Scope and boundary

This is the second design-only Candidate 5 theorem for `(s,R)=(2,6),(3,6),(4,6)`. It fixes the graph category required by the Stage 1 handoff and decides all endpoint-fixing candidate/control isomorphism questions exactly.

It contains no source module, test file, quotient claim, simulation, transport probability, parameter search, T9, protocol, lock, held-out access, hardware execution, report, experiment artifact, staging, commit or push.

Candidate 5 remains an engineered EOG-derived benchmark. Its common zero mode is universal and manufactured by `c=B1`; the result below concerns only whether genuine native pair identity remains structurally visible.

## Fixed uncoloured weighted-multigraph category

The only marked vertices are the lifted entrance `a_L` and exit `b_L`. No source/destination labels, native-versus-matching provenance colours, row identities or declared sublattice labels may be used by the isomorphism test.

Each native or matching channel is an uncoloured unit channel. Parallel unit-channel multiplicity is represented exactly by the integer aggregate adjacency entry, so entry `2` means two indistinguishable parallel unit channels. Weight-six rungs and weight-10/11 index edges retain their actual weights. This aggregate integer representation forgets channel provenance but not multiplicity.

For each nonidentity `pi`, separation means there is no permutation matrix `P` satisfying

`P^T H_id P=H_pi`, `P e_(a_L)=e_(a_L)`, and `P e_(b_L)=e_(b_L)`.

One valid witness would fail the universal gate.

## Intrinsic reduction to the native aggregate matrix

Let `n=6(s+1)`. In every Candidate 5 lift, weighted degrees are

- `deg(q)=10n+10`, equal to `190`, `250`, or `310`;
- `deg(R_v)=20` or `22`;
- `deg(L_v)=10` or `11`.

Thus `q` is the unique vertex of its weighted degree and is fixed by every weighted isomorphism. Its open neighbourhood is exactly the full right set `R`, so `R=N(q)` and the remaining original vertices are exactly `L`. The bipartition and chiral grading are therefore intrinsic; they are not imposed as labels.

Every `R_v` has exactly one incident weight-six edge, namely its rung to `L_v`. Its q-edge has weight 10 or 11 and all crossed aggregate native/matching entries have weight at most two. Hence every isomorphism preserves the rung pairing.

Every lifted isomorphism consequently has the form

`q -> q`, `L_v -> L_(phi(v))`, and `R_v -> R_(phi(v))`

for one permutation `phi` of the native vertices. The cross-block condition reduces exactly to

`phi^T (6I+A_id) phi = 6I+A_pi`, equivalently `phi^T A_id phi=A_pi`.

Endpoint fixation is exactly `phi(a)=a` and `phi(b)=b`. Conversely, every such base permutation lifts and automatically preserves `c=6*1+A_pi*1` and all index edges. Therefore the lifted and base endpoint-fixing isomorphism questions are equivalent.
## Complete exact exhaustion

An independent integer oracle reconstructed `C_6 square C_(s+1)` and all matching entries without importing production graph, root or control constants. It used only aggregate entries `0,1,2` and individualized only `a` and `b`.

For each candidate/control pair, joint exact equitable refinement repeatedly split vertices by weighted neighbour sums into the current cells. The endpoint-seeded candidate refinement became discrete within at most three rounds on every declared grid. Therefore any isomorphism, if one exists, has one forced vertex map. Unequal paired cell counts reject immediately; equal discrete colours define the unique possible `phi`, which was then verified entry by entry against `phi^T A_id phi=A_pi` and checked to fix both endpoints.

Exact results:

| grid | nonidentity controls | endpoint-fixing isomorphic | separated |
|---|---:|---:|---:|
| `s=2` | 119 | 0 | 119 |
| `s=3` | 119 | 0 | 119 |
| `s=4` | 119 | 0 | 119 |

Thus all `357` nonidentity grid/control decisions pass the declared endpoint-fixing non-isomorphism gate.

## Independent endpoint-walk invariant

A second independently reconstructed integer oracle used invariants preserved by every endpoint-fixing weighted isomorphism. It compared the exact sequences

`(<a|A^k|a>, <b|A^k|a>, <b|A^k|b>)`

through `k=2n`.

This independently separated all 119 controls for `s=2`, 118 controls for `s=3`, and all 119 controls for `s=4`. First scalar differences occurred only at powers three, four or five:

- `s=2`: counts `{3:96, 4:18, 5:5}`;
- `s=3`: counts `{3:96, 4:16, 5:6}`, with one scalar-moment exception;
- `s=4`: counts `{3:96, 4:16, 5:7}`.

The sole scalar-moment exception is `s=3`, permutation `(4,1,0,3,2)`. It shares all three tested scalar endpoint sequences through power `48`; this equality is not candidate success.

Define the stronger endpoint-fixed invariant

`M_d(A;a,b) = multiset_(v in V) ( ((A^k)_(v,a),(A^k)_(v,b)) )_(k=0)^d`.

The candidate and exception satisfy `M_2(A_id;a,b) != M_2(A_pi;a,b)`. An exact unlabeled count witness is: among vertices whose `k=1` endpoint pair is `(1,1)`, the candidate has zero whose `k=2` pair is also `(1,1)`, while the exceptional control has two. Their coordinate representatives are `S_0=(0,3)` and `D_4=(5,0)`, but coordinates and root labels are not part of the invariant. This independently proves the exception cannot be endpoint-fixing isomorphic.

Consequently the independent invariant also separates all `357` cases. It does not depend on native/matching provenance, source/destination sides or the lifted index labels.

## Interpretation and evidence boundary

The index star does not create hidden candidate/control isomorphisms and does not erase aggregate pair identity. The separation comes from the actual aggregate native-plus-matching matrices `A_pi`, not from explicit row fingerprints or provenance colours.

This is structural EOG pair-identity evidence only. It does not make the manufactured common zero mode EOG-specific, prove a strict endpoint quotient, establish spectral or dynamical superiority, or show transport probability or quantum advantage. Scalar endpoint moments distinguish most controls but are still structural invariants, not observed transport.

## Decision and next gate

Candidate 5 passes the endpoint-fixing aggregate non-isomorphism gate for all 119 controls on every declared grid. No hidden source/destination or provenance restriction was needed; `q`, the bipartition and the rung pairing are intrinsic to the weighted graph.

The next separately authorized theorem may investigate a strict endpoint-representing exact quotient of the Candidate 5 lift. It must not infer quotient closure from non-isomorphism, and it must stop before dynamics if the endpoint-seeded coarsest exact refinement is discrete or otherwise fails strict compression.

No Candidate 5 source, tests, quotient result, dynamics, simulation, T9, protocol, held-out work, hardware run, report, artifact, staging, commit or push is created or authorized by this theorem.