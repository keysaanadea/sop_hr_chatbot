"""
HR Service - Supabase PostgreSQL Edition with Integrated Insight Layer
=====================================================================
ENHANCED VERSION that routes through insight generation for narrative responses
FIXED: Properly sends analysis and narrative data to frontend
🆕 ENHANCED: Added SQL transparency for query inspection
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
                    # Query untuk get table structure dari hr schema
                    schema_query = """
                    SELECT 
                        t.table_name,
                        COALESCE(
                            STRING_AGG(
                                CONCAT(c.column_name, ' (', c.data_type, ')'), 
                                ', ' ORDER BY c.ordinal_position
                            ),
                            'No columns found'
                        ) as columns
                    FROM information_schema.tables t
                    LEFT JOIN information_schema.columns c
                        ON t.table_name = c.table_name 
                        AND t.table_schema = c.table_schema
                    WHERE t.table_schema = 'hr' 
                        AND t.table_type = 'BASE TABLE'
                    GROUP BY t.table_name
                    ORDER BY t.table_name;
                    """
                    
                    cursor.execute(schema_query)
                    schema_result = cursor.fetchall()
                    
                    # Build formatted schema text
                    schema_lines = ["HR Database Schema (Supabase PostgreSQL):"]
                    schema_lines.append("=" * 50)
                    
                    for table_name, columns_info in schema_result:
                        schema_lines.append(f"\nTable: hr.{table_name}")
                        schema_lines.append(f"Columns: {columns_info}")
                    
                    schema_text = "\n".join(schema_lines)
                    self._cached_schema = schema_text
                    
                    self.logger.debug(f"PostgreSQL schema cached: {len(schema_result)} tables")
                    return schema_text
                    
        except Exception as e:
            self.logger.error(f"Failed to read PostgreSQL schema: {str(e)}")
            # Fallback schema
            fallback_schema = """
            HR Database Schema (Supabase PostgreSQL - Fallback):
            ==================================================
            
            Table: hr.employees
            Columns: Basic employee information tables available
            
            Note: Unable to read detailed schema, using fallback structure.
            """
            return fallback_schema


class HRService:
    """
    🔥 MAIN HR SERVICE with Insight Generation Integration
    Enhanced dengan SQL transparency
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize HR Service dengan Supabase PostgreSQL connection + insight layer
        🆕 ENHANCED: Added SQL transparency tracking
        """
        try:
            self.logger = logging.getLogger(__name__)
            
            # Setup database connection
            self.connection_string = connection_string or self._get_supabase_connection()
            
            # Initialize components
            self.query_executor = PostgreSQLQueryExecutor(self.connection_string)
            self.schema_reader = SchemaReader(self.connection_string)
            self.sql_generator = SQLGenerator()  # Uses OpenAI for natural Indonesian
            self.sql_validator = SQLValidator()
            self.intent_analyzer = HRIntentAnalyzer()
            
            # 🔥 INSIGHT LAYER INTEGRATION (PRODUCTION)
            # Initialize both analyzers for comprehensive insights
            self.data_analyzer = DataFirstAnalyzer()
            self.data_narrator = ProductionDataNarrator(use_llm=False)  # Start with rule-based
            
            # 🆕 SQL transparency tracking
            self._last_generated_sql = None
            self._last_user_question = None
            
            # Test connection
            self._test_connection()
            
            self.logger.info("✅ HR Service initialized with Supabase PostgreSQL + Insight Layer + SQL Transparency")
            
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
        🔥 FIXED MAIN ENTRY POINT with proper frontend data structure + SQL transparency
        
        FIXED PIPELINE:
        SQL Result → Insight Generation → Frontend-Ready HRResponse + SQL Transparency
        
        Args:
            question: Natural language question dari user
            user_role: Role user (WAJIB dicek PERTAMA)
            selected_chart: Optional chart type (unused for now)
            
        Returns:
            HRResponse object with frontend-compatible analysis structure + SQL transparency
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
            
            # STEP 3: Execute query flow (WITH SQL TRACKING)
            query_result = self._execute_query_flow(question)
            
            # STEP 4: Check results
            if not query_result or not query_result.rows:
                return HRResponse(errors=["No data found for your query."])
            
            # 🔥 PRODUCTION REFACTOR: Guaranteed data preservation pipeline with FRONTEND COMPATIBILITY
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
                
                # 🔧 FIXED: Prepare FRONTEND-COMPATIBLE analysis data structure
                analysis_for_frontend = self._prepare_analysis_for_frontend(analysis_response, computed_metrics)
                narrative_for_frontend = self._prepare_narrative_for_frontend(analysis_response, query_result.total_rows)
                
                # STEP 4: Return response with complete data + FRONTEND-COMPATIBLE analysis + SQL TRANSPARENCY
                response = HRResponse(
                    data=query_result.to_dict(),
                    insight=narration_result.raw_data_display + "\n" + narration_result.llm_interpretation,
                    narrative=narrative_for_frontend,
                    analysis=analysis_for_frontend,  
                    recommendations=[]
                )

                # 🆕 ADD SQL transparency
                if self._last_generated_sql:
                    response.sql_query = self._last_generated_sql
                    response.sql_explanation = self._generate_sql_explanation(
                        self._last_generated_sql, 
                        self._last_user_question
                    )
                    
                return response
                
            except Exception as processing_error:
                self.logger.error(f"Production pipeline failed: {processing_error}")
                # CRITICAL FALLBACK: Never lose data, even on error
                fallback_response = HRResponse(
                    data=query_result.to_dict(),
                    insight=f"DATA:\nQuery returned {query_result.total_rows} rows (see raw data above)\n\nANALYSIS:\nProcessing temporarily unavailable",
                    narrative={'title': 'HR Data Analysis', 'summary': f'{query_result.total_rows} rows found'},
                    analysis={'note': 'Analysis temporarily unavailable'},
                    recommendations=[]
                )
                
                # Add SQL transparency even on fallback
                if self._last_generated_sql:
                    fallback_response.sql_query = self._last_generated_sql
                    fallback_response.sql_explanation = "Query untuk mengambil data HR dari database perusahaan."
                
                return fallback_response
            
        except Exception as e:
            self.logger.error(f"HR query processing failed: {str(e)}")
            return HRResponse(errors=[f"Query processing failed: {str(e)}"])
    
    def _prepare_analysis_for_frontend(self, analysis_response, computed_metrics) -> Dict[str, Any]:
        """
        🔧 NEW: Prepare analysis data in the exact format frontend expects
        
        Frontend expects:
        - analysis.highest.category, analysis.highest.value, analysis.highest.percent
        - analysis.lowest.category, analysis.lowest.value, analysis.lowest.percent
        - analysis.top_concentration_percent
        """
        analysis_for_frontend = {}
        
        # Prepare highest value data
        if analysis_response.metrics.highest_value:
            highest_row_idx, highest_category, highest_value = analysis_response.metrics.highest_value
            concentration_percent = analysis_response.metrics.concentration_top_percent or 0
            
            analysis_for_frontend['highest'] = {
                'category': str(highest_category),
                'value': float(highest_value),
                'percent': f"{concentration_percent:.1f}"  # Format as string with 1 decimal
            }
        
        # Prepare lowest value data
        if analysis_response.metrics.lowest_value:
            lowest_row_idx, lowest_category, lowest_value = analysis_response.metrics.lowest_value
            
            # Calculate lowest percentage if possible
            lowest_percent = 0.0
            if analysis_response.metrics.total_sum and analysis_response.metrics.total_sum > 0:
                lowest_percent = (float(lowest_value) / float(analysis_response.metrics.total_sum)) * 100
            
            analysis_for_frontend['lowest'] = {
                'category': str(lowest_category),
                'value': float(lowest_value),
                'percent': f"{lowest_percent:.1f}"  # Calculate actual lowest percentage
            }
        
        # Add concentration data
        if analysis_response.metrics.concentration_top_percent:
            analysis_for_frontend['top_concentration_percent'] = f"{analysis_response.metrics.concentration_top_percent:.1f}"
        
        self.logger.debug(f"🔧 Analysis prepared for frontend: {analysis_for_frontend}")
        return analysis_for_frontend
    
    def _prepare_narrative_for_frontend(self, analysis_response, total_rows) -> Dict[str, Any]:
        """
        🔧 NEW: Prepare narrative data in the exact format frontend expects
        
        Frontend expects:
        - narrative.title
        - narrative.summary  
        """
        category_count = analysis_response.metrics.category_count or total_rows
        
        # Create appropriate title based on data
        if analysis_response.analysis.data_shape == 'distribution':
            title = f'Distribusi Data - {category_count} Kategori'
        elif analysis_response.analysis.data_shape == 'listing':
            title = f'Daftar Data - {category_count} Items'
        else:
            title = f'Analisis Data HR - {category_count} Records'
        
        # Create summary with total information
        if analysis_response.metrics.total_sum:
            summary = f'Ditemukan {total_rows} data dengan total {float(analysis_response.metrics.total_sum):,.0f}'
        else:
            summary = f'Ditemukan {total_rows} data siap untuk analisis'
        
        narrative = {
            'title': title,
            'summary': summary
        }
        
        self.logger.debug(f"🔧 Narrative prepared for frontend: {narrative}")
        return narrative
    
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
        🆕 ENHANCED: Now stores SQL query for transparency
        """
        try:
            # 1. Get schema dari PostgreSQL
            schema = self.schema_reader.get_schema()
            self.logger.debug("Schema obtained from PostgreSQL")
            
            # 2. Generate SQL menggunakan schema context
            sql = self.sql_generator.generate_sql(question, schema)
            self.logger.info(f"Generated SQL: {sql[:100]}...")
            
            # 🆕 STORE SQL untuk transparency
            self._last_generated_sql = sql
            self._last_user_question = question
            
            # 3. Validate SQL
            is_valid = self.sql_validator.is_valid(sql)
            if not is_valid:
                raise Exception("SQL validation failed")
            
            # 4. Execute SQL via PostgreSQL executor
            query_result = self.query_executor.execute(sql)
            self.logger.info(f"Query executed successfully: {query_result.total_rows} rows")
            
            return query_result
            
        except Exception as e:
            self.logger.error(f"Query flow failed: {str(e)}")
            return None
    
    def _generate_sql_explanation(self, sql_query: str, user_question: str) -> str:
        """🆕 Generate human-readable explanation of SQL query"""
        try:
            # Simple rule-based explanation untuk common patterns
            sql_upper = sql_query.upper()
            
            if "GROUP BY" in sql_upper and "COUNT(*)" in sql_upper:
                return "Mengelompokkan data berdasarkan kategori dan menghitung jumlah untuk setiap kelompok, lalu menampilkan dalam urutan dari yang terbesar."
            elif "GROUP BY" in sql_upper:
                return "Mengelompokkan data berdasarkan kategori dan menghitung nilai untuk setiap kelompok."
            elif "COUNT(*)" in sql_upper:
                return "Menghitung jumlah total data yang sesuai dengan kriteria yang diminta."
            elif "ORDER BY" in sql_upper:
                return "Mengambil data dari database dan mengurutkan hasilnya sesuai dengan kriteria tertentu."
            elif "SELECT" in sql_upper:
                return "Mengambil data dari database HR perusahaan sesuai dengan pertanyaan yang diajukan."
            else:
                return "Mengeksekusi query untuk mendapatkan informasi HR yang diminta."
                
        except Exception as e:
            self.logger.error(f"Failed to generate SQL explanation: {str(e)}")
            return "Query untuk mengambil data HR dari database perusahaan."


# Factory function untuk create HR service
def create_hr_service(connection_string: str = None) -> HRService:
    """
    Factory function untuk create HRService instance dengan Supabase
    TIDAK ADA lagi parameter db_folder
    
    Args:
        connection_string: Optional Supabase connection string
        
    Returns:
        Configured HRService instance with integrated insight generation + SQL transparency
    """
    try:
        service = HRService(connection_string)
        logging.info("✅ HR Service factory: Supabase + Insight Layer + SQL Transparency initialization successful")
        return service
    except Exception as e:
        logging.error(f"❌ HR Service factory: initialization failed - {str(e)}")
        raise