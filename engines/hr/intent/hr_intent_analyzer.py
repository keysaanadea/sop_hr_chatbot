"""
Hybrid HR Intent Analyzer (Regex + LLM Fallback)
================================================
Mendeteksi intent dengan 2 layer:
1. Fast Track (Regex): Super cepat & Gratis
2. Fallback (LLM): Paham Konteks & Kebal Typo
"""

import re
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class HRIntentAnalyzer:
    """
    Smart Hybrid Analyzer untuk merutekan pertanyaan HR Analytics vs SOP.
    """
    
    def __init__(self, llm_client=None):
        """
        Inisialisasi Analyzer.
        Args:
            llm_client: LangChain ChatOpenAI instance (opsional, untuk fallback)
        """
        self.llm_client = llm_client
        
        # === LAYER 1: KEYWORDS & REGEX (PRE-COMPILED) ===
        self.hr_data_keywords = [
            'karyawan', 'employee', 'pegawai', 'staff', 'gaji', 'salary', 'payroll', 
            'department', 'departemen', 'divisi', 'jumlah', 'count', 'total',
            'rekrutmen', 'recruitment', 'hiring', 'turnover', 'resign', 'attrition', 
            'absensi', 'attendance', 'kehadiran', 'database'
        ]
        
        self.viz_keywords = [
            'grafik', 'chart', 'graph', 'plot', 'visualisasi', 'visual',
            'diagram', 'bar', 'pie', 'line', 'scatter', 'histogram',
            'dashboard', 'trend', 'tren', 'bandingkan'
        ]
        
        self.data_only_keywords = [
            'data saja', 'tanpa grafik', 'raw data', 'tabel saja',
            'list', 'daftar', 'export data', 'unduh data'
        ]
        
        self.hr_patterns = [re.compile(p) for p in [
            r'berapa\s+.*?(karyawan|employee|pegawai|orang)',
            r'siapa\s+.*?(manager|karyawan|staff|direktur)',
            r'distribusi\s+.*?(gaji|salary|department)',
            r'rata-rata\s+.*?(gaji|performa|score)'
        ]]
        
        logger.info("✅ Hybrid HRIntentAnalyzer initialized")
        
    async def analyze_async(self, question: str) -> Dict[str, bool]:
        """
        Main routing function. Eksekusi Regex dulu, kalau gagal baru panggil LLM.
        """
        question_lower = question.lower()
        
        # --- LAYER 1: FAST TRACK (REGEX) ---
        is_hr = self._regex_is_hr(question_lower)
        wants_viz = self._regex_wants_viz(question_lower)
        
        # Jika Regex sudah sangat yakin (True), langsung kembalikan hasilnya! Menghemat API!
        if is_hr:
            logger.info("⚡ Fast Track Intent: HR Data Query (Detected via Regex)")
            return {"is_hr_data_query": True, "wants_visualization": wants_viz}
            
        # --- LAYER 2: LLM FALLBACK ---
        # Jika Regex gagal mendeteksi HR (False), tapi kita punya LLM, tanyakan ke LLM!
        if self.llm_client:
            logger.info("🧠 Fallback Intent: Regex ragu, meminta deteksi semantik dari LLM...")
            return await self._llm_detect_intent(question, wants_viz)
            
        # Jika tidak ada LLM yang di-*passing*, kembalikan hasil mentah Regex (False)
        return {"is_hr_data_query": False, "wants_visualization": wants_viz}

    def _regex_is_hr(self, question_lower: str) -> bool:
        if any(kw in question_lower for kw in self.hr_data_keywords): return True
        if any(p.search(question_lower) for p in self.hr_patterns): return True
        return False
        
    def _regex_wants_viz(self, question_lower: str) -> bool:
        if any(kw in question_lower for kw in self.data_only_keywords): return False
        if any(kw in question_lower for kw in self.viz_keywords): return True
        return False

    async def _llm_detect_intent(self, question: str, fallback_viz: bool) -> Dict[str, bool]:
        """Layer cerdas menggunakan LLM untuk membaca niat tersembunyi/typo"""
        prompt = f"""Analyze the user question and output a JSON response.
Task: Determine if the question is asking to query/analyze HR Database records (e.g., employee stats, salary, headcount, demographics).

Question: "{question}"

Reply ONLY with a valid JSON matching this exact schema:
{{
    "is_hr_data_query": boolean,
    "wants_visualization": boolean
}}"""
        try:
            # Gunakan ainvoke agar server tidak macet
            response = await self.llm_client.ainvoke(prompt)
            
            # Bersihkan markdown (```json ... ```) dari output AI
            content = response.content.replace('```json', '').replace('```', '').strip()
            result = json.loads(content)
            
            logger.info(f"🤖 LLM Intent Result: {result}")
            return {
                "is_hr_data_query": bool(result.get("is_hr_data_query", False)),
                # Kita percayai LLM, tapi jika LLM False dan Regex True, kita ambil True
                "wants_visualization": bool(result.get("wants_visualization", fallback_viz)) or fallback_viz
            }
        except Exception as e:
            logger.error(f"❌ LLM Intent Detection failed: {e}")
            # Jika LLM OpenAI sedang down/timeout, kembalikan aman (bukan HR)
            return {"is_hr_data_query": False, "wants_visualization": fallback_viz}