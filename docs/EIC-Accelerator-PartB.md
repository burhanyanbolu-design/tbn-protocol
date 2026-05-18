# TBN Protocol — Trust Infrastructure for Autonomous AI Agents

## List of Participants

| Participant | Organisation Name | Country |
|-------------|------------------|---------|
| 1 (Coordinator) | Hardin Enterprises Ltd | United Kingdom |

---

## 1. Technology

### Novelty and breakthrough nature

**Is your innovation deep tech in nature stemming from cutting-edge scientific or technological advances?**

Yes. TBN Protocol combines three cryptographic and systems-level innovations that do not exist together in any current product:

1. **Cryptographic Runtime Attestation** — SHA-256 fingerprinting of AI agent identity (endpoint + system prompt + model configuration) at certification time, with runtime verification that the deployed agent matches the certified state. This is analogous to code signing in software distribution, but applied to AI agents whose behaviour is defined by prompts and configurations rather than compiled binaries.

2. **Tamper-Evident Verification Responses** — Each verification call returns a unique `verification_id` and a `response_hash` (SHA-256 of the canonical JSON response). This allows downstream governance systems to store trust-state snapshots as cryptographically verifiable evidence — proving the verification result has not been altered since issuance.

3. **Composite Trust-State Verification** — A single API call aggregates five independent checks (certification status, fingerprint attestation, budget compliance, policy drift score, and operational bounds) into one atomic response. No existing solution provides this composite view.

**Does it represent a significant improvement in cost or performance compared to existing solutions?**

Current AI governance approaches rely on:
- Manual audits (cost: £10,000-50,000 per assessment, weeks of delay)
- One-time certifications that become stale immediately after issuance
- Platform-specific controls that don't interoperate across systems

TBN provides continuous, automated verification in <100ms per call, at a cost of fractions of a penny per verification. This represents a 1000x improvement in both speed and cost compared to manual governance processes.

**Empirical data demonstrating novelty:**

- First external integration partner (CLARIXO/TGTRACING LLC) successfully integrated and confirmed all three verification paths in production (May 2026):
  - Unknown agent → correctly returns UNKNOWN / within_bounds: false
  - Certified agent → returns VALID / STANDARD / within_bounds: true
  - Fingerprint attestation → correctly returns MATCHED or MISMATCH
- No competing product offers runtime fingerprint attestation combined with budget enforcement and compliance drift scoring in a single protocol
- Published on PyPI (pip install tbn-protocol) — the only open-source AI agent trust protocol available as a package

### Technology Readiness Level (TRL)

**Evidence of TRL 5+ validation:**

TBN Protocol has completed TRL 7 (system prototype demonstration in operational environment):

- **Live production API** running on AWS infrastructure (https://tbn.hardinai.co.uk) since May 2026
- **First external system integration** — CLARIXO (an AI governance and responsibility attribution system) is consuming the /api/verify/full endpoint in their production environment
- **End-to-end verification confirmed** — all three trust-state paths (unknown, certified, attestation) validated by an independent external partner
- **SDK published** on PyPI (pip install tbn-protocol v0.1.5) — installable and usable by any developer
- **7 governance features** operational: security certification, fingerprint attestation, identity/config hash split, continuous monitoring, budget enforcement, compliance drift, webhook notifications
- **Partner onboarding infrastructure** — registration portal, terms acceptance, API key management, and real-time monitoring dashboard all operational

### IP Protection and Strategy

**Current IP position:**

- **Open Source (AGPL-3.0):** The protocol is published under AGPL-3.0, which requires any company using or modifying the code to open-source their modifications. This creates a strong incentive for commercial users to purchase a commercial licence instead.
- **Commercial Licensing:** Companies that want to use TBN without open-sourcing their own code must purchase a commercial licence from Hardin Enterprises Ltd. This dual-licensing model (used successfully by MongoDB, Redis, Elastic) generates revenue while maintaining open-source community growth.
- **Trade Secrets:** The operational infrastructure, partner relationships, certified bot registry, and governance data are proprietary and not included in the open-source release.
- **First-Mover Advantage:** TBN is the first protocol to combine cryptographic attestation + budget enforcement + compliance drift in a single standard. The network effect (more certified agents = more valuable registry) creates a defensible moat.
- **Patent Strategy:** We plan to file a patent on the composite trust-state verification method (single-call aggregation of certification, attestation, budget, policy, and bounds into a tamper-evident response) using EIC funding. Estimated filing: Q1 2027.
- **Freedom to Operate:** No existing patents cover the specific combination of AI agent fingerprint attestation with budget enforcement and compliance drift scoring. Prior art search confirms clear FTO.

---

## 2. Market

### Market Opportunity

**Total market:**

The AI agent governance market is driven by three converging forces:

1. **EU AI Act enforcement (2026):** Articles 9, 14, and 61 mandate risk management, human oversight, and post-market monitoring for high-risk AI systems. Every company deploying AI agents in the EU must implement governance controls. Estimated compliance market: €2-4B.

2. **AI agent deployment explosion:** LangChain (90K+ GitHub stars), CrewAI, AutoGPT, and enterprise copilots are entering production. Gartner estimates 250,000+ companies will deploy AI agents by 2027. Each needs governance infrastructure.

3. **Runaway cost problem:** AI agents consuming LLM APIs can generate thousands of pounds in unexpected costs within hours. Budget enforcement alone is a €1B+ pain point.

**Total Addressable Market:** €10B+ (trust infrastructure for the AI agent economy)
**Serviceable Addressable Market:** €2B (EU companies requiring AI Act compliance for agent deployments)
**Serviceable Obtainable Market (3 years):** €5-10M (500-1000 enterprise customers)

**Comparable exits:** Auth0 ($6.5B), HashiCorp ($5.1B), Snyk ($8.5B) — all infrastructure-layer companies.

### Go-to-market and commercialisation strategy

**Phase 1 (Now - Month 6): Developer adoption**
- Open-source SDK on PyPI drives awareness and adoption
- Integration partners (CLARIXO model) embed TBN in their products — their customers become our customers
- Content marketing: technical blog posts, conference talks on AI governance

**Phase 2 (Month 6-12): Enterprise sales**
- EU AI Act compliance positioning — "Deploy agents compliantly in one API call"
- Target: fintech, healthtech, and government contractors deploying AI agents
- Channel: compliance consultants recommending TBN as part of AI Act readiness

**Phase 3 (Month 12-24): Platform standard**
- Become the default trust layer that orchestration platforms (LangChain, CrewAI) integrate
- Network effects: more certified agents = more valuable verification = more integrations

### Customer value proposition and partnerships

**Value proposition:** "Certify, monitor, and enforce boundaries on your AI agents — one API call, continuous assurance, EU AI Act compliant."

**Current partner:** CLARIXO/TGTRACING LLC (AI governance system, Cambodia) — live integration consuming verify endpoint in production. Their customers will need TBN certification for their agents.

**Target customers:**
- Enterprise AI teams deploying agents in regulated environments
- AI platform companies needing governance features for their customers
- Compliance teams blocking AI deployment due to unquantified risk

**Why they adopt:** Legal/compliance teams currently block AI agent deployment because they cannot prove agents are safe, within budget, and unchanged since testing. TBN removes that blocker with automated, continuous verification.

---

## 3. Team, Financial Needs, Implementation

### Team capability

**Key team members:**

**Burhan Yanbolu — Founder & CEO (Technical)**
- Full-stack developer with 5+ years experience
- Built entire TBN Protocol solo (7 features, production API, SDK, partner integration)
- Technical skills: Python, Flask, cryptography (RSA-2048, AES-256-GCM, SHA-256), API design, cloud infrastructure (AWS), PostgreSQL
- Previously built: Hardin AI Search (143 users), LGMD Research Agent, SmartTrader AI
- Demonstrated execution speed: shipped 5 versions to PyPI in a single day

**Company governance:** Sole director of Hardin Enterprises Ltd (UK). All technical and business decisions made by founder. Advisory input from integration partners.

**Critical gaps and plan to fill:**

| Gap | Priority | Plan |
|-----|----------|------|
| Enterprise sales / BD | High | Hire with EIC funding (Month 1-3) |
| Distributed systems engineer | High | Hire with EIC funding (Month 3-6) |
| Security/compliance specialist | Medium | Hire with EIC funding (Month 6-9) |
| Gender balance | Noted | Active commitment to diverse hiring — will target 40%+ female candidates for all roles |

### Risk level of investment and leverage effect

**Early traction:**
- First integration partner (CLARIXO) live in production — validates market demand
- Applied to Y Combinator Summer 2026 — pending decision
- LinkedIn announcement received public validation from integration partner
- Inbound interest from multiple companies exploring AI governance

**Financing requirement:**

We are requesting **€2.5M grant** (UK applicants are eligible for grant only) to:

| Category | Amount | Purpose |
|----------|--------|---------|
| Engineering team (3 hires) | €1.2M | Scale platform, enterprise features, SOC2 certification |
| Go-to-market | €600K | Enterprise sales hire, EU AI Act compliance marketing, conferences |
| Infrastructure | €300K | Multi-region deployment, 99.99% SLA, security audits |
| Legal/IP | €200K | Patent filing, regulatory compliance certification |
| Operations | €200K | Office, admin, accounting, travel |

**Why EIC funding is needed:**

1. **Patient capital requirement:** AI governance infrastructure requires 12-18 months of development before enterprise customers will pay significant amounts. VCs want faster returns.
2. **Trust paradox:** A trust infrastructure company needs to demonstrate stability and longevity — VC-funded "move fast and break things" culture is incompatible with our market positioning.
3. **European sovereignty:** EU companies need a European-based trust standard for AI agents, not a US-controlled proprietary solution. EIC funding enables us to build this as a European standard.
4. **Market timing:** EU AI Act enforcement creates a narrow window (2026-2027) where companies must adopt governance solutions. We need to scale before US competitors (who have VC funding) establish dominance in the EU market.

**Why market actors will not fund the full amount:**
- Pre-revenue stage — too early for most VCs
- Infrastructure/protocol companies have long payback periods (Auth0 took 8 years to exit)
- Solo founder without prior exits — VCs typically require co-founders
- The €2.5M grant removes the need for dilutive VC funding at this critical early stage, allowing us to reach revenue and prove the model before raising equity

**Milestones:**
- Month 6: 50 paying customers, SOC2 certification initiated
- Month 12: €100K ARR, 3+ integration partners, patent filed
- Month 18: €350K ARR, EU AI Act compliance certification
- Month 24: €1M ARR, Series A ready (if needed)
