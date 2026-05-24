# TBN Protocol — Technical Explainer

## Understanding TBN: How It Works, Where It Connects, and Why It Matters

---

## Q: What is Salesforce and how does it relate to TBN?

## Salesforce in 60 Seconds

**What Salesforce is:** A cloud database where companies store their customer information — contacts, deals, support tickets, invoices. Everything lives in "records."

**Who uses it:** Banks, insurers, healthcare, telecoms — basically every large enterprise. 150,000+ companies worldwide.

**What "Agentforce" is:** Salesforce's new AI agents that can read and WRITE to those records automatically. That's the problem — AI writing to production customer data with no governance.

---

## Where TBN Fits (The Simple Version)

```
Customer data in Salesforce
        ↑
   AI Agent wants to WRITE
        ↑
   [TBN] — Is this agent trusted? PASS/FAIL
        ↑
   [Shango] — Should this specific write be allowed?
        ↑
   AI Agent makes a decision
```

**TBN's job:** Answer "is this agent allowed to act?" before anything touches the customer's data.

---

## The Lucrative Areas for TBN Beyond Salesforce

| Platform | What AI agents do there | Why they need TBN |
|----------|------------------------|-------------------|
| **Salesforce** | Write to customer records | Governance before CRM writes |
| **Microsoft Copilot** | Act across Office 365, Teams, Dynamics | Verify agent before it sends emails, edits docs |
| **ServiceNow** | Automate IT tickets, change requests | Prevent unauthorised changes to production |
| **SAP** | Process financial transactions, HR records | Stop AI from making wrong payments |
| **HubSpot** | Marketing automation, lead scoring | Govern AI that contacts customers |
| **Epic/Cerner (Health)** | Access patient records | Verify agent before touching NHS data |
| **SCADA/OT (Energy)** | Control power grids, water systems | Block unauthorised agents from CNI |

---

**Your pitch is the same everywhere:** "Before the AI agent acts, TBN verifies it's trusted. PASS or FAIL. Signed. Immutable."

The platform changes. TBN's role doesn't.

---

## Q: How does TBN actually control or check if an agent is allowed? Why can't the people who create the agent just put these parameters into the agent itself? Does the AI agent need an external, independent machine to check it — and is that where TBN comes in?

## Why can't the agent check itself?

**Think of it like this:**

You can't be your own referee. A football player can't decide if their own goal was offside. You need an **independent** referee who has no bias.

Same with AI agents:

- An agent can't verify itself — because if it's compromised, hacked, or misconfigured, it would just say "I'm fine" even when it's not
- The person who built the agent could put rules inside it — but those rules can be overridden, bypassed, or broken by prompt injection, bugs, or attacks
- **You need an external, independent machine that checks the agent from the outside**

**That's TBN.**

---

## The Simple Analogy

| Real World | AI World |
|-----------|----------|
| A passport office verifies your identity | TBN verifies the agent's identity |
| You can't print your own passport | The agent can't verify itself |
| The border guard checks your passport independently | The system checks TBN's verification independently |
| If your passport is expired → you're denied entry | If TBN says FAIL → agent is denied execution |

---

## Why "just putting rules in the agent" doesn't work

| Approach | Problem |
|----------|---------|
| "I'll put safety rules in the agent's prompt" | Prompt injection can override them |
| "I'll code limits into the agent" | A bug or hack can bypass them |
| "I'll trust the developer who built it" | The developer might make mistakes, or leave the company |
| "The agent will check itself" | A compromised agent will lie about its own state |

**The only reliable answer:** An independent external system that the agent cannot control, override, or lie to.

---

## How TBN actually does the check

1. Agent wants to act → sends its `agent_id` to TBN
2. TBN looks up: Is this agent registered? Is its certification valid? Is it within its declared scope?
3. TBN returns: **PASS** (proceed) or **FAIL** (blocked)
4. TBN **signs** the answer with a cryptographic key that nobody can fake
5. Anyone can verify that signature independently — the agent can't forge it

**The agent never touches TBN's decision.** It's like a locked door — the agent asks to come in, TBN decides yes or no, and the agent has no power to change that decision.

---

## One sentence to remember:

> "TBN is the independent referee that AI agents cannot override, bribe, or lie to."

---

## Q: So TBN is not actually giving people our bots to operate their systems. We're providing them with an independent layer — a gate — for their agents to interact with, which guards and controls what information gets released through the API?

## What TBN is NOT:

❌ We don't give people our bots to run their systems
❌ We don't replace their agents
❌ We don't operate inside their code

## What TBN IS:

✅ An **independent layer** that sits between their agents and their systems
✅ A **gate** — their agent talks to TBN first, TBN says yes or no
✅ An **API guard** — controls what information gets released and what actions get allowed
✅ A **referee** — we don't play the game, we enforce the rules

---

## Think of it like this:

**Their company:**
- They build their own agents ← their code, their business
- They run their own systems ← Salesforce, databases, whatever

**TBN (us):**
- We sit in the middle as the checkpoint
- Their agent asks TBN: "Can I do this?"
- TBN answers: PASS or FAIL
- We never touch their data, their code, or their operations

---

## The business model in one line:

> "Companies keep their agents, their code, their systems. They pay us to be the independent trust layer that guards the gate."

---

That's why it's a **protocol** (like HTTPS) — not a product you install and replace things with. Everyone keeps their own stuff. They just add TBN as the verification layer.

---

## Q: Just like websites have layers of security (HTTPS, firewalls, authentication), what other security measures can be adopted as an AI protocol? What are the equivalent layers for AI agents?

## Website Security Layers vs AI Agent Security Layers

| Layer | Website (what exists today) | AI Agents (what's needed) | Who does it? |
|-------|---------------------------|--------------------------|-------------|
| **Identity** | SSL Certificate (proves website is real) | Agent Certificate (proves agent is real) | **TBN ✅** |
| **Authentication** | Login (username/password) | Agent ID verification | **TBN ✅** |
| **Authorization** | "Can this user access this page?" | "Can this agent do this action?" | **TBN ✅** |
| **Firewall** | Blocks bad traffic before it reaches server | Blocks bad agents before they reach system | **TBN ✅** |
| **Rate limiting** | "Max 100 requests per minute" | "Max 50 writes per hour per agent" | **Shango (Ishaan)** |
| **Content filtering** | WAF blocks SQL injection | Blocks prompt injection, bad data | **Shango** |
| **Audit logging** | Server logs every request | Immutable log of every agent decision | **TBN + BlackVault** |
| **Evidence/compliance** | GDPR cookie consent, privacy policy | EU AI Act proof, regulatory evidence | **EVIDE (Emanuel)** |
| **Monitoring** | Uptime monitoring, alerts | Agent behaviour monitoring, drift detection | **Future layer** |
| **Encryption** | HTTPS encrypts data in transit | Signed attestations (RSA-PSS) | **TBN ✅** |

---

## What TBN Already Covers (Layer 0):

✅ Identity — "Is this agent who it says it is?"
✅ Authentication — "Is this agent registered?"
✅ Authorization — "Is this agent certified to act?"
✅ Cryptographic proof — "Here's the signed evidence"
✅ Revocation — "This agent is no longer trusted" (instant)

---

## What Other Layers Could Be Added (Future TBN Features or Partners):

| Security Layer | What it does | Status |
|---------------|-------------|--------|
| **Behaviour monitoring** | Detect if an agent starts acting differently from normal | Could build |
| **Anomaly detection** | "This agent usually makes 10 calls/hour, now it's making 10,000" | Could build |
| **Agent reputation score** | Trust score that goes up/down based on history | Already in TBN (trust score) |
| **Cross-agent verification** | Agent A verifies Agent B before they communicate | Already in TBN (handshake) |
| **Budget enforcement** | "This agent can only spend £X or use Y tokens" | Already in TBN |
| **Geo-fencing** | "This agent can only operate in UK systems" | Could add |
| **Time-based access** | "This agent only works during business hours" | Could add |
| **Data classification** | "This agent can access public data but not PII" | Shango does this |

---

## The Key Insight:

Websites took 20 years to build all these security layers (SSL came in 1995, WAFs in 2005, zero-trust in 2020).

**AI agents need all of this NOW — but it doesn't exist yet.** TBN is building the first layer (identity + trust). The rest will follow. You're early.
