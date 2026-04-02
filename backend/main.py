"""
DENAI API - Main Application Setup
Production-ready modular FastAPI application with clean architecture.
(UNIVERSAL ANALYTICS EDITION + SCHEMA EXPLORER)
"""

import socket
import logging

# =========================================================================
# MAGIC FIX: OBAT ANTI-HANG OPENAI API (KASUS MAC/IPV6)
# Hanya aktif di environment development (Mac/lokal).
# Di production (Linux), patch ini tidak diperlukan dan dinonaktifkan.
# =========================================================================
import os as _os
if _os.getenv("ENVIRONMENT", "development") == "development":
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [response for response in responses if response[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo
# =========================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.limiter import limiter

# ✅ FIX BUG: Import dari config tanpa sys.path hack
import os
from app.config import (
    ENVIRONMENT,
    FEATURE_VERBOSE_LOGGING,
    ELEVENLABS_API_KEY,
)

# Absolute Imports untuk semua router
from backend.api.chat import router as chat_router
from backend.api.speech import router as speech_router  
from backend.api.sessions import router as sessions_router
from backend.api.info import router as info_router
from backend.api.schema import router as schema_router  # ✅ NEW: Schema Explorer

# ✅ FIX KUNCI: Import Recommender untuk melayani Endpoint Katalog Chart!
from engines.hr.visualization.viz_recommender import UniversalVizRecommender

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if FEATURE_VERBOSE_LOGGING else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DENAI - AI Assistant API",
    version="8.1.0",
    description="Modular FastAPI application with Universal Analytics Architecture + Schema Explorer"
)

# Setup rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
# Set ALLOWED_ORIGINS in .env for production, e.g.: ALLOWED_ORIGINS=https://yourdomain.com
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if _raw_origins:
    CORS_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
else:
    # Development fallback — allow all
    CORS_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

# ✅ CLEAN ARCHITECTURE ROUTING
app.include_router(chat_router, prefix="", tags=["Chat"])
app.include_router(speech_router, prefix="/speech", tags=["Speech"])
app.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
app.include_router(info_router, prefix="", tags=["Info"])
app.include_router(schema_router)  # ✅ NEW: Schema Explorer routes (/api/schema/)

# ==============================================================================
# 🎯 ENDPOINT VISUALISASI KEMBALI DIBUKA (Hanya untuk Katalog)
# ==============================================================================
@app.get("/api/viz/chart-types", tags=["Visualization"])
async def get_chart_types():
    """
    Endpoint untuk melayani request pilihan/katalog chart dari Frontend.
    Tidak melakukan rendering, hanya memberikan metadata.
    """
    try:
        recommender = UniversalVizRecommender()
        raw_charts = recommender.get_all_chart_types()
        
        formatted_charts = []
        for chart in raw_charts:
            formatted_charts.append({
                "chart_type": chart["chart_type"],
                "display_name": chart["title"],  # 🎯 FIX: Frontend JS mencari 'display_name', bukan 'title'
                "description": chart["description"],
                "icon": chart.get("icon", "📊")
            })
            
        logger.info(f"Returning ALL {len(formatted_charts)} chart types (no filtering)")
        return {"chart_types": formatted_charts}
        
    except Exception as e:
        logger.error(f"Error fetching chart types: {e}")
        return {"error": str(e), "chart_types": []}
# ==============================================================================


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 DENAI API Starting...")
    logger.info(f"✅ Environment: {ENVIRONMENT}")
    logger.info(f"✅ ElevenLabs TTS: {'CONFIGURED' if ELEVENLABS_API_KEY else 'NOT CONFIGURED'}")
    logger.info("🎯 Architecture: API → ChatService → Universal Analytics")
    logger.info("📋 Schema Explorer: ENABLED (/api/schema/)")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("👋 DENAI API Shutting down...")


# ✅ FIX: Mengembalikan endpoint alias untuk Frontend lama
@app.get("/history/{session_id}")
async def get_history_alias(session_id: str, limit: int = 50):
    """Alias endpoint for older frontend compatibility"""
    from backend.api.sessions import get_session_history
    return await get_session_history(session_id, limit)


# Root endpoint (untuk ngecek apakah server nyala)
@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "status": "active",
        "service": "DENAI - Modular AI Assistant API",
        "version": "8.1.0",
        "architecture": "universal_analytics",
        "flow": "API → ChatService → tools.py → engines/",
        "improvements": [
            "✅ Clean layered architecture",
            "✅ Proper separation of concerns",
            "✅ Universal Analytics JSON payload",
            "✅ Visualization logic moved to Frontend!",
            "✅ Schema Explorer for database documentation"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting DENAI API (Universal Analytics + Schema Explorer)...")
    print(f"✅ Environment: {ENVIRONMENT}")
    
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=ENVIRONMENT == "development",
    )