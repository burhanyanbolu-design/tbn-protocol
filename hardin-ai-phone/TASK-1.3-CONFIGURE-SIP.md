# 📋 Task 1.3: Configure Vodafone SIP Trunk

**Date**: May 12, 2026  
**Status**: READY TO EXECUTE  
**Estimated Time**: 2 hours

---

## Objective

Configure the Vodafone SIP trunk connection and set up inbound call routing to the Hardin-AI Phone booking system.

---

## Prerequisites

- ✅ Asterisk 20.19.0 installed and running
- ✅ SSH access to server (3.11.229.68)
- ✅ Vodafone SIP trunk credentials
- ✅ Live agent phone number (for transfers)

---

## Configuration Steps

### Step 1: Get Vodafone SIP Credentials

**What you need**:
- SIP username (from Vodafone)
- SIP password (from Vodafone)
- SIP server address (usually sip.vodafone.co.uk)
- Phone number (+447999605080)

**Where to get it**:
- Contact Vodafone business support
- Check your Vodafone account portal
- Look for "SIP trunk" or "VoIP" settings

---

### Step 2: SSH into Server

```powershell
ssh -i .\.ssh_temp_key ubuntu@3.11.229.68
```

---

### Step 3: Edit SIP Configuration

```bash
sudo nano /etc/asterisk/sip.conf
```

**Find the `[vodafone-trunk]` section and update**:

```ini
[vodafone-trunk]
type=trunk
host=sip.vodafone.co.uk
username=YOUR_VODAFONE_USERNAME
secret=YOUR_VODAFONE_PASSWORD
fromuser=YOUR_VODAFONE_USERNAME
fromdomain=sip.vodafone.co.uk
insecure=port,invite
```

**Replace**:
- `YOUR_VODAFONE_USERNAME` → Your actual Vodafone SIP username
- `YOUR_VODAFONE_PASSWORD` → Your actual Vodafone SIP password

**Save**: Press `Ctrl+X`, then `Y`, then `Enter`

---

### Step 4: Configure Inbound Routing

Edit extensions configuration:

```bash
sudo nano /etc/asterisk/extensions.conf
```

**Find or create the `[incoming-calls]` context**:

```ini
[incoming-calls]
; Incoming calls from Vodafone SIP trunk
exten => s,1,Answer()
exten => s,n,Playback(welcome)
exten => s,n,AGI(agi://localhost:4573/call)
exten => s,n,Hangup()

; Transfer to live agent (press 0 or say "agent")
exten => 0,1,Playback(transferring-to-agent)
exten => 0,n,Dial(SIP/LIVE_AGENT_NUMBER)
exten => 0,n,Hangup()

; Fallback for unrecognized input
exten => i,1,Playback(invalid-input)
exten => i,n,Goto(s,1)
```

**Replace**:
- `LIVE_AGENT_NUMBER` → Live agent phone number (e.g., +447XXXXXXXXXX)
- `localhost:4573` → Your Python app AGI server address

---

### Step 5: Configure SIP Trunk Routing

Edit SIP configuration to route incoming calls:

```bash
sudo nano /etc/asterisk/sip.conf
```

**Add routing for incoming calls**:

```ini
[vodafone-trunk]
type=trunk
host=sip.vodafone.co.uk
username=YOUR_VODAFONE_USERNAME
secret=YOUR_VODAFONE_PASSWORD
fromuser=YOUR_VODAFONE_USERNAME
fromdomain=sip.vodafone.co.uk
insecure=port,invite
context=incoming-calls
```

**Key setting**: `context=incoming-calls` routes all incoming calls to the `[incoming-calls]` context

---

### Step 6: Restart Asterisk

```bash
sudo systemctl restart asterisk
```

**Verify restart**:

```bash
sudo systemctl status asterisk
```

Should show: `Active: active (running)`

---

### Step 7: Check SIP Trunk Status

```bash
asterisk -r -x "sip show peers"
```

**Expected output**:

```
Name/username             Host                                    Dyn Forcerport ACL Port     Status     
vodafone-trunk           sip.vodafone.co.uk                       N  No         A  5060     OK (0 ms)
```

**Status should be**: `OK (X ms)` (not UNREACHABLE)

---

### Step 8: Monitor SIP Registration

```bash
asterisk -r -x "sip show registry"
```

**Expected output**:

```
Host                                    Username       Refresh State                Reg.Exp
sip.vodafone.co.uk                      YOUR_USERNAME  3600    Registered           Yes
```

**State should be**: `Registered`

---

## Configuration Files

### `/etc/asterisk/sip.conf` (SIP Trunk)

```ini
[general]
context=default
allowoverlap=no
bindport=5060
bindaddr=0.0.0.0
srvlookup=yes
disallow=all
allow=ulaw
allow=alaw
allow=gsm

[vodafone-trunk]
type=trunk
host=sip.vodafone.co.uk
username=YOUR_VODAFONE_USERNAME
secret=YOUR_VODAFONE_PASSWORD
fromuser=YOUR_VODAFONE_USERNAME
fromdomain=sip.vodafone.co.uk
insecure=port,invite
context=incoming-calls
```

### `/etc/asterisk/extensions.conf` (Dialplan)

```ini
[incoming-calls]
; Welcome message
exten => s,1,Answer()
exten => s,n,Playback(welcome)
exten => s,n,AGI(agi://localhost:4573/call)
exten => s,n,Hangup()

; Transfer to live agent
exten => 0,1,Playback(transferring-to-agent)
exten => 0,n,Dial(SIP/LIVE_AGENT_NUMBER)
exten => 0,n,Hangup()

; Invalid input
exten => i,1,Playback(invalid-input)
exten => i,n,Goto(s,1)

; Timeout
exten => t,1,Playback(goodbye)
exten => t,n,Hangup()
```

---

## Call Flow Diagram

```
Incoming Call to +447999605080
        ↓
Vodafone SIP Trunk
        ↓
Asterisk (3.11.229.68:5060)
        ↓
[incoming-calls] context
        ↓
Answer call
        ↓
Play welcome message
        ↓
Route to Python AGI (localhost:4573)
        ↓
Python app handles booking flow
        ↓
Customer wants live agent?
        ↓
    YES → Transfer to LIVE_AGENT_NUMBER
    NO → Complete booking, save to database
        ↓
End call
```

---

## Testing Checklist

### Test 1: SIP Trunk Registration

```bash
asterisk -r -x "sip show registry"
```

- [ ] Status: `Registered`
- [ ] Refresh: `3600`
- [ ] Reg.Exp: `Yes`

### Test 2: SIP Peer Status

```bash
asterisk -r -x "sip show peers"
```

- [ ] Status: `OK (X ms)`
- [ ] Not: `UNREACHABLE`

### Test 3: Inbound Call

1. [ ] Call +447999605080 from mobile
2. [ ] Asterisk answers
3. [ ] Welcome message plays
4. [ ] Bot asks first question
5. [ ] You can respond

### Test 4: Live Agent Transfer

1. [ ] Call +447999605080
2. [ ] Say "I want to speak to someone"
3. [ ] Bot says "Transferring to agent"
4. [ ] Call transfers to live agent number
5. [ ] Live agent phone rings
6. [ ] Agent can answer

### Test 5: Call Logging

```bash
sudo tail -f /var/log/asterisk/messages
```

- [ ] Incoming call logged
- [ ] SIP registration logged
- [ ] Transfer logged

---

## Troubleshooting

### SIP Trunk Not Registering

**Problem**: Status shows `UNREACHABLE`

**Solutions**:
1. Check Vodafone credentials are correct
2. Verify SIP server address
3. Check firewall allows port 5060
4. Check network connectivity

```bash
# Test connectivity
ping sip.vodafone.co.uk

# Check firewall
sudo ufw status

# Allow SIP port
sudo ufw allow 5060/udp
```

### Incoming Calls Not Working

**Problem**: Call goes to voicemail or doesn't connect

**Solutions**:
1. Check `context=incoming-calls` is set in sip.conf
2. Verify extensions.conf has `[incoming-calls]` section
3. Check AGI server is running (localhost:4573)
4. Restart Asterisk

```bash
# Restart Asterisk
sudo systemctl restart asterisk

# Check logs
sudo tail -f /var/log/asterisk/messages
```

### Transfer Not Working

**Problem**: Transfer button doesn't work or call drops

**Solutions**:
1. Check live agent number is correct
2. Verify agent phone is on and reachable
3. Check dialplan has transfer extension (0)
4. Test with different transfer methods

```bash
# Check dialplan
asterisk -r -x "dialplan show incoming-calls"

# Enable SIP debug
asterisk -r -x "sip set debug on"
```

### Audio Issues

**Problem**: One-way audio or no audio

**Solutions**:
1. Check codec settings (ulaw, alaw, gsm)
2. Verify RTP ports are open (5000-5100)
3. Check NAT settings
4. Restart Asterisk

```bash
# Allow RTP ports
sudo ufw allow 5000:5100/udp

# Restart Asterisk
sudo systemctl restart asterisk
```

---

## Firewall Configuration

### Open Required Ports

```bash
# SIP port
sudo ufw allow 5060/udp

# RTP ports (audio)
sudo ufw allow 5000:5100/udp

# Verify
sudo ufw status
```

---

## Security Notes

⚠️ **Important**:

1. **Credentials**: Keep SIP credentials secure
   - Don't commit to version control
   - Don't share in emails
   - Use environment variables if possible

2. **Firewall**: Only allow necessary ports
   - SIP: 5060/udp
   - RTP: 5000-5100/udp
   - Restrict to known IPs if possible

3. **Monitoring**: Monitor for unauthorized access
   - Check SIP logs regularly
   - Monitor call logs
   - Set up alerts for failed registrations

---

## Next Steps

### After Configuration

1. **Test SIP trunk** (Task 1.4)
   - Make test calls
   - Verify booking flow
   - Verify transfer flow

2. **Monitor logs**
   - Check for errors
   - Verify calls are logged
   - Monitor SIP registration

3. **Optimize settings**
   - Adjust timeouts if needed
   - Configure voicemail
   - Set up call recording

---

## Configuration Summary

| Setting | Value |
|---------|-------|
| SIP Server | sip.vodafone.co.uk |
| SIP Port | 5060 |
| Username | YOUR_VODAFONE_USERNAME |
| Password | YOUR_VODAFONE_PASSWORD |
| Phone Number | +447999605080 |
| Context | incoming-calls |
| Live Agent Transfer | LIVE_AGENT_NUMBER |
| Codecs | ulaw, alaw, gsm |

---

## Commands Reference

```bash
# Restart Asterisk
sudo systemctl restart asterisk

# Check status
sudo systemctl status asterisk

# View SIP peers
asterisk -r -x "sip show peers"

# View SIP registry
asterisk -r -x "sip show registry"

# View dialplan
asterisk -r -x "dialplan show incoming-calls"

# Enable SIP debug
asterisk -r -x "sip set debug on"

# Disable SIP debug
asterisk -r -x "sip set debug off"

# View logs
sudo tail -f /var/log/asterisk/messages

# Reload configuration
asterisk -r -x "reload"
```

---

## Sign-Off

**Task 1.3: Configure Vodafone SIP trunk** - READY TO EXECUTE

**Status**: Awaiting Vodafone credentials and live agent phone number

**Next Action**: Provide credentials and proceed with configuration

---

**Report Generated**: May 12, 2026  
**Report Status**: READY FOR EXECUTION
