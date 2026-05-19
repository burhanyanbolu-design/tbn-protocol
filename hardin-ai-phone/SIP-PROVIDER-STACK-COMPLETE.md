# ✅ SIP Provider Stack — INSTALLED & RUNNING

**Date**: May 12, 2026  
**Server**: 3.11.229.68  
**Status**: ACTIVE

---

## What's Running

| Service | Port | Role | Status |
|---------|------|------|--------|
| **Kamailio** | 5060 (UDP/TCP) | SIP Proxy/Registrar (public-facing) | ✅ Active |
| **Asterisk** | 5080 (UDP/TCP) | Media Server (call handling, TTS, STT) | ✅ Active |
| **MySQL** | 3306 | Database (users, CDR, routing) | ✅ Active |

---

## Architecture

```
Internet (Customers / Wholesale DID Provider)
    ↓ SIP (port 5060)
┌─────────────────────────────────────────┐
│  Kamailio (SIP Proxy/Registrar)         │
│  ├─ Authenticates SIP users             │
│  ├─ Routes inbound calls to Asterisk    │
│  ├─ Routes outbound calls to wholesale  │
│  ├─ NAT traversal                       │
│  └─ Load balancing (future)             │
└─────────────────────────────────────────┘
    ↓ SIP (port 5080, localhost)
┌─────────────────────────────────────────┐
│  Asterisk (Media Server)                │
│  ├─ Answers calls                       │
│  ├─ Plays audio (TTS via Piper)         │
│  ├─ Records audio (STT via Whisper)     │
│  ├─ Runs booking bot (AGI)              │
│  └─ Transfers to live agent             │
└─────────────────────────────────────────┘
    ↓ AGI (port 4573, localhost)
┌─────────────────────────────────────────┐
│  Python App (Booking Logic)             │
│  ├─ 9-question booking flow             │
│  ├─ TBN bot integration                 │
│  ├─ Database operations                 │
│  └─ Admin dashboard                     │
└─────────────────────────────────────────┘
```

---

## Credentials

### Kamailio MySQL
- **Database**: kamailio
- **User**: kamailio
- **Password**: hardinai2026
- **Host**: localhost

### Test SIP User
- **Username**: testuser
- **Domain**: sip.hardinai.co.uk
- **Password**: testpass123
- **SIP URI**: sip:testuser@sip.hardinai.co.uk
- **Registrar**: 3.11.229.68:5060

---

## What's Left to Complete

### 1. Wholesale DID Provider (for PSTN connectivity)
Need to sign up with a wholesale DID provider to get phone numbers:
- **Voxbeam** — UK DIDs from ~$1.50/month
- **DIDLogic** — UK DIDs with Asterisk guides
- **BulkVS** — Wholesale DIDs

Once we have a DID, calls from the public phone network will reach our server.

### 2. DNS Record
Add DNS record for SIP:
```
sip.hardinai.co.uk → 3.11.229.68
```
Plus SRV record:
```
_sip._udp.hardinai.co.uk. 86400 IN SRV 10 60 5060 sip.hardinai.co.uk.
```

### 3. RTPProxy (for NAT traversal of media)
```bash
sudo apt-get install rtpproxy
sudo systemctl start rtpproxy
```

### 4. Sipgate Start Code (when letter arrives)
- Enter code in Sipgate dashboard
- Configure as additional trunk for testing
- Free 300 minutes/month

---

## How to Add a Customer

```bash
# Add new SIP user for a customer
sudo kamctl add customer1@sip.hardinai.co.uk SecurePassword123

# Verify user exists
sudo kamctl db show subscriber
```

---

## How to Manage

```bash
# Check Kamailio status
sudo kamctl stats

# List registered users
sudo kamctl ul show

# Check Asterisk
sudo asterisk -rx "pjsip show endpoints"

# View call logs
sudo asterisk -rx "core show channels"
```

---

## Firewall Ports Open

| Port | Protocol | Purpose |
|------|----------|---------|
| 5060 | UDP/TCP | SIP signaling (Kamailio) |
| 10000-20000 | UDP | RTP media (audio) |

---

## Next Steps

1. **Sign up for wholesale DID provider** (Voxbeam/DIDLogic)
2. **Add DNS record** for sip.hardinai.co.uk
3. **Install RTPProxy** for media relay
4. **Build Python AGI handler** (booking bot)
5. **Test end-to-end** with a real phone call
