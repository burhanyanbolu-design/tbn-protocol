# Area One Candidate 3 Balanced-Weight Structural Test Design

Date: 2026-08-17
Status: **AUTHORIZED THEOREM-FIRST MATHEMATICAL PREPARATION ONLY**
Authorization: Burhan instructed Kiro to proceed with the recommended balanced-weight mathematical design.

## Boundary

This work may analytically redesign and structurally test the Candidate 3 quotient lift. It is not a performance or transport experiment, parameter search, protocol, T9, lock, held-out access, hardware run, or quantum-advantage claim. It must not modify the completed unit-weight Candidate 3 seed, frozen Candidate 1 protocol, historical probes, `research_numerics.py`, container contract, or evidence artifacts. No report or experiment artifact is authorized.

## Fixed balanced construction

Use the same full-coordinate states, auxiliary hub, ordered cells and deterministic matching as the completed unit-weight seed for `(s,R)=(2,6),(3,6),(4,6)`. Let `N=R(s+1)` and `p=N/2-1`, with cell sizes `(1,1,p,p,1)`.

Assign fixed positive edge weights by cell boundary:

- `C0-C1`: weight `1`.
- `C1-C2`: weight `1` on every edge.
- matched `C2[j]-C3[j]`: weight `p` on every edge.
- `C3-C4`: weight `1` on every edge.

The first five matched edges remain exactly the genuine non-wrapping EOG overlap pairs. Remaining matched edges remain engineered support channels. The false periodic pair `(5,s)-(0,0)` is forbidden. The size-derived integer `p` is fixed by the graph and is not a tunable parameter.

## Exact quotient and chiral mechanism

For unnormalized cell incidence `P`, exact rational closure must be `H P = P B`, with directional quotient rows:

`(0,1,0,0,0)`, `(1,0,p,0,0)`, `(0,1,0,p,0)`, `(0,0,p,0,1)`, `(0,0,0,p,0)`.

The normalized quotient has path couplings `(1,sqrt(p),p,sqrt(p))`; these fixed couplings support the exactly balanced endpoint zero-mode coefficients proved below. The full lift remains connected and bipartite under positive cells `C0,C2,C4` and negative cells `C1,C3`, with exact `Gamma H Gamma=-H` and sublattice imbalance one.

## Exact zero mode, support and gap theorem

The cell-constant vector must be `z=(-p,0,1,0,-p)`. Its exact squared norm is `p(2p+1)`. Therefore entrance weight, exit weight and absolute zero-sector endpoint transfer are all exactly `p/(2p+1)`, at least `8/17` on the declared grids and approaching `1/2` rather than zero.

Write the bipartite Hamiltonian as `H=[[0,K],[K^T,0]]`. The off-diagonal block must have full column rank `p+1`, proving exact nullity one. It has `p-1` singular values equal to `p`. The remaining squared singular values `lambda_-` and `lambda_+` are the roots of

`x^2-(p+1)^2 x+p(2p+1)=0`.

For every declared `p>1`, evaluating this polynomial at `1` and `2` gives `p(p-1)>0` and `2-3p<0`, proving `1<lambda_-<2`. Thus the nearest nonzero spectral gap is `sqrt(lambda_-)`, strictly between `1` and `sqrt(2)`. Binary64 eigensolving may diagnose this value only after all exact certificates pass.

## Matched-control degeneracy theorem

Before any performance experiment, test whether matching permutations are distinct mechanisms. For any bijection `pi` of the `p` matched channels, the graph obtained by replacing `C2[j]-C3[j]` with `C2[j]-C3[pi(j)]` is related to the declared graph by a vertex permutation that fixes `C0`, `C1`, every `C2` vertex and `C4`, and relabels only `C3`. Because all `C3` vertices have the same edge to `C4`, this is an exact endpoint-fixing weighted-graph isomorphism.

Consequently every pure matching-permutation control has exactly the same spectrum and, for the isolated weighted-graph Hamiltonian defined here, the same entrance/exit matrix elements for every analytic function of `H`, including continuous-time evolution. This does not extend to added coordinate-sensitive terms, channel-resolved observables, unconjugated drives, or hardware noise tied to physical channel identity. Pure permutation controls therefore cannot establish an EOG-specific effect, and no simulation may portray their equality as candidate success.

## Structural tests and decision

Tests must independently reconstruct coordinates, cells, weights, quotient closure, chiral symmetry, exact rank/nullity, zero-vector equation, endpoint formulas, spectral polynomial certificates and endpoint-fixing permutation conjugacy for all declared grids. Mutations must reject malformed weights, closure or chiral breaks, false periodic edges, endpoint imbalance, extra nullity, invalid numerical gaps and invalid permutations.

Passing means the weighted lift repairs zero-mode endpoint balance and has a size-stable exact gap theorem. It also establishes that the present globally symmetric matching architecture is label-degenerate against permutation controls. The next research step, if separately authorized, must design coordinate-sensitive bipartite structure that breaks this isomorphism while retaining exact closure and matched control fairness. No governed probe or T9 is authorized by this design.