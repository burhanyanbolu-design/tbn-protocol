# Area One Post-Closure Strategy Options

Date: 2026-08-17  
Status: **STRATEGY RECORD / NO CLAIM, NO COMMITMENT, NO BUILD AUTHORIZED**

## Purpose

Records the strategic analysis after the Area One falsification: where the mathematics we built actually lands, whether EOG could serve as a classical component supporting quantum computing, what is genuinely open versus closed in the field, and the ranked options with their cheapest decisive tests.

This is analysis only. It asserts no advantage, no novelty and no commercial claim, and authorizes no build.

## What we proved works, stated precisely

Not the quantum mechanism. What is verified is **classical graph machinery**:

- **Exact structural discrimination.** The genuine matching was distinguished from all 119 controls on all three grids: `357` of `357` cases, zero false matches.
- **An independent invariant.** Endpoint-walk profiles `M_d` separated `356/357` using scalar moments alone; `M_2` separated the single exception, `s=3`, `pi=(4,1,0,3,2)`.
- **Canonical labelling.** Endpoint-seeded exact equitable refinement terminates discrete deterministically: `18/24/30` native, `37/49/61` lifted.
- **Verification infrastructure.** 210 tests, exact rational arithmetic, byte-for-byte independent reconstruction, atomic one-shot publication, digest-pinned runtime.

Honest correction to "we proved parts of it work": we proved the **discrimination and verification machinery** works. We did not prove EOG *helps* anything. No application benefit has been demonstrated.

## Does a quantum walk need the pair gate?

No. A discrete-time quantum walk is a coin plus a shift; spatial search adds only an oracle. The pair layer `P` was an optional additive term proposed by Kiro. An optional term carries the burden of proving it changes an observable, and it did not.

## Where the mathematics actually lands

### 1. Homological quantum error-correcting codes — strongest and exact

Candidate 6 built a chain complex with `partial_1 partial_2 = 0` and computed Betti numbers. That **is** the defining structure of CSS and homological codes, not an analogy. Physical qubits sit on 1-cells; `beta_1` counts logical qubits.

Computed: `(beta_0, beta_1, beta_2) = (1, 7, 1)`.

So the native EOG torus is a toric code with `2` logical qubits, and the five overlap seams raise it to `7`. What was filed as an obstruction is, in coding language, the encoding rate. For `s=4`: `65` edges carrying `7` logical qubits, rate about `0.108`, against the toric code's `2/60` or about `0.033` on the same lattice.

**Caveat that probably decides it.** Codes are judged on distance, not rate. An uncapped seam closes a short cycle: `(r+1,0)` returns to `(r,w-1)` in two native steps, implying a **weight-3 logical operator** and therefore distance near `3`. That is poor. Estimate only; the minimum-weight logical operator is directly computable and has not been computed.

Decisive cheap test: compute the code distance. An afternoon. No control-ranking trap exists here because code parameters are what they are.

### 2. Photonic meshes and multi-particle interference — concrete

A `2 x 2` unitary coupling two modes **is** a beamsplitter, and a layer of disjoint beamsplitters on paired modes is an interferometer mesh of the Reck or Clements type. Graph quantum walks are physically realised this way in waveguide arrays.

The interesting asymmetry: for **one** walker the pairing washed out, which is the `95/101` result. For **many** particles, interference depends on the full unitary through permanents, which are sensitive to exactly the structure a single walker averages over. So the pairing could matter with two or more photons where it provably did not with one; Hong-Ou-Mandel is the simplest case.

Caveats: boson sampling demonstrates advantage but solves no useful problem, and the same sensitivity implies noise fragility.

### 3. Matchgates — resemblance only, do not oversell

Disjoint-pair gate layers superficially resemble matchgate circuits, where nearest-neighbour matchgates are classically simulable and matchgates plus SWAP are universal. But matchgates are two-qubit gates with determinant conditions on qubit lines, whereas `P` is a two-level rotation on position states. Structurally suggestive, not the same object.

## EOG as a classical component supporting quantum computing

Quantum computers depend on heavy classical software in the loop, and those are graph problems. The reframe from "EOG is the algorithm" to "EOG is a supporting component" is sound.

| candidate role | fit with our assets | competition |
|---|---|---|
| Surface-code decoding, i.e. minimum-weight perfect matching on a lattice with boundaries | very high, literally matchings on grids | severe: PyMatching, union-find, neural decoders |
| Qubit routing and circuit mapping onto hardware topology | high: isomorphism, canonical labelling, partitions | active but not saturated: Qiskit transpiler, TKET |
| Minor embedding onto fixed hardware graphs for Ising machines and annealers | high, NP-hard, real bottleneck | moderate, weaker incumbents |
| Tensor-network contraction ordering | medium: partitioning, treewidth | severe and mathematically demanding |
| Verification and provenance of quantum claims | already built as ICV Lab | essentially none, no agreed standard |

Where "elastic" might specifically earn its place, as a hypothesis and not a result: hardware quality is non-uniform and drifts as qubits recalibrate. An index over **overlapping regions with adaptive resolution** is a plausible fit for selecting the best-quality subregion for placement, and for decoders facing non-uniform noise.

## What is genuinely open versus closed in the field

**Open, with no rules set in stone:** which physical platform wins; which error-correcting codes; monolithic versus modular architecture; **which applications are actually useful**, the most unsettled question in the field, where most transformation claims are unproven and variational or NISQ approaches are increasingly doubted; and **benchmarking and verification standards**.

**Closed by proof, not consensus:** unitarity, the Born rule, no-cloning, no-signalling; Grover's `sqrt(N)` optimality for unstructured search via the BBBV lower bound; the belief that BQP does not contain NP-complete problems; the threshold theorem.

The practical consequence: engineering and applications are contestable, mathematical limits are not. Advocacy cannot move a proven lower bound. Any proposal that requires beating one should be rejected at the door, including our own.

## On lobbying

Do not lobby physics. Do participate in **standards**, which genuinely accept outside input and where the gap is real.

There is no accepted procedure for independently verifying a quantum advantage claim. Google's 2019 supremacy claim was challenged by IBM and later undercut by improved tensor-network simulation. Claims are made, disputed, and quietly revised.

Plausible venues, current scope to be verified before approach: **NPL** for UK national metrology and quantum measurement; **NQCC**, which runs a UK benchmarking programme and is already in our orbit through SparQ; **IEEE** quantum standards working groups; **ISO/IEC JTC 1** quantum computing work.

Our credential here is rare and hard to fabricate: a pipeline strict enough to falsify its own author's project, with an untouched holdout and receipts. That is the qualification a benchmarking group values, and it does not require a new paradigm.

## Ranked options for a solo, pre-revenue, no-hardware position

1. **Verification, provenance and benchmarking standards.** Uses an asset already built, the gap is real, lowest technical risk.
2. **Minor embedding or routing index.** Best technical fit for proven tooling, testable with no quantum hardware, weaker incumbents.
3. **Homological code parameters.** One cheap decisive calculation; likely negative on distance but definite either way.
4. **A new computing paradigm.** Possible but longest odds, and starting there does not improve them.

## Discipline to apply, learned the hard way

1. **Measure the incumbent first.** For embedding: take a published hardware coupling map and an existing embedder, and measure. An afternoon.
2. **Effect size before infrastructure.** If the margin is a few percent, stop. Our effect was `0.0006`-`0.0024` against a `0.02` gate and we built a 210-test laboratory anyway.
3. **Ask the control question on day one.** Would any competent index do this, or specifically an elastic overlapping one? If any index works, EOG is not the story.
4. **Verify a criterion is satisfiable before freezing it.** We froze one that was unreachable by construction.
5. **Do not let belief precede measurement.** That, not ambition, is what cost six candidates.

## Boundary

Strategy analysis only. No transport effect, separation, advantage, novelty, code quality, embedding benefit, standards role or commercial claim is established. The Area One falsification stands: the genuine matching ranked 95 of 101 on the declared family. The frozen Candidate 1 protocol and the `-0.02` floor are unchanged. No build, simulation, protocol, staging, commit or push is authorized by this document.
