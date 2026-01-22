"""
DENAI Chat Service - FINAL FIX for Analytics API Response
========================================================

✅ FIXED: Analytics result now includes ALL required fields in API response
✅ FIXED: message_type field included for frontend detection
✅ FIXED: Multiple field names for maximum compatibility
"""

print("🔥🔥🔥 USING FINAL FIXED CHAT_SERVICE.PY 🔥🔥🔥")


import logging
import asyncio
import json
import time
from typing import Optional, List, Dict, Any, Literal, Union
from openai import OpenAI
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    API_TIMEOUT_DEFAULT,
    API_TIMEOUT_CALL_MODE,
    CALL_MODE_TEMPERATURE,
    CHAT_MODE_TEMPERATURE,
    CALL_MODE_MAX_TOKENS,
    CHAT_MODE_MAX_TOKENS
)

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Import dynamic tools routing (REQUIRED for proper routing)
try:
    from app.tools import (
        get_current_tools_schema,  # ✅ DYNAMIC routing
        TOOL_FUNCTIONS,            # Function registry
        StructuredResponse,        # ✅ FIX: Import StructuredResponse class
    )
    TOOLS_AVAILABLE = True
    logger.info("✅ Dynamic tools system imported successfully")
except ImportError as e:
    TOOLS_AVAILABLE = False
    logger.warning(f"⚠️ Tools not available: {e}")
    
    # Fallback functions
    def get_current_tools_schema(user_role="employee", intent="A"):
        return []
    
    TOOL_FUNCTIONS = {}
    
    # ✅ FIX: Fallback StructuredResponse class
    class StructuredResponse:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


# =====================================
# UNIVERSAL ANALYTICS RESPONSE BUILDER
# =====================================

def build_analytics_response(
    *,
    domain: str,
    text: str,
    columns: List[str],
    rows: List[List[Any]],
    session_id: str,
    turn_id: Optional[str] = None,
    visualization_available: bool = True,
    chart_hints: Optional[Dict[str, Any]] = None,
    sql_query: Optional[str] = None,
    sql_explanation: Optional[str] = None
) -> Dict[str, Any]:
    """Universal analytics response builder for ALL domains."""
    
    logger.error(f"🏗️ BUILDING ANALYTICS RESPONSE - Domain: {domain}, Viz: {visualization_available}")
    logger.error(f"🏗️ Columns: {columns}")
    logger.error(f"🏗️ Rows count: {len(rows) if rows else 0}")
    
    # Auto-generate turn_id if not provided
    if turn_id is None:
        turn_id = f"{session_id}-{int(time.time())}"
    
    response = {
        "message_type": "analytics_result",
        "domain": domain,
        "text": text,
        "data": {
            "columns": columns,
            "rows": rows
        },
        "visualization_available": visualization_available,
        "conversation_id": session_id,
        "turn_id": turn_id
    }
    if sql_query:
        response["sql_query"] = sql_query
    if sql_explanation:
        response["sql_explanation"] = sql_explanation
    
    # Add chart hints if provided (future-proof)
    if chart_hints:
        response["chart_hints"] = chart_hints
    if sql_query:
        response["sql_query"] = sql_query
        logger.info("✅ SQL query included in response for transparency")
    
    if sql_explanation:
        response["sql_explanation"] = sql_explanation
        logger.info("✅ SQL explanation included in response")
            
    logger.error(f"🏗️ FINAL ANALYTICS RESPONSE: {json.dumps(response, ensure_ascii=False, default=str)[:300]}...")
        
    return response


def generate_chart_hints(domain: str, columns: List[str], rows: List[List[Any]]) -> Optional[Dict[str, Any]]:
    """Generate smart chart recommendations based on data characteristics."""
    if not columns or not rows or len(columns) < 2:
        return None
    
    hints = {}
    
    # Domain-specific chart recommendations
    if domain == "hr":
        if any("band" in col.lower() for col in columns):
            hints = {
                "preferred_types": ["bar", "pie"],
                "x_axis": columns[0],
                "y_axis": columns[1] if len(columns) > 1 else None,
                "title_suggestion": f"Distribusi {columns[1]} per {columns[0]}"
            }
    
    return hints if hints else None

def generate_sql_explanation(sql_query: str, user_question: str) -> str:
    """Generate human-readable explanation of SQL query using LLM"""
    try:
        explanation_prompt = f"""Jelaskan query SQL berikut dalam bahasa sederhana:

PERTANYAAN: "{user_question}"
SQL: {sql_query}

Berikan penjelasan 2-3 kalimat yang mudah dipahami."""

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Kamu ahli database yang menjelaskan SQL dengan sederhana."},
                {"role": "user", "content": explanation_prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"❌ Failed to generate SQL explanation: {str(e)}")
        return f"Mengambil data dari database perusahaan."

def classify_intent_llm(question: str) -> Literal["A", "B"]:
    """Enhanced LLM-based intent classifier for SOP vs HR DATA routing."""
    try:
        # Enhanced prompt for better classification accuracy
        prompt = f"""You are an intent classifier for an internal company assistant.
Your task is to classify user queries into EXACTLY ONE category based on data source requirements.

=== CLASSIFICATION CATEGORIES ===

A. SOP_EXPLANATION
   → Information available in Standard Operating Procedures (SOP) documents
   → Fixed rules, policies, procedures, definitions, rates, and tables
   → Static company information that doesn't change frequently
   
   INCLUDES:
   • Policy explanations ("aturan cuti karyawan", "prosedur resign")
   • Procedure steps ("cara mengajukan lembur", "proses klaim medical")
   • Definition queries ("apa itu tunjangan keluarga", "pengertian band salary")
   • Fixed rates/amounts ("upah lembur per jam", "tunjangan makan per hari")
   • Entitlement tables ("cuti tahunan berdasarkan masa kerja", "medical limit per band")
   • Travel allowances ("uang perjalanan dinas ke luar negeri per band")
   • Company benefits ("fasilitas karyawan", "program training")

B. HR_DATA_REQUEST  
   → Information requiring queries to employee database
   → Dynamic data about actual employees, counts, statistics
   → Real-time or current employee information
   
   INCLUDES:
   • Employee counts/totals ("berapa jumlah karyawan", "total staff IT")
   • Individual employee data ("gaji si Andi", "cuti tersisa Budi")
   • Department statistics ("distribusi karyawan per divisi")
   • Performance data ("ranking karyawan terbaik")
   • Attendance records ("absensi bulan ini", "siapa yang lembur")
   • Current status checks ("apakah Sari masih bekerja di sini")
   • Analytics/aggregations ("rata-rata gaji per band", "trend recruitment")

=== DECISION FRAMEWORK ===

ASK YOURSELF:
1. Does this ask for a FIXED RULE/RATE that's the same for everyone in the same category? → A
2. Does this ask for SPECIFIC EMPLOYEE DATA or COUNTS of actual people? → B
3. Would the answer come from a POLICY DOCUMENT or from a DATABASE QUERY? → Document=A, Database=B

KEYWORD HINTS:
• "aturan", "prosedur", "cara", "apa itu" → Usually A
• "berapa banyak", "siapa saja", "daftar", "jumlah", "total" → Usually B
• "jika saya", "untuk band X", "limit" → Usually A
• Names of people ("Andi", "Budi") → Usually B

=== RULES ===
- Focus on DATA SOURCE needed, not keywords
- If answer exists in company manuals/policies → A
- If answer requires querying employee records → B
- When uncertain → choose A
- Output ONLY one letter: A or B

User query: "{question}"
"""

        # LLM call with exact specifications
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,  # Deterministic classification
            max_tokens=1,   # Only need one letter
        )
        
        result = response.choices[0].message.content.strip().upper()
        
        # Strict validation - only A or B allowed
        if result in ["A", "B"]:
            logger.info(f"🎯 LLM Intent: '{question[:50]}...' → {result}")
            return result
        else:
            # Fallback to A if invalid response
            logger.warning(f"⚠️ Invalid LLM response '{result}', defaulting to A")
            return "A"
            
    except Exception as e:
        # Fallback to A on any error
        logger.error(f"❌ LLM classification error: {e}, defaulting to A")
        return "A"


class ChatService:
    """Core AI chat orchestration service with universal analytics support"""
    
    def __init__(self):
        self.client = client
        self.model = LLM_MODEL
        self.default_temperature = LLM_TEMPERATURE
        self.tools_available = TOOLS_AVAILABLE
    
    async def process_question(
        self,
        question: str,
        user_role: str,
        session_id: str,
        history: List[Dict[str, Any]] = None,
        mode: str = "chat"
    ) -> Dict[str, Any]:
        """Process user question with LLM intent classification and universal analytics"""
        try:
            # 1. LLM INTENT CLASSIFICATION (DUAL-STAGE CLASSIFIER)
            intent = classify_intent_llm(question)
            
            # 2. HARD SECURITY GATE (role-based)
            if intent == "B" and user_role.lower() not in ['hr', 'admin', 'manager']:
                # HR DATA request from non-HR user = ACCESS DENIED
                logger.warning(f"🔒 HR DATA ACCESS DENIED: role={user_role}, intent={intent}")
                return {
                    "answer": f"""
🔒 <strong>Akses Dibatasi</strong>

Permintaan data karyawan hanya dapat diakses oleh:
• Tim HR
• Admin
• Manager

Role Anda saat ini: <strong>{user_role}</strong>

Untuk pertanyaan tentang prosedur dan kebijakan perusahaan, silakan ajukan pertanyaan yang berbeda.
""",
                    "authorized": False,
                    "tool_called": "security_gate",
                    "intent": intent,
                    "user_role": user_role
                }
            
            # 3. GET TOOLS FOR INTENT
            if self.tools_available:
                tools = get_current_tools_schema(user_role, intent)
                logger.debug(f"🔧 Available tools for intent {intent}: {[t['function']['name'] for t in tools]}")
            else:
                tools = []
                logger.warning("⚠️ Tools not available - using LLM-only mode")
            
            # 4. LLM COMPLETION WITH TOOLS
            messages = self._prepare_messages(question, history, mode)
            
            completion = await self._run_completion(
                messages=messages,
                tools=tools,
                intent=intent,
                mode=mode
            )
            
            # 5. PROCESS RESPONSE
            if completion.choices[0].message.tool_calls:
                # Tool execution path
                tool_call = completion.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                
                logger.info(f"🔧 Executing tool: {function_name}")
                
                result = await self._execute_tool(
                    tool_call, 
                    session_id, 
                    user_role, 
                    question,
                    mode
                )
                logger.error(f"🔧 PROCESS DEBUG: result type={type(result)}, has data={result.get('data') if isinstance(result, dict) else False}")
                logger.error(f"🔧 PROCESS DEBUG: result keys={list(result.keys()) if isinstance(result, dict) else 'Not dict'}")
                
                # ✅ CRITICAL FIX: Handle analytics responses from ANY domain
                if isinstance(result, dict) and result.get("data"):

                    # Universal analytics response - works for HR, Finance, Sales, etc.
                    logger.info(f"✅ Returning universal analytics response: {result.get('domain')} domain")
                    
                    # 🔧 CRITICAL FIX: Include ALL required fields for frontend contract
                    api_response = {
                        "answer": result.get("text", "Analytics result completed"),
                        "authorized": True,
                        "tool_called": function_name,
                        # ✅ CRITICAL: Include message_type for frontend detection
                        "message_type": "analytics_result",
                        # Frontend contract fields - ALL variants for maximum compatibility
                        "data": result["data"],              # Universal field (NEW)
                        "analytics_data": result["data"],   # Alternative field name
                        "hr_analytics": result["data"],     # Backward compatibility
                        "visualization_available": result["visualization_available"],
                        "conversation_id": result["conversation_id"],
                        "turn_id": result["turn_id"],
                        # Additional metadata
                        "domain": result["domain"],
                        "chart_hints": result.get("chart_hints"),
                        "intent": intent
                    }
                    
                    logger.info(f"🎉 FIXED API RESPONSE with all required fields")
                    return api_response
                
                elif isinstance(result, dict) and result.get("type") == "structured_response":
                    # Other structured responses (legacy format)
                    return {
                        "answer": result["answer"],
                        "authorized": True,
                        "tool_called": function_name,
                        "data_type": result["data_type"],
                        "structured_data": result["structured_data"],
                        "visualization_available": result.get("visualization_available", False),
                        "metadata": result.get("metadata"),
                        "intent": intent
                    }
                
                else:
                    # Simple string response (SOP, errors, etc.)
                    return {
                        "answer": str(result),
                        "authorized": True,
                        "tool_called": function_name,
                        "intent": intent
                    }
                    
            else:
                # Direct LLM response (no tools)
                final_answer = completion.choices[0].message.content
                
                return {
                    "answer": final_answer,
                    "authorized": True,
                    "tool_called": None,
                    "intent": intent
                }
                
        except Exception as e:
            logger.error(f"❌ Chat processing error: {e}")
            return {
                "error": f"Maaf, terjadi gangguan sistem: {str(e)}",
                "authorized": True,
                "tool_called": None
            }
    
    async def _run_completion(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None,
        intent: str = "A",
        mode: str = "chat"
    ):
        """Execute LLM completion with appropriate parameters"""
        try:
            # Dynamic parameters based on mode
            if mode == "call":
                temperature = CALL_MODE_TEMPERATURE
                max_tokens = CALL_MODE_MAX_TOKENS
                timeout = API_TIMEOUT_CALL_MODE
            else:
                temperature = CHAT_MODE_TEMPERATURE
                max_tokens = CHAT_MODE_MAX_TOKENS
                timeout = API_TIMEOUT_DEFAULT
            
            # Enhanced tool choice logic
            tool_choice = "auto"
            if tools:
                has_sop_tool = any(t['function']['name'] == 'search_sop' for t in tools)
                has_hr_tool = any(t['function']['name'] == 'query_hr_database' for t in tools)
                
                if has_sop_tool and not has_hr_tool:
                    # ✅ FORCE SOP tool - prevent LLM from answering directly
                    tool_choice = {
                        "type": "function", 
                        "function": {"name": "search_sop"}
                    }
                    logger.debug("🔥 FORCING SOP tool to prevent RAG bypass")
                elif has_hr_tool:
                    # HR tool - let LLM choose (auto)
                    tool_choice = "auto"
                    logger.debug("📊 HR tool available - using auto choice")
                else:
                    tool_choice = "auto"
            
            logger.debug(f"LLM completion: mode={mode}, tokens={max_tokens}, tools={len(tools) if tools else 0}, choice={tool_choice}")
            
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    tools=tools if tools else None,
                    tool_choice=tool_choice,
                    temperature=temperature,
                    max_tokens=max_tokens
                ),
                timeout=timeout
            )
            
        except asyncio.TimeoutError:
            logger.error(f"LLM timeout after {timeout}s")
            raise Exception("Request timeout")
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise
    
    async def _execute_tool(
        self,
        tool_call: Any,
        session_id: str,
        user_role: str,
        original_question: str,
        mode: str = "chat"
    ) -> Union[str, Dict[str, Any]]:
        """Execute tool function - UNIVERSAL structured response handler"""
        if not self.tools_available:
            return "Maaf, tools tidak tersedia."
        
        function_name = tool_call.function.name
        
        try:
            function_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid tool arguments: {e}")
            return "Maaf, terjadi kesalahan parsing argumen."
        
        # Check if function exists
        if function_name not in TOOL_FUNCTIONS:
            logger.error(f"Unknown function: {function_name}")
            return "Maaf, fungsi tidak tersedia."
        
        try:
            tool_function = TOOL_FUNCTIONS[function_name]
            
            # Add session_id for SOP search (compatibility)
            if function_name == "search_sop":
                function_args["session_id"] = session_id
            
            # EXECUTE TOOL - all business logic in engines/
            tool_result = tool_function(**function_args)
            
            # 🐛 DEBUG: Critical debugging to trace the issue
            logger.info(f"🔍 CRITICAL DEBUG - Tool result type: {type(tool_result)}")
            logger.info(f"🔍 CRITICAL DEBUG - Tool result value: {str(tool_result)[:200]}...")
            
            if hasattr(tool_result, 'data_type'):
                logger.info(f"🔍 CRITICAL DEBUG - Data type: {tool_result.data_type}")
            
            if hasattr(tool_result, 'structured_data'):
                logger.info(f"🔍 CRITICAL DEBUG - Structured data: {tool_result.structured_data}")
            
            # ✅ UNIVERSAL ANALYTICS RESPONSE HANDLING
            if isinstance(tool_result, StructuredResponse):
                logger.info(f"✅ FOUND StructuredResponse from {function_name}: {tool_result.data_type}")
                
                # For call mode, use shorter text
                if mode == "call" and hasattr(tool_result, 'text_content') and len(tool_result.text_content) > 150:
                    tool_result.text_content = tool_result.text_content[:130] + "... Butuh detail lengkap?"
                
                # ✅ UNIVERSAL: Convert ANY analytics to canonical format
                if tool_result.data_type == "analytics":
                    logger.error("🔥🔥🔥 ANALYTICS RESPONSE PATH TAKEN 🔥🔥🔥")
                    logger.info(f"🎯 CONVERTING ANALYTICS to universal format")
                    
                    # Extract data from structured response
                    structured_data = tool_result.structured_data or {}
                    columns = structured_data.get("columns", [])
                    rows = structured_data.get("rows", [])
                    
                    logger.info(f"🔍 Analytics data - Columns: {columns}, Rows count: {len(rows) if rows else 0}")
                    logger.error(f"🔧 DEBUG: columns exists: {bool(columns)}, rows exists: {bool(rows)}")
                    logger.error(f"🔧 DEBUG: columns content: {columns}")
                    logger.error(f"🔧 DEBUG: rows sample: {rows[:2] if rows else 'None'}")
                    
                    # 🔧 FORCE ANALYTICS FOR HR QUERIES - NO FALLBACK ALLOWED
                    if function_name == "query_hr_database":
                        logger.error("📊 FORCING ANALYTICS RESPONSE FOR HR QUERY - NO FALLBACK")
                        
                        # Extract data from structured response
                        structured_data = tool_result.structured_data or {}
                        columns = structured_data.get("columns", [])
                        rows = structured_data.get("rows", [])
                        
                        logger.error(f"🔧 HR DEBUG: Original columns={columns}")
                        logger.error(f"🔧 HR DEBUG: Original rows_count={len(rows) if rows else 0}")
                        
                        # Clean and fix data issues
                        if not columns or not rows:
                            logger.error("🔧 HR DEBUG: Missing data - using fallback structure")
                            columns = ["metric", "value"]
                            rows = [["Total Employees", "Data being processed"]]
                        else:
                            # Clean up "Undefined" columns
                            if "Undefined" in columns:
                                logger.error("🔧 HR DEBUG: Found 'Undefined' column - cleaning")
                                # Replace "Undefined" with meaningful names
                                clean_columns = []
                                for col in columns:
                                    if col == "Undefined":
                                        clean_columns.append("category")
                                    else:
                                        clean_columns.append(col)
                                columns = clean_columns
                        
                        # Extract meaningful text summary
                        text_content = getattr(tool_result, 'text_content', 'HR Analytics Result')
                        brief_text = self._extract_brief_summary(text_content)
                        
                        if not brief_text or brief_text == "Analisis data berhasil":
                            brief_text = f"Analisis distribusi karyawan: {len(rows)} kategori data"
                            
                        logger.error(f"🔍 HR DEBUGGING: tool_result type = {type(tool_result)}")
                        logger.error(f"🔍 HR DEBUGGING: tool_result dir = {[attr for attr in dir(tool_result) if not attr.startswith('_')]}")
                        logger.error(f"🔍 HR DEBUGGING: hasattr sql_query = {hasattr(tool_result, 'sql_query')}")
                        logger.error(f"🔍 HR DEBUGGING: hasattr sql_explanation = {hasattr(tool_result, 'sql_explanation')}")
                        
                        
                        # ✅ CRITICAL FIX: Extract SQL fields from tool_result
                        sql_query = getattr(tool_result, 'sql_query', None)
                        sql_explanation = getattr(tool_result, 'sql_explanation', None)
                        
                        logger.error(f"🔍 HR DEBUGGING: sql_query value = {repr(sql_query)}")
                        logger.error(f"🔍 HR DEBUGGING: sql_explanation value = {repr(sql_explanation)}")
                        # Use the CORRECT build_analytics_response function
                        result = build_analytics_response(
                            domain="hr",
                            text=brief_text,
                            columns=columns,
                            rows=rows,
                            session_id=session_id,
                            visualization_available=True,
                            chart_hints=None,
                            sql_query=sql_query,
                            sql_explanation=sql_explanation
                        )
                        
                        # Add answer field for compatibility
                        result["answer"] = brief_text
                        
                        logger.error(f"🎉 FORCED HR ANALYTICS RESULT: message_type={result['message_type']}")
                        logger.error(f"🎉 Data structure: columns={len(columns)}, rows={len(rows)}")
                        return result
                    
                    if columns and rows:
                        # Determine domain from function name
                        domain_map = {
                            "query_hr_database": "hr",
                            "finance_analysis": "finance", 
                            "sales_report": "sales",
                            "operations_query": "operations"
                        }
                        domain = domain_map.get(function_name, "general")
                        
                        # Extract brief summary (no markdown tables)
                        brief_text = self._extract_brief_summary(getattr(tool_result, 'text_content', ''))
                        
                        # Check if visualization makes sense for this data
                        viz_available = (
                            tool_result.visualization_available and 
                            len(rows) >= 2 and 
                            len(columns) >= 2 and
                            len(rows) <= 500  # Reasonable size limit
                        )
                        
                        # Generate chart hints (future-proof)
                        chart_hints = generate_chart_hints(domain, columns, rows) if viz_available else None
                        # 🔍 DEBUG: Check tool_result attributes
                        logger.error(f"🔍 DEBUGGING: tool_result type = {type(tool_result)}")
                        logger.error(f"🔍 DEBUGGING: tool_result attributes = {[attr for attr in dir(tool_result) if not attr.startswith('_')]}")
                        logger.error(f"🔍 DEBUGGING: hasattr sql_query = {hasattr(tool_result, 'sql_query')}")

                        if hasattr(tool_result, 'sql_query'):
                            logger.error(f"🔍 DEBUGGING: sql_query value = {getattr(tool_result, 'sql_query')}")
                        else:
                            logger.error(f"🔍 DEBUGGING: sql_query NOT FOUND in tool_result")

                        if hasattr(tool_result, 'sql_explanation'):  
                            logger.error(f"🔍 DEBUGGING: sql_explanation value = {getattr(tool_result, 'sql_explanation')}")
                        else:
                            logger.error(f"🔍 DEBUGGING: sql_explanation NOT FOUND in tool_result")
                        sql_query = getattr(tool_result, 'sql_query', None)
                        sql_explanation = getattr(tool_result, 'sql_explanation', None)
                        # Return universal analytics format
                        logger.info(f"🔧 SUCCESSFULLY converting to universal analytics format: {domain} domain, {len(rows)} rows")
                        
                        result = build_analytics_response(
                            domain=domain,
                            text=brief_text,
                            columns=columns,
                            rows=rows,
                            session_id=session_id,
                            visualization_available=viz_available,
                            chart_hints=chart_hints,
                            sql_query=sql_query,  # ✅ FIXED: Pass SQL query
                            sql_explanation=sql_explanation  # ✅ FIXED: Pass SQL explanation
                        )
                
                        
                        logger.info(f"🎉 ANALYTICS RESULT: {result}")
                        return result
                
                # Return original structured response for other types
                logger.error("❌❌❌ FALLBACK TEXT RESPONSE PATH TAKEN ❌❌❌")
                logger.info(f"📦 Returning legacy structured response format")
                return {
                    "type": "structured_response",
                    "data_type": tool_result.data_type,
                    "answer": getattr(tool_result, 'text_content', ''),
                    "structured_data": tool_result.structured_data,
                    "visualization_available": tool_result.visualization_available,
                    "metadata": getattr(tool_result, 'metadata', None)
                }
            
            # Handle legacy string responses (SOP, errors, etc.)
            elif isinstance(tool_result, str):
                logger.info(f"📝 String response from {function_name}")
                # Direct string result (e.g., SOP search) - CLEAN
                if mode == "call" and len(tool_result) > 150:
                    return tool_result[:130] + "... Butuh detail lengkap?"
                return tool_result
            
            # Handle legacy dict responses with LLM interpretation
            elif isinstance(tool_result, dict):
                logger.info(f"📊 Dict response from {function_name} - delegating to LLM")
                # Get AI interpretation of structured result
                final_response = await self._run_completion(
                    messages=[
                        {"role": "user", "content": original_question},
                        {"role": "assistant", "content": f"Used {function_name} to get data"},
                        {
                            "role": "user",
                            "content": f"Based on this data: {json.dumps(tool_result, ensure_ascii=False)[:500 if mode == 'call' else 2000]}, please provide a helpful response."
                        }
                    ],
                    mode=mode
                )
                
                return final_response.choices[0].message.content
            
            else:
                logger.info(f"🤔 Unknown type response from {function_name}: {type(tool_result)}")
                # Fallback for other result types
                return str(tool_result)
            
        except Exception as e:
            logger.error(f"Tool execution error ({function_name}): {e}")
            import traceback
            logger.error(f"Tool execution traceback: {traceback.format_exc()}")
            return "Maaf, terjadi gangguan sistem."
    
    def _extract_brief_summary(self, text_content: str) -> str:
        """Extract brief summary from tool result text, removing markdown tables."""
        if not text_content:
            return "Analisis data berhasil"
        
        # Split by lines and find first meaningful line
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, headers, tables
            if (line and 
                not line.startswith('#') and 
                not line.startswith('|') and 
                not line.startswith('---') and
                not line.startswith('*') and
                len(line) > 10):
                return line
        
        # Fallback: use first line with cleanup
        if lines:
            first_line = lines[0].strip()
            if first_line.startswith('#'):
                first_line = first_line.lstrip('# ')
            return first_line if first_line else "Analisis data berhasil"
        
        return "Analisis data berhasil"
    
    def _build_system_prompt(self, mode: str = "chat") -> str:
        """Build system prompt based on mode"""
        if mode == "call":
            return """DENAI, asisten AI perusahaan. Mode panggilan.

Jawaban: RINGKAS, SOPAN, NATURAL (max 2 kalimat)."""
        else:
            return """DENAI, asisten AI perusahaan. Jawab dalam bahasa Indonesia yang jelas dan membantu."""
    
    def _prepare_messages(
        self,
        current_question: str,
        history: List[Dict[str, Any]] = None,
        mode: str = "chat"
    ) -> List[Dict[str, str]]:
        """Prepare conversation messages with history"""
        messages = [{"role": "system", "content": self._build_system_prompt(mode)}]
        
        # Add history (limited for different modes)
        if history:
            limit = 1 if mode == "call" else 3
            for h in history[-limit:]:
                content = h.get("message", "") or h.get("content", "")
                if content and str(content).strip():
                    role = h["role"] if h["role"] in ["user", "assistant"] else "user"
                    content_limit = 100 if mode == "call" else 300
                    messages.append({"role": role, "content": str(content)[:content_limit]})
        
        # Add current question
        messages.append({"role": "user", "content": current_question})
        
        return messages
    
    def get_tools_info(self) -> Dict[str, Any]:
        """Get information about available tools"""
        return {
            "tools_available": self.tools_available,
            "routing": "LLM-based intent classifier + tools.py routing",
            "intent_classifier": "A=SOP_EXPLANATION, B=HR_DATA_REQUEST",
            "security_gate": "Role-based access control for HR data",
            "analytics_support": "Universal analytics for HR, Finance, Sales, Operations",
            "architecture": "LLM classifier → Security gate → Dynamic tools → Universal analytics",
            "visualization": "Chart hints generation for optimal UX"
        }