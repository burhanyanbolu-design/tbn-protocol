# Project Context — Hardin AI Solutions

## Who You Are
- **Name**: Burhan Yanbolu
- **Company**: Hardin Enterprises Ltd (trading as Hardin AI Solutions)
- **Email**: burhan@hardinai.co.uk
- **GitHub**: https://github.com/burhanyanbolu-design/tbn-protocol
- **Server**: 3.11.229.68 (AWS Lightsail, Ubuntu 22.04)

## Active Projects

### 1. TBN Protocol (Trust Infrastructure for AI Agents)
- **Status**: Live at https://tbn.hardinai.co.uk
- **What it does**: Cryptographically verifiable execution layer that prevents autonomous agents from exceeding operational boundaries. Security challenge system tests bots before certification.
- **Tech**: Python Flask, Gunicorn, SQLite
- **PyPI**: pip install tbn-protocol (v0.1.0)
- **License**: AGPL-3.0
- **Boomi**: Technology Partner (marketplace submission in review)
- **YC**: Applied for Summer 2026 batch
- **Key feature**: Security Challenge System — bots must pass automated security tests (prompt injection, hallucination, data boundary, budget limits) before getting certified

### 2. VoiceReport / Hardin-AI Phone (AI Phone Agent)
- **Status**: Live on +442045772353
- **What it does**: AI bot answers phone calls, collects structured data (bookings, absence reports, etc.)
- **Tech**: Kamailio (SIP proxy, port 5060) + Asterisk (media, port 5080) + Python AGI + Piper TTS + Google STT
- **Dashboard**: https://phone.hardinai.co.uk (admin/hardinai2026)
- **SIP Provider**: Zadarma (login: 517132)
- **Pricing**: £9.99/month, £4.99 first month
- **Use cases**: Taxi booking, school absence reporting, GP appointments, any structured phone data collection
- **Key feature**: Caller ID verification (matches parent phone to school database)

### 3. Hardin AI Search
- **Status**: Proof of concept (143 users)
- **URL**: hardinai.co.uk

## Server Architecture

```
3.11.229.68 (Ubuntu 22.04, 2GB RAM)
├── Kamailio (port 5060) — SIP proxy/registrar
├── Asterisk (port 5080) — Media server, TTS, call handling
├── AGI Bot (port 4573) — Python booking/voice agent
├── TBN Protocol (port 5004) — Flask API
├── Dashboard (port 5006) — Phone bookings dashboard
├── Nginx — Reverse proxy, SSL
├── MySQL — Kamailio database
├── Docker — Open WebUI (port 8080)
└── PostgreSQL — Video CV (port 5432)
```

## Domains
- hardinai.co.uk → Open WebUI (Docker)
- tbn.hardinai.co.uk → TBN Protocol
- phone.hardinai.co.uk → VoiceReport Dashboard
- blog.hardinai.co.uk → Static blog

## Key Decisions Made
- VoiceReport pricing: £9.99/month, £4.99 first month (half price)
- Schools/NHS: quote-based (£49-99/month)
- SIP: Zadarma for now, Gamma trunk when scaling past 10 concurrent calls
- Voice: Piper TTS (British female, alba model)
- STT: Google Speech Recognition (free tier), upgrade to faster-whisper later
- Bot identifies callers by matching Caller ID to registered phone numbers
- Flight number only asked if pickup is from an airport
- Transfer to office costs money (outbound call via Zadarma)

## Current Priorities
1. Get first paying customer for VoiceReport
2. Build landing page at phone.hardinai.co.uk or voicereport domain
3. Wait for Boomi marketplace review
4. Wait for YC response

## SSH Access
```
ssh -i .ssh_temp_key ubuntu@3.11.229.68
```

## Important Files
- api/routes.py — TBN Protocol API (Boomi endpoints at line 1025+)
- hardin-ai-phone/agi_server.py — Voice bot (deployed to /opt/hardin-ai-phone/)
- hardin-ai-phone/dashboard.py — Bookings dashboard
- hardin-ai-phone/kamailio.cfg — SIP proxy config
- hardin-ai-phone/pjsip_zadarma.conf — Zadarma SIP trunk config

## Style Preferences
- Direct action over suggestions
- Complete work before presenting
- Keep things simple
- Low cost / free where possible
- Product must be "shelf-ready" for customers
