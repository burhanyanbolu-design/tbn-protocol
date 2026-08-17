# Area One Candidate 3 Coordinate-Sensitive Structural Test Design

Date: 2026-08-17
Status: **AUTHORIZED THEOREM-FIRST MATHEMATICAL PREPARATION ONLY**
Authorization: Burhan instructed Kiro to proceed after the balanced-weight result exposed matching-permutation label degeneracy.

## Boundary

This work may construct and exactly test one coordinate-sensitive bipartite lift. It is not a transport/performance experiment, parameter search, protocol, T9, lock, held-out access, hardware run, report, evidence artifact, or quantum-advantage claim. Existing Candidate 3 files, the frozen Candidate 1 protocol, historical probes, `research_numerics.py`, and runtime contracts remain unchanged.

## Coordinate-role partition

For `(s,R)=(2,6),(3,6),(4,6)`, retain the previous full-coordinate states and auxiliary hub. Let `N=R(s+1)`, `p=N/2-1`, `g=R-1=5`, `h=p-g`, and `M=4g+h=p+3g`.

Split the previous source and destination cells by an intrinsic declared role:

1. `C0`: entrance `(0,0)`, positive.
2. `C1`: auxiliary hub, negative.
3. `C2G`: the `g` genuine overlap sources `(r,s)`, positive.
4. `C2S`: the `h` engineered support sources, positive.
5. `C3G`: the `g` genuine overlap destinations `(r+1,0)`, negative.
6. `C3S`: the `h` engineered support destinations, negative.
7. `C4`: exit `(5,s)`, positive.

The seven cells have sizes `(1,1,g,h,g,h,1)`, cover every state exactly once, and strictly compress every declared lift.

## Fixed weights

Use the primitive positive integer role contrast obtained after normalizing the support-role factor to `1`: factor `2` for genuine-role vertices and factor `1` for support-role vertices. Thus `gcd(2,1)=1`; there is no residual scale, free scalar, or tuned scalar.

- `C0-C1`: weight `1`.
- Hub to `C2G`: weight `2`; hub to `C2S`: weight `1`.
- Every matched `C2-C3` edge: the same weight `M`.
- `C3G-C4`: weight `2`; `C3S-C4`: weight `1`.

The candidate uses identity matching within each role, so its first five matched edges are exactly the genuine non-wrapping EOG overlap pairs. The false periodic pair remains forbidden.

## Exact mechanism

For unnormalized seven-cell incidence `P`, the candidate must satisfy exact rational `H P=P B`. Ordered quotient rows are:

- `(0,1,0,0,0,0,0)`
- `(1,0,2g,h,0,0,0)`
- `(0,2,0,0,M,0,0)`
- `(0,1,0,0,0,M,0)`
- `(0,0,M,0,0,0,2)`
- `(0,0,0,M,0,0,1)`
- `(0,0,0,0,2g,h,0)`

The graph must be connected and satisfy exact `Gamma H Gamma=-H`. Its fixed cell-constant zero vector is `z=(-M,0,2,1,0,0,-M)`. Exact cancellation follows from `M=4g+h`. Its norm is `M(2M+1)`, so both endpoint weights and the absolute zero-projector endpoint matrix element are `M/(2M+1)`.

Writing `H=[[0,K],[K^T,0]]`, exact elimination must give `rank(K)=p+1` and full-H nullity one. Exact rational LDL decomposition of `K^T K-I` must have only positive pivots on every declared grid, proving the nonzero Hamiltonian gap is strictly greater than `1` before any binary64 diagnostic.

## Fair cross-role controls and non-isomorphism theorem

A control is any perfect matching that preserves every vertex, every boundary weight, the constant matched-edge weight, edge count, complete edge-weight multiset, and every vertex's weighted degree, but crosses exactly `k` genuine sources to support destinations and therefore exactly `k` support sources to genuine destinations. Use canonical swaps for every `k=1,...,min(g,h)`; no control weight is retuned.

Candidate and controls are equally expressive weighted matching graphs. Because only endpoints of constant-`M` matched edges are permuted, each named vertex retains exactly its candidate weighted degree, not merely the same global weighted-degree multiset. They are nevertheless not weighted-graph isomorphic: candidate matched edges join equal-strength source/destination classes, while every cross-role control introduces matched edges between weighted degrees `M+2` and `M+1`. The multiset of `(edge weight, endpoint weighted-degree pair)` therefore differs exactly.

The first possible entrance-to-exit walk has length four. The exact candidate moment is

`<exit|H^4|entrance> = M^2`.

For a control with cross-count `k`, it is exactly `M(M-k)`. The difference `kM>0` proves coordinate-role alignment changes a structural endpoint matrix moment of the declared isolated Hamiltonian while preserving local weighted strength, and breaks the previous endpoint-fixing permutation degeneracy. This is not an observed transport probability, a time-domain transfer result, or evidence that EOG geometry or quantum transport causes an advantage.

## Tests and decision

Tests must independently reconstruct cells, weights, quotient closure, chiral symmetry, zero vector, endpoint formulas, `K` rank, exact LDL gap certificate, canonical cross-role controls, fairness invariants, weighted-degree non-isomorphism, and the fourth-moment formulas. Mutations must reject invalid role coverage, weights, closure, chiral edges, false periodic edges, endpoint imbalance, extra nullity, nonpositive LDL pivots, invalid cross controls, unfair weight multisets, and false moment claims.

Passing means a coordinate-sensitive exact mechanism exists and the prior permutation-isomorphism blocker is removed for declared cross-role controls. It does not establish useful time-domain transfer, superiority to all fair controls, scalability, EOG-specific quantum advantage, or permission to simulate. Any governed probe requires a separate architecture/control review and explicit approval.