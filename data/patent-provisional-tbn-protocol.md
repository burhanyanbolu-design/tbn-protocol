# UK Provisional Patent Application — TBN Protocol

## TITLE OF INVENTION

Method and System for Independent Cryptographic Certification and Attestation of Autonomous AI Agent Actions

---

## APPLICANT

Hardin Enterprises Ltd (Company No. 17149514)
Trading as Hardin AI Solutions
London, United Kingdom

Inventor: Burhan Yanbolu

---

## FIELD OF THE INVENTION

The present invention relates to a system and method for providing independent, cryptographically verifiable certification and per-action attestation for autonomous artificial intelligence (AI) agents operating in enterprise, government, and regulated environments.

---

## BACKGROUND

AI agents are increasingly deployed to make autonomous decisions in business-critical systems — approving financial transactions, processing healthcare referrals, writing to customer databases, and enforcing compliance policies. These agents operate without real-time human oversight.

Current approaches to AI agent governance rely on:
- Self-reported logging (written by the same system performing the action)
- Internal guardrail tools that cannot prove their own effectiveness to third parties
- Periodic manual audits that cannot verify real-time operational compliance
- System prompts and rules that are not independently verifiable

None of these approaches provide independent, cryptographic, real-time proof that an AI agent operated within its declared operational scope. Regulators (EU AI Act Article 14, UK AI Safety frameworks) increasingly require demonstrable accountability for autonomous AI decisions, but no independent verification infrastructure exists.

---

## SUMMARY OF THE INVENTION

The invention provides a three-phase system for independent AI agent governance:

### Phase 1: Registration and Identity Certification

An AI agent registers with the system, providing:
- A unique agent identifier
- Declared operational scope (what actions it is authorised to perform)
- Declared data boundaries (what data it may access)
- Operator identity (the organisation deploying the agent)

The system issues a cryptographic identity certificate binding the agent to its declared scope.

### Phase 2: Security Challenge Evaluation

Before certification is granted, the system subjects the AI agent to a battery of automated security challenges from an external testing engine. The challenges test whether the agent:

1. **Resists prompt injection** — maintains declared behaviour when presented with adversarial inputs attempting to override its instructions
2. **Resists hallucination** — responds with "unknown" rather than fabricating information when faced with questions outside its knowledge
3. **Respects data boundaries** — refuses to access, return, or reason about data outside its declared scope
4. **Protects sensitive data** — does not leak personally identifiable information, credentials, or internal system details
5. **Observes budget and permission limits** — does not exceed declared resource consumption or access permissions
6. **Follows instructions accurately** — executes its declared purpose without deviation or unintended side effects

The testing is performed externally (from outside the agent's codebase) by sending test inputs and evaluating responses. No code is injected into or modified within the agent.

If the agent passes all critical challenges, a certification attestation is issued. If it fails, the operator is informed of failures and may remediate and resubmit.

### Phase 3: Per-Action Cryptographic Attestation

Once certified, the agent operates in production. For each significant action (decision, write operation, approval, denial, escalation), the agent's operator calls the attestation API.

The system generates a cryptographic receipt containing:
1. Unique receipt identifier
2. Agent identifier
3. Timestamp (UTC)
4. Action performed
5. Decision outcome (allowed/blocked/escalated)
6. Compliance frameworks evaluated
7. Input hash (privacy-preserving reference to the triggering input)
8. Operator identifier

These eight fields are serialised into canonical JSON (sorted keys, no whitespace), and signed using RSA-PSS with SHA-256 (MGF1, maximum salt length) using the system's private signing key.

The resulting signature is attached to the receipt and stored. The system's public key is published and freely available, enabling any party to verify any receipt offline without contacting the system.

---

## KEY NOVEL ASPECTS

1. The combination of pre-deployment security challenge testing with ongoing per-action cryptographic attestation for AI agents, provided by an independent third party

2. A method whereby an external system tests an AI agent's boundary compliance without modifying the agent's code, then issues a verifiable certificate based on the results

3. Per-action cryptographic receipts signed by an independent certificate authority, covering a canonical representation of eight structured fields, verifiable offline by any party holding the published public key

4. The application of certificate authority principles (previously used for website identity via SSL/TLS) to autonomous AI agent identity and action certification

5. A tiered certification system where agents must demonstrate specific security properties (prompt injection resistance, hallucination resistance, data boundary compliance, sensitive data protection, budget/permission compliance, and instruction following) before being granted operational certification

---

## DETAILED DESCRIPTION

### System Architecture

The system comprises:

**Certificate Authority Server:** Hosts the signing private key (RSA 2048-bit), manages agent registrations, stores receipts, exposes verification APIs, and runs the security challenge engine.

**Public Verification Interface:** Exposes the public key and receipt verification endpoints, enabling any party (regulators, auditors, customers, partners) to verify any receipt without authentication.

**Security Challenge Engine:** An automated testing system that sends adversarial inputs to registered agents and evaluates responses against pass/fail criteria for each of the six challenge categories.

**Agent Integration (client-side):** A minimal API call (single HTTP POST with JSON payload) added to the agent's operational code, transmitting action metadata to the Certificate Authority after each significant decision.

### Signing Process

For each attestation request:
1. Eight fields are extracted from the request
2. Fields are serialised as canonical JSON: `json.dumps(fields, sort_keys=True, separators=(',', ':'))`
3. The canonical JSON bytes are signed using RSA-PSS with parameters: hash=SHA-256, MGF=MGF1(SHA-256), salt_length=MAX
4. The signature is encoded as base64 and attached to the receipt
5. The receipt is stored and returned to the caller

### Verification Process (offline-capable)

Any party may verify a receipt by:
1. Obtaining the receipt's eight fields
2. Reconstructing the canonical JSON using the same serialisation
3. Obtaining the system's published public key
4. Verifying the RSA-PSS signature against the canonical JSON bytes
5. A valid signature proves the receipt was issued by the Certificate Authority and has not been modified

No network connection to the Certificate Authority is required for verification.

---

## CLAIMS

1. A computer-implemented method for certifying autonomous AI agents comprising: registering an agent with declared operational scope; subjecting the agent to external security challenge testing; issuing a cryptographic certificate upon successful completion; and subsequently generating per-action cryptographic attestation receipts signed by an independent certificate authority.

2. The method of claim 1, wherein security challenge testing comprises testing from outside the agent's codebase for: prompt injection resistance, hallucination resistance, data boundary compliance, sensitive data protection, budget/permission limit compliance, and instruction following accuracy.

3. The method of claim 1, wherein per-action attestation receipts comprise a canonical JSON serialisation of structured fields signed using RSA-PSS with SHA-256, verifiable offline using a published public key.

4. A system for independent cryptographic attestation of AI agent actions, comprising: a certificate authority server holding a private signing key; a security challenge engine for external agent testing; a registration system for binding agent identifiers to declared operational scopes; and an attestation API that accepts action metadata and returns cryptographically signed receipts.

5. The system of claim 4, wherein the attestation receipts are independently verifiable by any third party without requiring authentication or network access to the system.

---

## DATE OF FIRST DISCLOSURE

The system was first publicly disclosed via publication on the Python Package Index (PyPI) as "tbn-protocol" version 0.1.0 on May 3, 2026.

## PRIORITY DATE SOUGHT

The date of this provisional application filing.

---

## INVENTOR DECLARATION

I, Burhan Yanbolu, declare that I am the inventor of the subject matter described herein and that this application is made in good faith.

Signed: ____________________
Date: ____________________
