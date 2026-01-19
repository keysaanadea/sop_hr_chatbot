from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
from datetime import datetime, timedelta  # ✅ ADDED
import os

from app.config import SESSION_CLEANUP_DAYS  # ✅ ADDED

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# CHAT MEMORY (MESSAGE)
# =====================
def save_message(session_id: str, role: str, message: str):
    supabase.table("chat_memory").insert({
        "session_id": session_id,
        "role": role,
        "message": message
    }).execute()


def get_recent_history(session_id: str, limit: int = 6):
    res = (
        supabase
        .table("chat_memory")
        .select("role,message")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(res.data))


# =====================
# CHAT SESSIONS (SIDEBAR)
# =====================
def save_session(session_id: str, title: str):
    supabase.table("chat_sessions").upsert({
        "session_id": session_id,
        "title": title
    }).execute()


def get_sessions(limit: int = 30):
    """Get sessions - pinned first, then by date"""
    res = (
        supabase
        .table("chat_sessions")
        .select("session_id,title,pinned,created_at")
        .order("pinned", desc=True)  # 🔥 Pinned sessions first!
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


def pin_session(session_id: str, pinned: bool):
    supabase.table("chat_sessions").update({
        "pinned": pinned
    }).eq("session_id", session_id).execute()


def delete_session(session_id: str):
    supabase.table("chat_memory") \
        .delete() \
        .eq("session_id", session_id) \
        .execute()

    supabase.table("chat_sessions") \
        .delete() \
        .eq("session_id", session_id) \
        .execute()


# =====================
# 🔥 NEW: SESSION MANAGEMENT (Pin & Delete)
# =====================
def toggle_pin_session(session_id: str) -> bool:
    """Toggle pin status for a session"""
    try:
        # Get current status
        response = supabase.table("chat_sessions")\
            .select("pinned")\
            .eq("session_id", session_id)\
            .execute()
        
        if response.data:
            current_pinned = response.data[0].get("pinned", False)
            new_pinned = not current_pinned
            
            # Update pin status
            supabase.table("chat_sessions")\
                .update({"pinned": new_pinned})\
                .eq("session_id", session_id)\
                .execute()
            
            print(f"✅ Session {session_id[:8]}... pinned={new_pinned}")
            return new_pinned
        
        return False
    except Exception as e:
        print(f"❌ Error toggling pin: {e}")
        return False


def delete_session_and_messages(session_id: str):
    """Delete session and all its messages (used by API endpoint)"""
    try:
        # Delete messages first
        supabase.table("chat_memory")\
            .delete()\
            .eq("session_id", session_id)\
            .execute()
        
        # Delete session
        supabase.table("chat_sessions")\
            .delete()\
            .eq("session_id", session_id)\
            .execute()
        
        print(f"✅ Session {session_id[:8]}... deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting session: {e}")
        raise


# =====================
# CLEANUP OLD SESSIONS
# =====================
def cleanup_old_sessions(days: int = None):
    """Delete sessions older than N days"""
    
    if days is None:
        days = SESSION_CLEANUP_DAYS
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Delete old sessions
        result_sessions = supabase.table("chat_sessions")\
            .delete()\
            .lt("created_at", cutoff_date.isoformat())\
            .execute()
        
        # Delete old messages
        result_memory = supabase.table("chat_memory")\
            .delete()\
            .lt("created_at", cutoff_date.isoformat())\
            .execute()
        
        print(f"✅ Cleaned up sessions older than {days} days")
        
    except Exception as e:
        print(f"❌ Error cleaning up sessions: {e}")