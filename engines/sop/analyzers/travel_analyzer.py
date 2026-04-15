"""
TRAVEL ANALYZER v2 (DUAL MODE - ASYNC SAFE)
======================================================
Otomatis mendeteksi scope tanpa memblokir server.
"""

import os
import re
import logging
import asyncio
from typing import Dict

logger = logging.getLogger(__name__)

# =====================
# GOOGLE MAPS SETUP
# =====================
try:
    import googlemaps
    GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    if GOOGLE_API_KEY:
        gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
        GOOGLE_API_AVAILABLE = True
    else:
        GOOGLE_API_AVAILABLE = False
except ImportError:
    GOOGLE_API_AVAILABLE = False
    gmaps = None

_distance_cache = {}
_flight_cache = {}

class TravelAnalyzer:
    def __init__(self, llm_client=None):
        self.domain = "travel"
        self.llm_client = llm_client
        logger.info("✅ TravelAnalyzer (Clean Async Edition) initialized")
    
    # ✅ FIX: Berubah menjadi ASYNC agar tidak memblokir server
    async def process_decision_query_async(self, origin: str, destination: str, scope: str = 'general') -> Dict:
        """Main Processor: Cek Scope -> Kembalikan Durasi/Jarak"""
        if not destination or destination.lower() in ["", "none", "null", "-", "tidak ada"]:
            return {'processed': False, 'reason': 'no_destination'}
            
        if not origin or origin.lower() in ["", "none", "null", "-", "tidak ada"]:
            origin = "Jakarta"
            
        origin = origin.strip().title()
        destination = destination.strip().title()
        
        logger.info(f"🛣️ Rute terdeteksi: {origin} → {destination} (Scope: {scope})")
        
        if scope == 'international':
            travel_data = await self._estimate_flight_duration_async(origin, destination)
        else:
            travel_data = await self._calculate_distance_async(origin, destination)
            
        return {
            'processed': True,
            'route': f"{origin} → {destination}",
            'distance_km': travel_data['distance_km'],
            'duration_hours': travel_data['duration_hours'],
            'data_source': travel_data['source'],
            'scope_used': scope
        }

    async def _estimate_flight_duration_async(self, origin: str, destination: str) -> Dict:
        cache_key = f"{origin.lower()}-{destination.lower()}"
        if cache_key in _flight_cache: return _flight_cache[cache_key]
        if not self.llm_client: return {'distance_km': 0, 'duration_hours': 0, 'source': 'unavailable'}
            
        prompt = f"Berapa estimasi rata-rata durasi penerbangan (dalam jam) dari {origin} ke {destination}? Jawab HANYA dengan angka desimal, tanpa teks lain. Contoh jika 2 jam setengah tulis: 2.5"
        
        try:
            # ✅ FIX: Menggunakan ainvoke (Async Invoke)
            response = await self.llm_client.ainvoke(prompt)
            cleaned = re.sub(r'[^\d.]', '', response.content.strip())
            hours = float(cleaned) if cleaned else 0.0
            # Guard: if parsed as 0 or implausibly large, use 3-hour fallback
            if hours <= 0 or hours > 24:
                logger.warning(f"⚠️ Flight duration parse suspicious ({hours}h) for {origin}→{destination}, using fallback 3.0h")
                hours = 3.0
            logger.info(f"✈️ Flight duration estimated: {origin}→{destination} = {hours} hrs")
            data = {'distance_km': 0, 'duration_hours': hours, 'source': 'llm_flight_estimate'}
            _flight_cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"❌ Gagal menebak durasi penerbangan: {e}")
            return {'distance_km': 0, 'duration_hours': 3.0, 'source': 'error_fallback'}

    async def _calculate_distance_async(self, origin: str, destination: str) -> Dict:
        cache_key = f"{origin.lower()}-{destination.lower()}"
        if cache_key in _distance_cache: return _distance_cache[cache_key]
            
        if GOOGLE_API_AVAILABLE:
            try:
                # ✅ FIX: Melempar tugas sinkron ke thread lain agar event loop tidak macet
                result = await asyncio.to_thread(
                    gmaps.distance_matrix, origins=[origin], destinations=[destination], mode="driving"
                )
                element = result['rows'][0]['elements'][0]
                
                if element['status'] == 'OK':
                    data = {
                        'distance_km': round(element['distance']['value'] / 1000, 1),
                        'duration_hours': round(element['duration']['value'] / 3600, 2),
                        'source': 'google_api'
                    }
                    _distance_cache[cache_key] = data
                    return data
            except Exception as e:
                logger.error(f"❌ Google API error: {e}")
                
        return await self._estimate_with_llm_async(origin, destination)

    async def _estimate_with_llm_async(self, origin: str, destination: str) -> Dict:
        """
        Smart Fallback: Jika Google Maps gagal (karena beda pulau),
        AI akan menebak kombinasi jarak penerbangan udara + darat.
        """
        if not self.llm_client: return {'distance_km': 0, 'duration_hours': 0, 'source': 'unavailable'}
        
        # PROMPT PINTAR: Memaksa AI memberikan 2 angka sekaligus (Jarak & Durasi)
        prompt = f"""Hitung estimasi total jarak (KM) dan total durasi (Jam) dari {origin} ke {destination}.
Instruksi:
1. Jika berbeda pulau, asumsikan menggunakan kombinasi Penerbangan Udara (Pesawat) + Perjalanan Darat.
2. JAWAB HANYA DENGAN FORMAT: [JARAK_KM]|[DURASI_JAM]
3. Tidak boleh ada huruf, spasi, atau teks lain! Contoh format yang benar: 2500.5|4.5"""
        
        try:
            # Panggil LLM (Async)
            response = await self.llm_client.ainvoke(prompt)
            content = response.content.strip()
            
            # Parsing hasil "2500.5|4.5"
            parts = content.split('|')
            if len(parts) >= 2:
                km = float(re.sub(r'[^\d.]', '', parts[0]))
                hours = float(re.sub(r'[^\d.]', '', parts[1]))
            else:
                # Fallback jika AI menjawab di luar format (mengambil 2 angka pertama yang ketemu)
                numbers = re.findall(r"[\d.]+", content)
                km = float(numbers[0]) if len(numbers) > 0 else 1000
                hours = float(numbers[1]) if len(numbers) > 1 else 3
                
            return {
                'distance_km': km, 
                'duration_hours': hours, 
                'source': 'llm_flight_and_land_estimate'
            }
            
        except Exception as e:
            logger.error(f"❌ Smart LLM Estimate failed: {e}")
            # Fallback pamungkas jika AI OpenAI sedang error
            return {'distance_km': 1500, 'duration_hours': 3.5, 'source': 'fallback_error'}