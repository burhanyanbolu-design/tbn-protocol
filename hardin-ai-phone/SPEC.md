# 🎯 Hardin-AI Phone — Complete Product Specification

**Project**: Hardin-AI Phone Booking System  
**Status**: Specification Phase  
**Date**: May 12, 2026  
**Version**: 1.0.0

---

## 📋 Executive Summary

**Hardin-AI Phone** is a **plugin-based phone booking system** that integrates into any website. It replaces expensive services like Twilio by using existing UK phone lines (Vodafone, BT, etc.) and certified TBN bots to handle customer calls.

**Key differentiator**: Uses **TBN Protocol certified bots** — trusted, verified AI agents that customers can rely on.

**Deployment models**:
1. **Managed Service** — We install and manage (£70-100/month)
2. **Self-Hosted** — Customer installs with clear instructions (£30-50/month)

---

## 🎯 Product Overview

### What It Does

Hardin-AI Phone allows businesses to:
- ✅ Accept phone bookings on their existing phone line
- ✅ Use a certified TBN bot to handle calls
- ✅ Save bookings to database automatically
- ✅ Integrate with any website (Shopify, WordPress, custom)
- ✅ No Twilio fees — use existing phone infrastructure

### Who It's For

- Taxi companies
- Restaurants (reservations)
- Salons (appointments)
- Hotels (bookings)
- Any business needing phone automation

### Why It's Better Than Twilio

| Feature | Hardin-AI Phone | Twilio |
|---------|-----------------|--------|
| **Cost** | £30-100/month | £100-300/month |
| **Phone line** | Use existing | Buy from Twilio |
| **Trust** | Certified TBN bots | Generic AI |
| **Data ownership** | Customer owns | Twilio owns |
| **Vendor lock-in** | None | High |
| **Self-hosted option** | Yes | No |

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    CUSTOMER WEBSITE                      │
│  (Shopify, WordPress, custom site, etc.)                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Hardin-AI Phone Plugin                           │  │
│  │  ├─ Booking form                                  │  │
│  │  ├─ Call handler                                  │  │
│  │  └─ Status dashboard                              │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              HARDIN-AI PHONE CORE                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Asterisk/FreePBX (Phone System)                  │  │
│  │  ├─ SIP trunk connection                          │  │
│  │  ├─ Call routing                                  │  │
│  │  └─ Audio handling                                │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Python FastAPI (Booking Logic)                   │  │
│  │  ├─ Call handler                                  │  │
│  │  ├─ Question flow                                 │  │
│  │  └─ Booking processor                             │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  TBN Bot Integration                              │  │
│  │  ├─ Certified bot selection                       │  │
│  │  ├─ Trust verification                            │  │
│  │  └─ Bot personality injection                     │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Speech Processing                                │  │
│  │  ├─ faster-whisper (speech-to-text)              │  │
│  │  └─ Piper TTS (text-to-speech)                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              CUSTOMER PHONE LINE                         │
│  (Vodafone, BT, Plusnet, etc.)                          │
│  SIP trunk connection                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              CUSTOMER DATABASE                           │
│  (SQLite, PostgreSQL, or cloud)                         │
│  Bookings, customer info, call logs                     │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Customer calls phone number
   ↓
2. Vodafone routes to SIP trunk
   ↓
3. Asterisk receives call
   ↓
4. Python app starts booking flow
   ↓
5. TBN bot handles conversation
   ↓
6. faster-whisper transcribes speech
   ↓
7. Bot processes answer
   ↓
8. Piper converts response to speech
   ↓
9. Customer hears response
   ↓
10. Booking saved to database
```

---

## 📋 Requirements

### Functional Requirements

#### 1. Phone Integration
- [ ] Accept inbound calls on customer's existing phone line
- [ ] Route calls via SIP trunk to Asterisk
- [ ] Handle multiple concurrent calls
- [ ] Support call transfer to human agent
- [ ] Record call logs and audio (optional)

#### 2. Booking Flow
- [ ] Ask customer name
- [ ] Ask pickup location
- [ ] Ask destination
- [ ] Ask date
- [ ] Ask time
- [ ] Ask number of passengers
- [ ] Ask luggage amount
- [ ] Ask flight number (if airport pickup)
- [ ] Ask callback number
- [ ] Confirm booking details
- [ ] Save booking to database

#### 3. TBN Bot Integration
- [ ] Select certified TBN bot for customer
- [ ] Verify bot certification
- [ ] Inject bot personality into responses
- [ ] Use bot's voice/style
- [ ] Log bot activity

#### 4. Speech Processing
- [ ] Convert speech to text (faster-whisper)
- [ ] Convert text to speech (Piper)
- [ ] Handle accents and dialects
- [ ] Detect intent (book vs. chat vs. info)
- [ ] Transfer to human if needed

#### 5. Database
- [ ] Store bookings with all details
- [ ] Store customer information
- [ ] Store call logs
- [ ] Store bot interactions
- [ ] Query bookings by date/customer/status

#### 6. Plugin System
- [ ] WordPress plugin
- [ ] Shopify app
- [ ] Custom website integration (API)
- [ ] Embed booking widget on website
- [ ] Dashboard to view bookings

#### 7. Admin Dashboard
- [ ] View all bookings
- [ ] Filter by date/customer/status
- [ ] Export bookings (CSV/PDF)
- [ ] View call logs
- [ ] Manage bot settings
- [ ] View analytics

### Non-Functional Requirements

- **Performance**: Handle 10+ concurrent calls
- **Reliability**: 99.5% uptime
- **Security**: Encrypt sensitive data, secure API
- **Scalability**: Support 100+ customers
- **Maintainability**: Clear code, good documentation
- **Cost**: <£5/month per customer (hosting + infrastructure)

---

## 🚀 Deployment Models

### Model 1: Managed Service

**What we do:**
- Install on our server
- Manage Asterisk/FreePBX
- Handle SIP trunk setup
- Manage TBN bot
- Monitor uptime
- Provide support

**What customer does:**
- Provide phone number
- Configure booking questions
- View bookings via dashboard
- Pay monthly fee

**Price**: £70-100/month  
**Setup time**: 1-2 days  
**Support**: Email + phone

---

### Model 2: Self-Hosted

**What we provide:**
- Complete installation package
- Step-by-step installation guide
- Configuration templates
- Support documentation
- Video tutorials

**What customer does:**
- Provision Ubuntu VPS
- Run installation script
- Configure SIP trunk
- Manage their own server
- Pay monthly fee

**Price**: £30-50/month  
**Setup time**: 2-4 hours (for tech-savvy)  
**Support**: Documentation + email

---

## 📦 Installation Package Contents

### For Managed Service
```
hardin-ai-phone-managed/
├── docker-compose.yml
├── asterisk-config/
├── python-app/
├── tbn-bot-config/
├── nginx-config/
└── deployment-scripts/
```

### For Self-Hosted
```
hardin-ai-phone-self-hosted/
├── INSTALLATION.md (step-by-step)
├── REQUIREMENTS.md (what you need)
├── setup.sh (automated setup script)
├── asterisk-config/
├── python-app/
├── tbn-bot-config/
├── troubleshooting.md
└── support-contact.md
```

---

## 💰 Business Model

### Revenue Streams

1. **Managed Service Subscriptions**
   - £70-100/month per customer
   - Recurring revenue
   - High margin (cost: ~£5/month)

2. **Self-Hosted Licenses**
   - £30-50/month per customer
   - Lower support cost
   - Attracts tech-savvy customers

3. **Premium Features**
   - Advanced analytics: +£20/month
   - Custom bot personality: +£30/month
   - Priority support: +£15/month
   - API access: +£25/month

4. **Professional Services**
   - Custom integration: £500-2000
   - Training: £200/day
   - Consulting: £150/hour

### Pricing Strategy (Flexible & Usage-Based)

**Pricing:**

| Tier | Price | First Month | Features |
|------|-------|-------------|----------|
| **Standard** | £9.99/mo | £4.99 | UK number, AI booking bot, live agent transfer, dashboard |
| **Professional** | £19.99/mo | £9.99 | + Custom greeting, multiple call flows, analytics |
| **Enterprise** | £49.99/mo | £24.99 | + API access, custom bot personality, priority support |

**Pricing will scale based on:**
- Customer usage patterns
- Call volume
- Feature adoption
- Market feedback

**Flexible models to test:**
1. **Flat monthly** — Fixed price regardless of usage
2. **Usage-based** — Base fee + per-call charges
3. **Hybrid** — Base fee + overage charges
4. **Freemium** — Free tier with paid upgrades

**We'll monitor and adjust pricing quarterly based on real data.**

---

## 🎯 Success Metrics

### Technical Metrics
- [ ] System uptime: 99.5%+
- [ ] Call success rate: 95%+
- [ ] Average call duration: 3-5 minutes
- [ ] Booking accuracy: 99%+
- [ ] Speech recognition accuracy: 90%+

### Business Metrics
- [ ] Customer acquisition: 10 customers in first 3 months
- [ ] Monthly recurring revenue: £1000+ by month 6
- [ ] Customer retention: 90%+
- [ ] Net promoter score: 50+
- [ ] Support ticket resolution: 24 hours

---

## 📅 Implementation Timeline

### Phase 1: MVP (Weeks 1-4)
- [ ] Set up Asterisk on test server
- [ ] Build Python booking app
- [ ] Integrate faster-whisper + Piper
- [ ] Connect to Vodafone SIP trunk
- [ ] Test with +447999605080
- [ ] Create basic documentation

### Phase 2: TBN Integration (Weeks 5-6)
- [ ] Integrate TBN bot selection
- [ ] Add bot personality injection
- [ ] Verify bot certification
- [ ] Test end-to-end

### Phase 3: Plugin System (Weeks 7-8)
- [ ] Build WordPress plugin
- [ ] Build Shopify app
- [ ] Create API for custom sites
- [ ] Build admin dashboard

### Phase 4: Deployment (Weeks 9-10)
- [ ] Create managed service setup
- [ ] Create self-hosted package
- [ ] Write installation guides
- [ ] Create video tutorials

### Phase 5: Launch (Week 11+)
- [ ] Beta testing with 3-5 customers
- [ ] Gather feedback
- [ ] Make improvements
- [ ] Public launch

---

## 🔧 Technology Stack

### Core
- **Asterisk** (open-source PBX)
- **FreePBX** (Asterisk UI)
- **Python 3.9+** (FastAPI)
- **SQLite/PostgreSQL** (database)

### Speech
- **faster-whisper** (speech-to-text)
- **Piper** (text-to-speech)

### Integration
- **TBN Protocol** (bot certification)
- **SIP** (phone protocol)
- **REST API** (plugin communication)

### Deployment
- **Docker** (containerization)
- **Ubuntu 22.04** (OS)
- **Nginx** (reverse proxy)
- **Let's Encrypt** (SSL/TLS)

---

## 📞 Support & Documentation

### Documentation to Create
- [ ] Installation guide (managed)
- [ ] Installation guide (self-hosted)
- [ ] Configuration guide
- [ ] API documentation
- [ ] Troubleshooting guide
- [ ] FAQ
- [ ] Video tutorials (5-10 videos)

### Support Channels
- Email support
- Documentation portal
- Video tutorials
- Community forum (optional)

---

## 🎯 Next Steps

1. **Approve this spec** — Confirm requirements and architecture
2. **Create detailed requirements document** — Break down each requirement
3. **Create architecture document** — Detailed technical design
4. **Create implementation tasks** — Step-by-step build plan
5. **Start Phase 1 development** — Build MVP

---

## 📝 Notes

- **Trial number**: +447999605080 (Vodafone)
- **Test bot**: Will use TBN certified bot
- **First customer**: Heathrow Black Cabs (taxi company)
- **Launch target**: June 2026

---

**Status**: Ready for approval  
**Next action**: Review and approve spec, then proceed to detailed requirements

