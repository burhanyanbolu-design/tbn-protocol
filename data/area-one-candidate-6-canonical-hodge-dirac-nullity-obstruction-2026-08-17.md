# Area One Candidate 6 Canonical Hodge–Dirac Nullity Obstruction

Date: 2026-08-17  
Status: **REJECTED AT THE MANDATORY UNIQUE-ZERO-MODE GATE**

## Scope and boundary

Candidate 6 changes operator class rather than patching Candidate 5. It tests the canonical signed incidence/Hodge–Dirac construction of the native EOG torus with the five genuine or control matching channels. It introduces no shifted adjacency, rung, index star, `c=B1` row, searched weight, coordinate fingerprint, support matching, pendant anchor, seam cut, cap cell or quotient-specific gadget.

This is an EOG-derived topological construction, not Harrow's exact construction and not evidence of useful transport. Cell-orientation changes give diagonal-sign orthogonal similarity, preserving rank, nullity, spectrum, and absolute endpoint amplitudes or probabilities; signed amplitudes may change sign under endpoint basis switching.

The entrance and exit are the previously declared native 0-cells `a=(0,0)` and `b=(5,w-1)`. Here "endpoint-supported" means that a zero vector has nonzero coefficients at both endpoints; it does not mean that its support is confined to those endpoints.

The ordered kill rule is applied within each predeclared branch as soon as exact nullity one fails. No quotient refinement, endpoint-fixing control exhaustion, dynamics, simulation, T9, protocol, lock, held-out access, hardware run, grant claim, report, experiment artifact, staging, commit or push is authorized.

## Fixed native chain data

Let `w=s+1` and `n=6w` for `s=2,3,4`. The native cubical torus `C_6 square C_w` has

- `n` vertices;
- `2n` native oriented 1-cells;
- `n` native square 2-cells.

Add the five source-to-destination matching channels as five further oriented 1-cells. Native and matching channels remain distinct when they have the same endpoints. Thus every candidate and control has

`m=2n+5`

oriented 1-cells. Rewiring the same five matching cells preserves every named vertex's incidence count and every unit incidence magnitude. The underlying multigraph remains connected.

Two predetermined canonical incidence operators are considered. Neither permits an outcome-dependent choice of orientation or cells. Variants A and B are independently predeclared branches evaluated at the same mandatory nullity gate. Each branch is killed immediately by its own nullity result; Variant B is not a refinement or repair chosen after observing Variant A.

## Variant A: graph-incidence Dirac operator

Let `partial_1:C_1 -> C_0` be the signed vertex-edge incidence matrix of the full native-plus-matching multigraph and define

`H_pi^(1)=[[0,partial_1],[partial_1^T,0]]`.

With `Gamma=diag(I_n,-I_m)`, this operator has exact chiral symmetry. Since the graph is connected,

`rank(partial_1)=n-1`.

Therefore

`nullity(H_pi^(1))=(n-(n-1))+(m-(n-1))=m-n+2=n+7`.
The exact nullities are consequently

- `25` for `s=2` and `n=18`;
- `31` for `s=3` and `n=24`;
- `37` for `s=4` and `n=30`.

The vertex-constant 0-form is a common zero vector and has nonzero equal entrance and exit coefficients, but it is accompanied by the full cycle space of dimension

`beta_1=m-n+1=n+6`.

Endpoint support of one vector cannot repair this extensive degeneracy.

## Variant B: native-plaquette Hodge–Dirac operator

Now retain all canonical native square plaquettes. Let `partial_2:C_2 -> C_1` be their signed face-edge boundary map, embedded into the enlarged 1-cell space. The five matching 1-cells occur in no added 2-cell. The native/matching distinction here is part of the predeclared CW incidence structure, not an auxiliary vertex or edge colour: matching 1-cells are separate basis cells and occur in no native 2-cell boundary. This is the predetermined construction using all and only the `n` existing native square 2-cells; attaching new matching-dependent caps would be a different architecture.

Use the even/odd parity block

`K_pi=[partial_1;partial_2^T]:C_1 -> C_0 direct-sum C_2`,

`H_pi^(2)=[[0,K_pi],[K_pi^T,0]]`.

The chain identity `partial_1 partial_2=0` gives exact Hodge decomposition, and `H_pi^(2)` is chiral. The native torus has Betti numbers `(1,2,1)`. Adding each of the five matching 1-cells without a 2-cell preserves connectedness and the native fundamental 2-cycle while adding one independent cycle. Hence

`beta_0=1`, `beta_1=2+5=7`, and `beta_2=1`.

Equivalently, exact ranks are

`rank(partial_1)=n-1`, `rank(partial_2)=n-1`, and `rank(K_pi)=2n-2`.

Because `K_pi` has `2n` rows and `2n+5` columns,

`nullity(H_pi^(2))=(2n-(2n-2))+((2n+5)-(2n-2))=2+7=9`.

Thus every declared candidate and control has exact nullity nine. The kernel decomposes into harmonic representatives of `H_0`, `H_1`, and `H_2` of dimensions `1`, `7`, and `1`. In particular, the desired constant endpoint-supported zero vector is not isolated.

## Universal nature of the obstruction

Both failures hold for the identity matching and every control permutation. They do not depend on which matching channels coincide geometrically with native edges, because matching channels are retained as separate 1-cells and no native plaquette boundary uses them. Adding a separate edge between two vertices of a connected graph raises the cycle rank by one even when it is parallel to an existing edge.

Orientation changes only multiply incidence basis vectors by `-1`. The resulting diagonal-sign orthogonal similarity cannot remove the extra kernel dimensions.

The obstruction is topological rather than numerical: no positive-gap estimate above zero, endpoint convention, or control permutation can turn nullity `n+7` or `9` into exact nullity one.

## Decision

Candidate 6 passes canonical EOG incidence, pointwise unit-incidence fairness and exact chiral symmetry, but fails the mandatory unique endpoint-supported zero-mode gate in both predetermined forms:

1. graph incidence gives exact nullity `n+7`, namely `25,31,37`;
2. adding every native torus plaquette reduces this only to exact nullity `9`;
3. the common constant vertex zero mode remains embedded in a higher-dimensional homological zero sector.

Candidate 6 is rejected before quotient work or dynamics. Per the kill rule, do not add seam cuts, cap cells, relative boundary conditions, weights, labels or endpoint gadgets under the Candidate 6 name to kill homology. A canonical construction with additional cell dimensions would require a separately named theorem-first authorization and must justify every attaching map intrinsically.

No Candidate 6 source, tests, quotient matrix, refinement oracle, control-isomorphism run, dynamics, simulation, T9, protocol, held-out work, hardware run, grant claim, report, experiment artifact, staging, commit or push is created or authorized by this theorem.