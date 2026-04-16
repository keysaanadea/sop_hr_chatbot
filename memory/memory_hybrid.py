"""
Hybrid Memory Manager (Supabase + Upstash Redis)
=================================================
Mengatur caching di RAM (Redis) secara ASYNC dan penyimpanan permanen di Disk (Supabase).
"""
import logging
import json
from typing import List, Dict, Any

from app.config import UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN

import re

logger = logging.getLogger(__name__)
_SESSION_META_TTL = 86400 * 7
_local_session_meta: Dict[str, Dict[str, Any]] = {}


def _session_meta_key(session_id: str) -> str:
    return f"chat:meta:{session_id}"


def _build_session_title(initial_message: str) -> str:
    base = (initial_message or "Percakapan baru").strip()
    return (base[:50] + "...") if base else "Percakapan baru"


async def _get_session_meta(session_id: str) -> Dict[str, Any]:
    if REDIS_AVAILABLE:
        try:
            raw = await redis_client.get(_session_meta_key(session_id))
            if raw:
                return json.loads(raw) if isinstance(raw, str) else raw
        except Exception as e:
            logger.debug(f"⚠️ Session meta read failed for {session_id}: {e}")
    return dict(_local_session_meta.get(session_id, {}))


async def _set_session_meta(session_id: str, meta: Dict[str, Any]):
    safe_meta = dict(meta or {})
    if REDIS_AVAILABLE:
        try:
            await redis_client.set(_session_meta_key(session_id), json.dumps(safe_meta))
            await redis_client.expire(_session_meta_key(session_id), _SESSION_META_TTL)
        except Exception as e:
            logger.debug(f"⚠️ Session meta write failed for {session_id}: {e}")
    _local_session_meta[session_id] = safe_meta


async def _delete_session_meta(session_id: str):
    if REDIS_AVAILABLE:
        try:
            await redis_client.delete(_session_meta_key(session_id))
        except Exception as e:
            logger.debug(f"⚠️ Session meta delete failed for {session_id}: {e}")
    _local_session_meta.pop(session_id, None)

def _strip_html_payload(content: str) -> str:
    """Buang HANYA hidden payload span sebelum disimpan ke Redis.
    HTML formatting (h3, p, strong, dll) DIPERTAHANKAN agar tampilan history
    sama persis dengan saat pertama kali di-render."""
    if not content:
        return content
    # Hanya buang <span class="denai-hidden-payload"> yang berisi encoded JSON besar
    content = re.sub(r'<span[^>]*denai-hidden-payload[^>]*>.*?</span>', '', content, flags=re.DOTALL)
    return content.strip()

# ---------------------------------------------------------
# 1. INIT SUPABASE (Async Wrappers)
# ---------------------------------------------------------
try:
    from memory.memory_supabase import get_recent_history_async, save_message_async, save_session
    import asyncio
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("⚠️ Supabase Memory system not available")

# ---------------------------------------------------------
# 2. INIT UPSTASH REDIS (ASYNC VERSION)
# ---------------------------------------------------------
try:
    # Menggunakan modul asyncio bawaan dari Upstash!
    from upstash_redis.asyncio import Redis
    
    if UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN:
        redis_client = Redis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)
        REDIS_AVAILABLE = True
        logger.info("⚡ Async Upstash Redis Connected Successfully!")
    else:
        redis_client = None
        REDIS_AVAILABLE = False
except Exception as e:
    redis_client = None
    REDIS_AVAILABLE = False
    logger.warning(f"⚠️ Redis belum aktif. Error: {e}")

# ---------------------------------------------------------
# CORE HYBRID FUNCTIONS (FULLY ASYNC)
# ---------------------------------------------------------

async def setup_hybrid_session(session_id: str, initial_message: str, nik: str = "", has_history: bool = False):
    """Inisialisasi metadata session secara ringan.
    Session permanen di Supabase baru dibuat saat pesan pertama benar-benar disimpan.
    Dengan begitu, new chat yang dibatalkan tidak meninggalkan ghost session."""
    existing = await _get_session_meta(session_id)
    merged = {
        "title": existing.get("title") or _build_session_title(initial_message),
        "nik": existing.get("nik") or (nik or ""),
        "persisted": bool(existing.get("persisted")) or bool(has_history),
    }
    await _set_session_meta(session_id, merged)


async def _ensure_session_persisted(session_id: str):
    if not MEMORY_AVAILABLE:
        return

    meta = await _get_session_meta(session_id)
    if meta.get("persisted"):
        return

    title = meta.get("title") or "Percakapan baru"
    nik = meta.get("nik") or ""
    await asyncio.to_thread(save_session, session_id, title, nik)
    meta["persisted"] = True
    await _set_session_meta(session_id, meta)

    try:
        from backend.api.sessions import _invalidate_sessions_cache
        _invalidate_sessions_cache(nik or None)
    except Exception:
        pass

async def get_hybrid_history(session_id: str, limit: int = 4) -> List[Dict[str, Any]]:
    """Mengambil history dengan prioritas: 1. Redis (RAM), 2. Supabase (Disk)"""
    
    # Prioritas 1: Ambil dari Redis secara Async
    if REDIS_AVAILABLE:
        try:
            # 🐛 FIX BUG: Gunakan index negatif untuk menarik data terbaru dari ujung kanan list
            cached_data = await redis_client.lrange(f"chat:{session_id}", -limit, -1)
            if cached_data:
                logger.info("⚡ History ditarik INSTAN dari Redis!")
                return [json.loads(msg) if isinstance(msg, str) else msg for msg in cached_data]
        except Exception as e:
            logger.error(f"❌ Redis Read Error: {e}")

    # Prioritas 2: Kalau Redis kosong/gagal, ambil dari Supabase
    if MEMORY_AVAILABLE:
        history = await get_recent_history_async(session_id, limit=limit)
        if history:
            logger.info("💾 History ditarik dari Supabase lalu di-cache ke Redis")
        else:
            logger.info("🪹 History kosong di Redis dan Supabase")
        
        # Simpan kembali ke Redis biar pemanggilan berikutnya kencang
        if REDIS_AVAILABLE and history:
            try:
                await redis_client.delete(f"chat:{session_id}") 
                for msg in history:
                    msg_dict = msg if isinstance(msg, dict) else msg.__dict__
                    # Ekstrak waktu/data complex agar aman saat di json.dumps
                    safe_dict = {k: v for k, v in msg_dict.items() if k in ["role", "message", "sql_query", "sql_explanation", "last_query"]}
                    await redis_client.rpush(f"chat:{session_id}", json.dumps(safe_dict))
                await redis_client.expire(f"chat:{session_id}", 86400) # Expire 24 Jam
            except Exception:
                pass
        return history
    
    return []

async def save_hybrid_message(session_id: str, role: str, content: str, **kwargs):
    """Menyimpan pesan secara paralel ke Supabase dan Redis"""
    
    tasks = []

    if MEMORY_AVAILABLE:
        await _ensure_session_persisted(session_id)
    
    # Task 1: Simpan ke Supabase (Permanen)
    if MEMORY_AVAILABLE:
        tasks.append(save_message_async(session_id, role, content, **kwargs))
    
    # Task 2: Simpan ke Redis (Cache Sementara)
    if REDIS_AVAILABLE:
        async def save_to_redis():
            try:
                msg_obj = {"role": role, "message": _strip_html_payload(content)}
                # Simpan metadata SQL agar history dari Redis sama lengkapnya dengan dari Supabase
                for key in ["sql_query", "sql_explanation", "last_query"]:
                    if key in kwargs and kwargs[key]:
                        msg_obj[key] = kwargs[key]
                await redis_client.rpush(f"chat:{session_id}", json.dumps(msg_obj))
                await redis_client.ltrim(f"chat:{session_id}", -20, -1)  # cap list 20 pesan terakhir
                await redis_client.expire(f"chat:{session_id}", 86400)
            except Exception as e:
                logger.error(f"❌ Redis Save Error: {e}")
        
        tasks.append(save_to_redis())
    
    # Jalankan kedua task penyimpanan secara bersamaan tanpa saling menunggu lama
    if tasks:
        await asyncio.gather(*tasks)


async def delete_hybrid_session(session_id: str):
    """Hapus session dari Supabase DAN invalidate Redis cache-nya secara bersamaan."""
    tasks = []

    if MEMORY_AVAILABLE:
        from memory.memory_supabase import delete_session_and_messages
        tasks.append(asyncio.to_thread(delete_session_and_messages, session_id))

    if REDIS_AVAILABLE:
        async def _delete_redis():
            try:
                await redis_client.delete(f"chat:{session_id}")
            except Exception as e:
                logger.error(f"❌ Redis delete error for {session_id}: {e}")
        tasks.append(_delete_redis())

    if tasks:
        await asyncio.gather(*tasks)
    await _delete_session_meta(session_id)
