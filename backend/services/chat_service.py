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

try:
    from app.langfuse_client import LANGFUSE_ENABLED, langfuse_observation
    if LANGFUSE_ENABLED:
        from langfuse.openai import OpenAI
    else:
        from openai import OpenAI
except Exception:
    LANGFUSE_ENABLED = False
    from openai import OpenAI
    from contextlib import nullcontext as _nc

    def langfuse_observation(name: str, **kwargs):  # type: ignore[misc]
        return _nc(None)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import (
    OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE,
    API_TIMEOUT_DEFAULT, API_TIMEOUT_CALL_MODE,
    CALL_MODE_TEMPERATURE, CHAT_MODE_TEMPERATURE,
    CALL_MODE_MAX_TOKENS, CHAT_MODE_MAX_TOKENS,
    INTENT_CLASSIFIER_MODEL, INTENT_CLASSIFIER_TEMPERATURE, INTENT_CLASSIFIER_MAX_TOKENS
)

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

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
- User asks for a PERSONAL CALCULATION using THEIR OWN hypothetical numbers, not real DB data (e.g., "Kalau gaji SAYA 10 juta", "Jika SAYA lembur 5 jam", "Hitungkan upah lembur SAYA").
- Keywords: "Bagaimana aturan", "Apa syarat", "Cara mengajukan", "Boleh atau tidak", "Coba hitungkan upah saya".
- Example: "Bagaimana aturan lembur di hari libur?" -> A
- Example: "Kalau gaji SAYA 5 juta dan saya lembur, dapat berapa?" -> A

B (EMPLOYEE_DATA / SQL DATABASE):
- User asks for FACTUAL COMPANY DATA, aggregation, statistics, lists of names, or data filtering from the database.
- ALSO includes GROUP/AGGREGATE calculations using real employee data (e.g., "Jika SELURUH karyawan band 5 lembur 5 jam, berapa total biaya?"). These require pulling actual DB data (salaries, headcount) and should be → B.
- Keywords: "Berapa total jumlah", "Siapa saja nama", "Tampilkan daftar", "Penyebaran", "seluruh karyawan", "semua band", "total biaya jika".
- Example: "Siapa saja karyawan yang akan pensiun tahun depan?" -> B
- Example: "Berapa total biaya lembur divisi IT bulan lalu?" -> B
- Example: "Jika seluruh karyawan band 5 lembur 5 jam, berapa total uang lembur perusahaan?" -> B

RULES:
1. Clear greeting → "greeting"
2. Casual/unrelated (world events, weather, celebrities, cooking) → "casual_chat"
3. Policy question OR personal (self) simulation → "A"
4. Factual company data query OR group/aggregate calculation → "B"
5. Unsure A/B → default "A"
6. If context shows previous HR/SOP topic, treat follow-up questions as HR even if phrased casually → "A"
7. Questions about company documents, teams, duties, regulations, procedures → always "A" (never casual_chat)
8. When in doubt → "A" (never refuse a potentially valid HR question as casual_chat)

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
            'ini', 'itu', 'nya', 'dia', 'mereka', 'tersebut', 'yang tadi',
            'it', 'that', 'this', 'they', 'he', 'she', 'them',
            'peraturan ini', 'aturan ini', 'kebijakan ini', 'dokumen ini'
        ]
        
        question_lower = current_question.lower()
        has_ambiguity = any(pattern in question_lower for pattern in ambiguous_patterns)
        
        # If question is long (>8 words) and has no ambiguous references → skip!
        word_count = len(current_question.split())
        if not has_ambiguity and word_count > 8:
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
Tugasmu: tulis ulang pertanyaan lanjutan menjadi pertanyaan mandiri (standalone) yang jelas tanpa perlu membaca riwayat.

ATURAN WAJIB:
- Klarifikasi subjek/objek yang ambigu (kata ganti seperti "ini", "itu", "nya", "peraturan ini") menggunakan konteks dari history
- BOLEH menyebutkan nama dokumen/SKD yang sedang dibahas dalam history HANYA jika pertanyaan secara eksplisit merujuk ke "peraturan ini", "aturan ini", "dokumen ini", atau sejenisnya
- DILARANG menambahkan "menurut SKD X" atau nama dokumen apapun jika pertanyaan tidak menyebut atau merujuk ke dokumen tertentu — pertanyaan faktual umum seperti "apa kepanjangan dari X" tidak perlu dikaitkan ke dokumen spesifik
- DILARANG mengubah maksud atau scope pertanyaan (contoh: jangan tambah "yang sudah pensiun" jika user tidak menyebutnya)
- DILARANG menambahkan asumsi yang sama sekali tidak ada di history maupun pertanyaan
- Jika pertanyaan sudah jelas dan tidak ada referensi ambigu, kembalikan PERSIS seperti aslinya

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

    async def _decompose_query(self, question: str) -> Dict[str, Any]:
        """
        Master Orchestrator: Memutuskan rute mana yang aktif.
        Sekarang lebih ketat dalam membedakan subjek 'SAYA' vs 'SELURUH'.
        """
        prompt = f"""Anda adalah Master Orchestrator untuk sistem Multi-Agent HR.
Tugas Anda: Analisis pertanyaan pengguna dan tentukan mesin mana yang harus dijalankan.

=== MESIN YANG TERSEDIA ===
- Mesin A (SOP/Policy): Aturan, kebijakan, dan simulasi PERSONAL (Subjek: "Saya", "Kalau gaji saya").
- Mesin B (HR Database): Data faktual dari database karyawan. Bisa menjawab: jumlah, distribusi, penyebaran, ranking, daftar, breakdown per grup (band, divisi, lokasi, jabatan, gender, status pensiun, dll).
  ⚠️ Database TIDAK punya data nominal gaji. Hanya data struktural karyawan.

=== ATURAN ROUTING ===
1. PERTANYAAN PERSONAL (Subjek: "Saya", "Gaji saya", "Kalau saya"):
   - Simulasi diri sendiri. SET: run_a=true, run_b=false.

2. PERTANYAAN FAKTUAL / DATA MURNI (Subjek: "Berapa", "Siapa saja", "Tampilkan", "Penyebaran", "Distribusi", "Daftar", "Ranking"):
   - SET: run_a=false, run_b=true.
   - query_b: salin pertanyaan user PERSIS, pertahankan kata kunci asli (penyebaran, distribusi, ranking, dll).

3. KALKULASI / SIMULASI KELOMPOK (misal: "hitung total biaya lembur Band 5 yang pensiun", "simulasi THR seluruh divisi"):
   - Butuh aturan dari SOP (A) DAN jumlah/data orang dari database (B).
   - SET: run_a=true, run_b=true.
   - query_a: pertanyaan fokus ke ATURAN/KEBIJAKAN saja (mis: "Apa tarif lembur hari libur nasional?").
   - query_b: pertanyaan MURNI DATA ke database (mis: "Berapa jumlah karyawan Band 5 yang pensiun tahun 2026?").
     ⚠️ query_b HARUS berupa pertanyaan database sederhana — JANGAN sertakan kata "simulasi", "hitung", "asumsikan", atau angka asumsi. Hanya minta DATA faktual yang dibutuhkan untuk kalkulasi.

Pertanyaan: "{question}"

Balas HANYA dengan JSON valid:
{{
  "run_a": true/false,
  "run_b": true/false,
  "query_a": "<pertanyaan fokus aturan/kebijakan untuk Mesin SOP>",
  "query_b": "<pertanyaan data murni untuk database, tanpa kata simulasi/asumsi>"
}}"""

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=INTENT_CLASSIFIER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(response.choices[0].message.content.strip())

            run_a = bool(parsed.get("run_a", True))
            run_b = bool(parsed.get("run_b", False))
            
            # Jika pertanyaan PERSONAL diri sendiri (bukan tentang kelompok/karyawan lain), paksa run_b=False
            question_lower = question.lower()
            is_personal = (
                ("saya" in question_lower or "gaji saya" in question_lower)
                and not any(w in question_lower for w in ["karyawan", "seluruh", "semua", "band", "divisi", "pegawai"])
            )
            if is_personal:
                run_b = False

            query_a = parsed.get("query_a") or (question if run_a else "")
            # Fallback: jika query_b kosong atau LLM mengubah terlalu jauh, gunakan pertanyaan original
            query_b = (parsed.get("query_b") or question) if run_b else ""

            if not run_a and not run_b:
                run_a = True
                query_a = question

            logger.info(f"🧭 [ORCHESTRATOR] run_a={run_a} | run_b={run_b} | A: {query_a[:50]} | B: {query_b}")
            return {"run_a": run_a, "run_b": run_b, "query_a": query_a, "query_b": query_b}

        except Exception as e:
            logger.warning(f"⚠️ Orchestrator failed: {e}. Defaulting to run_a=True.")
            return {"run_a": True, "run_b": False, "query_a": question, "query_b": ""}

    async def _execute_intent_flow(
        self, intent: str, question: str, user_role: str, session_id: str,
        history: List[Dict[str, Any]], mode: str, cancellation_check: Optional[Callable],
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
                cancellation_check=cancellation_check,
            )
            
            if isinstance(result, dict) and result.get("data"):
                return {
                    "answer": result.get("answer", result.get("text", "Analytics completed")),
                    "query": question,
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
        cancellation_check: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        try:
            is_hr_user = user_role.lower() in ['hr', 'admin', 'manager']
            gatekeeper_redirected = False

            if not is_hr_user:
                # ⚡ FAST PATH: Employee — skip ALL classification, direct to Route A
                logger.info(f"⚡ [FAST PATH] role='{user_role}' → Route A only (no classifier, no router)")
                standalone_question = question
                run_a, run_b = True, False
                query_for_a = question
                query_for_b = ""
            else:
                # ✨ STEP 1: UNIFIED Classification — OTel context otomatis di-inherit
                with langfuse_observation("intent_classification", input={"question": question}) as _sp:
                    classification = await classify_intent_unified(question, history)
                    if _sp:
                        _sp.update(output={"classification": classification})

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

                # ✨ STEP 2: Smart Paraphrase
                with langfuse_observation("query_contextualization", input={"question": question}) as _sp:
                    standalone_question = await self._smart_contextualize(question, history)
                    if _sp:
                        _sp.update(output={"standalone": standalone_question})

                # ✨ STEP 3: Always run A+B in parallel for HR users
                run_a = True
                run_b = True
                query_for_a = standalone_question
                query_for_b = standalone_question
                logger.info(f"🧭 [ORCHESTRATOR] run_a=True | run_b=True (always parallel) | A: {query_for_a[:50]} | B: {query_for_b[:50]}")

                # Safety gatekeeper
                if run_b and not is_hr_user:
                    logger.warning(
                        f"🔒 [GATEKEEPER] Route B blocked | role='{user_role}' | "
                        f"session_id='{session_id}' | query='{standalone_question[:60]}'"
                    )
                    run_b = False
                    if not run_a:
                        run_a = True
                        query_for_a = standalone_question
                    gatekeeper_redirected = True

            # ✨ STEP 4: Selective Parallel Execution
            # Bungkus setiap route dengan langfuse_observation agar semua child span
            # (RAG engine, LangChain calls, OpenAI calls) otomatis menjadi nested.
            # asyncio.create_task meng-copy OTel context saat task dibuat, sehingga
            # context "chat_interaction" diteruskan ke setiap task.

            async def _run_route_a():
                with langfuse_observation("route_a_rag", input={"query": query_for_a}):
                    return await self._execute_intent_flow(
                        intent="A", question=query_for_a, user_role=user_role,
                        session_id=session_id, history=history, mode=mode,
                        cancellation_check=cancellation_check,
                    )

            async def _run_route_b():
                with langfuse_observation("route_b_database", input={"query": query_for_b}):
                    return await self._execute_intent_flow(
                        intent="B", question=query_for_b, user_role=user_role,
                        session_id=session_id, history=history, mode=mode,
                        cancellation_check=cancellation_check,
                    )

            active_tasks: Dict[str, asyncio.Task] = {}
            if run_a:
                active_tasks["a"] = asyncio.create_task(_run_route_a())
            if run_b:
                active_tasks["b"] = asyncio.create_task(_run_route_b())

            logger.info(f"⚡ Launching routes: {list(active_tasks.keys())}")
            raw_results = await asyncio.gather(*active_tasks.values(), return_exceptions=True)
            results = dict(zip(active_tasks.keys(), raw_results))

            # Normalize exceptions to failure dicts
            for key in list(results.keys()):
                if isinstance(results[key], Exception):
                    logger.warning(f"⚠️ Intent {key.upper()} raised exception: {results[key]}")
                    results[key] = {"error": str(results[key]), "answer": "maaf, terjadi kesalahan", "authorized": True}

            result_a = results.get("a")
            result_b = results.get("b")
            a_failed = self._is_failure(result_a) if result_a is not None else True
            b_failed = self._is_failure(result_b) if result_b is not None else True

            # SCENARIO 1: Both ran and both succeeded → LLM Synthesis
            if result_a is not None and result_b is not None and not a_failed and not b_failed:
                # Siapkan data mentah B agar bisa dibaca dan dihitung oleh LLM
                b_content_for_llm = str(result_b.get("answer", ""))
                if result_b.get("message_type") == "analytics_result" and "data" in result_b:
                    b_data = result_b["data"]
                    b_content_for_llm += f"\n[RAW DATA: Kolom={b_data.get('columns')}, Baris={b_data.get('rows')}]"
                elif "structured_data" in result_b:
                    b_content_for_llm += f"\n[RAW DATA: {result_b['structured_data']}]"

                # Save pre-synthesis context for LLM Judge
                _eval_ctx = (
                    f"SOP Answer:\n{str(result_a.get('answer', ''))}"
                    f"\n\nDatabase Answer:\n{b_content_for_llm}"
                )

                merged_answer = await self._synthesize_results(
                    question=standalone_question,
                    answer_a=str(result_a.get("answer", "")),
                    answer_b=b_content_for_llm,
                    mode=mode
                )

                b_has_analytics = (
                    result_b.get("message_type") == "analytics_result"
                    or bool(result_b.get("structured_data"))
                )
                if b_has_analytics:
                    result_b["answer"] = merged_answer
                    result_b["_eval_context"] = _eval_ctx
                    logger.info("✅ MERGE: A + B (Used B as base due to analytics)")
                    return result_b
                else:
                    result_a["answer"] = merged_answer
                    result_a["_eval_context"] = _eval_ctx
                    logger.info("✅ MERGE: A + B (Used A as base, no analytics in B)")
                    return result_a

            # SCENARIO 2: A succeeded (B not run, or B failed)
            if not a_failed:
                if gatekeeper_redirected:
                    original_answer = result_a.get("answer", "")
                    result_a["answer"] = (
                        "Maaf, akses ke data analitik database dibatasi untuk peran Anda. "
                        "Berikut adalah informasi berdasarkan pedoman SOP perusahaan:\n\n"
                        + original_answer
                    )
                result_a["_eval_context"] = str(result_a.get("answer", ""))
                logger.info("✅ Returning A (RAG/SOP)")
                return result_a

            # SCENARIO 3: B succeeded (A not run, or A failed)
            if not b_failed:
                result_b["_eval_context"] = str(result_b.get("answer", ""))
                logger.info("✅ Returning B (Database)")
                return result_b

            # SCENARIO 4: Everything that ran failed
            logger.warning("❌ All active routes failed — returning failure message")
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
            base_result = result_a or result_b or {}
            base_result["answer"] = error_html
            return base_result
            
        except asyncio.CancelledError:
            logger.warning(f"🛑 Chat processing cancelled for session {session_id}")
            raise
                
        except Exception as e:
            logger.error(f"❌ Chat processing error: {e}", exc_info=True)
            return {"error": f"Maaf, terjadi gangguan: {str(e)}", "authorized": True}
    
    async def run_ab_parallel_for_stream(
        self,
        question: str,
        user_role: str,
        session_id: str,
        history: List[Dict[str, Any]] = None,
        mode: str = "chat",
        cancellation_check: Optional[Callable] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        If this is an A+B (merge) query, runs both routes in parallel and returns
        pre-synthesis data so the caller can stream the synthesis step.
        Returns None for non-A+B queries (caller falls back to process_question).

        OPTIMIZED: Calls search_sop and query_hr_database directly — skips the
        _run_completion LLM call inside _execute_intent_flow (which was a no-op:
        tool_choice was always forced and the generated args were always overridden).
        """
        is_hr_user = user_role.lower() in ['hr', 'admin', 'manager']

        with langfuse_observation("query_contextualization", input={"question": question}) as _sp:
            standalone_question = await self._smart_contextualize(question, history)
            if _sp:
                _sp.update(output={"standalone": standalone_question})

        if not is_hr_user:
            # Non-HR: run A only — if A fails, caller will show "Akses Terbatas"
            from app.tools import search_sop as _search_sop
            logger.info(f"⚡ [STREAM A-only] Non-HR user, route A only: {standalone_question[:60]}")
            with langfuse_observation("route_a_rag", input={"query": standalone_question}):
                try:
                    sop_answer = await _search_sop(
                        question=standalone_question,
                        session_id=session_id,
                        cancellation_check=cancellation_check,
                    )
                    result_a = {"answer": sop_answer, "authorized": True}
                except Exception as e:
                    result_a = {"error": str(e), "answer": "maaf, terjadi kesalahan", "authorized": True}

            if self._is_failure(result_a):
                return None  # A failed → caller shows "Akses Terbatas" for B-only content
            return {"mode": "a_only", "result_a": result_a, "standalone_question": standalone_question}

        # HR users: always run A+B in parallel — no orchestrator needed
        run_a = True
        run_b = True
        query_for_a = standalone_question
        query_for_b = standalone_question
        logger.info(f"🧭 [STREAM ORCHESTRATOR] run_a=True | run_b=True (always parallel) | A: {query_for_a[:50]} | B: {query_for_b[:50]}")

        from app.tools import search_sop, query_hr_database, StructuredResponse as _SR

        def _process_b_result(raw, q_b: str) -> Dict[str, Any]:
            """Convert query_hr_database output to a standard result dict."""
            if isinstance(raw, _SR) and raw.data_type == "analytics":
                sd = raw.structured_data or {}
                cols = ["category" if c == "Undefined" else c for c in sd.get("columns", [])]
                rows = sd.get("rows", [])
                title = f'<h3 class="analytics-query-title">{q_b.title()}</h3>'
                viz = (raw.visualization_available and 2 <= len(rows) <= 500 and len(cols) >= 2)
                result = build_analytics_response(
                    domain="hr", text=title, columns=cols, rows=rows,
                    session_id=session_id, visualization_available=viz,
                    chart_hints=generate_chart_hints("hr", cols, rows) if viz else None,
                    sql_query=raw.sql_query,
                    sql_explanation=raw.sql_explanation,
                )
                result["answer"] = title
                return result
            return {"answer": str(raw), "authorized": True}

        async def _run_route_a():
            with langfuse_observation("route_a_rag", input={"query": query_for_a}):
                sop_answer = await search_sop(
                    question=query_for_a,
                    session_id=session_id,
                    cancellation_check=cancellation_check,
                )
                return {"answer": sop_answer, "authorized": True}

        async def _run_route_b_parallel():
            with langfuse_observation("route_b_database", input={"query": query_for_b}):
                raw = await query_hr_database(
                    question=query_for_b, user_role=user_role, session_id=session_id
                )
                return _process_b_result(raw, query_for_b)

        logger.info(f"⚡ [STREAM A+B] Direct tool calls: A={query_for_a[:40]} | B={query_for_b[:40]}")
        raw_results = await asyncio.gather(
            asyncio.create_task(_run_route_a()),
            asyncio.create_task(_run_route_b_parallel()),
            return_exceptions=True,
        )
        result_a, result_b = raw_results

        if isinstance(result_a, Exception):
            result_a = {"error": str(result_a), "answer": "maaf, terjadi kesalahan", "authorized": True}
        if isinstance(result_b, Exception):
            result_b = {"error": str(result_b), "answer": "maaf, terjadi kesalahan", "authorized": True}

        a_failed = self._is_failure(result_a)
        b_failed = self._is_failure(result_b)

        # If both failed → caller falls back to process_question
        if a_failed and b_failed:
            return None

        # If only B failed → return A result as SOP-only (don't discard valid SOP answer)
        if not a_failed and b_failed:
            logger.info("⚡ [STREAM A+B] B failed but A succeeded — returning a_only result")
            return {"mode": "a_only", "result_a": result_a}

        # If only A failed → return B result as b_only
        if a_failed and not b_failed:
            logger.info("⚡ [STREAM A+B] A failed but B succeeded — returning b_only result")
            return {"mode": "b_only", "result_b": result_b, "query_for_b": query_for_b}

        b_content = str(result_b.get("answer", ""))
        if result_b.get("message_type") == "analytics_result" and "data" in result_b:
            b_data = result_b["data"]
            b_content += f"\n[RAW DATA: Kolom={b_data.get('columns')}, Baris={b_data.get('rows')}]"

        eval_ctx = (
            f"SOP Answer:\n{str(result_a.get('answer', ''))}"
            f"\n\nDatabase Answer:\n{b_content}"
        )
        b_has_analytics = result_b.get("message_type") == "analytics_result"
        return {
            "mode": "ab",
            "standalone_question": standalone_question,
            "answer_a": str(result_a.get("answer", "")),
            "answer_b_content": b_content,
            "eval_ctx": eval_ctx,
            "result_base": result_b if b_has_analytics else result_a,
        }

    async def _synthesize_results_stream(
        self,
        question: str,
        answer_a: str,
        answer_b: str,
        mode: str = "chat",
    ):
        """Async generator: streams synthesis of A+B results token by token."""
        from openai import AsyncOpenAI as _AsyncOpenAI
        async_client = _AsyncOpenAI(api_key=OPENAI_API_KEY)
        temperature = CALL_MODE_TEMPERATURE if mode == "call" else CHAT_MODE_TEMPERATURE
        max_tokens = CALL_MODE_MAX_TOKENS if mode == "call" else CHAT_MODE_MAX_TOKENS

        system_content = (
            "Anda adalah DEN.AI, Senior HR Data Analyst. Tugas Anda adalah mensintesis aturan SOP dan Data Faktual ke dalam satu kesimpulan analisis (Insight) yang komprehensif.\n\n"
            "ATURAN MUTLAK:\n"
            "1. DILARANG menggunakan Markdown (seperti **, ###, atau LaTeX \\[ \\]). WAJIB gunakan HANYA tag HTML bersih (seperti <h3>, <strong>, <ul>, <li>, <p>, <br>).\n"
            "2. WAJIB PERTAHANKAN DETAIL: Jangan membuang informasi penting dari Data A (SOP).\n"
            "3. Jika ini adalah pertanyaan simulasi biaya, Anda WAJIB melakukan kalkulasi matematika sampai ketemu estimasi TOTAL RUPIAH.\n"
            "4. Jika user TIDAK menyebutkan nominal gaji (untuk kasus lembur), WAJIB buat ASUMSI (misal: 'Asumsi rata-rata gaji pokok adalah Rp 5.000.000').\n"
            "5. Struktur HTML Anda harus terdiri dari 4 bagian:\n"
            "   <h3>Aturan & Kebijakan</h3>\n"
            "   <h3>Data Faktual</h3>\n"
            "   <h3>Simulasi & Insight Biaya</h3>\n"
            "   <h3>Rujukan Dokumen</h3>\n\n"
            "Gunakan bahasa Indonesia yang profesional."
        )
        user_content = (
            f"Pertanyaan User: {question}\n\n"
            f"Data dari Buku Panduan/SOP (Data A):\n{answer_a}\n\n"
            f"Data dari Database HR (Data B):\n{answer_b}\n\n"
            "Berikan laporan analisis HTML Anda sekarang."
        )

        try:
            stream = await async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"❌ Synthesis stream error: {e}")
            yield f"<p><strong>Berdasarkan Panduan/SOP:</strong></p>{answer_a}<p><strong>Berdasarkan Data Aktual:</strong></p>{answer_b}"

    async def _synthesize_results(
        self,
        question: str,
        answer_a: str,
        answer_b: str,
        mode: str
    ) -> str:
        fallback = f"<p><strong>Berdasarkan Panduan/SOP:</strong></p>{answer_a}<p><strong>Berdasarkan Data Aktual:</strong></p>{answer_b}"
        try:
            temperature = CALL_MODE_TEMPERATURE if mode == "call" else CHAT_MODE_TEMPERATURE
            max_tokens = CALL_MODE_MAX_TOKENS if mode == "call" else CHAT_MODE_MAX_TOKENS

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Anda adalah DEN.AI, Senior HR Data Analyst. Tugas Anda adalah mensintesis aturan SOP dan Data Faktual ke dalam satu kesimpulan analisis (Insight) yang komprehensif.\n\n"
                                "ATURAN MUTLAK:\n"
                                "1. DILARANG menggunakan Markdown (seperti **, ###, atau LaTeX \\[ \\]). WAJIB gunakan HANYA tag HTML bersih (seperti <h3>, <strong>, <ul>, <li>, <p>, <br>).\n"
                                "2. WAJIB PERTAHANKAN DETAIL: Jangan membuang informasi penting dari Data A (SOP). Jika ada informasi tentang jarak (km), jenis tarif (Umum/Khusus), atau syarat tertentu, cantumkan semuanya dengan jelas.\n"
                                "3. Jika ini adalah pertanyaan simulasi biaya, Anda WAJIB melakukan kalkulasi matematika sampai ketemu estimasi TOTAL RUPIAH. PERINGATAN: Lakukan perhitungan perkalian secara perlahan, sesuaikan tarif dengan kondisi di SOP, dan hitung dengan SANGAT AKURAT.\n"
                                "4. Jika user TIDAK menyebutkan nominal gaji (untuk kasus lembur), WAJIB buat ASUMSI (misal: 'Asumsi rata-rata gaji pokok adalah Rp 5.000.000'). Untuk kasus Perjalanan Dinas, gunakan tarif yang ada di SOP.\n"
                                "5. Struktur HTML Anda harus terdiri dari 4 bagian:\n"
                                "   <h3>Aturan & Kebijakan</h3> (Jelaskan aturan lengkap dari SOP, JANGAN dihilangkan detail syarat/jarak/tarifnya)\n"
                                "   <h3>Data Faktual</h3> (Sebutkan jumlah karyawan dari database)\n"
                                "   <h3>Simulasi & Insight Biaya</h3> (Tunjukkan step-by-step perkaliannya dengan angka yang PRESISI hingga ketemu Grand Total)\n"
                                "   <h3>Rujukan Dokumen</h3> (Salin persis sumber dokumen dan bab dari Data A).\n\n"
                                "Gunakan bahasa Indonesia yang profesional, rapi, dan mudah dibaca oleh jajaran direksi."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Pertanyaan User: {question}\n\n"
                                f"Data dari Buku Panduan/SOP (Data A):\n{answer_a}\n\n"
                                f"Data dari Database HR (Data B):\n{answer_b}\n\n"
                                "Berikan laporan analisis HTML Anda sekarang."
                            )
                        }
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                ),
                timeout=30
            )

            synthesized = response.choices[0].message.content
            if not synthesized or not synthesized.strip():
                logger.warning("⚠️ Synthesis returned empty response, using fallback")
                return fallback

            logger.info("✅ LLM synthesis completed successfully")
            return synthesized

        except asyncio.TimeoutError:
            logger.warning("⚠️ Synthesis timed out after 15s, using fallback")
            return fallback
        except Exception as e:
            logger.error(f"❌ Synthesis error: {e}")
            return fallback

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
        cancellation_check: Optional[Callable] = None,
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
                    
                    # Use question as styled HTML heading for chat bubble
                    title_text = original_question.title() if original_question else "Hasil Analisis Data"
                    brief_text = f'<h3 class="analytics-query-title">{title_text}</h3>'

                    viz_available = (tool_result.visualization_available and len(rows) >= 2 and len(columns) >= 2 and len(rows) <= 500)
                    chart_hints = generate_chart_hints(domain, columns, rows) if viz_available else None

                    result = build_analytics_response(
                        domain=domain, text=brief_text, columns=columns, rows=rows,
                        session_id=session_id, visualization_available=viz_available, chart_hints=chart_hints,
                        sql_query=getattr(tool_result, 'sql_query', None),
                        sql_explanation=getattr(tool_result, 'sql_explanation', None)
                    )
                    result["answer"] = brief_text
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
            # Strict filter: skip tables, headers, lists, and separators
            if line and not any(line.startswith(c) for c in ('#', '|', '---', '*', '-', '+')) and len(line) > 10:
                return line
        return "Berikut hasil analisis data Anda."
    
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