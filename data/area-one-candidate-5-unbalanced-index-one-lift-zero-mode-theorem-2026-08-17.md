# Area One Candidate 5 Unbalanced Index-One Lift Zero-Mode Theorem

Date: 2026-08-17  
Status: **STRUCTURAL ZERO-MODE GATE PASSED / EOG-SPECIFICITY UNPROVED**

## Scope and boundary

This is the first design-only Candidate 5 theorem for `(s,R)=(2,6),(3,6),(4,6)`. It responds directly to Candidate 4's even-nullity obstruction by using sublattices whose sizes differ by one. No weight search, row fingerprint, time evolution, transport probability, simulation, T9, protocol, lock, held-out access, hardware execution, report or experiment artifact is permitted.

Candidate 5 is an engineered EOG-derived benchmark, not Harrow's construction and not natural EOG/Harrow evidence. Passing this theorem does not establish candidate/control separation or useful dynamics.

## Native family

Let `n=6(s+1)` and let `A_pi` be the exact symmetric native torus-plus-matching adjacency from Candidate 3. The identity matching is the candidate and all `120` permutations are the candidate-plus-control family. Native and matching channels remain separate unit channels when they coincide.

For every permutation, the pointwise degree vector is the same:

`d=A_pi 1`, with `d_v=5` on the ten source/destination roots and `d_v=4` elsewhere.

Hence the exact common maximum weighted degree is `Delta=5`.

## Rejected naive index extension

A direct unbalanced extension would use `K_pi=[A_pi;r^T]` for one extra row `r`. This cannot repair the declared family. On `s=4`, the native candidate has a kernel vector `z` with `z(a)=z(b)=0`. The surplus-side vector `(z,0)` is in `ker(K_pi^T)` for every possible `r`.

If `K_pi` has full column rank, that inherited endpoint-zero vector is the unique lifted zero mode. If it does not, the lifted nullity is at least three. Therefore no one-row stack of the unchanged native adjacency can give both exact nullity one and nonzero native endpoint support on `s=4`. Because the gate is conjunctive across all three declared grids, this failure rejects the naive architecture. Candidate 5 does not use it.

## Declared degree-completed shifted-rung lift

Fix, without search,

`t=Delta+1=6`, `B_pi=tI+A_pi`, and `c=B_pi 1=t1+d`.

Thus `c_v=11` on the ten roots and `c_v=10` elsewhere, independently of `pi`.

The left sublattice contains one copy `v_L` of every native vertex plus one index vertex `q`; the right sublattice contains one copy `v_R` of every native vertex. Define

`K_pi=[B_pi;c^T]` in `Q^((n+1) x n)` and `H_pi=[[0,K_pi],[K_pi^T,0]]`.

For each undirected unit channel `{u,v}` contributing one unit to both `(A_pi)_(u,v)` and `(A_pi)_(v,u)`, the lift contains the two unit channels `u_L--v_R` and `v_L--u_R`. Native and matching channels are lifted separately. If a native and matching channel coincide, each crossed location contains two parallel unit channels with total Hamiltonian weight two. Each native vertex also has a weight-six rung `v_L--v_R`, and the index vertex has edge `q--v_R` of weight `c_v`. These additions are deterministic degree-derived structure, not native EOG edges.

The lifted sizes are `2n+1=37,49,61`.

## Exact chiral index theorem

The left and right sides are an exact bipartition. With `Gamma=diag(I_(n+1),-I_n)`, `Gamma H_pi Gamma=-H_pi`.

For any `(n+1) x n` matrix `K` of rank `r`,

`nullity([[0,K],[K^T,0]])=2(n-r)+1`.

Since `A_pi` is symmetric with nonnegative row sums at most five, every eigenvalue lies in `[-5,5]`. Therefore `B_pi=6I+A_pi` is positive definite with `lambda_min(B_pi)>=1`. It is invertible, so `K_pi` has full column rank `n`. Every candidate and control consequently has exact nullity one.

## Common endpoint-supported zero mode

Write a surplus-side vector as `(x,eta)`. Because `c=B_pi 1`,

`K_pi^T(x,eta)=B_pi(x+eta 1)`.

Invertibility of `B_pi` gives the same one-dimensional kernel for all `120` matchings:

`w=((1_n,-1),0_n)`.

Its exact squared norm is `n+1`. Declare the entrance and exit to be the surplus-side copies `a_L` and `b_L`. The normalized zero mode has coefficient `1/sqrt(n+1)` at both, and the signed zero-projector matrix element is `<b_L|P_0|a_L>=1/(n+1)`, namely `1/19`, `1/25`, and `1/31`.

"Endpoint-supported" here means nonzero endpoint coefficients. The mode is uniform on every original surplus-side vertex, not localized only at the endpoints, and it vanishes on the entire right sublattice.

## Rigorous uniform positive gap bound

The nonzero absolute eigenvalues of `H_pi` are the singular values of `K_pi`. For every vector `y`,

`||K_pi y||^2=||B_pi y||^2+(c^T y)^2 >= ||y||^2`.

Thus every candidate and control has the rigorous uniform lower bound `gap(H_pi)>=1`. This does not claim an exact evaluation of the actual gap, equal actual gaps across controls, or equality to one.

## Pointwise fairness and exact checks

The structural object is a weighted channel multigraph: parallel native and matching channels remain separately recorded even when the Hamiltonian entries add. Under that convention, every control preserves each named vertex's weighted degree and separate incident channel-weight multiset. The exact multisets are

- root `v_L`: `{6,1^5}`; nonroot `v_L`: `{6,1^4}`;
- root `v_R`: `{11,6,1^5}`; nonroot `v_R`: `{10,6,1^4}`;
- index vertex `q`: `{11^10,10^(n-10)}`.

The corresponding weighted degrees are `c_v` for `v_L`, `2c_v` for `v_R`, and `sum_v c_v=10n+10`, equal to `190`, `250`, or `310`, for `q`.

This is candidate/control fairness, not preservation of native numerical degrees. The weight-six rungs and weight-10/11 index star materially alter the graph. The separate-channel multiset conclusion follows from the declared channel lifting rule; collapsing parallel channels into one weighted edge would be a different structural object and is not permitted.

A direct exact summed-matrix check exhausted all 120 permutations on all three grids for the common 4/5 native degree vector, common 10/11 index row, zero residual and fixed index degree. Exact candidate ranks of `K` were `18`, `24`, and `30`, producing nullity one on lifted sizes `37`, `49`, and `61`. The command did not independently reconstruct decomposed channel records.

## Anti-tautology and evidence boundary

The zero mode is manufactured by the universal identity `c=B1`. The same argument works for any finite undirected graph family with symmetric nonnegative weighted adjacency, a common pointwise degree vector, and a common weighted-degree bound `Delta`, after choosing `t>Delta` and setting `c_pi=(tI+A_pi)1`. Its existence is therefore not an EOG-specific result, and the common zero mode itself cannot distinguish the genuine matching from a control.

The actual EOG topology and pair identity remain present in the off-diagonal `A_pi` channels, but no quotient, endpoint-fixing non-isomorphism, spectral discriminator, structural moment or transport effect has yet been proved. Large rung and star weights may dominate later behaviour and must be treated as a scientific risk, not hidden.

## Decision and next gate

Candidate 5 passes only the first engineered structural gate: exact chirality, common unique zero mode with nonzero declared endpoint coefficients, exact nullity one, a uniform positive gap bound and pointwise candidate/control fairness.

It is not yet promoted as an EOG mechanism. The next separately bounded theorem must first fix the structural object and marked data. For every `pi != id`, it must decide whether there exists a permutation matrix `P` satisfying `P^T H_id P=H_pi`, `P e_(a_L)=e_(a_L)`, and `P e_(b_L)=e_(b_L)`. It must state explicitly whether `P` must preserve `Gamma`, fix `q`, or preserve channel decomposition or provenance; every restriction must be declared and justified rather than inferred silently. If `q` or the bipartition is to be fixed automatically, that must follow from an intrinsic weighted-graph characterization. PASS means nonexistence for all 119 controls; one valid witness isomorphism fails the universal separation gate.

No quotient or second discriminator is authorized until that predicate is fixed and checked. Failure closes Candidate 5 before quotient work or simulation.

No Candidate 5 source, tests, quotient analysis, dynamics, T9, protocol, held-out work, hardware run, report, artifact, staging, commit or push is created or authorized by this theorem.