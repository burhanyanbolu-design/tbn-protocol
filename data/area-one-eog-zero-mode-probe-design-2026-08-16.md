# Area One EOG Hierarchical Zero-Mode Probe Design

Date: 2026-08-16
Status: **PRE-PROTOCOL TOPOLOGY-ONLY DISCOVERY**
Authorization: Burhan instructed Kiro to try the Harrow-inspired hierarchical zero-mode direction.

## Purpose

Test whether the current full-coordinate EOG development topology has the structural mechanism used by hierarchical continuous-time quantum walks: an exactly closed compressed subspace, chiral/bipartite symmetry, an isolated zero eigenvalue, and non-negligible zero-sector support connecting natural entrance and exit states.

This is not Candidate 1 or Candidate 2 T9. It introduces no oracle, angle, phase, tuning outcome, lock, held-out input, hardware execution, or performance claim.

## Declared topology

For development grids `(s,R)=(2,6),(3,6),(4,6)`, vertices are full coordinates `(r,c)`, `0<=r<R`, `0<=c<=s`. The ordinary position adjacency is the undirected torus `C_R square C_(s+1)`. Add exactly five weighted overlap channels `((r,s),(r+1,0))`, `r=0,...,4`; no false periodic overlap edge is allowed. Coin and oracle dynamics are not silently identified with this surrogate Hamiltonian.

The natural entrance is `a=(0,0)` and exit is `b=(5,s)`. The Hamiltonian is the real symmetric weighted adjacency `H=A_0+M`, with coincident ordinary/control edges retained additively.

## Declared partitions

Evaluate row cells, column cells, genuine overlap fibers plus interior columns, reflection orbits, and deterministic coarsest equitable refinement seeded by separate entrance, exit, left-boundary, right-boundary, and interior roles. For normalized characteristic matrix `Q`, exact closure requires equal weighted neighbour counts and numerical residual `||(I-QQ^T)AQ||_max <= 1e-12`. Entrance and exit projection errors must each be at most `1e-12`, remain in distinct cells, and quotient dimension must be smaller than the full graph.

## Spectral gates

Bipartiteness is checked combinatorially and by `Gamma A Gamma=-A`. Exact integer Gaussian elimination certifies nullity. A symmetric eigendecomposition constructs the basis-independent zero projector `P0`; numerical zero consistency tolerance is `1e-10`. Required quantities are `w_a=<a|P0|a>`, `w_b=<b|P0|b>`, transfer `|<b|P0|a>|`, and nearest nonzero gap. Each support, transfer, and gap must exceed `1e-12`.

## Matched controls and decision

Exhaust all 119 nonidentity bijections from sources `(r,s)`, `r=0,...,4`, to destinations `(d,0)`, `d=1,...,5`. They retain five channels, the same endpoint sets, weights, and zero tuning parameters. The preregistered descriptive score is `transfer*sqrt(w_a*w_b)*gap`; it cannot override a failed structural gate.

The natural mechanism is supported only if every development grid has a nontrivial exactly closed endpoint-representing quotient, bipartite/chiral symmetry, certified zero mode, endpoint support, transfer, positive isolated gap, and candidate score at or above the fixed 95th percentile of candidate plus controls. Otherwise this exact natural-adjacency mechanism is not supported. No result may be generalized to all EOG architectures or to the existing coined walk.

## Evidence boundary

The probe accepts only this design and an empty dedicated output directory. It must run in the named exact-image container, publish canonical UTF-8 JSON plus one LF, record source/design hashes and runtime identity, and report zero lock accesses, zero held-out accesses, and no new T9. Historical evidence and the frozen Candidate 1 protocol remain unchanged.