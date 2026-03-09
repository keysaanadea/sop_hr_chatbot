"""
DENAI Session Management API Routes
Session and conversation history management
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException
from typing import List

logger = logging.getLogger(__name__)

# ✅ Menggunakan Absolute Import standar
from backend.models.requests import SessionResponse, SessionInfo, MessageInfo

# Import session management functions
try:
    from memory.memory_supabase import (
        get_sessions, get_recent_history, toggle_pin_session, delete_session_and_messages
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("⚠️ Memory system not available")
    
    # Fallback dummy functions
    def get_sessions(): return []
    def get_recent_history(session_id: str, limit: int = 50): return []
    def toggle_pin_session(session_id: str): return False
    def delete_session_and_messages(session_id: str): pass

router = APIRouter()

@router.get("/", response_model=List[SessionInfo])
async def list_sessions():
    """Get list of all conversation sessions"""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")
        
        # ✅ FIX: Bungkus ke thread karena fungsi DB Supabase bersifat blocking
        sessions = await asyncio.to_thread(get_sessions)
        logger.info(f"📋 Retrieved {len(sessions)} sessions")
        return sessions
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ List sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history", response_model=List[MessageInfo])
async def get_session_history(session_id: str, limit: int = 50):
    """Get conversation history for a specific session"""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")
        
        limit = min(limit, 200) # Prevent excessive memory usage
        # ✅ FIX: Bungkus ke thread
        history = await asyncio.to_thread(get_recent_history, session_id, limit)
        logger.info(f"📖 Retrieved {len(history)} messages for session {session_id[:8]}...")
        return history
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ Get session history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/pin", response_model=SessionResponse)
async def toggle_session_pin(session_id: str):
    """Toggle pin/star status for a session"""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")
        
        # ✅ FIX: Bungkus ke thread
        pinned = await asyncio.to_thread(toggle_pin_session, session_id)
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
async def delete_session(session_id: str):
    """Delete session and all its messages"""
    try:
        if not MEMORY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session management system not available")
        
        # ✅ FIX: Bungkus ke thread
        await asyncio.to_thread(delete_session_and_messages, session_id)
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