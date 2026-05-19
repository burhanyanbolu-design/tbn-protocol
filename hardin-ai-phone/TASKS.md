# 🚀 Hardin-AI Phone — Phase 1 Implementation Tasks

**Project**: Hardin-AI Phone  
**Phase**: 1 (MVP)  
**Duration**: 4 weeks  
**Date**: May 12, 2026

---

## Phase 1 Overview

**Goal**: Build a working MVP that can:
- Accept calls on Vodafone SIP trunk
- Ask booking questions
- Save bookings to database
- Integrate with TBN bot

**Test number**: +447999605080 (Vodafone)

---

## Task Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1 TASKS                                │
└─────────────────────────────────────────────────────────────────┘

Week 1: Setup & Infrastructure
├─ Task 1.1: Set up development environment
├─ Task 1.2: Install Asterisk on test server
├─ Task 1.3: Configure Vodafone SIP trunk
└─ Task 1.4: Test SIP connection

Week 2: Python Application
├─ Task 2.1: Create FastAPI project structure
├─ Task 2.2: Implement call handler endpoints
├─ Task 2.3: Implement booking flow logic
├─ Task 2.4: Create database schema
└─ Task 2.5: Implement database operations

Week 3: Speech Processing
├─ Task 3.1: Install faster-whisper
├─ Task 3.2: Install Piper TTS
├─ Task 3.3: Integrate speech-to-text
├─ Task 3.4: Integrate text-to-speech
└─ Task 3.5: Test speech processing

Week 4: TBN Integration & Testing
├─ Task 4.1: Integrate TBN bot selection
├─ Task 4.2: Implement bot certification verification
├─ Task 4.3: Test end-to-end call flow
├─ Task 4.4: Create admin dashboard (basic)
└─ Task 4.5: Documentation & deployment

```

---

## Week 1: Setup & Infrastructure

### Task 1.1: Set up development environment

**Objective**: Prepare local development environment

**Subtasks**:
- [ ] Install Python 3.9+
- [ ] Install Docker
- [ ] Install Git
- [ ] Clone tbn-protocol repository
- [ ] Create virtual environment
- [ ] Install Python dependencies (FastAPI, SQLAlchemy, etc.)
- [ ] Set up IDE (VS Code recommended)
- [ ] Create .env file with configuration

**Deliverables**:
- Development environment ready
- All dependencies installed
- .env file configured

**Estimated time**: 2 hours

**Dependencies**: None

---

### Task 1.2: Install Asterisk on test server

**Objective**: Set up Asterisk on Ubuntu VPS

**Subtasks**:
- [ ] Provision Ubuntu 22.04 VPS (DigitalOcean/Linode)
- [ ] SSH into server
- [ ] Update system packages
- [ ] Install Asterisk 20+
- [ ] Install FreePBX (optional, for UI)
- [ ] Configure Asterisk basic settings
- [ ] Start Asterisk service
- [ ] Verify Asterisk is running

**Deliverables**:
- Asterisk running on VPS
- Asterisk CLI accessible
- Service auto-starts on reboot

**Estimated time**: 3 hours

**Dependencies**: None

---

### Task 1.3: Configure Vodafone SIP trunk

**Objective**: Connect Vodafone phone line to Asterisk

**Subtasks**:
- [ ] Get Vodafone SIP trunk credentials
- [ ] Configure SIP trunk in Asterisk
- [ ] Set up inbound routing
- [ ] Configure dialplan for incoming calls
- [ ] Test SIP registration
- [ ] Verify trunk is active

**Configuration**:
```ini
; /etc/asterisk/sip.conf
[vodafone-trunk]
type=trunk
host=sip.vodafone.co.uk
username=YOUR_USERNAME
secret=YOUR_PASSWORD
fromuser=YOUR_USERNAME
fromdomain=sip.vodafone.co.uk
insecure=port,invite
```

**Deliverables**:
- SIP trunk configured
- Trunk shows as active in Asterisk
- Inbound routing configured

**Estimated time**: 2 hours

**Dependencies**: Task 1.2

---

### Task 1.4: Test SIP connection

**Objective**: Verify SIP trunk is working

**Subtasks**:
- [ ] Make test call to +447999605080
- [ ] Verify call is received by Asterisk
- [ ] Check Asterisk logs for call details
- [ ] Test call routing to Python app (placeholder)
- [ ] Verify audio is captured
- [ ] Test call hangup

**Test procedure**:
```bash
# SSH into Asterisk server
ssh ubuntu@YOUR_SERVER_IP

# Check SIP trunk status
asterisk -r
sip show peers

# Monitor calls
sip set debug on
```

**Deliverables**:
- Incoming calls are received
- Call logs show successful routing
- Audio is captured

**Estimated time**: 1 hour

**Dependencies**: Task 1.3

---

## Week 2: Python Application

### Task 2.1: Create FastAPI project structure

**Objective**: Set up Python project structure

**Subtasks**:
- [ ] Create project directory structure
- [ ] Create main.py (FastAPI app)
- [ ] Create routers/ directory
- [ ] Create services/ directory
- [ ] Create models/ directory
- [ ] Create utils/ directory
- [ ] Create requirements.txt
- [ ] Create .env.example

**Project structure**:
```
hardin-ai-phone/
├── main.py
├── requirements.txt
├── .env
├── .env.example
├── routers/
│   ├── __init__.py
│   ├── calls.py
│   └── bookings.py
├── services/
│   ├── __init__.py
│   ├── booking_service.py
│   ├── bot_service.py
│   └── database_service.py
├── models/
│   ├── __init__.py
│   ├── booking.py
│   └── call.py
└── utils/
    ├── __init__.py
    ├── validators.py
    └── logger.py
```

**Deliverables**:
- Project structure created
- FastAPI app runs
- All imports work

**Estimated time**: 1 hour

**Dependencies**: Task 1.1

---

### Task 2.2: Implement call handler endpoints

**Objective**: Create API endpoints for call handling

**Endpoints to create**:
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

**Subtasks**:
- [ ] Create call router
- [ ] Implement /api/call/start endpoint
- [ ] Implement /api/call/answer endpoint
- [ ] Implement /api/call/transfer endpoint
- [ ] Add request validation
- [ ] Add error handling
- [ ] Add logging

**Deliverables**:
- All endpoints implemented
- Endpoints return correct responses
- Error handling works

**Estimated time**: 3 hours

**Dependencies**: Task 2.1

---

### Task 2.3: Implement booking flow logic

**Objective**: Create booking question flow

**Subtasks**:
- [ ] Create question list
- [ ] Implement question sequencing
- [ ] Implement response validation
- [ ] Implement response storage
- [ ] Implement confirmation logic
- [ ] Implement booking reference generation
- [ ] Add error handling

**Questions**:
1. Name
2. Pickup location
3. Destination
4. Date
5. Time
6. Number of passengers
7. Luggage amount
8. Flight number (if airport)
9. Callback number

**Deliverables**:
- Questions are asked in order
- Responses are validated
- Booking reference is generated

**Estimated time**: 4 hours

**Dependencies**: Task 2.2

---

### Task 2.4: Create database schema

**Objective**: Design and create database tables

**Tables to create**:
- bookings
- call_logs
- customers
- settings

**Subtasks**:
- [ ] Design database schema
- [ ] Create SQLAlchemy models
- [ ] Create database initialization script
- [ ] Create migration scripts
- [ ] Test schema creation

**Deliverables**:
- Database schema created
- All tables exist
- Indexes created

**Estimated time**: 2 hours

**Dependencies**: Task 2.1

---

### Task 2.5: Implement database operations

**Objective**: Create CRUD operations for database

**Subtasks**:
- [ ] Implement booking insert
- [ ] Implement booking query
- [ ] Implement booking update
- [ ] Implement call log insert
- [ ] Implement customer insert/query
- [ ] Implement settings get/set
- [ ] Add error handling
- [ ] Add transaction support

**Deliverables**:
- All CRUD operations work
- Data is persisted
- Queries are fast

**Estimated time**: 3 hours

**Dependencies**: Task 2.4

---

## Week 3: Speech Processing

### Task 3.1: Install faster-whisper

**Objective**: Set up speech-to-text

**Subtasks**:
- [ ] Install faster-whisper package
- [ ] Download model (base)
- [ ] Test transcription with sample audio
- [ ] Verify accuracy
- [ ] Optimize for speed

**Installation**:
```bash
pip install faster-whisper
```

**Deliverables**:
- faster-whisper installed
- Model downloaded
- Transcription works

**Estimated time**: 1 hour

**Dependencies**: Task 1.1

---

### Task 3.2: Install Piper TTS

**Objective**: Set up text-to-speech

**Subtasks**:
- [ ] Install Piper package
- [ ] Download voice model (en_US-ryan-medium)
- [ ] Test TTS with sample text
- [ ] Verify audio quality
- [ ] Optimize for speed

**Installation**:
```bash
pip install piper-tts
```

**Deliverables**:
- Piper installed
- Voice model downloaded
- TTS works

**Estimated time**: 1 hour

**Dependencies**: Task 1.1

---

### Task 3.3: Integrate speech-to-text

**Objective**: Connect faster-whisper to call handler

**Subtasks**:
- [ ] Create speech service
- [ ] Implement transcription function
- [ ] Handle audio input from Asterisk
- [ ] Add confidence scoring
- [ ] Add error handling
- [ ] Test with real audio

**Deliverables**:
- Speech-to-text integrated
- Transcription accuracy 90%+
- Real-time processing works

**Estimated time**: 3 hours

**Dependencies**: Task 3.1, Task 2.2

---

### Task 3.4: Integrate text-to-speech

**Objective**: Connect Piper to call handler

**Subtasks**:
- [ ] Create TTS service
- [ ] Implement speech generation function
- [ ] Handle audio output to Asterisk
- [ ] Add caching for generated audio
- [ ] Add error handling
- [ ] Test with real calls

**Deliverables**:
- Text-to-speech integrated
- Audio plays to customer
- Caching works

**Estimated time**: 3 hours

**Dependencies**: Task 3.2, Task 2.2

---

### Task 3.5: Test speech processing

**Objective**: Verify speech processing works end-to-end

**Subtasks**:
- [ ] Make test call
- [ ] Speak test phrase
- [ ] Verify transcription
- [ ] Verify bot response
- [ ] Verify audio playback
- [ ] Test with different accents
- [ ] Test with background noise

**Test cases**:
- Clear speech
- Accented speech
- Background noise
- Unclear speech

**Deliverables**:
- Speech processing works
- Accuracy is acceptable
- No dropped audio

**Estimated time**: 2 hours

**Dependencies**: Task 3.3, Task 3.4

---

## Week 4: TBN Integration & Testing

### Task 4.1: Integrate TBN bot selection

**Objective**: Select and use TBN bots

**Subtasks**:
- [ ] Import TBN bot classes
- [ ] Create bot service
- [ ] Implement bot selection logic
- [ ] Implement bot initialization
- [ ] Test bot responses
- [ ] Add error handling

**Deliverables**:
- Bot is selected
- Bot responds to queries
- Responses are appropriate

**Estimated time**: 2 hours

**Dependencies**: Task 2.2

---

### Task 4.2: Implement bot certification verification

**Objective**: Verify bot is certified

**Subtasks**:
- [ ] Query TBN BICA registry
- [ ] Check certification status
- [ ] Check certification expiry
- [ ] Verify bot permissions
- [ ] Add error handling
- [ ] Log verification results

**Deliverables**:
- Bot certification is verified
- Only certified bots are used
- Verification is logged

**Estimated time**: 2 hours

**Dependencies**: Task 4.1

---

### Task 4.3: Test end-to-end call flow

**Objective**: Test complete booking flow

**Test procedure**:
1. Call +447999605080
2. Bot asks "What is your name?"
3. Say "John Smith"
4. Bot asks "Where are you picking up from?"
5. Say "Terminal 3"
6. Continue through all questions
7. Bot confirms booking
8. Booking is saved to database

**Subtasks**:
- [ ] Make test call
- [ ] Go through complete booking flow
- [ ] Verify all questions are asked
- [ ] Verify responses are captured
- [ ] Verify booking is saved
- [ ] Verify booking reference is provided
- [ ] Test error cases

**Deliverables**:
- Complete booking flow works
- Booking is saved
- No errors occur

**Estimated time**: 3 hours

**Dependencies**: Task 3.5, Task 4.2, Task 2.5

---

### Task 4.4: Create admin dashboard (basic)

**Objective**: Create basic dashboard to view bookings

**Subtasks**:
- [ ] Create dashboard HTML/CSS
- [ ] Create dashboard route
- [ ] Implement booking list view
- [ ] Implement booking detail view
- [ ] Add filtering (date, status)
- [ ] Add sorting
- [ ] Test dashboard

**Deliverables**:
- Dashboard displays bookings
- Filtering works
- Sorting works

**Estimated time**: 3 hours

**Dependencies**: Task 2.5

---

### Task 4.5: Documentation & deployment

**Objective**: Document and deploy MVP

**Subtasks**:
- [ ] Write installation guide
- [ ] Write configuration guide
- [ ] Write troubleshooting guide
- [ ] Create Docker setup
- [ ] Deploy to test server
- [ ] Test deployment
- [ ] Create deployment checklist

**Deliverables**:
- Installation guide complete
- Docker setup works
- Deployment successful
- System is running

**Estimated time**: 4 hours

**Dependencies**: All previous tasks

---

## Success Criteria

### Technical
- [ ] System accepts calls on Vodafone SIP trunk
- [ ] Booking questions are asked in order
- [ ] Responses are captured correctly
- [ ] Bookings are saved to database
- [ ] TBN bot is integrated
- [ ] Speech processing works
- [ ] Admin dashboard displays bookings
- [ ] No errors in logs

### Functional
- [ ] Complete booking flow works
- [ ] Booking reference is provided
- [ ] Customer can hear all responses
- [ ] Booking is saved correctly
- [ ] Dashboard shows all bookings

### Non-Functional
- [ ] Response time < 500ms
- [ ] No dropped calls
- [ ] Speech accuracy 90%+
- [ ] System uptime 99%+

---

## Timeline

| Week | Tasks | Deliverable |
|------|-------|-------------|
| 1 | Setup & Infrastructure | Working SIP trunk |
| 2 | Python Application | Booking flow logic |
| 3 | Speech Processing | Speech integration |
| 4 | TBN Integration & Testing | Working MVP |

**Total duration**: 4 weeks  
**Start date**: May 12, 2026  
**End date**: June 9, 2026

---

## Resource Requirements

### Hardware
- Ubuntu VPS (2 CPU, 4GB RAM, 20GB disk)
- Development machine (any OS)

### Software
- Python 3.9+
- Asterisk 20+
- Docker
- Git

### Services
- Vodafone SIP trunk
- TBN Protocol access

### Team
- 1 developer (full-time)
- 1 DevOps engineer (part-time)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| SIP trunk issues | Medium | High | Test early, have backup provider |
| Speech accuracy | Medium | Medium | Use multiple models, test extensively |
| Database issues | Low | High | Use proven SQLAlchemy, test migrations |
| TBN integration | Low | Medium | Use existing TBN code, test early |

---

## Next Steps

1. **Approve tasks** — Confirm task list
2. **Assign resources** — Assign developer
3. **Start Week 1** — Begin setup
4. **Daily standups** — Track progress
5. **Weekly reviews** — Assess completion

---

**Status**: Ready to execute  
**Next action**: Start Task 1.1 (Set up development environment)

