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

def _strip_html_payload(content: str) -> str:
    """Buang hidden payload span dan HTML tags sebelum disimpan ke Redis cache.
    Tujuan: mengecilkan ukuran entry Redis agar tidak bengkak dengan full HTML response."""
    if not content:
        return content
    # Buang <span class="denai-hidden-payload" ...> yang berisi encoded JSON besar
    content = re.sub(r'<span[^>]*denai-hidden-payload[^>]*>.*?</span>', '', content, flags=re.DOTALL)
    # Buang semua HTML tags lainnya, sisakan teks bersih
    content = re.sub(r'<[^>]+>', '', content)
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

async def setup_hybrid_session(session_id: str, initial_message: str):
    """Membantu inisialisasi session pertama kali di Supabase.
    Cek Redis dulu — kalau sudah ada history, session pasti sudah terbuat, skip Supabase."""
    # Kalau Redis sudah ada history untuk session ini, session sudah terbuat — skip Supabase
    if REDIS_AVAILABLE:
        try:
            exists = await redis_client.exists(f"chat:{session_id}")
            if exists:
                return
        except Exception:
            pass

    if MEMORY_AVAILABLE:
        history = await get_recent_history_async(session_id, limit=1)
        if not history:
            # save_session masih sync, kita lempar ke thread agar aman
            await asyncio.to_thread(save_session, session_id, initial_message[:50] + "...")

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
        logger.info("💾 History ditarik dari Supabase (Lalu di-cache ke Redis)")
        history = await get_recent_history_async(session_id, limit=limit)
        
        # Simpan kembali ke Redis biar pemanggilan berikutnya kencang
        if REDIS_AVAILABLE and history:
            try:
                await redis_client.delete(f"chat:{session_id}") 
                for msg in history:
                    msg_dict = msg if isinstance(msg, dict) else msg.__dict__
                    # Ekstrak waktu/data complex agar aman saat di json.dumps
                    safe_dict = {k: v for k, v in msg_dict.items() if k in ["role", "message"]}
                    await redis_client.rpush(f"chat:{session_id}", json.dumps(safe_dict))
                await redis_client.expire(f"chat:{session_id}", 86400) # Expire 24 Jam
            except Exception:
                pass
        return history
    
    return []

async def save_hybrid_message(session_id: str, role: str, content: str, **kwargs):
    """Menyimpan pesan secara paralel ke Supabase dan Redis"""
    
    tasks = []
    
    # Task 1: Simpan ke Supabase (Permanen)
    if MEMORY_AVAILABLE:
        tasks.append(save_message_async(session_id, role, content, **kwargs))
    
    # Task 2: Simpan ke Redis (Cache Sementara)
    if REDIS_AVAILABLE:
        async def save_to_redis():
            try:
                msg_obj = {"role": role, "message": _strip_html_payload(content)}
                await redis_client.rpush(f"chat:{session_id}", json.dumps(msg_obj))
                await redis_client.ltrim(f"chat:{session_id}", -20, -1)  # cap list 20 pesan terakhir
                await redis_client.expire(f"chat:{session_id}", 86400)
            except Exception as e:
                logger.error(f"❌ Redis Save Error: {e}")
        
        tasks.append(save_to_redis())
    
    # Jalankan kedua task penyimpanan secara bersamaan tanpa saling menunggu lama
    if tasks:
        await asyncio.gather(*tasks)