"""
Currency Utility — Real-time USD/IDR exchange rate
Uses frankfurter.app (free, no API key required).
Rate is cached for CACHE_TTL_HOURS hours to avoid hammering the API.
"""

import asyncio
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 6
_FALLBACK_RATE = 16_200.0  # fallback jika API gagal

_cache: dict = {
    "rate": None,
    "fetched_at": 0.0,
}
_lock = asyncio.Lock()


async def get_usd_idr_rate() -> float:
    """
    Return current USD → IDR rate.
    Cached for CACHE_TTL_HOURS hours. Falls back to _FALLBACK_RATE on error.
    """
    async with _lock:
        age = time.time() - _cache["fetched_at"]
        if _cache["rate"] and age < CACHE_TTL_HOURS * 3600:
            logger.debug(f"💱 USD/IDR rate from cache: {_cache['rate']}")
            return _cache["rate"]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    "https://api.frankfurter.app/latest",
                    params={"from": "USD", "to": "IDR"},
                )
                res.raise_for_status()
                data = res.json()
                rate = float(data["rates"]["IDR"])
                _cache["rate"] = rate
                _cache["fetched_at"] = time.time()
                logger.info(f"💱 USD/IDR rate fetched: {rate:,.0f} (date: {data.get('date')})")
                return rate
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch USD/IDR rate: {e} — using fallback {_FALLBACK_RATE:,.0f}")
            return _fallback_with_cache()


def _fallback_with_cache() -> float:
    """Use cached rate if still somewhat fresh (< 24h), else use hardcoded fallback."""
    age = time.time() - _cache["fetched_at"]
    if _cache["rate"] and age < 24 * 3600:
        return _cache["rate"]
    return _FALLBACK_RATE


def usd_to_idr(usd: float, rate: float) -> str:
    """Format USD amount to IDR string, e.g. 'Rp 3.645.000'"""
    idr = round(usd * rate / 1000) * 1000  # round to nearest 1000
    return f"Rp {idr:,.0f}".replace(",", ".")
