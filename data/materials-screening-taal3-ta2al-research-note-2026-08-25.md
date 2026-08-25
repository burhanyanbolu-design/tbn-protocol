# Research note: TaAl3 and Ta2Al as unexplored candidate materials for superconducting qubit fabrication

**Date:** 2026-08-25
**Author:** Burhan Yanbolu (Hardin AI Solutions), assisted by an automated screening tool
**Status:** Computational screening result only. No physical synthesis, thin-film growth,
or coherence measurement has been performed. This is a hypothesis for a materials
science / experimental quantum computing group to evaluate, not a claim of a working result.

## Summary

A computational screening of the Materials Project database, filtered by stability,
metallicity, non-magnetism, elemental practicality, and confirmed experimental
synthesis, identifies **TaAl3** (mp-869) and **Ta2Al** (mp-1193531) as candidate
materials for superconducting qubit fabrication that do not appear to have been
tested for this purpose in published literature searched to date.

## Motivation

Tantalum (Ta) is the current best-performing base metal for superconducting
transmon qubits, having tripled coherence times (T1) relative to the previous
standard, niobium, largely attributed to a less lossy native surface oxide
(fewer two-level-system defects). Tantalum nitride compounds (TaN, Ta2N) are
independently confirmed in 2026 literature as active candidates for superconducting
resonators and qubits. Given the demonstrated value of the Ta-based chemical
family, this screening asked: what other stable, real, tantalum-based compounds
exist that share this family's promising properties, but have not yet been
explored?

## Method

1. Queried the Materials Project public API for all known compounds containing
   combinations of Ta with N, Nb, Al, and other elements.
2. Scored each result by: energy above hull (stability; 0 = confirmed stable
   ground state), band gap (0 required -- metallic behaviour needed for a
   superconducting circuit material).
3. Applied a practicality filter: disqualified compounds containing radioactive
   or otherwise unavailable elements (e.g. Tc, U); penalized compounds containing
   rare/expensive elements (platinum-group metals, Au, Re) or rare-earth elements.
4. Cross-checked the surviving top candidates against Materials Project's computed
   magnetic ordering data, disqualifying any with confirmed ferromagnetic or
   ferrimagnetic ordering (magnetic moments are known to suppress superconductivity
   via pair-breaking).
5. Cross-checked the remaining candidates against Materials Project's
   theoretical-vs-experimental flag (ICSD-backed structures only), disqualifying
   purely theoretical/predicted structures that have never been physically
   synthesized.
6. Searched published literature (web search, arXiv, Nature, IOP, APS) for each
   surviving candidate to check for existing qubit-specific research.

As a validation check, the same pipeline was run on TaN and Ta2N, both of which
correctly returned as stable, metallic, non-magnetic, experimentally-confirmed
(ICSD-backed), and matched to real, current (2026) published qubit/resonator
research -- confirming the screening method reproduces known results before
being used to evaluate unknown candidates.

## Result

After all filters, two candidates remain that are stable, metallic, non-magnetic,
composed of common/inexpensive elements, and experimentally confirmed to exist
(ICSD-backed), with no qubit-specific published research found:

| Material | Materials Project ID | Energy above hull | Band gap | Magnetic? | Synthesized? |
|---|---|---|---|---|---|
| TaAl3 | mp-869 | 0.0000 eV | 0.0000 eV | No | Yes (ICSD) |
| Ta2Al | mp-1193531 | 0.0000 eV | 0.0000 eV | No | Yes (ICSD) |

Other candidates considered and rejected at various stages, with reasons:

| Material | Rejected because |
|---|---|
| Ta3Cr3N | Confirmed ferrimagnetic (1.15 uB moment) |
| Ta4Co2N | Confirmed ferromagnetic (8.45 uB moment) |
| LiTa3N4 | Theoretical only, never synthesized |
| MgTa2N3 | Theoretical only, never synthesized |
| TaNbAl6 | Theoretical only, never synthesized |
| TaTiAl6 | Theoretical only, never synthesized |
| (various) | Contains radioactive element (disqualified) or rare/expensive element (penalized) |

## Open question for domain experts

Has TaAl3 or Ta2Al thin-film growth and superconducting/coherence characterization
been attempted, published, or informally tried and abandoned for a known reason
not captured by this screening (e.g. poor thin-film quality, unfavourable surface
oxide chemistry, fabrication incompatibility)? This screening has no way to detect
a negative result that was never published, and absence of published research is
weak evidence of genuine novelty, not confirmation of it.

## Limitations (explicit, so this is not oversold)

- This is a computational stability/practicality screen only. It does not model,
  simulate, or predict actual superconducting transition temperature, coherence
  time, or surface oxide chemistry -- the properties that actually determine
  qubit performance.
- No physical synthesis, thin-film growth, or measurement has been performed by
  the author.
- Absence of published research on a candidate is not evidence that it would
  work well; it may simply be unexplored, or it may have been tried informally
  and not written up.
- The literature search was not exhaustive; it is possible relevant unpublished
  or non-English-language research exists that was not found.

## Tooling

This result was produced by a locally-run research agent
(`demos/materials-research-agent/materials_agent.py`) built on the public
Materials Project API, with every search cryptographically signed
(RSA-PSS-SHA256) and independently verifiable. It is not connected to, and does
not use, any live production TBN Protocol infrastructure.
