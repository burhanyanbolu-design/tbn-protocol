"""
Input validation utilities
"""

import re
from typing import Tuple

def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate UK phone number
    
    Args:
        phone: Phone number to validate
    
    Returns:
        is_valid: True if valid
        message: Validation message
    """
    # UK phone number pattern
    pattern = r'^(\+44|0)[0-9]{10,11}$'
    
    if re.match(pattern, phone):
        return True, "Valid phone number"
    
    return False, "Invalid phone number format"

def validate_date(date_str: str) -> Tuple[bool, str]:
    """
    Validate date format (YYYY-MM-DD)
    
    Args:
        date_str: Date string to validate
    
    Returns:
        is_valid: True if valid
        message: Validation message
    """
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, "Valid date"
    except ValueError:
        return False, "Invalid date format (use YYYY-MM-DD)"

def validate_time(time_str: str) -> Tuple[bool, str]:
    """
    Validate time format (HH:MM)
    
    Args:
        time_str: Time string to validate
    
    Returns:
        is_valid: True if valid
        message: Validation message
    """
    try:
        from datetime import datetime
        datetime.strptime(time_str, "%H:%M")
        return True, "Valid time"
    except ValueError:
        return False, "Invalid time format (use HH:MM)"

def validate_passengers(passengers: int) -> Tuple[bool, str]:
    """
    Validate number of passengers
    
    Args:
        passengers: Number of passengers
    
    Returns:
        is_valid: True if valid
        message: Validation message
    """
    if 1 <= passengers <= 8:
        return True, "Valid passenger count"
    
    return False, "Passenger count must be between 1 and 8"
