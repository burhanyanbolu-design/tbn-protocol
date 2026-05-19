# 📞 SIP Provider Recommendation — Solving the Vodafone Problem

**Date**: May 12, 2026  
**Status**: DECISION REQUIRED  
**Blocker**: Vodafone does not provide SIP credentials to regular customers

---

## The Problem

Vodafone only offers SIP trunking as a **business service** (Vodafone Evolved Voice / Hybrid Voice). Regular consumer customers cannot get SIP credentials. This means:

1. You can't connect your Vodafone mobile (+447999605080) directly to Asterisk via SIP
2. Your customers will face the same problem with their own phone lines
3. The product needs a simpler approach that doesn't require customers to negotiate with their mobile provider

---

## The Solution: Two-Part Approach

### Part A: For YOUR Test Number (Quick Start)

**Use Vodafone Call Forwarding** to redirect calls to a SIP provider number.

How it works:
```
Customer calls +447999605080 (Vodafone)
    → Vodafone forwards to SIP provider number
        → SIP provider delivers to Asterisk
            → Bot handles the call
```

**Setup**: Dial `**21*[SIP_NUMBER]#` on your Vodafone phone to forward ALL calls.

This means:
- You keep your Vodafone number (+447999605080)
- Customers still call the same number
- Asterisk receives calls via the SIP provider
- No Vodafone SIP credentials needed
- Takes 30 seconds to set up

### Part B: For the PRODUCT (Customer-Facing)

Give each customer a **new geographic number** (01/02/03) from the SIP provider, OR let them forward their existing number to it. This is the simplest model for customers.

---

## Recommended Provider: Sipgate Trunking

### Why Sipgate?

| Feature | Detail |
|---------|--------|
| **Free plan** | £0/month — 1 number, 300 inbound minutes, 1 channel |
| **No setup fees** | Zero cost to start |
| **Free inbound calls** | No charge for receiving calls |
| **Outbound** | 1p/min landline, 7.9p/min mobile |
| **Asterisk guide** | Official documentation for Asterisk setup |
| **FreePBX guide** | Official documentation for FreePBX |
| **Number porting** | Supports UK geographic (01/02) numbers |
| **Trial** | 30-day trial with 3 test numbers + 1 hour of calls |
| **No contract** | Cancel anytime |

### Sipgate Free Plan Details

- 1 UK phone number (geographic 01/02 or 056 test number)
- 300 inbound minutes per month
- 1 outbound channel
- SIP credentials provided instantly
- Asterisk configuration documented

### Sipgate Asterisk Configuration (Ready to Use)

```ini
; /etc/asterisk/pjsip.conf

[transport-udp]
type = transport
protocol = udp
bind = 0.0.0.0

[sipgate]
type = registration
transport = transport-udp
outbound_auth = sipgate_auth
server_uri = sip:sipconnect.sipgate.co.uk:5060
client_uri = sip:YOUR_SIP_ID@sipconnect.sipgate.co.uk
retry_interval = 20
expiration = 3600

[sipgate_auth]
type = auth
auth_type = userpass
username = YOUR_SIP_ID
password = YOUR_SIP_PASSWORD

[sipgate_endpoint]
type = endpoint
transport = transport-udp
context = from-sipgate
disallow = all
allow = alaw
outbound_auth = sipgate_auth
aors = sipgate_aor

[sipgate_aor]
type = aor
contact = sip:sipconnect.sipgate.co.uk:5060

[sipgate_identify]
type = identify
endpoint = sipgate_endpoint
match = 217.10.68.149
```

```ini
; /etc/asterisk/extensions.conf

[from-sipgate]
exten => _X.,1,Answer()
exten => _X.,n,AGI(agi://localhost:4573/call)
exten => _X.,n,Hangup()
```

---

## Alternative Provider: VoiceHost

### Why VoiceHost as Backup?

| Feature | Detail |
|---------|--------|
| **Price** | £4.80/month (Starter Plan) |
| **Asterisk compatible** | Official Asterisk PJSIP guide |
| **24/7 support** | UK-based support team |
| **60-second provisioning** | Instant setup |
| **Number porting** | Supports geographic numbers |
| **18+ years experience** | Established provider |
| **99.99% uptime** | Enterprise-grade reliability |
| **TLS/SRTP** | Encrypted calls supported |

---

## Alternative Provider: Webmate

### Why Webmate as Second Backup?

| Feature | Detail |
|---------|--------|
| **Price** | From £7.57/month per channel |
| **Unlimited UK calls** | Free calls to 01, 02, 03, 07 numbers |
| **Asterisk/FreePBX** | Fully compatible |
| **Free DDI porting** | Port numbers for free |
| **30-day contracts** | No long-term commitment |
| **5-star reviews** | 430+ Trustpilot reviews |

---

## Critical Limitation: Mobile Number Porting

**Important**: Most UK SIP providers (including Sipgate) **cannot port mobile (07xx) numbers**. They only port geographic (01/02) numbers.

This means for your test number (+447999605080):
- ❌ Cannot port the number to a SIP provider
- ✅ CAN forward calls from Vodafone to a SIP number

**For the product**, this means customers will either:
1. Get a NEW geographic number from the SIP provider (simplest)
2. Forward their existing number to the SIP provider number (keeps their number)
3. Port their landline number if they have one (01/02 numbers only)

---

## Recommended Setup Steps

### Step 1: Sign Up for Sipgate (FREE — 5 minutes)

1. Go to https://www.sipgatetrunking.co.uk/
2. Create account (free)
3. Get your SIP-ID and password
4. Get your test number (056 prefix)

### Step 2: Configure Asterisk (10 minutes)

1. SSH into server (3.11.229.68)
2. Update pjsip.conf with Sipgate credentials
3. Update extensions.conf with call routing
4. Restart Asterisk
5. Verify registration

### Step 3: Set Up Call Forwarding (30 seconds)

On your Vodafone phone, dial:
```
**21*[SIPGATE_NUMBER]#
```

This forwards ALL calls from +447999605080 to your Sipgate number.

To cancel forwarding later:
```
##21#
```

### Step 4: Test

1. Call +447999605080 from another phone
2. Call should forward to Sipgate → Asterisk
3. Asterisk should answer and route to Python app

---

## Product Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER SETUP                               │
│                                                                  │
│  Option A: New Number (Simplest)                                │
│  ├─ Customer gets a new 01/02 number from SIP provider         │
│  ├─ Advertises this number for bookings                        │
│  └─ Asterisk receives calls directly                           │
│                                                                  │
│  Option B: Call Forwarding (Keep Existing Number)               │
│  ├─ Customer keeps their existing mobile/landline              │
│  ├─ Sets up call forwarding to SIP number                      │
│  ├─ Customers still call the familiar number                   │
│  └─ Calls forward to Asterisk via SIP                          │
│                                                                  │
│  Option C: Port Landline (01/02 numbers only)                  │
│  ├─ Customer ports their landline to SIP provider              │
│  ├─ Number moves permanently to SIP                            │
│  └─ Asterisk receives calls directly                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Comparison

| Approach | Monthly Cost | Setup Time | Complexity |
|----------|-------------|------------|------------|
| Sipgate Free | £0 | 15 minutes | Very Low |
| Sipgate Paid | £0 + call costs | 15 minutes | Very Low |
| VoiceHost | £4.80 | 30 minutes | Low |
| Webmate | £7.57 | 30 minutes | Low |
| Vodafone Business SIP | £50-100+ | Days/Weeks | High |
| Twilio | £20-50+ | 1 hour | Medium |

---

## For Your Customers (Product Simplicity)

The product setup for a customer would be:

1. **Sign up** on hardin-ai-phone dashboard
2. **Choose**: New number OR forward existing number
3. **If new number**: We provision it automatically (via SIP provider API)
4. **If forwarding**: We give them a number + simple instructions ("Dial **21*NUMBER# on your phone")
5. **Done** — Bot starts answering calls

This is **much simpler** than requiring customers to get SIP credentials from their mobile provider.

---

## My Recommendation

**Start with Sipgate (free plan)** for development and testing:
- Zero cost
- Instant setup
- Official Asterisk documentation
- 300 inbound minutes/month (plenty for testing)
- Upgrade to paid plan when ready for production

**For production customers**, offer:
- VoiceHost (£4.80/mo) or Webmate (£7.57/mo) for reliability
- Automated provisioning via their APIs
- Simple call forwarding instructions for customers who want to keep their number

---

## Next Action

1. ✅ Sign up for Sipgate (free) — https://www.sipgatetrunking.co.uk/
2. ✅ Get SIP credentials
3. ✅ Configure Asterisk on server
4. ✅ Set up call forwarding on Vodafone
5. ✅ Test end-to-end call flow

**Shall I proceed with configuring Asterisk for Sipgate once you've signed up?**

---

**Decision needed**: Confirm you want to go with Sipgate (free) for testing, then I'll configure the server immediately.
