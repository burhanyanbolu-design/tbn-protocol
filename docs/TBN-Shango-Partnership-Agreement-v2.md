# TBN Protocol × Shango MID — Partnership Agreement

**Version:** 2.0 (Amended)  
**Date:** 22 May 2026  
**Effective Date:** 26 May 2026  

---

## Parties

**Party A — TBN Protocol**  
Hardin Enterprises Ltd  
Company No. 17149514 (England & Wales)  
Represented by: Burhan Yanbolu, CEO  
Email: burhan@hardinai.co.uk  
Product: TBN Protocol (Layer 0 — Trust Verification)  

**Party B — Shango**  
Ishaan Ghosh, Founder  
Trading as: Shango  
Email: [Ishaan to confirm]  
Product: Shango MID (Layers 1–8 — Write Governance)  

---

## 1. Purpose

This agreement establishes a commercial partnership between TBN Protocol and Shango to jointly deliver AI governance solutions to enterprise customers. TBN provides Layer 0 (agent trust verification) and Shango provides Layers 1–8 (write governance and audit).

---

## 2. Joint Product

**Product Name:** TBN + Shango — Complete AI Governance Stack  

**What it does:** Real-time governance of AI agent writes, combining cryptographic trust verification (TBN) with 8-layer write boundary enforcement (Shango), producing an immutable audit trail for regulatory compliance.

**Proven capability:** 10,000 AI writes governed in 59 seconds, with cryptographic signatures on every decision.

---

## 3. Customer-Facing Pricing

### GBP Pricing

| Tier | Monthly (GBP) | Included |
|------|---------------|----------|
| Proof of Concept | £5,000 | Up to 10K writes, 50 agents, 90-day term |
| Professional | £12,000 | Up to 100K writes, 200 agents, SLA |
| Enterprise | £25,000 | Up to 1M writes, 1,000 agents, dedicated support |
| Enterprise+ | £50,000+ | Unlimited, custom SLA, on-prem option |

### USD Pricing (for US/international customers)

| Tier | Monthly (USD) | Included |
|------|---------------|----------|
| Proof of Concept | $6,500 | Up to 10K writes, 50 agents, 90-day term |
| Professional | $15,500 | Up to 100K writes, 200 agents, SLA |
| Enterprise | $32,500 | Up to 1M writes, 1,000 agents, dedicated support |
| Enterprise+ | $65,000+ | Unlimited, custom SLA, on-prem option |

**Currency:** Invoice in the customer's preferred currency (GBP or USD). Foreign exchange risk sits with the invoicing party.

---

## 4. Revenue Split

### Scenario A — Burhan sources the customer

| Party | Share |
|-------|-------|
| TBN (Burhan) | 70% |
| Shango (Ishaan) | 30% |

### Scenario B — Ishaan sources the customer

| Party | Share |
|-------|-------|
| Shango (Ishaan) | 70% |
| TBN (Burhan) | 30% |

### Scenario C — Joint sale (both involved in sourcing)

| Party | Share |
|-------|-------|
| TBN (Burhan) | 50% |
| Shango (Ishaan) | 50% |

**"Sourcing" defined as:** The party who initiated first contact with the customer and secured the commercial engagement.

**Payment terms:** Revenue share paid within 14 days of customer payment receipt. The invoicing party (whoever invoices the customer) pays the other party their share.

---

## 5. Minimum Payments & Pre-Revenue Period

**Pre-revenue period:** From the effective date until combined Monthly Recurring Revenue (MRR) reaches £20,000.

**During pre-revenue period:**
- No minimum payments from either party
- No fixed API fees from Shango to TBN
- TBN API access provided at no cost to Shango
- Pure revenue share model applies from first customer payment

**Post £20K MRR:**
- Both parties will revisit and agree minimum commitments
- Any minimums to be agreed in writing by both parties before taking effect

---

## 6. Service Level Agreements (Mutual)

### TBN Protocol (Layer 0)

| Metric | Target |
|--------|--------|
| API uptime | 99.5% monthly |
| Verification latency (cached) | <1ms p99 |
| Verification latency (cold) | <500ms p99 |
| Batch verification (1,000 agents) | <300ms |

### Shango MID (Layers 1–8)

| Metric | Target |
|--------|--------|
| Decision pipeline availability | 99.5% monthly |
| Per-record latency | <100ms p99 |
| Audit trail write | Synchronous, append-only |

### Fallback Clause

If TBN API is unavailable for more than 4 consecutive hours, Shango may activate local RSA-PSS signing (fallback mode) to maintain customer service continuity. Fallback events are logged and reported to TBN within 24 hours.

---

## 7. Responsibilities

### TBN Protocol (Burhan)
- Maintain and operate TBN Layer 0 API (https://tbn.hardinai.co.uk)
- Provide API keys and onboarding for joint customers
- Lead commercial/sales conversations
- Maintain 99.5% uptime SLA
- Invoice customers (when Burhan sources the deal)

### Shango (Ishaan)
- Maintain and operate Shango Layers 1–8
- Technical integration with customer Salesforce orgs
- Deliver governance configuration and tuning
- Maintain 99.5% decision pipeline SLA
- Invoice customers (when Ishaan sources the deal)

---

## 8. Intellectual Property

- Each party retains full ownership of their own IP
- TBN Protocol IP belongs exclusively to Hardin Enterprises Ltd
- Shango MID IP (including BlackVault) belongs exclusively to Ishaan Ghosh / Shango
- No IP is transferred, licensed, or shared under this agreement
- Joint marketing materials are co-owned

---

## 9. Non-Compete (Layer-Scoped)

- TBN will not build write governance layers (Layers 1–8) that compete with Shango
- Shango will not build a trust verification protocol (Layer 0) that competes with TBN
- Both parties are free to partner with other companies in non-competing layers
- This non-compete applies for the duration of this agreement plus 12 months after termination

---

## 10. Exclusivity

**Non-exclusive.** Both parties may:
- Sell their own products independently
- Partner with other companies
- Serve customers without involving the other party

Neither party is obligated to involve the other in every deal.

---

## 11. Data & Privacy

- Customer data remains in the customer's environment
- TBN receives only `agent_id` for verification — no customer PII
- Shango processes writes within the customer's Salesforce org
- Both parties comply with GDPR and applicable data protection laws
- Neither party shares customer data with third parties without written consent

---

## 12. Term & Termination

- **Start date:** 26 May 2026
- **Initial term:** 12 months (rolling)
- **Termination:** Either party may terminate with 30 days written notice
- **Post-termination:** Existing customer contracts continue to be serviced until their natural end. Revenue share continues for active customers acquired during the partnership.

---

## 13. Future Partners

If additional partners (e.g. EVIDE, Constitutional Memory, or others) formally join the commercial arrangement, a new agreement will be drafted with all parties. This agreement between TBN and Shango remains valid and unaffected until explicitly superseded.

---

## 14. Dispute Resolution

- Good faith negotiation first (14 days)
- If unresolved: mediation via Centre for Effective Dispute Resolution (CEDR), London
- Governing law: England & Wales

---

## 15. Timeline

| Milestone | Date | Owner |
|-----------|------|-------|
| Agreement signed | 26 May 2026 | Both |
| TBN live API integrated in Shango | 26 May 2026 | Ishaan |
| Joint 1K live proof | 28 May 2026 | Both |
| 100K proof on Enterprise+ sandbox | 2 June 2026 | Ishaan |
| Joint public announcement | 1 June 2026 | Both |
| First customer outreach | 2 June 2026 | Both |
| First POC signed | 30 June 2026 | Both |

---

## 16. Signatures

| | Party A — TBN Protocol | Party B — Shango |
|---|---|---|
| **Name** | Burhan Yanbolu | Ishaan Ghosh |
| **Role** | CEO, Hardin Enterprises Ltd | Founder, Shango |
| **Company No.** | 17149514 | [Ishaan to provide] |
| **Date** | ___/___/2026 | ___/___/2026 |
| **Signature** | ___________________ | ___________________ |

---

## Amendments Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 22 May 2026 | Initial proposal |
| 2.0 | 22 May 2026 | Accepted Ishaan's 4 amendments: (1) No minimum payments pre-revenue, pure rev-share until £20K MRR; (2) Removed Greg/BlackVault 10% — split is now 70/30; (3) Added USD pricing; (4) Added mutual SLA + fallback clause |

---

*This agreement is between Hardin Enterprises Ltd (Company No. 17149514) and Ishaan Ghosh (Shango). It does not constitute employment, equity transfer, or joint venture formation. Both parties remain independent entities.*
