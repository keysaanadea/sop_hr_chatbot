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
def save_session(session_id: str, title: str, nik: str = ""):
    if not supabase: return
    try:
        supabase.table("chat_sessions").upsert({
            "session_id": session_id,
            "title": title,
            "nik": nik,
        }).execute()
    except Exception as e:
        logger.error(f"❌ Failed to save session: {e}")

def get_sessions(nik: str = None, limit: int = 30):
    """
    Kembalikan sesi milik user yang didentifikasi oleh NIK.
    nik=None → tampilkan semua (mode dev/standalone).
    nik=""   → hanya sesi tanpa NIK (fallback backwards-compat).
    nik="xxx"→ filter ketat per user.
    """
    if not supabase: return []
    try:
        # Ambil sessions dengan filter NIK dulu — sudah pakai server-side filter
        query = (
            supabase
            .table("chat_sessions")
            .select("session_id,title,pinned,created_at,last_message_at,nik")
            .order("pinned", desc=True)
            .order("last_message_at", desc=True)
            .order("created_at", desc=True)
            # Ambil window lebih lebar agar ghost sessions (sesi tanpa pesan) tidak
            # mendorong sesi valid keluar dari jendela filter. Ghost sessions terjadi
            # saat setup_hybrid_session() membuat row sebelum pesan pertama dikirim.
            .limit(limit * 10)
        )
        if nik is not None:
            if nik != "":
                # NIK valid: tampilkan HANYA sesi milik user ini
                query = query.eq("nik", nik)
            else:
                # Context expired (nik=""): hanya sesi tanpa NIK
                query = query.or_("nik.is.null,nik.eq.")

        res = query.execute()
        sessions = res.data or []
        if not sessions:
            return []

        # Filter anti-ghost: buang sesi yang tidak punya pesan sama sekali.
        # Query distinct session_id dari chat_memory agar tidak terbatas 500 row.
        session_ids = [s["session_id"] for s in sessions]
        # Supabase tidak support IN filter langsung untuk list besar, pakai satu query per batch
        # Batasi ke session_ids yang ada di hasil sesi (sudah server-filtered) bukan seluruh tabel
        msgs_res = (
            supabase
            .table("chat_memory")
            .select("session_id")
            .in_("session_id", session_ids)
            .execute()
        )
        ids_with_msgs = {m["session_id"] for m in (msgs_res.data or [])}

        filtered = [s for s in sessions if s["session_id"] in ids_with_msgs]
        return filtered[:limit]
    except Exception as e:
        logger.error(f"❌ Failed to get sessions: {e}")
        return []

def get_session_owner(session_id: str) -> str:
    """Ambil NIK pemilik session. Return '' jika tidak ada / sesi lama."""
    if not supabase: return ""
    try:
        res = supabase.table("chat_sessions").select("nik").eq("session_id", session_id).execute()
        if res.data:
            return res.data[0].get("nik") or ""
    except Exception:
        pass
    return ""

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