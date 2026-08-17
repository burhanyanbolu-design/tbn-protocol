# Area One Candidate 3 Coordinate-Fingerprint Structural Test Design

Date: 2026-08-17
Status: **AUTHORIZED THEOREM-FIRST MATHEMATICAL PREPARATION ONLY**
Authorization: Burhan instructed Kiro to take the next step after the degree-preserving coordinate-role result.

## Boundary and review verdict

The completed seven-cell constant-`M` construction is **not cleared for a time-domain probe**. Its cross-role controls test genuine-versus-support assortativity only. Every matching that keeps genuine channels within the genuine role and support channels within support remains endpoint-fixing isomorphic, so actual EOG pair identity is still invisible.

This step may construct and exactly test one coordinate-fingerprint refinement. It is not a transport/performance experiment, protocol, parameter search, T9, lock, held-out access, hardware run, report, evidence artifact, or quantum-advantage claim. Existing Candidate 3 files and all frozen Area One boundaries remain unchanged.

## Fixed coordinate fingerprints

For `(s,R)=(2,6),(3,6),(4,6)`, retain all full-coordinate states and the auxiliary hub. Let `g=R-1=5`, `p=R(s+1)/2-1`, and `h=p-g`.

For genuine overlap pair `(r,s)<->(r+1,0)`, predeclare the primitive coordinate fingerprint

`q_r=r+2`, giving `(2,3,4,5,6)`.

Every engineered support channel has factor `1`. These values are fixed from the row coordinate before any outcome exists. Every matched source-destination edge has one constant weight

`W = h + sum_r q_r^2 = h+90`.

There is no tunable scalar, search, or outcome-dependent choice.

## Exact 15-cell lift

Use ordered cells: entrance; hub; five singleton genuine sources; one support-source cell; five singleton genuine destinations; one support-destination cell; exit. Cell count is `15`, and every declared graph has more than 15 vertices, so the partition strictly compresses the lift.

Edges are:

- entrance-hub: weight `1`;
- hub to genuine source `r`: weight `q_r`;
- hub to every support source: weight `1`;
- every matched source-destination edge: weight `W`;
- genuine destination `r` to exit: weight `q_r`;
- every support destination to exit: weight `1`.

The candidate uses the five genuine EOG identity pairs and identity support matching. The false periodic pair is forbidden. The candidate must satisfy exact `HP=PB`, connectivity, and `Gamma H Gamma=-H`.

Its exact zero vector has entrance and exit value `-W`, genuine-source values `q_r`, support-source value `1`, and zero on the hub and all destinations. Its norm is `W(2W+1)`, so each endpoint weight and the absolute static zero-projector endpoint matrix element is `W/(2W+1)`. Exact elimination must prove `rank(K)=p+1`, full nullity one, and positive rational LDL pivots for `K^T K-I`, hence a nonzero gap greater than `1` before binary64 diagnosis.

## Genuine-identity controls

Controls exhaust all `5!-1=119` nonidentity permutations of only the five genuine destinations; support matching remains fixed. Each control preserves every named vertex, every boundary weight, every matched-edge weight, edge count, complete edge-weight multiset, and each named vertex's weighted degree.

For genuine permutation `pi`, define

`S_pi = h + sum_r q_r q_{pi(r)}`.

The exact candidate fourth moment is `W^2`; the control moment is `W S_pi`; and

`W^2-W S_pi = (W/2) sum_r (q_r-q_{pi(r)})^2 > 0`.

Because fingerprints are distinct, every nonidentity control introduces a constant-`W` edge between unequal endpoint weighted degrees. The multiset `(edge weight, endpoint weighted-degree pair)` therefore differs, proving weighted-graph non-isomorphism while local weighted strength remains fixed.

Every control still has a chiral zero mode. Its entrance coefficient is `-S_pi`, exit coefficient is `-W`, and source coefficient at channel `i` is the destination factor selected by `pi`. Its norm is `S_pi^2+W+W^2`; therefore the entrance weight, exit weight, and absolute static zero-projector endpoint element generally differ. This is the exact tested fingerprint-alignment mechanism, not an uncontrolled numerical defect.

## Tests and decision

Independent tests must reconstruct coordinates, all 15 cells, fixed fingerprints, constant `W`, candidate and all 119 controls, exact quotient closure, chiral symmetry, rank/nullity, candidate and control zero modes, endpoint formulas, LDL gap certificate, pointwise degree preservation, edge-profile non-isomorphism, and moment identities. Mutations must reject malformed cells, weights, permutations, unfair overridden controls, false moment claims, zero-mode errors, and nonpositive LDL certificates.

Passing means only that actual genuine pair identity can be made structurally visible under a predeclared coordinate-fingerprint Hamiltonian. It does not show that natural EOG geometry causes the effect: the fingerprints deliberately encode row identity. It does not establish useful finite-time transfer, superiority to all controls, scalability, quantum advantage, or permission to simulate. Any time-domain work still requires a separately frozen development-only protocol and explicit approval.

## NOT in scope

- Time evolution, transfer probability, horizon selection, or threshold selection.
- Cross-role controls; they test the already-characterized role-assortativity mechanism.
- Held-out grids, hardware, runtime/container changes, reports, or evidence artifacts.
- Claims that engineered fingerprints are natural EOG dynamics.

## Implementation shape

```text
fixed coordinates -> q_r=r+2 -> W=h+90 -> exact candidate
                                        -> 119 genuine permutations
candidate/control -> exact invariants -> structural decision only
```

Sequential implementation only: one algebra module and one independent unit suite; no parallel workstream is needed.