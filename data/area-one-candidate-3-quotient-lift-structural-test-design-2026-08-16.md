# Area One Candidate 3 Quotient-Lift Structural Test Design

Date: 2026-08-16
Status: **AUTHORIZED PRE-PROTOCOL MATHEMATICAL PREPARATION ONLY**
Authorization: Burhan instructed Kiro to prepare Candidate 3 mathematical tests after sending the SparQ application-material request.

## Boundary

This work may construct and test a theorem-guided Hamiltonian seed. It is not a Candidate 3 protocol, parameter search, performance experiment, T9, lock, held-out access, hardware run, or quantum-advantage claim. Candidate 1, Candidate 2, the historical zero-mode probe, `research_numerics.py`, the research container contract, and all evidence artifacts remain unchanged.

## Exact seed construction

For structural grids `(s,R)=(2,6),(3,6),(4,6)`, retain every full EOG coordinate `(r,c)`, `0<=r<R`, `0<=c<=s`, and add one auxiliary hub state. Let `N=R(s+1)`, `p=N/2-1`, and partition the `N+1=2p+3` states into five ordered cells of sizes `(1,1,p,p,1)`:

1. `C0`: natural entrance `(0,0)`.
2. `C1`: one auxiliary hub.
3. `C2`: all five genuine overlap sources `(r,s)`, `r=0,...,4`, followed by the first deterministic half of unused coordinates.
4. `C3`: all five genuine overlap destinations `(r+1,0)`, `r=0,...,4`, followed by the second deterministic half of unused coordinates.
5. `C4`: natural exit `(5,s)`.

Add unit-weight undirected edges from `C0` to `C1`, from `C1` to every state in `C2`, from each `C2[j]` to `C3[j]`, and from every state in `C3` to `C4`. The first five matched `C2-C3` edges are exactly the genuine non-wrapping EOG overlap pairs. Extra matched edges are engineered support channels, not overlap claims. The false periodic pair `(5,s)-(0,0)` is forbidden. There are no free weights, angles, phases, oracle, coin, or outcome inputs.

## Required exact mechanism

With unnormalized cell-incidence matrix `P`, the lift must satisfy `H P = P B` exactly over rational arithmetic for the five-cell quotient. The quotient is an odd path with directional neighbour-count matrix rows `(0,1,0,0,0)`, `(1,0,p,0,0)`, `(0,1,0,1,0)`, `(0,0,1,0,1)`, `(0,0,0,p,0)`.

The full graph must be connected and bipartite with `C0,C2,C4` on one sublattice and `C1,C3` on the other, so `Gamma H Gamma=-H` exactly. Sublattice sizes differ by one. The exact candidate vector is constant by cell with values `(-p,0,1,0,-1)`; it must satisfy `H z=0`, have nonzero entrance and exit coordinates, and span the complete nullspace. A binary64 eigensolver may only diagnose the nearest nonzero gap after exact nullity is established; it must find one numerical zero and a finite positive gap above `1e-12`.

## Structural tests and decision

Tests must independently reconstruct indexing, genuine pairs, quotient closure, chiral symmetry, exact rank/nullity and the zero-vector equation for all three structural grids. Mutation tests must reject malformed partitions, asymmetric or looped matrices, nonpositive edge weights, closure breaks, same-sublattice edges, endpoint-zero vectors, even/non-compressing quotients, extra nullity, false periodic overlap edges and nonfinite gap diagnostics.

Passing these tests means only that a mathematically coherent seed exists and is ready for independent architecture/control review. It does not establish useful transport, superiority to controls, EOG-specific advantage, scalability, hardware suitability or permission to simulate outcomes. Before any governed probe, a separate approved design must define equally expressive controls and fresh development-validation configurations.