# Deploy Boomi integration to production server

Write-Host "Deploying Boomi integration..." -ForegroundColor Green
Write-Host ""

# SSH into server, pull latest code, and restart
$sshCommand = @"
cd /opt/tbn-protocol
git pull origin main
sudo systemctl restart tbn
sleep 3
curl -s https://tbn.hardinai.co.uk/api/boomi/health
"@

Write-Host "Pulling latest code and restarting service..." -ForegroundColor Cyan
ssh -i "c:\Users\Burhan Yanbolu\Desktop\tbn-protocol\aws-lightsail.pem" ubuntu@3.11.229.68 $sshCommand

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
