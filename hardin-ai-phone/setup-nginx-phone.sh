#!/bin/bash
cat > /etc/nginx/sites-enabled/phone << 'EOF'
server {
    listen 80;
    server_name phone.hardinai.co.uk;

    location / {
        proxy_pass http://127.0.0.1:5006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

nginx -t && systemctl reload nginx && echo "Nginx configured for phone.hardinai.co.uk"
