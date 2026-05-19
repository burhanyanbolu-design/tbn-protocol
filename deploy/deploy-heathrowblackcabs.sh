#!/bin/bash
# Deploy heathrowblackcabs to server
# Run from: /opt/tbn-protocol on the server, or locally with ssh

SERVER="ubuntu@3.11.229.68"
PEM="aws-lightsail.pem"
REMOTE_DIR="/var/www/heathrowblackcabs"
LOCAL_DIR="heathrowblackcabs"

echo "=== Creating remote directory ==="
ssh -i "$PEM" "$SERVER" "sudo mkdir -p $REMOTE_DIR && sudo chown ubuntu:ubuntu $REMOTE_DIR"

echo "=== Copying files ==="
scp -i "$PEM" "$LOCAL_DIR/index-saas.html" "$SERVER:$REMOTE_DIR/index.html"
scp -i "$PEM" "$LOCAL_DIR/balckcab.jpg" "$SERVER:$REMOTE_DIR/"
scp -i "$PEM" "$LOCAL_DIR/blackcab-front.jpg" "$SERVER:$REMOTE_DIR/"
scp -i "$PEM" "$LOCAL_DIR/blackcab-trafalgar.jpg" "$SERVER:$REMOTE_DIR/"
scp -i "$PEM" "$LOCAL_DIR/blackcabs2.jpg" "$SERVER:$REMOTE_DIR/"

echo "=== Setting up Nginx ==="
ssh -i "$PEM" "$SERVER" "sudo tee /etc/nginx/sites-available/heathrowblackcabs > /dev/null << 'EOF'
server {
    listen 80;
    server_name heathrowblackcabs.co.uk www.heathrowblackcabs.co.uk;
    root /var/www/heathrowblackcabs;
    index index.html;
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF"

echo "=== Enabling site ==="
ssh -i "$PEM" "$SERVER" "sudo ln -sf /etc/nginx/sites-available/heathrowblackcabs /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx"

echo "=== Setting up SSL ==="
ssh -i "$PEM" "$SERVER" "sudo certbot --nginx -d heathrowblackcabs.co.uk -d www.heathrowblackcabs.co.uk --non-interactive --agree-tos -m info@heathrowblackcabs.co.uk"

echo "=== Done! Site live at https://heathrowblackcabs.co.uk ==="
