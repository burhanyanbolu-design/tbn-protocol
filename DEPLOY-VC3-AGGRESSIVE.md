# 🚀 Deploy VC3 Aggressive Configuration

## ✅ Step 1: Files Pushed to GitHub

The following files have been pushed to GitHub:
- ✅ `.env.vc3.aggressive` - Aggressive configuration template
- ✅ `VC3-AGGRESSIVE-CONFIG.md` - Complete documentation
- ✅ `deploy/update-vc3-aggressive.sh` - Automated deployment script

## 🖥️ Step 2: Deploy to Server

### Option A: Automated Deployment (Recommended)

```bash
# SSH into server
ssh ubuntu@3.11.229.68

# Pull latest changes
cd /opt/tbn-protocol
sudo git pull origin main

# Run deployment script
sudo bash deploy/update-vc3-aggressive.sh
```

### Option B: Manual Deployment

```bash
# SSH into server
ssh ubuntu@3.11.229.68

# Pull latest changes
cd /opt/tbn-protocol
sudo git pull origin main

# Backup current config
sudo cp /opt/vc3/.env /opt/vc3/.env.backup.$(date +%Y%m%d_%H%M%S)

# Copy aggressive config
sudo cp .env.vc3.aggressive /opt/vc3/.env

# Update with your Alpaca API keys
sudo nano /opt/vc3/.env
# Find these lines and update:
# ALPACA_API_KEY=your_key_here
# ALPACA_SECRET_KEY=your_secret_here

# Save: Ctrl+O, Enter
# Exit: Ctrl+X

# Set permissions
sudo chown www-data:www-data /opt/vc3/.env
sudo chmod 600 /opt/vc3/.env

# Restart VC3
sudo systemctl restart vc3

# Check status
sudo systemctl status vc3

# Monitor logs
sudo journalctl -u vc3 -f
```

## 📊 Step 3: Verify Configuration

### Check if aggressive config is loaded:

```bash
ssh ubuntu@3.11.229.68 "sudo journalctl -u vc3 -n 50 | grep -i 'position\|profit\|aggressive'"
```

You should see:
```
Position size: $10,000
Take profit target: 20%
Stop loss: 8%
Strategy: AGGRESSIVE
```

### Check dashboard:

Visit: https://vc3.hardinai.co.uk

Should show:
- 🟢 Status: ONLINE
- 📊 Position Size: $10,000
- 🎯 Take Profit: 20%
- 🛑 Stop Loss: 8%

## 🎯 Expected Results

### Before (Current):
- Position Size: ~$500
- Take Profit: 2-5%
- Profit per trade: $16-$36 ❌

### After (Aggressive):
- Position Size: $10,000
- Take Profit: 20%
- Profit per trade: $1,500-$5,000 ✅

### Example Trade:
```
Stock: NIO
Entry: $5.00
Position: $10,000 = 2,000 shares
Take Profit: 20% = $6.00
Profit: 2,000 × $1.00 = $2,000 ✅
```

## ⚠️ Important Checks

### 1. Account Size
```bash
# Check your Alpaca account balance
# You need at least $50,000 for this configuration
```

### 2. Paper Trading First
```bash
# Make sure ALPACA_BASE_URL is set to paper trading:
# ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### 3. Monitor First Trades
```bash
# Watch live logs for first 5 trades
ssh ubuntu@3.11.229.68 "sudo journalctl -u vc3 -f"
```

## 🔧 Troubleshooting

### VC3 won't start:
```bash
# Check logs
ssh ubuntu@3.11.229.68 "sudo journalctl -u vc3 -n 100"

# Check if .env file exists
ssh ubuntu@3.11.229.68 "sudo ls -la /opt/vc3/.env"

# Verify API keys are set
ssh ubuntu@3.11.229.68 "sudo cat /opt/vc3/.env | grep ALPACA"
```

### Configuration not loading:
```bash
# Restart service
ssh ubuntu@3.11.229.68 "sudo systemctl restart vc3"

# Check if file has correct permissions
ssh ubuntu@3.11.229.68 "sudo ls -la /opt/vc3/.env"
# Should show: -rw------- 1 www-data www-data
```

### Still getting small trades:
```bash
# Verify configuration is actually loaded
ssh ubuntu@3.11.229.68 "sudo cat /opt/vc3/.env | grep POSITION_SIZE"
# Should show: POSITION_SIZE_DEFAULT=10000
```

## 📞 Quick Commands

```bash
# Check VC3 status
ssh ubuntu@3.11.229.68 "sudo systemctl status vc3"

# View live logs
ssh ubuntu@3.11.229.68 "sudo journalctl -u vc3 -f"

# Restart VC3
ssh ubuntu@3.11.229.68 "sudo systemctl restart vc3"

# Check configuration
ssh ubuntu@3.11.229.68 "sudo cat /opt/vc3/.env"

# View recent trades
ssh ubuntu@3.11.229.68 "sudo journalctl -u vc3 -n 100 | grep -i 'trade\|profit\|loss'"
```

## ✅ Deployment Checklist

- [ ] Files pushed to GitHub
- [ ] SSH into server
- [ ] Pull latest changes
- [ ] Backup current .env
- [ ] Copy aggressive config
- [ ] Update API keys
- [ ] Set permissions
- [ ] Restart VC3
- [ ] Check status (should be active)
- [ ] Verify config loaded
- [ ] Monitor first trade
- [ ] Check dashboard shows new settings

## 🎉 Success Indicators

You'll know it's working when:
1. ✅ VC3 service is active (green)
2. ✅ Logs show "Position size: $10,000"
3. ✅ Logs show "Take profit: 20%"
4. ✅ Dashboard shows ONLINE
5. ✅ First trade is $1,000+ profit (not $16-$36)

---

**Created:** May 9, 2026  
**Status:** ✅ Ready to Deploy  
**Expected Result:** $1,000-$5,000 profit per trade instead of $16-$36
