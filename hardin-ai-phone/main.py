"""
Hardin-AI Phone - Main Application
FastAPI application for phone booking system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hardin-AI Phone",
    description="Plugin-based phone booking system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routers import calls, bookings

# Include routers
app.include_router(calls.router, prefix="/api/call", tags=["calls"])
app.include_router(bookings.router, prefix="/api/booking", tags=["bookings"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hardin-AI Phone API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "hardin-ai-phone"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
