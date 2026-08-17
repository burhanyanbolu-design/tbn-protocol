# Area One Capacity Benchmark Amendment

Date: 2026-08-16  
Scope: T7 capacity measurement only  
Status: approved for implementation and measurement by the user's instruction to fix the T7 benchmark; no protocol freeze or held-out execution approval

## Reason

The original T3 concrete runner is a four-row, 1,152-work-unit implementation smoke. Each repetition pays fixed four-process startup cost before performing only four one-step evolutions. Dividing that fixed cost by 1,152 work units and extrapolating to 44,330,911,616 work units produced a non-representative 96,920,572-second estimate. The runner correctly labels itself `t3-implementation-smoke-not-capacity-approval` and cannot close Resolution 3.

This amendment defines the representative benchmark input before its output is measured. It does not alter the declared holdout workload, operator, controls, grids, horizons, worker count, safety factor, or resource gates.

## Frozen representative input

The capacity runner is `demos/area-one-control-simulator/pair_scatter_capacity_benchmark.py`, definition `area-one-capacity-benchmark/1.1`.

- Held-out grids remain the nine Cartesian combinations `s in {5,6,7}` and `R in {7,8,9}`.
- Horizons remain `ceil(sqrt(N))`, `ceil(2*sqrt(N))`, and `ceil(4*sqrt(N))`, where `N=R*(s+1)`.
- Primary evolution families remain baseline plus candidate plus 100 controls. Secondary horizons remain baseline plus candidate.
- The exact workload remains 3,010,612 four-column evolutions, 18,063,672 output rows, and 44,330,911,616 work units.
- The benchmark contains exactly 8,192 four-column evolutions and 49,152 output rows.
- The benchmark work-unit count is exactly 120,634,400.
- The 8,192 evolutions are apportioned over all 54 `(grid,horizon,baseline-or-paired-family)` strata by Hamilton largest-remainder apportionment, weighted by each stratum's exact declared evolution count. Ties resolve by canonical stratum order. Every stratum must receive at least one evolution.
- Primary paired-family tasks cycle deterministically through candidate and `control-000` through `control-099`. Secondary paired tasks use candidate. Control pairs come from the frozen manifest.
- Every task starts from four deterministic dense Fourier columns that are mutually orthonormal but are not any declared localized initial state. The terminal is derived deterministically from the benchmark ordinal. Therefore no task is a held-out micro-case and no held-out trajectory is executed.
- Paired tasks use fixed `theta=pi/4` and `phi=pi/2`. This fixes legal arithmetic work without selecting a scientific parameter from outcomes.
- Each evolution advances the real production four-column `complex128` kernel for its exact horizon, validates per-iteration norm drift, derives six synthetic linear combinations, performs final probability-bound checks only on those non-study states, and discards the values.
- Workers stream compact invariant metadata directly to per-worker files and return no trajectories, probabilities, state hashes, or row collections. Serialized benchmark rows use a fixed non-outcome scalar placeholder and synthetic keys.
- Encoding, 100,000-row sharding, merge, gzip, hashing, and verification are streaming and bounded independently of total row count; no stage retains all rows, shards, merged bytes, or compressed bytes in memory.
- Every numerical worker independently verifies one-thread native pool diagnostics. Linux `/proc` sampling covers the live process tree during evolution and is conservatively combined with parent and worker peak RSS.

## Frozen execution and gates

Run exactly three complete repetitions in the final digest-pinned Linux/amd64 image with four worker processes and one numerical thread per worker. Each repetition includes evolution, invariants, canonical row encoding, production sharding, deterministic merge, gzip level 9 with `mtime=0`, hashes, process-tree RSS, temporary/final disk measurement, and cleanup.

Apply the existing safety factor `2.0` and unchanged inclusive gates: wall time at most 28,800 seconds, peak RAM at most 8 GiB, final compressed output at most 10 GiB, and measured free disk at least three times projected temporary plus final bytes. `holdout_allowed` is the conjunction of all four gates.

A failed gate still blocks T7. The workload or benchmark input may not be changed after measurement without another amendment. Passing this benchmark is capacity evidence only and does not authorize T8, protocol freeze, tuning, lock finalization, or held-out execution.