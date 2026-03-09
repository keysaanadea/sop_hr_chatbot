import os
import json
import psycopg2
import asyncio
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ConstraintInterceptor:
    def __init__(self):
        # Ambil koneksi Supabase dari .env dan bersihkan formatnya
        raw_conn_str = os.getenv("SUPABASE_CONNECTION_STRING", "")
        self.db_conn_str = raw_conn_str.strip().strip("'").strip('"').replace("postgres://", "postgresql://", 1)
        
        # ✅ SIMPLE CACHE: Store guardrails by filename
        self._guardrails_cache = {}

    async def get_rules_async(self, filename: str) -> List[Dict]:
        """
        Menarik "Buku Aturan" (JSON Constraints) dari Supabase berdasarkan nama file.
        ✅ WITH CACHING: Hanya fetch dari DB sekali, selanjutnya pakai cache!
        """
        # ✅ Check cache first
        if filename in self._guardrails_cache:
            logger.debug(f"⚡ Cache hit for guardrails: {filename}")
            return self._guardrails_cache[filename]
        
        if not self.db_conn_str:
            return []

        def _fetch():
            try:
                conn = psycopg2.connect(self.db_conn_str)
                cursor = conn.cursor()

                # Tarik data JSONB dari database
                cursor.execute("""
                    SELECT rules_json 
                    FROM sop.document_rules 
                    WHERE filename = %s;
                """, (filename,))
                
                result = cursor.fetchone()
                cursor.close()
                conn.close()

                if result and result[0]:
                    rules_data = result[0]
                    if isinstance(rules_data, str):
                        rules_data = json.loads(rules_data)
                    
                    # Mengembalikan list of constraints
                    return rules_data.get("constraints", [])
                return []
            except Exception as e:
                logger.error(f"⚠️ Gagal menarik aturan dari Supabase untuk {filename}: {e}")
                return []

        # Jalankan fungsi blocking di background thread agar aman untuk asyncio
        rules = await asyncio.to_thread(_fetch)
        
        # ✅ Store in cache
        self._guardrails_cache[filename] = rules
        logger.debug(f"💾 Cached guardrails for: {filename}")
        
        return rules

    async def generate_guardrail_prompt_async(self, relevant_filenames: List[str]) -> str:
        """
        Membangun instruksi paksaan (Guardrails) untuk LLM.
        MENARIK ATURAN SECARA PARALEL (asyncio.gather) agar super cepat!
        """
        unique_files = list(set(relevant_filenames))
        if not unique_files:
            return ""

        # 🌟 1. BUAT DAFTAR TUGAS (TASKS) UNTUK DIAMBIL PARALEL
        tasks = [self.get_rules_async(fname) for fname in unique_files]

        # 🌟 2. JALANKAN SECARA PARALEL! (Semua query jalan barengan)
        results = await asyncio.gather(*tasks)

        # 🌟 3. GABUNGKAN SEMUA HASILNYA
        all_constraints = []
        for constraints in results:
            if constraints:
                all_constraints.extend(constraints)

        if not all_constraints:
            return "" 

        # 🌟 4. BANGUN TEKS SUNTIKAN (PROMPT)
        guardrail_prompt = "\n\n" + "="*50 + "\n"
        guardrail_prompt += "🚨 SYSTEM GUARDRAILS (ATURAN KAKU PERUSAHAAN) 🚨\n"
        guardrail_prompt += "ANDA WAJIB MEMATUHI BATASAN BERIKUT DALAM MELAKUKAN PERHITUNGAN ATAU MEMBERIKAN JAWABAN:\n\n"

        for idx, rule in enumerate(all_constraints, 1):
            topic = rule.get('topic', 'Aturan')
            desc = rule.get('description', '')
            rule_type = rule.get('type', '')
            
            # Antisipasi kalau key-nya 'value_max' atau 'value'
            val = rule.get('value')
            if val is None:
                val = rule.get('value_max', '')
            
            unit = rule.get('unit', '')
            
            guardrail_prompt += f"{idx}. [{topic.upper()}] -> {desc}\n"
            guardrail_prompt += f"   - Batasan Kaku: Tipe '{rule_type}', Nilai Maksimal/Pasti: {val} {unit}\n"

        guardrail_prompt += "\n🔥 INSTRUKSI KRITIS UNTUK AI (WAJIB DIIKUTI):\n"
        guardrail_prompt += "- JIKA input user (jam lembur, tarif hotel, jarak, dll) MELEBIHI atau MELANGGAR batasan di atas, Anda DILARANG KERAS menuruti angka user.\n"
        guardrail_prompt += "- Anda WAJIB MENGOREKSI hitungan menggunakan angka batas maksimal dari aturan di atas.\n"
        guardrail_prompt += "- Anda WAJIB mematuhi ATURAN MUTLAK No. 7 terkait TAMPILAN KOREKSI untuk menampilkan pemberitahuan ini.\n"
        guardrail_prompt += "="*50 + "\n"

        return guardrail_prompt