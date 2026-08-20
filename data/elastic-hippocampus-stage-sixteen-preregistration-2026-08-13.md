# Area Five Stage Sixteen — Separately Authorized Untouched Confirmation Preregistration

**Frozen:** 19 August 2026, before Stage Sixteen acquisition, preparation, prediction, pooling, labeling, or evaluation
**Evidence class:** pre-acquisition untouched public-corpus confirmation of the frozen Stage Thirteen `body_max` candidate
**Authorization basis:** separately authorized new study, not a continuation of the Stage Five–Fifteen confirmation loop
**Stopping rule:** Stage Sixteen is one attempt. Pass, fail, abort, or procedural incident is final and is not followed by Stage Seventeen.

## Authorization and the Stage Fifteen stopping rule

The Area Five final evidence conclusion states: *"No Stage Sixteen or further automatic confirmation loop will be started. Any future evaluation should be a separately authorized study with a newly designed corpus-size feasibility check, immutable exclusive label tooling, and preferably independent human relevance judgments."*

This package is that separately authorized study, and it is explicitly **not** an automatic continuation. The distinction is recorded honestly:

- It is authorized by the project owner as a new study on 19 August 2026, not triggered by the prior loop.
- It satisfies the conclusion's first stated condition: a corpus-size feasibility check now exists (`stage16_prepare.py --preflight-only`), which is the specific control whose absence made Stage Fifteen's 381-chunk shortfall unrecoverable.
- It satisfies the second stated condition: label tooling is immutable and exclusive (`O_CREAT|O_EXCL` throughout, score lock before the sole evaluator join).
- It does **not** satisfy the third, preferred condition. Labels remain `machine-pooled`, not independent human judgments. This is a real and declared limitation of this study, and a pass here does not become a human-adjudicated result.

**Multiple-comparisons disclosure.** Stages Five, Seven, Ten, and Twelve are prior held-out failures of the same architecture family against a `Recall@5 >= 0.60` gate. Stage Sixteen is therefore not a first attempt in the statistical sense, and a single pass here does not carry the evidential weight of a first-attempt pass. Any report of a Stage Sixteen pass must state the prior failure count alongside it. This is disclosed before acquisition specifically so that it cannot be omitted afterwards.

**Candidate freeze.** The `body_max` router was selected in Stage Thirteen using already-observed Stage Twelve labels. It is frozen here before acquisition, with no ablations and no alternates, so Stage Sixteen tests one pre-committed candidate rather than selecting among variants.

## Scope, untouched status, and one-attempt rule

Stage Twelve remains immutable prior held-out evidence, Stage Thirteen remains development evidence, Stage Fourteen remains an immutable pre-score protocol incident, and Stage Fifteen remains an immutable pre-score corpus-bound abort. Stage Sixteen is additive and modifies or rescores none of them. At freeze time no `stage16-corpus` directory or operational artifact exists and no corpus bytes have been acquired or inspected. Only source identities, URL syntax, and document-independent questions are frozen.

Canonical paths only: acquire once, prepare once, seal predictions once, build one blind review/private pool pair, create exactly one canonical blind proposal, freeze labels exactly once, create the exclusive score lock before the sole evaluator join, and evaluate exactly once. No source substitution, tuning, relabeling, deletion, repair, overwrite, lock removal, correction, rerun, or rescoring is permitted. A partial review created before a pool-write failure is preserved and terminates the attempt.

A pass supports only bounded retrieval generalization for this corpus and query set under machine-pooled labels. It does not establish general superiority, exhaustive relevance, independent human judgment, semantic or neural understanding, human-level memory, novelty, patentability, publication quality, or general intelligence. A failure is equally final.

## Exact ordered frozen sources

| Order | Artifact | Title | Publisher | Version | Exact URL |
|---:|---|---|---|---|---|
| 1 | `rfc791` | Internet Protocol | RFC Editor | RFC 791 | <https://www.rfc-editor.org/rfc/rfc791.txt> |
| 2 | `rfc2131` | Dynamic Host Configuration Protocol | RFC Editor | RFC 2131 | <https://www.rfc-editor.org/rfc/rfc2131.txt> |
| 3 | `rfc5849` | The OAuth 1.0 Protocol | RFC Editor | RFC 5849 | <https://www.rfc-editor.org/rfc/rfc5849.txt> |
| 4 | `rfc6376` | DomainKeys Identified Mail (DKIM) Signatures | RFC Editor | RFC 6376 | <https://www.rfc-editor.org/rfc/rfc6376.txt> |
| 5 | `rfc7230` | Hypertext Transfer Protocol (HTTP/1.1): Message Syntax and Routing | RFC Editor | RFC 7230 | <https://www.rfc-editor.org/rfc/rfc7230.txt> |
| 6 | `rfc3261` | SIP: Session Initiation Protocol | RFC Editor | RFC 3261 | <https://www.rfc-editor.org/rfc/rfc3261.txt> |

Every source is RFC Editor plaintext, publisher `RFC Editor`, and uses rights citation <https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/>. Acquisition is sequential and HTTPS-only, allowlists only `www.rfc-editor.org`, revalidates every redirect, rejects query strings, fragments, credentials, and nonstandard ports, requires `text/plain`, limits each artifact to 5 MiB and total bytes to 30 MiB, and uses a 30-second timeout with `Stage16ConfirmationAcquirer/1.0`. It refuses a nonempty destination and writes `acquisition-manifest.json` last.

These six sources are deliberately larger than the Stage Fifteen set, which produced 381 chunks against a 400 floor. No corpus bytes have been fetched or inspected at freeze time, so the resulting chunk count is unknown and is not guaranteed to land in range.

**No-substitution policy:** any source, transport, media-type, byte, parser, resource, dimension, or 400–2,000 chunk-bound failure terminates the attempt. No alternate URL, version, artifact, parser, chunk size, threshold, or replacement corpus is permitted.

**Mandatory corpus-size feasibility check.** After acquisition and before any preparation output is written, `stage16_prepare.py --preflight-only` must be run and its `resource-preflight` chunk count recorded. This mode writes no `chunks.json`, `runtime-inventory.json`, or `preparation-complete.json`. If the observed chunk count is outside 400–2,000 inclusive, the attempt terminates at that point under the no-substitution policy, with the acquired corpus preserved and no preparation output created. The feasibility check exists to make that failure visible before the one-shot path is entered; it does not license changing any source or bound.

## Exact frozen query set

Queries are document-independent, were written before acquisition, and expose neither expected artifact nor kind to retrieval. Positive distribution is exactly 3/3/3/3/2/2 in source order.

| ID | Kind | `artifact_id` | Exact query text |
|---|---|---|---|
| `q01` | positive | `rfc791` | What fields make up the IPv4 header, and what do the Total Length, Identification, and Time to Live fields represent? |
| `q02` | positive | `rfc791` | How does IP fragmentation use the Identification, Flags, and Fragment Offset fields to allow reassembly at the destination? |
| `q03` | positive | `rfc791` | How does the Time to Live field limit a datagram's lifetime, and what must a gateway do when it decrements TTL to zero? |
| `q04` | positive | `rfc2131` | What sequence of DHCPDISCOVER, DHCPOFFER, DHCPREQUEST, and DHCPACK messages makes up the DHCP DORA lease-allocation process? |
| `q05` | positive | `rfc2131` | Which client lease states does a DHCP client cycle through, and what triggers transitions among INIT, SELECTING, REQUESTING, BOUND, RENEWING, and REBINDING? |
| `q06` | positive | `rfc2131` | How do the T1 and T2 timers derived from a DHCP lease duration determine when a client attempts renewal or rebinding? |
| `q07` | positive | `rfc5849` | How is the OAuth 1.0 signature base string constructed from the HTTP method, base URI, and normalized request parameters? |
| `q08` | positive | `rfc5849` | How does the HMAC-SHA1 signature method combine the client shared secret and token secret to sign an OAuth 1.0 request? |
| `q09` | positive | `rfc5849` | What role do the oauth_nonce and oauth_timestamp parameters play in preventing replay of an OAuth 1.0 signed request? |
| `q10` | positive | `rfc6376` | Which tags in a DKIM-Signature header field identify the signing domain, selector, and signed header list? |
| `q11` | positive | `rfc6376` | How do the simple and relaxed canonicalization algorithms normalize header and body content before DKIM signing? |
| `q12` | positive | `rfc6376` | How does a DKIM verifier use the selector record published in DNS to retrieve the public key for signature validation? |
| `q13` | positive | `rfc7230` | How does a recipient distinguish framing that uses Content-Length from framing that uses chunked transfer coding when parsing an HTTP/1.1 message? |
| `q14` | positive | `rfc7230` | How is a chunked transfer coded body terminated, and what rules govern the chunk-size line that begins each chunk? |
| `q15` | positive | `rfc3261` | Which SIP headers, including Via, To, From, Call-ID, and CSeq, must appear in a request that establishes a new dialog? |
| `q16` | positive | `rfc3261` | How does an INVITE transaction combined with an ACK request establish a SIP dialog between a user agent client and server? |
| `q17` | control | `` | Which cyclin-CDK complex triggers the G1/S checkpoint transition in the eukaryotic cell cycle? |
| `q18` | control | `` | What mineral phase transition marks the boundary between the upper and lower mantle at roughly 660 km depth? |
| `q19` | control | `` | How does the Chandrasekhar limit constrain the maximum mass of a stable white dwarf star? |
| `q20` | control | `` | What condition defines a trembling-hand perfect equilibrium in an extensive-form game? |

One query-design note is recorded honestly: `q12` mentions DNS in a DKIM context. It is retained exactly as written pre-acquisition and must not be edited, but it is the one query whose wording could interact with routing in a way the Stage Twelve DNS misses make salient.

## Frozen preparation, resources, normalization, and retrieval

Preparation is offline and reads only a completed, hash-bound acquisition. RFC numbered sections are boundaries. Normalization is Unicode NFC plus collapsed whitespace. Chunks never cross artifact or heading boundaries, contain at most 320 normalized-whitespace tokens with 40-token overlap, and use IDs `artifact_id|heading|ordinal|text SHA-256`. Source provenance, previous/next links, canonical SHA-256 Merkle leaves, duplicate-final odd Merkle levels, root, runtime inventory, and completion marker are bound. Preparation creates no candidates, pool, review, proposal, or labels.

Resource ceilings are 30 MiB total raw bytes, 20,000 chunks, 5,000,000 analyzed terms, 250,000 features, 512 MiB estimated sparse matrix bytes, and 512 MiB estimated LSA working bytes. Exactly 64 LSA components require both dimensions greater than 64. Normal preparation additionally requires 400–2,000 chunks inclusive. Outputs are non-overwritable and the completion marker is written last.

Case-aware normalization is exactly Stage Twelve/Fourteen/Fifteen: `[A-Za-z0-9]+` surface segmentation must equal lowercase `[a-z0-9]+`; stopwords are removed; exact lowercase lookup occurs first; unknown all-uppercase alphabetic tokens longer than one bypass `s`/`ed` fallback; ordinary plural and past-tense fallback remains; document frequency above 50 removes a term. Known-normalized-term coverage below 0.75 causes abstention.

The sole artifact router is frozen Stage Thirteen **`body_max`**: body TF-IDF (`lowercase=True`, `sublinear_tf=True`) scores every chunk, each artifact receives its maximum chunk score, the highest artifact is selected, and ties use ascending artifact ID. There are no ablations or alternate routers. Within the selected artifact, ranking uses body TF-IDF, randomized LSA-64 (`algorithm=randomized`, `n_iter=5`, random state `20260813`), heading TF-IDF (`lowercase=True`, 1–2 grams, `sublinear_tf=True`), and RRF (`k=60`, heading weight `0.5`). The conditional technical-symbol channel retains `caret -> ^`, `tilde -> ~`, technical normalization, and weight `1.0`. Candidate budget is 30, top-k is 5, record ties use ascending record ID, integrity/provenance checks are mandatory, and Area Five scan/index outputs must have exact logical parity excluding only routing work.

A declared known risk of frozen `body_max`: maximum body pooling is outlier-sensitive, and artifacts with more chunks have more opportunities for a high accidental maximum. RFC 3261 is substantially larger than the other five sources. This is recorded before acquisition and is not grounds for changing the router afterwards.

## Prediction, pooling, and safer label workflow

Prediction is label-free and exclusive at its canonical path. Before sealing, it verifies prepared corpus, Merkle/provenance/resources, exact ordered sources, exact queries/distribution, all eight implementation hashes below, and all ten prior-evidence bindings below. Every method runs twice; integrity, provenance, and determinism failures must total zero. Scan/index selected artifact, candidates, rankings, traces, scores, stop reason, validations, and integrity failures must match exactly. Sealed output uses `O_CREAT|O_EXCL`.

The blind pool is built once after prediction. Per query it unions sealed flat/global top 30, independent all-corpus TF-IDF top 15, independent randomized LSA-64 top 15 (`n_iter=5`, random state `20260813`), and one-hop within-artifact previous/next neighbors for every pre-adjacency member. Private order is ascending SHA-256 of `query_id + '|' + chunk_id`. Opaque keys use exact domain `stage16-candidate|`. Provenance labels are `sealed_stage16_flat_global_top30`, `independent_all_corpus_tfidf_top15`, `independent_all_corpus_lsa64_top15`, and applicable adjacency labels. Review is exclusively created first, then pool; if pool creation fails, the partial review is preserved and the attempt aborts without deletion or retry. All output paths are canonical and exclusive.

The blind review exposes only query text, opaque candidate key, heading, text, and source title — never rank, score, method, chunk ID, artifact ID, corpus index, private mapping, expected artifact, prediction outcome, or prior outcome. The blind adjudication agent reads only that review and returns a `q01`–`q20` mapping in conversation; it must never write canonical labels. The parent creates exactly one canonical `stage16-corpus/blind-label-proposal.json`.

`stage16_labels.py` is a frozen non-network CLI with no path overrides. It reads canonical proposal, review, pool, and sealed-prediction bytes only. It never exposes the private key-to-chunk mapping. Proposal schema has no unknown fields and is exactly: `schema_version: 1`, `stage: 16`, `state: blind_machine_proposal`, `label_provenance: machine-pooled`, `independent_human_judgment: false`, and `labels` containing exactly `q01`–`q20`. Each `q01`–`q16` list is nonempty, unique, and in the same review query's opaque-key domain; `q17`–`q20` are empty. Any malformed proposal is preserved and aborts without final labels. The script never deletes, repairs, rewrites, or overwrites anything.

A valid proposal creates `relevance-labels.json` exactly once with `O_CREAT|O_EXCL`, without modifying the proposal. Final labels bind the corpus Merkle root, all prepared corpus-file hashes, query hash, pool hash, review hash, sealed-prediction hash, and `proposal_sha256`; include the evaluator join policy; retain `machine-pooled`; and set `independent_human_judgment` false. `stage16_evaluate.py` cannot create or modify proposal or labels. It verifies `proposal_sha256`, proposal/final label equality, `independent_human_judgment` false, and every existing corpus/query/pool/review/prediction/script binding before creating the exclusive score lock ahead of the sole private join.

## Exact frozen gates

All 17 gates are unchanged from Stage Twelve/Fourteen/Fifteen. Every gate must pass for `STAGE_SIXTEEN_HELD_OUT_PASS`; otherwise the final verdict is `HELD_OUT_FAIL`.

1. Exact artifact count is 6.
2. Chunk count is within 400–2,000 inclusive.
3. Exact query count is 20.
4. Exact split is 16 positives and four controls.
5. All labels resolve in the bound candidate pool, every positive is nonempty, and every control is empty.
6. Integrity, provenance, and determinism failures total zero.
7. Area Five scan/index logical parity is exact.
8. Area Five positive Hit@5 is at least 13/16.
9. Area Five mean Recall@5 is at least 0.60.
10. Area Five mean nDCG@5 is at least 0.60.
11. Area Five mean MRR is at least 0.60.
12. Area Five Recall@5 deficit from flat is at most 0.10.
13. Area Five nDCG@5 deficit from flat is at most 0.10.
14. Every one of the six positive artifact groups has at least one Hit@5.
15. Every method has zero nonempty retrievals on all four controls.
16. Area Five indexed median routing work is less than scan and at most 25% of scan.
17. Area Five indexed median evidence validations are at most 30.

Metrics are macro-averaged over 16 positives using binary machine-pooled relevance. Timing is descriptive, not a gate. Benchmark string is `area_five_stage_sixteen_untouched_confirmation`.

Gate 9 is the gate that failed at Stage Twelve with observed `0.541640`. Dense pooled labels can cap achievable Recall@5 below 1.0 for broad questions, exactly as recorded at Stage Twelve where `q04` had 17 relevant chunks against a top-5 budget. This ceiling effect is declared in advance; observing it is not grounds for reducing labels or adjusting the gate after scoring.

## Canonical paths and final-attempt stopping rule

- Corpus: `demos/elastic-hippocampus-proof/stage16-corpus/`
- Predictions: `demos/elastic-hippocampus-proof/stage16-corpus/sealed-predictions.json`
- Private pool: `demos/elastic-hippocampus-proof/stage16-corpus/adjudication-pool.json`
- Blind review: `demos/elastic-hippocampus-proof/stage16-corpus/adjudication-review.json`
- Parent-written proposal: `demos/elastic-hippocampus-proof/stage16-corpus/blind-label-proposal.json`
- Frozen labels: `demos/elastic-hippocampus-proof/stage16-corpus/relevance-labels.json`
- Score lock: `demos/elastic-hippocampus-proof/stage16-corpus/stage-sixteen-score.lock`
- Result: `data/elastic-hippocampus-stage-sixteen-held-out-2026-08-13.json`
- Report: `data/elastic-hippocampus-stage-sixteen-report-2026-08-13.md`
- Report sidecar: `data/elastic-hippocampus-stage-sixteen-report-2026-08-13.md.sha256`

No command-line override redirects any path. Once acquisition begins, any attempted phase, partial paired output, malformed proposal, final labels, score lock, or result is immutable and must be preserved. Stage Sixteen is one attempt and is not followed by Stage Seventeen regardless of pass, fail, or abort. This package creates no `stage16-corpus`.

## Frozen implementation bindings

The preregistration is excluded to avoid a hash cycle. Exact SHA-256 bindings are:

- `demos/elastic-hippocampus-proof/stage16_acquire.py`: `e078312df92ac290a8c51ac2b40c61f68fe7168441cb3b6b1b4c7c5730de600c`
- `demos/elastic-hippocampus-proof/stage16_prepare.py`: `c800535158663ca5e7c251205dddbc8fc03ace3fa2d1ddbc3e96749b310292ea`
- `demos/elastic-hippocampus-proof/stage16_retrieval.py`: `2141562da49a1245c813a4cff39d17fc78e23c643fe04d8cf4d2a29f48354dd0`
- `demos/elastic-hippocampus-proof/stage16_predict.py`: `209e953f6d20ca1caa0849b141b3829b0512064b810df16ad825a10b25e667df`
- `demos/elastic-hippocampus-proof/stage16_labels.py`: `8b144af108ecd4672f5543fd66180a9b3aa46167c6d0379eb098bcc33e40903d`
- `demos/elastic-hippocampus-proof/stage16_evaluate.py`: `bb4c900744f774d4fcbfa6f7ff3727fe489149d2eb6c830adb4bf47a3ffaac0b`
- `demos/elastic-hippocampus-proof/benchmark.py`: `0af933a75ab34d11f5502ff0f53ab1989c21af7dbace0ee647a1fab57c5afb94`
- `demos/elastic-hippocampus-proof/document_benchmark.py`: `286231f69ddc06112afd0bb0e9be12d4240dc4b15a2a6b19d6778ebfe2c7f8ab`

Any bound implementation change before acquisition requires a new preregistration freeze and updated hashes. No bound implementation may change after acquisition begins.

## Immutable prior-evidence bindings

Prediction verifies these exact paths and SHA-256 values before sealing:

- `data/elastic-hippocampus-stage-twelve-held-out-2026-08-13.json`: `ddbe8ecbd70e6d7c5035a2c81dd1a8a3bd5ef760f6e0c9aa27fd1445a4607796`
- `demos/elastic-hippocampus-proof/stage12-corpus/stage-twelve-score.lock`: `28129496ce6c0e196545c64f1879fdb4417fe60e5e8709ada2793c69f278a803`
- `data/elastic-hippocampus-stage-thirteen-development-result-2026-08-13.json`: `62803a7961f7236de2f25af816d0a081dc81d217bdac8aafe32b4b0ed7434ab7`
- `data/elastic-hippocampus-stage-thirteen-development-report-2026-08-13.md`: `5b103698439be30b687961bfe15d4c03eb977ff22c6055974466297041c62514`
- `data/elastic-hippocampus-stage-fourteen-preregistration-2026-08-13.md`: `8c0dfc720a2be44abcff96a8e611df16440cb9cebf5ffbe1930e776c54a9e0af`
- `data/elastic-hippocampus-stage-fourteen-protocol-incident-2026-08-13.md`: `372119db23c2da56c707750378ccac723a79827ee7063fa592a88aea31c25970`
- `demos/elastic-hippocampus-proof/stage14-corpus/sealed-predictions.json`: `2e46afcfffdee241e86f589be415bffffefab4b064f8359af2b6ae93959f1ac8`
- `demos/elastic-hippocampus-proof/stage14-corpus/relevance-labels.json`: `a0048dad3d2d87db9852340bdfb900264c78c516b33c4f68dda3ad7af9a7074e`
- `data/elastic-hippocampus-stage-fifteen-preregistration-2026-08-13.md`: `2ec990bebb68a3da273433f8324e2ab3dba5121205c46a774719a9b6b03f52c7`
- `data/elastic-hippocampus-stage-fifteen-report-2026-08-13.md`: `a093cb4f7315e256397406c4d4a1d074fa3b33c0db1dcb8625f794d44c4ba7e5`

All ten were verified present and hash-matching at freeze time.

## Permitted pre-acquisition validation record

Only Python compilation of six Stage Sixteen scripts; no-network/no-write `stage16_acquire.py --plan`; read-only `stage16_retrieval.py --self-test` against the immutable Stage Twelve local corpus; static source/constants/schema assertions; diagnostics; SHA-256 checks for eight bound implementations; and read-only verification of ten prior hashes are permitted. No network, corpus acquisition, Stage Sixteen preparation, prediction, pooling, labeling, or evaluation is permitted.

Recorded checks at freeze time:

- All six Stage Sixteen scripts compiled successfully.
- `stage16_acquire.py --plan` listed exactly the six ordered RFC Editor HTTPS plaintext sources with no network access and no writes.
- `stage16_retrieval.py --self-test` passed: 40 preserved global/body-max checks, four case-aware normalization vectors, and `body_max` metadata confirmed with `ablation_variants: false`.
- Cross-script binding consistency verified: `stage16_evaluate.FROZEN_FILES` equals `stage16_predict.SCRIPT_NAMES`; both reference this preregistration path; stage number is 16 throughout; opaque domain is `stage16-candidate|`; sealed provenance is `sealed_stage16_flat_global_top30`.
- Frozen query set verified as 20 queries, 16 positive and four control, with positive distribution 3/3/3/3/2/2 over `rfc791`, `rfc2131`, `rfc5849`, `rfc6376`, `rfc7230`, `rfc3261`.
- All eight implementation SHA-256 values recomputed and recorded above.
- All ten prior-evidence bindings verified hash-matching.
- No `stage16-corpus` directory exists.
