"""
DENAI API - Main Application Setup
Production-ready modular FastAPI application with clean architecture
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import (
    ENVIRONMENT,
    FEATURE_VERBOSE_LOGGING,
    ELEVENLABS_API_KEY,
)

from backend.api.chat import router as chat_router
from backend.api.speech import router as speech_router  
from backend.api.sessions import router as sessions_router
from backend.api.info import router as info_router

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if FEATURE_VERBOSE_LOGGING else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DENAI - AI Assistant API", 
    version="7.0.0",
    description="Modular FastAPI application with clean architecture"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - CLEAN ARCHITECTURE
app.include_router(chat_router, prefix="", tags=["Chat"])
app.include_router(speech_router, prefix="/speech", tags=["Speech"])
app.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
app.include_router(info_router, prefix="", tags=["Info"])
# NOTE: HR functionality is accessed via chat router with dynamic tools routing


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 DENAI API Starting...")
    logger.info(f"✅ Environment: {ENVIRONMENT}")
    logger.info(f"✅ ElevenLabs TTS: {'CONFIGURED' if ELEVENLABS_API_KEY else 'NOT CONFIGURED'}")
    logger.info("🎯 Clean architecture: API → ChatService → tools.py → engines/")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("👋 DENAI API Shutting down...")


# History endpoint (session management utility)
@app.get("/history/{session_id}")
async def get_history_endpoint(session_id: str):
    """Get conversation history for session"""
    from backend.api.sessions import get_session_history
    return await get_session_history(session_id)


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "status": "active",
        "service": "DENAI - Modular AI Assistant API",
        "version": "7.0.0",
        "architecture": "clean_layered",
        "flow": "API → ChatService → tools.py → engines/",
        "improvements": [
            "✅ Clean layered architecture",
            "✅ Dynamic tools routing via tools.py",
            "✅ Proper separation of concerns",
            "✅ SOP RAG protection maintained",
            "✅ HR analytics via unified chat interface"
        ],
        "endpoints": [
            "💬 Chat API (/ask) - Main conversation interface",
            "🎤 Speech API (/speech/*) - Voice interaction",
            "💾 Session Management (/sessions/*) - Conversation history",
            "ℹ️ System Info (/*) - API information"
        ],
        "note": "HR analytics accessed via /ask endpoint with role-based routing"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting DENAI API (Clean Architecture)...")
    print(f"✅ Environment: {ENVIRONMENT}")
    print("🎯 Flow: API → ChatService → tools.py → engines/")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True if ENVIRONMENT == "development" else False
    )