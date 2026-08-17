# Area One Candidate 3 Native Rooted-Type Compatibility Design

Date: 2026-08-17  
Status: **DIRECT BIPARTITE/CHIRAL INCOMPATIBILITY / NECESSARY-ONLY**

## Scope and boundary

This step asks whether the fixed native EOG backbone supplies genuine rooted types and whether the direct natural Candidate 3 bipartite/chiral mechanism survives exact structural gates. It is restricted to `(s,R)=(2,6),(3,6),(4,6)` and proves no separation.

This is structural preparation only. It uses no NumPy, numerical eigensolver, simulation, time evolution, probabilities, moments as transport evidence, parameter search, T9, protocol or lock, held-out access, Docker, report, experiment artifact, staging, commit, push, or historical-file change.

## Fixed native family and controls

For width `w=s+1`, the vertices are `(r,c)`, `0<=r<6`, `0<=c<w`. The native backbone is the unweighted Cartesian torus `C_6 square C_w`. The entrance and exit are

`a=(0,0)` and `b=(5,s)`.

The five genuine source and destination roots are

`S_i=(i,s)` and `D_i=(i+1,0)`, for `i=0,...,4`.

A control is one of all `5!=120` permutations `pi` and adds five unit channels `S_i--D_pi(i)`. The candidate is the genuine identity matching. Native and matching channels are retained separately as unit-weight edges. If a nonidentity matching channel coincides with a native edge, the exact symmetric adjacency entry is therefore `2`; this is an additive multigraph entry, not a changed channel weight.

Every control gives each named vertex the same weighted degree as the identity candidate. Every named vertex also has the same multiset of incident channel weights when coincident native and matching channels are retained separately: the channel weights are all exactly one. Both properties are certified for all 120 controls on all three grids.

## Native rooted-signature theorem

Delete the five matching channels and compute shortest-path distances in the native torus itself. No declared type metadata participates. For a root `v`, define its signature as

`tau(v)=(dist_native(a,v), dist_native(b,v))`.

Exact breadth-first reconstruction gives, on every declared width,

- sources: `((1,1),(2,2),(3,3),(4,2),(3,1))`;
- destinations: `((1,3),(2,4),(3,3),(2,2),(1,1))`.

The dedicated implication certificate derives these signatures from native weighted-backbone distances and checks distinctness within each preserved side. A native weighted graph automorphism maps paths to equal-weight paths; if it fixes both endpoints, it therefore preserves both endpoint distances. Consequently, any such automorphism that also preserves the source side and destination side must fix every genuine root pointwise. The separate per-map validator additionally rejects any proposed bijection that fails to preserve the native weighted adjacency. This is the only automorphism conclusion asserted. In particular, no stronger claim about the full automorphism group is made.

The native signatures remove the repeated-type stabilizer witness from the preceding theorem. The exact disposition is only

`obstruction absent / no conclusion`.

Trivial rooted-type stabilizers never prove separation, and every affirmative separation claim must fail closed.

## Direct bipartite/chiral incompatibility

The identity candidate is non-bipartite on every declared grid, by an explicit combinatorial witness rather than a numerical spectrum:

- for `s=2`, the row-zero horizontal `C_3` is an odd native cycle;
- for `s=4`, the row-zero horizontal `C_5` is an odd native cycle;
- for `s=3`, the native torus is parity-colored by `(r+c) mod 2`, but the identity edge `S_0=(0,3)--D_0=(1,0)` joins two vertices of the same parity.

Thus the direct natural Candidate 3 bipartite/chiral mechanism is incompatible.

## Exact endpoint-seeded refinement

Start from the three-cell partition

`{a}, {b}, V\{a,b}`

and repeatedly split each cell by its exact vector of weighted neighbour sums into the current cells. On the identity candidate this deterministic equitable refinement becomes discrete:

- `18` singleton cells for `s=2`;
- `24` singleton cells for `s=3`;
- `30` singleton cells for `s=4`.

Therefore no strict endpoint-representing compression survives the coarsest exact refinement of that seed.

The natural row, column, and genuine-overlap-fiber/interior-column partitions are reconstructed independently and tested against the conjunction: exact equitability, singleton representation of both endpoints, distinct endpoint cells, and strict compression. Each fails the conjunction. The native reflection `(r,c)->(5-r,s-c)` is also reconstructed; including its orbits merges `a` with `b`, so it is not an endpoint-separating representation.

## Exact nullspaces

The production exact nullspace calculation gives candidate nullities

`nullity(H_2)=0, nullity(H_3)=0, nullity(H_4)=1`.

An independent modular-rank oracle over the fixed checked prime `101`, accepting only integral `Fraction` entries, certifies ranks `18`, `24`, and `29`. For `s=4`, the modular rank is an exact lower bound over the rationals, while the following independently supplied nonzero integer kernel witness gives the matching upper bound `29`; therefore the exact nullity is one.

```text
 0 -1 -1  0  1
 1  1  0 -1 -1
-1  0  1  1  0
 0 -1 -1  0  1
 1  1  0 -1 -1
-1  0  1  1  0
```

Its exact residual is zero, and its entrance coordinate `(0,0)` and exit coordinate `(5,4)` are both exactly zero. The production `s=4` nullspace basis is compared with this independent witness up to a nonzero exact scalar. Hence even the sole candidate zero mode has no endpoint support.

## All-control common-kernel theorem

Let `H_pi x=0` for every one of the 120 matching controls. Comparing controls that differ by a transposition in the image of one source shows

`x(D_0)=x(D_1)=...=x(D_4)`.

Reading the same control differences in destination rows shows

`x(S_0)=x(S_1)=...=x(S_4)`.

These are the eight exact common-kernel difference constraints: four destination differences and four source differences. Exact elimination is checked in two equivalent ways on each grid:

1. stack all rows of all 120 exact control adjacencies;
2. append the eight side-constant constraints to the identity adjacency.

Both systems have full column ranks `18`, `24`, and `30`, respectively, certified independently by modular full-rank checks. The intersection of the 120 kernels is therefore `{0}`. In particular, there is no endpoint-supported common zero mode.

## Fail-closed validation

The implementation reconstructs and validates the fixed coordinate labels, all native torus edges, endpoints, source and destination root sets, all 120 bijective matchings, and the identity candidate adjacency. Every matrix entry is a nonnegative exact `Fraction`, and every matrix is symmetric and loop-free. Native edges are required to remain present in `H`.

It rejects undeclared grids, malformed permutations, changed labels, changed endpoints, changed root sets, omitted native edges, foreign edges, changed channel weights, a nonidentity candidate, endpoint-moving or nonbijective automorphism maps, endpoint-fixed side-preserving bijections that are not native weighted automorphisms, fake metadata-only type claims, and false bipartite, compression, compatibility, or separation claims.

The independent tests do not import production grid, signature, matrix, partition, rank, or control constants as expected-value oracles. They reconstruct coordinates, native distances, additive exact matrices, partitions and refinement, fairness, transposition difference rows, and the all-control stacked systems. A fixed-prime modular-rank oracle requiring integral Fractions certifies candidate and common-kernel ranks; the displayed independent `s=4` integer vector certifies the exact residual, endpoint zeros, one-dimensional rational nullspace, and agreement with the production basis up to nonzero scalar. All 120 controls are exhausted on all three grids wherever controls matter.

## Final assessment

- native rooted types: **yes**;
- repeated-type witness: **obstruction absent / no conclusion**;
- direct mechanism assessment: **direct natural Candidate 3 bipartite/chiral mechanism incompatible**;
- separation: **no conclusion**.

This theorem certifies only **direct natural Candidate 3 bipartite/chiral mechanism incompatible**. It does not claim every direct mechanism is impossible, authorize an affirmative separation statement, or authorize any experimental next phase.
