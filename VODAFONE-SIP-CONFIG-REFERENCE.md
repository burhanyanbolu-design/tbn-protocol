# 📞 Vodafone UK SIP Configuration Reference

**Source**: https://github.com/mouldybread/VodafoneUKVOIPConfig  
**Date**: May 12, 2026

---

## Key Vodafone SIP Settings

### Primary SIP Server
```
resvoip.vodafone.co.uk
```

### SIP Port
```
5065 (Vodafone uses non-standard port)
```

### RTP Port
```
10000 (base port, range 10000-32767)
```

### DNS Servers (CRITICAL)
```
Primary DNS: 90.255.255.91
Secondary DNS: 90.255.255.255
```

⚠️ **IMPORTANT**: Your device MUST use Vodafone DNS servers to resolve SRV records. This cannot be set on the phone - must be set via DHCP.

### SIP User-Agent (CRITICAL)
```
Vox 3.0
```

⚠️ **IMPORTANT**: Vodafone requires this specific User-Agent string. Without it, registration will fail.

---

## What You Need from Vodafone

When you contact Vodafone, ask for:

1. **SIP Username** (authenticate ID)
2. **SIP Password** (authenticate password)
3. **Outbound Proxy** (may be same as primary server)
4. **SIP Server Address** (should be `resvoip.vodafone.co.uk`)

---

## Asterisk Configuration

### SIP Trunk Configuration

**File**: `/etc/asterisk/sip.conf`

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
host=resvoip.vodafone.co.uk
port=5065
username=YOUR_SIP_USERNAME
secret=YOUR_SIP_PASSWORD
fromuser=YOUR_SIP_USERNAME
fromdomain=resvoip.vodafone.co.uk
insecure=port,invite
context=incoming-calls
useragent=Vox 3.0
```

### Key Settings Explained

| Setting | Value | Reason |
|---------|-------|--------|
| `host` | `resvoip.vodafone.co.uk` | Vodafone's primary SIP server |
| `port` | `5065` | Vodafone uses non-standard port |
| `useragent` | `Vox 3.0` | Vodafone requires this specific string |
| `srvlookup` | `yes` | Enable SRV record lookup |
| `insecure` | `port,invite` | Allow non-standard port |

---

## Dialplan Configuration

**File**: `/etc/asterisk/extensions.conf`

```ini
[incoming-calls]
; Incoming calls from Vodafone SIP trunk
exten => s,1,Answer()
exten => s,n,Playback(welcome)
exten => s,n,AGI(agi://localhost:4573/call)
exten => s,n,Hangup()

; Transfer to live agent (press 0 or say "agent")
exten => 0,1,Playback(transferring-to-agent)
exten => 0,n,Dial(SIP/+447740304061)
exten => 0,n,Hangup()

; Fallback for unrecognized input
exten => i,1,Playback(invalid-input)
exten => i,n,Goto(s,1)
```

---

## Network Configuration (OPNSense/PFSense)

### Firewall Rules

**For VOIP to work through NAT, you need**:

1. **Outbound NAT Rule** (disable source port rewriting)
   - Source: Your phone's IP
   - Ports: 5065 (SIP) + 10000-32767 (RTP)
   - Static Port: YES

2. **Firewall Rules**
   - Allow outbound TCP/UDP on port 5065
   - Allow outbound UDP on ports 10000-32767

### DNS Configuration

**DHCP Server Settings**:
- Primary DNS: `90.255.255.91`
- Secondary DNS: `90.255.255.255`

This ensures your Asterisk server gets Vodafone DNS for SRV record resolution.

---

## Testing Vodafone Connection

### Check SIP Registration

```bash
# SSH into Asterisk server
ssh -i .\.ssh_temp_key ubuntu@3.11.229.68

# Check SIP peers
asterisk -r -x "sip show peers"

# Expected output:
# Name/username             Host                    Dyn Forcerport ACL Port     Status     
# vodafone-trunk           resvoip.vodafone.co.uk   N  No         A  5065     OK (0 ms)
```

### Check SIP Registry

```bash
asterisk -r -x "sip show registry"

# Expected output:
# Host                                    Username       Refresh State                Reg.Exp
# resvoip.vodafone.co.uk                  YOUR_USERNAME  3600    Registered           Yes
```

### Enable SIP Debug

```bash
asterisk -r -x "sip set debug on"

# Monitor logs
sudo tail -f /var/log/asterisk/messages
```

---

## Important Notes

### 1. SIP User-Agent is Critical
Vodafone's system specifically checks for `Vox 3.0` user agent. Without this, registration will fail.

### 2. DNS Must Use Vodafone Servers
Your Asterisk server must use Vodafone's DNS servers (90.255.255.91 and 90.255.255.255) to resolve SRV records. This is not optional.

### 3. Port 5065 is Non-Standard
Vodafone uses port 5065 instead of the standard SIP port 5060. Make sure your firewall allows this.

### 4. RTP Port Range
RTP uses UDP ports 10000-32767. Ensure your firewall allows outbound UDP on this range.

### 5. Credentials are Sensitive
- You cannot change your SIP credentials
- If compromised, calls will be billed to your account
- Guard them carefully

---

## Troubleshooting

### SIP Registration Fails

**Check**:
1. Username and password are correct
2. SIP server is `resvoip.vodafone.co.uk`
3. SIP port is `5065`
4. User-Agent is `Vox 3.0`
5. Firewall allows port 5065
6. DNS is set to Vodafone servers

### No Audio or One-Way Audio

**Check**:
1. RTP ports (10000-32767) are open
2. Firewall NAT rules disable source port rewriting
3. Outbound NAT is configured correctly
4. No other device is using RTP ports

### Incoming Calls Don't Work

**Check**:
1. SIP registration shows "Registered"
2. Dialplan has `[incoming-calls]` context
3. SIP trunk has `context=incoming-calls`
4. Asterisk is listening on port 5060

---

## Reference Links

- **GitHub**: https://github.com/mouldybread/VodafoneUKVOIPConfig
- **Asterisk Config**: https://github.com/clayface/VF-UK-Asterisk-config
- **Vodafone Forum**: https://forum.vodafone.co.uk/ (now closed)

---

## Next Steps

1. **Contact Vodafone** for your SIP credentials
2. **Provide credentials** to Kiro
3. **Configure Asterisk** with settings above
4. **Test SIP registration**
5. **Test incoming calls**

---

**Status**: CONFIGURATION REFERENCE READY  
**Next Action**: Get SIP credentials from Vodafone and provide to Kiro
