# Area One Candidate 3 Typed-Arm Stabilizer Obstruction Design

Date: 2026-08-17  
Status: **THEOREM-FIRST, NECESSARY-ONLY NEGATIVE RESULT**

## Scope and boundary

This formalizes a local matching-only obstruction after the completed neutral-anchor theorem. It is a necessary-only negative theorem: passing does not establish separation, and failure to find a stabilizer witness gives only `obstruction absent / no conclusion`.

This is not natural EOG evidence, transport, time evolution, probability, advantage, a protocol, T9, held-out work, a report, or an artifact. It authorizes no simulation, tuning, parameter search, or experimental claim.

## Fixed family

The construction retains the 35-cell neutral-anchor shape on only `(s,R)=(2,6),(3,6),(4,6)`. It has entrance, hub, five singleton genuine source roots, one support-source cell, five singleton genuine destination roots, one support-destination cell, exit, and twenty singleton gadget cells. Each genuine root has a two-edge arm

`root --q_i-- anchor --M-- terminal`,

where `p=R(s+1)/2-1` and the constant matching and terminal weight is fixed as `M=p+15`. Support matching remains pointwise fixed. There is no search or tuning.

The only declared rooted-type profiles are:

- neutral-both: source and destination `(2,2,2,2,2)`;
- duplicate-both: source and destination `(2,2,3,4,5)`;
- source-neutral/destination-distinct: `(2,2,2,2,2)` and `(2,3,4,5,6)`;
- source-distinct/destination-neutral: `(2,3,4,5,6)` and `(2,2,2,2,2)`;
- rigid-distinct: source and destination `(2,3,4,5,6)`.

## Stabilizer theorem

Label source roots `s_i` and destination roots `d_i`. Define

`G_S={alpha in S_5 : q^S_i=q^S_{alpha(i)} for every i}`

and

`G_D={beta in S_5 : q^D_i=q^D_{beta(i)} for every i}`.

The candidate has matching `s_i--d_i`; control `pi` has `s_i--d_{pi(i)}`. If

`pi = beta composed with alpha^{-1}`, with `alpha in G_S` and `beta in G_D`,

map every source arm `i` to source arm `alpha(i)`, every destination arm `i` to destination arm `beta(i)`, and fix every other vertex. This map includes each root, anchor, and terminal. It is a bijection, fixes entrance and exit, preserves rooted types, and maps every candidate edge with its exact weight to a control edge. Therefore the two Fraction matrices are exactly permutation-similar.

Exact conjugacy certifies identical characteristic polynomials and spectra, rank, nullity, zero projector, and every endpoint moment. It is stronger than checking finitely many moments. Pointwise weighted degrees and the edge-weight multiset are also unchanged for every matching-only control, whether or not it has a stabilizer witness.

The common integer-scaled zero vector is:

- entrance and exit: `-M^2`;
- each genuine source root: `2M`;
- each support source: `M`;
- source terminal `i`: `-2q^S_i`;
- all other vertices: zero.

Its exact norm and absolute endpoint projector element are

`N=M^3(2M+1)+4 sum_i (q^S_i)^2`,

`|P_0(x,e)|=M^4/N`.

Exact elimination certifies candidate rank `n-1` and nullity one on every declared grid/profile. A valid stabilizer map leaves this zero vector invariant and gives zero residual for candidate and control.

## Minimality obstruction and decision rule

If either typed side has a repeated rooted type, its stabilizer contains a transposition. Taking the other side's identity produces a nonidentity `pi=beta alpha^{-1}`. Thus exhaustive separation of all `5!-1=119` nonidentity matching controls requires five distinct source types and five distinct destination types.

This condition is necessary, not sufficient. For rigid-distinct, both stabilizers are trivial and identity is the only invisible matching certified by this theorem. Every rigid nonidentity control must still return `obstruction absent / no conclusion`; trivial stabilizers never prove separation.

The declared invisible-set predictions are:

- neutral-both: all 120 permutations;
- source-neutral/destination-distinct: all 120;
- source-distinct/destination-neutral: all 120;
- duplicate-both: exactly `{identity, (0 1)}`;
- rigid-distinct: identity only.

## Certification and tests

Production rejects undeclared grids/profiles, malformed permutations, unequal-type arm swaps, endpoint-moving or nonbijective maps, unequal matching weights, foreign edges, false conjugacy witnesses, changed zero residuals, and separation claims for invisible controls. It validates the fixed topology, all labels and cells, exact quotient closure, Fraction-only matrices, pointwise fairness, exact rank/nullity, and the projector formula.

Independent tests reconstruct coordinates, all 35 cells, gadgets, matrices, stabilizers, vertex maps, zero vectors, and an exact rank oracle without importing production grid/profile constants. They exhaust all 120 permutations on all fifteen declared grid/profile pairs. Entrywise conjugacy is exhaustive for every invisible control; endpoint moments through `H^8` are checked exactly on representative redundant cases. Fail-closed mutations cover every theorem assumption.

A passing suite certifies only the stated local matching-only obstruction. It creates no affirmative evidence for the rigid case and grants no permission for experimental work.
