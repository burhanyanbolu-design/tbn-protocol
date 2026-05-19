# TBN Protocol — Project Status
## Last Updated: May 19, 2026

---

## CURRENT PRIORITIES

### Immediate (This Week)
1. **SEO UPDATE** — Update landing page (api/templates/dashboard_new.html) with keywords: "AI agent certification EU AI Act", "AI agent governance compliance", "AI agent attestation verification", "runtime governance", "AI agent trust verification API"
2. **Ishaan/Shango call** — Tomorrow. He wants TBN as "Layer 0" in his Salesforce write-governance pipeline. T-Systems (German enterprise) deal. Keep it high-level, T-Systems gets their own Enterprise key directly.
3. **Authbound meeting** — Tuesday 11am UK time. Turkish founder in Finland. EU Digital Identity Wallet + TBN = verified human + verified agent.
4. **Bruno's schema** — DigiEmu Core sending canonical snapshot structure this week for TBN ↔ DigiEmu boundary test.

### Pending (No Action Needed Yet)
- YC Summer 2026 decision — application under review
- EIC Accelerator — draft proposal done, deadline December 2026
- TfL Innovation — RankWatch submitted, waiting for response (2-3 weeks)

---

## LIVE INTEGRATIONS

| Partner | System | Status | Key |
|---------|--------|--------|-----|
| TGTRACING LLC (Stone Shi) | CLARIXO — responsibility attribution | LIVE | tbn_live_ggssrZqCaiOWIBgB187tTw9Em7liGJ3D |
| Baumgartner Digital (Bruno) | DigiEmu Core — decision state reconstruction | CONFIRMED, schema this week | Not yet issued |
| VectorPeak (Vallikat) | Causeway — admissibility | Ecosystem, not integrated yet | Not yet issued |
| Shango MID (Ishaan Ghosh) | Write governance for Salesforce | INCOMING — call tomorrow | Not yet issued |

---

## WHAT'S DEPLOYED (Live at tbn.hardinai.co.uk)

- Dashboard: /
- Live Demo: /demo
- Public Verification Registry: /verify (no API key needed)
- Partner Registration: /partners
- Partner Monitor (admin): /admin/partners?key=hardin-admin-2026-secret
- Health: /health
- API Stats: /api/stats
- API Bots: /api/bots
- Verify Full (protected): POST /api/verify/full
- Verify Public: POST /api/verify/public
- Signing Public Key: GET /api/signing/public-key

---

## RECENT UPGRADES (May 17-18)

1. ✅ /api/verify/full — Full trust-state verification endpoint (for partners)
2. ✅ /api/verify/public — Public verification registry (no key needed)
3. ✅ Certification scoring (0-100)
4. ✅ Mandatory Failure Conditions (6 MFCs)
5. ✅ EU AI Act framework mapping
6. ✅ RSA signing module (api/tbn_signing.py)
7. ✅ Partner registration page with T&Cs
8. ✅ Partner monitoring dashboard (admin-locked)
9. ✅ Email notifications on partner signup (IONOS SMTP)
10. ✅ Certification persistence across restarts
11. ✅ SVG assets (LinkedIn banner, certified badge, powered-by badge)

---

## STILL TODO

- [ ] SEO keywords on landing page
- [ ] RSA signature on verify/full responses (Bruno requested provenance proof)
- [ ] German language page (optional, for EU market)
- [ ] Blog/docs section on site
- [ ] Pitch deck (10 slides) for EIC
- [ ] 3-minute video for EIC
- [ ] First paying customer

---

## KEY FILES

- Server: server.py
- Routes: api/routes.py
- State: api/state.py
- Access Control: api/access_control.py
- Security Challenges: api/security_challenge.py
- Budget Enforcement: api/budget_enforcement.py
- Compliance Drift: api/compliance_drift.py
- Webhooks: api/webhooks.py
- Governance Engine: api/governance_engine.py
- Landing Page: api/templates/dashboard_new.html
- Public Verify Page: api/templates/verify_public.html
- Partner Registration: api/templates/partner_register.html
- Partner Monitor: api/templates/partner_monitor.html
- Founders Manual: docs/TBN-Founders-Manual.md
- Staff Training Manual: docs/TBN-Staff-Training-Manual.md
- EIC Proposal: docs/EIC-Accelerator-PartB.md

---

## SERVER INFO

- IP: 3.11.229.68
- SSH: ssh -i .ssh_temp_key ubuntu@3.11.229.68
- Service: sudo systemctl restart tbn
- Logs: sudo journalctl -u tbn --no-pager
- Access log: /var/log/tbn/access.log
- Port: 5004 (behind Nginx)
- Domain: tbn.hardinai.co.uk
- SMTP: info@hardinai.co.uk via smtp.ionos.co.uk

---

## COMPETITIVE POSITIONING

- TBN = "The Enforcer" (runtime verification + budget enforcement)
- Raknor.ai = "The Auditor" (static certification, 26 criteria, patents)
- Don't compete on criteria count. Compete on runtime enforcement.
- "Raknor tells you what to do. TBN automatically enforces it."

---

## THE GOVERNANCE CHAIN (Our Ecosystem)

```
L1-L2: TBN Protocol (us) — agent certification & attestation
L3: DigiEmu Core (Bruno) — decision state reconstruction
L4: Causeway (Vallikat) — admissibility
L5: Execution control — budget enforcement (us) + kill switches
L6: Behaviour observation — open
L7: CLARIXO (Stone) — responsibility attribution
L8: Consequence & enforcement — open
```

---

## LINKEDIN NETWORK (Key Contacts)

- Stone Shi — CLARIXO founder, Cambodia (1st partner, live)
- Bruno Baumgartner — DigiEmu Core, Switzerland (2nd partner, confirmed)
- Vallikat Peethamber — Causeway/VectorPeak, London (potential partner)
- Ishaan Ghosh — Shango MID, India (incoming partner, T-Systems deal)
- Julia Kung — AI governance researcher (named TBN in her post)
- Brian Peister — AI Governance Periodic Table creator (validated TBN)
- Adriana Coppelmans — Dossier Secure founder (connected)
- Saudamini Dubey — Deloitte Digital Partner, UAE (connected)
- Alena Elmer — Senior Compliance & GRC Leader, Zürich (connected)
- Gerard (Garry) Foy — CONTROLTOWER OS, Ireland (connected, reached out)
- Authbound founder — Finland, Tuesday meeting
- Rebeka Nagy — AuditifAI, Hungary (AI Governance, EU AI Act)
