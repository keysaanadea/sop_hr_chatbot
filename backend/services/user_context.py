"""
User Context Store - SINTA Integration
=======================================
Menyimpan data user dari SINTA per session_id.
Layer 1: In-memory (cepat)
Layer 2: Redis (persistent, survive server restart)
"""

import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# In-memory cache (layer 1)
_user_context_store: Dict[str, Dict[str, Any]] = {}

# Redis client (layer 2) — diinit lazy
_redis = None
REDIS_TTL = 86400 * 7  # 7 hari

HC_UNIT_KEYWORDS = ["human capital", "hc ", " hc", "hcis", "people", "hr ", " hr"]


def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    try:
        from app.config import UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN
        if UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN:
            from upstash_redis import Redis
            _redis = Redis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)
            logger.info("✅ Redis connected for user context store")
        else:
            _redis = False  # tidak tersedia
    except Exception as e:
        logger.warning(f"⚠️ Redis not available for user context: {e}")
        _redis = False
    return _redis


def determine_role_from_unit(unit_kerja: str) -> str:
    unit_lower = unit_kerja.lower()
    for keyword in HC_UNIT_KEYWORDS:
        if keyword in unit_lower:
            return "hc"
    return "karyawan"


def set_user_context(session_id: str, context: Dict[str, Any]) -> None:
    """Simpan ke memory + Redis."""
    _user_context_store[session_id] = context

    redis = _get_redis()
    if redis:
        try:
            redis.set(f"denai:user_ctx:{session_id}", json.dumps(context), ex=REDIS_TTL)
        except Exception as e:
            logger.warning(f"⚠️ Failed to save user context to Redis: {e}")

    logger.info(
        f"✅ User context saved | session={session_id[:8]}... | "
        f"nama={context.get('nama')} | band={context.get('band_angka')} | role={context.get('role')}"
    )


def get_user_context(session_id: str) -> Optional[Dict[str, Any]]:
    """Cek memory dulu, kalau tidak ada coba Redis."""
    # Layer 1: memory
    if session_id in _user_context_store:
        return _user_context_store[session_id]

    # Layer 2: Redis (misalnya setelah server restart)
    redis = _get_redis()
    if redis:
        try:
            raw = redis.get(f"denai:user_ctx:{session_id}")
            if raw:
                context = json.loads(raw)
                _user_context_store[session_id] = context  # cache balik ke memory
                logger.info(f"♻️ User context restored from Redis | session={session_id[:8]}...")
                return context
        except Exception as e:
            logger.warning(f"⚠️ Failed to get user context from Redis: {e}")

    return None


def clear_user_context(session_id: str) -> None:
    _user_context_store.pop(session_id, None)
    redis = _get_redis()
    if redis:
        try:
            redis.delete(f"denai:user_ctx:{session_id}")
        except Exception:
            pass
