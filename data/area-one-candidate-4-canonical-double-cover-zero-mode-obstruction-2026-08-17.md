# Area One Candidate 4 Canonical Double-Cover Zero-Mode Obstruction

Date: 2026-08-17  
Status: **REJECTED AT THE MANDATORY ZERO-MODE GATE**

## Scope and boundary

This is the design-only theorem requested by the Candidate 4 handoff for `(s,R)=(2,6),(3,6),(4,6)`. It tests one predetermined canonical bipartite double cover of the completed native Candidate 3 family. It introduces no searched weights, fingerprints, gadgets or tuned parameters.

Candidate 4 is an EOG-derived engineered lift testing a Harrow-inspired protected-zero-mode idea. It is not Harrow's construction and is not natural EOG/Harrow evidence. This theorem contains no time evolution, transport probability, simulation, parameter search, T9, protocol, lock, held-out access, hardware execution, report or experiment artifact.

## Native family

Let `V_s={(r,c):0<=r<6, 0<=c<=s}`. Let `T_s` be the unit-channel adjacency of the native torus `C_6 square C_(s+1)`. Define

- entrance `a=(0,0)` and exit `b=(5,s)`;
- sources `S_i=(i,s)` and destinations `D_i=(i+1,0)`, `i=0,...,4`;
- `A_pi=T_s+sum_i (|S_i><D_pi(i)|+|D_pi(i)><S_i|)` for `pi in S_5`.

The identity permutation is the candidate and the other 119 permutations are controls. Native and matching channels remain separate unit channels, including when two channels coincide.

## Canonical full double cover

Replace every native vertex `v` by `(v,0)` and `(v,1)`. Every unit channel `u--v`, native or matching and with multiplicity retained, becomes exactly the two crossed channels

`(u,0)--(v,1)` and `(u,1)--(v,0)`.

Ordering layer zero before layer one gives the exact lifted adjacency

`H_pi = [[0,A_pi],[A_pi,0]]`.

Every native EOG channel is therefore genuinely represented twice, without changing its unit weight. Every matching identity or control channel is represented by the same canonical rule. Each lifted named vertex has the same weighted degree and incident channel-weight multiset as its native antecedent.

## Bipartite and chiral gate: passed

The two layers are an exact bipartition. With `Gamma=diag(I,-I)`,

`Gamma H_pi Gamma = -H_pi`

for every candidate and control. Thus the full lift has exact bipartite/chiral symmetry despite the direct native candidate being non-bipartite.
## Universal even-nullity theorem

Let

`U=(1/sqrt(2))*[[I,I],[I,-I]]`.

Direct block multiplication gives

`U^T H_pi U = diag(A_pi,-A_pi)`

and equivalently `H_pi^2=diag(A_pi^2,A_pi^2)`. Hence

- `spec(H_pi)=spec(A_pi) union spec(-A_pi)` with multiplicity;
- `ker(H_pi)=ker(A_pi) direct-sum ker(A_pi)`;
- `nullity(H_pi)=2 nullity(A_pi)`;
- the nearest nonzero absolute eigenvalue of `H_pi` equals that of `A_pi`.

Therefore every canonical equal-layer double cover has even nullity. Exact nullity one is impossible for any square base adjacency, independently of the declared grid or control.

## Declared candidates fail the zero-mode gate

The completed exact native theorem already certifies candidate nullities

`nullity(A_id)=(0,0,1)` for `s=(2,3,4)`.

The canonical lifted candidate nullities are consequently

`nullity(H_id)=(0,0,2)`.

Thus `s=2` and `s=3` have no lifted zero mode, while `s=4` has a two-dimensional zero sector rather than the required unique zero mode.

For `s=4`, the unique native kernel vector `z` has `z(a)=z(b)=0`. The lifted kernel is spanned by `(z,0)` and `(0,z)`. Every lifted zero vector therefore vanishes on `(a,0)`, `(a,1)`, `(b,0)` and `(b,1)`. Its projection onto each full endpoint fibre span is zero, so no real or complex state supported within either native endpoint fibre has zero-sector support.

The earlier all-control theorem gives `intersection_pi ker(A_pi)={0}`. Therefore

`intersection_pi ker(H_pi) = {0} direct-sum {0} = {0}`.

There is no common zero mode across candidate and controls. A positive nearest-nonzero gap cannot repair the absence, wrong multiplicity or missing endpoint support of the required zero sector.

The ordered kill rule now applies. No quotient derivation, 119-control endpoint-fixing isomorphism exhaustion or later structural gate is pursued for this rejected architecture.

## Decision

The canonical full bipartite double cover passes native-edge preservation and exact chiral symmetry but fails the mandatory protected-zero-mode gate on every declared grid:

1. no zero mode for `s=2,3`;
2. exact nullity two, never one, for `s=4`;
3. zero entrance and exit support throughout the only lifted zero sector;
4. trivial common kernel across all 120 matchings.

Candidate 4 in this predetermined form is rejected before simulation. The failure is structural and cannot be fixed by choosing a different lifted endpoint convention. Per the kill rule, do not add arbitrary weights, anchors, fingerprints or other gadgets under the Candidate 4 name. Any materially different architecture must be proposed separately and receive a new theorem-first authorization.

No Candidate 4 source, tests, simulation, T9, protocol, held-out work, report, artifact, staging, commit or push is created or authorized by this theorem.