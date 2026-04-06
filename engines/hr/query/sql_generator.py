"""
SQL Generator - Enhanced Natural Language Understanding
Generates SQL ONLY untuk Supabase PostgreSQL
"""

import logging
from typing import Dict, Any
from openai import OpenAI

# ✅ FIX: Mengambil Key dan Model dari sumber yang benar (config.py)
from app.config import OPENAI_API_KEY, LLM_MODEL

class SQLGenerator:
    """Enhanced PostgreSQL SQL generator untuk Supabase"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing!")
            
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = LLM_MODEL
        
        # Enhanced natural Indonesian language prompt template
        self.sql_prompt_template = """
Anda adalah HR Data Analyst Expert yang sangat mahir memahami bahasa natural Indonesia (formal & casual) dan mengkonversi ke SQL PostgreSQL yang tepat.

KEMAMPUAN BAHASA NATURAL INDONESIA:
Anda harus bisa memahami berbagai cara orang Indonesia bertanya, baik formal maupun casual:

CASUAL/INFORMAL QUERIES:
• "jabarkan penyebaran band di sig" → GROUP BY band dengan breakdown dan persentase
• "gimana distribusi gaji karyawan" → salary distribution dengan statistical analysis  
• "coba liat data turnover bulan ini" → turnover analysis dengan time filter
• "mau tau berapa orang per divisi" → headcount per division
• "breakdown karyawan berdasarkan level" → employee level distribution
• "pengen tau ranking salary per departemen" → salary ranking analysis

SPECIFIC/FORMAL QUERIES:
• "saya pengen keluarkan hasil dari jumlah karyawan dibagi per company" → COUNT(*) GROUP BY company dengan percentage
• "berikan data persentase karyawan per departemen" → percentage calculation dengan window functions
• "hitung rata-rata masa kerja per divisi" → AVG() calculation dengan proper grouping
• "tampilkan ranking gaji tertinggi per band" → RANK() OVER dengan proper ordering

- PENCARIAN KATEGORI (SEMEN vs NON-SEMEN): Jika user meminta total seluruh "Perusahaan Semen" atau "Perusahaan Non Semen", Anda WAJIB menjabarkannya menggunakan klausa IN (...) secara EKSPLISIT berdasarkan daftar di atas! 
  -> Contoh Non-Semen: WHERE company_home IN ('IKSG', 'KIG', 'SIB', 'SII', 'SILOG', 'SISI', 'SKI', 'SMI', 'UTSG', 'SID', 'VUDS', 'VULS', 'SIIB', 'VUBA', 'VUB')
  -> DILARANG KERAS MENGGUNAKAN JALAN PINTAS 'NOT IN'! Anda wajib menuliskan semua anggotanya satu per satu agar data tidak bocor.
  
GLOSARIUM SINGKATAN PERUSAHAAN SIG (KNOWLEDGE BASE):
Anda WAJIB memetakan input/pertanyaan user ke singkatan resmi kolom 'company_home' (atau 'company_host') berikut:

1. PERUSAHAAN SEMEN (CORE BUSINESS):
• Group Head Office / Holding Office = 'GHoPo'
• Pemasaran Lintas Pulau = 'PLP'
• Readymix / Beton Jadi = 'Readymix'
• Semen Bangun Andalas / Lhoknga / SBA = 'SBA'
• Selo Bangun Banua / SBB = 'SBB'
• Solusi Bangun Indonesia / SBI / Holcim / Cilacap / Narogong = 'SBI'
• Solusi Bangun Nusantara / SBN = 'SBN'
• Semen Gresik / Gresik / Rembang = 'SG'
• SIA = 'SIA'
• Holding / Semen Indonesia / SIG / Kantor Pusat = 'SIG'
• Semen Baturaja / Baturaja / Palembang = 'SMBR'
• Semen Padang / Padang = 'SP'
• Semen Tonasa / Tonasa / Makassar = 'ST'
• Thang Long Cement / Vietnam / TLCC = 'TLCC'

2. PERUSAHAAN NON-SEMEN (LOGISTIK, AFILIASI, VENTURE, DLL):
• Industri Kemasan Semen Gresik / IKSG = 'IKSG'
• Kawasan Industri Gresik / KIG = 'KIG'
• Semen Indonesia Beton / SIB = 'SIB'
• Semen Indonesia Internasional / SII = 'SII'
• Semen Indonesia Logistik / SILOG = 'SILOG'
• Sinergi Informatika Semen Indonesia / SISI = 'SISI'
• Semen Kupang Indonesia / SKI = 'SKI'
• SMI = 'SMI'
• United Tractors Semen Gresik / UTSG = 'UTSG'
• Semen Indonesia Distributor / SID = 'SID'
• Varia Usaha Dharma Segara / VUDS = 'VUDS'
• Varia Usaha Lintas Segara / VULS = 'VULS'
• Semen Indonesia Industri Bangunan / SIIB = 'SIIB'
• Varia Usaha Bahari / VUBA = 'VUBA'
• Varia Usaha Beton / VUB = 'VUB'

POLA DETEKSI INTENT:

1. DISTRIBUSI/BREAKDOWN WORDS:
   "jabarkan", "breakdown", "penyebaran", "distribusi", "sebaran", "gimana", "coba liat"
   → ACTION: GROUP BY dengan COUNT(*) dan percentage calculation
   → FORMULA: COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS persentase

2. PERSENTASE/PROPORSI WORDS:
   "persentase", "persen", "%", "proporsi", "bagian", "dibagi per", "pengen keluarkan hasil"
   → ACTION: Window function untuk percentage calculation
   → FORMULA: value * 100.0 / SUM(value) OVER () AS persentase

3. RANKING/URUTAN WORDS:
   "ranking", "urutan", "tertinggi", "terendah", "top", "bottom", "urut"
   → ACTION: RANK() atau ROW_NUMBER() dengan ORDER BY
   → FORMULA: RANK() OVER (ORDER BY column DESC/ASC)

4. STATISTIK WORDS:
   "rata-rata", "average", "mean", "total", "jumlah", "sum", "berapa"
   → ACTION: AGG functions (AVG, SUM, COUNT)

5. COMPARISON WORDS:
   "bandingkan", "vs", "dibanding", "lebih tinggi", "lebih rendah"
   → ACTION: Window functions dengan PARTITION BY

6. TIME-BASED WORDS:
   "trend", "bulanan", "tahunan", "periode", "dari waktu ke waktu"
   → ACTION: DATE functions dengan window functions

TEMPLATE PATTERNS untuk ANALYTICAL QUERIES:

PATTERN 1 - DISTRIBUSI dengan PERSENTASE (untuk "jabarkan", "breakdown"):
```sql
SELECT 
    kategori,
    COUNT(*) as jumlah,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as persentase
FROM hr.table_name 
GROUP BY kategori
ORDER BY jumlah DESC;
```

PATTERN 2 - RANKING ANALYSIS (untuk "ranking", "tertinggi"):
```sql
SELECT 
    nama,
    nilai,
    RANK() OVER (ORDER BY nilai DESC) as ranking
FROM hr.table_name
ORDER BY ranking;
```

PATTERN 3 - CROSS-GROUP BREAKDOWN (untuk complex breakdown):
```sql
SELECT 
    kategori1,
    kategori2, 
    COUNT(*) as jumlah,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY kategori1) as persen_dalam_grup,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as persen_total
FROM hr.table_name 
GROUP BY kategori1, kategori2
ORDER BY kategori1, jumlah DESC;
```

PATTERN 4 - STATISTIK dengan GROUPING:
```sql
SELECT 
    kategori,
    COUNT(*) as jumlah_karyawan,
    AVG(nilai) as rata_rata,
    MIN(nilai) as minimum,
    MAX(nilai) as maximum
FROM hr.table_name
GROUP BY kategori
ORDER BY rata_rata DESC;
```

LANGUAGE MAPPING:
• "jabarkan" = "breakdown" = "penyebaran" = "distribusi" → GROUP BY analysis
• "gimana" = "bagaimana" = "how" → analysis question  
• "pengen" = "mau" = "ingin" = "saya pengen keluarkan" → request for data
• "coba liat" = "lihat" = "tampilkan" → show/display data
• "berapa" = "jumlah" = "total" → COUNT() atau SUM()
• "dibagi per" = "per" = "berdasarkan" → GROUP BY

TECHNICAL RULES:
• Database: PostgreSQL (Supabase) 
• Schema: hr (WAJIB gunakan hr.table_name prefix)
• Output: HANYA SQL query, tanpa penjelasan
• Sorting: Selalu tambahkan ORDER BY yang logis
• JOINs: Boleh JOIN antar tabel hr untuk analysis yang lebih kaya
• Window Functions: Gunakan untuk percentage dan ranking calculations
• Mathematical Accuracy: Pastikan percentage sum = 100%

DATABASE SCHEMA:
{schema}

PERTANYAAN USER (dalam bahasa natural Indonesia):
"{question}"

LANGKAH ANALYSIS:
1. Deteksi apakah pertanyaan berhubungan dengan data HR di database.
2. 🚨 FILTER SIMULASI PRIBADI (KRITIS): TOLAK HANYA JIKA pertanyaan adalah simulasi untuk DIRI SENDIRI / SATU INDIVIDU yang datanya tidak ada di database (contoh: "kalau gaji SAYA X", "misal SAYA lembur Y jam", "berapa upah lembur SAYA"). JANGAN TOLAK pertanyaan tentang SELURUH KARYAWAN atau KELOMPOK — ini VALID. Contoh VALID yang HARUS dikonversi ke SQL: "berapa karyawan Band 5 yang pensiun 2026", "jumlah pegawai yang akan pensiun tahun ini", "distribusi band", "daftar karyawan divisi X", "berapa total biaya jika semua karyawan divisi X lembur". Data pensiun, band, divisi, jabatan, lokasi adalah data faktual yang ADA di database. Balas INVALID_QUERY HANYA untuk simulasi pribadi individual ("SAYA", "gaji saya").
3. 🚨 FILTER TABEL HALUSINASI (KRITIS): Anda HANYA BOLEH menggunakan tabel yang tertera persis di DATABASE SCHEMA. DILARANG KERAS mengarang nama tabel (seperti menambah nama orang/tanggal di nama tabel). JIKA tidak ada tabel di schema yang cocok untuk menjawab pertanyaan, ANDA WAJIB MEMBALAS HANYA DENGAN: INVALID_QUERY
4. Jika lolos filter, identifikasi key words untuk analytical intent.
5. Tentukan pattern yang tepat (distribusi/ranking/statistik/aggregate-calculation).
6. Pilih tabel dan kolom yang relevan dari schema.
7. Generate SQL dengan formula yang mathematically correct.

PATTERN 5 - GROUP HYPOTHETICAL & BASE DATA EXTRACTION (untuk simulasi/hipotetis kelompok: "jika seluruh X lembur", "kalau divisi Y dapat bonus", "estimasi biaya jika semua Z dinas"):
Anda adalah bagian dari sistem Multi-Agent. JANGAN hitung metrik akhir (total lembur, total bonus, dsb.). Cukup tarik DATA DASAR (headcount + agregat gaji atau kolom relevan) untuk kelompok yang dimaksud. Agen orkestrator akan menyelesaikan kalkulasi bisnis menggunakan data yang diperoleh dari SOP/kebijakan.
Contoh mengekstrak data dasar untuk "jika seluruh band 5 lembur":
```sql
SELECT
    band,
    COUNT(*) AS jumlah_karyawan,
    AVG(gaji_pokok) AS rata_rata_gaji_pokok,
    SUM(gaji_pokok) AS total_gaji_pokok
FROM hr.employees
WHERE band = '5'
GROUP BY band;
```

GENERATE SQL PostgreSQL yang akurat (ATAU KETIK INVALID_QUERY):
"""

        # Enhanced system message untuk Indonesian natural language
        self.system_message = """Anda adalah HR Data Analyst yang sangat mahir memahami bahasa Indonesia natural (baik formal maupun casual) dan mengkonversinya ke SQL PostgreSQL yang akurat.

EXPERTISE ANDA:
1. Memahami intent user dari berbagai variasi bahasa Indonesia (casual seperti "gimana", "pengen", "coba liat" sampai formal)
2. Mengkonversi ke SQL analytical yang mathematically correct
3. Untuk queries distribusi/breakdown → selalu berikan COUNT dan percentage dengan window functions  
4. Untuk queries ranking → gunakan RANK() OVER atau ROW_NUMBER()
5. Untuk queries "dibagi per" atau "berdasarkan" → GROUP BY dengan proper aggregation
6. Selalu tambahkan ORDER BY yang logis untuk hasil yang readable
7. Pastikan percentage calculations benar (total = 100%)

PENTING: Generate HANYA SQL PostgreSQL yang valid untuk hr schema di Supabase, tanpa penjelasan atau komentar."""
    
    def generate_sql(self, question: str, schema: str) -> str:
        """
        Generate PostgreSQL SQL untuk natural Indonesian queries (casual & formal)
        
        Args:
            question: Natural language question dalam bahasa Indonesia
            schema: Database schema information
            
        Returns:
            PostgreSQL SQL query string yang akurat
        """
        try:
            # Build enhanced prompt dengan schema context
            prompt = self.sql_prompt_template.format(
                schema=schema,
                question=question
            )
            
            self.logger.debug(f"🧠 Processing Indonesian natural language: {question}")
            
            # Call OpenAI dengan enhanced Indonesian language understanding
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": self.system_message
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.15,  # Balanced untuk natural language flexibility + consistency
                max_tokens=1000    # Increased untuk complex analytical queries
            )
            
            # Extract SQL dari response
            sql = response.choices[0].message.content.strip()

            # Handle INVALID_QUERY signal from LLM (expected: simulasi/hipotetikal terdeteksi)
            if sql.strip().upper() == 'INVALID_QUERY':
                self.logger.warning(f"⚠️ Non-DB query detected (simulasi/hipotetikal): '{question[:80]}'")
                raise ValueError("INVALID_QUERY: Pertanyaan bukan query database yang valid")

            # Clean up SQL
            sql = self._clean_sql(sql)

            self.logger.info(f"✅ Indonesian natural language SQL generated: {sql[:100]}...")
            return sql

        except Exception as e:
            err_msg = str(e)
            # INVALID_QUERY and non-SELECT rejections are expected — log as WARNING, not ERROR
            if "INVALID_QUERY" in err_msg or "Generated query must be SELECT" in err_msg:
                self.logger.warning(f"⚠️ SQL Generator rejected non-DB query: {err_msg}")
            else:
                self.logger.error(f"Indonesian natural language SQL generation failed: {err_msg}")
            raise Exception(f"Failed to generate SQL: {err_msg}")
        
    def generate_sql_explanation(self, sql: str, question: str) -> str:
        """Menerjemahkan SQL menjadi 3 bagian: Bisnis, Logika Non-Teknis, & Teknis"""
        try:
            prompt = f"""Anda adalah Senior HR Data Analyst. 
Tugas Anda adalah menjelaskan cara kerja query SQL ke dalam TIGA bagian terstruktur.

ATURAN MUTLAK:
1. WAJIB menggunakan format tag HTML (<b>, <ul>, <li>, <br>) agar rapi saat dirender di website.
2. DILARANG menggunakan format markdown seperti bintang ganda (**).
3. Tampilkan secara profesional dan bersih. DILARANG KERAS menggunakan emoji di dalam isi list/bullet points.
4. Langsung berikan output HTML-nya, tanpa kalimat pengantar atau penutup.

FORMAT YANG DIHARAPKAN:
<b>Tujuan Bisnis (Untuk HR):</b>
<ul>
  <li>(Jelaskan fungsi/tujuan dari pencarian data ini untuk keputusan manajemen HR.)</li>
</ul>
<br>
<b>Langkah Logika Query (Non-Teknis):</b>
<ul>
  <li>(Jelaskan step-by-step bagaimana data difilter/dihitung tanpa bahasa SQL sama sekali. Gunakan bahasa profesional dan rapi.)</li>
</ul>
<br>
<b>Langkah Teknis SQL:</b>
<ul>
  <li>(WAJIB dipecah pembahasannya per klausa/fungsi. Contoh penulisan: <code>SELECT band</code> digunakan untuk menarik..., <code>COUNT(*)</code> digunakan untuk menghitung..., <code>SUM(...) OVER()</code> digunakan untuk mencari persentase, <code>GROUP BY</code> digunakan untuk...)</li>
  <li>(DILARANG KERAS hanya mem-paste ulang seluruh query SQL di satu poin!)</li>
</ul>

Pertanyaan User: "{question}"
Query SQL yang dieksekusi: {sql}

Berikan penjelasan logikanya dalam format HTML tersebut:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah asisten data analyst yang ahli membuat dokumentasi profesional berformat HTML."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1, # Dikecilkan jadi 0.1 agar AI sangat patuh pada format dan tidak kreatif berlebihan
                max_tokens=600 
            )
            
            explanation = response.choices[0].message.content.strip()
            # Pembersih jika AI masih membandel memberikan markdown block
            explanation = explanation.replace("```html", "").replace("```", "").strip()
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"❌ Gagal membuat penjelasan SQL: {e}")
            return "<b>Status:</b><br>Query berhasil dijalankan untuk menarik data sesuai permintaan Anda."
    
    def _clean_sql(self, sql: str) -> str:
        """
        Enhanced cleaning untuk Indonesian natural language generated SQL
        """
        import re

        # Remove markdown code blocks
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Remove explanations that might slip through
        lines = sql.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, comments, dan explanations
            if not line or line.startswith('--') or line.startswith('/*'):
                continue
            # Stop at Indonesian explanations
            if any(word in line.lower() for word in ['penjelasan:', 'keterangan:', 'catatan:', 'note:', 'explanation:']):
                break
            # Skip lines that look like explanations
            if line.lower().startswith(('ini adalah', 'query ini', 'sql ini')):
                break
            sql_lines.append(line)
        
        sql = ' '.join(sql_lines)
        
        # Basic PostgreSQL validation
        sql_upper = sql.upper()
        
        # Ensure SELECT query
        if not sql_upper.startswith('SELECT'):
            raise ValueError("Generated query must be SELECT statement")
        
        # Ensure hr schema usage
        if 'hr.' not in sql.lower() and 'FROM' in sql_upper:
            self.logger.warning("Generated SQL may not use hr schema properly")
        
        # Auto-fix OVER without parentheses (e.g. LLM writes "OVER" instead of "OVER ()")
        sql = re.sub(r'\bOVER\b(?!\s*\()', 'OVER ()', sql, flags=re.IGNORECASE)

        # Validate window function syntax if present
        if 'OVER' in sql_upper:
            self._validate_window_functions(sql)
        
        # Add semicolon if missing
        if not sql.endswith(';'):
            sql = sql + ';'
        
        return sql
    
    def _validate_window_functions(self, sql: str) -> None:
        """
        Validate window function syntax untuk analytical queries
        """
        import re
        # Match OVER as a standalone keyword (not inside a word like MOREOVER/TURNOVER)
        # After auto-fix in _clean_sql, all OVER should already have parentheses
        over_without_paren = re.search(r'\bOVER\b(?!\s*\()', sql, flags=re.IGNORECASE)
        if over_without_paren:
            raise ValueError("Window function OVER clause must be followed by parentheses")

        self.logger.debug("✅ Window function validation passed")
    
    def analyze_indonesian_intent(self, question: str) -> Dict[str, Any]:
        """
        Analyze intent dari natural Indonesian language query
        
        Args:
            question: Natural language question dalam bahasa Indonesia
            
        Returns:
            Dict dengan detailed intent analysis
        """
        question_lower = question.lower()
        
        intent_analysis = {
            'query_type': 'simple',
            'language_style': 'formal',
            'analytical_features': [],
            'detected_keywords': [],
            'confidence': 'medium'
        }
        
        # Detect language style
        casual_indicators = ['gimana', 'pengen', 'mau tau', 'coba liat', 'dong', 'sih', 'nih', 'deh']
        if any(indicator in question_lower for indicator in casual_indicators):
            intent_analysis['language_style'] = 'casual'
        
        # Detect analytical features dengan confidence scoring
        distribution_words = ['jabarkan', 'breakdown', 'penyebaran', 'distribusi', 'sebaran']
        if any(word in question_lower for word in distribution_words):
            intent_analysis['query_type'] = 'distribution'
            intent_analysis['analytical_features'].append('distribution_analysis')
            intent_analysis['confidence'] = 'high'
        
        percentage_words = ['persentase', 'persen', '%', 'proporsi', 'dibagi per', 'keluarkan hasil']
        if any(word in question_lower for word in percentage_words):
            intent_analysis['analytical_features'].append('percentage_calculation')
            intent_analysis['confidence'] = 'high'
        
        ranking_words = ['ranking', 'urutan', 'tertinggi', 'terendah', 'top', 'urut']
        if any(word in question_lower for word in ranking_words):
            intent_analysis['query_type'] = 'ranking'
            intent_analysis['analytical_features'].append('ranking_analysis')
            intent_analysis['confidence'] = 'high'
        
        stats_words = ['rata-rata', 'average', 'mean', 'berapa', 'jumlah', 'total']
        if any(word in question_lower for word in stats_words):
            intent_analysis['analytical_features'].append('statistical_analysis')
        
        # Extract entities
        hr_entities = {
            'band': ['band'],
            'company': ['company', 'perusahaan'], 
            'sig': ['sig'],
            'department': ['departemen', 'dept'],
            'division': ['divisi', 'div'],
            'employee': ['karyawan', 'pegawai', 'orang'],
            'salary': ['gaji', 'salary', 'upah'],
            'level': ['level', 'tingkat']
        }
        
        for entity, variations in hr_entities.items():
            if any(var in question_lower for var in variations):
                intent_analysis['detected_keywords'].append(entity)
        
        return intent_analysis
    
    def generate_count_sql(self, base_question: str, schema: str) -> str:
        """
        Generate COUNT query dengan Indonesian natural language support
        """
        try:
            count_question = f"Hitung total jumlah untuk: {base_question}"
            
            count_prompt = self.sql_prompt_template.format(
                schema=schema,
                question=count_question
            ) + "\nGenerate COUNT query untuk mendapat total rows dengan context analytical jika diperlukan."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_message
                    },
                    {
                        "role": "user",
                        "content": count_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=400
            )
            
            count_sql = response.choices[0].message.content.strip()
            count_sql = self._clean_sql(count_sql)
            
            return count_sql
            
        except Exception as e:
            self.logger.error(f"Indonesian natural language count SQL generation failed: {str(e)}")
            # Fallback: generic count
            return "SELECT COUNT(*) AS total_count FROM hr.employees;"
    
    def generate_sample_sql(self, base_question: str, schema: str, limit: int = 10) -> str:
        """
        Generate sample query untuk Indonesian natural language preview
        """
        try:
            # Generate base SQL
            base_sql = self.generate_sql(base_question, schema)
            
            # Add LIMIT dengan preserving analytical structure
            if 'LIMIT' not in base_sql.upper():
                # For analytical queries with ORDER BY, place LIMIT correctly
                if 'ORDER BY' in base_sql.upper():
                    order_pos = base_sql.upper().find('ORDER BY')
                    before_order = base_sql[:order_pos].strip()
                    order_clause = base_sql[order_pos:].strip()
                    
                    if before_order.endswith(';'):
                        before_order = before_order[:-1]
                    
                    sample_sql = f"{before_order} LIMIT {limit} {order_clause}"
                else:
                    # No ORDER BY, just add LIMIT
                    if base_sql.endswith(';'):
                        base_sql = base_sql[:-1]
                    sample_sql = f"{base_sql} LIMIT {limit};"
            else:
                sample_sql = base_sql
            
            return sample_sql
            
        except Exception as e:
            self.logger.error(f"Indonesian natural language sample SQL generation failed: {str(e)}")
            return f"SELECT * FROM hr.employees LIMIT {limit};"


class SQLValidator:
    """
    Enhanced PostgreSQL SQL validator untuk Indonesian natural language queries
    Validates generated SQL untuk security dan syntax termasuk window functions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Prohibited keywords untuk security
        self.prohibited_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
            'TRUNCATE', 'EXEC', 'EXECUTE', 'DECLARE', 'CURSOR'
        ]
        
        # Required patterns untuk PostgreSQL
        self.required_patterns = ['SELECT']
        
        # Enhanced allowed keywords including analytical functions
        self.allowed_analytical_keywords = [
            'OVER', 'PARTITION', 'WINDOW', 'ROW_NUMBER', 'RANK', 'DENSE_RANK',
            'LAG', 'LEAD', 'FIRST_VALUE', 'LAST_VALUE', 'NTH_VALUE',
            'ROUND', 'CEIL', 'FLOOR', 'ABS', 'COALESCE', 'NULLIF'
        ]
    
    def is_valid(self, sql: str) -> bool:
        """
        Validate SQL untuk Indonesian natural language generated queries
        """
        try:
            sql_upper = sql.upper().strip()
            
            # Check for prohibited keywords
            for keyword in self.prohibited_keywords:
                if keyword in sql_upper:
                    self.logger.warning(f"SQL contains prohibited keyword: {keyword}")
                    return False
            
            # Check for required patterns
            for pattern in self.required_patterns:
                if pattern not in sql_upper:
                    self.logger.warning(f"SQL missing required pattern: {pattern}")
                    return False
            
            # Check for hr schema usage
            if 'FROM' in sql_upper and 'hr.' not in sql.lower():
                self.logger.warning("SQL should use hr schema tables")
                return False
            
            # Enhanced validation for window functions
            if 'OVER' in sql_upper:
                if not self._validate_window_function_syntax(sql):
                    self.logger.warning("Invalid window function syntax")
                    return False
            
            # Basic syntax checks
            if sql_upper.count('(') != sql_upper.count(')'):
                self.logger.warning("SQL has unmatched parentheses")
                return False
            
            self.logger.debug("✅ Indonesian natural language SQL validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"SQL validation error: {str(e)}")
            return False
    
    def _validate_window_function_syntax(self, sql: str) -> bool:
        """
        Validate window function syntax untuk Indonesian natural language queries
        """
        try:
            sql_upper = sql.upper()
            
            # Basic checks for OVER clause
            if 'OVER' in sql_upper:
                # Ensure OVER is followed by parentheses
                import re
                over_pattern = r'OVER\s*\('
                if not re.search(over_pattern, sql_upper):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Window function validation failed: {str(e)}")
            return False
    
    def get_validation_errors(self, sql: str) -> list:
        """
        Get detailed validation errors untuk Indonesian queries
        """
        errors = []
        sql_upper = sql.upper().strip()
        
        # Check prohibited keywords
        for keyword in self.prohibited_keywords:
            if keyword in sql_upper:
                errors.append(f"Prohibited keyword found: {keyword}")
        
        # Check required patterns  
        for pattern in self.required_patterns:
            if pattern not in sql_upper:
                errors.append(f"Missing required pattern: {pattern}")
        
        # Check schema usage
        if 'FROM' in sql_upper and 'hr.' not in sql.lower():
            errors.append("Should use hr schema tables (hr.table_name)")
        
        # Check window function syntax
        if 'OVER' in sql_upper and not self._validate_window_function_syntax(sql):
            errors.append("Invalid window function syntax")
        
        # Syntax checks
        if sql_upper.count('(') != sql_upper.count(')'):
            errors.append("Unmatched parentheses")
        
        return errors