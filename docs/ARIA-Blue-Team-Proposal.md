# TBN Protocol — Formally Verifiable Trust Identity Infrastructure for AI Agent Cybersecurity

**ARIA Safeguarded AI — Cybersecurity Technical Area 2**
**Track 1: Blue Team Application**

**Applicant:** Hardin Enterprises Ltd (Company No. 17149514)
**Lead:** Burhan Yanbolu, Founder & CEO
**Contact:** burhan@hardinai.co.uk
**Date:** May 2026

---

## 1. Project Summary

We propose to build a production-grade, formally verified trust identity layer for AI agent systems operating in security-critical cyber environments.

TBN Protocol already provides cryptographically signed agent verification in production. This project will extend it with machine-checked proofs of its core security properties, demonstrating that the trust verification logic is provably correct under clearly stated threat models.

**Target system:** A trust identity verification service whose security-critical properties (authentication correctness, revocation completeness, non-forgery of attestations) are backed by machine-checked formal proofs.

**Key security properties to verify:**

- **Authentication soundness:** An agent receiving PASS has a valid, non-revoked certification issued by the authority
- **Revocation completeness:** A revoked agent cannot receive PASS under any input sequence
- **Non-forgery:** No party without the private key can produce a valid TBN signature
- **Determinism:** Identical inputs always produce identical verification outcomes
- **Audit integrity:** The hash-chained governance ledger is tamper-evident — any modification is detectable

---

## 2. Technical Approach

### 2.1 Current System (Production)

TBN Protocol is live at tbn.hardinai.co.uk, serving real verification requests. Current architecture:

- **Verification endpoint:** Accepts agent ID + action context, returns PASS/WARN/FAIL with RSA-PSS-SHA256 signature
- **Certification authority:** Multi-level (L1–L5) with real-time validity and instant revocation
- **Governance ledger:** Hash-chained (SHA-256) audit trail of all trust events
- **Interoperability:** Confirmed third-party boundary verification (DigiEmu, May 2026)
- **Stack:** Python/Flask, RSA-2048, deployed on AWS

### 2.2 Proposed Formal Verification Work

**Phase 1 (Months 1–3): Specification and Modelling**

- Define formal threat model: adversarial agents, compromised networks, replay attacks, timing attacks on revocation
- Specify security properties as formal propositions in Lean 4 or Coq
- Model the verification state machine (registration → certification → verification → revocation)
- Define the trust boundary formally: what constitutes a valid PASS, WARN, FAIL transition

**Phase 2 (Months 4–8): Proof Development**

- Machine-check authentication soundness: prove that PASS implies valid certification under the threat model
- Prove revocation completeness: demonstrate no execution path allows PASS after revocation
- Prove signature non-forgery (reduction to RSA-PSS security assumptions)
- Prove hash-chain integrity: any ledger modification breaks the chain
- Use AI-assisted proof search (LLM-guided tactic generation) to accelerate proof development

**Phase 3 (Months 9–12): Verified Implementation**

- Extract verified implementation from proofs (or prove equivalence with production code)
- Deploy formally verified verification logic alongside production system
- Produce machine-checkable compliance certificates for each security property
- Document assumptions, threat model boundaries, and proof coverage

### 2.3 AI-Enabled Formal Methods

We will use AI to accelerate formal verification:

- **LLM-guided proof search:** Using large language models to suggest proof tactics and lemma structures
- **Automated invariant discovery:** AI-assisted identification of loop invariants and inductive hypotheses
- **Counterexample generation:** AI-driven fuzzing to find edge cases before formal proof attempts
- **Specification refinement:** Using AI to translate natural-language security requirements into formal specifications

This directly addresses ARIA's question: "what are the most ambitious, security-critical systems we can verify today?" — we propose verifying a live, production trust infrastructure that AI agents depend on for security-critical decisions.

---

## 3. Threat Model

**Adversary capabilities:**
- Can register arbitrary agents and attempt verification
- Can observe network traffic (passive eavesdropping)
- Can replay captured verification responses
- Can attempt to forge signatures without the private key
- Can attempt to use revoked credentials before propagation completes
- Cannot compromise the TBN server's private key storage (assumption)

**Security goals under this model:**
- No forged PASS attestation is possible without the private key
- Revocation takes effect within one verification cycle (no window of vulnerability)
- The governance ledger cannot be modified without detection
- Verification is deterministic — same inputs always produce same outputs

---

## 4. Deployment and Adoption Path

TBN Protocol is already deployed and serving real requests. This is not a research prototype — it is production infrastructure with confirmed third-party integrations.

**Current deployment:**
- Live at tbn.hardinai.co.uk (AWS, Gunicorn, nginx)
- Published on PyPI (pip install tbn-protocol)
- Open-source (AGPL-3.0) with commercial licensing
- Confirmed interoperability with external systems (DigiEmu boundary verification)
- Active partner integrations (Boomi enterprise connector, Shango governance layer, CLARIXO responsibility attribution)

**Post-verification adoption plan:**
- Publish formally verified TBN core as open-source reference implementation
- Offer verified trust verification as a service for critical infrastructure operators
- Provide machine-checkable compliance certificates to regulated industries (financial services, healthcare, defence)
- Upstream verified components to the open-source TBN package
- Engage with UK AI Safety Institute and EU AI Act compliance bodies

**Commercial viability:** TBN already has paying interest from enterprise governance platforms. Formal verification adds a unique differentiator — no other trust identity system for AI agents offers machine-checked security proofs.

---

## 5. Team

**Burhan Yanbolu — Lead, System Architecture & Deployment**
- Founder & CEO, Hardin Enterprises Ltd
- Built and deployed TBN Protocol from concept to production
- Designed the cryptographic verification model, governance engine, and certification framework
- Experience: full-stack engineering, cloud infrastructure (AWS), cryptographic systems
- Availability: Full-time on this project

**Cem Aslan — Automation & Industrial AI**
- Automation Director, Hardin AI Solutions
- Industrial AI and smart manufacturing architect
- Experience: automotive/EV manufacturing systems, robotics, MES
- Contribution: real-world deployment scenarios, industrial threat modelling

**Sukumar Srinivasan — Cloud Services & Infrastructure**
- Cloud Services Director, Hardin AI Solutions
- Ranked amongst top AI/ML/Cloud training providers globally (EkasCloud)
- Experience: AWS architecture, distributed systems, cloud security
- Contribution: infrastructure hardening, distributed deployment, scalability

**Seeking (via ARIA teaming):** Formal methods researcher with Lean 4 or Coq expertise to lead proof development. We bring the production system and security engineering — we need a collaborator who brings mathematical rigour.

**Division of responsibilities:**
- System design & specification: Burhan Yanbolu
- Formal specification & proof: [Formal methods collaborator — TBC via teaming]
- AI workflow design (LLM-guided proof): Burhan Yanbolu + collaborator
- Infrastructure & deployment: Sukumar Srinivasan
- Industrial validation & threat scenarios: Cem Aslan
- Commercialisation & adoption: Burhan Yanbolu

---

## 6. Why This Team, This Target

**Why TBN is the right target for formal verification:**
- It is already production-grade — not a toy or prototype
- Its security properties are clearly definable and provable
- It sits at a critical boundary — if trust verification is wrong, all downstream security fails
- It has real users and integrations — verification results matter immediately
- The system is small enough to verify completely, yet important enough to matter

**Why this team:**
- We built the system — we understand every design decision and edge case
- We have production deployment experience — we know what breaks in the real world
- We are commercially motivated — formal verification directly enables enterprise sales
- We learn fast — TBN went from concept to production with confirmed interoperability in under 6 months

**Evidence of execution:**
- TBN Protocol: live, serving requests, cryptographically signed responses
- Confirmed third-party interoperability proof (May 2026)
- Published PyPI package
- Active enterprise partner pipeline
- Open-source codebase

---

**References**

1. TBN Protocol — https://tbn.hardinai.co.uk
2. GitHub — https://github.com/burhanyanbolu-design/tbn-protocol
3. PyPI — https://pypi.org/project/tbn-protocol/
4. ARIA Safeguarded AI Programme Thesis v2 — https://aria.org.uk/media/ikrkutfk/safeguarded-ai-programme-thesis-v2.pdf
