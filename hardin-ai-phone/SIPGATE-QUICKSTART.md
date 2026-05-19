# ⚡ Sipgate Quick Start Guide

**Time to complete**: 15 minutes  
**Cost**: £0 (free plan)

---

## Step 1: Create Sipgate Account (5 minutes)

1. Go to: **https://www.sipgatetrunking.co.uk/**
2. Click "Sign Up" or "Free Trial"
3. Enter your email and create password
4. Verify your email
5. You'll get:
   - **SIP-ID** (looks like: `1234567e0`)
   - **SIP Password** (auto-generated)
   - **Test number** (056 prefix, or choose a 01/02 number)

---

## Step 2: Give Me Your Credentials

Once you have your Sipgate account, tell me:
- Your **SIP-ID**
- Your **SIP Password**  
- Your **Sipgate phone number**

I'll configure Asterisk on the server immediately.

---

## Step 3: Set Up Call Forwarding (30 seconds)

On your Vodafone phone (+447999605080), dial:

```
**21*[YOUR_SIPGATE_NUMBER]#
```

Example: If your Sipgate number is 02012345678, dial:
```
**21*02012345678#
```

You'll hear a confirmation tone. Done.

---

## Step 4: Test

Call +447999605080 from any other phone.  
The call should:
1. Ring your Vodafone number
2. Forward to Sipgate
3. Arrive at Asterisk on the server
4. Get answered by the bot

---

## To Cancel Forwarding Later

Dial on your Vodafone phone:
```
##21#
```

---

## What I'll Configure (Once You Give Credentials)

On the server (3.11.229.68), I'll:
1. Update `/etc/asterisk/pjsip.conf` with Sipgate credentials
2. Update `/etc/asterisk/extensions.conf` with call routing
3. Restart Asterisk
4. Verify SIP registration is active
5. Test inbound call routing

---

## Why This Works

```
Someone calls +447999605080
    ↓
Vodafone forwards (via **21*) to Sipgate number
    ↓
Sipgate delivers call via SIP to your server (3.11.229.68:5060)
    ↓
Asterisk answers and routes to Python booking bot
    ↓
Bot asks questions, saves booking
```

**No Vodafone SIP credentials needed. No business account needed. Free.**

---

## FAQ

**Q: Will I still receive texts on +447999605080?**  
A: Yes. Call forwarding only affects voice calls, not SMS.

**Q: Can I still make outgoing calls from +447999605080?**  
A: Yes. Forwarding only affects incoming calls.

**Q: What about my personal calls?**  
A: Since this number is exclusively for the booking system (as agreed), all calls will go to the bot. If you need to temporarily disable it, dial `##21#`.

**Q: Is there a cost for call forwarding?**  
A: Vodafone may charge for forwarded calls (typically the cost of a call to the forwarded number). Since Sipgate numbers are geographic (01/02), this would be a standard UK landline call rate. Check your Vodafone plan — many include unlimited UK calls.

**Q: What happens if the server is down?**  
A: Calls will forward to Sipgate but won't be answered. You could set up a voicemail fallback on Sipgate for this scenario.

---

## Ready?

1. Sign up at https://www.sipgatetrunking.co.uk/
2. Share your SIP-ID and password
3. I'll have it running in 10 minutes
