---
status: in-progress
branch: main
timestamp: 2026-08-17T04:13:40+01:00
files_modified:
  - data/area-one-candidate-3-typed-arm-stabilizer-obstruction-design-2026-08-17.md
  - demos/area-one-control-simulator/candidate3_typed_arm_stabilizer.py
  - demos/area-one-control-simulator/test_candidate3_typed_arm_stabilizer.py
  - data/area-one-candidate-3-native-rooted-type-compatibility-design-2026-08-17.md
  - demos/area-one-control-simulator/candidate3_native_rooted_type_compatibility.py
  - demos/area-one-control-simulator/test_candidate3_native_rooted_type_compatibility.py
---

## Working on: Candidate 4 theorem-first handoff

### Summary

Candidate 3 structural work is complete at 92/92 tests and final independent audit PASS. The direct native EOG graph is blocked for a Harrow-style bipartite/chiral zero-mode route, so Burhan decided to stop for the night and continue tomorrow with a bounded Candidate 4 canonical bipartite-lift investigation. No Candidate 4 implementation has started.

### Decisions Made

- Preserve Candidate 3 as a completed structural research record, including every negative result.
- The native EOG graph genuinely supplies five distinct source and destination rooted signatures, but its direct candidate is non-bipartite, has no strict endpoint quotient, and has no usable endpoint-supported common zero mode.
- Candidate 4 is a new EOG-derived engineered architecture, not a repair or relabelling of the direct native graph.
- Use one canonical double-cover rule: two copies of each native vertex and crossed copies of every native edge; no searched weights or artificial row fingerprints.
- Candidate 4 tests a Harrow-inspired protected zero-mode mechanism but is not Harrow's exact construction and must not be described as natural EOG/Harrow evidence.
- Stop Candidate 4 before simulation if any mathematical gate fails. Do not add arbitrary gadgets until it passes.
- Candidate 4 T9 remains blocked until architecture proofs, independent validation, a separate protocol, and explicit protocol freeze.

### Remaining Work

1. Write the Candidate 4 canonical bipartite-lift theorem design only for `(s,R)=(2,6),(3,6),(4,6)`.
2. Prove native EOG edges are genuinely represented and exact bipartite/chiral symmetry holds.
3. Derive or reject a common zero mode with nonzero entrance and exit support, exact nullity one, and a positive gap. Stop immediately if this gate fails.
4. Derive or reject a strict endpoint-representing exact quotient.
5. Exhaust all 119 nonidentity matching controls for pointwise degree fairness and endpoint-fixing isomorphisms.
6. If viable, add independent exact tests, run the full Candidate 3 plus Candidate 4 suite, and obtain a clean adversarial audit.
7. Only after all structural gates pass, design and explicitly freeze a separate Candidate 4 development protocol before any simulation or T9.

### Notes

- Latest native-rooted files: design `f6dfa00ebac094b7b90a2625df8d2f9964425ab33add0b95781af15f13cda8f8`; source `ad27942a9f3ec163ce28f2be3892f5aec96883e01763c4d4d059338f390ae23d`; tests `f00347fde3693e15a0a8bb924ec664a03c9af982054cc12768bfdc493f52e50b`.
- Latest typed-arm files: design `5e7cab0610e4e98bfe4bc555622ea6620b4b6c45b05619a3a7d7542ddde62793`; source `c664bd9cbf972c4fbc2efb6b064e7386aca937cae9298a6200e5354293efc3b2`; tests `53a512789e1639099542343a5947436b9056419a17bd06f1d3befe6f8881498b`.
- Focused native-rooted suite passed 18/18 in 9.512s; complete Candidate 3 suite passed 92/92 in 291.748s.
- Frozen Candidate 1 remains rejected and unchanged at 46,074 bytes, `9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be`.
- Historical zero-mode files and `research_numerics.py` remain frozen at their recorded hashes.
- Expected effort: an early Candidate 4 rejection may take 1-3 focused hours; proof-complete maturity, if viable, may take 8-16 agent hours across one or two focused days.
- SparQ application materials are still pending from STFC; deadline remains 19 August 2026 at 5:30pm.
- Repository has many pre-existing unrelated tracked/untracked changes. Do not stage, delete, or modify them.
- Final state: no Python process, no staged files, no Candidate 4 simulation, T9, held-out access, report, artifact, commit, or push.
### Candidate 4 canonical double-cover theorem result — REJECTED

On 2026-08-17 the authorized design-only Candidate 4 theorem was completed and stopped at its mandatory zero-mode kill gate. The canonical full lift has exact block adjacency `H_pi=[[0,A_pi],[A_pi,0]]`, genuinely retains every native and matching unit channel twice, and passes exact bipartite/chiral symmetry. Orthogonal block diagonalization gives `H_pi` similar to `diag(A_pi,-A_pi)`, so `nullity(H_pi)=2 nullity(A_pi)` and exact nullity one is universally impossible for this equal-layer lift.

The exact lifted candidate nullities are `0,0,2` for `s=2,3,4`. The `s=4` zero sector vanishes on both copies of both native endpoints, and the all-control common kernel remains trivial. An independent read-only mathematical audit found no material error after removal of a post-kill quotient observation and narrowing the endpoint statement to all states supported on the native endpoint fibres. Direct exact rank checks returned lifted ranks/nullities `36/0`, `48/0`, and `58/2`.

Design: `data/area-one-candidate-4-canonical-double-cover-zero-mode-obstruction-2026-08-17.md`, 5,124 bytes, SHA-256 `f2df92f721a671a9700456cf91e4f5a459e28157655573ba00b42438417894d7`.

Per the kill rule, Candidate 4 in this predetermined form is closed. No quotient derivation, 119-control isomorphism exhaustion, source, tests, simulation, T9, protocol, held-out work, report, artifact, staging, commit or push followed. Any materially different architecture requires a separately named theorem-first authorization; it must not be patched into Candidate 4.
### Candidate 5 unbalanced index-one lift — Stage 1 PASS only

On 2026-08-17 Burhan authorized Candidate 5. The design-only theorem first rejected the naive one-row extension `K=[A;r^T]`: the native `s=4` endpoint-zero kernel vector is inherited for every extra row, so nullity one and endpoint support cannot both hold.

The declared Candidate 5 benchmark instead uses `t=Delta+1=6`, `B_pi=6I+A_pi`, the degree-completed index row `c=B_pi 1`, `K_pi=[B_pi;c^T]`, and `H_pi=[[0,K_pi],[K_pi^T,0]]`. It has sublattice sizes `n+1` and `n`, exact chirality, full column rank, one common zero vector `((1_n,-1),0_n)`, signed endpoint projector `1/(n+1)`, and rigorous uniform gap bound at least one for every candidate/control. Exact summed-matrix checks exhausted all 120 permutations on all three grids; candidate `K` ranks were `18,24,30` on lifted sizes `37,49,61`. Independent corrected-design audit PASS, quality `9.7/10`.

This zero mode is universally manufactured by `c=B1`; it is not EOG-specific evidence. The weight-six rungs and weight-10/11 index star materially alter native degrees and may dominate later behaviour. Candidate 5 is therefore not promoted. Its next separately authorized theorem must fix the marked weighted-graph category and exhaust endpoint-fixing permutation similarity for all 119 controls. One witness isomorphism fails the separation gate. No source, tests, quotient, dynamics, simulation, T9, protocol, held-out work, report, artifact, staging, commit or push occurred.

Design: `data/area-one-candidate-5-unbalanced-index-one-lift-zero-mode-theorem-2026-08-17.md`, 8,380 bytes, SHA-256 `57df75a07f765a4fff302a1a0fbbda67f279d07351b827cba776342ac7608d7d`.
### Candidate 5 endpoint-fixed aggregate isomorphism gate — PASSED

On 2026-08-17 Burhan authorized the next Candidate 5 theorem. The structural category uses only the two marked endpoints and the actual uncoloured weighted multigraph; native/matching provenance, source/destination labels, row identities and declared layer labels are forbidden.

The index vertex `q` is intrinsically unique by weighted degree, `R=N(q)` is intrinsic, and every right vertex's unique weight-six edge intrinsically fixes the rung pairing. Therefore every lifted endpoint-fixing isomorphism is equivalent to one base permutation `phi` with `phi^T A_id phi=A_pi`, `phi(a)=a`, and `phi(b)=b`.

An independently reconstructed exact joint-refinement oracle exhausted all 357 nonidentity grid/control cases and found zero isomorphisms. A separate endpoint-walk invariant distinguished 356 cases using scalar moments through `2n`. The sole scalar exception, `s=3`, `pi=(4,1,0,3,2)`, was independently separated by `M_2`, the multiset of all vertex endpoint-walk profiles through powers 0..2: among vertices with first-step pair `(1,1)`, candidate count at second-step `(1,1)` is zero and control count is two. Final audit PASS, `10/10`.

This proves only aggregate structural pair-identity separation. It does not make the manufactured zero mode EOG-specific or establish quotient closure, dynamics, transport or advantage. Next separately authorized gate is strict endpoint-representing exact quotient; stop if endpoint-seeded exact refinement is discrete or not strictly compressive. No source, tests, simulation, T9, protocol, held-out work, report, artifact, staging, commit or push occurred.

Design: `data/area-one-candidate-5-endpoint-fixed-aggregate-isomorphism-theorem-2026-08-17.md`, 7,200 bytes, SHA-256 `ade3358c69565907e9f98affe941ae5f3cd36260f076c6922a721f2d4dd57a6e`.
### Candidate 5 strict endpoint-quotient gate — REJECTED / CLOSED

On 2026-08-17 the authorized third Candidate 5 design-only theorem completed the mandatory strict endpoint-representing exact quotient gate. Starting only from `{a_L}`, `{b_L}`, and the unmarked remainder, exact weighted equitable refinement became discrete on every declared lift: `3 -> 14 -> 26 -> 35 -> 37` for `s=2`, `3 -> 14 -> 27 -> 41 -> 48 -> 49` for `s=3`, and `3 -> 14 -> 32 -> 50 -> 59 -> 61` for `s=4`. An independent colour-signature implementation reproduced the same round counts, complete cell-size histograms, and final discrete partitions. Since the stable partition is the coarsest equitable refinement of the endpoint seed, no strict exact quotient with distinct singleton entrance and exit cells exists. Final audit PASS, `9.7/10`; optional wording hardening now defines strict as `|P|<|V|` and states the normalized quotient `H_P=Q_P^T H_id Q_P`.

Candidate 5 therefore closes before dynamics. Its earlier positive zero-mode and endpoint-fixed non-isomorphism theorems remain valid but insufficient: the zero mode is still universally manufactured by `c=B1`, and structural pair-identity separation does not imply quotient closure. Per the kill rule, do not patch Candidate 5 with labels, weights, symmetry restrictions, endpoint fibres, or quotient-specific gadgets. Any materially different architecture requires a separately named theorem-first authorization.

Design: `data/area-one-candidate-5-strict-endpoint-quotient-obstruction-2026-08-17.md`, 5,678 bytes, SHA-256 `d6895d7f82df382b37b41ec9eae63ae2b261f3d5ba1084ef9c79c7840b45aeca`. No Candidate 5 source, tests, quotient matrix, dynamics, simulation, T9, protocol, held-out work, hardware run, grant claim, report, experiment artifact, staging, commit or push followed. Closure check found no staged files and no Python processes.
### Candidate 6 canonical Hodge–Dirac incidence route — REJECTED / CLOSED

On 2026-08-17 Burhan authorized the next theorem-first architecture. Candidate 6 changed operator class to the canonical signed incidence/Hodge–Dirac construction of the native `C_6 square C_(s+1)` EOG torus with five matching 1-cells. It used no Candidate 5 shifted adjacency, rungs, index star or `c=B1`, and no searched weights, fingerprints, support channels, anchors, cuts, caps or quotient gadgets.

Two independently predeclared branches failed the mandatory unique-zero-mode gate. For graph incidence, connectedness gives `rank(partial_1)=n-1` with `m=2n+5`, so the exact Dirac nullity is `n+7`, namely `25,31,37`. For the Hodge–Dirac branch using all and only the `n` native torus plaquettes, the five matching 1-cells add five uncapped cycle classes: `(beta_0,beta_1,beta_2)=(1,7,1)`, `rank(K)=2n-2`, and exact nullity is `9` on every grid and control. The common constant vertex 0-form has equal nonzero endpoint coefficients but is not isolated from the homological zero sector. Orientation switching cannot alter these ranks or nullities. Final corrected-design audit PASS, `10/10`.

Candidate 6 is closed before quotient refinement or dynamics. Do not add seam cuts, cap cells, relative boundary conditions, weights, labels or endpoint gadgets under the Candidate 6 name. Any higher-cell construction requires a separately named theorem-first authorization with intrinsic attaching maps.

Design: `data/area-one-candidate-6-canonical-hodge-dirac-nullity-obstruction-2026-08-17.md`, 6,845 bytes, SHA-256 `4a9239654a95ba18adc3c17764dfbc30da6a2393478f68ae619e4ee93416b4bc`. No Candidate 6 source, tests, quotient matrix, control-isomorphism run, dynamics, simulation, T9, protocol, held-out work, hardware run, grant claim, report, experiment artifact, staging, commit or push followed. Closure check found no staged files and no Python processes.
### Research direction evaluation — TRANSPORT LINE REINSTATED AS PRIMARY

On 2026-08-17 Burhan challenged the zero-mode programme and asked for an honest evaluation against the original T9-compatible Candidate 1, including whether the Harrow framing helped. Evaluation of recorded evidence only; no new architecture was authorized.

Verdict: the Harrow zero-mode framing was net negative for the T9 objective. It replaced an observable transport metric with structural invariants, discarded the coin and oracle where Candidate 1's diagnosed harm actually lives, produced four candidates the validated T9 laboratory cannot execute, and repeatedly protected a zero mode provably common to candidate and all controls, which therefore cannot separate them. Genuine value retained: four rigorous no-go theorems, proof that the direct native EOG graph has no protected zero-mode mechanism, the quotient-versus-rigidity tension as a reusable design filter, and an entirely untouched holdout.

Recomputed and verified transport facts. Candidate 1 aggregate median lift was positive at `+0.00060741042468487674`; rejection came only from min q10 `-0.020494795710597848` against the frozen `-0.02` floor, a shortfall of `0.000494795710597848`, i.e. `2.474%` of the floor magnitude. Candidate 2's alternating-phase point reached aggregate median `0.0011123773263897116`, `1.831x` Candidate 1, with min q10 `-0.019471881637683139`, which clears the floor by `0.000528118362316861`; a later screen reached `1.917x`. Candidate 2 was therefore paused while ahead, correctly, for method reasons: selection on discovery cases, exact-zero `s=3` median, tiny absolute effect, and missing matched controls.

Localized harm confirmed: uniform coin `100/184` bottom-decile at `3.26x` enrichment, same-column `110/184` (`59.8%`), displacement three `54/184` (`29.3%`), triple intersection `18` cases with zero positive and median `-0.03971415772844654`, about `1.99x` the floor magnitude.

New cross-line hypothesis, not a theorem: median lift is exactly zero on `s=3` in both Candidate 1 and Candidate 2, and `w=s+1=4` is precisely the grid whose native torus `C_6 square C_4` is bipartite. Even-width grids may null the mechanism, which would also mean the declared family aggregates incomparable regimes and inflates the tail that rejected Candidate 1. Test this before choosing any new candidate.

Ordered recommendation: test width parity first; target the diagnosed uniform-coin/same-column/displacement-three subpopulation; apply the cheap universal pre-build filter that the discriminating quantity must differ between candidate and controls; use fresh predeclared development configurations and matched controls; write a new protocol for any redesigned operator without editing or lowering the frozen `-0.02` floor; and revive zero modes only against the actual coined operator including coin space and oracle.

Design: `data/area-one-research-direction-evaluation-transport-versus-zero-mode-2026-08-17.md`, 10,898 bytes, SHA-256 `7686d59181c36c35d21577431995b086214db0d7ddb874c1a69ee722838517f8`. No simulation, tuning, parameter search, T9, protocol change, lock, held-out access, hardware run, grant claim, artifact, staging, commit or push occurred. No staged files and no Python processes remain.
### Width-parity selection rule — CONFIRMED; TWO FROZEN HELD-OUT CRITERIA UNSATISFIABLE

Resumed after a host computer crash. Crash-state verification found the evaluation document intact at its recorded hash, no staged files, no Python processes and no partially written parity work.

On 2026-08-17 the first recommended action from the direction evaluation was executed: test the width-parity hypothesis. It is **confirmed and stronger than hypothesised**.

Theorem: position colour `(r+c) mod 2` is an exactly conserved selection rule if and only if **both** `R` and `w=s+1` are even. Row moves flip colour under wraparound only when `R` is even; column moves only when `w` is even. `O_t` is position-diagonal, `C_G` is direction-only, and the candidate pair layer joins equal colours when `w` is even. So `U_A=S C_G P O_t` and `U_G=S C_G O_t` both flip colour exactly once per step, and the complementary colour holds amplitude exactly zero. Verified by independent standard-library construction of the real operators at `R=6`, `k=1..6`, with and without `P`: the rule holds at every step for `s=3` and is absent for `s=2` and `s=4`. The verification script was temporary and deleted, so the reproducibility gap is disclosed in the document.

Consequence 1: on `(s=3,R=6)`, `N=24`, colour classes `12/12`, `552` ordered pairs, `3312` micro-cases, and the declared horizon is `10`, which is even. Forced exact-zero lifts are `288/552 = 12/23 = 52.17%`, a strict majority, so the median is exactly `0` regardless of `theta`, `phi`, coin state or pair layer. This is the structural cause of the exact-zero `s=3` median recorded for **both** Candidate 1 and Candidate 2. It was never mechanism evidence.

Consequence 2, correcting a first-draft error found by audit: the claim that no control could satisfy the criterion was **false**. Colour preservation needs `f(r) != r (mod 2)`; the candidate `f(r)=r+1` always satisfies it, `control-004` (reversed) does, but `control-000` (rotation by one) does not. Parity-breaking controls leak across colours and can score positive lift exactly where the candidate is pinned to zero, so the rule **handicaps** the candidate rather than flattering it.

Consequence 3: held-out grids are `s in {5,6,7}` by `R in {7,8,9}`; both `R` and `w` are even only for `(s=5,R=8)`, `N=48`, and `(s=7,R=8)`, `N=64`. Maximum attainable positive fraction is `(N/2-1)/(N-1)` at even horizon and `(N/2)/(N-1)` at odd horizon, giving `23/47=0.4894`, `31/63=0.4921`, `24/47=0.5106`, `32/63=0.5079`. All are below the required `3/5`. Therefore frozen success criterion 3 is **unsatisfiable by construction** on those two grids at any horizon parity and any parameter value. Criterion 2 (`m[0,g] > epsilon`) additionally fails at even horizon; declared development horizons `9,10,11` match `ceil(2*sqrt(N))`, implying `14` and `16`, both even, but that inference must be confirmed against the declared held-out horizon table. Criterion 3 fails either way.

Audit history: first audit FAIL `7/10` for scoping parity to width alone, the false "any control" claim, omitting criterion 2, over-generalised constants, and an unnecessary conditional about held-out widths. All were corrected. Second audit PASS `9/10` with two precision fixes, both applied: the caps are at most `3/5` with equality only at the unattainable `N=6` and strictly below for doubly even `N>=8`, and the pair-layer colour statement now flags that it assumes the candidate map.

Consequence: do not execute held out under the current frozen success rule. Any amendment is a preregistration-integrity event, must be drafted from structure alone without reference to measured performance, and needs explicit re-approval. The frozen protocol was reverified unchanged at 46,074 bytes, SHA-256 `9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be`, and was not edited.

Design: `data/area-one-width-parity-selection-rule-theorem-2026-08-17.md`, 10,764 bytes, SHA-256 `c479457eb77c2177e4a5cb374298fb88cad52b14bf73cc205fe5f775df2cdfc0`. No held-out execution, tuning, parameter selection, candidate promotion, T9, lock, protocol edit, hardware run, grant claim, artifact, staging, commit or push occurred. Temporary script removed; no staged files and no Python processes remain.
### EOG-SPECIFICITY FALSIFIED — genuine matching ranks 95 of 101; physics line closed

On 2026-08-17 Burhan pushed back that the work had become endless verification with no proposal. Correct. The untested assumption behind all five candidates was that the genuine EOG matching is physically special. The decisive test needed no new computation: the completed T9 development run already scored 101 families, the candidate plus 100 control matchings, each with its own best parameter over identical micro-cases and baseline, and those winners were never ranked.

Read of `demos/area-one-control-simulator/t9-development-output/area-one-development-selection.json`, 1,895,391 bytes, SHA-256 `69a922211e9adf7b8c37050e0390e4aaab1ad0436f46faed9962f14640e34302`, matching its recorded T9 value, with `lock_accesses=0` and `heldout_accesses=0`.

Result: the genuine candidate ranks **95 of 101** by development aggregate median, the 6th percentile. 94 controls beat it. 86 of 101 families are feasible above the `-0.02` floor and the genuine candidate is not one of them. 80 families beat it on median and feasibility simultaneously. `control-018` reaches `0.0024265285908328937`, which is **3.995x** the candidate's `0.00060741042468487674`, while also passing the floor the candidate failed. The frozen protocol requires candidate rank at most 10; actual rank 95 fails by 85 places.

Robustness across metrics: rank 95 on aggregate median, 23 on `s=2`, 91 on `s=3`, 95 on `s=4`, 87 on minimum grid q10. No metric puts the genuine matching in front. Its best showing, `s=2`, is the grid whose tail rejected it.

The parity theorem was independently confirmed by this data and explains part of the deficit. Exactly 11 of 101 families have median lift exactly `0` on the doubly even grid `s=3`: `candidate`, `control-004`, `control-020`, `control-030`, `control-037`, `control-048`, `control-053`, `control-062`, `control-069`, `control-097`, `control-098`. There are exactly 12 parity-preserving bijections for `R=6`, the candidate plus 11 possible controls, of which the manifest contains 10. `control-004`, the reversed list, was predicted parity-preserving from theory and is observed pinned at zero. So the candidate is parity-locked to zero on `s=3` while 90 parity-breaking families can score positive there: the selection rule penalises the genuine matching.

Conclusion: for the declared overlap-pair scatterer class, EOG overlap identity confers no transport advantage. The hypothesis is falsified on development data by the protocol's own comparison. Per the pre-agreed rule this closes the physics line as framed. Do not build Candidate 7, and do not retune or redefine the metric to rescue a rank of 95, which is not a threshold miss.

Retained value: a decisive self-obtained falsification rather than an inconclusive null; an intact credible laboratory at 210 tests with pinned image, byte-reproducible independent verifier and atomic publication; a completely untouched holdout; five structural no-go theorems; the quotient-versus-rigidity tension; the parity selection rule; and an unsatisfiable preregistered criterion discovered in our own protocol. The defensible contribution is methodological.

Design: `data/area-one-eog-specificity-falsification-rank-2026-08-17.md`, 6,688 bytes, SHA-256 `8bab5f9c09bb014f0c1cedecbf8f0cc3c58329d2960a40014b46ebb2513311e5`. Frozen protocol reverified unchanged at `9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be`. Temporary ranking scripts deleted; no source or test file added; no evolution, tuning, selection, held-out access, protocol edit, artifact, staging, commit or push occurred.
### AREA ONE CLOSED — internal knowledge saved; pivot to Elastic Hippocampus

On 2026-08-17 Burhan accepted the falsification and closed the Area One quantum-advantage line. He noted, fairly, that my framing had led him to believe each next candidate was a fix; that was a framing error on my part, not his misreading.

Nothing was ever published, advertised, submitted as a result, or claimed to any funder, so no retraction or disclosure is required. The held-out set was never touched. This is internal knowledge only.

Direction now: return to the Elastic Overlapping Grid as a **classical** data structure, specifically the Elastic Hippocampus memory agent, while Burhan continues StanfordOnline `SOE-YEEQMSE01` quantum mechanics. Quantum work becomes study and exploration, not a deliverable.

Consolidated knowledge record written covering: the root cause that matching permutation is near-relabelling; effect size `0.0006`-`0.0024` against a `0.02` gate, a thirty-fold mismatch; that discriminators common to candidate and controls cannot separate; the quotient-versus-rigidity tension; native topology fighting protected zero modes; and parity penalising the genuine matching.

Transferable methodology lessons recorded: estimate effect size before building infrastructure; define and rank the deliberately wrong versions first, which we could have done for weeks and did not; verify a proposed discriminator actually differs between real and fake; check success criteria are satisfiable before freezing; distinguish not-proven from disproven; and rigour does not substitute for direction.

Quantum-walk facts preserved: the exact conservation condition that position colour is conserved iff both `R` and `w` are even; the bipartite block nullity formula `(m-r)+(n-r)` and why equal layers force even nullity; that any added edge raises cycle rank by one even when parallel; the rational Grover coin; and that known walk speedups come from engineered graphs such as glued trees rather than naturally occurring ones, which makes the five no-gos consistent with the field rather than surprising. If protected zero modes are revisited it must be in a continuous-time walk where the Hamiltonian is the graph, not a coined walk with the coin stripped out.

Bridge to Elastic Hippocampus identified as classical spectral graph theory: equitable partitions and exact quotients as graph compression, endpoint-seeded refinement as fingerprinting and deduplication, the rigidity-versus-compressibility tension as a memory-index design constraint, and walk-profile invariants as near-duplicate detectors.

Design: `data/area-one-closure-and-transferable-quantum-walk-knowledge-2026-08-17.md`, 7,837 bytes, SHA-256 `778583ec9c6c21089e1c7d181bb13ed74ccb218583281bb0154890b073840c8a`. Frozen Candidate 1 protocol reverified unchanged at `9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be`. All prior negative results and no-go theorems preserved. No staged files, no Python processes, no commit or push.
---

## SESSION END 2026-08-17 — Area One closed, resume on Elastic Hippocampus

Burhan stopped for the day to go to work. Everything is saved and verified. Resume from this section.

### Where things stand

Area One quantum-advantage line is **closed by falsification**, not paused. The genuine EOG matching ranked 95 of 101 against its own control family. Do not reopen it, do not build Candidate 7, and do not retune or redefine the metric to rescue that rank.

Nothing was ever published, advertised, submitted as a result, or claimed to any funder. The held-out set was never touched. No retraction or disclosure is owed to anyone. This is internal knowledge.

### Verified state at close

All six documents written today, confirmed at these exact sizes and digests:

| bytes | SHA-256 prefix | file |
|---:|---|---|
| 5,678 | `d6895d7f82df` | `data/area-one-candidate-5-strict-endpoint-quotient-obstruction-2026-08-17.md` |
| 6,845 | `4a9239654a95` | `data/area-one-candidate-6-canonical-hodge-dirac-nullity-obstruction-2026-08-17.md` |
| 10,898 | `7686d59181c3` | `data/area-one-research-direction-evaluation-transport-versus-zero-mode-2026-08-17.md` |
| 10,764 | `c479457eb77c` | `data/area-one-width-parity-selection-rule-theorem-2026-08-17.md` |
| 6,688 | `8bab5f9c09bb` | `data/area-one-eog-specificity-falsification-rank-2026-08-17.md` |
| 7,837 | `778583ec9c6c` | `data/area-one-closure-and-transferable-quantum-walk-knowledge-2026-08-17.md` |

Frozen boundaries reverified unchanged:

- Candidate 1 protocol: 46,074 bytes, `9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be`
- T9 development artifact: `69a922211e9adf7b8c37050e0390e4aaab1ad0436f46faed9962f14640e34302`

Clean state confirmed: no staged files, no Python processes, no temporary scripts, no Docker run, no commit, no push. All prior Candidate 1 through Candidate 6 negative results and no-go theorems preserved.

### Time-sensitive item

The STFC SparQ deadline is **19 August 2026, 5:30pm**, two days out. That application was framed as an EOG **quantum** PoC, which today's falsification contradicts. Either reframe it as a feasibility and negative-results study or skip the round. Recommendation given: skip, since nothing was ever advertised and there is no inconsistency to manage. Do not submit any quantum-advantage claim for EOG.

### Resume here

Primary next work is the **Elastic Hippocampus memory agent**, treating EOG as a classical data structure. The reusable mathematics is classical spectral graph theory already built and exercised here: equitable partitions and exact quotients as graph compression, endpoint-seeded refinement as fingerprinting and deduplication, walk-profile invariants as near-duplicate detection, and the rigidity-versus-compressibility tension as a memory-index design constraint.

Quantum work continues as **study only**, not a deliverable, alongside StanfordOnline `SOE-YEEQMSE01`. Suggested first exercise is reproducing the glued-trees continuous-time walk to see a real exponential separation, reusing the existing pinned laboratory.

### Standing rules carried forward

Estimate effect size before building infrastructure. Rank the deliberately wrong versions first. A discriminator common to candidate and controls proves nothing. Check that success criteria are satisfiable before freezing them. Distinguish not-proven from disproven. Never present the parity-protected `s=3` exact-zero median as mechanism evidence. Never edit the frozen protocol or lower the `-0.02` floor.

Session closed cleanly. It was a genuine falsification obtained with an untouched holdout, which is a stronger scientific position than an unverified positive.
---

## POST-CLOSURE ANALYSIS 2026-08-17 — inverse conditions and strategy options

Burhan asked three questions after the closure that produced genuinely new results.

### 1. Does the quantum walk need the pair gate? No.

A discrete-time walk is coin plus shift; spatial search adds only an oracle. The pair layer `P` was an optional additive term proposed by Kiro, so the burden of proving it moved an observable was always on it. It never did.

### 2. Inverse analysis — the question that should have been asked first

Burhan asked whether the conditions for success could be **derived** rather than guessed. Candidates 1-6 were all forward attempts. The inverse problem had never been stated. Four necessary conditions were derived:

- **N1 non-isomorphism.** If genuine and control are endpoint-fixing isomorphic then `<b|f(H_id)|a> = <b|f(H_pi)|a>` for every analytic `f`, so dynamics are provably identical. Candidate 3 balanced failed this; Candidate 5 passed for all 119 controls.
- **N2 discriminator not shared.** Candidates 3 and 5 both built zero modes common to all 120 matchings via `c=B1`, carrying zero information.
- **N3 rewired edges must be load-bearing. NEWLY FOUND FAILURE.** Exact combinatorial check: the native torus `C_6 square C_w` wraps in the column direction, so it **already** joins column `0` to column `w-1` at all `6` rows, independently of any matching. Verified `6 of 6` wraparound edges present on every grid, and `a`-to-`b` remains **reachable with all five pair edges deleted** on all three grids. None of the 5 matching edges coincides exactly with a native edge, but they are redundant as a route. The mechanism under test was never on the critical path. This is a deeper cause than "small perturbation" and was a ten-line check never run across six candidates.
- **N4 advantage must be quantum, not topological. NEVER TESTED.** No classical comparator was ever run; the frozen protocol explicitly deferred it.

Consequence: the seam was redundant with the wraparound, so no pairing could be load-bearing and any gate placed there was pre-emptively diluted. The specific fix for N3 is to remove the column wraparound, making the grid a cylinder or strip so the seam becomes a genuine cut. Honest catch: that makes the **pairing** matter but not **quantum** matter, since a classical walk would see the same difference. Design: `data/area-one-inverse-conditions-for-a-distinguishable-gate-2026-08-17.md`, 7,110 bytes, SHA-256 `85c3696e4398f002b0daf3a1bfb38c105335973ba3a9446f3cbb3fdf86f04345`.

### 3. Strategy — where the mathematics actually lands

Recorded in `data/area-one-post-closure-strategy-options-2026-08-17.md`, 9,347 bytes, SHA-256 `31533f97cc682d58fe0bfe84d45d4d2f7d739c3aeb0b4b0a525c0da9821b74b4`.

Key content. Candidate 6 built a chain complex with `partial_1 partial_2 = 0` and Betti numbers `(1,7,1)`, which **is** the structure of CSS/homological codes: the native torus is a toric code with `2` logical qubits and the seams raise it to `7`, giving rate about `0.108` for `s=4` against the toric `0.033`. The filed obstruction is, in coding language, the encoding rate. Probable killer is distance: an uncapped seam closes a length-3 cycle implying a weight-3 logical operator and distance near `3`. Estimate only, and directly computable.

Also recorded: `P` is literally a beamsplitter, so disjoint pair layers are Reck/Clements interferometer meshes, and multi-particle interference depends on permanents, so the pairing could matter for two or more photons where it provably did not for one. Matchgate resemblance noted as superficial and not to be oversold.

Component roles ranked by fit and competition: surface-code decoding (highest fit, severe competition), routing and mapping (high fit, active), minor embedding for Ising machines and annealers (high fit, weaker incumbents), tensor-network ordering (severe competition), and verification/provenance via ICV (already built, no agreed standard exists).

Open versus closed recorded explicitly: platforms, codes, architecture, useful applications and benchmarking standards are genuinely open; unitarity, no-cloning, Grover `sqrt(N)` optimality via BBBV, and the threshold theorem are closed by proof. Advocacy cannot move a proven lower bound, including for our own proposals.

On lobbying: do not lobby physics, do participate in standards, where no accepted procedure exists for independently verifying an advantage claim. Venues to verify before approach: NPL, NQCC (already in orbit via SparQ), IEEE quantum working groups, ISO/IEC JTC 1. Our rare credential is a pipeline that falsified its own author's project with an untouched holdout.

Ranked: (1) verification and standards, (2) minor embedding or routing, (3) homological code distance as one cheap decisive calculation, (4) new paradigm, longest odds.

### Standing discipline carried forward

Measure the incumbent first. Effect size before infrastructure. Ask the control question on day one, namely whether any competent index would do this or specifically an elastic overlapping one. Verify criteria are satisfiable before freezing. Do not let belief precede measurement.

No build, simulation, protocol, staging, commit or push was authorized or performed by this analysis. Temporary verification scripts were deleted. Nothing staged, no Python processes.
---

## MODELLING ERROR FOUND 2026-08-17 — the tested graph was probably not EOG

Burhan supplied the actual EOG label chart, which exposed a modelling error that materially qualifies the falsification.

Chart verified exactly: `L(r,c) = 5r + c`; every overlap shares a label, `L(r,5) = L(r+1,0)` for `r=0..4`; steps are right `+1`, down `+5`, diagonal `+6`; the diagonal is `L(r,r)=6r` giving `0,6,12,18,24,30` and reversing symmetrically as `30,24,18,12,6,0`; 36 grid cells carry only **31 distinct labels**; `sqrt(31)=5.57` against a 5-step diagonal crossing. Burhan's arithmetic and reading were correct.

**Error 1.** A shared label means the two cells are the **same item**, an identity or quotient. We modelled them as two distinct basis states coupled by a `2x2` gate `P`. Coupling two nodes is not identifying them.

**Error 2.** Our torus wrapped in both directions, so entrance `(0,0)` to exit `(5,s)` was only **2 steps** apart: row `min(5,1)=1` plus column `min(5,1)=1`. There was essentially no journey for any mechanism to influence.

Exact shortest paths, label `0` to label `30`:

| model | nodes | distance | after removing overlap mechanism |
|---|---:|---:|---:|
| plain strip, no wraparound | 36 | 10 | 10 |
| **identified, as the chart specifies** | **31** | **6** | 10 un-glued |
| **torus with 5 pair edges, what we tested** | 36 | **2** | **2** |

So in the correctly identified model the overlaps **are load-bearing**, `6` versus `10`, which **passes condition N3** that our tested model failed. On our torus, deleting all five pair edges changed the distance not at all.

**Does not change.** The falsification stands for the family actually tested: genuine matching ranked 95 of 101 on that declared torus family.

**Does change.** The tested graph was very likely **not EOG**. Do not say "EOG has no quantum advantage." The defensible statement is that a torus-with-extra-edges surrogate, with a redundant seam and endpoints two steps apart, showed no advantage.

**Still open for the corrected model:** N1 non-isomorphism on identified graphs, N2, and critically **N4 quantum versus classical**, since a shorter path helps a classical walk equally. Distance `6` versus `10` is a classical topological gain and must not be reported as quantum. The roughly square-root crossing is generic to folding a line into two dimensions.

**Mandatory first test before any further work:** build the identified graph for all 120 pairings and measure collapsed node count and entrance-to-exit distance for each. If the genuine pairing is not distinguished, stop — otherwise the same trap recurs. Only then N1, then a classical comparator for N4.

Design: `data/area-one-modelling-error-shared-label-identity-2026-08-17.md`, 5,776 bytes, SHA-256 `240d6834f834020d5bd737d2f991a24e082ca86ca0f23a769277ced954ddb4fd`. Temporary script deleted. No source or test file added, nothing staged, no commit or push.