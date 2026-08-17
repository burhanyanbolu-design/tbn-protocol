# ICV Lab — Independent Claim Verification

Preregistered adversarial verification of computational research claims.

Status: **internal, pre-revenue, zero external engagements.** Reference engagement 000 is our own falsified project.

## What this is

A reusable process and toolchain for answering one question about a computational claim:

> If this claim were wrong, would this experiment have caught it?

It was built while testing our own Elastic Overlapping Grid quantum-walk hypothesis, and it rejected that hypothesis. That is the only track record it currently has, and it is the honest basis of the pitch.

## The five checks

1. **Criterion satisfiability.** Is the declared success rule reachable at all? We froze a protocol requiring a per-grid positive fraction above `3/5`, then proved a parity selection rule caps it near `0.49` on two of nine held-out grids. The rule was unreachable independent of whether the physics worked. Most preregistrations are never checked for this.
2. **Control design and ranking.** What are the deliberately wrong versions of the claim, and where does the real one rank among them? Our genuine mechanism ranked 95 of 101. We held those numbers for weeks without ranking them.
3. **Effect-size triage.** Estimate the size of the claimed effect before building infrastructure. Ours was `0.0006`-`0.0024` against a `0.02` tail gate, a thirty-fold mismatch that doomed the design from the start.
4. **Independent reconstruction.** Rebuild every claimed statistic from raw records using a separate implementation that imports none of the producer's code, and compare the canonical summary byte for byte.
5. **One-shot holdout discipline.** Consumed-attempt publication so a held-out evaluation cannot be silently retried, retuned, or reinterpreted after the fact.

## What is reusable, precisely

Domain-independent spine, already built and exercised:

| module | bytes | role |
|---|---:|---|
| `publication_verifier.py` | 62,485 | independent streaming reconstruction and byte-for-byte summary comparison |
| `atomic_publication.py` | 31,059 | consumed-attempt state machine, fsync ordering, fail-closed recovery |
| `research_numerics.py` | 15,592 | exact binary64 and `Fraction` decision semantics, epsilon and tie rules |
| `matching_control_manifest.py` | 13,929 | deterministic control-family generation |
| `protocol_approval_anchor.py` | 8,418 | canonical normalization and freeze-by-hash |
| `independent_control_manifest.py` | 4,710 | independent regeneration of the control manifest |
| `independent_protocol_anchor.py` | 4,788 | independent protocol hash verification |

Domain-specific and **not** reusable: all `candidate*`, `eog*`, `overlap*`, `*quantum_walk*` kernels, and the eight `area-one-pair-*` schemas. Each new domain needs its own operator model, metric, and control class.

## Honest limitations

- No external client has ever been served. No revenue, no delivered engagement.
- Verification requires domain expertise per claim. The toolchain checks discipline, not physics.
- A passing verification means "this experiment could have caught this error," not "this claim is true."
- We falsified our own hypothesis. That is evidence the process bites, not evidence that we can validate arbitrary quantum theory.
- Nothing here is a certification, accreditation, or endorsement.

## Engagement layout

```
engagements/<id>-<client>-<claim-slug>/
  00-intake/          claim statement, declared metric, declared success rule
  01-protocol/        protocol document + .sha256 sidecar, frozen before any run
  02-controls/        control manifest + independent regeneration
  03-effect-size/     triage estimate versus declared thresholds
  04-criteria-check/  satisfiability analysis of every success criterion
  05-run/             raw records, shards, hashes, runtime identity
  06-verification/    independent reconstruction result
  07-verdict/         verdict.json and report
  audit/              findings, corrections, sign-off
```

## Dashboard

`python icv_dashboard.py` scans `engagements/`, writes `dashboard.json` and `dashboard.html`, and prints a summary. Standard library only, no dependencies, static output suitable for existing nginx.
