# Area One Candidate 3 Zero-Mode-Neutral Anchor Structural Test Design

Date: 2026-08-17
Status: **AUTHORIZED THEOREM-FIRST MATHEMATICAL PREPARATION ONLY**
Authorization: Burhan instructed Kiro to continue to the next Candidate 3 step.

## Boundary and purpose

The direct coordinate-fingerprint lift proves an engineered identity-pairing theorem, but its controls change the zero-mode endpoint coefficients and projector element. This refinement must keep those quantities exactly common across the candidate and all genuine-only controls, while postponing identity sensitivity beyond the fourth and sixth endpoint moments.

This is not a transport/performance experiment, protocol, parameter search, T9, lock, held-out access, hardware run, report, evidence artifact, or quantum-advantage claim. Existing Candidate 3 files and frozen Area One boundaries remain unchanged.

## Fixed minimal anchor gadget

Start from the seven-cell constant-matched-weight family with genuine boundary factor `2`, support factor `1`, `g=5`, `h=p-g`, and `M=4g+h`.

For each genuine source and genuine destination with row index `r`, set the fixed coordinate weight `q_r=r+2`, giving `(2,3,4,5,6)`. Attach the length-two bipartite pendant path

`genuine vertex --q_r-- anchor --M-- terminal`.

A one-edge leaf is impossible: its zero-mode equation would force the nonzero genuine-source coefficient to vanish. Two edges are therefore the minimum local pendant depth. The terminal weight is fixed to `T=M`; it is not tuned.

## Exact partition, zero mode, and gap

Use 35 ordered cells: entrance; hub; five singleton genuine sources; support-source cell; five singleton genuine destinations; support-destination cell; exit; then singleton anchor and terminal cells for each of the ten genuine vertices. Enlarged graph sizes are `39,45,51`, so the partition strictly compresses every declared grid and exactly closes `HP=PB` for candidate and controls.

Use the integer-scaled common zero vector:

- entrance and exit: `-M^2`;
- each genuine source: `2M`;
- each support source: `M`;
- source-anchor terminals: `-2q_r`;
- hub, all destinations, all anchors, and destination terminals: `0`.

It applies unchanged to every genuine-destination permutation. Its norm is

`N=M^3(2M+1)+360`.

Thus candidate and controls have identical endpoint weights and absolute static zero-projector endpoint element `M^4/N`. Exact elimination must prove the candidate's full off-diagonal rank and nullity one. For every control, the uniform proof uses the ordered negative columns hub, five source anchors, the `p` matched destinations, and five destination terminals, with witness rows entrance, five source terminals, the `p` sources, and five destination anchors. Their square minor is triangular with diagonal `(1,M,...,M)`, so it is nonsingular for every declared permutation and proves `rank(K)=p+11` and full nullity one without repeating generic elimination. Independent tests must still exact-rank every control.

The old `gap>1` theorem is not inherited. Let `G=K^T K`, `m=p+11`, and

`tr(G)=181+2M+pM^2+10M^2`.

Because `G` is positive-definite integral, `det(G)>=1`, giving the exact uniform bound

`gap(H)>=tr(G)^(-(m-1)/2)>0`.

Binary64 may diagnose the gap only after this exact certificate passes.

## Fair controls and first separating moment

Exhaust all `5!-1=119` nonidentity permutations of genuine destinations; support matching and all anchor attachments remain fixed. Every control preserves every named vertex, every fixed edge, edge-weight multiset, and each named vertex's weighted degree within the enlarged family.

Candidate and controls have identical endpoint moments through order six:

- odd moments vanish by bipartiteness;
- moments below four vanish by endpoint distance;
- `<x|H^4|e>=M^2`;
- `<x|H^6|e>=M^2(M+1)^2+720M`.

The first identity-sensitive moment is order eight. For genuine permutation `pi`,

`Delta_8(pi)=<x|H_candidate^8|e>-<x|H_pi^8|e>`

`=2M sum_r (q_r^2-q_pi(r)^2)^2 > 0`.

The candidate's matched `M` edges join genuine vertices of equal weighted degree `M+2+q_r`; every nonidentity control introduces an unequal pair. The edge-degree profile therefore proves non-isomorphism. Terminal edges also have weight `M`, but their endpoint degree pairs are disjoint from the matching-edge range and cannot mask the invariant.

## Tests and decision

Tests must independently reconstruct all vertices, 35 cells, fixed gadgets, candidate, and 119 controls on each grid. They must certify exact quotient closure, chiral symmetry, common zero vector/norm/projector, rank/nullity, trace/determinant gap logic, pointwise degree and edge-weight fairness, non-isomorphism, equality through `H^6`, strict `H^8` formula, and fail-closed mutations.

Passing proves only an engineered decorated-graph identity mechanism with a common zero sector and delayed structural separation. It does not retain the ungadgeted numerical degrees or old projector value; those are preserved only across the enlarged candidate/control family. It does not show natural EOG geometry, useful finite-time transfer, quantum advantage, or permission to simulate.

## NOT in scope

- Time evolution, probabilities, horizons, thresholds, or protocol freeze.
- Claims that the coordinate anchor occurs naturally in EOG hardware.
- Retaining the old `gap>1` bound without a new proof.
- Held-out data, hardware, runtime/container changes, reports, or evidence artifacts.

```text
seven-cell role seed
  + fixed q_r two-edge anchors
  -> common zero sector + common H^4/H^6
  -> 119 genuine controls
  -> first strict identity separation at H^8
```
