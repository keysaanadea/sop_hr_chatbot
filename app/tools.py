"""
DENAI Tools - Universal Structured Response Handler (CANCELLATION PATCHED)
============================================================
🔥 NEW: Cancellation support for search_sop
⚡ FIXED: Async support for HR Database query (Anti-Blocking)
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StructuredResponse:
    """Universal structured response container for Frontend rendering."""
    text_content: str
    data_type: str
    structured_data: Optional[Dict[str, Any]] = None
    visualization_available: bool = False
    metadata: Optional[Dict[str, Any]] = None
    sql_query: Optional[str] = None           
    sql_explanation: Optional[str] = None     

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "text_content": self.text_content,
            "data_type": self.data_type,
            "structured_data": self.structured_data,
            "visualization_available": self.visualization_available
        }
        if self.metadata: result["metadata"] = self.metadata
        if self.sql_query: result["sql_query"] = self.sql_query
        if self.sql_explanation: result["sql_explanation"] = self.sql_explanation
        return result
    
    def has_structured_data(self) -> bool:
        return self.structured_data is not None and len(self.structured_data) > 0

# =====================
# ENGINE INITIALIZATION
# =====================

# 1. SOP RAG Engine
try:
    from engines.sop.rag_engine import answer_question
    logger.info("✅ SOP RAG engine imported successfully")
    USE_SOP_ENGINE = True
except Exception as e:
    logger.error(f"❌ Failed to import SOP RAG engine: {e}")
    USE_SOP_ENGINE = False

# 2. HR Analytics Engine
try:
    from engines.hr import create_hr_service
    hr_service = create_hr_service() 
    USE_HR_ENGINE = True
    logger.info("✅ HR Service initialized with Supabase PostgreSQL via DatabaseManager")
except Exception as e:
    logger.error(f"❌ Failed to import/initialize HR Analytics engine: {e}", exc_info=True)
    USE_HR_ENGINE = False
    hr_service = None


# =====================
# ROUTING & SCHEMAS
# =====================

def get_current_tools_schema(user_role: str, intent: str) -> List[Dict[str, Any]]:
    user_role = (user_role or "employee").lower()
    
    if intent == "A":
        logger.info(f"✅ Intent A (SOP) → Exposing SOP tools for {user_role}")
        return _get_sop_tools()
    elif intent == "B":
        if user_role in ["hr", "admin", "manager"]:
            logger.info(f"✅ Intent B (HR_DATA) → Exposing HR tools for {user_role}")
            return _get_hr_tools()
        else:
            logger.warning(f"🔐 Intent B (HR_DATA) blocked for unauthorized role: {user_role}")
            return []
            
    logger.info(f"📋 Fallback → SOP tools for {user_role}")
    return _get_sop_tools()

def _get_sop_tools() -> List[Dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": "search_sop",
            "description": "Search company SOP documents using RAG engine. Pass-through langsung tanpa modifikasi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "WAJIB isi dengan EXACT RAW INPUT / teks asli dari user. DILARANG merangkum/mengubah."
                    }
                },
                "required": ["question"]
            }
        }
    }]

def _get_hr_tools() -> List[Dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": "query_hr_database",
            "description": "Query employee database for structured HR analytics. Returns data in table format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question about employee database: counts, departments, salary, etc."
                    },
                    "user_role": {
                        "type": "string",
                        "description": "User role for authorization",
                        "enum": ["HR", "hr", "admin", "manager"],
                        "default": "HR"
                    }
                },
                "required": ["question"]
            }
        }
    }]


# =====================
# TOOL IMPLEMENTATIONS
# =====================

async def search_sop(
    question: str, 
    session_id: str = "default",
    cancellation_check: Optional[Callable] = None  # 🔥 NEW parameter
) -> str:
    """
    🔥 ENHANCED: Search SOP with cancellation support
    """
    try:
        logger.info(f"📖 Executing SOP search for: {question[:50]}...")
        if USE_SOP_ENGINE:
            # 🔥 Pass cancellation_check to RAG engine
            result = await answer_question(question, session_id, cancellation_check)
            logger.info(f"✅ SOP search completed ({len(result)} chars)")
            return result
        else:
            logger.error("❌ SOP engine not available")
            return "<h3>❌ Sistem Tidak Tersedia</h3><p>Sistem pencarian SOP sedang dalam pemeliharaan.</p>"
    except Exception as e:
        logger.error(f"❌ SOP search error: {e}", exc_info=True)
        return f"<h3>❌ Error Pencarian SOP</h3><p>Terjadi kesalahan: {str(e)}</p>"


async def query_hr_database(question: str, user_role: str = "HR", session_id: str = "default") -> Union[str, StructuredResponse]:
    """
    ⚡ FIXED: Made Async to prevent blocking the event loop while querying Supabase
    """
    try:
        logger.info(f"📊 Executing HR query: {question[:50]} (role: {user_role})")
        
        if not USE_HR_ENGINE:
            return "❌ **HR Analytics Tidak Tersedia**\n\nSistem tidak tersedia. Hubungi administrator."
        
        # ⚡ Membungkus proses query DB yang blocking ke dalam thread
        response = await asyncio.to_thread(
            hr_service.process_hr_query,
            question=question, 
            user_role=user_role, 
            session_id=session_id
        )
        
        if response.has_errors():
            logger.warning(f"⚠️ HR query failed: {response.errors}")
            return "⚠️ **Data Tidak Tersedia**\n\nInformasi tidak tersedia atau Anda tidak memiliki otorisasi."
        
        if response.has_data():
            query_data = response.data
            columns = query_data.get('columns', [])
            rows = query_data.get('rows', [])
            
            sql_q = query_data.get('sql_query')
            sql_exp = query_data.get('sql_explanation')
            
            result_parts = []
            if columns and rows:
                result_parts.append("# 📊 **COMPLETE QUERY RESULTS**\n")
                result_parts.append("| " + " | ".join(str(col) for col in columns) + " |")
                result_parts.append("|" + "|".join(["---"] * len(columns)) + "|")
                
                for row in rows:
                    formatted_row = [f"{v:,}" if isinstance(v, (int, float)) else str(v) for v in (row.get(col, "") for col in columns)]
                    result_parts.append("| " + " | ".join(formatted_row) + " |")
                
                result_parts.append(f"\n**VERIFICATION: {len(rows)} rows displayed above - COMPLETE DATASET**\n---\n")
            
            if hasattr(response, 'insight') and response.insight:
                result_parts.append(response.insight)
            else:
                result_parts.append(f"# 📋 **ANALYSIS**\n\n✅ Complete dataset displayed above: {len(rows)} total records")
            
            if sql_q:
                result_parts.append("\n---\n### 🧑‍💻 **Transparansi Query (SQL)**")
                result_parts.append(f"Berikut adalah query yang dijalankan oleh sistem untuk mengambil data Anda:\n```sql\n{sql_q}\n```")
                if sql_exp:
                    result_parts.append(f"**Penjelasan Logika:**\n🔸 {sql_exp}")

            viz_available = _can_data_be_visualized(rows, columns)
            if viz_available:
                result_parts.append("\n---\n*📊 This data can be visualized. Use visualization controls to create charts.*")
            
            text_content = "\n".join(result_parts)
            
            structured_payload = {
                "columns": columns, 
                "rows": rows, 
                "total_rows": len(rows), 
                "source": "hr_database"
            }
            if sql_q: structured_payload["sql_query"] = sql_q
            if sql_exp: structured_payload["sql_explanation"] = sql_exp
            
            if columns and rows:
                return StructuredResponse(
                    text_content=text_content,
                    data_type="analytics",
                    structured_data=structured_payload,
                    visualization_available=viz_available,
                    metadata={"query": question, "user_role": user_role, "timestamp": logger.name},
                    sql_query=sql_q,
                    sql_explanation=sql_exp
                )
            return text_content
            
        return "# 📊 **QUERY RESULTS**\n\nQuery berhasil dijalankan tetapi tidak ada data yang ditemukan (0 rows)."
            
    except Exception as e:
        logger.error(f"❌ HR query failed: {e}", exc_info=True)
        return f"❌ **Error Query HR Database**\n\nTerjadi kesalahan: {str(e)}"

def _can_data_be_visualized(rows: List[Dict], columns: List[str]) -> bool:
    return bool(rows and columns and 2 <= len(rows) <= 500 and len(columns) >= 2)


# =====================
# REGISTRY
# =====================

TOOL_FUNCTIONS = {
    "search_sop": search_sop,
    "query_hr_database": query_hr_database,
}

TOOLS_SCHEMA = _get_sop_tools()

__all__ = [
    "search_sop", "query_hr_database", "get_current_tools_schema",
    "TOOL_FUNCTIONS", "StructuredResponse", "TOOLS_SCHEMA"
]