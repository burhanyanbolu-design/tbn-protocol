# 📋 Hardin-AI Phone — Detailed Requirements

**Project**: Hardin-AI Phone  
**Date**: May 12, 2026  
**Version**: 1.0.0

---

## Overview

This document breaks down each requirement from SPEC.md into detailed, actionable tasks.

---

## 1. Phone Integration Requirements

### 1.1 SIP Trunk Connection
**Requirement**: Accept inbound calls on customer's existing phone line via SIP trunk

**Tasks**:
- [ ] Configure Asterisk to accept SIP connections
- [ ] Set up SIP trunk authentication (username/password)
- [ ] Configure inbound call routing
- [ ] Test with Vodafone SIP trunk (+447999605080)
- [ ] Handle SIP registration and keep-alive
- [ ] Log all SIP connections for debugging

**Acceptance Criteria**:
- Incoming calls are received by Asterisk
- Call is routed to Python app
- Call audio is captured
- No dropped calls

**Dependencies**:
- Asterisk installed and running
- Vodafone SIP trunk configured
- Network connectivity

---

### 1.2 Concurrent Call Handling
**Requirement**: Handle multiple simultaneous calls

**Tasks**:
- [ ] Configure Asterisk for 10+ concurrent channels
- [ ] Set up call queuing
- [ ] Implement session management in Python
- [ ] Test with load testing tool (SIPp)
- [ ] Monitor resource usage (CPU, memory)
- [ ] Set up alerts for high load

**Acceptance Criteria**:
- System handles 10 concurrent calls without dropping
- Each call has independent session
- No cross-talk between calls
- CPU usage <80%

**Dependencies**:
- Asterisk configuration
- Python session management
- Load testing tools

---

### 1.3 Call Transfer to Human
**Requirement**: Transfer call to human agent if needed

**Tasks**:
- [ ] Implement transfer logic in Python
- [ ] Create transfer queue
- [ ] Set up human agent phone number
- [ ] Test transfer flow
- [ ] Log transfer reasons
- [ ] Provide transfer confirmation to customer

**Acceptance Criteria**:
- Call transfers successfully to human
- Customer hears hold music during transfer
- Agent receives call with context
- Transfer is logged

**Dependencies**:
- Asterisk transfer configuration
- Human agent phone number
- Call context passing

---

### 1.4 Call Logging
**Requirement**: Record call logs and optional audio

**Tasks**:
- [ ] Implement call logging to database
- [ ] Log: caller number, duration, status, timestamp
- [ ] Implement optional audio recording
- [ ] Store audio files securely
- [ ] Implement audio playback in dashboard
- [ ] Add privacy notice for recording

**Acceptance Criteria**:
- All calls are logged
- Audio is recorded (if enabled)
- Logs are searchable
- Privacy compliant

**Dependencies**:
- Database schema for call logs
- Audio storage
- Privacy policy

---

## 2. Booking Flow Requirements

### 2.1 Question Flow
**Requirement**: Ask customer questions in sequence

**Questions to ask**:
1. Name
2. Pickup location
3. Destination
4. Date
5. Time
6. Number of passengers
7. Luggage amount
8. Flight number (if airport)
9. Callback number

**Tasks**:
- [ ] Create question list in database
- [ ] Implement question sequencing logic
- [ ] Handle customer responses
- [ ] Validate responses (e.g., date format)
- [ ] Allow customer to repeat/correct answers
- [ ] Handle "I don't know" responses
- [ ] Implement timeout handling (no response for 10 seconds)

**Acceptance Criteria**:
- All questions are asked in order
- Responses are captured correctly
- Invalid responses are re-asked
- Customer can correct mistakes
- Timeouts are handled gracefully

**Dependencies**:
- Question database schema
- Response validation logic
- Timeout handling

---

### 2.2 Booking Confirmation
**Requirement**: Confirm booking details before saving

**Tasks**:
- [ ] Read back all booking details
- [ ] Ask for confirmation ("Is this correct?")
- [ ] Handle yes/no responses
- [ ] Allow customer to change details
- [ ] Generate booking reference number
- [ ] Provide booking reference to customer

**Acceptance Criteria**:
- Customer hears all details
- Customer confirms or denies
- Booking reference is provided
- Customer can repeat reference

**Dependencies**:
- Booking details formatting
- Confirmation logic
- Reference number generation

---

### 2.3 Booking Storage
**Requirement**: Save booking to database

**Tasks**:
- [ ] Create booking database schema
- [ ] Implement booking save function
- [ ] Generate unique booking ID
- [ ] Store all customer details
- [ ] Store call metadata (duration, timestamp, etc.)
- [ ] Implement error handling for save failures
- [ ] Log booking creation

**Acceptance Criteria**:
- Booking is saved to database
- All fields are populated
- Booking ID is unique
- Save failures are logged
- Customer is notified of success

**Dependencies**:
- Database schema
- Error handling
- Logging

---

## 3. TBN Bot Integration Requirements

### 3.1 Bot Selection
**Requirement**: Select appropriate certified TBN bot for customer

**Tasks**:
- [ ] Query TBN registry for available bots
- [ ] Filter bots by certification level
- [ ] Select bot based on business type (taxi, restaurant, etc.)
- [ ] Store selected bot ID with booking
- [ ] Log bot selection

**Acceptance Criteria**:
- Correct bot is selected
- Bot is certified
- Bot ID is stored with booking
- Selection is logged

**Dependencies**:
- TBN registry access
- Bot certification data
- Bot selection logic

---

### 3.2 Bot Certification Verification
**Requirement**: Verify bot is certified before using

**Tasks**:
- [ ] Query TBN BICA registry
- [ ] Check bot certification status
- [ ] Check certification expiry
- [ ] Verify bot permissions
- [ ] Log verification result

**Acceptance Criteria**:
- Bot certification is verified
- Expired certs are rejected
- Verification is logged
- Only certified bots are used

**Dependencies**:
- TBN BICA registry access
- Certification data structure
- Verification logic

---

### 3.3 Bot Personality Injection
**Requirement**: Inject bot personality into responses

**Tasks**:
- [ ] Load bot personality from TBN registry
- [ ] Create system prompt with bot personality
- [ ] Inject personality into all responses
- [ ] Test personality consistency
- [ ] Allow customer to hear bot name/intro

**Acceptance Criteria**:
- Bot personality is evident in responses
- Responses are consistent with personality
- Customer knows which bot they're talking to
- Personality doesn't interfere with booking

**Dependencies**:
- Bot personality data
- System prompt template
- Response generation

---

## 4. Speech Processing Requirements

### 4.1 Speech-to-Text (faster-whisper)
**Requirement**: Convert customer speech to text

**Tasks**:
- [ ] Install faster-whisper
- [ ] Configure audio input from Asterisk
- [ ] Implement real-time transcription
- [ ] Handle background noise
- [ ] Implement confidence scoring
- [ ] Log transcription results
- [ ] Handle transcription errors

**Acceptance Criteria**:
- Speech is transcribed to text
- Accuracy is 90%+
- Real-time processing (< 2 seconds)
- Errors are logged
- Confidence scores are available

**Dependencies**:
- faster-whisper installation
- Audio input configuration
- Error handling

---

### 4.2 Text-to-Speech (Piper)
**Requirement**: Convert bot responses to speech

**Tasks**:
- [ ] Install Piper TTS
- [ ] Configure voice selection
- [ ] Implement text-to-speech conversion
- [ ] Handle special characters/numbers
- [ ] Implement audio playback
- [ ] Cache generated audio
- [ ] Handle TTS errors

**Acceptance Criteria**:
- Text is converted to speech
- Voice is clear and professional
- Special characters are handled correctly
- Audio is played to customer
- Errors are handled gracefully

**Dependencies**:
- Piper TTS installation
- Voice configuration
- Audio playback

---

### 4.3 Intent Detection
**Requirement**: Detect customer intent (book vs. chat vs. info)

**Tasks**:
- [ ] Implement intent detection logic
- [ ] Classify: "book", "chat", "info", "transfer"
- [ ] Use keyword matching or ML model
- [ ] Route based on intent
- [ ] Log intent detection
- [ ] Handle ambiguous intents

**Acceptance Criteria**:
- Intent is correctly detected
- Routing is appropriate
- Ambiguous cases are handled
- Detection is logged

**Dependencies**:
- Intent detection model/logic
- Routing logic
- Logging

---

### 4.4 Transfer to Human
**Requirement**: Transfer to human if customer requests or bot can't help

**Tasks**:
- [ ] Detect transfer request
- [ ] Queue call for human agent
- [ ] Play hold music
- [ ] Notify agent of incoming call
- [ ] Pass call context to agent
- [ ] Log transfer reason

**Acceptance Criteria**:
- Transfer is initiated
- Hold music plays
- Agent receives call
- Context is available to agent
- Transfer is logged

**Dependencies**:
- Transfer detection
- Queue management
- Agent notification
- Call context passing

---

## 5. Database Requirements

### 5.1 Booking Storage
**Requirement**: Store bookings with all details

**Schema**:
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
    booking_reference TEXT
);
```

**Tasks**:
- [ ] Create booking table
- [ ] Implement booking insert
- [ ] Implement booking query
- [ ] Implement booking update
- [ ] Add indexes for performance
- [ ] Implement data validation

**Acceptance Criteria**:
- Bookings are stored correctly
- All fields are populated
- Queries are fast
- Data is validated

**Dependencies**:
- Database schema
- ORM or SQL library

---

### 5.2 Call Logs
**Requirement**: Store call logs

**Schema**:
```sql
CREATE TABLE call_logs (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    caller_number TEXT,
    duration INTEGER,
    status TEXT,
    bot_id TEXT,
    transfer_reason TEXT,
    audio_file TEXT
);
```

**Tasks**:
- [ ] Create call_logs table
- [ ] Log all calls
- [ ] Store call duration
- [ ] Store call status
- [ ] Store transfer reason
- [ ] Store audio file path

**Acceptance Criteria**:
- All calls are logged
- Logs are queryable
- Audio files are linked
- Logs are searchable

**Dependencies**:
- Database schema
- Logging logic

---

### 5.3 Customer Information
**Requirement**: Store customer information

**Schema**:
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

**Tasks**:
- [ ] Create customers table
- [ ] Store customer info
- [ ] Track booking history
- [ ] Implement customer lookup
- [ ] Handle duplicate customers

**Acceptance Criteria**:
- Customer info is stored
- Duplicates are handled
- Booking history is tracked
- Customers are identifiable

**Dependencies**:
- Database schema
- Duplicate detection logic

---

## 6. Plugin System Requirements

### 6.1 WordPress Plugin
**Requirement**: Create WordPress plugin for easy installation

**Tasks**:
- [ ] Create WordPress plugin structure
- [ ] Implement plugin activation/deactivation
- [ ] Create admin settings page
- [ ] Add shortcode for booking widget
- [ ] Implement webhook for call notifications
- [ ] Create plugin documentation

**Acceptance Criteria**:
- Plugin installs without errors
- Settings page works
- Shortcode displays widget
- Webhooks are received
- Documentation is clear

**Dependencies**:
- WordPress plugin API
- Webhook implementation
- Admin UI

---

### 6.2 Shopify App
**Requirement**: Create Shopify app for easy installation

**Tasks**:
- [ ] Create Shopify app structure
- [ ] Implement OAuth authentication
- [ ] Create app settings page
- [ ] Add booking widget to store
- [ ] Implement webhook for orders
- [ ] Create app documentation

**Acceptance Criteria**:
- App installs without errors
- Settings page works
- Widget displays on store
- Webhooks are received
- Documentation is clear

**Dependencies**:
- Shopify API
- OAuth implementation
- Webhook handling

---

### 6.3 Custom Website Integration
**Requirement**: Provide API for custom website integration

**Tasks**:
- [ ] Create REST API endpoints
- [ ] Implement API authentication
- [ ] Create API documentation
- [ ] Provide code examples
- [ ] Implement rate limiting
- [ ] Create API client library

**Acceptance Criteria**:
- API endpoints work
- Authentication is secure
- Documentation is complete
- Examples are clear
- Rate limiting works

**Dependencies**:
- REST API framework
- Authentication system
- API documentation

---

### 6.4 Booking Widget
**Requirement**: Embed booking widget on website

**Tasks**:
- [ ] Create widget HTML/CSS/JS
- [ ] Implement widget configuration
- [ ] Add widget to plugins
- [ ] Test widget on different sites
- [ ] Implement responsive design
- [ ] Add accessibility features

**Acceptance Criteria**:
- Widget displays correctly
- Widget is responsive
- Widget is accessible
- Configuration works
- Widget works on all sites

**Dependencies**:
- Frontend framework
- CSS framework
- Accessibility standards

---

## 7. Admin Dashboard Requirements

### 7.1 Booking Management
**Requirement**: View and manage bookings

**Tasks**:
- [ ] Create dashboard UI
- [ ] Implement booking list view
- [ ] Add filtering (date, customer, status)
- [ ] Add sorting
- [ ] Implement pagination
- [ ] Add booking detail view
- [ ] Implement booking status update

**Acceptance Criteria**:
- Bookings are displayed
- Filtering works
- Sorting works
- Pagination works
- Status updates work

**Dependencies**:
- Frontend framework
- Database queries
- UI components

---

### 7.2 Call Logs
**Requirement**: View call logs and audio

**Tasks**:
- [ ] Create call logs view
- [ ] Implement call log filtering
- [ ] Add audio playback
- [ ] Implement call log export
- [ ] Add call log search
- [ ] Implement call log analytics

**Acceptance Criteria**:
- Call logs are displayed
- Filtering works
- Audio plays
- Export works
- Search works

**Dependencies**:
- Frontend framework
- Audio player
- Export functionality

---

### 7.3 Analytics
**Requirement**: View booking and call analytics

**Tasks**:
- [ ] Create analytics dashboard
- [ ] Implement booking metrics (total, by date, by status)
- [ ] Implement call metrics (total, duration, success rate)
- [ ] Create charts and graphs
- [ ] Implement date range filtering
- [ ] Add export functionality

**Acceptance Criteria**:
- Metrics are displayed
- Charts are accurate
- Filtering works
- Export works
- Data is up-to-date

**Dependencies**:
- Frontend framework
- Charting library
- Analytics calculations

---

### 7.4 Settings
**Requirement**: Configure system settings

**Tasks**:
- [ ] Create settings page
- [ ] Implement bot selection
- [ ] Implement question customization
- [ ] Implement notification settings
- [ ] Implement API key management
- [ ] Implement user management

**Acceptance Criteria**:
- Settings are saved
- Changes take effect
- Settings are persistent
- User management works
- API keys are secure

**Dependencies**:
- Settings storage
- User authentication
- API key generation

---

## 8. Non-Functional Requirements

### 8.1 Performance
**Requirement**: System performs well under load

**Tasks**:
- [ ] Implement caching
- [ ] Optimize database queries
- [ ] Implement connection pooling
- [ ] Load test with 10+ concurrent calls
- [ ] Monitor response times
- [ ] Optimize slow queries

**Acceptance Criteria**:
- Response time < 500ms
- System handles 10+ concurrent calls
- CPU usage < 80%
- Memory usage < 2GB
- No dropped calls

**Dependencies**:
- Load testing tools
- Monitoring tools
- Performance optimization

---

### 8.2 Reliability
**Requirement**: System is reliable and available

**Tasks**:
- [ ] Implement error handling
- [ ] Implement retry logic
- [ ] Implement health checks
- [ ] Implement monitoring
- [ ] Implement alerting
- [ ] Implement backup/recovery

**Acceptance Criteria**:
- Uptime 99.5%+
- Errors are handled gracefully
- Retries work
- Health checks pass
- Alerts are sent
- Recovery is automatic

**Dependencies**:
- Error handling
- Monitoring tools
- Alerting system
- Backup system

---

### 8.3 Security
**Requirement**: System is secure

**Tasks**:
- [ ] Implement HTTPS/TLS
- [ ] Implement API authentication
- [ ] Implement input validation
- [ ] Implement SQL injection prevention
- [ ] Implement rate limiting
- [ ] Implement audit logging
- [ ] Implement data encryption

**Acceptance Criteria**:
- All data is encrypted in transit
- API is authenticated
- Input is validated
- SQL injection is prevented
- Rate limiting works
- Audit logs are complete
- Sensitive data is encrypted

**Dependencies**:
- SSL/TLS certificates
- Authentication system
- Input validation
- Encryption library

---

### 8.4 Scalability
**Requirement**: System can scale to 100+ customers

**Tasks**:
- [ ] Implement multi-tenancy
- [ ] Implement database sharding
- [ ] Implement load balancing
- [ ] Implement caching layer
- [ ] Implement CDN for static files
- [ ] Implement horizontal scaling

**Acceptance Criteria**:
- System supports 100+ customers
- Performance doesn't degrade
- Data is isolated per customer
- Load is distributed
- Scaling is automatic

**Dependencies**:
- Multi-tenancy architecture
- Load balancer
- Caching system
- CDN

---

## 9. Documentation Requirements

### 9.1 Installation Guide (Managed)
**Tasks**:
- [ ] Write step-by-step installation guide
- [ ] Include screenshots
- [ ] Include troubleshooting section
- [ ] Include FAQ
- [ ] Include support contact

---

### 9.2 Installation Guide (Self-Hosted)
**Tasks**:
- [ ] Write step-by-step installation guide
- [ ] Include prerequisites
- [ ] Include configuration guide
- [ ] Include troubleshooting section
- [ ] Include FAQ
- [ ] Include support contact

---

### 9.3 API Documentation
**Tasks**:
- [ ] Document all API endpoints
- [ ] Include request/response examples
- [ ] Include error codes
- [ ] Include rate limits
- [ ] Include authentication

---

### 9.4 Video Tutorials
**Tasks**:
- [ ] Create installation video
- [ ] Create configuration video
- [ ] Create usage video
- [ ] Create troubleshooting video
- [ ] Create API integration video

---

## Summary

**Total requirements**: 50+  
**Total tasks**: 200+  
**Estimated effort**: 8-10 weeks

**Next steps**:
1. Review requirements
2. Prioritize requirements
3. Create implementation tasks
4. Start Phase 1 development

