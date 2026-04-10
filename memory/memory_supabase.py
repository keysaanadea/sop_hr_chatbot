"""
DENAI Memory Management (Supabase)
Handles chat history, sessions, and memory persistence safely.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client

from app.config import (
    SUPABASE_URL, 
    SUPABASE_ANON_KEY, 
    SESSION_CLEANUP_DAYS
)

logger = logging.getLogger(__name__)

if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    supabase = None
    logger.error("❌ SUPABASE_URL or SUPABASE_ANON_KEY is missing! Memory system will fail gracefully.")

# =====================
# CHAT MEMORY (MESSAGE)
# =====================
def save_message(session_id: str, role: str, message: str, **kwargs):
    if not supabase: return
    try:
        data = {
            "session_id": session_id,
            "role": role,
            "message": message
        }

        # Ekstrak field tambahan secara dinamis jika ada (misal dari visualisasi HR)
        for key in ["sql_query", "sql_explanation", "last_query"]:
            if key in kwargs and kwargs[key]:
                data[key] = kwargs[key]

        supabase.table("chat_memory").insert(data).execute()

        # Update last_message_at pada session agar sidebar sorting akurat
        # Gunakan UTC timezone-aware agar konsisten dengan Supabase timestamptz
        from datetime import timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        supabase.table("chat_sessions").update({"last_message_at": now_iso}).eq("session_id", session_id).execute()
    except Exception as e:
        logger.error(f"❌ Failed to save message: {e}")

def get_recent_history(session_id: str, limit: int = 6):
    if not supabase: return []
    try:
        # Menarik kolom tambahan agar RAG engine & UI Frontend bisa memulihkan dashboard
        res = (
            supabase
            .table("chat_memory")
            .select("role, message, sql_query, sql_explanation, last_query, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        # Supabase mengembalikan data dari terbaru ke terlama, kita balik agar kronologis
        return list(reversed(res.data))
    except Exception as e:
        logger.error(f"❌ Failed to get history: {e}")
        return []

# =====================
# CHAT SESSIONS & CLEANUP
# =====================
def save_session(session_id: str, title: str):
    if not supabase: return
    try:
        supabase.table("chat_sessions").upsert({
            "session_id": session_id,
            "title": title
        }).execute()
    except Exception as e:
        logger.error(f"❌ Failed to save session: {e}")

def get_sessions(limit: int = 30):
    if not supabase: return []
    try:
        # Ambil session_ids yang benar-benar punya pesan (anti-ghost)
        msgs_res = (
            supabase
            .table("chat_memory")
            .select("session_id")
            .limit(500)
            .execute()
        )
        ids_with_msgs = {m["session_id"] for m in (msgs_res.data or [])}
        if not ids_with_msgs:
            return []

        # Ambil sessions dan filter ghost di sini
        res = (
            supabase
            .table("chat_sessions")
            .select("session_id,title,pinned,created_at,last_message_at")
            .order("pinned", desc=True)
            .order("last_message_at", desc=True)
            .order("created_at", desc=True)
            .limit(limit * 3)
            .execute()
        )
        sessions = res.data or []
        filtered = [s for s in sessions if s["session_id"] in ids_with_msgs]
        return filtered[:limit]
    except Exception as e:
        logger.error(f"❌ Failed to get sessions: {e}")
        return []

def toggle_pin_session(session_id: str) -> bool:
    if not supabase: return False
    try:
        response = supabase.table("chat_sessions").select("pinned").eq("session_id", session_id).execute()
        if response.data:
            new_pinned = not response.data[0].get("pinned", False)
            supabase.table("chat_sessions").update({"pinned": new_pinned}).eq("session_id", session_id).execute()
            return new_pinned
        return False
    except Exception as e:
        logger.error(f"❌ Error toggling pin: {e}")
        return False

def delete_session_and_messages(session_id: str):
    if not supabase: return
    try:
        supabase.table("chat_memory").delete().eq("session_id", session_id).execute()
        supabase.table("chat_sessions").delete().eq("session_id", session_id).execute()
    except Exception as e:
        logger.error(f"❌ Error deleting session: {e}")
        raise

def cleanup_old_sessions(days: int = None):
    if not supabase: return
    days = days if days is not None else SESSION_CLEANUP_DAYS
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        iso_cutoff = cutoff_date.isoformat()
        supabase.table("chat_sessions").delete().lt("created_at", iso_cutoff).execute()
        supabase.table("chat_memory").delete().lt("created_at", iso_cutoff).execute()
    except Exception as e:
        logger.error(f"❌ Error cleaning up sessions: {e}")

# =========================================================
# 🚀 ASYNC WRAPPERS
# =========================================================
async def save_message_async(session_id: str, role: str, message: str, **kwargs):
    await asyncio.to_thread(save_message, session_id, role, message, **kwargs)

async def get_recent_history_async(session_id: str, limit: int = 6):
    return await asyncio.to_thread(get_recent_history, session_id, limit)