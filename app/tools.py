"""
CORRECTED DENAI Tools - Universal Structured Response Handler
============================================================
ARCHITECTURE COMPLIANCE:
✅ NO UX orchestration logic  
✅ NO visualization flow control
✅ NO frontend bubble generation
✅ Universal structured response protocol
✅ Backend remains authoritative

UNIVERSAL DESIGN:
✅ Works for ANY tool that returns structured data
✅ No hardcoded tool names or response types
✅ Backward compatible with string responses
✅ Extensible for future data types
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StructuredResponse:
    """
    Universal structured response container
    
    Works for ANY tool that needs to return both:
    1. Human-readable text (for display/LLM)  
    2. Machine-readable data (for frontend rendering)
    
    Examples:
    - HR analytics: text summary + table data
    - Chart data: description + chart config
    - File analysis: summary + structured metadata
    - Any future structured data type
    """
    # Required fields
    text_content: str                              # Human-readable response
    data_type: str                                # Type identifier (analytics, chart, file, etc.)
    
    # Optional structured data
    structured_data: Optional[Dict[str, Any]] = None    # Machine-readable payload
    visualization_available: bool = False               # Can this be visualized?
    metadata: Optional[Dict[str, Any]] = None           # Additional metadata
    sql_query: Optional[str] = None           # ✅ ADD THIS
    sql_explanation: Optional[str] = None     # ✅ ADD THIS
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "text_content": self.text_content,
            "data_type": self.data_type,
            "structured_data": self.structured_data,
            "visualization_available": self.visualization_available
        }
        if self.metadata:
            result["metadata"] = self.metadata
        if self.sql_query:
            result["sql_query"] = self.sql_query
        if self.sql_explanation:
            result["sql_explanation"] = self.sql_explanation
        return result
    
    def has_structured_data(self) -> bool:
        """Check if this response contains structured data"""
        return self.structured_data is not None and len(self.structured_data) > 0

# =====================
# SOP SEARCH ENGINE (COMPLETELY UNCHANGED!)
# =====================
try:
    from engines.sop.rag_engine import answer_question
    print("✅ SOP RAG engine imported successfully")
    USE_SOP_ENGINE = True
except ImportError as e:
    print(f"❌ Failed to import SOP RAG engine: {e}")
    USE_SOP_ENGINE = False
    
    def answer_question(question: str, session_id: str) -> str:
        return f"📋 SOP Search for: '{question}'\n\nSOP engine not available. Please check the import path."

# =====================
# HR ANALYTICS ENGINE (SUPABASE-ONLY, NO VIZ ORCHESTRATION!)
# =====================
try:
    from engines.hr import create_hr_service
    import os
    print("✅ HR Analytics engine imported successfully")
    
    # Initialize HR service dengan Supabase connection (NO db_folder!)
    connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
    if not connection_string:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_password = os.getenv("SUPABASE_DB_PASSWORD")
        if supabase_url and supabase_password:
            project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
            connection_string = f"postgresql://postgres:{supabase_password}@db.{project_id}.supabase.co:5432/postgres"
    
    if connection_string:
        hr_service = create_hr_service(connection_string)
        USE_HR_ENGINE = True
        print("✅ HR Service initialized with Supabase PostgreSQL - CORRECTED ARCHITECTURE")
    else:
        print("⚠️ Supabase configuration missing - HR engine disabled")
        USE_HR_ENGINE = False
        hr_service = None
    
except ImportError as e:
    print(f"❌ Failed to import HR Analytics engine: {e}")
    USE_HR_ENGINE = False
    hr_service = None

# =====================
# CORRECTED ROUTING (INTENT-BASED, NO UX LOGIC)
# =====================

def get_current_tools_schema(user_role: str, intent: str) -> List[Dict[str, Any]]:
    """
    Get tools schema based on intent from LLM classifier.
    
    Args:
        user_role: User role (employee, hr, admin, manager)
        intent: LLM classification result ("A" or "B")
                A = SOP_EXPLANATION
                B = HR_DATA_REQUEST
    
    Returns:
        List of tool schemas to expose to LLM
    """
    user_role = (user_role or "employee").lower()
    
    # Route based on LLM intent classification
    if intent == "A":
        # SOP_EXPLANATION → Always SOP tools
        logger.debug(f"✅ Intent A (SOP) → SOP tools for {user_role}")
        return _get_sop_tools()
    
    elif intent == "B":
        # HR_DATA_REQUEST → HR tools (only for HR roles)
        if user_role in ["hr", "admin", "manager"]:
            logger.debug(f"✅ Intent B (HR_DATA) → HR tools for {user_role}")
            return _get_hr_tools()
        else:
            # Non-HR user requesting HR data → No tools (will be blocked at security gate)
            logger.debug(f"🔐 Intent B (HR_DATA) blocked for {user_role}")
            return []
    
    # Fallback: SOP tools
    logger.debug(f"📋 Fallback → SOP tools for {user_role}")
    return _get_sop_tools()

def _get_sop_tools() -> List[Dict[str, Any]]:
    """Return SOP tools only."""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_sop",
                "description": "Search company SOP documents using RAG engine. Covers procedures, policies, benefits, leave, overtime, travel allowances, country rates, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question about company procedures, policies, benefits, leave, overtime, travel allowances, etc."
                        }
                    },
                    "required": ["question"]
                }
            }
        }
    ]

def _get_hr_tools() -> List[Dict[str, Any]]:
    """Return HR analytics tools only - CORRECTED VERSION."""
    return [
        {
            "type": "function",
            "function": {
                "name": "query_hr_database",
                "description": "Query employee database for structured HR analytics. Returns data in table format with visualization flag.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question about employee database: counts, departments, salary, performance data."
                        },
                        "user_role": {
                            "type": "string",
                            "description": "User role for authorization",
                            "enum": ["HR", "hr"],
                            "default": "HR"
                        }
                    },
                    "required": ["question"]
                }
            }
        }
    ]

# =====================
# CORRECTED TOOL FUNCTIONS (FORMAT + FLAG ONLY)
# =====================

def search_sop(question: str, session_id: str = "default") -> str:
    """
    Search company SOP documents using RAG engine.
    COMPLETELY UNCHANGED - PROTECTED IMPLEMENTATION!
    """
    try:
        logger.info(f"📖 SOP search: {question[:50]}...")
        
        if USE_SOP_ENGINE:
            result = answer_question(question, session_id)
            logger.info(f"✅ SOP search completed ({len(result)} chars)")
            return result
        else:
            logger.error("❌ SOP engine not available")
            return """
<h3>❌ Sistem Tidak Tersedia</h3>
<p>Sistem pencarian SOP sedang dalam pemeliharaan.</p>
<p>Silakan coba lagi dalam beberapa saat atau hubungi administrator.</p>
"""
            
    except Exception as e:
        logger.error(f"❌ SOP search error: {e}")
        return f"""
<h3>❌ Error Pencarian SOP</h3>
<p>Terjadi kesalahan dalam pencarian SOP: {str(e)}</p>
<p>Silakan coba lagi atau hubungi administrator.</p>
"""

def query_hr_database(question: str, user_role: str = "HR") -> Union[str, StructuredResponse]:
    """
    UNIVERSAL: HR database query with structured response
    
    Returns StructuredResponse for any query with tabular data
    Returns string for errors or non-tabular responses
    
    NO hardcoding - works for any HR query type
    """
    try:
        logger.info(f"📊 HR query: {question[:50]} (role: {user_role})")
        
        if not USE_HR_ENGINE:
            logger.error("❌ HR Analytics engine not available")
            return "❌ **HR Analytics Tidak Tersedia**\n\nSistem HR Analytics tidak tersedia. Hubungi administrator."
        
        # Execute HR query (UNCHANGED)
        response = hr_service.process_hr_query(
            question=question,
            user_role=user_role
        )
        
        # Handle errors (UNCHANGED)
        if response.has_errors():
            logger.warning(f"⚠️ HR query failed: {response.errors}")
            return (
                "⚠️ **Data Tidak Tersedia di Sistem HR**\n\n"
                "Informasi yang Anda minta tidak tersedia dalam database HR saat ini "
                "atau Anda tidak memiliki otorisasi untuk mengaksesnya."
            )
        
        # Process successful response with data
        if response.has_data():
            query_data = response.data
            columns = query_data.get('columns', [])
            rows = query_data.get('rows', [])
            
            # Build human-readable text response (UNCHANGED formatting)
            result_parts = []
            
            if columns and rows:
                result_parts.append("# 📊 **COMPLETE QUERY RESULTS**")
                result_parts.append("")
                result_parts.append("| " + " | ".join(str(col) for col in columns) + " |")
                result_parts.append("|" + "|".join([" --- "] * len(columns)) + "|")
                
                # SYSTEM CONTRACT: Show EVERY row without exception
                for row in rows:
                    formatted_row = []
                    for col in columns:
                        value = row.get(col, "")
                        if isinstance(value, (int, float)):
                            formatted_row.append(f"{value:,}")
                        else:
                            formatted_row.append(str(value))
                    result_parts.append("| " + " | ".join(formatted_row) + " |")
                
                result_parts.append("")
                result_parts.append(f"**VERIFICATION: {len(rows)} rows displayed above - COMPLETE DATASET**")
                result_parts.append("")
                result_parts.append("---")
                result_parts.append("")
            
            # Analysis/interpretation (UNCHANGED)
            if hasattr(response, 'insight') and response.insight:
                result_parts.append(response.insight)
            else:
                result_parts.append("# 📋 **ANALYSIS**")
                result_parts.append("")
                result_parts.append(f"✅ Complete dataset displayed above: {len(rows)} total records")
            
            # Universal visualization check
            viz_available = _can_data_be_visualized(rows, columns)
            
            if viz_available:
                result_parts.append("")
                result_parts.append("---")
                result_parts.append("")
                result_parts.append("*📊 This data can be visualized. Use visualization controls to create charts.*")
            
            text_content = "\n".join(result_parts)
            
            # ✅ UNIVERSAL: Return structured response if we have tabular data
            if columns and rows:
                logger.info(f"✅ HR query completed: {len(rows)} rows, returning StructuredResponse")
                sql_query = getattr(response, 'sql_query', None)
                sql_explanation = getattr(response, 'sql_explanation', None)
                
                return StructuredResponse(
                    text_content=text_content,
                    data_type="analytics",
                    structured_data={
                        "columns": columns,
                        "rows": rows,
                        "total_rows": len(rows),
                        "source": "hr_database"
                    },
                    visualization_available=viz_available,
                    metadata={
                        "query": question,
                        "user_role": user_role,
                        "timestamp": logger.name # Simple timestamp
                    },
                    sql_query=sql_query,           # ✅ ADD THIS
                    sql_explanation=sql_explanation # ✅ ADD THIS
                )
            else:
                # No tabular data - return text
                return text_content
        
        # No data case
        else:
            return (
                "# 📊 **QUERY RESULTS**\n\n"
                "Query berhasil dijalankan tetapi tidak ada data yang ditemukan.\n\n"
                "**VERIFICATION: 0 rows - no matching data**"
            )
            
    except Exception as e:
        logger.error(f"❌ HR query failed: {str(e)}")
        return (
            "❌ **Error Query HR Database**\n\n"
            f"Terjadi kesalahan: {str(e)}\n\n"
            "**DATA STATUS: Query failed - no results available**"
        )

def _can_data_be_visualized(rows: List[Dict], columns: List[str]) -> bool:
    """
    SIMPLE visualization availability check
    
    ONLY checks basic criteria:
    - Minimum row count
    - Minimum column count
    - Maximum reasonable size
    
    NO complex heuristics
    NO user tracking
    NO chart type analysis
    """
    if not rows or not columns:
        return False
    
    # Simple rules
    if len(rows) < 2 or len(rows) > 500:
        return False
    
    if len(columns) < 2:
        return False
    
    return True

# =====================
# TOOL FUNCTIONS REGISTRY (UNCHANGED)
# =====================

TOOL_FUNCTIONS = {
    "search_sop": search_sop,
    "query_hr_database": query_hr_database,
}

# =====================
# LEGACY COMPATIBILITY (UNCHANGED)
# =====================

def get_tools_for_request(user_role: str, message: str) -> List[Dict[str, Any]]:
    """DEPRECATED: Use get_current_tools_schema() with intent parameter instead."""
    logger.warning("⚠️ DEPRECATED: get_tools_for_request() called. Use get_current_tools_schema() with intent.")
    return _get_sop_tools()

def is_hr_data_query(question: str) -> bool:
    """DEPRECATED: HR detection now handled by LLM classifier in chat_service.py"""
    logger.warning("⚠️ DEPRECATED: is_hr_data_query() called. Use LLM classifier instead.")
    return False

# Static schema for legacy compatibility
TOOLS_SCHEMA = _get_sop_tools()

# =====================
# CORRECTED SYSTEM STATUS
# =====================
print("=" * 80)
print("🎯 DENAI Tools - CORRECTED ARCHITECTURE (Format + Flag Only)")
print("=" * 80)

# Engine status
if USE_SOP_ENGINE:
    print("📖 SOP RAG Engine: ACTIVE (UNCHANGED)")
else:
    print("❌ SOP RAG Engine: FAILED TO LOAD")

if USE_HR_ENGINE:
    print("📊 HR Analytics Engine: ACTIVE (Supabase PostgreSQL) - DATA + FLAG ONLY")
else:
    print("❌ HR Analytics Engine: NOT AVAILABLE")

print("🧠 Routing: LLM intent classification (A=SOP, B=HR_DATA)")
print("🔐 Security: Role-based access control in chat_service.py")
print("🎯 Architecture: Supabase PostgreSQL only, no SQLite")
print("✅ CORRECTED: No UX orchestration, no visualization flow control")
print("✅ COMPLIANT: Format + flag only, backend authoritative")
print("=" * 80)

# =====================
# EXPORTS (CORRECTED)
# =====================

__all__ = [
    # Core functions
    "search_sop",
    "query_hr_database", 
    "get_current_tools_schema",
    "TOOL_FUNCTIONS",
    
    # Universal response class
    "StructuredResponse",
    
    # Legacy exports (deprecated)
    "get_tools_for_request",
    "is_hr_data_query",
    "TOOLS_SCHEMA"
]

# =====================
# UNIVERSAL EXAMPLES: How ANY tool can return structured data
# =====================

"""
EXAMPLE 1: File Analysis Tool
-----------------------------
def analyze_file(file_path: str) -> Union[str, StructuredResponse]:
    try:
        file_stats = get_file_analysis(file_path)
        
        if file_stats:
            return StructuredResponse(
                text_content=f"File analyzed: {file_stats['size']} bytes",
                data_type="file",
                structured_data={
                    "file_path": file_path,
                    "size": file_stats['size'],
                    "type": file_stats['type']
                },
                visualization_available=False
            )
        else:
            return "File analysis failed"
    except Exception as e:
        return f"Error: {e}"

EXAMPLE 2: Chart Generator Tool  
------------------------------
def generate_chart(data: str) -> Union[str, StructuredResponse]:
    try:
        chart_config = build_chart_config(data)
        
        if chart_config:
            return StructuredResponse(
                text_content="Chart generated with 3 data series",
                data_type="chart",
                structured_data={
                    "config": chart_config,
                    "chart_type": "bar"
                },
                visualization_available=True
            )
        else:
            return "Chart generation failed"
    except Exception as e:
        return f"Error: {e}"

FRONTEND RESPONSES:
------------------
Analytics → {"hr_analytics": {...}, "visualization_available": true}
Charts   → {"chart_data": {...}, "visualization_available": true}  
Files    → {"file_metadata": {...}}
Custom   → {"custom_data": {...}, "data_type": "custom"}
"""