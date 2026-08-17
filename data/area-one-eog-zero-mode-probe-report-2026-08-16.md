# Area One EOG Hierarchical Zero-Mode Probe Report

Date: 2026-08-16
Status: **COMPLETED — NATURAL ZERO-MODE MECHANISM NOT SUPPORTED**
Scope: topology-only pre-protocol discovery on `(s,R)=(2,6),(3,6),(4,6)`

## Question and boundary

Following Burhan's instruction to try the Aram-Harrow-inspired direction, this probe tested whether the current full-coordinate EOG topology naturally reduces to an endpoint-preserving hierarchical Hamiltonian with chiral symmetry and a useful zero mode. It read no T9/outcome artifact, lock, or held-out input and started no new T9. It did not alter the frozen Candidate 1 protocol or historical Candidate 2 evidence.

Design: `data/area-one-eog-zero-mode-probe-design-2026-08-16.md`, SHA-256 `sha256:d4f67699eee997bdf02fcec97304533b8b64d995b8b7aa6006b3d8ea4d93b701`.
Source: `demos/area-one-control-simulator/eog_zero_mode_topology_probe.py`, SHA-256 `sha256:2513f83b83fd79b7cfe8951873c51c27e93ed6acb29bf5b6d42e0c3306051e33`.
Artifact: `demos/area-one-control-simulator/eog-zero-mode-topology-probe-output/eog-zero-mode-topology-probe.json`, 179,033 bytes, SHA-256 `sha256:23b81deb83b892b9ce6c74399dfaa182e9f6e43ba47e3fe3945d266ba3b54179`; canonical UTF-8 JSON plus one LF, no CR.

The exact-image run used named container `area-one-eog-zero-mode-topology-probe`, full ID `fc9fc78e1ad0e90c31e4a340f57b0da1642c560074308046011da7189e303239`, image `sha256:96379ff14fb29df67b28c19102d93cb1cc912e23962e0c917b5209b605edb3f2`, from `2026-08-16T16:05:36.599450198Z` to `2026-08-16T16:05:40.09898975Z`. It exited `0`, was not OOM-killed, and logged `EOG_ZERO_MODE_TOPOLOGY_PROBE_PASS` with `mechanism_supported=false`.

## Structural result

For every grid, row, column, and overlap-fiber partitions failed exact quotient closure or endpoint representation. Reflection orbits were exactly closed but folded entrance and exit into the same cell. Deterministic equitable refinement with entrance and exit separated returned all `18`, `24`, or `30` original vertices, giving no compression. Therefore no nontrivial endpoint-preserving hierarchical quotient was found.

All three candidate graphs were non-bipartite and lacked chiral symmetry. For `s=2` and `s=4`, the ordinary horizontal cycles have odd length. For `s=3`, the torus is bipartite before overlap edges, but every genuine overlap edge connects the same checkerboard colour and breaks bipartiteness.

Exact integer rank gave nullity `0` for `s=2` and `s=3`. Their nearest-to-zero gaps were `0.23292613694443678` and `0.2757737228212539`, but without a zero sector their endpoint weights and transfer were zero. For `s=4`, nullity was `1` and gap `0.07843899586689047`. An independent exact-arithmetic nullspace reconstruction established that this unique null vector has entrance and exit coordinates exactly equal to zero. The artifact's entrance weight `1.93e-28`, exit weight `7.36e-29`, and transfer `1.19e-28` are therefore floating-point eigensolver noise, not physical endpoint support, and remain far below the preregistered `1e-12` gate.

All 357 matched controls retained the declared weighted edge-channel counts and connectivity; none was bipartite. Some had accidental zero eigenvalues, but none supplied the complete protected hierarchical mechanism. High tied percentiles on zero-valued scores do not override the failed structural gates.

## Independent audit and cleanup

A read-only independent audit found no material computational defect or scientific overclaim. It checked the declared topology, partitions, bipartiteness, exact ranks and nullities, matched controls, canonical artifact form, source/design bindings, and bounded conclusion. Runtime and container identity remain supported by the separately captured Docker inspection and logs rather than by the JSON artifact alone.

After those IDs, timestamps, logs, hashes, results, and the exact-nullspace correction were recorded locally and in remote Kiro memory, the exited probe container was removed. A filtered Docker check found no remaining container with the probe name, and no managed background process remained.

## Decision

The direct natural surrogate `H=A_torus+M_genuine` is not a valid Harrow-style EOG mechanism and must not be promoted to a protocol or T9. This does not reject hierarchical quantum walks, Harrow's result, EOG arithmetic, the laboratory, or every engineered EOG Hamiltonian. A future attempt would have to deliberately redesign boundary conditions, supervertex regularity, weights and/or auxiliary states before seeing outcomes, then compare against equally expressive matched controls. No such redesign is authorized by this report.

The frozen Candidate 1 protocol remains `sha256:9710588a73381b2599233a7fefeab17e4dcf0e2bea26b8e845dcd048c6d355be`. No hardware, quantum-advantage, novelty, patent, product, market, or revenue claim is established.