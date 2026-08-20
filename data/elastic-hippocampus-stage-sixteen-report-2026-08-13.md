# Area Five Stage Sixteen — Separately Authorized Untouched Confirmation Report

**Date:** 19 August 2026
**Verdict:** `HELD_OUT_FAIL` — 15/17 preregistered gates passed
**Evidence class:** one immutable untouched public-corpus confirmation of the frozen Stage Thirteen `body_max` router
**Policy:** The sole evaluator join has been consumed. No tuning, relabeling, correction, lock removal, or rescoring is allowed. Stage Sixteen was declared a one-attempt study and is not followed by Stage Seventeen.

## Frozen design and evidence limits

Stage Sixteen used six untouched RFC Editor plaintext sources, 918 verified chunks, 16 positive questions, and four out-of-domain controls. Acquisition was bounded and sequential; preparation was offline; predictions were sealed label-free before blind pooling and adjudication. Labels have `machine-pooled` provenance and were produced by a blind sub-agent that read only the blind review file. They are not independent human judgments or exhaustive corpus labels.

Stages Five, Seven, Ten, and Twelve remain immutable held-out failures. Stage Thirteen remains development evidence. Stage Fourteen remains a pre-score protocol incident and Stage Fifteen a pre-score corpus-bound abort. Stage Sixteen modified none of them.

**Multiple-comparisons position, as disclosed before acquisition:** this is the fifth held-out attempt by the same architecture family against the same `Recall@5 >= 0.60` gate. It is not a first-attempt result and does not carry first-attempt evidential weight.

## Result

| Method | Candidate recall | Recall@5 | nDCG@5 | MRR | Positive Hit@5 | Control nonempty | Median validations | Median routing work |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Area Five indexed | 0.897165 | 0.373146 | 0.638267 | 0.770833 | 15/16 | 1/4 | 30 | 85 |
| Area Five scan | 0.897165 | 0.373146 | 0.638267 | 0.770833 | 15/16 | 1/4 | 30 | 1041 |
| Flat scan | 0.868643 | 0.386043 | 0.630154 | 0.723958 | 15/16 | 1/4 | 30 | 918 |

Integrity, provenance, and determinism failures were zero. Scan/index logical parity was exact. Indexed routing work was `85` against flat `918` and scan `1041`, a 10.8× reduction against flat.

## Failed gates

**Gate 9 — Area Five mean Recall@5 >= 0.60. Observed `0.373146`.**

This gate is very likely unsatisfiable as specified, and the evidence for that claim is internal to this run: flat scan, which examines every chunk exhaustively and is the effective ceiling for this corpus, scored `0.386043` and also failed. A gate that the exhaustive baseline cannot pass is not measuring the candidate architecture.

The mechanism is the declared dense-label ceiling. The blind adjudicator marked 154 relevant chunks across 16 positive queries, a mean of 9.6 per query, with `q16` at 19 and `q01` at 14. Against a frozen top-5 budget, a query with 19 relevant chunks caps at `5/19 = 0.263` under perfect ranking. The Stage Sixteen preregistration declared this ceiling effect in advance, citing Stage Twelve `q04` at 17 relevant chunks, and prohibited reducing labels or adjusting the gate after scoring. That prohibition is honoured here: the gate is recorded as failed.

**Gate 15 — every method has zero nonempty retrievals on all four controls. Observed 1 nonempty for all three methods.**

Control `q20` ("What condition defines a trembling-hand perfect equilibrium in an extensive-form game?") did not abstain and returned five results. Known-normalized-term coverage was exactly `0.750000` against a `>= 0.75` abstention threshold, clearing it by zero margin. Six of eight tokens (`condition`, `defines`, `hand`, `perfect`, `extensive`, `game`) are ordinary English words present in the networking corpus vocabulary; only `trembling` and `equilibrium` were absent.

The other three controls abstained correctly: `q17` at `0.400000`, `q18` at `0.500000`, `q19` at `0.666667`. All three methods including flat scan failed this gate identically, so the defect is in the shared abstention rule, not in Area Five routing.

This was predicted from the sealed label-free predictions before the evaluator join and was reported to the project owner before scoring. The attempt proceeded deliberately rather than being aborted or retuned.

## Supported findings

**Artifact routing is fixed, and this is the load-bearing result.** Stage Twelve failed `q01` and `q03` by routing DNS questions to `rfc5280` and `rfc8259` because the metadata router read only titles and headings. Stage Thirteen's `body_max` corrected both, but on already-observed labels. Stage Sixteen confirms `body_max` on a corpus and query set never previously seen: **16/16 positive queries routed to their frozen expected artifact.** This includes `q12`, which the preregistration flagged in advance as the single risky wording because it references DNS inside a DKIM question; it routed correctly to `rfc6376`.

**Indexed routing efficiency held.** Median routing work of 85 against flat 918 is a 10.8× reduction, passing the frozen 25%-of-scan gate with wide margin while preserving exact scan/index parity.

**Ranking quality was competitive with, and on two measures better than, exhaustive scan.** Area Five exceeded flat on candidate recall (`0.897` vs `0.869`), nDCG@5 (`0.638` vs `0.630`), and MRR (`0.771` vs `0.724`), and matched it on Hit@5 (15/16). Both deficit gates passed.

**Integrity properties held without exception:** zero integrity, provenance, and determinism failures, and exact scan/index logical parity across all 20 queries.

## Two identified defects

1. **Boundary-fragile abstention.** The `>= 0.75` coverage threshold admits an out-of-domain query whose common-word tokens happen to appear in the corpus. A strict `> 0.75` comparison, or an additional minimum count of known content-bearing terms, would close the observed case. Not applied here; applying it now would be post-hoc tuning against an observed failure.

2. **A likely unsatisfiable quality gate.** `Recall@5 >= 0.60` cannot be met against dense pooled labels with a fixed top-5 budget, demonstrated by the exhaustive baseline also failing. Any future study needs a metric whose achievable maximum is not capped below its own threshold — for example Recall@k with k scaled to label count, or a precision-oriented measure.

Both are recorded as findings rather than repaired, because the one-attempt rule and the no-tuning rule bind after acquisition.

## Immutable bindings

- Evaluator joins: exactly 1.
- Corpus Merkle root: `2ad8b7fd4debf50e26041f80b658a34a902d45d97063d3266e12654d4cc6d9db`.
- Query strings SHA-256: `bf9781c64811c83ca648711769fa5ba9f07dbc04225bff5a45c6bf4dca53c50d`.
- Acquisition manifest SHA-256: `1b78110938a6acfe80502e18a2947a644875261a3c61f8429018d5d88d816ec5`.
- Preparation complete SHA-256: `890291e1b569e0d3b3f6de7b81eda738e53adf4cec8c68bd9e8108ea7a7cfad4`.
- Sealed predictions SHA-256: `c613f99a605519ce1b7d1d791511008e993fbd309729d9befac3dd01fb20093f`.
- Blind review SHA-256: `e7f70120f5a7ebebb82d1a892649d03a9fb3576aeba4cc7a1d496c56cca26262`.
- Private pool SHA-256: `f85be158f85011586c5c3e408df7e5e4f1fbe1254a8e36e33951a78f68b42918`.
- Frozen labels SHA-256: `1c6a6632ad3bbaf7193b1587d92ad02ea52b12c2bbd151fc43d430c2b02bf9e4`.
- Score lock SHA-256: `ba262963984da7130d23f13fac8e9251b170b246175e3af30a022680f4f61f50`.
- Result: `data/elastic-hippocampus-stage-sixteen-held-out-2026-08-13.json`.
- Result SHA-256: `d341998536e1112d0c2580bd27831489a5d9949d7a325ddd4718df6aceee11cc`.

## Interpretation and boundary

Stage Sixteen provides positive untouched evidence for artifact routing correctness, indexed routing efficiency, ranking quality competitive with exhaustive scan, provenance, determinism, and exact scan/index parity. It remains a held-out failure because two frozen gates did not pass: one from a genuine abstention defect, one from a threshold the exhaustive baseline also could not meet.

The defensible claim from this run is **narrowing**, not final ranking: Area Five selects the correct artifact and reduces routing work by an order of magnitude, while its top-5 recall does not exceed exhaustive scan. This matches the existing non-authoritative shadow-router integration in `api/area_five_shadow.py`, where Area Five proposes candidates and Hardin reauthorizes, reloads, verifies, and ranks before any memory text is returned.

This result does not establish general superiority, independent human relevance, semantic or neural understanding, human-level memory, novelty, patentability, publication quality, or general intelligence. Per the preregistered stopping rule, no Stage Seventeen follows, and no gate, label, threshold, or router may be altered to revisit this score.
