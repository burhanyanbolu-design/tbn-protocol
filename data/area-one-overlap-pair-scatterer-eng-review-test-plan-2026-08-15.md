# Area One Overlap-Pair Scatterer — Engineering Review Test Plan

Generated: 2026-08-15  
Scope: blocker-closure implementation only; no tuning or held-out execution

## Critical paths

1. Generate the 100-family cross-row manifest twice and require byte-identical output and hash.
2. Evolve candidate and representative controls through production kernels and compare with a separately constructed direct-formula matrix.
3. Serialize canonical rows, merge deterministic shards, reconstruct summaries independently, and require byte-identical decisions.
4. Consume a holdout attempt before first outcome and fault-inject every crash boundary; no restart may resume or expose staging.

## Coverage diagram

```text
family generator -> schema checks -> family hash
  | candidate/duplicate/non-bijection/unstable-kind => hard failure

state input -> oracle -> pair layer -> coin -> shift -> probability
  | bad dtype/shape/stride/non-finite/norm/order      => hard failure
  +-> direct matrix oracle -> amplitude comparison   => <= 1e-12

rows -> shard assignment -> canonical merge -> gzip -> completion
  | missing/duplicate/order/hash/count/schema error  => hard failure
  +-> standalone reconstruction -> thresholds/rank  => exact match

lock verify -> attempt-consumed -> staging -> verify -> lock recheck
  | crash at any post-consumption point              => fail, never resume
  +-> atomic publish -> completion last              => accepted publication
```

## Required edge cases

- Every `R=6,7,8,9`; candidate, cyclic `control-000`, reflected `control-004`, and random `control-009`/`control-099`.
- Every candidate parameter, `theta=0`, `theta=pi/2`, every phase, paired/unpaired terminals, every basis vector, and 32 frozen vectors per dimension.
- NaN, infinities, negative zero, exact thresholds, adjacent binary64 values, quantile endpoints/ties, and exact count fractions.
- C/non-C-contiguous tensors, wrong axes/dtype, unexpected BLAS threads, worker-count changes, final partial shard, and insufficient disk.
- Truncated/concatenated gzip, CRLF, missing final LF, duplicate JSON keys/rows, unknown fields, malformed `.17g`, and compression abuse.
- Crashes before/after marker creation, every staging write, lock recheck, every rename, directory sync, and completion publication.

## Acceptance

All tests must pass in the frozen Linux container. Producer and independent verifier must not share evolution or aggregation implementations. No test fixture may contain held-out outcomes. Passing this plan closes implementation evidence only; it does not establish scientific performance.
