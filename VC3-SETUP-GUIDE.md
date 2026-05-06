# VC3 Trading Bot - Quick Setup Guide

## 🚀 One-Command Deployment

Run this on your server to deploy VC3:

```bash
cd /opt/tbn-protocol && sudo git pull origin main && sudo bash deploy/deploy-vc3.sh
```

The script will:
1. ✅ Clone the VC3 repository
2. ✅ Set up Python environment
3. ✅ Ask for your Alpaca API keys (or you can add them later)
4. ✅ Create systemd service
5. ✅ Start the trading bot

## 🔑 Getting Alpaca API Keys

1. Go to: https://app.alpaca.markets/
2. Sign up or log in
3. Go to **Paper Trading** dashboard (for testing) or **Live Trading** (for real money)
4. Click **"Generate API Keys"**
5. Copy both:
   - **API Key** (starts with PK...)
   - **Secret Key** (starts with SK...)

## 📝 What to Enter During Setup

When the script asks:
```
Enter your Alpaca API Key:
```
Paste your API Key (PK...)

```
Enter your Alpaca Secret Key:
```
Paste your Secret Key (SK...)

**OR** press Enter to skip and add them later by editing `/opt/vc3/.env`

## ✅ After Deployment

Check if it's running:
```bash
sudo systemctl status vc3
```

You should see:
- ✅ **Active: active (running)** in green
- ✅ Bot listening on port 5003

Visit your dashboard:
```
https://vc3.hardinai.co.uk
```

The status should change from **OFFLINE** to **ONLINE** 🟢

## 🔧 If You Need to Add/Update API Keys Later

```bash
sudo nano /opt/vc3/.env
```

Update these lines:
```
ALPACA_API_KEY=your_actual_key_here
ALPACA_SECRET_KEY=your_actual_secret_here
```

Save (Ctrl+O, Enter) and exit (Ctrl+X), then restart:
```bash
sudo systemctl restart vc3
```

## 📊 Useful Commands

```bash
# Check status
sudo systemctl status vc3

# View live logs
sudo journalctl -u vc3 -f

# View last 50 log lines
sudo journalctl -u vc3 -n 50

# Restart bot
sudo systemctl restart vc3

# Stop bot
sudo systemctl stop vc3

# Start bot
sudo systemctl start vc3
```

## ⏰ Trading Hours

The bot only trades during US market hours:
- **Monday - Friday**
- **9:30 AM - 4:00 PM** New York time

Outside these hours, the bot will show signals but won't execute trades.

## 🐛 Troubleshooting

### Bot shows OFFLINE
```bash
# Check if service is running
sudo systemctl status vc3

# Check logs for errors
sudo journalctl -u vc3 -n 50

# Restart the service
sudo systemctl restart vc3
```

### Port 5003 not listening
```bash
# Check what's using the port
sudo netstat -tlnp | grep 5003

# Check logs for startup errors
sudo journalctl -u vc3 -n 100
```

### API Key errors in logs
```bash
# Edit the .env file
sudo nano /opt/vc3/.env

# Make sure keys are correct (no quotes, no spaces)
# Then restart
sudo systemctl restart vc3
```

## 📞 Need Help?

Check the logs first:
```bash
sudo journalctl -u vc3 -n 100
```

The logs will show exactly what's wrong (API key issues, connection problems, etc.)
