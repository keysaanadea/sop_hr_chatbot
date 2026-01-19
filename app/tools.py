"""
DENAI Tools - NARRATIVE-FIRST HR RESPONSE FORMATTER (Supabase PostgreSQL Only)
===============================================================================

ENHANCED VERSION:
✅ ENHANCED: Narrative-first HR responses with business insights
✅ ENHANCED: Rule-based insight integration from hr_service
✅ MAINTAINED: Universal response formatter based on query result SHAPE
✅ MAINTAINED: No debug metadata in chat responses
✅ MAINTAINED: Clean business answers for all query types
✅ MAINTAINED: Supabase PostgreSQL only initialization
✅ FIXED: No data reconstruction in tools layer - assumes insight generation complete

NEW PIPELINE:
- chat_service.py: LLM classifier + security gate
- hr_service.py: Query execution → insight generation → enriched response
- tools.py: Narrative formatting for insight-enriched responses (NO data reconstruction)
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

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
# HR ANALYTICS ENGINE (SUPABASE-ONLY WITH INSIGHT LAYER!)
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
        print("✅ HR Service initialized with Supabase PostgreSQL + Insight Layer")
    else:
        print("⚠️ Supabase configuration missing - HR engine disabled")
        USE_HR_ENGINE = False
        hr_service = None
    
except ImportError as e:
    print(f"❌ Failed to import HR Analytics engine: {e}")
    USE_HR_ENGINE = False
    hr_service = None

# =====================
# SIMPLIFIED ROUTING (INTENT-BASED FROM CHAT_SERVICE)
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
            logger.debug(f"🔒 Intent B (HR_DATA) blocked for {user_role}")
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
    """Return HR analytics tools only."""
    return [
        {
            "type": "function",
            "function": {
                "name": "query_hr_database",
                "description": "Query employee database for structured HR analytics. For employee counts, departments, salary data, and performance metrics.",
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
# TOOL FUNCTIONS (IMPLEMENTATION)
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

def query_hr_database(question: str, user_role: str = "HR") -> str:
    """
    🔥 PRODUCTION REFACTOR: GUARANTEED data preservation with separated analysis
    
    SYSTEM CONTRACT ENFORCEMENT:
    - ALL query rows MUST be visible in output
    - DATA section ALWAYS comes first  
    - ANALYSIS section clearly separated
    - Raw data NEVER hidden by insight logic
    """
    try:
        logger.info(f"📊 Production HR query: {question[:50]} (role: {user_role})")
        
        if not USE_HR_ENGINE:
            logger.error("❌ HR Analytics engine not available")
            return "❌ **HR Analytics Tidak Tersedia**\n\nSistem HR Analytics tidak tersedia. Hubungi administrator."
        
        # Get response from production pipeline
        response = hr_service.process_hr_query(
            question=question,
            user_role=user_role
        )
        
        # Handle errors
        if response.has_errors():
            logger.warning(f"⚠️ HR query failed: {response.errors}")
            return (
                "⚠️ **Data Tidak Tersedia di Sistem HR**\n\n"
                "Informasi yang Anda minta tidak tersedia dalam database HR saat ini "
                "atau Anda tidak memiliki otorisasi untuk mengaksesnya."
            )
        
        # 🔥 PRODUCTION CONTRACT: ALWAYS show complete data first
        if response.has_data():
            result_parts = []
            
            # MANDATORY: Complete raw data table (ALWAYS FIRST)
            query_data = response.data
            columns = query_data.get('columns', [])
            rows = query_data.get('rows', [])
            
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
            
            # SEPARATED: Analysis/interpretation (references data above)
            if hasattr(response, 'insight') and response.insight:
                # The insight field now contains both DATA and ANALYSIS sections
                # from ProductionDataNarrator, so we just display it
                result_parts.append(response.insight)
            else:
                # Fallback: Ensure user knows data is complete
                result_parts.append("# 📋 **ANALYSIS**")
                result_parts.append("")
                result_parts.append(f"✅ Complete dataset displayed above: {len(rows)} total records")
                result_parts.append("Analysis temporarily unavailable - all data preserved")
            
            logger.info(f"✅ PRODUCTION: {len(rows)} rows guaranteed visible to user")
            return "\n".join(result_parts)
        
        # No data case
        else:
            return (
                "# 📊 **QUERY RESULTS**\n\n"
                "Query berhasil dijalankan tetapi tidak ada data yang ditemukan.\n\n"
                "**VERIFICATION: 0 rows - no matching data**"
            )
            
    except Exception as e:
        logger.error(f"❌ Production HR query failed: {str(e)}")
        return (
            "❌ **Error Query HR Database**\n\n"
            f"Terjadi kesalahan: {str(e)}\n\n"
            "**DATA STATUS: Query failed - no results available**"
        )



# =====================
# TOOL FUNCTIONS REGISTRY
# =====================

TOOL_FUNCTIONS = {
    "search_sop": search_sop,
    "query_hr_database": query_hr_database,
}

# =====================
# LEGACY COMPATIBILITY
# =====================

# Legacy functions for backward compatibility (DEPRECATED)
def get_tools_for_request(user_role: str, message: str) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Use get_current_tools_schema() with intent parameter instead.
    This function is kept for backward compatibility only.
    """
    logger.warning("⚠️ DEPRECATED: get_tools_for_request() called. Use get_current_tools_schema() with intent.")
    # Default to SOP tools for legacy compatibility
    return _get_sop_tools()

def is_hr_data_query(question: str) -> bool:
    """
    DEPRECATED: HR detection now handled by LLM classifier in chat_service.py
    This function is kept for backward compatibility only.
    """
    logger.warning("⚠️ DEPRECATED: is_hr_data_query() called. Use LLM classifier instead.")
    return False

# Static schema for legacy compatibility
TOOLS_SCHEMA = _get_sop_tools()

# =====================
# SYSTEM STATUS
# =====================
print("=" * 70)
print("🎯 DENAI Tools - NARRATIVE-FIRST HR RESPONSES (Supabase PostgreSQL Only)")
print("=" * 70)

# Engine status
if USE_SOP_ENGINE:
    print("📖 SOP RAG Engine: ACTIVE (UNCHANGED)")
else:
    print("❌ SOP RAG Engine: FAILED TO LOAD")

if USE_HR_ENGINE:
    print("📊 HR Analytics Engine: ACTIVE (Supabase PostgreSQL) - NARRATIVE-FIRST WITH INSIGHTS")
else:
    print("❌ HR Analytics Engine: NOT AVAILABLE")

print("🧠 Routing: LLM intent classification (A=SOP, B=HR_DATA)")
print("🔒 Security: Role-based access control in chat_service.py")
print("🎯 Architecture: Supabase PostgreSQL only, no SQLite")
print("🔥 PIPELINE: Query → Insight Generation → Narrative Formatting (NO DATA RECONSTRUCTION)")
print("✨ FEATURES: Business insights, key facts, structured narrative")
print("🛡️ FIXED: Tools layer assumes insight generation complete - no data reconstruction")
print("=" * 70)

# =====================
# EXPORTS
# =====================

__all__ = [
    "search_sop",
    "query_hr_database", 
    "get_current_tools_schema",
    "TOOL_FUNCTIONS",
    # Legacy exports (deprecated)
    "get_tools_for_request",
    "is_hr_data_query",
    "TOOLS_SCHEMA"
]