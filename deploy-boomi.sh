#!/bin/bash
# Deploy Boomi integration to production server

echo "🚀 Deploying Boomi integration..."

# SSH into server, pull latest code, and restart
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 << 'EOF'
  echo "📥 Pulling latest code..."
  cd /opt/tbn-protocol
  git pull origin main
  
  echo "🔄 Restarting TBN service..."
  sudo systemctl restart tbn
  
  echo "⏳ Waiting for service to start..."
  sleep 3
  
  echo "✅ Deployment complete!"
  echo ""
  echo "Testing health check..."
  curl -s https://tbn.hardinai.co.uk/api/boomi/health | python3 -m json.tool
EOF

echo ""
echo "🎉 Boomi integration deployed!"
