"""
Query Executor - COMPLETE FIXED VERSION
Menjalankan SQL HANYA di Supabase PostgreSQL dengan data structure yang BENAR
Menggunakan DatabaseManager untuk efisiensi koneksi (Connection Pooling)
"""

import logging
from typing import Dict, Any
from engines.hr.database.db_manager import DatabaseManager
import decimal

class QueryResult:
    """QueryResult model yang menyimpan result query dalam format yang benar"""
    def __init__(self, columns: list, rows: list, total_rows: int):
        self.columns = columns
        self.rows = rows  # List[Dict]
        self.total_rows = total_rows
    
    def to_dict(self) -> Dict[str, Any]:
        return {'columns': self.columns, 'rows': self.rows, 'total_rows': self.total_rows}
    
    def __repr__(self) -> str:
        return f"QueryResult(columns={len(self.columns)}, rows={self.total_rows})"


class QueryExecutor:
    """
    Pure PostgreSQL executor untuk Supabase.
    Memanfaatkan DatabaseManager agar tidak boros koneksi.
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.logger = logging.getLogger(__name__)
        # ✅ FIX: Gunakan DatabaseManager yang sudah ada!
        self.db = db_manager or DatabaseManager()
    
    def execute(self, sql: str) -> QueryResult:
        try:
            result_dict = self.db.execute_query(sql)
            
            # 🌟 FIX DECIMAL KE FLOAT AGAR FRONTEND BISA BACA ANGKA
            clean_rows = []
            for r in result_dict['rows']:
                clean_row = {}
                for k, v in r.items():
                    if isinstance(v, decimal.Decimal):
                        clean_row[k] = float(v)
                    else:
                        clean_row[k] = v
                clean_rows.append(clean_row)
            
            result = QueryResult(
                columns=result_dict['columns'],
                rows=clean_rows, 
                total_rows=result_dict['total_rows']
            )
            return result
                    
        except Exception as e:
            self.logger.error(f"❌ Query execution failed: {e}")
            raise Exception(f"Failed to execute query: {str(e)}")
    
    def execute_with_limit(self, sql: str, max_rows: int = 1000) -> QueryResult:
        try:
            sql_upper = sql.upper()
            if 'LIMIT' not in sql_upper:
                limited_sql = sql[:-1] + f' LIMIT {max_rows};' if sql.endswith(';') else sql + f' LIMIT {max_rows}'
            else:
                limited_sql = sql
            
            result = self.execute(limited_sql)
            if result.total_rows >= max_rows:
                self.logger.warning(f"⚠️ Results limited to {max_rows} rows")
            return result
        except Exception as e:
            self.logger.error(f"❌ Limited query execution failed: {e}")
            raise