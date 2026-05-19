"""
Call data model
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Call(BaseModel):
    """Call data model"""
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    caller_number: str
    duration: int
    status: str
    bot_id: Optional[str] = None
    transfer_reason: Optional[str] = None
    audio_file: Optional[str] = None
    
    class Config:
        from_attributes = True
