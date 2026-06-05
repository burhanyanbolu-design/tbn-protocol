# Session Context — 5 June 2026 (Landing Page Animation)

## What Was Done This Session

### ✅ TBN Handshake Animation — Built & Deployed to Landing Page
- Built a cinematic agent handshake animation through multiple iterations (v1 → v6)
- Two TBN-certified agents (green "Agent" + blue "Validator") walk from edges toward each other
- Arms extend from 3 o'clock / 9 o'clock positions (outer edge of circle)
- Handclasp forms in the middle with sparks and particle burst
- "✓ VERIFIED — TBN handshake complete" badge appears
- Agents walk back, animation loops

#### Key technical details:
- Built with pure HTML5 Canvas + SVG (no dependencies)
- Rotating SVG hash rings around each agent (TBN cert IDs, RSA-PSS references)
- Energy beam connecting agents during handshake
- Traveling data packets along the beam
- Particle burst on verification (green/gold/blue with gravity)
- Glowing neon agents against dark background
- Responsive (uses container width)

#### Files:
- `demo/tbn_agent_handshake.html` — v1 (original from external source)
- `demo/tbn_handshake_v4.html` — v4 (arms-only, stationary agents)
- `demo/tbn_handshake_v5.html` — v5 (combined: walk + arms)
- `demo/tbn_handshake_v6.html` — v6 FINAL (cinematic: glowing, particles, beam)
- `api/templates/tbn_landing.html` — Landing page with embedded compact animation

#### Landing page animation settings:
- Stage height: 150px (compact)
- Agent width: 90px
- Scene: 80px circles
- Face canvas: 48x48
- SVG rings: 80x80, 70% opacity
- Animation durations: WALK_IN:240, REACH:65, SHAKE:120, HOLD:150, RETRACT:55, WALK_BACK:240, PAUSE:90
- Ring rotation speed: outer 0.06 deg/frame, inner 0.03 deg/frame
- Agents start from edges (6px from sides), meet at center with 22px gap

### ✅ Server Status Confirmed
- tbn.hardinai.co.uk/ → Landing page with animation (LIVE)
- tbn.hardinai.co.uk/dashboard → Old dashboard (preserved)
- tbn.hardinai.co.uk/console → Admin console (unchanged)
- tbn.hardinai.co.uk/partner → Partner registration (unchanged)
- certify.hardinai.co.uk/ → Certify app (unchanged)

### ✅ Git Push
- Commit: a66f10d "Add TBN handshake animation to landing page hero section"
- Branch: feat/instagram-video-agent
- Pushed to GitHub ✓

---

## Server Info (confirmed)
- IP: 3.11.229.68
- SSH: ubuntu@3.11.229.68
- Key: .ssh_temp_key (in repo root)
- Service: `sudo systemctl restart tbn`
- Templates: /opt/tbn-protocol/api/templates/
- Landing page: /opt/tbn-protocol/api/templates/tbn_landing.html

## Current Site Architecture
| URL | What it serves |
|-----|---------------|
| tbn.hardinai.co.uk/ | Landing page (animation + SEO content) |
| tbn.hardinai.co.uk/dashboard | Network Dashboard (bot registration, guided tour) |
| tbn.hardinai.co.uk/console | Admin Console |
| tbn.hardinai.co.uk/partner | Partner Registration |
| certify.hardinai.co.uk/ | Certify app (video content certification) |
