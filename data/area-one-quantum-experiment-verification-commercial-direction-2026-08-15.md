# Area One Commercial Direction: Quantum Experiment Verification

Date: 2026-08-15  
Status: SELECTED FOR VALIDATION  
Commercial path: Option 1 — quantum-experiment verification

## Decision

Area One will pursue a platform-neutral verification layer for quantum experiments as its first possible commercial route. The product is the evidence and reproducibility layer, not the unproven overlap-pair operator and not quantum hardware.

The existing `area-one-evidence-verifier==0.1.0` remains frozen as a local engineering prototype. This decision does not authorize changing it, publishing it, or representing it as commercially validated.

## Customer problem hypothesis

Quantum experiment results can depend on mutable notebooks, source versions, dependency environments, circuit compilation, backend identity, calibration state, shot configuration, raw counts, and analysis transformations. A recipient may be unable to establish exactly what ran or detect later substitution of inputs and results.

No customer interviews, paid pilots, purchase commitments, or demand evidence currently validate this hypothesis.

## Proposed product

For one declared experiment, capture and bind:

- source, dependency lock, circuit representation, and compiler settings;
- provider, backend, job identifiers, shot count, and execution timestamps;
- available calibration and device metadata;
- raw returned observations and the deterministic analysis recipe;
- derived claims, limitations, signatures, timestamps, and independent trust anchors.

Produce a portable evidence bundle and a standalone verdict that can be checked on a clean machine without trusting the experiment author's working directory.

## What verification would and would not establish

A passing verdict would establish internal integrity, provenance consistency, declared-environment reproducibility, and resistance to detectable artifact tampering under the specified trust anchors. It would not prove that a quantum provider reported honestly, that hardware was calibrated correctly, that an algorithm is novel, that quantum advantage exists, or that a scientific conclusion is true.

## First sellable pilot

The narrow pilot is one real experiment from one external quantum research team, initially targeting a single provider integration. The pilot deliverable is a complete evidence bundle, an independently runnable verifier, a verification report, and documented tamper tests.

Pilot acceptance requires clean-environment verification, detection of altered critical artifacts, explicit treatment of unavailable provider metadata, and confirmation from the external team that the evidence solves a material reproducibility or audit problem. Pricing and licence structure remain unset until that value is validated.

## Separation from overlap-pair research

The overlap-pair scatterer remains an independent falsifiable research program with six mandatory blockers. Its tuning and held-out evaluation remain prohibited. The commercial verifier must be useful for ordinary quantum experiments even if the scatterer fails.

## Immediate assignment

The provider-neutral schema and conditional IBM Quantum pilot protocol are now drafted:

- `data/quantum-experiment-evidence-schema-design-2026-08-15.md`
- `data/ibm-quantum-experiment-verification-pilot-protocol-2026-08-15.md`

Next, run engineering, security/data-governance, and developer-experience reviews. Do not implement an integration or begin partner execution until the schema contract, trust boundary, pilot acceptance criteria, and external data-handling terms are reviewed and approved.
