# TBN 2-Computer Demo - Quick Start

## 🚀 Run the Demo in 5 Minutes

### Computer 1: AWS Server (Company)

```bash
# Pull latest code
cd /opt/tbn-protocol
sudo git pull origin main

# Install dependencies
sudo pip install flask flask-cors requests

# Start company server
python3 demo/company-server.py
```

**Server will start on port 5010**

---

### Computer 2: Your PC (Bot)

```bash
# Pull latest code
cd C:\Users\Burhan Yanbolu\Desktop\tbn-protocol
git pull origin main

# Install TBN
pip install tbn-protocol

# Run bot client
python demo/bot-client.py --company-url http://3.11.229.68:5010
```

---

## 🎬 What You'll See

### On Server (Company):
```
🏢 Acme Corp - Company Data Provider
📄 TBN Configuration published
🔍 Waiting for bot requests...

🔍 [Acme Corp] Verifying bot: tbn-bot-xxxxx
   Checking with TBN infrastructure...
   ✅ Bot verified by TBN!
   📜 Certification level: STANDARD

✅ [Acme Corp] Access GRANTED
   Providing data...
```

### On Your PC (Bot):
```
🤖 [DataCollectorBot] Registering with TBN...
   ✅ Registered!
   🆔 Bot ID: tbn-bot-xxxxx

🤖 Requesting data from Acme Corp
   Presenting TBN certificate...

✅ Data received!
   {
     "company": "Acme Corp",
     "products": [...]
   }
```

---

## 💡 What This Proves

✅ **TBN is the infrastructure layer**
- Company doesn't build verification
- They just check with TBN

✅ **TBN has monopoly position**
- Only TBN can certify bots
- Companies depend on TBN
- Bots need TBN to access companies

✅ **Network effect**
- More companies → More bots need TBN
- More bots → More companies use TBN
- Creates unstoppable growth

---

## 🎥 Perfect for Investors

This demo shows:
1. Real infrastructure in action
2. Clear monopoly position
3. Network effect potential
4. Practical use case

**Run time:** 2 minutes  
**Impact:** Massive

---

## 📞 Questions?

burhan@hardinai.co.uk
