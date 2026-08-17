# Area One Candidate 2 Development-Discovery Report

Date: 2026-08-16  
Status: **PRE-PROTOCOL DISCOVERY — NO CANDIDATE 2 SELECTED**  
Scope: Area One development data only

## Boundary

This work used only the validated Candidate 1 T9 development artifact:

`sha256:69a922211e9adf7b8c37050e0390e4aaab1ad0436f46faed9962f14640e34302`

No lock was created, no held-out configuration or outcome was accessed, and the frozen Candidate 1 protocol was not edited. Results in this report are hypothesis-generating discovery evidence, not a new T9 result, protocol approval, held-out result, hardware result, or quantum-advantage claim.

## Candidate 1 failure localization

The exact-image diagnostic replayed Candidate 1 and passing controls `control-004` and `control-010` over 31,104 development records. It exited 0 with maximum norm drift `1.6653345369377348e-15`.

Artifact: `demos/area-one-control-simulator/candidate2-development-diagnostic-output/candidate2-development-diagnostic.json`  
SHA-256: `sha256:9c70d8c2be11ddd51ffaeeefbb95e42f7a8b4ca712d8845ae86ce8b24d752355`  
Bytes: `7,568,826`

On `(s,R)=(2,6)`, Candidate 1 had 190 of 1,836 lifts below `-0.02`. The harmful tail was concentrated rather than random:

- Uniform initial coin: 100 of 184 bottom-decile records, despite being one-sixth of the population; q10 `-0.04054819608008209`.
- Same-column journeys: 110 of 184 bottom-decile records; q10 `-0.03584074165613914`.
- Row displacement three: 54 of 184 bottom-decile records; mean `-0.010470373755454673`.
- Uniform plus same-column: median `-0.028899898421319126`, q10 `-0.05954197646509207`.
- Uniform plus same-column plus row displacement three: 18 cases, zero positive, median `-0.03971415772844654`.

Root-cause hypothesis: rotating all four directional amplitudes identically at every monotone adjacent EOG pair creates a symmetry-sensitive coherent path that damages uniform, vertically aligned cases. This is an operator-architecture weakness, not a numerical or publication defect.

## Bounded pair-layer mechanism screen

Five mechanisms were screened over all 24 frozen parameter pairs and all three old development grids, with an exact Candidate 1 replay as the correctness control. The exact image completed 360 groups, exit 0, OOM false.

Artifact: `demos/area-one-control-simulator/candidate2-variant-screen-output/candidate2-variant-screen.json`  
SHA-256: `sha256:68e8f9fbf1a15dcc8a085b22ae4b836837108f8d03bcdb824767c2dffa3fbfad`  
Bytes: `93,100`
All four redesigned pair layers had some feasible parameters. The strongest feasible discovery point was `all-directions-alternating-phase` at `theta=pi/8`, `phi=pi/2`: aggregate median `0.0011123773263897116`, minimum grid q10 `-0.019471881637683139`. It passed the old safety floor, but `(s,R)=(3,6)` retained exact median lift `0` and the effect remained much smaller than the later `0.05` held-out target.

The frozen safety-first selection order instead chose `theta=pi/16`, producing an even smaller aggregate median. Therefore a near-identity feasibility pass would not be sufficient evidence of a useful mechanism.

## Joint-coin probe

The previously deferred eight-state joint Grover coin was tested once as `S C_joint O_t`. It was exactly norm preserving but scientifically negative: aggregate median `-0.0018772134290543363`, with grid q10 values between approximately `-0.0329` and `-0.0634`.

Artifact: `demos/area-one-control-simulator/candidate2-joint-coin-probe-output/candidate2-joint-coin-probe.json`  
SHA-256: `sha256:29f474d17e12d2ccf875fc5f66687520b17f018776879b7fcbd1f45980265b8a`  
Bytes: `707`

This fixed joint-coin form is rejected from Candidate 2 consideration.

## Operator-placement screen

Balanced pair scattering was tested before the coin, after the coin, after the shift, in a symmetric half-angle sandwich, and as an outward-edge layer after the coin. The exact image completed 432 groups, exit 0, OOM false.

Artifact: `demos/area-one-control-simulator/candidate2-placement-screen-output/candidate2-placement-screen.json`  
SHA-256: `sha256:c3d8dd21fe6053489b1619c314346e3456ecd7a5570b661276ca9d3a11d92d2e`  
Bytes: `109,384`

Placement did not remove the deeper limitation. The strongest feasible aggregate median was `0.0011645284495637345` for alternating-phase scattering after the shift at `theta=pi/8`, `phi=pi/2`; `(s,R)=(3,6)` remained exactly zero.

## Decision

Do not promote any screened pair-rotation or fixed joint-coin variant directly into a new T9. They can satisfy the development tail gate, but the observed effect is too small and the zero-median symmetry remains. Running a new T9 on the same discovery cases would only reproduce tuning data and would not be independent evidence.

The next Candidate 2 design should be structurally broader while remaining falsifiable. The recommended next architecture to design is an explicit overlap-edge channel: add a dedicated coherent edge state for each genuine EOG pair rather than rotating all existing directional amplitudes. This must embed a fair baseline, use equally expressive cardinality-matched controls, receive independent unitarity/resource review, and use newly declared development-validation configurations that were not part of this discovery screen.

Candidate 1 and every discovery artifact remain immutable evidence. Thresholds must not be lowered. The final held-out configurations remain untouched.

## Grant timing

A scientifically defensible Candidate 2 protocol, implementation, affected gate reruns, and new independent development validation are estimated at one to two working days before computation, with no guarantee of a positive result. The 19 August 2026 grant application should not wait for or claim a positive Candidate 2 T9. The honest application evidence is the validated simulator/test laboratory, completed falsification of Candidate 1, preserved untouched held-out set, diagnosed failure mechanism, and a bounded hardware-validation research plan.

## Dedicated overlap-edge probe

The separately designed five-state prototype used coin basis `(UP,RIGHT,DOWN,LEFT,OVERLAP)`, embedded baseline `C_0=C_G direct-sum 1`, genuine overlap swaps `((r,s),(r+1,0))`, and candidate step `U_X=S_X R_X C_0 O_t`. The implementation signs and phases agree with the design. The overlap shift is bijective, uses five genuine swaps and ten endpoints on every development grid, self-loops every unpaired overlap state, preserves the ordinary periodic flip-flop shift, and has no false periodic edge.

The successful exact-image run used named container `area-one-candidate2-overlap-edge-probe`, full container ID `96b2623fec96dcc301f68f04414907e0ee36ab0707ed82ace405fdbae68ad6d4`, and image `sha256:96379ff14fb29df67b28c19102d93cb1cc912e23962e0c917b5209b605edb3f2`. It ran from `2026-08-16T15:28:15.359472704Z` to `2026-08-16T15:30:19.520451729Z`, exited `0`, and was not OOM-killed. Its logs contain `CANDIDATE2_OVERLAP_EDGE_PROBE_PASS`, the source T9 hash, four-worker/fork confirmation, and `no_lock=true heldout_executed=false new_t9_started=false`.

The first named attempt, `area-one-candidate2-overlap-edge-probe-attempt1-path-failure`, full ID `6a0e914b03ed45e4c283dd2bccce2e5960e6934fb9d4425e6d3f3f39fd8eb437`, used the same image, ran from `2026-08-16T15:27:50.213721647Z` to `2026-08-16T15:27:51.371109832Z`, exited `1`, and was not OOM-killed. It failed during module import because the initial mount depth left `Path(__file__).resolve().parents[2]` unavailable. The failure occurred before experiment data access and produced no artifact.

The successful source is `demos/area-one-control-simulator/candidate2_overlap_edge_probe.py`, SHA-256 `sha256:a60012b851e48a37458148d01cba64f7f94eda8bf8a418aef8e102e1170cbc57`. Explicit `python -m py_compile candidate2_overlap_edge_probe.py` passed. The artifact is `demos/area-one-control-simulator/candidate2-overlap-edge-probe-output/candidate2-overlap-edge-probe.json`, 30,907 bytes, SHA-256 `sha256:7417b38cc673fcd4d0aa81edb2341f02861ce874da96925ce9b7ffd9240a7548`, strict canonical UTF-8 JSON plus one LF and no CR. It binds Candidate 1 T9 hash `sha256:69a922211e9adf7b8c37050e0390e4aaab1ad0436f46faed9962f14640e34302` and embedded baseline hash `sha256:8b8d46b407e3ea8ef51e923c4fc82f566ca3bbccb23eac9ee67db4b7400ac99c`.

All pre-screen and runtime checks passed: 24 parameters, 72 groups, 248,832 micro-cases, 1,728 alpha-zero baseline records, 10,368 baseline probability comparisons, and 432 direct/derived comparisons. Alpha zero reproduced the existing baseline with exactly zero amplitude and probability error. Direct/derived maximum amplitude and probability errors were `1.668583973270389e-16` and `9.7144514654701197e-17`. Screen maximum norm drift was `1.5543122344752192e-15`; probability-bound error was zero.

The old-floor winner was `alpha=pi/16`, `beta=0`, aggregate median lift `4.2161412685034344e-06`, and minimum-grid q10 `-0.0090759651096356236`. Grid medians were `4.2161412685034344e-06` for `s=2`, `0.0004355983423991966` for `s=3`, and `-0.00015357458578160147` for `s=4`. Larger alpha produced more central lift but unacceptable tails; at `alpha=pi/4`, aggregate median was `0.0060692904035125877` while minimum q10 was `-0.058249306863888989`.

`beta` is mathematically redundant in this construction, not an implementation defect. Let `G_beta` multiply every `OVERLAP` basis state by `exp(i beta)` and leave ordinary directions unchanged. The local rotation satisfies `R_X(alpha,beta)=G_beta R_X(alpha,0) G_beta^-1`; the oracle, `C_0`, overlap shift, ordinary shift, and terminal probability measurement commute with or are invariant under this global overlap-channel rephasing. Every initial state has zero overlap amplitude. Therefore all measured probabilities are beta-independent. The artifact confirms zero beta spread for five alpha indices and only `1.3e-17` numerical spread at `alpha=pi/4`.

**Disposition: NOT PROMOTED.** Passing the old q10 floor is insufficient. The selected effect is near zero, weaker than Candidate 1's aggregate median, and negative on one grid; beta adds no identifiable degree of freedom; and this discovery probe does not include the matched alternative overlap-edge controls or new development-validation configurations required by the design. No Candidate 2 was selected. No new protocol, T9, lock, held-out execution, signing, hardware claim, quantum-advantage claim, or market claim is authorized by this result.

After all IDs, timestamps, status, logs, hashes, and failure evidence were recorded, both exited overlap-edge probe containers were removed. A final filtered Docker check found no remaining container with the probe name, and no managed background process remained.