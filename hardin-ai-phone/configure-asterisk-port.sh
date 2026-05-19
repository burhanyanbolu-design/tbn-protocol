#!/bin/bash
# Configure Asterisk to listen on port 5080 (Kamailio takes 5060)

# Check if pjsip.conf exists, create if not
PJSIP_CONF="/etc/asterisk/pjsip.conf"

# Backup existing config
sudo cp "$PJSIP_CONF" "${PJSIP_CONF}.bak" 2>/dev/null

# Create PJSIP transport on port 5080
sudo bash -c "cat > /etc/asterisk/pjsip_hardin.conf << 'EOF'
; Hardin-AI Phone — Asterisk PJSIP Configuration
; Asterisk listens on port 5080, Kamailio on 5060

[transport-udp-5080]
type=transport
protocol=udp
bind=0.0.0.0:5080

[transport-tcp-5080]
type=transport
protocol=tcp
bind=0.0.0.0:5080

; Kamailio as a trusted peer (no auth needed from Kamailio)
[kamailio]
type=endpoint
transport=transport-udp-5080
context=from-kamailio
disallow=all
allow=alaw
allow=ulaw
allow=gsm
direct_media=no
trust_id_inbound=yes
trust_id_outbound=yes

[kamailio]
type=identify
endpoint=kamailio
match=127.0.0.1

[kamailio]
type=aor
max_contacts=1
contact=sip:127.0.0.1:5060

; Wholesale DID provider endpoint (to be configured with actual provider)
; [wholesale]
; type=endpoint
; transport=transport-udp-5080
; context=from-wholesale
; disallow=all
; allow=alaw
; allow=ulaw
; direct_media=no
EOF"

# Create dialplan for incoming calls from Kamailio
sudo bash -c "cat > /etc/asterisk/extensions_hardin.conf << 'EOF'
; Hardin-AI Phone — Asterisk Dialplan
; Handles calls routed from Kamailio

[from-kamailio]
; All inbound calls from Kamailio (from customers or wholesale DID)
exten => _X.,1,NoOp(Incoming call from Kamailio: ${CALLERID(num)} -> ${EXTEN})
 same => n,Answer()
 same => n,Wait(1)
 same => n,Playback(hello-world)
 same => n,AGI(agi://127.0.0.1:4573/booking)
 same => n,Hangup()

; Transfer to live agent
exten => transfer,1,NoOp(Transferring to live agent)
 same => n,Dial(SIP/+447740304061@kamailio,60,tT)
 same => n,Hangup()

[from-wholesale]
; Calls coming directly from wholesale DID provider
exten => _X.,1,NoOp(Incoming DID call: ${CALLERID(num)} -> ${EXTEN})
 same => n,Goto(from-kamailio,${EXTEN},1)

[outbound]
; Outbound calls (via wholesale provider)
exten => _X.,1,NoOp(Outbound call to ${EXTEN})
 same => n,Dial(PJSIP/${EXTEN}@wholesale,60)
 same => n,Hangup()
EOF"

# Include our config files in the main Asterisk config
if ! grep -q "pjsip_hardin.conf" /etc/asterisk/pjsip.conf 2>/dev/null; then
    echo '#include "pjsip_hardin.conf"' | sudo tee -a /etc/asterisk/pjsip.conf
fi

if ! grep -q "extensions_hardin.conf" /etc/asterisk/extensions.conf 2>/dev/null; then
    echo '#include "extensions_hardin.conf"' | sudo tee -a /etc/asterisk/extensions.conf
fi

# Restart Asterisk
sudo systemctl restart asterisk

echo ""
echo "=== Asterisk Configuration Complete ==="
echo "Asterisk SIP port: 5080"
echo "Kamailio SIP port: 5060 (public-facing)"
echo "Dialplan context: from-kamailio"
echo "Live agent transfer: +447740304061"
