# 📞 How to Get Vodafone SIP Credentials

**Phone Number**: +447999605080 (Vodafone)  
**Date**: May 12, 2026

---

## Overview

To use your Vodafone phone line with Asterisk, you need SIP (Session Initiation Protocol) credentials. These are like a username and password for your phone line.

---

## Where to Get Vodafone SIP Credentials

### Option 1: Vodafone Business Portal (RECOMMENDED)

**Steps**:

1. **Go to Vodafone Business Portal**
   - URL: https://www.vodafone.co.uk/business/
   - Or: https://myvodafone.vodafone.co.uk/

2. **Log in with your account**
   - Username: Your Vodafone account email
   - Password: Your Vodafone account password

3. **Navigate to VoIP/SIP Settings**
   - Look for: "VoIP", "SIP", "Phone Settings", or "Trunk Settings"
   - May be under: "Services" → "Phone" → "SIP Trunk"

4. **Find SIP Credentials**
   - Look for: "SIP Username", "SIP Password", "SIP Server"
   - May also show: "SIP Port" (usually 5060)

5. **Copy the credentials**
   - SIP Username: `[copy this]`
   - SIP Password: `[copy this]`
   - SIP Server: `sip.vodafone.co.uk` (usually)

---

### Option 2: Contact Vodafone Business Support

**If you can't find credentials online**:

1. **Call Vodafone Business Support**
   - Number: 0344 404 0444 (UK)
   - Hours: Monday-Friday, 8am-6pm

2. **Tell them**:
   - "I need SIP trunk credentials for my phone line"
   - "Phone number: +447999605080"
   - "I want to use Asterisk/FreePBX"

3. **They will provide**:
   - SIP username
   - SIP password
   - SIP server address
   - SIP port (usually 5060)

4. **Ask for**:
   - "Can you email me the credentials?"
   - "Can you confirm the SIP server address?"
   - "What's the SIP port?"

---

### Option 3: Check Your Vodafone Bill/Welcome Email

**Look for**:

1. **Original welcome email** when you set up the line
   - May contain SIP credentials
   - Check spam folder if not in inbox

2. **Vodafone bill/invoice**
   - May have SIP details attached
   - Check online bill portal

3. **Vodafone account documents**
   - Any setup guides
   - Any configuration documents

---

## What You're Looking For

### Required Information

| Item | Example | Where to Find |
|------|---------|---------------|
| **SIP Username** | `yourname@vodafone.co.uk` or `12345678` | Portal or email |
| **SIP Password** | `abc123XYZ!@#` | Portal or email |
| **SIP Server** | `sip.vodafone.co.uk` | Portal or support |
| **SIP Port** | `5060` | Portal or support |
| **Phone Number** | `+447999605080` | Your bill |

### Optional Information

| Item | Example | Notes |
|------|---------|-------|
| **Outbound Proxy** | `sip.vodafone.co.uk` | Usually same as server |
| **Registrar** | `sip.vodafone.co.uk` | Usually same as server |
| **From Domain** | `vodafone.co.uk` | Usually vodafone.co.uk |

---

## Step-by-Step: Vodafone Portal

### 1. Log In to Vodafone Business

```
URL: https://myvodafone.vodafone.co.uk/
Username: your-email@example.com
Password: your-password
```

### 2. Find Phone/VoIP Settings

**Look for menu items**:
- "Services"
- "Phone"
- "VoIP"
- "Trunk"
- "SIP"
- "Communications"

### 3. Find SIP Configuration

**Look for sections**:
- "SIP Trunk Settings"
- "VoIP Configuration"
- "Phone Line Settings"
- "Advanced Settings"

### 4. Copy Credentials

**You should see**:
```
SIP Username: [your-username]
SIP Password: [your-password]
SIP Server: sip.vodafone.co.uk
SIP Port: 5060
```

### 5. Save Somewhere Safe

**Write down or copy**:
- [ ] SIP Username: ___________________
- [ ] SIP Password: ___________________
- [ ] SIP Server: ___________________
- [ ] SIP Port: ___________________

---

## Common Vodafone SIP Server Addresses

| Server | Port | Notes |
|--------|------|-------|
| `sip.vodafone.co.uk` | 5060 | Standard |
| `sip-uk.vodafone.co.uk` | 5060 | Alternative |
| `sip.vodafone.net` | 5060 | Alternative |

**Most common**: `sip.vodafone.co.uk:5060`

---

## If You Can't Find Credentials

### Troubleshooting

**Problem**: Can't log into Vodafone portal

**Solution**:
1. Reset password: https://myvodafone.vodafone.co.uk/forgot-password
2. Call support: 0344 404 0444
3. Check email for account details

**Problem**: Portal doesn't show SIP settings

**Solution**:
1. Your account may not have SIP trunk enabled
2. Call Vodafone: 0344 404 0444
3. Ask them to enable SIP trunk
4. Ask them to provide credentials

**Problem**: Credentials don't work

**Solution**:
1. Double-check username and password (case-sensitive)
2. Verify SIP server address
3. Call Vodafone support
4. Ask for new credentials

---

## Vodafone Support Contact

### Phone
- **Business Support**: 0344 404 0444
- **Hours**: Monday-Friday, 8am-6pm
- **What to say**: "I need SIP trunk credentials for +447999605080"

### Online
- **Portal**: https://myvodafone.vodafone.co.uk/
- **Chat**: Available in portal
- **Email**: support@vodafone.co.uk

### What to Tell Them

```
"Hello, I need SIP trunk credentials for my Vodafone phone line.

Phone number: +447999605080

I want to use this line with Asterisk/FreePBX for a phone booking system.

Can you provide:
1. SIP username
2. SIP password
3. SIP server address
4. SIP port

Can you email me these details?"
```

---

## Security Notes

⚠️ **Important**:

1. **Keep credentials secure**
   - Don't share with anyone
   - Don't commit to version control
   - Don't post online

2. **Use strong passwords**
   - If you can change password, use strong one
   - Mix of letters, numbers, symbols

3. **Monitor usage**
   - Check Vodafone bill for unexpected charges
   - Monitor call logs
   - Set up alerts if available

4. **Protect your server**
   - Use firewall
   - Restrict SIP port access
   - Monitor for unauthorized access

---

## Once You Have Credentials

### Next Steps

1. **Save credentials securely**
   - Write them down
   - Store in password manager
   - Don't lose them!

2. **Provide to Kiro**
   - SIP Username: ___________________
   - SIP Password: ___________________
   - Live Agent Phone: ___________________

3. **Execute Task 1.3**
   - Configure Asterisk
   - Test SIP registration
   - Verify incoming calls

4. **Execute Task 1.4**
   - Make test calls
   - Verify booking flow
   - Verify transfer flow

---

## Checklist

- [ ] Log into Vodafone Business portal
- [ ] Find SIP settings
- [ ] Copy SIP username
- [ ] Copy SIP password
- [ ] Confirm SIP server (sip.vodafone.co.uk)
- [ ] Confirm SIP port (5060)
- [ ] Save credentials securely
- [ ] Provide to Kiro
- [ ] Ready for Task 1.3

---

## Questions?

If you have questions about:
- Finding credentials
- Vodafone portal
- SIP settings
- Support contact

Please ask before proceeding.

---

**Status**: AWAITING VODAFONE CREDENTIALS  
**Next Action**: Get credentials and provide to Kiro
