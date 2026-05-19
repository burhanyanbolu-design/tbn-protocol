# Boomi Integration — Flow Diagrams

## Overall Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      BOOMI CUSTOMER                             │
│                   (Using Boomi Platform)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Creates/Manages Bots
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    BOOMI PROCESS                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Receive input document                                │  │
│  │ 2. Map to TBN request format                             │  │
│  │ 3. Call HTTP connector                                   │  │
│  │ 4. Parse response                                        │  │
│  │ 5. Continue workflow                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP POST
                         │ /api/boomi/process
                         │ Authorization: Bearer tbn_live_xxx
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   TBN PROTOCOL API                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Receive request                                       │  │
│  │ 2. Validate API key                                      │  │
│  │ 3. Route by process_type                                 │  │
│  │ 4. Execute handler                                       │  │
│  │ 5. Return JSON response                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ JSON Response
                         │ { success: true, result: {...} }
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    BOOMI PROCESS                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Receive response                                      │  │
│  │ 2. Check success field                                   │  │
│  │ 3. Extract result                                        │  │
│  │ 4. Continue or error handling                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Continue workflow
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   BOOMI CUSTOMER                                │
│              (Gets result from TBN)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Bot Registration Flow

```
BOOMI SENDS:
┌─────────────────────────────────────────┐
│ {                                       │
│   "process_type": "bot_registration",   │
│   "data": {                             │
│     "bot_name": "SearchBot",            │
│     "bot_type": "SEARCH",               │
│     "company": "Acme Corp",             │
│     "email": "contact@acme.com",        │
│     "description": "..."                │
│   },                                    │
│   "metadata": { ... }                   │
│ }                                       │
└─────────────────────────────────────────┘
           │
           ▼
    TBN PROCESSES:
    1. Validate input
    2. Create bot instance
    3. Register in database
    4. Generate bot_id
           │
           ▼
TBN RETURNS:
┌─────────────────────────────────────────┐
│ {                                       │
│   "success": true,                      │
│   "process_id": "proc-12345",           │
│   "result": {                           │
│     "bot_id": "tbn-bot-searchbot-001",  │
│     "bot_name": "SearchBot",            │
│     "bot_type": "SEARCH",               │
│     "company": "Acme Corp",             │
│     "status": "registered",             │
│     "created_at": "2026-05-12T..."      │
│   },                                    │
│   "status": "completed"                 │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## Certification Check Flow

```
BOOMI SENDS:
┌─────────────────────────────────────────┐
│ {                                       │
│   "process_type": "certification_check",│
│   "data": {                             │
│     "bot_id": "tbn-bot-searchbot-001",  │
│     "cert_level": "GOLD"                │
│   },                                    │
│   "metadata": { ... }                   │
│ }                                       │
└─────────────────────────────────────────┘
           │
           ▼
    TBN PROCESSES:
    1. Look up bot
    2. Check certification
    3. Verify expiry
    4. Return status
           │
           ▼
TBN RETURNS:
┌─────────────────────────────────────────┐
│ {                                       │
│   "success": true,                      │
│   "process_id": "proc-12346",           │
│   "result": {                           │
│     "bot_id": "tbn-bot-searchbot-001",  │
│     "certified": true,                  │
│     "cert_level": "GOLD",               │
│     "expires": "2027-05-12T...",        │
│     "verified_at": "2026-05-12T..."     │
│   },                                    │
│   "status": "completed"                 │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## Governance Query Flow

```
BOOMI SENDS:
┌─────────────────────────────────────────┐
│ {                                       │
│   "process_type": "governance_query",   │
│   "data": {                             │
│     "query_type": "bot_status",         │
│     "bot_id": "tbn-bot-searchbot-001",  │
│     "limit": 10                         │
│   },                                    │
│   "metadata": { ... }                   │
│ }                                       │
└─────────────────────────────────────────┘
           │
           ▼
    TBN PROCESSES:
    1. Parse query_type
    2. Fetch data from database
    3. Filter by bot_id (if provided)
    4. Apply limit
           │
           ▼
TBN RETURNS:
┌─────────────────────────────────────────┐
│ {                                       │
│   "success": true,                      │
│   "process_id": "proc-12347",           │
│   "result": {                           │
│     "query_type": "bot_status",         │
│     "count": 1,                         │
│     "bots": [                           │
│       {                                 │
│         "bot_id": "tbn-bot-...",        │
│         "bot_name": "SearchBot",        │
│         "company": "Acme Corp",         │
│         "status": "active"              │
│       }                                 │
│     ]                                   │
│   },                                    │
│   "status": "completed"                 │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## Error Handling Flow

```
BOOMI SENDS REQUEST
           │
           ▼
    TBN VALIDATES
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
  VALID       INVALID
    │             │
    │             ▼
    │      TBN RETURNS ERROR:
    │      ┌──────────────────────┐
    │      │ {                    │
    │      │   "success": false,  │
    │      │   "error": "...",    │
    │      │   "status": "error"  │
    │      │ }                    │
    │      └──────────────────────┘
    │             │
    ▼             ▼
PROCESS      BOOMI ERROR
HANDLER      HANDLING
    │             │
    ▼             ▼
RETURN       LOG ERROR
SUCCESS      & ALERT
```

---

## Authentication Flow

```
BOOMI PROCESS
    │
    ├─ Get API key: tbn_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
    │
    ├─ Add to request header:
    │  Authorization: Bearer tbn_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
    │
    ▼
TBN API GATEWAY
    │
    ├─ Extract key from header
    │
    ├─ Hash key: SHA256(tbn_live_...)
    │
    ├─ Look up in database
    │
    ├─ Check if active
    │
    ├─ Check if expired
    │
    ├─ Check rate limit
    │
    ├─ Check tier permissions
    │
    ├─ If all OK: ✅ ALLOW
    │
    └─ If any fail: ❌ DENY
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    BOOMI CUSTOMER                            │
│                                                              │
│  Input Document                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ {                                                      │ │
│  │   "bot_name": "SearchBot",                             │ │
│  │   "bot_type": "SEARCH",                                │ │
│  │   "company": "Acme Corp",                              │ │
│  │   ...                                                  │ │
│  │ }                                                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ BOOMI MAPS
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                    BOOMI PROCESS                             │
│                                                              │
│  Mapped Request                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ {                                                      │ │
│  │   "process_type": "bot_registration",                  │ │
│  │   "data": {                                            │ │
│  │     "bot_name": "SearchBot",                           │ │
│  │     "bot_type": "SEARCH",                              │ │
│  │     "company": "Acme Corp",                            │ │
│  │     "email": "contact@acme.com",                       │ │
│  │     "description": "..."                               │ │
│  │   },                                                   │ │
│  │   "metadata": {                                        │ │
│  │     "boomi_process_id": "proc-12345",                  │ │
│  │     "timestamp": "2026-05-12T10:30:00Z",               │ │
│  │     "source": "boomi"                                  │ │
│  │   }                                                    │ │
│  │ }                                                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ HTTP POST
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                   TBN PROTOCOL API                           │
│                                                              │
│  Response                                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ {                                                      │ │
│  │   "success": true,                                     │ │
│  │   "process_id": "proc-12345",                          │ │
│  │   "result": {                                          │ │
│  │     "bot_id": "tbn-bot-searchbot-001",                 │ │
│  │     "bot_name": "SearchBot",                           │ │
│  │     "bot_type": "SEARCH",                              │ │
│  │     "company": "Acme Corp",                            │ │
│  │     "status": "registered",                            │ │
│  │     "created_at": "2026-05-12T10:30:00Z"               │ │
│  │   },                                                   │ │
│  │   "status": "completed"                                │ │
│  │ }                                                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ BOOMI MAPS
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                    BOOMI PROCESS                             │
│                                                              │
│  Output Document                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ {                                                      │ │
│  │   "bot_id": "tbn-bot-searchbot-001",                   │ │
│  │   "status": "registered",                              │ │
│  │   "created_at": "2026-05-12T10:30:00Z"                 │ │
│  │ }                                                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ CONTINUE WORKFLOW
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                    BOOMI CUSTOMER                            │
│                                                              │
│  Result: Bot successfully registered with TBN               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Summary

1. **Boomi sends** a request to TBN with process_type and data
2. **TBN validates** the API key and processes the request
3. **TBN returns** a JSON response with success/error status
4. **Boomi receives** the response and continues the workflow

This is a simple, synchronous request-response pattern that integrates seamlessly with Boomi's workflow engine.

