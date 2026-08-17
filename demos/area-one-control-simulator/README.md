# Area One deterministic control simulator

This is the first bounded prototype for the Elastic Overlapping Grid Area One concept. It executes a fixed route over full `(row, column)` coordinates and emits simulated control events. It does not connect to hardware and is not a quantum simulator.

## Model

For step `s >= 1`, valid positions satisfy `row >= 0` and `0 <= column <= s`. Their displayed label is:

```text
label = s * row + column
```

Full coordinates remain authoritative because `(r, s)` and `(r + 1, 0)` share a label but are distinct states in this prototype. The boundary policy is explicit rejection: an invalid move stops execution without dispatching its event.

The simulator stops when it reaches the terminal coordinate, rejects a boundary crossing, or exhausts the supplied route.

## Run

From the repository root:

```powershell
python demos/area-one-control-simulator/simulator.py
```

Custom deterministic route:

```powershell
python demos/area-one-control-simulator/simulator.py --step 5 --start 0,0 --terminal 3,2 --route down-right,right,down-left,down-right
```

The default demonstration follows labels `0 -> 6 -> 7 -> 11 -> 17` and halts at coordinate `(3,2)`.

## Address identity and verification

`positions_for_label()` returns every coordinate represented by a label. With step `5`, label `5` returns both `(0,5)` and `(1,0)`; neither is silently discarded or treated as the other.

Run the focused deterministic verification:

```powershell
python -m unittest discover -s demos/area-one-control-simulator -p "test_*.py" -v
```

It verifies identical replay, overlapping-address identity, boundary rejection without event dispatch, and immediate terminal halting.

## Stage-three demonstrations

Run the verified demonstrations:

```powershell
python demos/area-one-control-simulator/demonstrations.py
```

The program fails with a non-zero exit if any invariant is broken. It demonstrates the `0 -> 6 -> 7 -> 11 -> 17` zigzag terminal route, zero events when starting at a terminal, divergent behavior for the two coordinate states carrying label `5`, and byte-for-structure deterministic replay.

## Stage-four classical probability

The probabilistic simulator chooses movements using explicit weights and Python's seeded classical pseudorandom generator. It is not a quantum model. The same seed, weights, initial state, and step limit reproduce the same complete trace.

```powershell
python demos/area-one-control-simulator/probabilistic_simulator.py
```

Custom example:

```powershell
python demos/area-one-control-simulator/probabilistic_simulator.py --seed 21 --max-steps 20 --weights "down-right=2,right=1,down-left=2"
```

A selected invalid movement invokes the existing reject boundary policy and dispatches no event. Every run also has a mandatory maximum-step stop.

## Standard quantum-walk baseline

`quantum_walk_baseline.py` is a classical numerical simulation of an established discrete-time coined quantum walk on the integer line. Each ordinary step applies a Hadamard coin and conditional shift. A declared terminal position is then projected out into an absorbing sink, making the effect of repeated detection explicit.

```powershell
python demos/area-one-control-simulator/quantum_walk_baseline.py --steps 12 --start 0 --terminal 3
```

The output compares per-step and cumulative absorption with a symmetric classical random walk under the same terminal rule. It also verifies probability accounting and reports the maximum norm error during ordinary unitary evolution.

This is only a reference baseline. It is not an EOG-specific quantum operator, a hardware implementation, evidence of quantum advantage, or a novelty claim. The absorbing measurement is intentionally reported because it changes the walk's dynamics.

## EOG-coordinate Grover walk

`eog_quantum_walk.py` applies the standard four-direction Grover coin to full EOG `(row, column, direction)` states on a finite periodic grid. The periodic flip-flop shift is a reversible permutation, so the ordinary coin-plus-shift operation is unitary. Terminal coordinates are projected into an absorbing sink only after each ordinary step.

```powershell
python demos/area-one-control-simulator/eog_quantum_walk.py
```

The default terminal `(1,0)` and endpoint `(0,3)` both display label `3` when `step=3`, but only `(1,0)` is absorbing. This directly proves that displayed labels cannot define quantum-state identity.

The module compares absorption with a four-neighbour classical random walk on the same periodic grid and checks total probability plus ordinary-step norm preservation. This operator is an established Grover walk expressed through EOG coordinates; the coordinate presentation does not create new quantum dynamics or establish an advantage.

## Measurement-protocol comparison

Terminal detection is not a harmless implementation detail. `measurement_protocols.py` compares three declared schedules: projection after every step, projection at a configurable interval, and projection only after the final unitary step.

```powershell
python demos/area-one-control-simulator/measurement_protocols.py --steps 12 --interval 3
```

Every protocol preserves norm during ordinary coin-plus-shift evolution and accounts for absorbed plus surviving probability. Different cumulative absorption values demonstrate that changing when detection occurs changes the model itself. The output must therefore accompany any reported hitting or termination result.

## Toy phase-noise sensitivity

`noise_sensitivity.py` performs seeded Monte Carlo trajectories in which each basis amplitude independently receives a random π phase flip between the Grover step and terminal measurement. Every trajectory remains norm-preserving until the absorbing projection, and absorbed plus surviving probability is checked.

```powershell
python demos/area-one-control-simulator/noise_sensitivity.py --trajectories 200 --noise "0,0.01,0.05,0.1"
```

The zero-noise ensemble must reproduce the exact noiseless walk. Non-zero settings report mean absorption and population standard deviation across trajectories. This is a deliberately simple, uncalibrated phase-noise model: it does not represent a named device, predict hardware performance, or establish robustness.

## Evaluation metrics

`evaluation_metrics.py` reports terminal probability, the conditional mean detection step, terminal-check count, and logical Grover-coin/shift applications for each measurement schedule.

```powershell
python demos/area-one-control-simulator/evaluation_metrics.py --steps 12 --intervals "1,3,12"
```

The conditional mean is calculated only over absorbed probability; it is not an unconditional runtime guarantee. Terminal checks and operator applications are transparent logical-operation counts. They are useful comparison proxies but are not compiled quantum-circuit gate counts, wall-clock costs, or device resource estimates.

## Surviving-state coherence

`coherence_analysis.py` builds the Monte Carlo ensemble density matrix after phase noise and terminal absorption. It conditions the density matrix on survival, then reports ℓ1 coherence normalized by the full Hilbert-space maximum and ensemble purity.

```powershell
python demos/area-one-control-simulator/coherence_analysis.py --trajectories 200
```

At zero noise all trajectories are identical, so the surviving ensemble must have purity `1`. Random phase histories generally produce a mixed ensemble with lower purity and coherence. Conditioning on survival is explicit: the separate survival probability is reported and coherence is undefined if nothing survives. These values characterize only the simulated basis, initial state, measurement schedule, and toy phase-noise channel.

## Independent operator-matrix verification

`operator_matrix_verification.py` constructs the complete Grover evolution matrix column-by-column from individual basis states. It independently checks `U†U = I` and compares repeated dense-matrix evolution with the dictionary-based simulator.

```powershell
python demos/area-one-control-simulator/operator_matrix_verification.py
```

The matrix basis includes every `(row, column, direction)` state. Coordinates that share an EOG label occupy separate matrix rows and columns. Passing this check validates the implemented finite periodic operator; it does not validate a physical device or establish that the operator is novel.

## Exhaustive bounded parameter sweep

`parameter_sweep.py` enumerates small grid dimensions, every possible start/terminal pair, repeated/periodic/final measurement schedules, classical walks, overlapping-coordinate identities, and complete operator matrices.

```powershell
python demos/area-one-control-simulator/parameter_sweep.py
```

The default bounds cover step sizes `1..3`, row counts `1..3`, and four evolution steps. Any unitarity, per-step norm, total-probability, or overlapping-identity failure terminates the sweep with a non-zero exit. This is exhaustive only within the printed finite bounds, not a proof for all grid sizes.

## Exact density-channel oracle

`exact_density_channel.py` implements the ensemble channel corresponding to the toy independent random π phase flips. Diagonal density entries remain unchanged while off-diagonal entries receive the exact factor `(1 - 2p)²` after each phase-noise step.

```powershell
python demos/area-one-control-simulator/exact_density_channel.py --noise 0.1 --trajectories 1000
```

The exact density evolution reports absorption, survival-conditioned ℓ1 coherence, purity, and probability error, then compares them with seeded Monte Carlo trajectories. Agreement validates that the trajectory sampler averages the channel it claims to model. It does not make the toy channel representative of real hardware.

## Monte Carlo convergence

`monte_carlo_convergence.py` compares nested seeded trajectory samples with the exact density-channel absorption value. It reports absolute error, standard error, and a normal-approximation 95% confidence interval at each sample size.

```powershell
python demos/area-one-control-simulator/monte_carlo_convergence.py --sample-sizes "100,500,1000,5000"
```

The study makes sampling uncertainty visible instead of treating one Monte Carlo estimate as exact. Confidence intervals describe repeated sampling under this toy model; they do not cover model misspecification or hardware uncertainty.

## Boundary-policy classification

`boundary_policies.py` constructs and checks complete operators for periodic, reflective, and absorbing finite-grid boundaries.

```powershell
python demos/area-one-control-simulator/boundary_policies.py
```

Periodic wrapping and the implemented reflection rule are reversible permutations and must pass `U†U = I`. The absorbing boundary discards outward amplitude, loses norm, and must be classified as non-unitary. It represents an open-system sink and cannot be presented as ordinary closed-system evolution.

## Topology-matched ordinary-index baseline

`topology_baseline.py` maps every full EOG coordinate to a conventional unique row-major node ID and evolves both representations with identical Grover, boundary, terminal, and measurement rules.

```powershell
python demos/area-one-control-simulator/topology_baseline.py
```

The amplitude and absorption results must agree exactly. The report also shows that there are fewer displayed EOG labels than coordinate states because boundary labels overlap. Therefore full EOG coordinates are isomorphic to ordinary unique node indices, while displayed labels are metadata rather than new quantum dynamics. This is a required fairness result and limits any novelty claim based only on the numbering system.

## Initial-state and terminal sensitivity

`sensitivity_sweep.py` evaluates uniform, directional and phase-balanced normalized coin states against every possible non-start terminal coordinate and multiple measurement schedules.

```powershell
python demos/area-one-control-simulator/sensitivity_sweep.py
```

For each configuration family it reports minimum, mean and maximum absorption plus the full spread and associated terminal positions. Large spreads reveal dependence on configuration choices. Any published result must disclose the initial coin, terminal-selection method and measurement schedule rather than reporting only the best case.

## Local scaling benchmark

`scaling_benchmark.py` measures median pure-state simulation runtime and peak Python allocation while reporting Hilbert-space dimension and dense density-matrix growth.

```powershell
python demos/area-one-control-simulator/scaling_benchmark.py --configurations "2:3,3:5,5:8" --steps 20 --repeats 5
```

Configuration syntax is `STEP:ROWS`; width is `STEP + 1`. Dense storage reports the minimum 16-byte-per-complex numeric payload and excludes Python object overhead. Runtime and memory numbers describe only this Python implementation on the machine that executed the command, not QPU speed, compiled-circuit cost, or hardware scalability.

## Integrity-hashed verification report

`verification_report.py` assembles the coordinate, operator, topology, boundary, measurement and phase-noise checks into one deterministic JSON evidence report.

```powershell
python demos/area-one-control-simulator/verification_report.py --output demos/area-one-control-simulator/verification-report.json
```

The report contains its complete configuration, individual pass/fail checks, measured results, supported statements, explicit non-claims and a SHA-256 hash over canonical JSON. Identical parameters and code produce identical reports; modifying any hashed field invalidates verification. This is integrity evidence, not a digital signature or proof of who generated the report.

## Standalone report-file verification

`report_file_verifier.py` validates a saved report without importing or rerunning the simulator. It uses only the Python standard library and checks strict JSON parsing, duplicate keys, schema version, SHA-256 content integrity, check/verdict consistency, and optional comparison with a separately supplied expected hash.

```powershell
python demos/area-one-control-simulator/report_file_verifier.py demos/area-one-control-simulator/verification-report.json --expected-hash sha256:368122498686b446dc00d496e28fd00a3a97cd64e7c9ea5193a8c648faabb640 --require-passed
```

Exit code `0` means the file is structurally consistent, its content hash matches, and any requested expectations passed. Exit code `1` means verification failed; `2` means the file could not be read as strict JSON. This verifies integrity only. Because SHA-256 is unkeyed, it does not prove who issued the report; issuer authentication would require a separate digital-signature stage.

## Optional issuer signatures

`report_signature.py` adds issuer authentication as a detached JSON sidecar. The original report remains unchanged, so its established content hash stays compatible. The sidecar binds the report schema and hash to an issuer name, a public-key-derived `a1key_...` identifier, and `RSA-PSS-SHA256`, then signs that canonical envelope.

Signing and timestamping are the only optional features with external dependencies. Exact compatible pins are in `requirements-signing.txt`: [PyPI cryptography 46.0.6](https://pypi.org/project/cryptography/46.0.6/) and [PyPI rfc3161ng 2.1.3](https://pypi.org/project/rfc3161ng/2.1.3/).

```powershell
python -m pip install -r demos/area-one-control-simulator/requirements-signing.txt
python demos/area-one-control-simulator/report_signature.py sign demos/area-one-control-simulator/verification-report.json --private-key C:\secure\area-one-private.pem --issuer "Hardin AI Solutions" --output demos/area-one-control-simulator/verification-report.signature.json
python demos/area-one-control-simulator/report_signature.py verify demos/area-one-control-simulator/verification-report.json demos/area-one-control-simulator/verification-report.signature.json --public-key C:\public\area-one-public.pem --expected-issuer "Hardin AI Solutions" --require-passed
```

The signer never creates a key, embeds a private key, or accepts a password on the command line. An encrypted PEM can be unlocked through the `AREA_ONE_SIGNING_KEY_PASSWORD` environment variable. Verification fails closed for report tampering, signature tampering, wrong issuer, wrong public key, unsupported algorithm, weak RSA keys, or malformed evidence. Trust still depends on distributing the correct public key through an independent trusted channel; a valid signature alone does not establish that a supplied public key belongs to the claimed organization.

## Issuer trust, rotation, and revocation

`issuer_trust.py` manages a portable trust registry containing canonical public keys and explicit `active`, `retired`, or `revoked` status. Each registry has a deterministic SHA-256 `trust_hash`. That hash must be obtained through an independent trusted channel; accepting a registry and its expected hash from the same untrusted source provides no authentication.

```powershell
python demos/area-one-control-simulator/issuer_trust.py create --issuer "Hardin AI Solutions" --public-key C:\public\area-one-public.pem --valid-from 2026-08-15T09:00:00Z --output C:\public\area-one-trust.json
python demos/area-one-control-simulator/issuer_trust.py verify C:\public\area-one-trust.json --expected-hash sha256:<independently-obtained-hash>
python demos/area-one-control-simulator/issuer_trust.py verify-report demos/area-one-control-simulator/verification-report.json demos/area-one-control-simulator/verification-report.signature.json C:\public\area-one-trust.json --expected-trust-hash sha256:<independently-obtained-hash> --require-passed
```

Rotation requires the current independently expected hash and creates a new registry: the old key becomes `retired` at the cutover while the new key becomes `active`. Signatures made by the retired key before cutover remain valid. Revocation also requires the current expected hash, a time, and a reason; a revoked key invalidates every associated signature, including signatures claiming an earlier issuance time.

```powershell
python demos/area-one-control-simulator/issuer_trust.py rotate C:\public\area-one-trust.json --expected-current-hash sha256:<current-hash> --new-public-key C:\public\area-one-public-v2.pem --effective-at 2026-09-01T00:00:00Z --output C:\public\area-one-trust-v2.json
python demos/area-one-control-simulator/issuer_trust.py revoke C:\public\area-one-trust.json --expected-current-hash sha256:<current-hash> --key-id a1key_<16-hex> --revoked-at 2026-08-20T12:00:00Z --reason "suspected compromise" --output C:\public\area-one-trust-revoked.json
```

The signed `issued_at` field supports ordinary rotation windows but is not a trusted timestamp. A compromised key holder could backdate a new signature, which is why revoked keys fail closed regardless of the claimed issuance time. External timestamping or transparency logging would be a separate future stage.

## Append-only transparency evidence

`transparency_log.py` accepts only reports that already pass the pinned issuer-trust policy. Each append binds the report hash, complete signature-evidence hash, issuer, key ID, signed issuance time, and log time. Entries form a SHA-256 chain; every prefix also receives a Merkle root and chained checkpoint hash.

Create an empty log, append the first trusted report into a new immutable bundle, then publish the resulting checkpoint hash independently:

```powershell
python demos/area-one-control-simulator/transparency_log.py create --log-id area-one-public --output C:\public\area-one-log-0.json
python demos/area-one-control-simulator/transparency_log.py append C:\public\area-one-log-0.json demos/area-one-control-simulator/verification-report.json demos/area-one-control-simulator/verification-report.signature.json C:\public\area-one-trust.json --expected-trust-hash sha256:<trusted-registry-hash> --output C:\public\area-one-log-1.json
python demos/area-one-control-simulator/transparency_log.py verify C:\public\area-one-log-1.json --expected-checkpoint-hash sha256:<independently-published-checkpoint>
```

Every later append requires the currently pinned checkpoint hash and writes a new bundle rather than silently replacing history. `verify-extension` proves that all old entries and checkpoints are an exact prefix of the newer bundle. `proof` creates a compact Merkle inclusion proof, and `verify-proof` checks it against an independently obtained root hash.

```powershell
python demos/area-one-control-simulator/transparency_log.py verify-extension C:\public\area-one-log-1.json C:\public\area-one-log-2.json --expected-old-checkpoint sha256:<old-checkpoint> --expected-new-checkpoint sha256:<new-checkpoint>
python demos/area-one-control-simulator/transparency_log.py proof C:\public\area-one-log-2.json --index 0 --output C:\public\area-one-proof-0.json
python demos/area-one-control-simulator/transparency_log.py verify-proof C:\public\area-one-proof-0.json --expected-root sha256:<independently-published-root>
```

This is tamper-evident, not an independent timestamp authority by itself. If the issuer controls both the log and all checkpoint publication, it can still construct an alternate history before anyone pins a checkpoint. Independence begins only when another party observes and preserves a checkpoint or when an external timestamp authority signs it.

## Independent checkpoint witnesses

`checkpoint_witness.py` lets a separate organization observe and sign a transparency checkpoint using its own RSA key. The attestation binds the log ID, tree size, Merkle root, checkpoint hash, checkpoint-generation time, witness-observation time, witness identity, and public-key-derived witness key ID.

The witness signs only after independently checking the expected checkpoint hash. Private keys are always supplied explicitly, never generated by this tool, and encrypted witness keys use the `AREA_ONE_WITNESS_KEY_PASSWORD` environment variable rather than a command-line password.

```powershell
python demos/area-one-control-simulator/checkpoint_witness.py sign C:\public\area-one-log-1.json --expected-checkpoint-hash sha256:<observed-checkpoint> --private-key C:\witness-secure\witness-private.pem --witness "Independent Witness Ltd" --output C:\public\area-one-log-1.witness.json
python demos/area-one-control-simulator/checkpoint_witness.py verify C:\public\area-one-log-1.json C:\public\area-one-log-1.witness.json --public-key C:\witness-public\witness-public.pem --expected-witness "Independent Witness Ltd"
```

A valid attestation proves control of the corresponding witness private key and that the signed checkpoint fields were not altered. Independence additionally requires the witness key to be controlled outside the report issuer and the public key to be obtained through a trusted channel. This is a witness protocol, not RFC 3161 certification and not proof that the witness's clock was externally synchronized.

## Multi-witness quorum

`witness_quorum.py` prevents one witness from becoming a single point of trust. A deterministic policy pins the exact witness names, canonical public keys, key fingerprints, key status, and threshold. The policy hash must be distributed independently so an attacker cannot silently replace members or reduce a `2-of-3` rule to `1-of-1`.

```powershell
python demos/area-one-control-simulator/witness_quorum.py create-policy --policy-id area-one-2-of-3 --threshold 2 --member "Witness A=C:\witness-a\public.pem" --member "Witness B=C:\witness-b\public.pem" --member "Witness C=C:\witness-c\public.pem" --output C:\public\area-one-witness-policy.json
python demos/area-one-control-simulator/witness_quorum.py verify-policy C:\public\area-one-witness-policy.json --expected-policy-hash sha256:<independently-published-policy-hash>
python demos/area-one-control-simulator/witness_quorum.py verify C:\public\area-one-log-1.json C:\public\area-one-witness-policy.json C:\public\witness-a.json C:\public\witness-b.json --expected-policy-hash sha256:<independently-published-policy-hash>
```

Only distinct active witness key IDs count. Duplicate attestations, unknown keys, revoked members, invalid signatures, altered checkpoints, and wrong witness names are rejected evidence and contribute zero votes. Invalid extra evidence does not defeat an otherwise valid quorum; this prevents an attacker from causing failure merely by attaching garbage. The verifier reports both accepted witnesses and every rejection.

Quorum strength still depends on genuine operational independence. Three keys controlled by the same person or stored on the same machine are not three independent witnesses, even if a `2-of-3` signature policy passes cryptographically.

## RFC 3161 trusted timestamps

`rfc3161_timestamp.py` implements a real [RFC 3161 Time-Stamp Protocol](https://datatracker.ietf.org/doc/html/rfc3161) client and offline verifier without requiring the OpenSSL executable. A request sends only the 32-byte SHA-256 checkpoint imprint plus a random 128-bit nonce. Evidence preserves the complete DER request and response.

Verification fails closed unless it confirms the request/response nonce, SHA-256 checkpoint imprint, granted status, CMS signed attributes, CMS signature, timestamping-only critical EKU, certificate validity at the granted time, and a path to an explicitly supplied root. It supports RSA PKCS#1 v1.5, ECDSA, Ed25519, and Ed448 TSA signatures; RSA-PSS CMS parameters are deliberately rejected rather than guessed.

```powershell
python demos/area-one-control-simulator/rfc3161_timestamp.py request C:\public\area-one-log-1.json --expected-checkpoint-hash sha256:<checkpoint> --tsa-url https://freetsa.org/tsr --ca-file C:\trusted\tsa-root.pem --output C:\public\area-one-log-1.rfc3161.json
python demos/area-one-control-simulator/rfc3161_timestamp.py verify C:\public\area-one-log-1.json C:\public\area-one-log-1.rfc3161.json --ca-file C:\trusted\tsa-root.pem
```

The repository includes an offline regression token inside `area-one-evidence-bundle-fixture.zip`, created through the live [FreeTSA endpoint](https://freetsa.org/tsr) on 15 August 2026. The bundle is explicitly synthetic and carries no production issuer identity; its disposable private keys were never persisted. Its published [FreeTSA root](https://freetsa.org/files/cacert.pem) is stored as `freetsa-root.pem` with SHA-256 fingerprint `a6379e7cecc05faa3cbf076013d745e327bbbaa38c0b9af22469d4701d18aabc`.

The verifier performs bounded offline path validation but does not fetch CRLs or OCSP responses. A passing result proves the token was signed by a certificate chaining to the supplied root and was valid at token generation time; it does not establish current non-revocation, eIDAS qualification, or legal status. Production deployments must obtain and pin TSA roots through an independently trusted distribution channel rather than trusting a certificate downloaded alongside an evidence file.

## Portable end-to-end evidence bundle

`evidence_bundle.py` packages the report, issuer signature, issuer trust registry, transparency log, witness policy and attestations, RFC 3161 response, and TSA certificates into one deterministic ZIP. `manifest.json` hashes every member and binds the exact transparency entry that references the report and issuer signature.

One command verifies the complete fixture from report semantics through the live timestamp:

```powershell
python demos/area-one-control-simulator/evidence_bundle.py verify demos/area-one-control-simulator/area-one-evidence-bundle-fixture.zip --expected-report-hash sha256:368122498686b446dc00d496e28fd00a3a97cd64e7c9ea5193a8c648faabb640 --expected-issuer-trust-hash sha256:c06763c8bbe77750c912cde0dca7fdd6ba76c586b020c676fb1244ab9b38c97a --expected-witness-policy-hash sha256:ffbca3acf215a28c9702e84ace9d0bf76de8c97eb1eaca73d6356f911783d033 --expected-checkpoint-hash sha256:57a88cbc9f3605ea1294232360aa2ed8cabb0d89d15f86d6f73d2a7e75363011 --expected-tsa-root-sha256 sha256:a6379e7cecc05faa3cbf076013d745e327bbbaa38c0b9af22469d4701d18aabc
```

`create` accepts the component files and the same independent anchors, verifies the complete chain in memory, and writes nothing if validation fails. Use `python evidence_bundle.py create --help` for its explicit component arguments.

The ZIP reader rejects duplicate names, path traversal, symbolic links, encryption, unlisted files, oversized members, suspicious compression ratios, duplicate JSON keys, non-standard JSON constants, and artifact or manifest hash mismatches. Bundled trust files are never self-authenticating: verification still requires the issuer-trust hash, witness-policy hash, checkpoint hash, report hash, and TSA-root fingerprint from independent channels.

`area-one-evidence-bundle-fixture.zip` is a public-only regression artifact. Its issuer and witness keys were generated only in memory and discarded after signing; it is not a Hardin production issuance or customer evidence package. The corresponding expected values are recorded in `area-one-evidence-bundle-fixture-anchors.json` for tests, not as a model for production anchor distribution.
## Installable verifier CLI (local release artifact)

Version `0.1.0` is packaged as a local pure-Python wheel. It has been clean-room tested outside the source tree, but it is not published to PyPI. From `demos/area-one-control-simulator`, install the retained wheel into a fresh Python 3.11-or-newer environment:

```powershell
python -m pip install .\dist\area_one_evidence_verifier-0.1.0-py3-none-any.whl
area-one-verify --version
```

The expected version output is `area-one-verify 0.1.0`. Verify the complete public fixture with the installed command:

```powershell
area-one-verify verify .\area-one-evidence-bundle-fixture.zip --expected-report-hash sha256:368122498686b446dc00d496e28fd00a3a97cd64e7c9ea5193a8c648faabb640 --expected-issuer-trust-hash sha256:c06763c8bbe77750c912cde0dca7fdd6ba76c586b020c676fb1244ab9b38c97a --expected-witness-policy-hash sha256:ffbca3acf215a28c9702e84ace9d0bf76de8c97eb1eaca73d6356f911783d033 --expected-checkpoint-hash sha256:57a88cbc9f3605ea1294232360aa2ed8cabb0d89d15f86d6f73d2a7e75363011 --expected-tsa-root-sha256 sha256:a6379e7cecc05faa3cbf076013d745e327bbbaa38c0b9af22469d4701d18aabc
```

`requirements-lock.txt` records the exact package and transitive dependency versions observed in the successful disposable clean-room environment. To recreate that resolved environment while selecting the verifier from the local `dist` directory:

```powershell
python -m pip install --find-links .\dist -r .\requirements-lock.txt
python -m pip check
```

The build backend versions are pinned in `pyproject.toml`. With the `build` frontend available, reproduce the wheel timestamp normalization and build twice for byte comparison:

```powershell
$env:SOURCE_DATE_EPOCH = "1767225600"
python -m build --wheel --outdir .\dist
python .\normalize_wheel.py .\dist\area_one_evidence_verifier-0.1.0-py3-none-any.whl
```

The retained wheel is `dist/area_one_evidence_verifier-0.1.0-py3-none-any.whl`, size `132,341` bytes, SHA-256 `98e01a5d7654266cde12aee0058bf8ca9a8d48ae61aff96320a4be7858812cf6`. Two builds using that epoch were byte-identical. A disposable clean-room installation loaded `evidence_bundle.py` from `site-packages`, passed `pip check`, reported version `0.1.0`, and verified the complete fixture successfully. `dist/SHA256SUMS.txt` records the wheel digest.
## Cross-platform release verification

`release_verification.py` verifies one interpreter and operating-system environment end to end. It checks the retained wheel checksum, compiles all packaged modules, runs all source tests, confirms exact build-tool versions, performs two isolated builds, installs the retained wheel into a fresh virtual environment, compares every installed package with `requirements-lock.txt`, runs `pip check`, confirms the import comes from `site-packages`, and verifies the complete evidence fixture.

`normalize_wheel.py` canonicalizes generated wheels before comparison. It normalizes UTF-8 Python and wheel-metadata line endings, regenerates `RECORD`, fixes ZIP timestamps and permissions, and uses stored ZIP entries to avoid platform-dependent compression output. This resolved the observed Windows-versus-Linux differences in generated `METADATA` line endings and ZIP attributes without changing packaged Python code.

Install the exact build frontend dependencies, then run the local plus Docker Linux matrix:

```powershell
python -m pip install -r .\requirements-build.txt
python .\run_release_matrix.py
```

The completed matrix covers Windows CPython 3.13.14 and Docker Linux CPython 3.11.16, 3.12.14, and 3.13.15. Every target compiled 10 release files, passed all 144 tests, reproduced the same canonical wheel twice, matched all 14 locked packages in a fresh environment, and verified the bundle fixture. The aggregate evidence is `release-matrix-report.json`, with matrix hash `sha256:c7465a6a0fe4221ef921eb490290996dab80625f04d87a573b2c36232026744c`.

The final canonical wheel is `132,341` bytes with SHA-256 `98e01a5d7654266cde12aee0058bf8ca9a8d48ae61aff96320a4be7858812cf6`. Windows Python 3.11 and 3.12 were unavailable, and no macOS environment was tested. The scripts are suitable as CI job entry points, but no repository-root CI workflow is installed here. These local reports are integrity-hashed evidence, not production signatures or proof of publication.