"""
Hardin-AI Phone — AGI Server
Handles incoming phone calls from Asterisk via FastAGI protocol.
Runs the booking flow conversation with callers.
"""

import socketserver
import logging
import json
import uuid
import subprocess
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Booking questions - conditional flow
QUESTIONS = [
    {"key": "name", "ask": "Can I take your name please?"},
    {"key": "pickup", "ask": "Where are you picking up from?"},
    {"key": "destination", "ask": "Where are you going to?"},
    {"key": "date", "ask": "What date do you need the taxi for?"},
    {"key": "time", "ask": "What time do you need to be picked up?"},
    {"key": "passengers", "ask": "How many passengers will there be?"},
    {"key": "luggage", "ask": "How much luggage will you have?"},
    {"key": "callback", "ask": "And what is the best number to reach you on?"},
]

# Only asked if pickup is an airport
AIRPORT_QUESTION = {"key": "flight", "ask": "What is your flight number?"}

# Airport keywords to detect airport pickups
AIRPORT_KEYWORDS = [
    "heathrow", "gatwick", "stansted", "luton", "city airport",
    "terminal", "airport", "arrivals", "departures", "t1", "t2", "t3", "t4", "t5"
]

GREETING = "Hello, thank you for calling Heathrow Black Cabs. How can I help you today? I can help you with a booking, provide information about our services, or transfer you to the office."
MENU_PROMPT = "Would you like to make a booking, get some information, or speak to the office?"
BOOKING_START = "Great, let me help you book a taxi. I just need a few details."
INFO_RESPONSE = "We provide airport transfers and taxi services across London. Our rates start from 45 pounds for Heathrow transfers. Would you like to make a booking?"
CONFIRMATION_PREFIX = "Let me read that back to you. "
BOOKING_COMPLETE = "Your booking is confirmed. Your reference number is {}. Thank you for calling Heathrow Black Cabs. Goodbye."
TRANSFER_MSG = "No problem, I will transfer you to the office now. Please hold."
LIVE_AGENT_NUMBER = "+447740304061"

# Audio file directory
AUDIO_DIR = "/tmp/hardin-ai-audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# In-memory store for completed bookings
completed_bookings = []
BOOKINGS_FILE = "/opt/hardin-ai-phone/bookings.json"


def save_booking(booking):
    """Save booking to JSON file."""
    bookings = []
    if os.path.exists(BOOKINGS_FILE):
        try:
            with open(BOOKINGS_FILE, "r") as f:
                bookings = json.load(f)
        except:
            bookings = []
    bookings.append(booking)
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=2)
    completed_bookings.append(booking)


PIPER_BIN = "/home/ubuntu/.local/bin/piper"
PIPER_MODEL = "/opt/hardin-ai-phone/voices/en_GB-alba-medium.onnx"


def text_to_audio(text, filename):
    """Convert text to WAV audio file using Piper TTS.
    
    Uses British English female voice (alba).
    Generates 8kHz mono WAV suitable for Asterisk playback.
    """
    raw_file = f"{filename}_raw.wav"
    
    # Generate speech with Piper TTS (natural sounding)
    try:
        process = subprocess.run(
            [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", raw_file],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30
        )
        
        if not os.path.exists(raw_file):
            raise FileNotFoundError("Piper failed to generate audio")
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback to espeak-ng if Piper fails
        logger.warning("Piper TTS failed, falling back to espeak-ng")
        subprocess.run(
            ["espeak-ng", "-w", raw_file, "-s", "140", "-p", "50", text],
            capture_output=True
        )
    
    # Convert to 8kHz mono (Asterisk format) using sox
    subprocess.run(
        ["sox", raw_file, "-r", "8000", "-c", "1", "-b", "16", f"{filename}.wav"],
        capture_output=True
    )
    
    # Clean up raw file
    try:
        os.remove(raw_file)
    except:
        pass
    
    return f"{filename}.wav"


def transcribe_audio(audio_file):
    """Transcribe audio file to text.
    
    Tries multiple methods in order:
    1. faster-whisper (best quality, if installed)
    2. Google Speech Recognition (free, needs internet)
    3. Returns empty string as fallback
    """
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu")
        segments, _ = model.transcribe(audio_file)
        text = " ".join([s.text for s in segments])
        return text.strip()
    except ImportError:
        pass

    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception as e:
        logger.warning(f"Speech recognition failed: {e}")

    return ""


class AGIHandler(socketserver.StreamRequestHandler):
    """Handles a single AGI call from Asterisk."""

    def handle(self):
        """Main handler for an incoming AGI connection."""
        try:
            # Read AGI environment variables
            env = self._read_env()
            caller = env.get("agi_callerid", "unknown")
            channel = env.get("agi_channel", "unknown")
            call_id = uuid.uuid4().hex[:8]

            logger.info(f"[{call_id}] New call from {caller} on {channel}")

            # Answer the call
            self._agi_command("ANSWER")

            # Play greeting
            self._speak(GREETING, call_id)

            # Listen for initial response (hello, booking, info, etc.)
            intent = self._get_intent(call_id)

            if intent == "transfer":
                self._speak(TRANSFER_MSG, call_id)
                self._agi_command(f'EXEC Dial "PJSIP/{LIVE_AGENT_NUMBER}@zadarma-endpoint,60,tT"')
                return

            if intent == "info":
                self._speak(INFO_RESPONSE, call_id)
                # Listen if they want to book after info
                response = self._listen(call_id)
                if response and self._is_booking_intent(response):
                    intent = "booking"
                else:
                    self._speak("Is there anything else I can help with? If not, thank you for calling. Goodbye.", call_id)
                    self._agi_command("HANGUP")
                    return

            # Booking flow
            if intent == "booking" or intent == "unknown":
                self._speak(BOOKING_START, call_id)
                booking = self._run_booking_flow(caller, call_id)
            else:
                booking = None

            if booking is None:
                # Caller requested transfer
                self._speak(TRANSFER_MSG, call_id)
                # Transfer to live agent via Zadarma
                self._agi_command(f'EXEC Dial "PJSIP/{LIVE_AGENT_NUMBER}@zadarma-endpoint,60,tT"')
                return

            # Confirm booking
            ref = f"HAP-{uuid.uuid4().hex[:6].upper()}"
            confirmation = self._build_confirmation(booking)
            self._speak(confirmation, call_id)
            
            # Ask for confirmation
            confirm_response = self._listen(call_id)
            
            if confirm_response and any(word in confirm_response.lower() for word in ["no", "wrong", "incorrect", "change", "not right"]):
                self._speak("I'm sorry about that. Let me transfer you to the office to sort this out.", call_id)
                self._agi_command(f'EXEC Dial "PJSIP/{LIVE_AGENT_NUMBER}@zadarma-endpoint,60,tT"')
                return
            
            # Confirmed - save and complete
            self._speak(BOOKING_COMPLETE.format(ref), call_id)

            # Save booking
            booking["reference"] = ref
            booking["caller"] = caller
            booking["timestamp"] = datetime.now().isoformat()
            booking["call_id"] = call_id
            save_booking(booking)
            logger.info(f"[{call_id}] Booking saved: {ref} for {caller}")

            # Hang up
            self._agi_command("HANGUP")

        except BrokenPipeError:
            logger.warning(f"Call disconnected (broken pipe)")
        except Exception as e:
            logger.error(f"Error handling call: {e}", exc_info=True)
            try:
                self._agi_command("HANGUP")
            except:
                pass

    def _read_env(self):
        """Read AGI environment variables sent by Asterisk."""
        env = {}
        while True:
            line = self.rfile.readline().decode("utf-8").strip()
            if line == "":
                break
            if ":" in line:
                key, value = line.split(":", 1)
                env[key.strip()] = value.strip()
        return env

    def _agi_command(self, command):
        """Send an AGI command and read the response."""
        self.wfile.write(f"{command}\n".encode("utf-8"))
        self.wfile.flush()
        response = self.rfile.readline().decode("utf-8").strip()
        logger.debug(f"AGI cmd: {command} -> {response}")
        return response

    def _speak(self, text, call_id="0"):
        """Convert text to speech and play to caller via Asterisk."""
        # Generate unique audio filename
        audio_id = uuid.uuid4().hex[:8]
        filepath = f"{AUDIO_DIR}/{call_id}_{audio_id}"
        
        # Generate audio file
        text_to_audio(text, filepath)
        
        # Play the file via Asterisk (without .wav extension)
        self._agi_command(f'EXEC Playback "{filepath}"')
        
        # Clean up
        try:
            os.remove(f"{filepath}.wav")
        except:
            pass

    def _listen(self, call_id="0", timeout=10):
        """Record caller speech and return transcription."""
        audio_id = uuid.uuid4().hex[:8]
        filepath = f"{AUDIO_DIR}/{call_id}_{audio_id}_rec"
        
        # Record audio from caller
        # RECORD FILE <filename> <format> <escape_digits> <timeout> [offset] [BEEP] [s=<silence>]
        self._agi_command(
            f'RECORD FILE "{filepath}" "wav" "#*" {timeout * 1000} 0 s=3'
        )
        
        # Transcribe the recording
        audio_file = f"{filepath}.wav"
        if os.path.exists(audio_file):
            text = transcribe_audio(audio_file)
            # Clean up recording
            try:
                os.remove(audio_file)
            except:
                pass
            return text
        
        return ""

    def _run_booking_flow(self, caller, call_id):
        """Run through all booking questions with conditional logic."""
        booking = {}

        for q in QUESTIONS:
            # Ask the question
            self._speak(q["ask"], call_id)

            # Listen for response, with retry logic
            max_attempts = 3
            response = None

            for attempt in range(max_attempts):
                response = self._listen(call_id)
                
                logger.info(f"[{call_id}] Q: {q['key']} (attempt {attempt+1}) -> A: {response}")

                # Check for transfer request
                if response and self._is_transfer_request(response):
                    logger.info(f"[{call_id}] Transfer requested by {caller}")
                    return None

                # Check if caller asked to repeat
                if response and self._is_repeat_request(response):
                    self._speak("Of course. " + q["ask"], call_id)
                    continue

                # If empty response, ask again
                if not response:
                    if attempt < max_attempts - 1:
                        self._speak("Sorry, I didn't catch that. " + q["ask"], call_id)
                        continue
                    else:
                        self._speak("Let me move on to the next question.", call_id)
                        response = "not provided"

                # Got a valid response, break out of retry loop
                break

            # Check for transfer again
            if response and self._is_transfer_request(response):
                return None

            booking[q["key"]] = response

            # After pickup question, check if it's an airport and ask flight number
            if q["key"] == "pickup" and self._is_airport_pickup(response):
                self._speak(AIRPORT_QUESTION["ask"], call_id)
                flight_response = self._listen(call_id)
                if flight_response and self._is_repeat_request(flight_response):
                    self._speak("Of course. " + AIRPORT_QUESTION["ask"], call_id)
                    flight_response = self._listen(call_id)
                booking["flight"] = flight_response or "not provided"

        return booking

    def _get_intent(self, call_id):
        """Listen to caller and determine their intent."""
        response = self._listen(call_id)
        
        if not response:
            # If they didn't say anything, ask again briefly
            self._speak("Are you looking to make a booking today?", call_id)
            response = self._listen(call_id)
        
        if not response:
            return "booking"  # Default to booking if still no response
        
        # Check for transfer/office
        if self._is_transfer_request(response):
            return "transfer"
        
        # Check for information request
        if self._is_info_intent(response):
            return "info"
        
        # Check for booking intent
        if self._is_booking_intent(response):
            return "booking"
        
        # If they just said hello/hi/yeah, assume booking
        if self._is_greeting(response):
            self._speak("Would you like to make a booking?", call_id)
            response = self._listen(call_id)
            if response and self._is_transfer_request(response):
                return "transfer"
            if response and self._is_info_intent(response):
                return "info"
            return "booking"
        
        return "booking"  # Default to booking

    def _is_transfer_request(self, text):
        """Check if caller wants to speak to a person."""
        transfer_phrases = [
            "transfer", "speak to someone", "speak to a person",
            "office", "human", "agent", "real person", "operator",
            "speak to office", "talk to someone"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in transfer_phrases)

    def _is_info_intent(self, text):
        """Check if caller wants information."""
        info_phrases = [
            "information", "info", "how much", "price", "cost",
            "rates", "services", "what do you", "hours", "opening"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in info_phrases)

    def _is_booking_intent(self, text):
        """Check if caller wants to make a booking."""
        booking_phrases = [
            "book", "booking", "taxi", "cab", "ride", "pick up",
            "pickup", "yes", "yeah", "please", "i need", "i want",
            "i'd like"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in booking_phrases)

    def _is_greeting(self, text):
        """Check if caller just said hello."""
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "alright"]
        text_lower = text.lower().strip()
        return any(text_lower.startswith(g) for g in greetings)

    def _is_airport_pickup(self, pickup_location):
        """Check if the pickup location is an airport."""
        if not pickup_location:
            return False
        pickup_lower = pickup_location.lower()
        return any(keyword in pickup_lower for keyword in AIRPORT_KEYWORDS)

    def _is_repeat_request(self, text):
        """Check if the caller is asking to repeat the question."""
        repeat_phrases = [
            "repeat", "say again", "say that again", "what was that",
            "pardon", "sorry what", "come again", "one more time",
            "didn't hear", "didn't catch", "can you repeat",
            "what did you say", "again please"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in repeat_phrases)

    def _build_confirmation(self, booking):
        """Build a confirmation message from booking data."""
        parts = [CONFIRMATION_PREFIX]
        
        if booking.get("name") and booking["name"] != "not provided":
            parts.append(f"Name: {booking['name']}.")
        if booking.get("pickup") and booking["pickup"] != "not provided":
            parts.append(f"Pickup from: {booking['pickup']}.")
        if booking.get("destination") and booking["destination"] != "not provided":
            parts.append(f"Going to: {booking['destination']}.")
        if booking.get("date") and booking["date"] != "not provided":
            parts.append(f"Date: {booking['date']}.")
        if booking.get("time") and booking["time"] != "not provided":
            parts.append(f"Time: {booking['time']}.")
        if booking.get("passengers") and booking["passengers"] != "not provided":
            parts.append(f"Passengers: {booking['passengers']}.")
        if booking.get("luggage") and booking["luggage"] != "not provided":
            parts.append(f"Luggage: {booking['luggage']}.")
        if booking.get("flight") and booking["flight"].lower() not in ("no", "not provided"):
            parts.append(f"Flight number: {booking['flight']}.")
        if booking.get("callback") and booking["callback"] != "not provided":
            parts.append(f"Callback number: {booking['callback']}.")

        parts.append("Is that all correct?")
        return " ".join(parts)


class AGIServer(socketserver.ThreadingTCPServer):
    """Threaded AGI server — handles multiple concurrent calls."""
    allow_reuse_address = True
    daemon_threads = True


def get_bookings():
    """Return all completed bookings (for API/dashboard access)."""
    return completed_bookings


def main():
    """Start the AGI server."""
    host = "127.0.0.1"
    port = 4573

    server = AGIServer((host, port), AGIHandler)
    logger.info(f"=== Hardin-AI Phone AGI Server ===")
    logger.info(f"Listening on {host}:{port}")
    logger.info(f"TTS: espeak-ng")
    logger.info(f"STT: SpeechRecognition (Google)")
    logger.info(f"Transfer number: {LIVE_AGENT_NUMBER}")
    logger.info(f"Waiting for calls...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
