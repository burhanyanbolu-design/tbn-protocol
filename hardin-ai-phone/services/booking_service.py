"""
Booking service - handles booking logic
"""

import logging
from typing import Dict, List, Optional
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class BookingService:
    """Service for managing bookings"""
    
    # Questions to ask in order
    QUESTIONS = [
        "What is your name?",
        "Where are you picking up from?",
        "Where are you going to?",
        "What date do you need the booking for?",
        "What time do you need the booking for?",
        "How many passengers?",
        "How much luggage do you have?",
        "Is this an airport pickup? If yes, what's your flight number?",
        "What's your callback number?"
    ]
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, caller_number: str) -> str:
        """Create a new booking session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "caller_number": caller_number,
            "created_at": datetime.now(),
            "current_question": 0,
            "responses": {},
            "status": "active"
        }
        logger.info(f"Created session {session_id} for {caller_number}")
        return session_id
    
    def get_current_question(self, session_id: str) -> Optional[str]:
        """Get the current question for a session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        question_index = session["current_question"]
        
        if question_index < len(self.QUESTIONS):
            return self.QUESTIONS[question_index]
        
        return None
    
    def process_response(self, session_id: str, response: str) -> Dict:
        """Process customer response and move to next question"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        question_index = session["current_question"]
        
        # Store response
        session["responses"][question_index] = response
        
        # Move to next question
        session["current_question"] += 1
        
        # Check if all questions answered
        if session["current_question"] >= len(self.QUESTIONS):
            session["status"] = "completed"
            return {
                "status": "completed",
                "booking_data": session["responses"]
            }
        
        # Return next question
        next_question = self.QUESTIONS[session["current_question"]]
        return {
            "status": "next_question",
            "question": next_question
        }
    
    def get_booking_data(self, session_id: str) -> Optional[Dict]:
        """Get booking data from session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return session["responses"]
    
    def generate_booking_reference(self) -> str:
        """Generate a booking reference"""
        return f"HAP-{uuid.uuid4().hex[:8].upper()}"
