#!/bin/bash
cat > /etc/nginx/sites-enabled/phone << 'EOF'
server {
    listen 80;
    server_name phone.hardinai.co.uk;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name phone.hardinai.co.uk;

    ssl_certificate /etc/letsencrypt/live/phone.hardinai.co.uk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phone.hardinai.co.uk/privkey.pem;

    # Password protect the dashboard
    auth_basic "Hardin-AI Phone Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:5006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check without auth (for monitoring)
    location /health {
        auth_basic off;
        proxy_pass http://127.0.0.1:5006;
    }
}
EOF

nginx -t && systemctl reload nginx && echo "Dashboard secured with auth"
