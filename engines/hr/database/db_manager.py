"""
Database Manager - Supabase PostgreSQL Edition
SATU-SATUNYA gerbang ke Supabase PostgreSQL database
Enterprise-grade connection management dengan schema hr
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Any, Tuple, Optional
from contextlib import contextmanager


class DatabaseManager:
    """
    Mengelola koneksi dan eksekusi SQL ke Supabase PostgreSQL
    HANYA urusan technical database, bukan business logic
    Fokus pada schema hr untuk HR analytics
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize dengan Supabase connection string
        
        Args:
            connection_string: PostgreSQL connection string untuk Supabase
                              Jika None, akan dibaca dari environment
        """
        self.connection_string = connection_string or self._get_supabase_connection()
        self.logger = logging.getLogger(__name__)
        
        # Validate connection on initialization
        if not self.test_connection():
            raise ConnectionError("Cannot connect to Supabase PostgreSQL database")
    
    def _get_supabase_connection(self) -> str:
        """Get Supabase connection string from environment"""
        connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        if connection_string:
            return connection_string
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_DB_PASSWORD")
        
        if not supabase_url or not supabase_password:
            raise ValueError("Missing Supabase configuration. Set SUPABASE_CONNECTION_STRING or (SUPABASE_URL + SUPABASE_DB_PASSWORD)")
        
        project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
        return f"postgresql://postgres:{supabase_password}@db.{project_id}.supabase.co:5432/postgres"
    
    @contextmanager
    def get_connection(self):
        """
        Context manager untuk Supabase PostgreSQL connection
        Automatically sets search_path to hr schema
        """
        conn = None
        try:
            conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor,
                sslmode='require'
            )
            conn.autocommit = False
            
            # Set search_path to hr schema untuk HR analytics
            with conn.cursor() as cursor:
                cursor.execute("SET search_path TO hr, public")
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Supabase connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
        """
        Execute SELECT query pada Supabase dan return hasil
        
        Args:
            sql: SQL SELECT statement
            params: Optional parameters for parameterized query
            
        Returns:
            Dict dengan 'columns', 'rows', dan metadata
            
        Raises:
            Exception: Jika query gagal atau bukan SELECT
        """
        # Security check - hanya SELECT yang diizinkan
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Get all rows as list of dicts
                    rows = cursor.fetchall()
                    
                    # Convert RealDictRow to regular dicts for JSON serialization
                    rows_list = [dict(row) for row in rows]
                    
                    self.logger.debug(f"Query executed successfully: {len(rows_list)} rows returned")
                    
                    return {
                        'columns': columns,
                        'rows': rows_list,
                        'total_rows': len(rows_list)
                    }
                    
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL query execution failed: {str(e)}")
            self.logger.error(f"SQL: {sql}")
            raise Exception(f"Supabase query failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Database query failed: {str(e)}")
            raise Exception(f"Database query failed: {str(e)}")
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a specific table dalam hr schema
        
        Args:
            table_name: Nama tabel (tanpa schema prefix)
            
        Returns:
            Dict dengan struktur tabel PostgreSQL
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get table schema dari information_schema (PostgreSQL standard)
                    cursor.execute("""
                        SELECT 
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            ordinal_position
                        FROM information_schema.columns 
                        WHERE table_schema = 'hr' 
                        AND table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                    
                    schema_info = cursor.fetchall()
                    
                    if not schema_info:
                        raise ValueError(f"Table 'hr.{table_name}' not found")
                    
                    columns = []
                    for column_info in schema_info:
                        columns.append({
                            'name': column_info['column_name'],
                            'type': column_info['data_type'],
                            'not_null': column_info['is_nullable'] == 'NO',
                            'default': column_info['column_default'],
                            'position': column_info['ordinal_position']
                        })
                    
                    return {
                        'table_name': f"hr.{table_name}",
                        'schema': 'hr',
                        'columns': columns,
                        'total_columns': len(columns)
                    }
                    
        except psycopg2.Error as e:
            self.logger.error(f"Failed to get table info for hr.{table_name}: {str(e)}")
            raise Exception(f"Failed to get table info: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to get table info for hr.{table_name}: {str(e)}")
            raise
    
    def list_tables(self, schema: str = 'hr') -> List[str]:
        """
        Get list of all tables dalam specified schema (default: hr)
        
        Args:
            schema: Database schema name (default: 'hr')
            
        Returns:
            List of table names (tanpa schema prefix)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """, (schema,))
                    
                    tables = [row['table_name'] for row in cursor.fetchall()]
                    
                    self.logger.debug(f"Found {len(tables)} tables in schema '{schema}'")
                    return tables
                    
        except psycopg2.Error as e:
            self.logger.error(f"Failed to list tables in schema '{schema}': {str(e)}")
            raise Exception(f"Failed to list tables: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to list tables in schema '{schema}': {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test Supabase PostgreSQL connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    
                    # Test hr schema access
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'hr'")
                    hr_tables = cursor.fetchone()
                    
                    self.logger.info(f"✅ Supabase connection successful. HR schema contains {hr_tables['count']} tables")
                    return True
                    
        except Exception as e:
            self.logger.error(f"❌ Supabase connection test failed: {str(e)}")
            return False
    
    def get_schema_info(self, schema: str = 'hr') -> Dict[str, Any]:
        """
        Get comprehensive schema information
        
        Args:
            schema: Schema name (default: 'hr')
            
        Returns:
            Dict dengan informasi lengkap schema
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get schema statistics
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as table_count
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                        AND table_type = 'BASE TABLE'
                    """, (schema,))
                    
                    stats = cursor.fetchone()
                    
                    # Get all tables with column counts
                    cursor.execute("""
                        SELECT 
                            table_name,
                            COUNT(*) as column_count
                        FROM information_schema.columns 
                        WHERE table_schema = %s
                        GROUP BY table_name
                        ORDER BY table_name
                    """, (schema,))
                    
                    tables_info = cursor.fetchall()
                    
                    return {
                        'schema_name': schema,
                        'table_count': stats['table_count'],
                        'tables': [dict(table) for table in tables_info],
                        'connection_type': 'Supabase PostgreSQL'
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get schema info for '{schema}': {str(e)}")
            raise