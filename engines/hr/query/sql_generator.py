"""
SQL Generator - Enhanced Natural Language Understanding for Indonesian HR Queries
Generates SQL ONLY untuk Supabase PostgreSQL
ENHANCED dengan natural language flexibility untuk bahasa casual dan formal
TIDAK ADA SQLite syntax atau logic
"""

import logging
from typing import Dict, Any, Optional
import openai
import os


class SQLGenerator:
    """
    Enhanced PostgreSQL SQL generator untuk Supabase
    HANYA menggunakan PostgreSQL syntax dan hr schema
    ENHANCED dengan natural Indonesian language understanding
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
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
1. Deteksi apakah ini casual/formal language
2. Identifikasi key words untuk analytical intent
3. Tentukan pattern yang tepat (distribusi/ranking/statistik)
4. Pilih tabel dan kolom yang relevan dari schema
5. Generate SQL dengan formula yang mathematically correct

GENERATE SQL PostgreSQL yang akurat:
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
            
            # Clean up SQL
            sql = self._clean_sql(sql)
            
            self.logger.info(f"✅ Indonesian natural language SQL generated: {sql[:100]}...")
            return sql
            
        except Exception as e:
            self.logger.error(f"Indonesian natural language SQL generation failed: {str(e)}")
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def _clean_sql(self, sql: str) -> str:
        """
        Enhanced cleaning untuk Indonesian natural language generated SQL
        """
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
        sql_upper = sql.upper()
        
        if 'OVER' in sql_upper:
            # Ensure parentheses balance for OVER clauses
            over_positions = [i for i, char in enumerate(sql_upper) if sql_upper[i:i+4] == 'OVER']
            
            for pos in over_positions:
                # Find the opening parenthesis after OVER
                remaining = sql[pos+4:].strip()
                if not remaining.startswith('('):
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