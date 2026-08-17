# Area One Candidate 2: Dedicated Overlap-Edge Design

Generated: 2026-08-16  
Status: **PRE-PROTOCOL DISCOVERY DESIGN — NOT APPROVED OR FROZEN**  
Area: One only

## Purpose

Candidate 1 showed that applying an identical position-pair rotation to all four existing direction amplitudes creates a harmful symmetry-sensitive tail and only a small central benefit. Candidate 2 tests a different hypothesis: represent each genuine EOG overlap as a dedicated coherent edge channel rather than modifying every ordinary direction.

This document authorizes prototype discovery on already-used development data only. It does not authorize a new T9, parameter lock, held-out execution, production signing, hardware claims, or changes to the frozen Candidate 1 protocol.

## State space

For step size `s` and `R` rows, width is `W=s+1` and positions remain full coordinates `(r,c)`. The coin basis becomes

```text
(UP, RIGHT, DOWN, LEFT, OVERLAP) = (0,1,2,3,4).
```

The Hilbert basis is `|r,c,d>` with dimension `5 R W`. Display labels remain metadata.

Every declared initial state has zero `OVERLAP` amplitude. The existing six four-direction coin states are embedded as `(v_UP,v_RIGHT,v_DOWN,v_LEFT,0)`.

## Embedded standard baseline

Define

```text
C_0 = C_G direct-sum 1_OVERLAP.
```

`C_0` applies the four-direction Grover coin and leaves the overlap component unchanged. The baseline overlap shift is a self-loop at every position. With zero initial overlap amplitude, the embedded five-state baseline is exactly the existing four-state Grover walk and must match it amplitude-wise and probability-wise within `1e-12`.

## Genuine overlap edges

For `r=0,...,R-2`, retain only

```text
p_r = (r,s),
q_r = (r+1,0).
```

The overlap shift swaps

```text
|p_r,OVERLAP> <-> |q_r,OVERLAP>.
```

Unpaired overlap states self-loop. There is no false periodic edge between `(R-1,s)` and `(0,0)`. Ordinary directions retain the existing periodic flip-flop shift.

## Local overlap entrance

At every endpoint participating in a declared pair, let

```text
|u_4> = (|UP>+|RIGHT>+|DOWN>+|LEFT>)/2.
```

After applying `C_0`, apply a two-state unitary `R_X(alpha,beta)` only on the span of `|u_4>` and `|OVERLAP>`:

```text
R_X |u_4>       = cos(alpha)|u_4> + exp(i beta)sin(alpha)|OVERLAP>,
R_X |OVERLAP>   = -exp(-i beta)sin(alpha)|u_4> + cos(alpha)|OVERLAP>.
```

The three ordinary coin components orthogonal to `|u_4>` are unchanged. At unpaired positions `R_X` is identity. `alpha=0` closes the overlap channel and must reproduce the embedded standard baseline exactly.

## Candidate and controls

The prototype candidate step is

```text
U_X(alpha,beta,t) = S_X R_X C_0 O_t.
```

Operators act right-to-left. `O_t` marks all five coin states at the terminal coordinate. Every component is unitary: the oracle and local coins are unitary blocks, `R_X` is a two-state rotation on disjoint local subspaces, and `S_X` is a permutation.

The matched controls use the same state dimension, local entrance rotation, parameter budget, number of overlap endpoints, and number of overlap-edge swaps. Only the endpoint pairing in `S_X` changes according to the immutable control family. This separates the effect of a fifth state and generic extra edges from the declared EOG matching.

Required comparators for a later protocol are:

1. Original four-state Grover walk.
2. Embedded five-state baseline with an inactive self-loop channel.
3. Genuine EOG overlap-edge candidate.
4. Cardinality- and tuning-matched alternative overlap-edge controls.

## Pre-protocol discovery gate

The first prototype screen may use only the already-consumed Candidate 1 development grids `(s,R)=(2,6),(3,6),(4,6)` and the existing 24 angle/phase indices. Those outcomes are discovery data and cannot become a new T9 result.

The prototype must fail closed unless:

- all trajectories remain finite and have norm drift at most `1e-12`;
- `alpha=0` agrees with the existing baseline within `1e-12`;
- direct six-state and four-column derivation agree within `1e-12` on a fixed sample;
- overlap shift is a bijection with exactly `R-1` genuine swaps and no false periodic edge;
- every reported probability remains within physical tolerance;
- no lock or held-out access occurs.

Promotion requires more than passing the old `q10 >= -0.02` floor. The effect must be materially larger than the pair-rotation discovery variants, avoid exact zero-median symmetry, and justify the added fifth-state resource cost.

If promising, a separate protocol must declare new development-validation configurations not used during discovery, matched controls, parameter-selection order, workload, schemas, independent dense verification, resource accounting, and explicit approval before any new T9-equivalent run.

## Non-claims

This is an abstract algorithmic model. It is not a hardware component, physical gate decomposition, quantum advantage, patent conclusion, product, grant outcome, or revenue claim. A positive discovery probe would justify protocol design only.