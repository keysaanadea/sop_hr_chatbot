"""
HR Service - Supabase PostgreSQL Edition with Integrated Insight Layer
=====================================================================
ENHANCED VERSION that routes through insight generation for narrative responses
"""

import os
import logging
from typing import List, Dict, Any, Optional
import psycopg2

from engines.hr.models import HRResponse
from engines.hr.intent import HRIntentAnalyzer
from engines.hr.query import SQLGenerator, SQLValidator
from engines.hr.analysis.data_first_analyzer import DataFirstAnalyzer
from engines.hr.analysis.data_narrator import ProductionDataNarrator


class QueryResult:
    """QueryResult model untuk menyimpan result query"""
    
    def __init__(self, columns: list, rows: list, total_rows: int):
        self.columns = columns
        self.rows = rows  # List[Dict] - properly structured
        self.total_rows = total_rows
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'columns': self.columns,
            'rows': self.rows,
            'total_rows': self.total_rows
        }


class PostgreSQLQueryExecutor:
    """
    Pure PostgreSQL query executor untuk Supabase
    TIDAK ADA SQLite dependencies, TIDAK ADA double conversion bugs
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
    
    def execute(self, sql: str) -> QueryResult:
        """Execute SQL query pada Supabase PostgreSQL dengan CORRECT data handling"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:  # ✅ FIXED: Standard cursor, no RealDictCursor
                    # Set search_path to hr for convenient querying
                    cursor.execute("SET search_path TO hr, public")
                    
                    # Execute the actual query
                    cursor.execute(sql)
                    
                    # ✅ CRITICAL FIX: Extract columns and map tuples to dicts ONCE
                    columns = [desc[0] for desc in cursor.description]
                    raw_tuples = cursor.fetchall()
                    
                    # ✅ CRITICAL FIX: Map tuples to dicts - this is the FINAL transformation
                    rows_structured = [dict(zip(columns, row)) for row in raw_tuples]
                    
                    result = QueryResult(
                        columns=columns,
                        rows=rows_structured,  # ✅ List[Dict] - properly structured
                        total_rows=len(rows_structured)
                    )
                    
                    self.logger.info(f"Query executed successfully: {result.total_rows} rows returned")
                    if rows_structured:
                        self.logger.debug(f"🔍 Sample: {rows_structured[0]}")
                    
                    return result
                    
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL query failed: {str(e)}")
            self.logger.error(f"SQL: {sql}")
            raise Exception(f"Database query failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise Exception(f"Query execution failed: {str(e)}")


class SchemaReader:
    """
    Pure PostgreSQL schema reader untuk Supabase
    TIDAK ADA file scanning atau SQLite
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
        self._cached_schema = None
    
    def get_schema(self) -> str:
        """Get formatted schema text untuk SQL generation"""
        if self._cached_schema:
            return self._cached_schema
        
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    # Get all tables in hr schema
                    cursor.execute("""
                        SELECT table_name
                        FROM information_schema.tables 
                        WHERE table_schema = 'hr'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    
                    hr_tables = cursor.fetchall()
                    
                    if not hr_tables:
                        self._cached_schema = "No tables found in hr schema"
                        return self._cached_schema
                    
                    # Build schema text for LLM
                    schema_lines = [
                        "=== HR SCHEMA (Supabase PostgreSQL) ===",
                        f"Schema: hr",
                        f"Total Tables: {len(hr_tables)}",
                        ""
                    ]
                    
                    # Get detailed info for each table
                    for table_row in hr_tables:
                        table_name = table_row[0]
                        
                        # Get columns
                        cursor.execute("""
                            SELECT column_name, data_type
                            FROM information_schema.columns 
                            WHERE table_schema = 'hr' 
                            AND table_name = %s
                            ORDER BY ordinal_position
                        """, (table_name,))
                        
                        columns = cursor.fetchall()
                        
                        schema_lines.append(f"TABLE: hr.{table_name}")
                        schema_lines.append(f"Columns ({len(columns)}):")
                        
                        for col in columns:
                            schema_lines.append(f"  • {col[0]}: {col[1]}")
                        
                        schema_lines.append("")
                    
                    schema_lines.extend([
                        "=== SQL GUIDELINES ===",
                        "• Use PostgreSQL syntax",
                        "• Prefix tables: hr.table_name", 
                        "• JOINs between hr tables allowed",
                        "• No cross-schema queries",
                        ""
                    ])
                    
                    self._cached_schema = "\n".join(schema_lines)
                    self.logger.info(f"✅ Schema loaded: {len(hr_tables)} tables")
                    return self._cached_schema
                    
        except psycopg2.Error as e:
            self.logger.error(f"Schema loading failed: {str(e)}")
            self._cached_schema = f"Error loading schema: {str(e)}"
            return self._cached_schema


class HRService:
    """
    Pure Supabase HR analytics service with INTEGRATED INSIGHT LAYER
    Now includes rule-based insight generation for narrative responses
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize HR service dengan Supabase connection and insight generator
        
        Args:
            connection_string: PostgreSQL connection string untuk Supabase
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            # Get Supabase connection
            self.connection_string = connection_string or self._get_supabase_connection()
            
            # Initialize pure PostgreSQL components
            self.schema_reader = SchemaReader(self.connection_string)
            self.query_executor = PostgreSQLQueryExecutor(self.connection_string)
            
            # Initialize other components (unchanged)
            self.intent_analyzer = HRIntentAnalyzer()
            self.sql_generator = SQLGenerator()
            self.sql_validator = SQLValidator()
            
            # 🔥 PRODUCTION REFACTOR: Data-first pipeline
            self.data_analyzer = DataFirstAnalyzer()
            self.data_narrator = ProductionDataNarrator(use_llm=False)  # Start with rule-based
            
            # Test connection
            self._test_connection()
            
            self.logger.info("✅ HR Service initialized with Supabase PostgreSQL + Insight Layer")
            
        except Exception as e:
            self.logger.error(f"HR Service initialization failed: {str(e)}")
            raise
    
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
    
    def _test_connection(self):
        """Test Supabase connection"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'hr'")
                    table_count = cursor.fetchone()[0]
                    self.logger.info(f"✅ Supabase connection verified: {table_count} tables in hr schema")
        except Exception as e:
            self.logger.error(f"❌ Supabase connection test failed: {e}")
            raise ConnectionError(f"Cannot connect to Supabase: {e}")
    
    def process_hr_query(self, question: str, user_role: str, 
                        selected_chart: Optional[str] = None) -> HRResponse:
        """
        🔥 ENHANCED MAIN ENTRY POINT with integrated insight generation
        
        NEW PIPELINE:
        SQL Result → Insight Generation → Enriched HRResponse
        
        Args:
            question: Natural language question dari user
            user_role: Role user (WAJIB dicek PERTAMA)
            selected_chart: Optional chart type (unused for now)
            
        Returns:
            HRResponse object with insights included
        """
        try:
            # STEP 1: Security check
            if not self._validate_hr_access(user_role):
                return HRResponse(
                    errors=["Access denied. HR role required for this operation."]
                )
            
            # STEP 2: Intent analysis
            intent_result = self.intent_analyzer.analyze(question)
            wants_visualization = intent_result.get('wants_visualization', False)
            
            # STEP 3: Execute query flow
            query_result = self._execute_query_flow(question)
            
            # STEP 4: Check results
            if not query_result or not query_result.rows:
                return HRResponse(errors=["No data found for your query."])
            
            # 🔥 PRODUCTION REFACTOR: Guaranteed data preservation pipeline
            try:
                # STEP 1: Analyze data without filtering or hiding rows
                analysis_response = self.data_analyzer.analyze(query_result.to_dict(), question)
                
                # STEP 2: Extract computed metrics (totals, percentages, etc.)
                computed_metrics = {
                    'total_sum': analysis_response.metrics.total_sum,
                    'highest_value': analysis_response.metrics.highest_value,
                    'lowest_value': analysis_response.metrics.lowest_value,
                    'concentration_top_percent': analysis_response.metrics.concentration_top_percent,
                    'category_count': analysis_response.metrics.category_count
                }
                
                # STEP 3: Generate narrative with GUARANTEED data preservation
                narration_result = self.data_narrator.narrate_with_data_guarantee(
                    query_result.to_dict(),
                    computed_metrics,
                    question
                )
                
                self.logger.info(f"✅ Production pipeline: {narration_result.total_rows_confirmed} rows guaranteed displayed")
                
                # STEP 4: Return response with complete data + separated analysis
                return HRResponse(
                    data=query_result.to_dict(),
                    insight=narration_result.raw_data_display + "\n" + narration_result.llm_interpretation,
                    recommendations=[]  # Not needed - all info in insight field
                )
                
            except Exception as processing_error:
                self.logger.error(f"Production pipeline failed: {processing_error}")
                # CRITICAL FALLBACK: Never lose data, even on error
                return HRResponse(
                    data=query_result.to_dict(),
                    insight=f"DATA:\nQuery returned {query_result.total_rows} rows (see raw data above)\n\nANALYSIS:\nProcessing temporarily unavailable",
                    recommendations=[]
                )
            
        except Exception as e:
            self.logger.error(f"HR query processing failed: {str(e)}")
            return HRResponse(errors=[f"Query processing failed: {str(e)}"])
    
    def _validate_hr_access(self, user_role: str) -> bool:
        """Validate HR access permissions"""
        valid_roles = ['HR', 'hr', 'Hr', 'ADMIN', 'admin', 'manager', 'Manager']
        
        if user_role not in valid_roles:
            self.logger.warning(f"Access denied for role: {user_role}")
            return False
        
        self.logger.info(f"HR access granted for role: {user_role}")
        return True
    
    def _execute_query_flow(self, question: str) -> Optional[QueryResult]:
        """
        Execute query flow menggunakan Supabase PostgreSQL
        ✅ UNCHANGED - No re-processing of already-normalized data
        """
        try:
            # 1. Get schema dari PostgreSQL
            schema = self.schema_reader.get_schema()
            self.logger.debug("Schema obtained from PostgreSQL")
            
            # 2. Generate SQL menggunakan schema context
            sql = self.sql_generator.generate_sql(question, schema)
            self.logger.info(f"Generated SQL: {sql[:100]}...")
            
            # 3. Validate SQL
            is_valid = self.sql_validator.is_valid(sql)
            if not is_valid:
                raise Exception("SQL validation failed")
            
            # 4. Execute SQL via PostgreSQL executor
            # ✅ CRITICAL FIX: query_result is already normalized - DON'T touch it
            query_result = self.query_executor.execute(sql)
            self.logger.info(f"Query executed successfully: {query_result.total_rows} rows")
            
            return query_result
            
        except Exception as e:
            self.logger.error(f"Query flow failed: {str(e)}")
            return None


# Factory function untuk create HR service
def create_hr_service(connection_string: str = None) -> HRService:
    """
    Factory function untuk create HRService instance dengan Supabase
    TIDAK ADA lagi parameter db_folder
    
    Args:
        connection_string: Optional Supabase connection string
        
    Returns:
        Configured HRService instance with integrated insight generation
    """
    try:
        service = HRService(connection_string)
        logging.info("✅ HR Service factory: Supabase + Insight Layer initialization successful")
        return service
    except Exception as e:
        logging.error(f"❌ HR Service factory: initialization failed - {str(e)}")
        raise