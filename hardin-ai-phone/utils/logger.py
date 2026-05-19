"""
Logging configuration
"""

import logging
import sys

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up logger with console handler
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
