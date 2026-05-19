# Quick Deploy Guide
## Deploy Expansion Bots in 3 Commands

---

## 🚀 One-Command Deployment

```bash
chmod +x hardin-data-network/deploy-expansion-bots.sh && ./hardin-data-network/deploy-expansion-bots.sh
```

This will:
1. Upload UKAutomotiveBot.py to server
2. Upload MasterPlanComplete.py to server
3. Run both bots
4. Show updated statistics

**Expected Time:** 2-3 minutes
**Expected Result:** +9,442 data points (total: 11,442)

---

## 📊 What Gets Added

### UK Automotive Bot (3,020 data points):
- Car manufacturing data (140 records)
- Car sales data (960 records)
- Car import data (960 records)
- Car export data (960 records)

### Master Plan Bot (6,422 data points):
- Government statistics (92 records)
- Currency exchange rates (1,700 records)
- Commodity prices (1,700 records)
- Trade data (2,880 records)
- Books (30 records)
- Geography (20 records)

---

## ✅ Verification

After deployment, check:

```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "/opt/tbn-protocol/hardin-data-network/stats.sh"
```

You should see:
- **Total Data Points:** 11,442
- **New Categories:** Car Manufacturing, Car Sales, Car Imports, Car Exports, Gov Statistics, Currency Rates, Commodities, Trade Data, Books, Geography

---

## 🔄 Update Stats Script (Optional)

To get detailed breakdown of all categories:

```bash
scp -i aws-lightsail.pem hardin-data-network/stats-updated.sh ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/stats.sh
```

---

## 🎯 Progress

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Data Points | 2,000 | 11,442 | +9,442 |
| Categories | 17 | 24 | +7 |
| Bots | 20 | 22 | +2 |
| Week 1 Goal | 1,000 | 11,442 | 1,144% ✅ |
| Month 1 Goal | 50,000 | 11,442 | 23% 🔄 |

---

## 🚨 Troubleshooting

**If SSH fails:**
```bash
# Check if key has correct permissions
chmod 400 aws-lightsail.pem
```

**If bot fails:**
```bash
# SSH into server and run manually
ssh -i aws-lightsail.pem ubuntu@3.11.229.68
cd /opt/tbn-protocol/hardin-data-network
python3 bots/UKAutomotiveBot.py
python3 bots/MasterPlanComplete.py
```

**If database connection fails:**
```bash
# Check PostgreSQL is running
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo systemctl status postgresql"
```

---

## 📝 Files Created

Local files:
- `hardin-data-network/bots/UKAutomotiveBot.py`
- `hardin-data-network/bots/MasterPlanComplete.py`
- `hardin-data-network/deploy-expansion-bots.sh`
- `hardin-data-network/stats-updated.sh`
- `hardin-data-network/EXPANSION-SUMMARY.md`
- `hardin-data-network/QUICK-DEPLOY.md`

Server files (after deployment):
- `/opt/tbn-protocol/hardin-data-network/bots/UKAutomotiveBot.py`
- `/opt/tbn-protocol/hardin-data-network/bots/MasterPlanComplete.py`

---

**Ready to deploy? Run the command above!** 🚀
