# TBN Infrastructure Demo - 2 Computer Setup

This demo shows TBN as the **infrastructure monopoly** for AI agent trust.

## 🎯 What This Demonstrates

**TBN's Position:**
- ✅ ONLY authority that can certify bots
- ✅ Companies don't build verification - they use TBN
- ✅ Bots get ONE certificate that works everywhere
- ✅ Network effect creates monopoly position

---

## 🖥️ Setup

### Computer 1: AWS Server (Company)
**Role:** Company providing data to certified bots only

**Location:** `3.11.229.68` (your AWS server)

**What it does:**
- Hosts a company website with `/tbn.json`
- Provides API endpoint with data
- Verifies bots using TBN infrastructure
- Logs all access attempts

### Computer 2: Your PC (Bot)
**Role:** Bot requesting data using TBN certificate

**What it does:**
- Registers with TBN to get certificate
- Requests data from company
- Presents TBN certificate for verification

---

## 📦 Installation

### On AWS Server (Computer 1):

```bash
cd /opt/tbn-protocol
git pull origin main

# Install demo dependencies
pip install -r requirements.txt

# Create demo directory
mkdir -p /var/www/demo-company
```

### On Your PC (Computer 2):

```bash
cd C:\Users\Burhan Yanbolu\Desktop\tbn-protocol
git pull origin main

# Install TBN client
pip install tbn-protocol

# Or use local version
pip install -e .
```

---

## 🚀 Running the Demo

### Option 1: Automated Demo (Single Computer)

Run the complete demo on one computer to see all scenarios:

```bash
python demo/tbn-infrastructure-demo.py
```

This shows:
1. ✅ Certified bot gets access
2. ❌ Uncertified bot gets blocked
3. 🌐 One certificate works across multiple companies

---

### Option 2: Real 2-Computer Demo

#### Step 1: Start Company Server (AWS)

```bash
cd /opt/tbn-protocol

# Run company server
python demo/company-server.py
```

This starts a Flask server on port 5010 that:
- Serves `/tbn.json`
- Provides `/api/data` endpoint
- Verifies bots using TBN

#### Step 2: Run Bot Client (Your PC)

```bash
cd C:\Users\Burhan Yanbolu\Desktop\tbn-protocol

# Run bot client
python demo/bot-client.py --company-url http://3.11.229.68:5010
```

This:
- Registers bot with TBN
- Gets certificate
- Requests data from company server
- Shows verification process

---

## 📊 What You'll See

### On Company Server (Computer 1):

```
🏢 [Acme Corp] Company Data Provider Started
📄 Published tbn.json at /tbn.json
🔍 Waiting for bot requests...

🔍 [Acme Corp] Verifying bot: tbn-bot-a1b2c3d4
   Checking with TBN infrastructure...
   ✅ Bot verified by TBN!
   📜 Certification level: COMMUNITY

✅ [Acme Corp] Access GRANTED to bot tbn-bot-a1b2c3d4
   Providing data...
```

### On Bot Client (Computer 2):

```
🤖 [DataBot] Registering with TBN infrastructure...
   ✅ Registered with TBN!
   🆔 Bot ID: tbn-bot-a1b2c3d4
   📜 Certificate issued by TBN

🤖 [DataBot] Requesting data from Acme Corp
   Presenting TBN certificate: tbn-bot-a1b2c3d4

✅ [DataBot] Data received!
   Data: {
     "company": "Acme Corp",
     "products": ["AI Tool A", "AI Tool B"],
     "pricing": {"basic": "$99/mo"}
   }
```

---

## 🎬 Demo Scenarios

### Scenario 1: Certified Bot ✅
- Bot registers with TBN
- Gets certificate
- Company verifies with TBN
- Access granted

### Scenario 2: Uncertified Bot ❌
- Fake bot tries to access
- No TBN certificate
- Company blocks access
- Shows TBN is required

### Scenario 3: Multiple Companies 🌐
- One bot, one TBN certificate
- Accesses 3 different companies
- Same certificate works everywhere
- Shows network effect

---

## 💡 Key Insights

### For Companies:
```
WITHOUT TBN:
❌ Build own bot verification system
❌ Maintain bot whitelist
❌ Handle security yourself
❌ Different standard for each company

WITH TBN:
✅ Just check TBN certificate
✅ TBN maintains the registry
✅ TBN handles security
✅ One standard across all companies
```

### For Bots:
```
WITHOUT TBN:
❌ Get credentials from each company
❌ Different auth for each API
❌ No trust between systems

WITH TBN:
✅ One certificate for all companies
✅ Standard authentication
✅ Trusted across the network
```

### For TBN:
```
MONOPOLY POSITION:
✅ Only authority that can certify bots
✅ Companies depend on TBN infrastructure
✅ Bots must use TBN to access companies
✅ Network effect: more companies → more bots → more value
```

---

## 📈 Business Model

### Revenue Streams:

1. **Bot Certification:**
   - Free: STANDARD level
   - $99/mo: COMMUNITY level
   - $499/mo: ENTERPRISE level

2. **Company API Access:**
   - Free: 1,000 verifications/month
   - $299/mo: 10,000 verifications/month
   - $999/mo: Unlimited verifications

3. **Enterprise:**
   - Custom certification levels
   - Private TBN nodes
   - SLA guarantees

---

## 🔐 Security Features

- ✅ RSA-2048 key pairs for bot identity
- ✅ SHA-256 fingerprints for bot IDs
- ✅ AES-256-GCM encrypted communication
- ✅ Public BICA registry on GitHub
- ✅ 3-tier certification system
- ✅ Automatic violation tracking

---

## 📞 Next Steps

1. **Run the demo** to see TBN in action
2. **Show to investors** - demonstrates infrastructure monopoly
3. **Onboard first company** - get them to publish tbn.json
4. **Onboard first bot** - get them to use TBN certificate
5. **Create network effect** - more companies → more bots → more value

---

## 🎥 Demo Video Script

**Opening:**
"This is TBN - the trust infrastructure for AI agents. Watch how it works..."

**Scene 1: Company Side**
"A company wants to provide data to bots, but only certified ones. They publish a tbn.json file and use TBN to verify bots."

**Scene 2: Bot Side**
"A bot wants to access the company's data. It registers with TBN and gets a certificate."

**Scene 3: The Exchange**
"The bot presents its TBN certificate. The company verifies it with TBN. Access granted!"

**Scene 4: Network Effect**
"Now the bot can access ANY company using TBN. One certificate, unlimited access. This is the power of infrastructure."

**Closing:**
"TBN - the only authority that can certify AI agents. The infrastructure layer everyone needs."

---

## 📧 Contact

Questions about the demo?  
burhan@hardinai.co.uk
