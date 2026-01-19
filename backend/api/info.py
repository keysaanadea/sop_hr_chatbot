"""
DENAI Info API Routes - CLEAN SYSTEM INFORMATION
===============================================
Pure system information endpoint - NO business logic
NO engine probing, NO HR availability checks
"""

import logging
import os
from fastapi import APIRouter
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from models.requests import (
    HealthResponse, SpeechStatusResponse, UserRoleResponse,
    ConfigResponse, ModelConfig, SpeechConfig, TimeoutConfig,
    ModeConfig, FeatureFlags
)

from app.config import (
    ENVIRONMENT, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    SPEECH_LANGUAGE_DEFAULT, TTS_PRIMARY_ENGINE, TTS_FALLBACK_ENGINE,
    ELEVENLABS_SETTINGS, OPENAI_TTS_SETTINGS, ELEVENLABS_API_KEY,
    API_TIMEOUT_DEFAULT, API_TIMEOUT_CALL_MODE, API_TIMEOUT_TTS,
    CALL_MODE_TEMPERATURE, CHAT_MODE_TEMPERATURE,
    CALL_MODE_MAX_TOKENS, CHAT_MODE_MAX_TOKENS,
    FEATURE_NATURAL_TTS, FEATURE_VERBOSE_LOGGING,
    ELEVENLABS_VOICE_ID_INDONESIAN
)

logger = logging.getLogger(__name__)
router = APIRouter()

# =====================
# SYSTEM INFORMATION ENDPOINTS
# =====================

@router.get("/", response_model=HealthResponse)
async def system_info():
    """
    Get general system information and status
    
    Returns:
        HealthResponse: System status and capabilities
    """
    features = [
        "🎤 Natural conversational TTS",
        "📱 HTML text output preserved", 
        "🔊 Smart text cleaning for speech",
        "💰 Cost-optimized configuration",
        "📌 Session management",
        "🔥 Fixed ElevenLabs integration",
        "🎯 Proper mode detection (text vs voice)",
        "✅ Clean architecture with separated concerns",
        "✅ Dynamic tools routing (API → ChatService → tools.py → engines/)",
        "✅ Production-ready structure"
    ]
    
    return HealthResponse(
        status="healthy",
        version="8.0.0",
        environment=ENVIRONMENT,
        features=features,
        config_status={
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "elevenlabs_configured": bool(ELEVENLABS_API_KEY),
            "model": LLM_MODEL,
            "tts_engines": f"{TTS_PRIMARY_ENGINE} → {TTS_FALLBACK_ENGINE}",
            "natural_tts": FEATURE_NATURAL_TTS,
            "verbose_logging": FEATURE_VERBOSE_LOGGING,
            "architecture": "clean_layered"
        }
    )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Detailed health check endpoint
    
    Returns:
        HealthResponse: Comprehensive health status
    """
    return await system_info()

@router.get("/user/role", response_model=UserRoleResponse)
async def get_user_role():
    """
    Get user role and permissions
    
    Returns:
        UserRoleResponse: User role information
    """
    role = os.getenv("USER_ROLE", "Employee")
    is_hr = role.upper() == "HR"
    
    return UserRoleResponse(
        role=role,
        is_hr=is_hr,
        permissions={
            "access_sop": True,
            "speech_features": True,
            "natural_tts": FEATURE_NATURAL_TTS,
            "hr_access_via_chat": is_hr  # HR functionality via chat tools routing
        }
    )

@router.get("/speech/status", response_model=SpeechStatusResponse)
async def speech_system_status():
    """
    Get speech system status and configuration
    
    Returns:
        SpeechStatusResponse: Speech system information
    """
    return SpeechStatusResponse(
        speech_recognition={
            "available": True,
            "engine": "OpenAI Whisper",
            "language": SPEECH_LANGUAGE_DEFAULT,
            "model": "whisper-1"
        },
        text_to_speech={
            "available": True,
            "primary_engine": TTS_PRIMARY_ENGINE,
            "fallback_engine": TTS_FALLBACK_ENGINE,
            "voice_id": ELEVENLABS_VOICE_ID_INDONESIAN,
            "elevenlabs_model": ELEVENLABS_SETTINGS["model"],
            "openai_voice": OPENAI_TTS_SETTINGS["voice"],
            "natural_speech": FEATURE_NATURAL_TTS,
            "elevenlabs_configured": bool(ELEVENLABS_API_KEY)
        },
        ai_model={
            "model": LLM_MODEL,
            "chat_temperature": CHAT_MODE_TEMPERATURE,
            "call_temperature": CALL_MODE_TEMPERATURE,
            "max_tokens_chat": CHAT_MODE_MAX_TOKENS,
            "max_tokens_call": CALL_MODE_MAX_TOKENS
        }
    )

@router.get("/services/status")
async def all_services_status():
    """
    Get status of all system services
    
    Returns:
        dict: Status of all services
    """
    try:
        # Import services to check their status
        from services.chat_service import ChatService
        from services.tts_service import TTSService
        from services.stt_service import STTService
        
        chat_service = ChatService()
        tts_service = TTSService()
        stt_service = STTService()
        
        return {
            "overall_status": "healthy",
            "architecture": "API → ChatService → tools.py → engines/",
            "services": {
                "chat": {
                    "status": "active",
                    "service": "ChatService",
                    "description": "Core AI conversation orchestration"
                },
                "tts": {
                    "status": "active", 
                    "service": "TTSService",
                    "engines": [TTS_PRIMARY_ENGINE, TTS_FALLBACK_ENGINE]
                },
                "stt": {
                    "status": "active",
                    "service": "STTService", 
                    "engine": "OpenAI Whisper"
                }
            },
            "note": "HR and SOP functionality accessed via unified chat interface with dynamic tools routing"
        }
        
    except Exception as e:
        logger.error(f"Services status error: {e}")
        return {
            "overall_status": "degraded",
            "error": str(e),
            "services": {
                "chat": {"status": "unknown"},
                "tts": {"status": "unknown"},
                "stt": {"status": "unknown"}
            }
        }

@router.get("/version")
async def version_info():
    """
    Get version and build information
    
    Returns:
        dict: Version information
    """
    return {
        "version": "8.0.0",
        "architecture": "clean_layered",
        "release_date": "2024-01-01",
        "components": {
            "api_routes": ["chat", "speech", "sessions", "info"],
            "services": ["chat_service", "tts_service", "stt_service"],
            "routing": "Dynamic tools routing (tools.py)",
            "engines": "Separated engines/ folder (SOP RAG + HR Analytics)",
            "utils": ["text_utils"],
            "models": ["requests", "responses"]
        },
        "improvements": [
            "✅ Clean layered architecture",
            "✅ Dynamic tools routing via tools.py", 
            "✅ Proper separation of concerns",
            "✅ SOP RAG protection maintained",
            "✅ HR analytics via unified chat interface",
            "✅ Production-ready implementation"
        ],
        "environment": ENVIRONMENT,
        "build_info": {
            "python_version": "3.9+",
            "framework": "FastAPI",
            "database": "Supabase + SQLite",
            "tts_engines": [TTS_PRIMARY_ENGINE, TTS_FALLBACK_ENGINE],
            "ai_model": LLM_MODEL,
            "routing": "Dynamic via tools.py based on user role and query type"
        }
    }

@router.get("/endpoints")
async def list_api_endpoints():
    """
    List all available API endpoints
    
    Returns:
        dict: Available API endpoints by category
    """
    return {
        "chat_endpoints": [
            "POST /ask - Unified conversation interface (SOP + HR via dynamic routing)",
            "POST /call/process - Voice call mode processing",
            "GET /tools - List available chat tools",
            "GET /status - Chat system status"
        ],
        "speech_endpoints": [
            "POST /speech/text-to-speech - Convert text to speech",
            "POST /speech/speech-to-text - Convert speech to text", 
            "GET /speech/status - Speech system status",
            "GET /speech/engines - List available engines",
            "GET /speech/test - Test speech system"
        ],
        "session_endpoints": [
            "GET /sessions - List all sessions",
            "GET /sessions/{id}/history - Get session history",
            "POST /sessions/{id}/pin - Toggle session pin",
            "DELETE /sessions/{id} - Delete session",
            "GET /sessions/stats/overview - Session statistics"
        ],
        "info_endpoints": [
            "GET / - System information",
            "GET /health - Health check",
            "GET /user/role - User role information",
            "GET /version - Version information",
            "GET /services/status - All services status",
            "GET /endpoints - This endpoint list"
        ],
        "development_endpoints": [
            "GET /config - Configuration (dev only)",
            "GET /debug/logs - Recent logs (dev only)"
        ] if ENVIRONMENT == "development" else [],
        "note": "HR functionality accessed via POST /ask with role-based dynamic routing"
    }

# =====================
# DEVELOPMENT ENDPOINTS
# =====================

if ENVIRONMENT == "development":
    
    @router.get("/config", response_model=ConfigResponse)
    async def get_current_config():
        """
        Development-only endpoint to inspect configuration
        
        Returns:
            ConfigResponse: Complete system configuration
        """
        return ConfigResponse(
            model_config=ModelConfig(
                llm_model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS
            ),
            speech_config=SpeechConfig(
                language=SPEECH_LANGUAGE_DEFAULT,
                primary_tts=TTS_PRIMARY_ENGINE,
                fallback_tts=TTS_FALLBACK_ENGINE,
                elevenlabs_settings=ELEVENLABS_SETTINGS,
                openai_settings=OPENAI_TTS_SETTINGS
            ),
            timeout_config=TimeoutConfig(
                default=API_TIMEOUT_DEFAULT,
                call_mode=API_TIMEOUT_CALL_MODE,
                tts=API_TIMEOUT_TTS
            ),
            mode_config=ModeConfig(
                call_temperature=CALL_MODE_TEMPERATURE,
                chat_temperature=CHAT_MODE_TEMPERATURE,
                call_max_tokens=CALL_MODE_MAX_TOKENS,
                chat_max_tokens=CHAT_MODE_MAX_TOKENS
            ),
            feature_flags=FeatureFlags(
                natural_tts=FEATURE_NATURAL_TTS,
                verbose_logging=FEATURE_VERBOSE_LOGGING
            ),
            environment=ENVIRONMENT
        )
    
    @router.get("/debug/logs")
    async def get_recent_logs():
        """
        Development-only endpoint to get recent log entries
        
        Returns:
            dict: Recent log information
        """
        return {
            "note": "Log retrieval not implemented",
            "logging_level": "DEBUG" if FEATURE_VERBOSE_LOGGING else "INFO",
            "loggers": [
                "main",
                "services.chat_service", 
                "services.tts_service",
                "services.stt_service",
                "api.chat",
                "api.speech",
                "api.sessions",
                "api.info"
            ]
        }

# =====================
# CLEAN STARTUP LOGGING
# =====================

logger.info("📋 Info API routes loaded - Clean System Information:")
logger.info(f"   - Architecture: Clean Layered (API → ChatService → tools.py → engines/)")
logger.info(f"   - Environment: {ENVIRONMENT}")
logger.info(f"   - Version: 8.0.0")
logger.info(f"   - Routing: Dynamic tools routing based on role + query")