"""
DENAI Auth Dependencies
=======================
FastAPI dependency untuk validasi auth session dari SINTA.
Digunakan di semua endpoint yang butuh isolasi per-user.
"""
from typing import Optional
from fastapi import Header


async def get_auth_nik(x_auth_session: Optional[str] = Header(None)) -> Optional[str]:
    """
    Baca X-Auth-Session header dan kembalikan NIK user yang sedang login.

    Return None  → header tidak ada (mode dev / standalone, tidak ada filter)
    Return ""    → header ada tapi session tidak dikenali (user context expired/hilang)
    Return "xxx" → NIK valid
    """
    if not x_auth_session:
        return None  # dev mode: tidak ada header → tidak ada filter

    from backend.services.user_context import get_user_context
    ctx = get_user_context(x_auth_session)
    if not ctx:
        # Session ada tapi context sudah expired di server (Redis TTL habis)
        # Kembalikan "" bukan raise 401 agar tidak lock-out user yang server-nya restart
        return ""

    return ctx.get("nik") or ""
