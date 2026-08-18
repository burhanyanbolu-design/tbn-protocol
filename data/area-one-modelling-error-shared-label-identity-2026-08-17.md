# Area One Modelling Error: Shared Label Is Identity, Not Adjacency

Date: 2026-08-17  
Status: **MATERIAL QUALIFICATION OF THE FALSIFICATION / TESTED GRAPH WAS PROBABLY NOT EOG**

## Origin

Burhan supplied the actual EOG label chart. Checking it against what we simulated revealed two things that change how the Area One result must be described.

Development-only structural verification. No held-out access, no tuning, no new candidate, no dynamics. The verification script was temporary and deleted.

## The chart is exactly as Burhan described

With `R=6` rows, `W=6` columns and stride `W-1=5`, the label map is

`L(r,c) = 5r + c`

| row | labels |
|---|---|
| 0 | 0 1 2 3 4 5 |
| 1 | 5 6 7 8 9 10 |
| 2 | 10 11 12 13 14 15 |
| 3 | 15 16 17 18 19 20 |
| 4 | 20 21 22 23 24 25 |
| 5 | 25 26 27 28 29 30 |

Verified exactly:

- every overlap shares a label: `L(r,5) = L(r+1,0)` for all `r = 0..4`;
- step sizes are `right = +1`, `down = +5`, `diagonal = +6`;
- the diagonal is `L(r,r) = 6r`, giving `0, 6, 12, 18, 24, 30`, constant step `6`, and it reverses symmetrically as `30, 24, 18, 12, 6, 0`;
- 36 grid cells carry only **31 distinct labels**; the five overlaps collapse five cells;
- labels run `0..30`, and `sqrt(31) = 5.57` against a diagonal crossing of `5` steps, so the fold gives a roughly square-root-length crossing of the sequence.

Burhan's arithmetic and his reading of the structure are correct.

## Error 1: shared label means identity, not an extra edge

The chart states that the last cell of row `r` and the first cell of row `r+1` are **the same item**, because they carry the same label.

Our simulation did not model that. It kept `(r,W-1)` and `(r+1,0)` as two distinct basis states and coupled them with a `2x2` gate `P`. Coupling two separate nodes is not the same graph as identifying them. Identification is a quotient; adding an edge is not.

## Error 2: the tested topology destroyed the journey

Our declared graph was a torus, wrapping in both rows and columns, with entrance `a=(0,0)` and exit `b=(5,s)`.

Exact shortest-path measurement, start label `0` to goal label `30`:

| model | nodes | distance `0` to `30` | after removing the overlap mechanism |
|---|---:|---:|---:|
| plain strip, no wraparound, no overlaps | 36 | 10 | 10 |
| **identified**, overlaps glued as the chart says | **31** | **6** | 10 when un-glued |
| **torus with 5 pair edges, i.e. what we tested** | 36 | **2** | **2** |

Two consequences.

**On the torus, entrance and exit were two steps apart.** Row distance `min(5,1)=1` and column distance `min(5,1)=1`. There was essentially no journey for any mechanism to influence, and deleting all five pair edges changed the distance not at all.

**In the correct identified model, the overlaps are load-bearing.** Distance is `6` with the overlaps and `10` without, a 40 percent reduction. That is exactly condition **N3** from `data/area-one-inverse-conditions-for-a-distinguishable-gate-2026-08-17.md`, the condition our tested model failed.

For completeness, if rows were joined only at overlaps with no vertical adjacency, the structure is a pure 1D chain and the distance is `30`. So the vertical adjacency plus the overlaps together produce the short crossing.

## What this does and does not change

**Does not change.** The falsification stands for the family we actually tested: on that declared torus family the genuine matching ranked 95 of 101. That measurement is correct and remains valid for that graph.

**Does change.** The tested graph was very likely **not EOG**. It identified nothing, and it added wraparound that reduced the entrance-to-exit distance to two steps. Describing the Area One result as "EOG has no quantum advantage" overstates it. The defensible statement is narrower: *a torus-with-extra-edges surrogate, in which the overlap seam was redundant and the endpoints were two steps apart, showed no advantage.*

**Newly open.** The correctly modelled EOG passes N3. That is one necessary condition, not a result.

## Remaining conditions, all still open for the corrected model

- **N1 non-isomorphism.** Do the 119 control pairings give non-isomorphic *identified* graphs with endpoints fixed? Untested on this model.
- **N2 discriminator not shared.** Untested.
- **N4 quantum versus classical.** Critical. A shorter path helps a classical walk too. Distance `6` against `10` is a classical topological gain and must not be reported as quantum.
- **Control question.** Do other pairings also collapse 36 cells to 31 and also yield distance `6`? If any pairing gives the same distance, the specific EOG pairing is still not special and the same trap recurs. This must be checked **before** any further work.
- **Genericity.** A roughly `sqrt(N)` crossing is the ordinary property of folding a line into a two-dimensional grid, not evidence unique to EOG.

## Required next steps, in order

1. Build the identified EOG graph for all 120 pairings and measure the entrance-to-exit distance and the collapsed node count for each. If the genuine pairing is not distinguished here, stop.
2. Only if step 1 separates the genuine pairing, test N1 on the identified graphs.
3. Run a classical random walk comparator before any quantum claim, satisfying N4.
4. No new protocol, no simulation of outcomes, and no advantage language until steps 1 to 3 are complete.

## Boundary

This corrects a modelling error and records exact shortest-path measurements. It establishes no transport effect, no separation, no quantum advantage and no revival of Candidate 1. The frozen Candidate 1 protocol and the `-0.02` floor are unchanged. No source or test file was added; no staging, commit or push occurred.
