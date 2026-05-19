# 📞 Phone Number Usage Policy

**Phone Number**: +447999605080 (Vodafone)  
**Date**: May 12, 2026  
**Status**: CRITICAL REQUIREMENT

---

## Overview

The phone number +447999605080 is **exclusively for the Hardin-AI Phone booking system**. It must NOT be used for personal calls or regular business calls.

---

## Usage Rules

### ✅ ALLOWED

- **Booking system calls only**
  - Customers calling to make bookings
  - Automated bot handling booking questions
  - Transfer to live agent (if requested)

### ❌ NOT ALLOWED

- Personal calls from friends/family
- Regular business calls
- Incoming calls unrelated to bookings
- Any non-booking system traffic

---

## Call Flow

```
Incoming Call to +447999605080
        ↓
Is this a booking system call?
        ↓
    YES → Route to Asterisk/Bot
        ↓
    Bot asks booking questions
        ↓
    Customer wants live agent?
        ↓
    YES → Transfer to designated agent number
    NO → Complete booking, save to database
        ↓
    End call

        ↓
    NO → Reject call or forward to personal number
        ↓
    (Do NOT answer as personal line)
```

---

## Live Agent Transfer

### When to Transfer

- Customer explicitly requests "live agent"
- Customer says "speak to someone"
- Customer says "I want to talk to a person"
- Bot cannot understand customer
- Customer is confused or frustrated

### Transfer Destination

**Live Agent Number**: [TO BE CONFIGURED]

Options:
1. **Your personal mobile**: +44XXXXXXXXXX
2. **Business line**: +44XXXXXXXXXX
3. **Voicemail**: Automated voicemail system
4. **Queue**: Hold music + queue system

---

## Asterisk Configuration

### Dialplan Logic

```ini
; /etc/asterisk/extensions.conf

[incoming-calls]
exten => s,1,Answer()
exten => s,n,Playback(welcome-to-booking-system)
exten => s,n,AGI(agi://localhost:4573/call)
exten => s,n,Hangup()

; If customer presses 0 or says "agent"
exten => 0,1,Playable(transferring-to-agent)
exten => 0,n,Dial(SIP/agent-line)
exten => 0,n,Hangup()
```

---

## Important Notes

### 1. No Personal Use

⚠️ **CRITICAL**: This number is **NOT** your personal phone line.

- Do NOT give this number to friends/family
- Do NOT use for personal calls
- Do NOT answer as if it's your personal line
- Do NOT expect to receive personal calls

### 2. Booking System Only

✅ This number is **EXCLUSIVELY** for:
- Hardin-AI Phone booking system
- Automated bot handling
- Live agent transfers (if requested)

### 3. Live Agent Transfer

When a customer requests a live agent:
1. Bot detects request
2. Asterisk transfers call to designated number
3. You (or agent) answer the call
4. Handle customer request
5. Complete booking or resolve issue

### 4. Call Routing

```
+447999605080 (Vodafone SIP Trunk)
        ↓
Asterisk (3.11.229.68)
        ↓
    ├─ Booking System (Bot)
    │   ├─ Ask questions
    │   ├─ Save booking
    │   └─ End call
    │
    └─ Live Agent Transfer
        ├─ Transfer to agent number
        ├─ Agent handles call
        └─ End call
```

---

## Configuration Steps

### Step 1: Set Agent Transfer Number

Edit `/etc/asterisk/extensions.conf`:

```ini
[incoming-calls]
; Set your agent number here
exten => 0,1,Dial(SIP/YOUR_AGENT_NUMBER)
```

Replace `YOUR_AGENT_NUMBER` with:
- Your personal mobile number
- Your business line
- A voicemail system
- A queue system

### Step 2: Configure Bot to Detect Transfer Requests

The bot should detect:
- "I want to speak to someone"
- "Can I talk to a person?"
- "I need a live agent"
- "Transfer me to an agent"
- "0" (DTMF digit)

### Step 3: Test Transfer Flow

1. Call +447999605080
2. Bot answers and asks questions
3. Say "I want to speak to someone"
4. Bot transfers call to agent number
5. Verify transfer works

---

## Booking System Flow

### Normal Booking (No Transfer)

```
1. Customer calls +447999605080
2. Bot answers: "Welcome to Hardin-AI Phone Booking"
3. Bot asks: "What is your name?"
4. Customer: "John Smith"
5. Bot asks: "Where are you picking up from?"
6. Customer: "Terminal 3"
7. ... (continue through all questions)
8. Bot: "Your booking reference is HAP-12345678"
9. Bot: "Thank you for booking with us"
10. Call ends
11. Booking saved to database
```

### With Live Agent Transfer

```
1. Customer calls +447999605080
2. Bot answers: "Welcome to Hardin-AI Phone Booking"
3. Bot asks: "What is your name?"
4. Customer: "I want to speak to someone"
5. Bot: "Transferring you to a live agent"
6. Call transfers to agent number
7. Agent answers
8. Agent handles customer request
9. Agent completes booking or resolves issue
10. Call ends
```

---

## Security & Privacy

### Call Recording

⚠️ **Important**: Inform customers if calls are recorded

Add to bot greeting:
> "This call may be recorded for quality and training purposes"

### Data Protection

- Store customer data securely
- Comply with GDPR/UK data protection laws
- Only use data for booking purposes
- Delete data after retention period

### Voicemail

If customer calls and bot is unavailable:
- Play voicemail greeting
- Record message
- Notify agent of missed call

---

## Troubleshooting

### If Personal Call Comes In

**Scenario**: Friend calls +447999605080

**What happens**:
1. Asterisk answers
2. Bot plays booking system greeting
3. Friend is confused
4. Friend hangs up

**Solution**: Tell friends to use your personal number instead

### If Bot Doesn't Recognize Transfer Request

**Scenario**: Customer says "I need help" but bot doesn't transfer

**Solution**:
1. Update bot intent detection
2. Add more keywords for transfer
3. Allow customer to press 0 for agent
4. Test with various phrases

### If Transfer Fails

**Scenario**: Bot tries to transfer but agent number is unreachable

**Solution**:
1. Check agent number is correct
2. Verify agent phone is on
3. Check network connectivity
4. Set up voicemail as fallback

---

## Agent Number Configuration

### Option 1: Personal Mobile

```ini
exten => 0,1,Dial(SIP/+447XXXXXXXXXX)
```

**Pros**: Direct to you  
**Cons**: You must always be available

### Option 2: Business Line

```ini
exten => 0,1,Dial(SIP/business-line)
```

**Pros**: Dedicated line  
**Cons**: Requires separate phone line

### Option 3: Voicemail

```ini
exten => 0,1,VoiceMail(u1234)
```

**Pros**: Always available  
**Cons**: Customer can't speak to live agent

### Option 4: Queue System

```ini
exten => 0,1,Queue(booking-agents)
```

**Pros**: Multiple agents  
**Cons**: More complex setup

---

## Recommended Setup

### For MVP (Phase 1)

**Agent Number**: Your personal mobile  
**Transfer Logic**: Press 0 or say "agent"  
**Voicemail**: Enabled as fallback

### For Production

**Agent Number**: Dedicated business line  
**Transfer Logic**: Multiple keywords + DTMF  
**Voicemail**: Professional greeting  
**Queue**: Multiple agents if needed

---

## Testing Checklist

- [ ] Call +447999605080
- [ ] Bot answers with booking greeting
- [ ] Bot asks first question
- [ ] Say "I want to speak to someone"
- [ ] Bot transfers call
- [ ] Agent number rings
- [ ] Call connects successfully
- [ ] Agent can handle booking
- [ ] Call ends properly
- [ ] Booking is saved

---

## Important Reminders

✅ **DO**:
- Use this number ONLY for booking system
- Transfer to agent when requested
- Keep agent number updated
- Test transfer flow regularly
- Monitor call logs

❌ **DON'T**:
- Give this number to friends/family
- Use for personal calls
- Answer as personal line
- Ignore transfer requests
- Leave agent number unreachable

---

## Next Steps

1. **Decide on agent transfer number**
   - Personal mobile?
   - Business line?
   - Voicemail?
   - Queue system?

2. **Configure Asterisk**
   - Update `/etc/asterisk/extensions.conf`
   - Set agent transfer number
   - Test transfer flow

3. **Update Bot**
   - Add transfer request detection
   - Configure transfer logic
   - Test with various phrases

4. **Test End-to-End**
   - Make test calls
   - Verify booking flow
   - Verify transfer flow
   - Check call logs

---

## Questions?

If you have questions about:
- Phone number usage
- Transfer configuration
- Bot behavior
- Call routing

Please clarify before proceeding to Task 1.3.

---

**Status**: CRITICAL REQUIREMENT DOCUMENTED  
**Next Action**: Confirm agent transfer number and proceed to Task 1.3
