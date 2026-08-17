# Area One Candidate 5 Strict Endpoint-Quotient Obstruction

Date: 2026-08-17  
Status: **REJECTED AT THE MANDATORY STRICT ENDPOINT-QUOTIENT GATE**

## Scope and boundary

This is the third design-only Candidate 5 theorem for `(s,R)=(2,6),(3,6),(4,6)`. It asks whether the identity Candidate 5 lift admits any strict exact equitable quotient that represents the lifted entrance and exit as distinct singleton cells.

Only `a_L` and `b_L` are seeded. The calculation uses no labels for `q`, sublattices, roots, rows, columns, coordinates, rungs, native/matching provenance or pair identities. Construction metadata builds the aggregate weighted adjacency and is then discarded.

This theorem contains no source module, test file, control exhaustion, dynamics, simulation, transport probability, parameter search, T9, protocol, lock, held-out access, hardware execution, report, experiment artifact, staging, commit or push.

## Fixed Candidate 5 identity lift

For `n=6(s+1)`, let `A_id` be the native torus-plus-identity-matching aggregate adjacency. Define

`B_id=6I+A_id`, `c=B_id 1`, `K_id=[B_id;c^T]`, and `H_id=[[0,K_id],[K_id^T,0]]`.

The full graph sizes are `2n+1=37,49,61`. The declared endpoints are the surplus-side copies `a_L` and `b_L`.

## Exact quotient criterion

Start from the three-cell seed

`S=({a_L},{b_L},V\{a_L,b_L})`.

For a current partition `P`, vertices `u` and `v` in one cell remain together exactly when, for every target cell `D` in `P`,

`sum_(x in D) H_id[u,x] = sum_(x in D) H_id[v,x]`.

Repeated simultaneous splitting by these exact integer weighted-neighbour signatures terminates at a stable equitable partition `P*`.

`P*` is the coarsest equitable partition refining `S`. To see this, let `Q` be any equitable partition refining `S`. Inductively, every current refinement cell is a union of `Q`-cells. Equitability makes the weighted sum into each such union constant on every `Q`-cell, so each split still leaves every `Q`-cell inside one new cell. Hence `Q` refines every round and therefore refines `P*`.

For an equitable partition `P`, let `Q_P` be its normalized cell-indicator matrix. The corresponding exact normalized quotient is `H_P=Q_P^T H_id Q_P`, with `H_id Q_P=Q_P H_P`. Here **strict** means `|P|<|V|`.

Any partition with distinct singleton cells `{a_L}` and `{b_L}` necessarily refines `S`. If `P*` is discrete, every such exact equitable partition must equal the discrete partition. No strict endpoint-representing quotient can then exist.

## Exact refinement results

An independently reconstructed integer oracle built each aggregate identity lift and refined only from the two endpoint singleton cells. The stable partitions were discrete:

| grid | full size | refinement cell counts | stable cells | result |
|---|---:|---|---:|---|
| `s=2` | 37 | `3 -> 14 -> 26 -> 35 -> 37` | 37 | discrete |
| `s=3` | 49 | `3 -> 14 -> 27 -> 41 -> 48 -> 49` | 49 | discrete |
| `s=4` | 61 | `3 -> 14 -> 32 -> 50 -> 59 -> 61` | 61 | discrete |

Every stable cell is a singleton and direct weighted-neighbour checks certify exact equitability.

The complete cell-size histograms by round were:

- `s=2`: `{1:2,35:1}`, `{1:9,2:1,4:1,6:2,10:1}`, `{1:21,2:3,4:1,6:1}`, `{1:33,2:2}`, `{1:37}`;
- `s=3`: `{1:2,47:1}`, `{1:9,2:1,6:1,10:2,12:1}`, `{1:21,2:3,6:2,10:1}`, `{1:37,2:3,6:1}`, `{1:47,2:1}`, `{1:49}`;
- `s=4`: `{1:2,59:1}`, `{1:9,2:1,6:1,10:1,16:1,18:1}`, `{1:25,2:2,4:1,6:3,10:1}`, `{1:45,2:3,4:1,6:1}`, `{1:57,2:2}`, `{1:61}`.

## Independent colour-signature oracle

A second implementation independently rebuilt the same aggregate lifts and represented the current partition by integer colours rather than explicit cell lists. It repeatedly replaced each colour by the exact tuple consisting of the old colour and weighted sums into every current colour class. It seeded only `a_L`, `b_L`, and the unmarked remainder.

This oracle produced the same round counts, the same cell-size histograms and the same final discrete partitions on all three grids. No metadata-defined cell was injected by either implementation.

## Obstruction and interpretation

Because the coarsest endpoint-seeded exact equitable partition is discrete on every declared grid, Candidate 5 has no strict exact quotient with distinct singleton entrance and exit cells. This is a universal obstruction over all such partitions, not a failure of only row, column, layer, fibre or symmetry guesses.

The positive earlier gates remain true and preserved: Candidate 5 has exact chirality, one common endpoint-supported zero mode, a uniform positive gap bound, pointwise fair controls and no endpoint-fixing candidate/control isomorphism. None of those properties implies quotient closure.

Relaxing the endpoint requirement to non-singleton fibre states would define a different mechanism and is not authorized under the established Area One endpoint-representing quotient contract.

## Decision

Candidate 5 is rejected at the mandatory strict endpoint-quotient gate before dynamics. Per the kill rule, do not add labels, weights, symmetry constraints or quotient-specific gadgets to manufacture compression under the Candidate 5 name.

This result blocks Candidate 5 simulation and T9. It does not prove every EOG-derived architecture lacks an endpoint quotient, invalidate the earlier structural theorems, or alter the frozen Candidate 1 rejection.

No Candidate 5 source, tests, control rerun, quotient matrix, dynamics, simulation, T9, protocol, held-out work, hardware run, grant claim, report, artifact, staging, commit or push is created or authorized by this theorem.