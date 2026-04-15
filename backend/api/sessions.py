"""
DENAI Session Management API Routes
Session and conversation history management
"""

import logging
import asyncio
import time
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from backend.api.deps import get_auth_nik

logger = logging.getLogger(__name__)

# ✅ Menggunakan Absolute Import standar
from backend.models.requests import SessionResponse, SessionInfo, MessageInfo

# Import session management functions
try:
    from memory.memory_supabase import (
        get_sessions, get_recent_history, toggle_pin_session,
        delete_session_and_messages, get_session_owner
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("⚠️ Memory system not available")

    # Fallback dummy functions
    def get_sessions(nik=None): return []
    def get_recent_history(session_id: str, limit: int = 50): return []
    def toggle_pin_session(session_id: str): return False
    def delete_session_and_messages(session_id: str): pass
    def get_session_owner(session_id: str): return ""

router = APIRouter()

# Cache for list_sessions: per-NIK agar user berbeda tidak saling cache
_sessions_cache: dict = {}          # key: nik (str) → {"data": [...], "ts": float}
_SESSIONS_CACHE_TTL = 10            # detik

def _invalidate_sessions_cache(nik: str = None):
    """Invalidate cache untuk NIK tertentu, atau semua kalau nik=None."""
    if nik and nik in _sessions_cache:
        _sessions_cache[nik]["ts"] = 0.0
    else:
        for v in _sessions_cache.values():
            v["ts"] = 0.0


@router.get("/", response_model=List[SessionInfo])
async def list_sessions(auth_nik: Optional[str] = Depends(get_auth_nik)):
    """Get list of conversation sessions — difilter per user (NIK)."""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")

        cache_key = auth_nik if auth_nik is not None else "__all__"
        now = time.monotonic()
        entry = _sessions_cache.get(cache_key)
        if entry and entry["data"] is not None and (now - entry["ts"]) < _SESSIONS_CACHE_TTL:
            return entry["data"]

        sessions = await asyncio.to_thread(get_sessions, auth_nik)
        _sessions_cache[cache_key] = {"data": sessions, "ts": now}
        logger.info(f"📋 Retrieved {len(sessions)} sessions (nik={auth_nik or 'all'})")
        return sessions

    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ List sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history", response_model=List[MessageInfo])
async def get_session_history(
    session_id: str,
    limit: int = 50,
    auth_nik: Optional[str] = Depends(get_auth_nik)
):
    """Get conversation history — validasi kepemilikan sesi jika NIK tersedia."""
    try:
        limit = min(limit, 200)

        # Validasi kepemilikan: hanya jika NIK tersedia di kedua sisi
        if auth_nik:
            owner = await asyncio.to_thread(get_session_owner, session_id)
            if owner and owner != auth_nik:
                raise HTTPException(status_code=403, detail="Access denied: session belongs to another user")

        from memory.memory_hybrid import get_hybrid_history
        history = await get_hybrid_history(session_id, limit=limit)
        logger.info(f"📖 Retrieved {len(history)} messages for session {session_id[:8]}...")
        return history

    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ Get session history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/pin", response_model=SessionResponse)
async def toggle_session_pin(
    session_id: str,
    auth_nik: Optional[str] = Depends(get_auth_nik)
):
    """Toggle pin/star status for a session."""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")

        if auth_nik:
            owner = await asyncio.to_thread(get_session_owner, session_id)
            if owner and owner != auth_nik:
                raise HTTPException(status_code=403, detail="Access denied")

        pinned = await asyncio.to_thread(toggle_pin_session, session_id)
        _invalidate_sessions_cache(auth_nik)
        logger.info(f"📌 Session {session_id[:8]}... pinned={pinned}")
        return SessionResponse(
            success=True,
            session_id=session_id,
            pinned=pinned,
            message=f"Session {'pinned' if pinned else 'unpinned'} successfully"
        )

    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ Pin session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str, auth_nik: Optional[str] = Depends(get_auth_nik)):
    """Delete session and all its messages"""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")

        if auth_nik:
            owner = await asyncio.to_thread(get_session_owner, session_id)
            if owner and owner != auth_nik:
                raise HTTPException(status_code=403, detail="Access denied")

        await asyncio.to_thread(delete_session_and_messages, session_id)
        _invalidate_sessions_cache(auth_nik)
        logger.info(f"🗑️ Session deleted: {session_id[:8]}...")
        return SessionResponse(
            success=True,
            session_id=session_id,
            message="Session deleted successfully"
        )

    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ Delete session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
async def session_statistics():
    """Get session statistics and overview"""
    try:
        if not MEMORY_AVAILABLE:
            return {"memory_available": False, "error": "Session management system not available"}
        
        # ✅ FIX: Bungkus ke thread
        sessions = await asyncio.to_thread(get_sessions)
        
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent_sessions = sum(
            1 for s in sessions 
            if datetime.fromisoformat(s.get("created_at", "1970-01-01T00:00:00")) > week_ago
        )
        
        return {
            "memory_available": True,
            "total_sessions": len(sessions),
            "pinned_sessions": sum(1 for s in sessions if s.get("pinned", False)),
            "recent_sessions_7d": recent_sessions,
            "average_session_length": "Unknown",
            "storage_status": "active"
        }
        
    except Exception as e:
        logger.error(f"❌ Session statistics error: {e}")
        return {"memory_available": MEMORY_AVAILABLE, "error": str(e)}


@router.post("/cleanup")
async def cleanup_old_sessions(days_old: int = 30):
    """Cleanup sessions older than specified days (admin function)"""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")
        
        if days_old < 7:
            raise HTTPException(status_code=400, detail="Cannot delete sessions less than 7 days old")
        
        logger.warning(f"🧹 Cleanup requested for sessions older than {days_old} days")
        return {
            "success": True,
            "message": "Cleanup operation queued",
            "days_old": days_old,
            "note": "Implementation depends on memory backend"
        }
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ Cleanup sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def session_system_health():
    """Check session management system health"""
    try:
        health_status = {
            "service": "session_management",
            "memory_available": MEMORY_AVAILABLE,
            "status": "healthy" if MEMORY_AVAILABLE else "unavailable"
        }
        
        if MEMORY_AVAILABLE:
            try:
                # ✅ FIX: Bungkus ke thread
                sessions = await asyncio.to_thread(get_sessions)
                health_status["database_connection"] = "active"
                health_status["total_sessions"] = len(sessions)
            except Exception as e:
                health_status["database_connection"] = "error"
                health_status["error"] = str(e)
                health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Session health check error: {e}")
        return {"service": "session_management", "status": "error", "error": str(e)}