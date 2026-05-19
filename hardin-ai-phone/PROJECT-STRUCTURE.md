# Hardin-AI Phone — Project Structure

**Date**: May 12, 2026  
**Version**: 1.0.0

---

## Directory Layout

```
hardin-ai-phone/
│
├── 📄 main.py                          # Flask application entry point
├── 📄 requirements.txt                 # Python dependencies
├── 📄 .env                             # Environment configuration (local)
├── 📄 .env.example                     # Environment configuration (template)
├── 📄 .gitignore                       # Git ignore rules
│
├── 📁 venv/                            # Python virtual environment
│   ├── Scripts/                        # Executable scripts
│   ├── Lib/                            # Python packages
│   └── pyvenv.cfg                      # Virtual environment config
│
├── 📁 routers/                         # API route handlers
│   ├── __init__.py
│   ├── calls.py                        # Call handling endpoints
│   │   ├── POST /api/call/start        # Start new call
│   │   ├── POST /api/call/answer       # Handle response
│   │   └── POST /api/call/transfer     # Transfer to human
│   │
│   └── bookings.py                     # Booking management endpoints
│       ├── POST /api/booking/save      # Save booking
│       ├── GET /api/booking/list       # List bookings
│       └── GET /api/booking/{id}       # Get booking details
│
├── 📁 services/                        # Business logic services
│   ├── __init__.py
│   ├── bot_service.py                  # TBN bot integration
│   │   ├── select_bot()                # Select appropriate bot
│   │   ├── verify_certification()      # Verify bot is certified
│   │   ├── get_bot_personality()       # Get bot personality
│   │   └── generate_response()         # Generate bot response
│   │
│   ├── booking_service.py              # Booking flow logic
│   │   ├── create_session()            # Create booking session
│   │   ├── get_current_question()      # Get current question
│   │   ├── process_response()          # Process customer response
│   │   ├── get_booking_data()          # Get booking data
│   │   └── generate_booking_reference()# Generate reference
│   │
│   ├── speech_service.py               # Speech processing
│   │   ├── transcribe_audio()          # Speech-to-text (faster-whisper)
│   │   ├── generate_speech()           # Text-to-speech (Piper)
│   │   └── detect_intent()             # Detect customer intent
│   │
│   └── database_service.py             # Database operations
│       ├── save_booking()              # Save booking to DB
│       ├── get_booking()               # Get booking from DB
│       ├── list_bookings()             # List bookings with filters
│       └── save_call_log()             # Save call log to DB
│
├── 📁 models/                          # Data models
│   ├── __init__.py
│   ├── booking.py                      # Booking data model
│   │   └── Booking                     # Pydantic model
│   │
│   └── call.py                         # Call data model
│       └── Call                        # Pydantic model
│
├── 📁 utils/                           # Utility functions
│   ├── __init__.py
│   ├── validators.py                   # Input validation
│   │   ├── validate_phone_number()     # Validate UK phone
│   │   ├── validate_date()             # Validate date format
│   │   ├── validate_time()             # Validate time format
│   │   └── validate_passengers()       # Validate passenger count
│   │
│   └── logger.py                       # Logging configuration
│       └── setup_logger()              # Configure logger
│
├── 📁 templates/                       # HTML templates (future)
│   └── (empty - for admin dashboard)
│
├── 📁 static/                          # Static files (future)
│   ├── css/                            # CSS files
│   ├── js/                             # JavaScript files
│   └── images/                         # Images
│
├── 📁 database/                        # Database files (future)
│   └── hardin_ai_phone.db              # SQLite database
│
├── 📁 logs/                            # Log files (future)
│   └── app.log                         # Application logs
│
├── 📄 SPEC.md                          # Product specification
├── 📄 REQUIREMENTS.md                  # Detailed requirements
├── 📄 ARCHITECTURE.md                  # Technical architecture
├── 📄 TASKS.md                         # Implementation tasks
├── 📄 SETUP-COMPLETE.md                # Setup completion report
└── 📄 PROJECT-STRUCTURE.md             # This file
```

---

## File Descriptions

### Core Application Files

#### `main.py`
- Flask application entry point
- Initializes Flask app
- Registers blueprints (routers)
- Configures middleware
- Defines health check endpoints

#### `requirements.txt`
- Python package dependencies
- Versions pinned for reproducibility
- Includes: Flask, SQLAlchemy, requests, python-dotenv

#### `.env`
- Local environment configuration
- Database URL
- Asterisk credentials
- SIP trunk credentials
- TBN API credentials
- Speech processing settings

#### `.env.example`
- Template for `.env` file
- Shows all available configuration options
- Safe to commit to version control

---

### Routers (API Endpoints)

#### `routers/calls.py`
Handles phone call operations:
- **POST /api/call/start** — Initialize new call session
- **POST /api/call/answer** — Process customer response
- **POST /api/call/transfer** — Transfer to human agent

#### `routers/bookings.py`
Handles booking operations:
- **POST /api/booking/save** — Save booking to database
- **GET /api/booking/list** — List bookings with filtering
- **GET /api/booking/{booking_id}** — Get specific booking

---

### Services (Business Logic)

#### `services/bot_service.py`
TBN bot integration:
- Select appropriate bot for business type
- Verify bot certification
- Retrieve bot personality
- Generate responses using bot

#### `services/booking_service.py`
Booking flow management:
- Create booking sessions
- Manage question sequence (9 questions)
- Process customer responses
- Generate booking references

**Questions asked**:
1. Name
2. Pickup location
3. Destination
4. Date
5. Time
6. Number of passengers
7. Luggage amount
8. Flight number (if airport)
9. Callback number

#### `services/speech_service.py`
Speech processing:
- Convert speech to text (faster-whisper)
- Convert text to speech (Piper)
- Detect customer intent

#### `services/database_service.py`
Database operations:
- Save bookings
- Retrieve bookings
- List bookings with filters
- Save call logs

---

### Models (Data Structures)

#### `models/booking.py`
Booking data model with fields:
- id, created_at, caller_number
- name, pickup, destination
- date, time, passengers, luggage
- flight_number, callback_number
- status, bot_id, call_duration
- booking_reference

#### `models/call.py`
Call data model with fields:
- id, created_at, caller_number
- duration, status, bot_id
- transfer_reason, audio_file

---

### Utilities

#### `utils/validators.py`
Input validation functions:
- `validate_phone_number()` — UK phone format
- `validate_date()` — YYYY-MM-DD format
- `validate_time()` — HH:MM format
- `validate_passengers()` — 1-8 passengers

#### `utils/logger.py`
Logging configuration:
- `setup_logger()` — Configure logger with console handler

---

## Database Schema (Future)

### Tables

#### `bookings`
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

#### `call_logs`
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

#### `customers`
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

---

## API Endpoints

### Call Management

#### Start Call
```
POST /api/call/start
Content-Type: application/json

{
    "caller_number": "+447999605080",
    "phone_number": "+447999605080"
}

Response:
{
    "session_id": "session_...",
    "first_question": "What is your name?",
    "status": "started"
}
```

#### Answer Call
```
POST /api/call/answer
Content-Type: application/json

{
    "session_id": "session_...",
    "user_text": "John Smith"
}

Response:
{
    "session_id": "session_...",
    "next_question": "Where are you picking up from?",
    "status": "processing"
}
```

#### Transfer Call
```
POST /api/call/transfer
Content-Type: application/json

{
    "session_id": "session_...",
    "reason": "Customer requested human agent"
}

Response:
{
    "session_id": "session_...",
    "status": "transferred",
    "reason": "Customer requested human agent"
}
```

### Booking Management

#### Save Booking
```
POST /api/booking/save
Content-Type: application/json

{
    "caller_number": "+447999605080",
    "name": "John Smith",
    "pickup": "Terminal 3",
    "destination": "Central London",
    "date": "2026-05-15",
    "time": "14:30",
    "passengers": 2,
    "luggage": "2 large bags",
    "flight_number": "BA123",
    "callback_number": "+447999605080",
    "bot_id": "bot_taxi_001"
}

Response:
{
    "booking_id": "booking_...",
    "booking_reference": "HAP-12345678",
    "status": "saved"
}
```

#### List Bookings
```
GET /api/booking/list?date=2026-05-15&status=saved&limit=50&offset=0

Response:
{
    "bookings": [...],
    "total": 10,
    "limit": 50,
    "offset": 0
}
```

#### Get Booking
```
GET /api/booking/booking_123

Response:
{
    "booking_id": "booking_123",
    "name": "John Smith",
    "status": "saved",
    ...
}
```

---

## Development Workflow

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Run Application
```bash
python main.py
```

### 3. Access API
```
http://localhost:5000
```

### 4. Make Changes
- Edit files in `routers/`, `services/`, `models/`, `utils/`
- Changes are reflected on next request (Flask debug mode)

### 5. Test Endpoints
```bash
# Test health check
curl http://localhost:5000/health

# Test start call
curl -X POST http://localhost:5000/api/call/start \
  -H "Content-Type: application/json" \
  -d '{"caller_number": "+447999605080", "phone_number": "+447999605080"}'
```

---

## Next Steps

### Phase 1 Tasks

- [x] Task 1.1: Set up development environment
- [ ] Task 1.2: Install Asterisk on test server
- [ ] Task 1.3: Configure Vodafone SIP trunk
- [ ] Task 1.4: Test SIP connection
- [ ] Task 2.1: Create FastAPI project structure
- [ ] Task 2.2: Implement call handler endpoints
- [ ] Task 2.3: Implement booking flow logic
- [ ] Task 2.4: Create database schema
- [ ] Task 2.5: Implement database operations
- [ ] Task 3.1: Install faster-whisper
- [ ] Task 3.2: Install Piper TTS
- [ ] Task 3.3: Integrate speech-to-text
- [ ] Task 3.4: Integrate text-to-speech
- [ ] Task 3.5: Test speech processing
- [ ] Task 4.1: Integrate TBN bot selection
- [ ] Task 4.2: Implement bot certification verification
- [ ] Task 4.3: Test end-to-end call flow
- [ ] Task 4.4: Create admin dashboard (basic)
- [ ] Task 4.5: Documentation & deployment

---

## Notes

- All code follows PEP 8 style guidelines
- Logging is configured for debugging
- Environment variables are used for configuration
- Database operations are abstracted in services
- API endpoints are RESTful
- Error handling is implemented throughout

---

**Status**: Development environment ready  
**Next Action**: Task 1.2 (Install Asterisk on test server)
