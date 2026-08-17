# Area One Closure and Transferable Quantum-Walk Knowledge

Date: 2026-08-17  
Status: **AREA ONE CLOSED / INTERNAL KNOWLEDGE RECORD**

## Disposition

The Area One quantum-advantage line is closed. The genuine EOG matching ranked 95 of 101 against its own control family, so overlap identity confers no transport advantage in the declared operator class.

Nothing was ever published, advertised, submitted as a result, or claimed to any funder. No retraction, correction or disclosure is required. The held-out data was never touched: `lock_accesses=0`, `heldout_accesses=0`. This record is internal.

Burhan is returning to the Elastic Overlapping Grid as a classical data structure, specifically the Elastic Hippocampus memory agent, and continuing quantum study through StanfordOnline `SOE-YEEQMSE01`, Quantum Mechanics for Scientists and Engineers 1.

## What was actually settled

1. Permuting which source connects to which destination is close to a relabelling. Candidate and control graphs are near-identical objects, so no observable had much to detect. This is the root cause of every failure.
2. The measured transport effect was about `0.0006` to `0.0024` in probability, i.e. tenths of a percent, while the tail-risk gate was `0.02`. The gate was thirty times the effect. That mismatch alone doomed the design.
3. Structural quantities that are identical for candidate and controls cannot separate them. Candidate 3 balanced and Candidate 5 both built zero modes common to all 120 matchings.
4. A strict endpoint quotient needs coarse local symmetry; distinguishable controls need rigidity. These pull against each other, so quotient-plus-separation kept forcing artificial gadgets.
5. Native topology fights protected zero modes. Equal-layer covers force even nullity; the natural incidence complex carries extra homology.
6. Symmetry can penalise the thing you are testing. The genuine matching is parity-preserving, which locks its median to exactly zero on the doubly even grid, while parity-breaking controls score freely there.

## The methodological lessons that transfer

These are the reusable ones, and they are worth more than the physics attempt.

**Estimate effect size before building infrastructure.** One afternoon evolving the candidate and three controls on the smallest grid would have shown a tenth-of-a-percent difference. Knowing that, nobody would have set a two-percent tail gate or expected to separate 120 near-identical variants. We built a 210-test laboratory before knowing the signal was smaller than the threshold.

**Define the wrong version first.** The decisive comparison was never "does it beat the standard baseline" but "does it beat deliberately wrong versions of itself." We had the control family and the winning numbers for weeks and never ranked them. Rank first; it is usually cheap and often fatal.

**A quantity common to treatment and control is not evidence.** Ask of any proposed discriminator: does this number actually differ between the real thing and the fake? If not, stop before implementing.

**Check that your success criterion is satisfiable.** Our own preregistered rule required a per-grid positive fraction above `3/5`, which the parity selection rule caps near `0.49` on two of nine held-out grids. It was unreachable by construction, independent of whether the physics worked. Test criteria against structure before freezing them.

**Distinguish "not proven" from "disproven."** Five negative results are knowledge. One measured rank of 95 out of 101 is a falsification. They are not the same strength and should not be reported the same way.

**Rigour is not a substitute for direction.** Exhaustive verification of a wrong direction produces confident wrongness. Audits caught real errors here, but no amount of auditing would have found the missing ranking.

## Useful quantum-walk facts established or confirmed

- Discrete-time coined walk `S C_G P O_t` on `C_R square C_w`, with basis `|r,c,d>`, four directions, periodic flip-flop shift.
- Position colour `(r+c) mod 2` is exactly conserved iff both `R` and `w` are even. Row wraparound only flips colour when `R` is even, column wraparound only when `w` is even.
- Consequence: on a doubly even grid, terminal probability is exactly zero unless the terminal colour matches start colour plus step count. Half of all start/terminal pairs are structurally unreachable at any fixed horizon.
- This is the walk analogue of a selection rule, the same idea as forbidden transitions in spectroscopy, and it is a standard-QM concept rather than an exotic one.
- Grover coin on four directions is exactly rational: `0.5` off-diagonal, `-0.5` on-diagonal.
- For a bipartite block Hamiltonian `[[0,K],[K^T,0]]` with `K` of size `m x n` and rank `r`, nullity is `(m-r)+(n-r)`. Equal-size layers force even nullity, so unique zero modes require unequal layers.
- Adding an edge to a connected graph raises cycle rank by exactly one, even if parallel to an existing edge. Uncapped added edges therefore create homology and destroy unique-zero-mode designs.

## Where quantum walks genuinely help, for future reference

The known speedups come from deliberately engineered structure, not from naturally occurring graphs:

- unstructured search, quadratic, Grover-type;
- glued trees, exponential separation for continuous-time walks, Childs and collaborators;
- element distinctness and triangle finding, Ambainis-style walk algorithms;
- spatial search on specific lattices and expanders, where the spectral gap is favourable.

The pattern matters: exponential walk speedups are built into contrived graphs. Expecting a naturally-arising data-structure graph to carry a protected mechanism was optimistic, and our five no-gos are consistent with the field's actual state rather than surprising.

If the protected zero-mode idea is revisited, it belongs in a **continuous-time** walk where the Hamiltonian is the graph itself. Applying it to a coined discrete walk by dropping the coin and oracle, as we did, removes exactly the structure where the behaviour lived.

## Course topics that pay off directly

From the Stanford course, the highest-leverage items for this kind of work:

- eigenvalues and eigenstates, then spectral gap, which controls walk speed and mixing;
- degenerate perturbation theory, which explains why two near-identical graphs give near-identical dynamics, i.e. our central failure, stated properly;
- parity operators and selection rules, which is exactly the width-parity rule we rediscovered the hard way;
- time evolution of superpositions and interference, the actual engine of any walk speedup.

## Bridge to Elastic Hippocampus

The genuinely reusable mathematics from this work is classical spectral graph theory, not quantum mechanics:

- equitable partitions and exact quotients are graph compression, directly relevant to hierarchical memory and retrieval;
- endpoint-seeded refinement is a canonical fingerprinting and deduplication routine;
- the rigidity-versus-compressibility tension is a real design constraint for any memory index that must be both compressible and able to distinguish similar records;
- weighted-degree and walk-profile invariants are practical near-duplicate detectors.

These were built and exercised here and can be carried across without any quantum claim.

## Boundary

This document records internal knowledge and closure. It asserts no transport effect, no advantage, no novelty, no hardware value and no grant deliverable. The frozen Candidate 1 protocol remains unedited at 46,074 bytes, SHA-256 `9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be`. All prior negative results and no-go theorems remain preserved. No staging, commit or push occurred.
