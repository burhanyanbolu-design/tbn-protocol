# We tried to find quantum advantage. Here are the seven things we got wrong.

A feasibility study of output-aware tensor-network contraction against real
quantum hardware.

**Author:** Burhan Yanbolu, Hardin AI Solutions
**Date:** September 2026 (v2 — adds Addendum VI, 9 September 2026)
**IBM Quantum jobs:** `dadm3mjdd5gc73d7gvjg`, `dadm9qdnj4cs73ae2teg` (2 jobs, 40,960 shots total)

## What changed in v2

Addendum VI adds a **seventh self-correction**, and it works against the
original study's own hardness argument: the 2^w classical cost figure describes
the *exact* regime only. An adversary willing to accept ~10⁻⁴ error reaches an
answer on 0.01% of the configurations at w=20. Hardness must be quoted against
a named accuracy target, not only a width.

Read `EQCCM-addendum-VI-pruning-2026-09-09.md` alongside the main writeup.

## Contents

- `EQCCM-feasibility-writeup-2026-09-05.md` — the full writeup (read this first)
- `EQCCM-addendum-VI-pruning-2026-09-09.md` — **new in v2**: amplitude-magnitude pruning, and the seventh correction
- `banded_scaling.py` — correctness vs statevector; the 2^w width sweep
- `banded_scaling_pruned.py` — **new in v2**: pruned contraction (imports the above; does not modify it)
- `fetch_fez_topology.py` — device coupling map + calibration (metadata only, no IBM credentials required)
- `heavyhex_width_search.py` — depth vs optimised contraction width on real topology
- `topology_comparison.py` — width-per-gate across seven topologies
- `sliced_cost_model.py` — sliced FLOP cost vs four adversary models
- `error_vs_depth.py` — mirror benchmark on hardware
- `analyse_error_vs_depth.py` — the corrected two-parameter fit
- `error_suppression_test.py` — dynamical decoupling + twirling comparison

## What this is

An honest, evidence-backed feasibility study testing whether quantum circuits
can be built where exact classical simulation cost grows much faster than the
physical circuit depth needed to run them. The answer, on hardware available
today, is no — and reaching that answer required correcting our own
conclusions seven times over the course of the study.

## What this is NOT

- **No quantum advantage, and no claim to it.**
- **No novel algorithm.** Frontier contraction is variable elimination, which
  is textbook. Multi-amplitude reuse is established in the literature.
  Amplitude-magnitude pruning (Addendum VI) is standard tensor-network practice.
- **No verified large-width result.** Any serious attempt at widths beyond
  ~50 needs a verification strategy designed in from the start. Addendum VI
  makes this requirement more urgent, not less.
- **No physical interpretation of the pruning geometry.** Addendum VI's
  coordinates are abstract state-space magnitudes, not physical positions.
- All *exact* classical cost figures are upper bounds favourable to the quantum
  side. Addendum VI shows the *approximate* cost is far lower.

## Reproducing this

Scripts marked with no IBM dependency can be run standalone. Scripts that
touch hardware (`error_vs_depth.py`, `error_suppression_test.py`) require
your own IBM Quantum credentials and will submit real jobs — do not run
these without understanding the cost/quota implications.

## License

This work is released for reproducibility and citation. See the writeup for
full technical detail, methodology, and the six corrections made during the
study.
