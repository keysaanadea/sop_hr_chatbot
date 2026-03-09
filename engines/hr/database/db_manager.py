"""
Database Manager - Supabase PostgreSQL Edition
SATU-SATUNYA gerbang ke Supabase PostgreSQL database
Enterprise-grade connection management dengan schema hr
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, Any, Tuple, Optional, List
from contextlib import contextmanager

# ✅ FIX: Mengambil connection string langsung dari Config tersentralisasi
from app.config import SUPABASE_CONNECTION_STRING

class DatabaseManager:
    """Mengelola koneksi dan eksekusi SQL ke Supabase PostgreSQL"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or SUPABASE_CONNECTION_STRING
        self.logger = logging.getLogger(__name__)
        
        if not self.connection_string:
            self.logger.error("❌ SUPABASE_CONNECTION_STRING is missing!")
            raise ValueError("Database connection string is required")
            
        if not self.test_connection():
            self.logger.error("❌ Cannot connect to Supabase PostgreSQL database")
    
    @contextmanager
    def get_connection(self):
        """Context manager untuk Supabase PostgreSQL connection"""
        conn = None
        try:
            conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor,
                sslmode='require',
                connect_timeout=10 # ✅ Tambahan safety timeout untuk Digital Ocean
            )
            conn.autocommit = False
            
            with conn.cursor() as cursor:
                cursor.execute("SET search_path TO hr, public")
            
            yield conn
            
        except Exception as e:
            if conn: conn.rollback()
            self.logger.error(f"❌ Supabase connection error: {e}")
            raise
        finally:
            if conn: conn.close()
    
    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
        """Execute SELECT query pada Supabase dan return hasil"""
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params) if params else cursor.execute(sql)
                    
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    rows_list = [dict(row) for row in rows]
                    
                    self.logger.info(f"✅ Query executed successfully: {len(rows_list)} rows returned")
                    return {'columns': columns, 'rows': rows_list, 'total_rows': len(rows_list)}
                    
        except Exception as e:
            self.logger.error(f"❌ Database query failed: {e}\nSQL: {sql}")
            raise Exception(f"Database query failed: {str(e)}")
            
    def test_connection(self) -> bool:
        """Test Supabase PostgreSQL connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'hr'")
                    hr_tables = cursor.fetchone()
                    self.logger.info(f"✅ Supabase connection successful. HR schema: {hr_tables['count']} tables")
                    return True
        except Exception as e:
            self.logger.error(f"❌ Supabase connection test failed: {e}")
            return False