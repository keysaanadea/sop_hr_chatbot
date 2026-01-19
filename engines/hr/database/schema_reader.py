"""
Schema Reader - Supabase PostgreSQL Only
SATU-SATUNYA sumber schema database untuk seluruh sistem
PURE POSTGRESQL - NO SQLite, NO file scanning, NO multi-db
Fokus pada schema hr di Supabase PostgreSQL
"""

import os
import logging
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor


class SchemaReader:
    """
    OWNER TUNGGAL schema database untuk Supabase PostgreSQL
    Semua logic schema HARUS ada di sini
    PURE POSTGRESQL - tidak ada SQLite legacy code
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize dengan Supabase PostgreSQL connection
        
        Args:
            connection_string: PostgreSQL connection string untuk Supabase
        """
        self.connection_string = connection_string or self._get_supabase_connection()
        self.logger = logging.getLogger(__name__)
        self._cached_schema = None
        
        # Test connection pada initialization
        if not self._test_connection():
            raise ConnectionError("Cannot connect to Supabase PostgreSQL database")
        
        self.logger.info("✅ SchemaReader initialized with Supabase PostgreSQL")
    
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
    
    def _test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            with psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_schema(self, refresh_cache: bool = False) -> Dict[str, Any]:
        """
        Get complete schema dari hr schema - MAIN API untuk HR Service
        
        Args:
            refresh_cache: Force refresh cache
            
        Returns:
            Dict dengan complete schema information untuk LLM context
        """
        if self._cached_schema and not refresh_cache:
            return self._cached_schema
        
        try:
            with psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cursor:
                    # Get all tables in hr schema
                    cursor.execute("""
                        SELECT 
                            table_name,
                            table_type
                        FROM information_schema.tables 
                        WHERE table_schema = 'hr'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    
                    hr_tables = cursor.fetchall()
                    
                    if not hr_tables:
                        self.logger.warning("No tables found in hr schema")
                        return {
                            'total_tables': 0,
                            'schema_name': 'hr',
                            'tables': {},
                            'formatted_schema': "No tables found in hr schema"
                        }
                    
                    self.logger.info(f"🔍 Found {len(hr_tables)} tables in hr schema")
                    
                    # Initialize schema structure
                    schema = {
                        'total_tables': len(hr_tables),
                        'schema_name': 'hr',
                        'connection_type': 'Supabase PostgreSQL',
                        'tables': {}
                    }
                    
                    # Process each table for LLM context
                    for table_info in hr_tables:
                        table_name = table_info['table_name']
                        
                        # Get detailed column information
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
                        
                        columns_info = cursor.fetchall()
                        
                        # Process column information for LLM
                        columns = []
                        column_types = {}
                        
                        for col_info in columns_info:
                            col_name = col_info['column_name']
                            col_type = col_info['data_type']
                            
                            columns.append(col_name)
                            column_types[col_name] = col_type
                        
                        # Store processed table schema
                        schema['tables'][table_name] = {
                            'columns': columns,
                            'column_types': column_types,
                            'total_columns': len(columns)
                        }
                        
                        self.logger.debug(f"📋 Table hr.{table_name}: {len(columns)} columns")
            
            # Generate formatted schema text for LLM
            schema['formatted_schema'] = self._format_schema_for_llm(schema)
            
            # Cache the schema
            self._cached_schema = schema
            
            self.logger.info(f"✅ HR schema loaded: {schema['total_tables']} tables")
            return schema
            
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL error reading schema: {str(e)}")
            raise Exception(f"Schema reading failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to read schema: {str(e)}")
            raise Exception(f"Schema reading failed: {str(e)}")
    
    def get_schema_text(self) -> str:
        """
        Get formatted schema text untuk LLM context
        MAIN API yang dipanggil oleh SQLGenerator
        
        Returns:
            Formatted string representation schema untuk LLM
        """
        try:
            schema = self.get_schema()
            return schema.get('formatted_schema', 'No schema available')
        except Exception as e:
            self.logger.error(f"Failed to get schema text: {str(e)}")
            return f"Error loading schema: {str(e)}"
    
    def get_tables(self) -> List[str]:
        """
        Get list of all tables dalam hr schema
        
        Returns:
            List of table names (tanpa schema prefix)
        """
        try:
            schema = self.get_schema()
            return list(schema['tables'].keys())
        except Exception as e:
            self.logger.error(f"Failed to get tables: {str(e)}")
            return []
    
    def get_columns(self, table_name: str) -> List[str]:
        """
        Get columns untuk specific table
        
        Args:
            table_name: Name of table (tanpa schema prefix)
            
        Returns:
            List of column names
        """
        try:
            schema = self.get_schema()
            if table_name in schema['tables']:
                return schema['tables'][table_name]['columns']
            else:
                self.logger.warning(f"Table hr.{table_name} not found")
                return []
        except Exception as e:
            self.logger.error(f"Failed to get columns for {table_name}: {str(e)}")
            return []
    
    def _format_schema_for_llm(self, schema: Dict[str, Any]) -> str:
        """
        Format schema untuk LLM consumption
        Clean, readable format untuk SQL generation
        
        Returns:
            String representation yang LLM-friendly
        """
        try:
            formatted_lines = [
                "=== HR SCHEMA (Supabase PostgreSQL) ===",
                f"Schema: hr",
                f"Total Tables: {schema['total_tables']}",
                "",
                "📋 AVAILABLE TABLES:",
                ""
            ]
            
            # Format each table untuk LLM context
            for table_name, table_info in schema['tables'].items():
                formatted_lines.append(f"TABLE: hr.{table_name}")
                formatted_lines.append(f"Columns ({table_info['total_columns']}):")
                
                # Format columns dengan types
                for col_name in table_info['columns']:
                    col_type = table_info['column_types'][col_name]
                    formatted_lines.append(f"  • {col_name}: {col_type}")
                
                formatted_lines.append("")  # Empty line between tables
            
            formatted_lines.extend([
                "=== SQL GENERATION GUIDELINES ===",
                "• Use schema prefix: hr.table_name",
                "• PostgreSQL syntax only",
                "• JOINs between hr tables are allowed",
                "• No cross-schema queries",
                "• Use proper PostgreSQL data types",
                ""
            ])
            
            return "\n".join(formatted_lines)
            
        except Exception as e:
            self.logger.error(f"Failed to format schema for LLM: {str(e)}")
            return f"Error formatting schema: {str(e)}"
    
    def refresh_cache(self):
        """Force refresh schema cache"""
        self._cached_schema = None
        self.get_schema()
        self.logger.info("✅ Schema cache refreshed")
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about specific table
        
        Args:
            table_name: Name of table (tanpa schema prefix)
            
        Returns:
            Dict dengan detailed table information
        """
        try:
            schema = self.get_schema()
            
            if table_name not in schema['tables']:
                raise ValueError(f"Table 'hr.{table_name}' not found")
            
            table_info = schema['tables'][table_name].copy()
            table_info['full_table_name'] = f"hr.{table_name}"
            table_info['table_name'] = table_name
            table_info['schema'] = 'hr'
            
            return table_info
            
        except Exception as e:
            self.logger.error(f"Failed to get table info for {table_name}: {str(e)}")
            raise