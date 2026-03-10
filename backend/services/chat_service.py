"""
DENAI Chat Service - UNIFIED CLASSIFIER VERSION (COMPLETE)
==================================================================
🔥 NEW: Unified Classifier (Greeting + Intent in ONE LLM call!)
⚡ OPTIMIZED: Reduced from 3-4 LLM calls to 2-3 LLM calls
✨ NEW: Smart Paraphrase (Skip if question already clear)
🚀 FEATURE: Greeting/Casual Chat handling with safe templates
"""

import logging
import asyncio
import json
import time
import os
import sys
from typing import Optional, List, Dict, Any, Literal, Union, Callable
from openai import OpenAI

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import (
    OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE,
    API_TIMEOUT_DEFAULT, API_TIMEOUT_CALL_MODE,
    CALL_MODE_TEMPERATURE, CHAT_MODE_TEMPERATURE,
    CALL_MODE_MAX_TOKENS, CHAT_MODE_MAX_TOKENS,
    SEMANTIC_ROUTER_ENABLED, SEMANTIC_ROUTER_THRESHOLD, SEMANTIC_ROUTER_ENCODER,
    INTENT_CLASSIFIER_MODEL, INTENT_CLASSIFIER_TEMPERATURE, INTENT_CLASSIFIER_MAX_TOKENS
)

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

# =====================================
# SEMANTIC ROUTER SETUP  
# =====================================
try:
    from semantic_router import Route
    from semantic_router.routers import SemanticRouter
    from semantic_router.encoders import OpenAIEncoder
    from semantic_router.index.local import LocalIndex
    SEMANTIC_ROUTER_AVAILABLE = True
    logger.info("✅ Semantic Router module imported successfully")
except ImportError as e:
    SEMANTIC_ROUTER_AVAILABLE = False
    logger.warning(f"⚠️ semantic-router tidak tersedia: {e}. Fallback ke LLM Judge.")

# =====================================
# DYNAMIC TOOLS ROUTING
# =====================================
try:
    from app.tools import get_current_tools_schema, TOOL_FUNCTIONS, StructuredResponse
    TOOLS_AVAILABLE = True
except ImportError as e:
    TOOLS_AVAILABLE = False
    def get_current_tools_schema(user_role="employee", intent="A"): return []
    TOOL_FUNCTIONS = {}
    class StructuredResponse:
        def __init__(self, **kwargs):
            for k, v in kwargs.items(): setattr(self, k, v)

# =====================================
# UNIVERSAL ANALYTICS BUILDER
# =====================================
def build_analytics_response(
    *, domain: str, text: str, columns: List[str], rows: List[List[Any]],
    session_id: str, turn_id: Optional[str] = None, visualization_available: bool = True,
    chart_hints: Optional[Dict[str, Any]] = None, sql_query: Optional[str] = None,
    sql_explanation: Optional[str] = None
) -> Dict[str, Any]:
    turn_id = turn_id or f"{session_id}-{int(time.time())}"
    response = {
        "message_type": "analytics_result", "domain": domain, "text": text,
        "data": {"columns": columns, "rows": rows},
        "visualization_available": visualization_available,
        "conversation_id": session_id, "turn_id": turn_id
    }
    if chart_hints: response["chart_hints"] = chart_hints
    if sql_query: response["sql_query"] = sql_query
    if sql_explanation: response["sql_explanation"] = sql_explanation
    return response

def generate_chart_hints(domain: str, columns: List[str], rows: List[List[Any]]) -> Optional[Dict[str, Any]]:
    if not columns or not rows or len(columns) < 2: return None
    if domain == "hr" and any("band" in col.lower() for col in columns):
        return {
            "preferred_types": ["bar", "pie"], "x_axis": columns[0],
            "y_axis": columns[1] if len(columns) > 1 else None,
            "title_suggestion": f"Distribusi {columns[1]} per {columns[0]}"
        }
    return None

# =====================================
# ✨ SEMANTIC INTENT CLASSIFIER
# =====================================
class SemanticIntentClassifier:
    def __init__(self):
        self.route_layer = None
        if SEMANTIC_ROUTER_AVAILABLE and SEMANTIC_ROUTER_ENABLED:
            try:
                if OPENAI_API_KEY:
                    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

                encoder = OpenAIEncoder(name="text-embedding-3-small", score_threshold=0.0)
                
                sop_route = Route(
                    name="sop_documents",
                    utterances=[
                        "bagaimana aturan perusahaan mengenai hal ini",
                        "apa syarat untuk bisa mengajukan hal tersebut",
                        "jelaskan prosedur atau langkah-langkahnya",
                        "apakah ada kebijakan yang mengatur masalah ini",
                        "saya mau tahu ketentuan dan regulasi dari perusahaan",
                        "bolehkah saya melakukan ini menurut buku panduan",
                        "bagaimana cara klaim atau mengajukan permohonan",
                        "apa hak dan kewajiban karyawan dalam situasi ini",
                        "bantu jelaskan pedoman operasional standar untuk proses ini",
                        "apakah hal ini diperbolehkan oleh aturan HR",
                        "dimana saya bisa membaca panduan tentang hal ini",
                        "apa sanksi atau konsekuensi jika melanggar aturan ini"
                    ]
                )

                hr_database_route = Route(
                    name="hr_database",
                    utterances=[
                        "berapa total jumlah karyawan yang ada di kriteria ini",
                        "tampilkan daftar nama orang-orang yang masuk kategori ini",
                        "hitung total biaya atau pengeluaran untuk periode ini",
                        "siapa saja yang memiliki status atau level ini",
                        "berapa rata-rata dari data tersebut",
                        "tolong rincikan penyebaran atau distribusi datanya",
                        "kelompokkan data ini berdasarkan divisinya",
                        "tolong tarik data historis untuk kejadian ini",
                        "filter data yang nilainya di atas atau di bawah angka ini",
                        "carikan karyawan dengan spesifikasi atau kualifikasi seperti ini",
                        "berikan laporan statistik mengenai hal ini",
                        "coba jumlahkan semua record yang sesuai"
                    ]
                )

                local_index = LocalIndex()
                self.route_layer = SemanticRouter(
                    encoder=encoder,
                    routes=[sop_route, hr_database_route],
                    index=local_index
                )

                if hasattr(self.route_layer, "index") and len(self.route_layer.index) == 0:
                    logger.warning("⚙️ Index Semantic Router kosong! Memaksa sinkronisasi manual...")
                    self.route_layer.add(routes=[sop_route, hr_database_route])
                    logger.info("✅ Sinkronisasi manual selesai.")
                
                logger.info(f"✅ Semantic Router Layer initialized (Threshold: {SEMANTIC_ROUTER_THRESHOLD})")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize RouteLayer: {e}")
                self.route_layer = None

    def classify(self, query: str) -> Optional[Literal["A", "B"]]:
        if not self.route_layer:
            return None
        
        try:
            route_choice = self.route_layer(query)
            
            if not route_choice:
                logger.info(f"⚠️ No confident match for: '{query[:50]}...'")
                return None
            
            score = getattr(route_choice, 'similarity_score', getattr(route_choice, 'score', 0.0))
            route_name = route_choice.name or "None"
            
            logger.info(f"📊 [SEMANTIC] Rute: '{route_name}' | Score: {score:.4f} | Threshold: {SEMANTIC_ROUTER_THRESHOLD}")
            
            if score < SEMANTIC_ROUTER_THRESHOLD:
                logger.info(f"⚠️ Score {score:.4f} below threshold. Fallback to LLM.")
                return None
                
            route_map = {"sop_documents": "A", "hr_database": "B"}
            intent = route_map.get(route_name)
            
            if intent:
                logger.info(f"⚡ Semantic Match: '{query[:50]}...' → {intent}")
                return intent
            
            logger.warning(f"⚠️ Unknown route: {route_name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Semantic Routing error: {e}")
            return None

try:
    semantic_classifier = SemanticIntentClassifier()
    logger.info("✅ Semantic classifier ready")
except Exception as e:
    logger.error(f"❌ Failed to init semantic classifier: {e}")
    semantic_classifier = None

# =====================================
# ✨ UNIFIED CLASSIFIER (Greeting + Intent in ONE!)
# =====================================
async def classify_intent_unified(
    question: str, 
    history: List[Dict[str, Any]] = None
) -> Literal["greeting", "casual_chat", "A", "B"]:
    """
    ✨ UNIFIED: Greeting detection + Intent classification in ONE LLM call!
    Saves 1 LLM call compared to separate greeting + intent detection.
    
    Returns:
        "greeting" - Simple greetings/tests (halo, hi, test)
        "casual_chat" - Non-HR casual talk (presiden, cuaca)
        "A" - SOP/Policy questions
        "B" - HR Database queries
    """
    
    # Try Semantic Router first (free, no LLM call!)
    if semantic_classifier:
        intent = await asyncio.to_thread(semantic_classifier.classify, question)
        if intent:
            # Semantic Router only returns A or B
            logger.info(f"⚡ Semantic Router Result: {intent}")
            return intent
    
    # Fallback to Unified LLM Classifier
    try:
        context_text = ""
        if history and len(history) > 0:
            last_msgs = [f"{h.get('role')}: {h.get('message', h.get('content', ''))}" 
                        for h in history[-4:]]
            context_text = "=== CHAT CONTEXT ===\n" + "\n".join(last_msgs) + "\n\n"

        prompt = f"""You are an elite intent classifier for an Enterprise HR Chatbot.
Classify the user's query into EXACTLY one: 'greeting', 'casual_chat', 'A', or 'B'.

{context_text}
=== CATEGORY DEFINITIONS ===

greeting:
- Simple greetings, salutations, system tests
- Very short (1-5 words), clearly greetings
- Examples: "halo", "hi", "good morning", "test", "apa kabar"

casual_chat:
- Casual talk NOT related to HR/company  
- World events, weather, recipes, celebrities
- Examples: "siapa presiden", "cuaca hari ini", "resep nasi goreng"

A (SOP_DOCUMENTS / RAG POLICY):
- User asks for rules, policies, guidelines, requirements, or procedures.
- User asks for a PERSONAL CALCULATION or SIMULATION using hypothetical numbers (e.g., "Kalau gaji saya 10 juta", "Jika saya lembur 5 jam").
- Keywords: "Bagaimana aturan", "Apa syarat", "Cara mengajukan", "Boleh atau tidak", "Coba hitungkan upah saya".
- Example: "Bagaimana aturan lembur di hari libur?" -> A
- Example: "Kalau gaji saya 5 juta dan saya lembur, dapat berapa?" -> A

B (EMPLOYEE_DATA / SQL DATABASE):
- User asks for FACTUAL COMPANY DATA, aggregation, statistics, lists of names, or data filtering from the database.
- MUST NOT be used for personal/hypothetical simulations.
- Keywords: "Berapa total jumlah", "Siapa saja nama", "Tampilkan daftar", "Penyebaran".
- Example: "Siapa saja karyawan yang akan pensiun tahun depan?" -> B
- Example: "Berapa total biaya lembur divisi IT bulan lalu?" -> B

RULES:
1. Clear greeting → "greeting"
2. Casual/unrelated → "casual_chat"
3. Policy question or personal simulation → "A"
4. Factual company data query → "B"
5. Unsure A/B → default "A"
6. Unsure casual → treat as HR (A or B)

Respond ONLY: greeting, casual_chat, A, or B

User: "{question}"
"""
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=INTENT_CLASSIFIER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        if result in ["greeting", "casual_chat", "a", "b"]:
            result_mapped = result.upper() if result in ["a", "b"] else result
            logger.info(f"🎯 Unified Classifier: '{question[:50]}...' → {result_mapped}")
            return result_mapped
        
        logger.warning(f"⚠️ Invalid result: '{result}', default to A")
        return "A"
        
    except Exception as e:
        logger.error(f"❌ Unified classifier error: {e}, default to A")
        return "A"


# Safe template responses for greeting/casual_chat
GREETING_RESPONSE = "Halo! Saya DEN.AI, asisten HR digital. Ada yang bisa saya bantu?"

CASUAL_CHAT_RESPONSE = """Maaf, saya adalah asisten khusus untuk informasi HR dan kebijakan perusahaan.

Saya bisa membantu dengan:
• Kebijakan dan prosedur (SOP)
• Data karyawan dan analytics
• Informasi terkait HR lainnya

Silakan ajukan pertanyaan terkait topik di atas! 😊"""


# =====================================
# CORE CHAT SERVICE
# =====================================
class ChatService:
    def __init__(self):
        self.client = client
        self.model = LLM_MODEL
        self.tools_available = TOOLS_AVAILABLE

    async def _smart_contextualize(
        self, 
        current_question: str, 
        history: List[Dict[str, Any]] = None
    ) -> str:
        """
        ✨ SMART PARAPHRASE: Skip if question already clear!
        Saves 1 LLM call for clear questions.
        """
        
        # No history = no need to paraphrase
        if not history or len(history) == 0:
            logger.info(f"⚡ SKIP paraphrase: No history")
            return current_question
        
        # Check for ambiguous patterns
        ambiguous_patterns = [
            'itu', 'nya', 'dia', 'mereka', 'tersebut', 'yang tadi',
            'it', 'that', 'this', 'they', 'he', 'she', 'them'
        ]
        
        question_lower = current_question.lower()
        has_ambiguity = any(pattern in question_lower for pattern in ambiguous_patterns)
        
        # If question is long (>6 words) and has no ambiguous references → skip!
        word_count = len(current_question.split())
        if not has_ambiguity and word_count > 6:
            logger.info(f"⚡ SKIP paraphrase: Question clear ({word_count} words, no ambiguity)")
            return current_question
        
        # Otherwise, paraphrase
        logger.info(f"🔄 NEED paraphrase: Ambiguous or short ({word_count} words)")
        return await self._contextualize_query(current_question, history)

    async def _contextualize_query(
        self, 
        current_question: str, 
        history: List[Dict[str, Any]] = None
    ) -> str:
        """
        ✨ STANDALONE QUERY GENERATOR ✨
        Mengubah pertanyaan ambigu (karena obrolan lanjutan) menjadi pertanyaan utuh/jelas.
        """
        if not history or len(history) == 0:
            return current_question

        context_text = "\n".join([
            f"{h.get('role', 'user')}: {h.get('message', h.get('content', ''))}" 
            for h in history[-4:]
        ])

        prompt = f"""Diberikan riwayat percakapan berikut dan pertanyaan lanjutan dari pengguna.
Formulasikan ulang pertanyaan lanjutan tersebut menjadi satu pertanyaan mandiri (standalone query) yang komprehensif tanpa perlu membaca riwayat lagi.
JANGAN menjawab pertanyaannya, cukup tulis ulang pertanyaannya agar jelas maksud subjeknya. 
Jika pertanyaan lanjutan sudah sangat jelas dengan sendirinya tanpa perlu history, kembalikan persis seperti aslinya.

Riwayat Percakapan:
{context_text}

Pertanyaan Lanjutan: {current_question}

Pertanyaan Mandiri:"""

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=INTENT_CLASSIFIER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=150
            )
            standalone_query = response.choices[0].message.content.strip()
            
            logger.info(f"🔄 [PARAPHRASE] '{current_question}' -> '{standalone_query}'")
            return standalone_query
        except Exception as e:
            logger.error(f"⚠️ Contextualize error: {e}")
            return current_question

    def _is_failure(self, result: Dict[str, Any]) -> bool:
        if not result or not isinstance(result, dict):
            return True
            
        if result.get("authorized") is False:
            return False
            
        if "error" in result:
            return True
            
        answer = str(result.get("answer", "")).lower()
        
        failure_keywords = [
            "[data_tidak_ditemukan_di_sop]",
            "data tidak tersedia",
            "no data found",
            "maaf, terjadi gangguan",
            "maaf, terjadi kesalahan",
            "tidak ditemukan",
            "failed to generate sql",
            "window function over clause",
            "informasi tidak tersedia atau anda tidak memiliki otorisasi" 
        ]
        
        return any(keyword in answer for keyword in failure_keywords)

    async def _execute_intent_flow(
        self, intent: str, question: str, user_role: str, session_id: str, 
        history: List[Dict[str, Any]], mode: str, cancellation_check: Optional[Callable]
    ) -> Dict[str, Any]:
        
        if intent == "B" and user_role.lower() not in ['hr', 'admin', 'manager']:
            logger.warning(f"🔒 HR DATA ACCESS DENIED: role={user_role}")
            return {
                "answer": f"🔒 <strong>Akses Dibatasi</strong>\n\nRole Anda (<strong>{user_role}</strong>) tidak memiliki otorisasi untuk mengakses database spesifik karyawan.",
                "authorized": False,
                "intent": intent
            }
        
        tools = get_current_tools_schema(user_role, intent) if self.tools_available else []
        messages = self._prepare_messages(question, history, mode)
        
        completion = await self._run_completion(messages, tools, mode)
        
        if completion.choices[0].message.tool_calls:
            tool_call = completion.choices[0].message.tool_calls[0]
            function_name = tool_call.function.name
            
            result = await self._execute_tool(
                tool_call, session_id, user_role, question, mode,
                cancellation_check=cancellation_check
            )
            
            if isinstance(result, dict) and result.get("data"):
                return {
                    "answer": result.get("answer", result.get("text", "Analytics completed")),
                    "authorized": True,
                    "tool_called": function_name,
                    "message_type": "analytics_result",
                    "data": result["data"],
                    "visualization_available": result["visualization_available"],
                    "conversation_id": result["conversation_id"],
                    "turn_id": result["turn_id"],
                    "domain": result["domain"],
                    "chart_hints": result.get("chart_hints"),
                    "intent": intent,
                    "sql_query": result.get("sql_query"),
                    "sql_explanation": result.get("sql_explanation")
                }
            
            elif isinstance(result, dict) and result.get("type") == "structured_response":
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
            
            return {
                "answer": str(result),
                "authorized": True,
                "tool_called": function_name,
                "intent": intent
            }
                
        return {
            "answer": completion.choices[0].message.content,
            "authorized": True,
            "tool_called": None,
            "intent": intent
        }
    
    async def process_question(
        self, 
        question: str, 
        user_role: str, 
        session_id: str, 
        history: List[Dict[str, Any]] = None, 
        mode: str = "chat",
        cancellation_check: Optional[Callable] = None
    ) -> Dict[str, Any]:
        try:
            # ✨ STEP 1: UNIFIED Classification (Greeting + Intent in ONE!)
            classification = await classify_intent_unified(question, history)
            
            # Handle greeting
            if classification == "greeting":
                logger.info(f"👋 Greeting detected: '{question}'")
                return {
                    "answer": GREETING_RESPONSE,
                    "authorized": True,
                    "intent": "greeting",
                    "tool_called": None,
                    "is_greeting": True
                }
            
            # Handle casual chat
            if classification == "casual_chat":
                logger.info(f"💬 Casual chat detected: '{question}'")
                return {
                    "answer": CASUAL_CHAT_RESPONSE,
                    "authorized": True,
                    "intent": "casual_chat",
                    "tool_called": None,
                    "is_casual_chat": True
                }
            
            # classification is now "A" or "B"
            original_intent = classification
            
            # ✨ STEP 2: Smart Paraphrase (SKIP if clear!)
            standalone_question = await self._smart_contextualize(question, history)

            # ✨ STEP 3: Execute with intent
            result = await self._execute_intent_flow(
                intent=original_intent, 
                question=standalone_question, 
                user_role=user_role, 
                session_id=session_id, 
                history=history, 
                mode=mode, 
                cancellation_check=cancellation_check
            )
            
            # 4. SISTEM FALLBACK NINJA (B -> A)
            if original_intent == "B" and self._is_failure(result):
                logger.warning("🔄 Rute B (Database) Gagal. Fallback ke SOP (Ninja Mode)...")
                
                fallback_result = await self._execute_intent_flow(
                    intent="A",
                    question=standalone_question, 
                    user_role=user_role, 
                    session_id=session_id, 
                    history=history, 
                    mode=mode, 
                    cancellation_check=cancellation_check
                )
                
                if not self._is_failure(fallback_result):
                    fallback_result["is_fallback"] = True
                    return fallback_result
                else:
                    result = fallback_result 
            
            # 5. ERROR HTML DOUBLE FAILURE
            if self._is_failure(result):
                error_html = """
                <div style="background-color: #fdfafb; border-left: 4px solid #c81e1e; padding: 16px; border-radius: 6px; font-family: sans-serif; margin-top: 8px;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <strong style="color: #c81e1e; font-size: 15px;">⚠️ Informasi Tidak Ditemukan</strong>
                    </div>
                    <p style="color: #4b5563; margin: 0; font-size: 14px; line-height: 1.5;">
                        Maaf, data spesifik atau panduan aturan yang Anda tanyakan tidak tersedia di <b>Sistem Database</b> maupun <b>Buku Panduan (SOP)</b> kami saat ini. <br><br>Silakan periksa kembali kata kunci Anda atau hubungi <b>Departemen HR</b> untuk mendapatkan bantuan lebih lanjut.
                    </p>
                </div>
                """
                result["answer"] = error_html

            return result
            
        except asyncio.CancelledError:
            logger.warning(f"🛑 Chat processing cancelled for session {session_id}")
            raise
                
        except Exception as e:
            logger.error(f"❌ Chat processing error: {e}", exc_info=True)
            return {"error": f"Maaf, terjadi gangguan: {str(e)}", "authorized": True}
    
    async def _run_completion(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None, mode: str = "chat"):
        try:
            temperature = CALL_MODE_TEMPERATURE if mode == "call" else CHAT_MODE_TEMPERATURE
            max_tokens = CALL_MODE_MAX_TOKENS if mode == "call" else CHAT_MODE_MAX_TOKENS
            timeout = API_TIMEOUT_CALL_MODE if mode == "call" else API_TIMEOUT_DEFAULT
            
            tool_choice = "auto"
            if tools:
                has_sop = any(t['function']['name'] == 'search_sop' for t in tools)
                has_hr = any(t['function']['name'] == 'query_hr_database' for t in tools)
                
                if has_sop and not has_hr:
                    tool_choice = {"type": "function", "function": {"name": "search_sop"}}
                elif has_hr:
                    tool_choice = {"type": "function", "function": {"name": "query_hr_database"}}
            
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model, messages=messages, tools=tools or None,
                    tool_choice=tool_choice, temperature=temperature, max_tokens=max_tokens
                ), timeout=timeout
            )
            
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise
    
    async def _execute_tool(
        self, 
        tool_call: Any, 
        session_id: str, 
        user_role: str, 
        original_question: str, 
        mode: str = "chat",
        cancellation_check: Optional[Callable] = None
    ) -> Union[str, Dict[str, Any]]:
        if not self.tools_available: return "Maaf, tools tidak tersedia."
        
        function_name = tool_call.function.name
        try:
            function_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            return "Maaf, terjadi kesalahan parsing argumen."
        
        if function_name not in TOOL_FUNCTIONS:
            return "Maaf, fungsi tidak tersedia."
        
        try:
            tool_function = TOOL_FUNCTIONS[function_name]
                
            function_args["session_id"] = session_id
            
            if "question" in function_args:
                function_args["question"] = original_question
                logger.info(f"🛡️ OVERRIDE: Mengirim teks mentah ke {function_name}")
            
            if cancellation_check and "cancellation_check" in tool_function.__code__.co_varnames:
                function_args["cancellation_check"] = cancellation_check
                logger.info(f"🔥 Threading cancellation check to {function_name}")
            
            tool_result = await tool_function(**function_args) if asyncio.iscoroutinefunction(tool_function) else tool_function(**function_args)
            
            if isinstance(tool_result, StructuredResponse):
                
                if tool_result.data_type == "analytics":
                    structured_data = tool_result.structured_data or {}
                    columns = structured_data.get("columns", [])
                    rows = structured_data.get("rows", [])
                    
                    columns = ["category" if col == "Undefined" else col for col in columns]
                    
                    domain_map = {"query_hr_database": "hr", "finance_analysis": "finance"}
                    domain = domain_map.get(function_name, "general")
                    
                    brief_text = self._extract_brief_summary(getattr(tool_result, 'text_content', ''))
                    
                    viz_available = (tool_result.visualization_available and len(rows) >= 2 and len(columns) >= 2 and len(rows) <= 500)
                    chart_hints = generate_chart_hints(domain, columns, rows) if viz_available else None
                    
                    result = build_analytics_response(
                        domain=domain, text=brief_text, columns=columns, rows=rows,
                        session_id=session_id, visualization_available=viz_available, chart_hints=chart_hints,
                        sql_query=getattr(tool_result, 'sql_query', None),
                        sql_explanation=getattr(tool_result, 'sql_explanation', None)
                    )
                    result["answer"] = getattr(tool_result, 'text_content', brief_text)
                    return result
                
                return {
                    "type": "structured_response", "data_type": tool_result.data_type,
                    "answer": getattr(tool_result, 'text_content', ''),
                    "structured_data": tool_result.structured_data,
                    "visualization_available": tool_result.visualization_available,
                    "metadata": getattr(tool_result, 'metadata', None)
                }
            
            elif isinstance(tool_result, str):
                return tool_result
            
            elif isinstance(tool_result, dict):
                final_response = await self._run_completion(
                    messages=[
                        {"role": "user", "content": original_question},
                        {"role": "assistant", "content": f"Used {function_name}"},
                        {"role": "user", "content": f"Data: {json.dumps(tool_result)[:500 if mode == 'call' else 2000]}"}
                    ], mode=mode
                )
                return final_response.choices[0].message.content
            
            return str(tool_result)
            
        except asyncio.CancelledError:
            logger.warning(f"🛑 Tool {function_name} cancelled")
            raise
            
        except Exception as e:
            logger.error(f"Tool execution error ({function_name}): {e}", exc_info=True)
            return "Maaf, terjadi gangguan sistem."
    
    def _extract_brief_summary(self, text_content: str) -> str:
        if not text_content: return "Analisis data berhasil"
        for line in text_content.split('\n'):
            line = line.strip()
            if line and not any(line.startswith(c) for c in ('#', '|', '---', '*')) and len(line) > 10:
                return line
        return text_content.split('\n')[0].strip().lstrip('# ') if text_content.split('\n') else "Analisis data berhasil"
    
    def _prepare_messages(self, current_question: str, history: List[Dict[str, Any]] = None, mode: str = "chat") -> List[Dict[str, str]]:
        system_prompt = "DENAI, asisten AI perusahaan. Jawab dalam bahasa Indonesia."
        
        if mode == "call":
            system_prompt = "DENAI, asisten AI. Mode panggilan: Jawab dengan ramah, natural, dan JABARKAN SEMUA POIN PENTING secara lengkap tanpa ada yang tertinggal."
        
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            limit = 2 if mode == "call" else 3
            for h in history[-limit:]:
                content = h.get("message", "") or h.get("content", "")
                if content and str(content).strip():
                    role = h["role"] if h["role"] in ["user", "assistant"] else "user"
                    messages.append({"role": role, "content": str(content)[:500 if mode == "call" else 300]})
        
        messages.append({"role": "user", "content": current_question})
        return messages