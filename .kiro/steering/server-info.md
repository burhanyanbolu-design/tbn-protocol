# Hardin AI Solutions — Server & Project Info

## Server
- **Provider**: AWS Lightsail
- **IP**: 3.11.229.68
- **OS**: Ubuntu 22.04
- **SSH user**: ubuntu
- **Project root**: /opt/tbn-protocol

## Domains & Services

| Domain | Service | Port | Location |
|--------|---------|------|----------|
| hardinai.co.uk | Open WebUI (Docker) | 8080 | Docker container: hardin-ai |
| tbn.hardinai.co.uk | TBN Protocol (Flask/Gunicorn) | 5004 | /opt/tbn-protocol |
| blog.hardinai.co.uk | Static blog (Nginx) | 80/443 | /var/www/blog |
| lgmd.hardinai.co.uk | LGMD Research Agent | unknown | /home/ubuntu/lgmd-research-agent |
| ai.hardinai.co.uk | AI service | unknown | unknown |

## Nginx
- Config files: /etc/nginx/sites-enabled/
- Key configs: hardinai, tbn, lgmd.hardinai.co.uk, video-cv, vc3, marketplace, gobybilly

## TBN Protocol
- Location: /opt/tbn-protocol
- Service: sudo systemctl restart tbn
- Dashboard: https://tbn.hardinai.co.uk
- Dashboard file: /opt/tbn-protocol/api/templates/dashboard.html
- Google Analytics: G-EF6RKG8KY2
- License: AGPL-3.0

## Docker Containers
- hardin-ai: Open WebUI on port 8080 (hardinai.co.uk)
- video-cv-redis: Redis on port 6379
- video-cv-postgres: PostgreSQL on port 5432

## Static Files
- hardinai.co.uk static: /home/ubuntu/hardinai.co.uk/
- Files: index.html, robots.txt, sitemap.xml, startup-loan/, team/

## Other Services Running
- research.service: SmartTrader-AI Research
- smarttrader.service: SmartTrader-AI Strategy
- stocktrader.service: Stock Trader App
- video-cv-api.service: Video CV API
- tbn.service: TBN Protocol

## PyPI Package
- Package: tbn-protocol
- Version: 0.1.0
- URL: https://pypi.org/project/tbn-protocol/0.1.0/
- Install: pip install tbn-protocol
- Published: May 3, 2026

## Google Analytics
- Measurement ID: G-EF6RKG8KY2
- Registered domains: lgmd.hardinai.co.uk, lgmd.hardinai.co.uk/patient
- Added to: tbn.hardinai.co.uk dashboard

## Company Info
- Company: Hardin Enterprises Ltd (trading as Hardin AI Solutions)
- Founder: Burhan Yanbolu
- Email: burhan@hardinai.co.uk / info@hardinai.co.uk
- GitHub: https://github.com/burhanyanbolu-design/tbn-protocol
- License: AGPL-3.0 with commercial licensing

## Key Projects
1. **TBN Protocol** - Trust infrastructure for AI agents (main focus)
2. **Hardin AI Search** - AI search engine (143 users, proof of concept)
3. **LGMD Research Agent** - Medical research tool
4. **Video CV** - Video CV platform
5. **SmartTrader** - AI trading system

## YC Application
- Applied to YC Summer 2026
- Main focus: TBN Protocol
- Demo video: https://drive.google.com/file/d/1SfLMFRSgrhx1lHDQc-pKDOCtI5LsH3Y8/view
- Live demo: https://tbn.hardinai.co.uk
