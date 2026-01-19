"""
DENAI Chat Service - LLM Intent Classifier Implementation
=========================================================

PERUBAHAN UTAMA:
✅ LLM-based intent classifier menggantikan regex HR detection
✅ Dual-stage classification: LLM classifier → Security gate
✅ Query SOP seperti "apa itu upah lembur" sekarang masuk ke SOP RAG
✅ Routing bersih: A=SOP_EXPLANATION, B=HR_DATA_REQUEST

FLOW BARU:
User Question → classify_intent_llm() → Security Gate → Tools → Engine
             A atau B              Role Check     SOP/HR   RAG/DB

NO hardcoded regex HR detection - ONLY LLM classification + security gate
"""

import logging
import asyncio
import json
from typing import Optional, List, Dict, Any, Literal
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


def classify_intent_llm(question: str) -> Literal["A", "B"]:
    """
    Enhanced LLM-based intent classifier for SOP vs HR DATA routing.
    
    Returns:
        "A" = SOP_EXPLANATION (policies, procedures, definitions, fixed rates)
        "B" = HR_DATA_REQUEST (actual employee data from database)
    """
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
    """
    Core AI chat orchestration service with LLM intent classification
    THIN LAYER - delegates routing to tools.py, business logic to engines/
    """
    
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
        """
        Process user question with LLM intent classification and security gate
        
        Args:
            question: User's question
            user_role: User role for authorization
            session_id: Session identifier
            history: Conversation history
            mode: Conversation mode ("chat" or "call")
            
        Returns:
            Dict with answer, tool_called, authorized, error
        """
        try:
            # 1. LLM INTENT CLASSIFICATION (DUAL-STAGE CLASSIFIER)
            intent = classify_intent_llm(question)
            
            # 2. HARD SECURITY GATE (role-based)
            if intent == "B" and user_role.lower() not in ['hr', 'admin', 'manager']:
                # HR DATA request from non-HR user = ACCESS DENIED
                logger.warning(f"🔒 HR DATA ACCESS DENIED: role={user_role}, intent={intent}")
                return {
                    "answer": "🔒 **Akses Terbatas**\n\nMaaf, informasi data karyawan hanya dapat diakses oleh tim HR. Untuk pertanyaan seputar kebijakan dan prosedur perusahaan, silakan tanya saja!",
                    "tool_called": None,
                    "authorized": False
                }
            
            # 3. GET DYNAMIC TOOLS BASED ON INTENT + ROLE
            dynamic_tools = self._get_dynamic_tools(user_role, intent)
            
            # 4. PREPARE CONVERSATION MESSAGES
            messages = self._prepare_messages(question, history, mode)
            
            # 5. RUN LLM WITH DYNAMIC TOOLS
            response = await self._run_completion(
                messages=messages,
                tools=dynamic_tools,
                mode=mode
            )
            
            message = response.choices[0].message
            
            # 6. HANDLE LLM RESPONSE
            if message.tool_calls and self.tools_available:
                # LLM chose to use a tool - execute it
                answer = await self._execute_tool(
                    tool_call=message.tool_calls[0],
                    session_id=session_id,
                    user_role=user_role,
                    original_question=question,
                    mode=mode
                )
                
                # Check for authorization failure
                authorized = not ("🔒" in answer and "tim HR" in answer)
                
                return {
                    "answer": answer,
                    "tool_called": message.tool_calls[0].function.name,
                    "authorized": authorized
                }
            
            # 7. DIRECT LLM RESPONSE (no tools)
            return {
                "answer": message.content,
                "tool_called": None,
                "authorized": True
            }
            
        except Exception as e:
            logger.error(f"Process question error: {e}")
            return {
                "answer": "Maaf, terjadi gangguan sistem.",
                "error": str(e),
                "authorized": True
            }
    
    def _get_dynamic_tools(self, user_role: str, intent: Literal["A", "B"]) -> List[Dict[str, Any]]:
        """
        Get dynamic tools schema based on intent classification
        SINGLE RESPONSIBILITY: Route based on intent + role
        """
        if not self.tools_available:
            return []
        
        try:
            # Route based on intent and role
            if intent == "A":
                # SOP_EXPLANATION = always SOP tools
                dynamic_tools = get_current_tools_schema(user_role, intent)
                logger.debug(f"✅ Intent A (SOP) → SOP tools for role={user_role}")
            else:
                # HR_DATA_REQUEST = HR tools (only if HR role, already checked above)
                dynamic_tools = get_current_tools_schema(user_role, intent)
                logger.debug(f"✅ Intent B (HR_DATA) → HR tools for role={user_role}")
            
            # Log for debugging
            tool_names = [tool['function']['name'] for tool in dynamic_tools]
            logger.debug(f"Dynamic tools: {tool_names}")
            
            return dynamic_tools
            
        except Exception as e:
            logger.error(f"Dynamic tools error: {e}")
            return []
    
    async def _run_completion(
        self,
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None, 
        mode: str = "chat"
    ) -> Any:
        """
        Run OpenAI chat completion with mode-specific settings
        🔥 CRITICAL: FORCE SOP tool to prevent RAG bypass
        """
        try:
            # Use mode-specific settings
            if mode == "call":
                timeout = API_TIMEOUT_CALL_MODE
                max_tokens = CALL_MODE_MAX_TOKENS
                temperature = CALL_MODE_TEMPERATURE
            else:
                timeout = API_TIMEOUT_DEFAULT
                max_tokens = CHAT_MODE_MAX_TOKENS
                temperature = CHAT_MODE_TEMPERATURE
            
            # 🔥 CRITICAL: Determine tool_choice to prevent SOP bypass
            tool_choice = None
            if tools:
                # Check if SOP tool is available
                has_sop_tool = any(tool['function']['name'] == 'search_sop' for tool in tools)
                has_hr_tool = any(tool['function']['name'] == 'query_hr_database' for tool in tools)
                
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
    ) -> str:
        """
        Execute tool function - DELEGATES to tools.py functions
        """
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
            
            # Handle different tool result types
            if isinstance(tool_result, str):
                # Direct string result (e.g., SOP search) - CLEAN
                if mode == "call" and len(tool_result) > 150:
                    return tool_result[:130] + "... Butuh detail lengkap?"
                return tool_result
            
            # Handle structured results with LLM interpretation
            elif isinstance(tool_result, dict):
                # Get AI interpretation of structured result
                final_response = await self._run_completion(
                    messages=[
                        {"role": "user", "content": original_question},
                        {"role": "assistant", "content": None, "tool_calls": [tool_call]},
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, ensure_ascii=False)[:500 if mode == "call" else 2000]
                        }
                    ],
                    mode=mode
                )
                
                return final_response.choices[0].message.content
            
            else:
                # Fallback for other result types
                return str(tool_result)
            
        except Exception as e:
            logger.error(f"Tool execution error ({function_name}): {e}")
            return "Maaf, terjadi gangguan sistem."
    
    def _build_system_prompt(self, mode: str = "chat") -> str:
        """
        Build system prompt based on mode
        MINIMAL PROMPT - no business logic here
        """
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
        """
        Prepare conversation messages with history
        """
        messages = [{"role": "system", "content": self._build_system_prompt(mode)}]
        
        # Add history (limited for different modes)
        if history:
            limit = 1 if mode == "call" else 3
            for h in history[-limit:]:
                role = h["role"] if h["role"] in ["user", "assistant"] else "user"
                content_limit = 100 if mode == "call" else 300
                content = h["message"][:content_limit]
                messages.append({"role": role, "content": content})
        
        # Add current question
        messages.append({"role": "user", "content": current_question})
        
        return messages
    
    def get_tools_info(self) -> Dict[str, Any]:
        """
        Get information about available tools
        """
        return {
            "tools_available": self.tools_available,
            "routing": "LLM-based intent classifier + tools.py routing",
            "intent_classifier": "A=SOP_EXPLANATION, B=HR_DATA_REQUEST",
            "security_gate": "Role-based access control for HR data",
            "modes": {
                "chat": {
                    "description": "Full conversation mode with detailed responses",
                    "max_tokens": CHAT_MODE_MAX_TOKENS,
                    "temperature": CHAT_MODE_TEMPERATURE
                },
                "call": {
                    "description": "Voice mode with concise responses",
                    "max_tokens": CALL_MODE_MAX_TOKENS,
                    "temperature": CALL_MODE_TEMPERATURE
                }
            },
            "architecture": "LLM classifier → Security gate → Dynamic tools → Engine execution"
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the chat service"""
        return {
            "model": self.model,
            "default_temperature": self.default_temperature,
            "chat_temperature": CHAT_MODE_TEMPERATURE,
            "call_temperature": CALL_MODE_TEMPERATURE,
            "chat_max_tokens": CHAT_MODE_MAX_TOKENS,
            "call_max_tokens": CALL_MODE_MAX_TOKENS,
            "tools_available": self.tools_available,
            "routing_method": "LLM intent classifier (A/B) + role-based security",
            "security": "Hard security gate prevents unauthorized HR access",
            "sop_protection": "FORCED tool choice prevents RAG bypass",
            "architecture": "Clean separation: classification→security→routing→execution"
        }