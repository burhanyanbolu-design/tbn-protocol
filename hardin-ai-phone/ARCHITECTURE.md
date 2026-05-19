# 🏗️ Hardin-AI Phone — Technical Architecture

**Project**: Hardin-AI Phone  
**Date**: May 12, 2026  
**Version**: 1.0.0

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CUSTOMER WEBSITE                            │
│  (Shopify, WordPress, custom site)                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Hardin-AI Phone Plugin/Widget                            │  │
│  │  ├─ Booking form                                          │  │
│  │  ├─ Call handler                                          │  │
│  │  └─ Status dashboard                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                          ↓ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                  HARDIN-AI PHONE CORE                           │
│  (Hosted on Ubuntu VPS or customer's server)                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Nginx (Reverse Proxy)                                  │   │
│  │  ├─ SSL/TLS termination                                 │   │
│  │  ├─ Load balancing                                      │   │
│  │  └─ Static file serving                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Asterisk/FreePBX (Phone System)                        │   │
│  │  ├─ SIP trunk connection                                │   │
│  │  ├─ Call routing                                        │   │
│  │  ├─ Audio handling                                      │   │
│  │  ├─ Call recording (optional)                           │   │
│  │  └─ AGI interface to Python                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓ AGI                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Python FastAPI (Application Logic)                     │   │
│  │  ├─ /api/call/start — Start new call                    │   │
│  │  ├─ /api/call/answer — Handle customer response         │   │
│  │  ├─ /api/call/transfer — Transfer to human              │   │
│  │  ├─ /api/booking/save — Save booking                    │   │
│  │  ├─ /api/booking/list — List bookings                   │   │
│  │  └─ /api/admin/* — Admin endpoints                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Speech Processing                                      │   │
│  │  ├─ faster-whisper (speech-to-text)                     │   │
│  │  └─ Piper TTS (text-to-speech)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  TBN Bot Integration                                    │   │
│  │  ├─ Bot selection                                       │   │
│  │  ├─ Certification verification                          │   │
│  │  ├─ Personality injection                               │   │
│  │  └─ Response generation                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Database (SQLite or PostgreSQL)                        │   │
│  │  ├─ Bookings table                                      │   │
│  │  ├─ Call logs table                                     │   │
│  │  ├─ Customers table                                     │   │
│  │  └─ Settings table                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                          ↓ SIP
┌─────────────────────────────────────────────────────────────────┐
│              CUSTOMER PHONE LINE                                │
│  (Vodafone, BT, Plusnet SIP trunk)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Asterisk/FreePBX (Phone System)

**Purpose**: Handle phone calls, SIP connections, audio routing

**Key components**:
- **SIP Trunk**: Connects to customer's phone provider
- **Dialplan**: Routes calls to Python app
- **AGI (Asterisk Gateway Interface)**: Communicates with Python
- **Audio Processing**: Records/plays audio
- **Call Recording**: Optional call recording

**Configuration**:
```ini
; /etc/asterisk/extensions.conf
[incoming-calls]
exten => s,1,Answer()
exten => s,n,AGI(agi://localhost:4573/call)
exten => s,n,Hangup()

; /etc/asterisk/sip.conf
[vodafone-trunk]
type=trunk
host=sip.vodafone.co.uk
username=YOUR_USERNAME
secret=YOUR_PASSWORD
```

**Responsibilities**:
- Accept inbound SIP calls
- Route to Python app via AGI
- Handle audio I/O
- Record calls (optional)
- Transfer calls to human agents

---

### 2. Python FastAPI (Application Logic)

**Purpose**: Handle booking logic, bot integration, database operations

**Key endpoints**:

#### Call Management
```python
POST /api/call/start
# Start new call
# Input: caller_number, phone_number
# Output: session_id, first_question

POST /api/call/answer
# Handle customer response
# Input: session_id, user_text
# Output: next_question or booking_complete

POST /api/call/transfer
# Transfer to human
# Input: session_id, reason
# Output: transfer_status
```

#### Booking Management
```python
POST /api/booking/save
# Save booking to database
# Input: booking_data
# Output: booking_id, confirmation

GET /api/booking/list
# List all bookings
# Input: filters (date, status, etc.)
# Output: bookings array

GET /api/booking/{booking_id}
# Get booking details
# Input: booking_id
# Output: booking_data
```

#### Admin
```python
GET /api/admin/dashboard
# Get dashboard data
# Output: stats, recent bookings, call logs

GET /api/admin/analytics
# Get analytics
# Input: date_range
# Output: metrics, charts

POST /api/admin/settings
# Update settings
# Input: settings_data
# Output: success/error
```

**Architecture**:
```
FastAPI app
├── routers/
│   ├── calls.py (call handling)
│   ├── bookings.py (booking management)
│   ├── admin.py (admin endpoints)
│   └── webhooks.py (plugin webhooks)
├── services/
│   ├── booking_service.py (booking logic)
│   ├── bot_service.py (TBN bot integration)
│   ├── speech_service.py (speech processing)
│   └── database_service.py (database operations)
├── models/
│   ├── booking.py (booking data model)
│   ├── call.py (call data model)
│   └── customer.py (customer data model)
└── utils/
    ├── validators.py (input validation)
    ├── formatters.py (response formatting)
    └── logger.py (logging)
```

---

### 3. Speech Processing

#### Speech-to-Text (faster-whisper)

**Purpose**: Convert customer speech to text

**Flow**:
```
Asterisk audio stream
        ↓
faster-whisper
        ↓
Transcribed text
        ↓
Python app
```

**Implementation**:
```python
import whisper

model = whisper.load_model("base")

def transcribe_audio(audio_file):
    result = model.transcribe(audio_file)
    return result["text"]
```

**Configuration**:
- Model: "base" (good balance of speed/accuracy)
- Language: English
- Confidence threshold: 0.5

---

#### Text-to-Speech (Piper)

**Purpose**: Convert bot responses to speech

**Flow**:
```
Bot response text
        ↓
Piper TTS
        ↓
Audio file
        ↓
Asterisk plays to customer
```

**Implementation**:
```python
import subprocess

def text_to_speech(text, voice="en_US-ryan-medium"):
    subprocess.run([
        "piper",
        "--model", voice,
        "--output_file", "response.wav"
    ], input=text.encode())
    return "response.wav"
```

**Configuration**:
- Voice: "en_US-ryan-medium" (professional male voice)
- Speed: 1.0 (normal)
- Pitch: 1.0 (normal)

---

### 4. TBN Bot Integration

**Purpose**: Select and use certified TBN bots

**Flow**:
```
Customer calls
        ↓
Select TBN bot
        ↓
Verify certification
        ↓
Inject personality
        ↓
Generate responses
        ↓
Speak to customer
```

**Implementation**:
```python
from tbn.bots import SearchBot, ValidatorBot
from tbn.certification import CertificationAuthority

class BotService:
    def __init__(self):
        self.ca = CertificationAuthority()
        self.bots = {}
    
    def select_bot(self, business_type):
        # Select appropriate bot for business
        if business_type == "taxi":
            return self.get_certified_bot("taxi-booking-bot")
        elif business_type == "restaurant":
            return self.get_certified_bot("restaurant-booking-bot")
    
    def get_certified_bot(self, bot_id):
        # Verify bot is certified
        cert = self.ca.get_cert(bot_id)
        if not cert or not cert.valid:
            raise ValueError(f"Bot not certified: {bot_id}")
        return self.bots[bot_id]
    
    def generate_response(self, bot, user_input):
        # Generate response using bot
        response = bot.handle_request(user_input)
        return response
```

---

### 5. Database Schema

#### Bookings Table
```sql
CREATE TABLE bookings (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    caller_number TEXT,
    name TEXT,
    pickup TEXT,
    destination TEXT,
    date TEXT,
    time TEXT,
    passengers INTEGER,
    luggage TEXT,
    flight_number TEXT,
    callback_number TEXT,
    status TEXT,
    bot_id TEXT,
    call_duration INTEGER,
    booking_reference TEXT,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);
```

#### Call Logs Table
```sql
CREATE TABLE call_logs (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    caller_number TEXT,
    duration INTEGER,
    status TEXT,
    bot_id TEXT,
    transfer_reason TEXT,
    audio_file TEXT,
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);
```

#### Customers Table
```sql
CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE,
    name TEXT,
    email TEXT,
    created_at TIMESTAMP,
    last_booking TIMESTAMP,
    total_bookings INTEGER
);
```

#### Settings Table
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);
```

---

## Call Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CALL FLOW                                    │
└─────────────────────────────────────────────────────────────────┘

1. Customer calls +447999605080
   ↓
2. Vodafone routes to SIP trunk
   ↓
3. Asterisk receives call
   ├─ Answer call
   ├─ Play greeting
   └─ Connect to AGI
   ↓
4. Python app receives call
   ├─ Create session
   ├─ Select TBN bot
   └─ Generate first question
   ↓
5. Asterisk plays question
   ├─ "What is your name?"
   └─ Record customer response
   ↓
6. Python app processes response
   ├─ Transcribe audio (faster-whisper)
   ├─ Validate response
   └─ Generate next question
   ↓
7. Repeat steps 5-6 for each question
   ├─ Pickup location
   ├─ Destination
   ├─ Date
   ├─ Time
   ├─ Passengers
   ├─ Luggage
   ├─ Flight number
   └─ Callback number
   ↓
8. Confirmation
   ├─ Read back all details
   ├─ Ask for confirmation
   └─ Record response
   ↓
9. Save booking
   ├─ Insert into database
   ├─ Generate booking reference
   └─ Provide reference to customer
   ↓
10. End call
    ├─ Play thank you message
    ├─ Hang up
    └─ Log call
```

---

## Deployment Architecture

### Managed Service Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    HARDIN-AI SERVERS                            │
│  (AWS/DigitalOcean/Linode)                                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Load Balancer (Nginx)                                  │   │
│  │  ├─ Distribute traffic                                  │   │
│  │  ├─ SSL/TLS termination                                 │   │
│  │  └─ Rate limiting                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Application Servers (Python FastAPI)                   │   │
│  │  ├─ Server 1                                            │   │
│  │  ├─ Server 2                                            │   │
│  │  └─ Server 3                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Asterisk Servers (Phone System)                        │   │
│  │  ├─ Server 1 (Vodafone trunk)                           │   │
│  │  ├─ Server 2 (BT trunk)                                 │   │
│  │  └─ Server 3 (Plusnet trunk)                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Database (PostgreSQL)                                  │   │
│  │  ├─ Primary                                             │   │
│  │  └─ Replica (backup)                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Cache (Redis)                                          │   │
│  │  ├─ Session cache                                       │   │
│  │  └─ Response cache                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Storage (S3)                                           │   │
│  │  ├─ Call recordings                                     │   │
│  │  └─ Audio files                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Self-Hosted Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER SERVER                              │
│  (Ubuntu VPS)                                                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Docker Container 1: Asterisk                           │   │
│  │  ├─ SIP trunk connection                                │   │
│  │  ├─ Call routing                                        │   │
│  │  └─ AGI interface                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Docker Container 2: Python FastAPI                     │   │
│  │  ├─ Application logic                                   │   │
│  │  ├─ Booking management                                  │   │
│  │  └─ Admin dashboard                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Docker Container 3: SQLite Database                    │   │
│  │  ├─ Bookings                                            │   │
│  │  ├─ Call logs                                           │   │
│  │  └─ Customers                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Docker Container 4: Nginx                              │   │
│  │  ├─ Reverse proxy                                       │   │
│  │  ├─ SSL/TLS                                             │   │
│  │  └─ Static files                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Phone System** | Asterisk | 20+ | Handle phone calls |
| **Phone UI** | FreePBX | 16+ | Asterisk management |
| **Application** | Python | 3.9+ | Business logic |
| **Web Framework** | FastAPI | 0.100+ | REST API |
| **Database** | SQLite/PostgreSQL | Latest | Data storage |
| **Speech-to-Text** | faster-whisper | Latest | Audio transcription |
| **Text-to-Speech** | Piper | Latest | Audio generation |
| **Web Server** | Nginx | 1.24+ | Reverse proxy |
| **Containerization** | Docker | 24+ | Deployment |
| **OS** | Ubuntu | 22.04 LTS | Server OS |

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
└─────────────────────────────────────────────────────────────────┘

1. Network Security
   ├─ Firewall (UFW)
   ├─ VPN (optional)
   └─ DDoS protection

2. Transport Security
   ├─ HTTPS/TLS 1.3
   ├─ SIP over TLS
   └─ Encrypted database connections

3. Application Security
   ├─ Input validation
   ├─ SQL injection prevention
   ├─ CSRF protection
   └─ Rate limiting

4. Data Security
   ├─ Encryption at rest
   ├─ Encryption in transit
   ├─ Secure key management
   └─ Data backup

5. Access Control
   ├─ API authentication (JWT)
   ├─ User authentication (password)
   ├─ Role-based access control
   └─ Audit logging
```

---

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING STACK                             │
└─────────────────────────────────────────────────────────────────┘

1. Metrics
   ├─ Prometheus (metrics collection)
   ├─ Grafana (visualization)
   └─ Custom metrics (calls, bookings, etc.)

2. Logging
   ├─ ELK Stack (Elasticsearch, Logstash, Kibana)
   ├─ Application logs
   ├─ System logs
   └─ Call logs

3. Alerting
   ├─ Prometheus Alertmanager
   ├─ Email alerts
   ├─ SMS alerts
   └─ Slack integration

4. Health Checks
   ├─ API health endpoint
   ├─ Database health
   ├─ Asterisk health
   └─ Disk space monitoring
```

---

## Scalability Strategy

### Horizontal Scaling

```
Load Balancer
├─ Application Server 1
├─ Application Server 2
├─ Application Server 3
└─ Application Server N

Database
├─ Primary (write)
└─ Replicas (read)
```

### Vertical Scaling

- Increase CPU cores
- Increase RAM
- Increase disk space
- Upgrade network bandwidth

### Database Scaling

- Connection pooling
- Query optimization
- Caching layer (Redis)
- Database sharding (if needed)

---

## Disaster Recovery

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISASTER RECOVERY                            │
└─────────────────────────────────────────────────────────────────┘

1. Backup Strategy
   ├─ Daily database backups
   ├─ Weekly full backups
   ├─ Monthly archive backups
   └─ Offsite backup storage

2. Recovery Plan
   ├─ RTO (Recovery Time Objective): 1 hour
   ├─ RPO (Recovery Point Objective): 1 hour
   ├─ Failover to backup server
   └─ Data restoration procedure

3. Testing
   ├─ Monthly backup restoration tests
   ├─ Quarterly disaster recovery drills
   └─ Annual full system recovery test
```

---

## Next Steps

1. **Review architecture** — Confirm design
2. **Create implementation tasks** — Step-by-step build plan
3. **Start Phase 1 development** — Build MVP
4. **Set up development environment** — Local testing
5. **Deploy to test server** — Integration testing

