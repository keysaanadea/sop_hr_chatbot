"""
Query Executor - COMPLETE FIXED VERSION
Menjalankan SQL HANYA di Supabase PostgreSQL dengan data structure yang BENAR
TIDAK ADA SQLite dependencies, TIDAK ADA result mapping bugs
"""

import logging
from typing import Dict, Any
import psycopg2


class QueryResult:
    """
    QueryResult model yang menyimpan result query dalam format yang benar
    TIDAK ada bug data mapping
    """
    
    def __init__(self, columns: list, rows: list, total_rows: int):
        """
        Initialize QueryResult dengan structured data
        
        Args:
            columns: List column names 
            rows: List of dicts - SETIAP ROW ADALAH DICT
            total_rows: Total number of rows
        """
        self.columns = columns
        self.rows = rows  # List[Dict] - FIXED: not List[List]
        self.total_rows = total_rows
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary untuk API response
        MAINTAINS structured data format
        
        Returns:
            Dict dengan structured data yang benar
        """
        return {
            'columns': self.columns,
            'rows': self.rows,  # ✅ FIXED: Keeps List[Dict] structure
            'total_rows': self.total_rows
        }
    
    def __repr__(self) -> str:
        return f"QueryResult(columns={len(self.columns)}, rows={self.total_rows})"


class QueryExecutor:
    """
    Pure PostgreSQL executor untuk Supabase
    HANYA eksekusi SQL di PostgreSQL, tidak ada SQLite, tidak ada bug mapping
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize dengan Supabase connection string
        TIDAK ADA lagi DatabaseManager dependency
        
        Args:
            connection_string: PostgreSQL connection string untuk Supabase
        """
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
    
    def execute(self, sql: str) -> QueryResult:
        """
        Execute SQL query di Supabase PostgreSQL dengan CORRECT data structure
        
        Args:
            sql: SQL query yang sudah tervalidasi
            
        Returns:
            QueryResult object dengan data yang BENAR
            
        Raises:
            Exception: Jika eksekusi SQL gagal
        """
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:  # ✅ FIXED: Standard cursor, NOT RealDictCursor
                    # Set search_path to hr schema untuk convenience
                    cursor.execute("SET search_path TO hr, public")
                    
                    # Execute the main query
                    cursor.execute(sql)
                    
                    # ✅ CRITICAL FIX: Extract columns from cursor.description ONCE
                    columns = [desc[0] for desc in cursor.description]
                    
                    # ✅ CRITICAL FIX: Get raw tuples from PostgreSQL
                    raw_tuples = cursor.fetchall()
                    
                    # ✅ CRITICAL FIX: Map tuples to dicts ONCE - this is the ONLY transformation point
                    rows_structured = []
                    for raw_tuple in raw_tuples:
                        row_dict = dict(zip(columns, raw_tuple))
                        rows_structured.append(row_dict)
                    
                    # Create QueryResult with CORRECTLY structured data
                    result = QueryResult(
                        columns=columns,
                        rows=rows_structured,  # ✅ Now contains [{"band": "Band 1", "jumlah_karyawan": 120}, ...]
                        total_rows=len(rows_structured)
                    )
                    
                    self.logger.info(f"✅ PostgreSQL query executed: {result.total_rows} rows returned")
                    if rows_structured:
                        self.logger.debug(f"🔍 Sample data: {rows_structured[0]}")
                    
                    return result
                    
        except psycopg2.Error as e:
            self.logger.error(f"❌ PostgreSQL execution failed: {str(e)}")
            self.logger.error(f"SQL: {sql}")
            raise Exception(f"Database query failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"❌ Query execution failed: {str(e)}")
            raise Exception(f"Failed to execute query: {str(e)}")
    
    def execute_with_limit(self, sql: str, max_rows: int = 1000) -> QueryResult:
        """
        Execute query dengan automatic LIMIT untuk performance
        
        Args:
            sql: SQL query
            max_rows: Maximum number of rows to return
            
        Returns:
            QueryResult dengan limited rows
        """
        try:
            sql_upper = sql.upper()
            
            # Add LIMIT if not present
            if 'LIMIT' not in sql_upper:
                # Remove semicolon dan add LIMIT
                if sql.endswith(';'):
                    limited_sql = sql[:-1] + f' LIMIT {max_rows};'
                else:
                    limited_sql = sql + f' LIMIT {max_rows}'
            else:
                limited_sql = sql
            
            # Execute with limit
            result = self.execute(limited_sql)
            
            # Add warning jika results potentially truncated
            if result.total_rows >= max_rows:
                self.logger.warning(f"⚠️ Results limited to {max_rows} rows")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Limited query execution failed: {str(e)}")
            raise
    
    def execute_count_query(self, base_sql: str) -> int:
        """
        Execute count query untuk mendapatkan total rows
        
        Args:
            base_sql: Base SQL query
            
        Returns:
            Total number of rows
        """
        try:
            # Convert to count query
            count_sql = self._convert_to_count_query(base_sql)
            
            # Execute count query
            result = self.execute(count_sql)
            
            if result.rows and len(result.rows) > 0:
                # Get first column of first row (count result)
                first_row = result.rows[0]
                if isinstance(first_row, dict):
                    # Get first value from dict
                    return list(first_row.values())[0]
                else:
                    return first_row[0]
            else:
                return 0
                
        except Exception as e:
            self.logger.error(f"❌ Count query execution failed: {str(e)}")
            return -1  # Indicate count failed
    
    def _convert_to_count_query(self, sql: str) -> str:
        """
        Convert SELECT query to COUNT query
        
        Args:
            sql: Original SELECT query
            
        Returns:
            COUNT version of the query
        """
        try:
            sql_upper = sql.upper().strip()
            
            # Find FROM clause
            from_index = sql_upper.find('FROM')
            if from_index == -1:
                raise ValueError("Cannot convert to count query: no FROM clause found")
            
            # Extract FROM clause and beyond
            from_clause = sql[from_index:]
            
            # Remove ORDER BY dan LIMIT dari count query
            from_clause_upper = from_clause.upper()
            
            # Remove ORDER BY
            order_by_index = from_clause_upper.find('ORDER BY')
            if order_by_index != -1:
                from_clause = from_clause[:order_by_index].strip()
            
            # Remove LIMIT
            limit_index = from_clause_upper.find('LIMIT')
            if limit_index != -1:
                from_clause = from_clause[:limit_index].strip()
            
            # Create count query
            count_sql = f"SELECT COUNT(*) {from_clause}"
            
            # Remove trailing semicolon untuk processing
            if count_sql.endswith(';'):
                count_sql = count_sql[:-1]
            
            return count_sql + ";"
            
        except Exception as e:
            self.logger.error(f"❌ Failed to convert to count query: {str(e)}")
            # Fallback: wrap original query
            return f"SELECT COUNT(*) FROM ({sql}) AS subquery;"
    
    def test_connection(self) -> bool:
        """
        Test Supabase PostgreSQL connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    
                    # Test hr schema access
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'hr'")
                    hr_tables = cursor.fetchone()[0]
                    
                    self.logger.info(f"✅ Supabase connection test passed. HR schema has {hr_tables} tables")
                    return True
                    
        except Exception as e:
            self.logger.error(f"❌ Supabase connection test failed: {str(e)}")
            return False