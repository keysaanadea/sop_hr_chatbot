"""
Schema Reader - Supabase PostgreSQL Only
✅ FAST CACHING EDITION (TTL 5 Minutes)
✅ SMART SAMPLING: 
   - Teks/Varchar: Sampling detail (Kategori lengkap)
   - Angka/Tanggal: Sampling ringan (Limit 3, tanpa kalkulasi berat)
"""

import time
import logging
from typing import Dict, Any

from engines.hr.database.db_manager import DatabaseManager

class SchemaReader:
    """OWNER TUNGGAL schema database untuk Supabase PostgreSQL"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager or DatabaseManager()
        
        # 🚀 CACHING SYSTEM
        self._cached_schema = None
        self._cache_timestamp = 0
        self._cache_ttl = 300  # Schema bertahan 5 menit di RAM (300 detik)
        
        self.logger.info("✅ SchemaReader initialized (With FAST Caching & Smart Sampling 🚀)")
    
    def get_schema(self, refresh_cache: bool = False) -> Dict[str, Any]:
        """Get schema dengan fitur Fast Cache (Mencegah ratusan query berulang)"""
        
        # Cek apakah cache masih segar (< 5 menit)
        if not refresh_cache and self._cached_schema and (time.time() - self._cache_timestamp < self._cache_ttl):
            self.logger.info("⚡ Using CACHED Schema (Instant!)")
            return self._cached_schema
            
        self.logger.info("🔄 Fetching FRESH Schema from Supabase... (This might take a few seconds)")
        start_time = time.time()
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'hr' 
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    
                    hr_tables = cursor.fetchall()
                    
                    if not hr_tables:
                        self.logger.warning("⚠️ No valid tables found in hr schema")
                        return {'total_tables': 0, 'schema_name': 'hr', 'tables': {}, 'formatted_schema': "No valid tables found."}
                    
                    schema = {'total_tables': len(hr_tables), 'schema_name': 'hr', 'connection_type': 'Supabase PostgreSQL', 'tables': {}}
                    
                    for table_info in hr_tables:
                        table_name = table_info['table_name'] if isinstance(table_info, dict) else table_info[0]
                        
                        cursor.execute("""
                            SELECT column_name, data_type FROM information_schema.columns 
                            WHERE table_schema = 'hr' AND table_name = %s ORDER BY ordinal_position
                        """, (table_name,))
                        
                        columns_info = cursor.fetchall()
                        columns = []
                        column_types = {}
                        distinct_values = {} 
                        
                        for col in columns_info:
                            col_name = col['column_name'] if isinstance(col, dict) else col[0]
                            data_type = col['data_type'] if isinstance(col, dict) else col[1]
                            
                            columns.append(col_name)
                            column_types[col_name] = data_type
                            
                            # ========================================================
                            # 🚀 SMART SAMPLING LOGIC
                            # ========================================================
                            try:
                                # 1. TEXT/VARCHAR (Sampling Detail: Cek Distinct Count)
                                if data_type in ('character varying', 'text', 'varchar', 'char'):
                                    cursor.execute(f"""
                                        SELECT COUNT(DISTINCT "{col_name}") 
                                        FROM hr."{table_name}" 
                                        WHERE "{col_name}" IS NOT NULL AND "{col_name}" != ''
                                    """)
                                    res_count = cursor.fetchone()
                                    distinct_count = res_count['count'] if isinstance(res_count, dict) else res_count[0]
                                    
                                    if distinct_count == 0: continue
                                        
                                    if distinct_count <= 30:
                                        cursor.execute(f"""
                                            SELECT DISTINCT "{col_name}" FROM hr."{table_name}"
                                            WHERE "{col_name}" IS NOT NULL AND "{col_name}" != ''
                                            ORDER BY "{col_name}"
                                        """)
                                        vals = cursor.fetchall()
                                        val_list = [v[col_name] if isinstance(v, dict) else v[0] for v in vals]
                                        distinct_values[col_name] = f"Kategori: {val_list}"
                                    else:
                                        cursor.execute(f"""
                                            SELECT "{col_name}" FROM hr."{table_name}"
                                            WHERE "{col_name}" IS NOT NULL AND "{col_name}" != '' LIMIT 3
                                        """)
                                        vals = cursor.fetchall()
                                        val_list = [v[col_name] if isinstance(v, dict) else v[0] for v in vals]
                                        distinct_values[col_name] = f"Contoh: {val_list} ... ({distinct_count} data unik)"
                                        
                                # 2. ANGKA/TANGGAL/BOOLEAN (Sampling Ringan: Cuma ambil 3 baris teratas)
                                elif data_type in ('integer', 'bigint', 'smallint', 'numeric', 'decimal', 'double precision', 'real', 'float', 'timestamp without time zone', 'timestamp with time zone', 'date', 'time', 'boolean', 'bool'):
                                    cursor.execute(f"""
                                        SELECT "{col_name}" FROM hr."{table_name}"
                                        WHERE "{col_name}" IS NOT NULL LIMIT 3
                                    """)
                                    vals = cursor.fetchall()
                                    # Ubah jadi string biar aman saat ditaruh di list
                                    val_list = [str(v[col_name] if isinstance(v, dict) else v[0]) for v in vals]
                                    if val_list:
                                        distinct_values[col_name] = f"Contoh: {val_list}"
                                        
                            except Exception as e:
                                self.logger.warning(f"⚠️ Gagal ambil sampel untuk {col_name}: {e}")
                        
                        schema['tables'][table_name] = {
                            'columns': columns, 
                            'column_types': column_types, 
                            'total_columns': len(columns),
                            'distinct_values': distinct_values
                        }
            
            schema['formatted_schema'] = self._format_schema_for_llm(schema)
            
            # 🚀 SIMPAN KE CACHE MEMORI!
            self._cached_schema = schema
            self._cache_timestamp = time.time()
            
            self.logger.info(f"✅ Schema Fresh dimuat dalam {time.time() - start_time:.2f} detik!")
            return schema
            
        except Exception as e:
            self.logger.error(f"❌ Schema reading failed: {e}")
            raise Exception(f"Schema reading failed: {str(e)}")
            
    def get_schema_text(self) -> str:
        try:
            schema = self.get_schema()
            return schema.get('formatted_schema', 'No schema available')
        except Exception as e:
            self.logger.error(f"❌ Failed to get schema text: {e}")
            return "ERROR: Database schema could not be loaded. Do not generate SQL."
            
    def _format_schema_for_llm(self, schema: Dict[str, Any]) -> str:
        try:
            lines = [
                "=== HR SCHEMA (Supabase PostgreSQL) ===",
                f"Schema: hr | Total Tables: {schema['total_tables']}\n",
                "📋 AVAILABLE TABLES & DATA EXAMPLES:\n"
            ]
            
            for table_name, table_info in schema['tables'].items():
                lines.append(f"TABLE: hr.{table_name} ({table_info['total_columns']} columns)")
                for col_name in table_info['columns']:
                    col_type = table_info['column_types'][col_name]
                    col_str = f"  • {col_name}: {col_type}"
                    
                    dist_vals = table_info.get('distinct_values', {}).get(col_name)
                    if dist_vals:
                        col_str += f"  --> {dist_vals}"
                        
                    lines.append(col_str)
                lines.append("")
            
            lines.extend([
                "=== SQL GENERATION GUIDELINES ===",
                "• Use schema prefix: hr.table_name",
                "• PostgreSQL syntax only",
                "• JOINs between hr tables are allowed",
                "• SANGAT PENTING: Gunakan referensi 'Kategori' atau 'Contoh' di atas saat memfilter (WHERE).",
                "• Jika user menggunakan sinonim (misal: 'Sarjana' atau 'Strata 1'), Anda WAJIB memetakan ke nilai yang TEPAT ada di 'Kategori' (misal: 'S1') menggunakan ILIKE.",
                "• DILARANG KERAS memfilter kolom 'band' dengan isian pendidikan. Kolom 'band' hanya untuk level jabatan/strata struktural."
            ])
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"❌ Failed to format schema: {e}")
            return "ERROR: Could not format schema."