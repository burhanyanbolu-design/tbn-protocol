# Hardin Data Network - Command Reference
## Quick Commands for Managing the Data Network

---

## 🚀 Deploy New Bots

### Deploy Expansion Bots (UK Automotive + Master Plan):
```bash
chmod +x hardin-data-network/deploy-expansion-bots.sh
./hardin-data-network/deploy-expansion-bots.sh
```

### Deploy Individual Bot:
```bash
# Upload bot
scp -i aws-lightsail.pem hardin-data-network/bots/BotName.py ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/bots/

# Run bot
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "cd /opt/tbn-protocol/hardin-data-network && python3 bots/BotName.py"
```

---

## 📊 Check Statistics

### Quick Stats:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "/opt/tbn-protocol/hardin-data-network/stats.sh"
```

### Detailed Stats (after updating stats script):
```bash
# First, upload updated stats script
scp -i aws-lightsail.pem hardin-data-network/stats-updated.sh ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/stats.sh

# Then run it
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "/opt/tbn-protocol/hardin-data-network/stats.sh"
```

---

## 🗄️ Database Commands

### Connect to Database:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68
sudo -u postgres psql -d hardin_data_network
```

### Quick Query:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c 'SELECT COUNT(*) FROM restaurants;'"
```

### List All Tables:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c '\dt'"
```

### Check Table Size:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c 'SELECT pg_size_pretty(pg_total_relation_size(tablename::text)) FROM pg_tables WHERE schemaname = '\''public'\'';'"
```

---

## 🔧 API Commands

### Check API Status:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "curl http://localhost:5006/stats"
```

### Test API Endpoints:
```bash
# Stats
curl http://3.11.229.68:5006/stats

# Restaurants
curl http://3.11.229.68:5006/restaurants?city=London

# Retail
curl http://3.11.229.68:5006/retail?city=Manchester

# Lottery
curl http://3.11.229.68:5006/lottery?name=EuroMillions

# Football
curl http://3.11.229.68:5006/football?team=Arsenal

# Bots
curl http://3.11.229.68:5006/bots
```

### Restart API:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo systemctl restart hardin-data-api"
```

---

## 📁 File Management

### Upload File to Server:
```bash
scp -i aws-lightsail.pem local-file.py ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/
```

### Download File from Server:
```bash
scp -i aws-lightsail.pem ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/file.py ./
```

### List Files on Server:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "ls -lah /opt/tbn-protocol/hardin-data-network/bots/"
```

---

## 🤖 Bot Management

### List All Bots:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "ls -lah /opt/tbn-protocol/hardin-data-network/bots/"
```

### Run Specific Bot:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "cd /opt/tbn-protocol/hardin-data-network && python3 bots/BotName.py"
```

### Check Bot Output:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "cd /opt/tbn-protocol/hardin-data-network && python3 bots/BotName.py 2>&1 | tee bot-output.log"
```

---

## 🔍 Monitoring

### Check Disk Space:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "df -h"
```

### Check Database Size:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c 'SELECT pg_size_pretty(pg_database_size('\''hardin_data_network'\''));'"
```

### Check PostgreSQL Status:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo systemctl status postgresql"
```

### Check System Resources:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "top -bn1 | head -20"
```

---

## 🧹 Maintenance

### Backup Database:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres pg_dump hardin_data_network > /tmp/hardin_backup_$(date +%Y%m%d).sql"
```

### Download Backup:
```bash
scp -i aws-lightsail.pem ubuntu@3.11.229.68:/tmp/hardin_backup_*.sql ./backups/
```

### Clean Old Logs:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "find /opt/tbn-protocol/hardin-data-network -name '*.log' -mtime +7 -delete"
```

---

## 🐛 Debugging

### Check Bot Errors:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "cd /opt/tbn-protocol/hardin-data-network && python3 bots/BotName.py 2>&1"
```

### Check Database Connections:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c 'SELECT * FROM pg_stat_activity;'"
```

### Check PostgreSQL Logs:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo tail -f /var/log/postgresql/postgresql-*.log"
```

---

## 📊 Data Analysis

### Count All Data Points:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c 'SELECT SUM(count) FROM (SELECT COUNT(*) FROM retail_shops UNION ALL SELECT COUNT(*) FROM restaurants UNION ALL SELECT COUNT(*) FROM lottery_draws) AS counts;'"
```

### Top Restaurants by Rating:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c 'SELECT name, city, rating FROM restaurants ORDER BY rating DESC LIMIT 10;'"
```

### Latest Football Matches:
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "sudo -u postgres psql -d hardin_data_network -c 'SELECT home_team, away_team, score, date FROM football_matches ORDER BY date DESC LIMIT 10;'"
```

---

## 🚀 Quick Deploy Workflow

### Full Deployment (Recommended):
```bash
# 1. Deploy bots
chmod +x hardin-data-network/deploy-expansion-bots.sh
./hardin-data-network/deploy-expansion-bots.sh

# 2. Update stats script
scp -i aws-lightsail.pem hardin-data-network/stats-updated.sh ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/stats.sh

# 3. Check results
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "/opt/tbn-protocol/hardin-data-network/stats.sh"

# 4. Test API
curl http://3.11.229.68:5006/stats
```

---

## 🔑 SSH Shortcuts

### Add to ~/.ssh/config:
```
Host hardin-data
    HostName 3.11.229.68
    User ubuntu
    IdentityFile ~/path/to/aws-lightsail.pem
```

### Then use:
```bash
ssh hardin-data
scp file.py hardin-data:/opt/tbn-protocol/hardin-data-network/
```

---

## 📝 Common Tasks

### Add New Bot:
1. Create bot file locally: `hardin-data-network/bots/NewBot.py`
2. Upload: `scp -i aws-lightsail.pem hardin-data-network/bots/NewBot.py ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/bots/`
3. Make executable: `ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "chmod +x /opt/tbn-protocol/hardin-data-network/bots/NewBot.py"`
4. Run: `ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "cd /opt/tbn-protocol/hardin-data-network && python3 bots/NewBot.py"`

### Update Existing Bot:
1. Edit bot file locally
2. Upload: `scp -i aws-lightsail.pem hardin-data-network/bots/BotName.py ubuntu@3.11.229.68:/opt/tbn-protocol/hardin-data-network/bots/`
3. Run: `ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "cd /opt/tbn-protocol/hardin-data-network && python3 bots/BotName.py"`

### Check Data Growth:
```bash
# Run stats multiple times to see growth
ssh -i aws-lightsail.pem ubuntu@3.11.229.68 "/opt/tbn-protocol/hardin-data-network/stats.sh"
```

---

**Keep this file handy for quick reference!** 📚
