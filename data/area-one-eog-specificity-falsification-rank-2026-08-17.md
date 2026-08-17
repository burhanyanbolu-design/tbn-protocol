# Area One EOG-Specificity Falsification: the Genuine Matching Ranks 95 of 101

Date: 2026-08-17  
Status: **EOG-SPECIFICITY HYPOTHESIS FALSIFIED FOR THIS OPERATOR CLASS**

## What was asked

Five candidates assumed the genuine EOG matching is physically special and searched for an observable that would reveal it. That assumption was never tested. This document tests it directly.

## Method: no new computation

The completed T9 development run already evaluated **101 method families**, the genuine candidate plus 100 control matchings, each with its own best parameter chosen from the same 24-parameter grid, over the same micro-cases, against the same shared baseline. Those 101 winners were recorded and never ranked.

Source artifact: `demos/area-one-control-simulator/t9-development-output/area-one-development-selection.json`, 1,895,391 bytes, SHA-256 `69a922211e9adf7b8c37050e0390e4aaab1ad0436f46faed9962f14640e34302`, matching its recorded T9 value. It reports `lock_accesses=0` and `heldout_accesses=0`.

This is a read of existing evidence. No evolution, tuning, parameter selection, protocol change, held-out access, Docker run or artifact creation was performed. The ranking uses the protocol's own recorded `winners`, and exact decimal comparison.

## Result: the genuine matching is near the bottom

Ranked by development aggregate median lift, higher is better:

| rank | family | aggregate median | min grid q10 | feasible |
|---:|---|---|---|---|
| 1 | `control-018` | `0.0024265285908328937` | `-0.018322990439156830` | **yes** |
| 2 | `control-068` | `0.0023665254328914843` | `-0.022871313203388765` | no |
| 3 | `control-066` | `0.0022896245496064355` | `-0.023110281705713342` | no |
| 5 | `control-005` | `0.0022034702246225800` | `-0.017664488036087628` | **yes** |
| ... | | | | |
| 94 | `control-069` | `0.00062840621069609835` | `-0.017395207320514545` | yes |
| **95** | **`candidate` (genuine EOG)** | **`0.00060741042468487674`** | **`-0.020494795710597848`** | **no** |
| 96 | `control-020` | `0.00057969176104583986` | `-0.017250704389936866` | yes |

- Genuine candidate rank: **95 of 101**, the **6th percentile**.
- Control families with strictly higher aggregate median: **94**.
- Feasible families, i.e. min grid q10 above the `-0.02` floor: **86 of 101**. The genuine candidate is **not** one of them.
- Families beating the genuine candidate on **both** median and feasibility: **80**.
- `control-018` achieves **3.995x** the genuine candidate's aggregate median **and** passes the feasibility floor the genuine candidate failed.

## The protocol's own control criterion fails catastrophically

The frozen protocol requires, for the control ablation, that **candidate rank is at most 10**. The observed development rank is **95**, failing by **85 places**.

Candidate 1 was recorded as rejected on the feasibility floor, a `2.474%` tail shortfall. That framing was far too generous. On the control comparison, which is the test of whether EOG structure matters at all, the candidate is not marginal. It is beaten by nearly every arbitrary matching.

## The result is robust across metrics

| metric | genuine rank of 101 | candidate value |
|---|---:|---|
| aggregate median lift | 95 | `0.00060741042468487674` |
| median lift, `s=2` | 23 | `0.0019860027525655712` |
| median lift, `s=3` (parity-protected) | 91 | `0` |
| median lift, `s=4` | 95 | `0.00060741042468487674` |
| minimum grid q10, tail safety | 87 | `-0.020494795710597848` |

Its single best showing is rank 23 on `s=2`, which is also the grid whose tail rejected it. There is no metric on which the genuine matching leads.

## The parity theorem is confirmed, and it explains part of the deficit

The parity selection rule predicted that exactly the **parity-preserving** families, those with `f(r) != r (mod 2)` for all `r`, are pinned to a median of exactly zero on the doubly even grid `s=3`.

Independent confirmation from the artifact:

- families with median lift exactly `0` on `s=3`: **11 of 101**, namely `candidate`, `control-004`, `control-020`, `control-030`, `control-037`, `control-048`, `control-053`, `control-062`, `control-069`, `control-097`, `control-098`;
- total parity-preserving bijections for `R=6`: **12**, i.e. the candidate plus 11 possible controls, of which the manifest contains 10;
- `control-004`, the reversed list, was predicted parity-preserving from theory and is observed pinned at zero.

So the genuine candidate is parity-locked to exactly zero on `s=3`, while the 90 parity-breaking families are free to score positive there. The rule actively handicaps the genuine matching. This is a structural penalty on the candidate, not a hidden advantage, and it accounts for its rank 91 on that grid.

## Conclusion

For the declared overlap-pair scatterer operator class, the genuine EOG matching is **not special**. It is outperformed by 94 of 100 arbitrary control matchings, fails the feasibility floor that 86 families pass, is beaten on both criteria simultaneously by 80 families, and misses the protocol's own rank-10 requirement by 85 places.

The hypothesis that EOG overlap identity produces a measurable transport advantage in this operator class is **falsified on development data**, by the protocol's own comparison, using evidence already paid for.

Under the pre-agreed rule, this closes the physics line as framed. Do not build Candidate 7. Do not tune, reparameterize, or reframe the metric to rescue this rank; a rank of 95 is not a threshold miss.

## What remains true and valuable

- The result is a clean, decisive, self-obtained falsification, not an inconclusive null.
- The laboratory that produced it is intact and credible: 210 tests, digest-pinned image, byte-reproducible independent verifier, atomic publication, exhaustive enumeration.
- The held-out set was never touched: `lock_accesses=0`, `heldout_accesses=0`.
- Five structural no-go theorems, the quotient-versus-rigidity tension, the parity selection rule, and an unsatisfiable preregistered criterion found in our own protocol.

The defensible contribution is methodological: a falsification-grade pipeline that rejected its own author's mechanism, with receipts.

## Boundary

This falsifies the declared operator class on development data. It does not prove that no quantum-walk mechanism can exploit overlap structure, does not invalidate quantum walks or EOG as a data structure, and makes no claim about held-out data, hardware, advantage, or any grant deliverable. The frozen protocol and the `-0.02` floor were not edited. No staging, commit or push occurred.
