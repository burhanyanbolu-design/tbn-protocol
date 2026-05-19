"""
Booking data model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Booking(BaseModel):
    """Booking data model"""
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    caller_number: str
    name: str
    pickup: str
    destination: str
    date: str
    time: str
    passengers: int
    luggage: str
    flight_number: Optional[str] = None
    callback_number: str
    status: str = "pending"
    bot_id: Optional[str] = None
    call_duration: Optional[int] = None
    booking_reference: Optional[str] = None
    
    class Config:
        from_attributes = True
