import logging
from typing import Dict, Any, Optional

from engines.hr.models.hr_response import HRResponse
from engines.hr.intent.hr_intent_analyzer import HRIntentAnalyzer
from engines.hr.query.sql_generator import SQLGenerator
from engines.hr.query.sql_validator import SQLValidator
from engines.hr.query.query_executor import QueryExecutor, QueryResult
from engines.hr.database.schema_reader import SchemaReader
from engines.hr.database.db_manager import DatabaseManager
from engines.hr.analysis.data_first_analyzer import DataFirstAnalyzer
from engines.hr.analysis.data_narrator import ProductionDataNarrator

from openai import OpenAI
from app.config import OPENAI_API_KEY

class HRService:
    """
    🔥 MAIN HR SERVICE
    Menyatukan komponen Database, SQL Engine, dan Analytics Pipeline.
    """
    
    def __init__(self):
        """
        Initialize HR Service tanpa perlu string koneksi manual (ditangani DB Manager)
        """
        try:
            self.logger = logging.getLogger(__name__)
            
            # ✅ FIX: Gunakan DatabaseManager yang elegan untuk mengurus koneksi!
            self.db_manager = DatabaseManager()
            
            self.llm = OpenAI(api_key=OPENAI_API_KEY)
            
            # Initialize components dengan meminjam DatabaseManager
            self.query_executor = QueryExecutor(db_manager=self.db_manager)
            self.schema_reader = SchemaReader(db_manager=self.db_manager)
            
            self.sql_generator = SQLGenerator()  
            self.sql_validator = SQLValidator()
            self.intent_analyzer = HRIntentAnalyzer() 
            
            # INSIGHT LAYER
            self.data_analyzer = DataFirstAnalyzer()
            self.data_narrator = ProductionDataNarrator(use_llm=False)  
            
            # SQL transparency tracking
            self._last_generated_sql = None
            self._last_user_question = None
            
            self.logger.info("✅ HR Service (Orchestrator) initialized successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ HR Service initialization failed: {e}")
            raise

    def process_hr_query(self, question: str, user_role: str, selected_chart: Optional[str] = None, session_id: str = "default") -> HRResponse:
        """
        🔥 MAIN ENTRY POINT
        SQL Result → Insight Generation → Frontend-Ready HRResponse + SQL Transparency
        """
        try:
            # 1. Security check
            if not self._validate_hr_access(user_role):
                return HRResponse(errors=["Access denied. HR role required for this operation."])
            
            # =========================================================================
            # 🧠 2. STANDALONE QUESTION HANDLING (CLEAN ARCHITECTURE)
            # Karena sudah diparafrase oleh Chat Service di pintu depan,
            # variabel 'question' di sini SUDAH berupa pertanyaan utuh & spesifik.
            # =========================================================================
            standalone_question = question
            self.logger.info(f"⚙️ Memproses HR Query: '{standalone_question}'")

            # 3. Execute query flow
            query_result = self._execute_query_flow(standalone_question)
            
            # 4. Check results
            if not query_result or not query_result.rows:
                return HRResponse(errors=[f"No data found for your query: '{standalone_question}'"])
            
            # 5. Production Analytics Pipeline
            try:
                # 5a. Analyze data 
                analysis_response = self.data_analyzer.analyze(query_result.to_dict(), standalone_question)
                
                computed_metrics = {
                    'total_sum': getattr(analysis_response.metrics, 'total_sum', None),
                    'highest_value': getattr(analysis_response.metrics, 'highest_value', None),
                    'lowest_value': getattr(analysis_response.metrics, 'lowest_value', None),
                    'concentration_top_percent': getattr(analysis_response.metrics, 'concentration_top_percent', None),
                    'category_count': getattr(analysis_response.metrics, 'category_count', None)
                }
                
                # 5b. Generate narrative
                narration_result = self.data_narrator.narrate_with_data_guarantee(
                    query_result.to_dict(), computed_metrics, standalone_question
                )
                
                # 5c. Prepare frontend-compatible structures
                analysis_for_frontend = self._prepare_analysis_for_frontend(analysis_response, computed_metrics)
                narrative_for_frontend = self._prepare_narrative_for_frontend(analysis_response, query_result.total_rows)
                
                # 5d. Assemble response
                query_dict = query_result.to_dict()
                
                # ✅ SUNTIKKAN SQL LANGSUNG KE DALAM DICTIONARY
                if self._last_generated_sql:
                    query_dict['sql_query'] = self._last_generated_sql
                    query_dict['sql_explanation'] = self._generate_sql_explanation(
                        self._last_generated_sql, self._last_user_question
                    )
                
                response = HRResponse(
                    data=query_dict,
                    insight=narration_result.raw_data_display + "\n" + narration_result.llm_interpretation,
                    narrative=narrative_for_frontend,
                    analysis=analysis_for_frontend,  
                    recommendations=[]
                )
                return response
                
            except Exception as processing_error:
                self.logger.error(f"Analytics Pipeline failed: {processing_error}")
                # Fallback aman
                fallback = HRResponse(
                    data=query_result.to_dict(),
                    insight=f"DATA:\nQuery returned {query_result.total_rows} rows.\nANALYSIS:\nUnavailable",
                    narrative={'title': 'HR Data Analysis', 'summary': f'{query_result.total_rows} rows found'},
                    analysis={'note': 'Analysis temporarily unavailable'},
                    recommendations=[]
                )
                if self._last_generated_sql:
                    fallback.sql_query = self._last_generated_sql
                    fallback.sql_explanation = "Query untuk mengambil data HR."
                return fallback
            
        except Exception as e:
            self.logger.error(f"❌ HR query processing failed: {e}")
            return HRResponse(errors=[f"Query processing failed: {str(e)}"])
    
    def _prepare_analysis_for_frontend(self, analysis_response, computed_metrics) -> Dict[str, Any]:
        """Prepare analysis data in the format frontend expects"""
        analysis_for_frontend = {}
        
        if analysis_response.metrics.highest_value:
            _, highest_category, highest_value = analysis_response.metrics.highest_value
            conc_percent = analysis_response.metrics.concentration_top_percent or 0
            analysis_for_frontend['highest'] = {
                'category': str(highest_category), 'value': float(highest_value), 'percent': f"{conc_percent:.1f}"
            }
        
        if analysis_response.metrics.lowest_value:
            _, lowest_category, lowest_value = analysis_response.metrics.lowest_value
            lowest_percent = 0.0
            if analysis_response.metrics.total_sum:
                lowest_percent = (float(lowest_value) / float(analysis_response.metrics.total_sum)) * 100
            analysis_for_frontend['lowest'] = {
                'category': str(lowest_category), 'value': float(lowest_value), 'percent': f"{lowest_percent:.1f}"
            }
        
        if analysis_response.metrics.concentration_top_percent:
            analysis_for_frontend['top_concentration_percent'] = f"{analysis_response.metrics.concentration_top_percent:.1f}"
        
        return analysis_for_frontend
    
    def _prepare_narrative_for_frontend(self, analysis_response, total_rows) -> Dict[str, Any]:
        """Prepare narrative data in the format frontend expects"""
        category_count = analysis_response.metrics.category_count or total_rows
        
        if analysis_response.analysis.data_shape == 'distribution':
            title = f'Distribusi Data - {category_count} Kategori'
        elif analysis_response.analysis.data_shape == 'listing':
            title = f'Daftar Data - {category_count} Items'
        else:
            title = f'Analisis Data HR - {category_count} Records'
        
        if analysis_response.metrics.total_sum:
            summary = f'Ditemukan {total_rows} baris dengan total {float(analysis_response.metrics.total_sum):,.0f}'
        else:
            summary = f'Ditemukan {total_rows} baris data siap untuk analisis'
        
        return {'title': title, 'summary': summary}
    
    def _validate_hr_access(self, user_role: str) -> bool:
        """Validate HR access permissions"""
        valid_roles = ['hr', 'admin', 'manager']
        return str(user_role).lower() in valid_roles
    
    def _execute_query_flow(self, question: str) -> Optional[QueryResult]:
        """Orchestrate SQL Generation -> Validation -> Execution"""
        try:
            schema = self.schema_reader.get_schema_text() 
            
            sql = self.sql_generator.generate_sql(question, schema)
            
            self._last_generated_sql = sql
            self._last_user_question = question
            
            if not self.sql_validator.is_valid(sql):
                raise Exception("SQL did not pass security validation.")
            
            # Menggunakan fitur execute_with_limit dari QueryExecutor untuk safety
            query_result = self.query_executor.execute_with_limit(sql, max_rows=1000)
            return query_result
            
        except Exception as e:
            err_msg = str(e)
            if "INVALID_QUERY" in err_msg:
                self.logger.warning(f"⚠️ Query rejected (non-DB/simulasi): {err_msg}")
            else:
                self.logger.error(f"❌ Query execution flow failed: {err_msg}")
            return None
    
    def _generate_sql_explanation(self, sql_query: str, user_question: str) -> str:
        """Memanggil LLM untuk menjelaskan SQL"""
        try:
            if hasattr(self.sql_generator, 'generate_sql_explanation'):
                return self.sql_generator.generate_sql_explanation(sql_query, user_question)
            return "Query berhasil diproses."
        except Exception as e:
            return "Query HR berhasil dijalankan."
        
def create_hr_service() -> HRService:
    """Factory function untuk HRService"""
    return HRService()