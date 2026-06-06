# Session Context — 5-6 June 2026 (Landing Page Animation + Business Development + Documentation)

## What Was Done This Session (continued from Friday evening into Saturday)

### ✅ TBN Handshake Animation — Built & Deployed to Landing Page
- Built cinematic agent handshake animation (v1 → v6)
- Deployed to tbn.hardinai.co.uk hero section
- Agents walk from edges, handshake, particle burst, walk back

### ✅ Landing Page Updates
- Removed "Console" button (internal admin — not public)
- Changed to "Demo" button linking to /demo
- Embedded full 8-step "How It Works" explainer directly on landing page (below 3-card summary)
- Added /how-it-works route as standalone page too

### ✅ hardinai.co.uk — Pen Testing Service Added
- Service card #10: "PENETRATION TESTING" 
- Industry card #06: "Cybersecurity & Penetration Testing"
- SEO keywords updated for pen testing
- TBN Protocol button fixed → links to tbn.hardinai.co.uk (not /demo)
- Pushed to GitHub Pages repo (burhanyanbolu-design/hardinai.co.uk)
- **NOTE:** hardinai.co.uk served via GitHub Pages, not Lightsail

### ✅ Documentation Created
- `data/bot-anatomy-and-tbn-governance.md` — Full technical + conceptual guide (13 parts)
- `data/tbn-explained-plain-language.md` — Plain language walkthrough
- `demo/tbn-step-by-step.html` — Interactive 8-step click-through
- `demo/tbn-leaflet.html` — Printable one-page leaflet (all 8 steps on 1 page)
- `demo/tbn-leaflet-web.html` — Web version (dark theme, vertical scroll)
- `demo/tbn-visual-explainer.html` — Visual infographic with analogies

### ✅ Provisional Patent Document Drafted
- `data/patent-provisional-tbn-protocol.md`
- Ready to file at IPO.gov.uk when service is back online
- Cost: £30 | Deadline: Before May 3, 2027

### ✅ Referral Split Demo Built
- `demo/referral-split-demo.html` — Interactive SplitPay concept demo
- Split contracts + payment simulation + TBN receipts

### ✅ Logo & Product Image Generated
- `demo/tbn-logo-256.png` — 256x256 square logo
- `demo/tbn-product-800x450.png` — 16:9 product image

---

## Business Development

### Dharani Sri Penumacha (Pen Tester) — CONFIRMED ✅
- Said yes to freelancing on pen test engagements
- Ready to subcontract

### Slava Shestakovskyi (Obriy AI) — CALL BOOKED ✅
- Monday 8 June, 12:00-12:30 BST, Google Meet
- $500K funded, GovTech pilot, Glovo pilot
- Partnership angle: his agents + TBN certification

### YC Application — REJECTED
- Not selected for Summer 2026 interview
- Apply again Winter 2027 with revenue + multiple partners
- Over 50% of funded companies are repeat applicants

### Google for Startups Cloud — FIXED ✅
- Created Google account with info@hardinai.co.uk
- Set up GCP billing, replied with screenshot
- Waiting for $100K+ credits approval

### Web Summit Lisbon — November 9-12, 2026 ✅
- 4 days, MEO Arena, startup stand confirmed

---

## Key Learnings This Session

### TBN Product (deepened understanding):
- TBN records and signs what the bot did (independent witness)
- TBN does NOT stop/guide/modify the bot
- Security challenges = one-time test (driving test)
- Attestation = every action forever (dashcam)
- Boundaries are declared by BD, tested by TBN, recorded ongoing
- Only escape: stop using the service (but past receipts remain)
- Biggest weakness: selective reporting → solved by governance-layer integration (Shango model)
- Receipts prove THAT action happened, not WHAT the content was (privacy)

### Red Team Against TBN:
- Silence the recorder → gap detection
- Selective reporting → governance layer reports, not operator
- DDoS → redundancy + queuing
- Forge receipts → cryptographically impossible
- Tamper receipts → signature fails
- Steal key → revoke + reissue

### Business Model Options:
- TBN Certify (self-service) — customer tests own bot
- TBN Govern (done-for-you) — we add governance layer + certify (premium)
- Referral split product — future Phase 2

---

## Infrastructure Notes
- hardinai.co.uk: GitHub Pages (185.199.108.153)
- tbn.hardinai.co.uk: AWS Lightsail (3.11.229.68) → Flask/Gunicorn port 5004
- /how-it-works route added to server.py
- GCP backup planned when credits arrive

---

## Git Commits This Session
- ce10cb6 — Add referral split commission demo
- 79e347c — Add pen testing service and SEO to hardinai.co.uk
- a80ac2e — Add penetration testing service, fix TBN link (GitHub Pages)
- 0f213a7 — Update session context + provisional patent draft
- 70021f4 — Add TBN how-it-works explainer pages
- d89cf3d — Add remaining explainer files
- 6043de8 — Embed 8-step explainer on landing page

---

## TODO / Next Actions
- [ ] Slava call Monday 12:00 BST
- [ ] Send pen test scoping questions to client
- [ ] File provisional patent (IPO site down — try Monday)
- [ ] Get Dharani's rate for pen test scope
- [ ] Follow up Nishaan (ActTrident) + Adem (Beyond Guard)

## What Was Done This Session

### ✅ TBN Handshake Animation — Built & Deployed to Landing Page
- Built a cinematic agent handshake animation through multiple iterations (v1 → v6)
- Two TBN-certified agents (green "Agent" + blue "Validator") walk from edges toward each other
- Arms extend from 3 o'clock / 9 o'clock positions (outer edge of circle)
- Handclasp forms in the middle with sparks and particle burst
- "✓ VERIFIED — TBN handshake complete" badge appears
- Agents walk back, animation loops
- Deployed to tbn.hardinai.co.uk landing page hero section

#### Files:
- `demo/tbn_agent_handshake.html` — v1 (original)
- `demo/tbn_handshake_v4.html` — v4 (arms-only, stationary)
- `demo/tbn_handshake_v5.html` — v5 (combined walk + arms)
- `demo/tbn_handshake_v6.html` — v6 FINAL (cinematic: glowing, particles, beam)
- `api/templates/tbn_landing.html` — Landing page with embedded compact animation

### ✅ Landing Page Nav Fixed
- Removed "Console" button (internal admin, shouldn't be public)
- Changed to "Demo" button linking to /demo
- Footer updated to remove Console reference

### ✅ hardinai.co.uk Updated with Pen Testing Service
- Added service card #10: "PENETRATION TESTING"
- Added Industry card #06: "Cybersecurity & Penetration Testing"
- Updated SEO meta tags with pen testing keywords
- Updated page title to include "Penetration Testing"
- Fixed TBN Protocol button to link to tbn.hardinai.co.uk (not /demo)
- Pushed to GitHub Pages repo (burhanyanbolu-design/hardinai.co.uk)
- **NOTE:** hardinai.co.uk is served via GitHub Pages (IPs: 185.199.108.153 etc), NOT the Lightsail server

### ✅ Provisional Patent Document Drafted
- Full description ready at `data/patent-provisional-tbn-protocol.md`
- Title: "Method and System for Independent Cryptographic Certification and Attestation of Autonomous AI Agent Actions"
- 5 claims covering: security challenges + certification + per-action receipts + offline verification
- Ready to submit at IPO.gov.uk when service is back online (was down today)
- Cost: £30 online
- Deadline: Before May 3, 2027 (12 months from first PyPI disclosure)

---

## Business Development

### ✅ Dharani Sri Penumacha (Pen Tester) — CONFIRMED
- Responded YES to freelancing on pen test engagements
- Ready to subcontract when the client confirms scope
- Next: send scoping questions to pen test client, get her rate, quote with margin

### ✅ Slava Shestakovskyi (Obriy AI) — CALL BOOKED
- Monday 8 June, 12:00-12:30 BST, Google Meet
- CEO of Obriy AI (multi-agent enterprise/GovTech automation)
- Raised $500K April 2026
- GovTech pilot with Ukraine Ministry of Justice
- Glovo customer support pilot
- Partnership angle: his agents do the work, TBN certifies them
- Also attending Web Summit Lisbon (met there last year)

### ✅ Web Summit Lisbon — November 9-12, 2026
- 4 days at MEO Arena
- Hardin AI has a startup stand
- 70,000+ attendees
- Prep starts September

### ✅ Google for Startups Cloud Program — Fixed
- Created Google account with info@hardinai.co.uk
- Set up GCP billing under company domain
- Replied with screenshot for re-processing
- Waiting for approval ($100K+ credits)

### Tiny Hunt Submission — Attempted
- Filled form, generated logo (tbn-logo-256.png) and product image (tbn-product-800x450.png)
- Free slots fully booked through July — skipped (not worth $9)

### Pen Test Client Lead
- Scoping questions drafted, ready to send
- Scope: 1 external IP, 3 app URLs, 1 internal IP, 3 instrumented app URLs, 1 on-prem + devices
- Timeline: 2 weeks
- Estimated value: £16-30k (Burhan keeps 25-30% margin)

### Sharad Kumar Agarwal (JK Tyre CDIO)
- Cold outreach via Ishaan's introduction
- Message sent, waiting for reply
- Don't follow up yet

### Referral Chain Business Idea — Noted
- Instant commission splitting at payment time
- Multi-level referral chains with TBN governance/proof
- Park for later — good Phase 2 product / demo use case

---

## Key Learnings / Decisions

### TBN Product Understanding (deepened this session):
- TBN does NOT stop bad behaviour — it PROVES what happened
- TBN does NOT inject code into bots — it tests from outside and receipts from outside
- Security challenges happen ONCE (like a driving test)
- Attestation receipts happen EVERY ACTION (like a dashcam)
- One bot = one certificate, many actions, many receipts
- The certification process itself drives quality up (bots must pass to get certified)
- TBN = independent witness + cryptographic stamp

### Governance Stack:
- Guardrails (Beyond Guard, Shango) = bouncer (blocks)
- TBN = body-cam/CCTV (proves)
- Regulator = judge (checks the footage)

### Patent Strategy:
- File provisional (£30) to lock priority date
- Open source doesn't block patent if filed within 12 months of disclosure
- Real moat = trust + network effect + being first, not patents
- Patent adds credibility ("patent pending")

---

## Infrastructure Notes

### hardinai.co.uk
- Served via **GitHub Pages** (NOT Lightsail nginx)
- Repo: github.com/burhanyanbolu-design/hardinai.co.uk
- DNS: A records point to 185.199.108/109/110/111.153
- To update: push to the GitHub repo, not SCP to server

### tbn.hardinai.co.uk
- Served via **Lightsail nginx → Flask/Gunicorn** on port 5004
- Deploy: SCP template to /opt/tbn-protocol/api/templates/ + restart tbn service
- Landing page: /opt/tbn-protocol/api/templates/tbn_landing.html

---

## Git Commits This Session
- `a66f10d` — Add TBN handshake animation to landing page hero section
- `a1be927` — Save session context 5 June 2026
- `79e347c` — Add pen testing service and SEO to hardinai.co.uk
- `a80ac2e` — Add penetration testing service, fix TBN link (GitHub Pages repo)

---

## TODO / Next Actions

### Monday (8 June):
- [ ] Call with Slava (Obriy AI) 12:00 BST
- [ ] Send scoping questions to pen test client
- [ ] File provisional patent when IPO site is back

### This week:
- [ ] Get Dharani's rate for pen test scope
- [ ] Quote pen test client (rate + 25-30% margin)
- [ ] Follow up with Nishaan (ActTrident) — technical one-pager
- [ ] Follow up with Adem (Beyond Guard) on LinkedIn

### Later:
- [ ] Web Summit prep (September)
- [ ] Referral chain concept development
- [ ] Show HN post
- [ ] Operations manual for TBN
