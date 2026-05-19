#!/bin/bash
# Configure Asterisk to connect to Zadarma as wholesale DID provider
# Zadarma credentials:
# Server: sip.zadarma.com
# Login: 517132
# Password: Lr85j2dxDg

# Update the PJSIP config to include Zadarma trunk
sudo bash -c 'cat > /etc/asterisk/pjsip_zadarma.conf << EOF
; Zadarma Wholesale DID Provider
; Provides UK phone numbers and PSTN connectivity

[zadarma-transport]
type=transport
protocol=udp
bind=0.0.0.0:5080

[zadarma-registration]
type=registration
transport=zadarma-transport
outbound_auth=zadarma-auth
server_uri=sip:sip.zadarma.com
client_uri=sip:517132@sip.zadarma.com
retry_interval=60
expiration=600

[zadarma-auth]
type=auth
auth_type=userpass
username=517132
password=Lr85j2dxDg

[zadarma-aor]
type=aor
contact=sip:sip.zadarma.com
qualify_frequency=60

[zadarma-endpoint]
type=endpoint
transport=zadarma-transport
context=from-zadarma
disallow=all
allow=alaw
allow=ulaw
outbound_auth=zadarma-auth
aors=zadarma-aor
from_user=517132
from_domain=sip.zadarma.com
direct_media=no

[zadarma-identify]
type=identify
endpoint=zadarma-endpoint
match=sip.zadarma.com
EOF'

# Update extensions to handle Zadarma inbound calls
sudo bash -c 'cat > /etc/asterisk/extensions_zadarma.conf << EOF
; Zadarma inbound call handling
[from-zadarma]
exten => _X.,1,NoOp(Incoming call from Zadarma DID)
 same => n,Answer()
 same => n,Wait(1)
 same => n,Playback(hello-world)
 same => n,Hangup()

; When AGI is ready, replace Playback with:
; same => n,AGI(agi://127.0.0.1:4573/booking)
EOF'

# Include in main configs if not already there
grep -q "pjsip_zadarma.conf" /etc/asterisk/pjsip.conf 2>/dev/null || echo '#include "pjsip_zadarma.conf"' | sudo tee -a /etc/asterisk/pjsip.conf
grep -q "extensions_zadarma.conf" /etc/asterisk/extensions.conf 2>/dev/null || echo '#include "extensions_zadarma.conf"' | sudo tee -a /etc/asterisk/extensions.conf

# Reload Asterisk
sudo asterisk -rx "core reload" 2>/dev/null || sudo systemctl restart asterisk

# Check registration status
sleep 3
echo ""
echo "=== Zadarma Configuration Complete ==="
echo "Server: sip.zadarma.com"
echo "Login: 517132"
echo ""
echo "Checking registration status..."
sudo asterisk -rx "pjsip show registrations" 2>/dev/null
