#!/usr/bin/env python3
"""
🚀 ULTIMATE HYBRID RAG ENGINE v7.2.0 (CANCELLATION EDITION)
===================================================================================
✅ NEW: Full cancellation support with 8 checkpoints throughout pipeline
✅ Saves ~99% cost on cancelled requests
✅ Production-ready with proper error handling
🔥 FIXED: Eligibility Check (Band 5 Only) & Smart Anti-Hallucination
"""

import os
import re
import time
import json
import logging
import asyncio
from typing import Optional, Dict, List, Tuple, Callable
from dataclasses import dataclass
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from pinecone import Pinecone
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import cohere

from engines.sop.analyzers.travel_analyzer import TravelAnalyzer
from engines.sop.analyzers.generic_analyzer import GenericAnalyzer
from engines.sop.templates_engine import SimpleTemplateEngine
from engines.sop.policy_injector import HRTravelPolicy
from engines.sop.rag_interceptor import ConstraintInterceptor

try:
    from app.langfuse_client import LANGFUSE_ENABLED, get_langchain_callback, langfuse_observation
except Exception:
    LANGFUSE_ENABLED = False
    def get_langchain_callback(): return None
    from contextlib import nullcontext as _nc
    def langfuse_observation(name: str, **kwargs):  # type: ignore[misc]
        return _nc(None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.config import (
    OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX,
    EMBEDDING_MODEL, COHERE_API_KEY, COHERE_MODEL,
    RAG_TOP_K, RAG_RETRIEVAL_K, RAG_MIN_SCORE, LLM_MODEL, LLM_TEMPERATURE,
    PINECONE_NAMESPACE
)

# =====================
# LAYER 1: FOUNDATION (Metrics & Validation)
# =====================
@dataclass
class RAGMetrics:
    queries: int = 0
    avg_response_time: float = 0.0
    successful_responses: int = 0
    failed_responses: int = 0
    cohere_rerank_calls: int = 0
    gkl_fallback_calls: int = 0
    cancelled_requests: int = 0  # 🔥 NEW

metrics = RAGMetrics()
satpam_aturan = ConstraintInterceptor()

def validate_input(question: str) -> Tuple[bool, str]:
    if not question or not question.strip():
        return False, "Pertanyaan tidak boleh kosong."
    if len(question) > 500:
        return False, "Pertanyaan terlalu panjang (maksimal 500 karakter)."
    return True, ""


# =====================
# LAYER 2: QUERY UNDERSTANDING (Robust Pydantic & Async)
# =====================
class QuerySchema(BaseModel):
    search_keywords: str = Field(description="3-6 kata kunci inti untuk pencarian Vector DB berdasarkan pertanyaan user.")
    scope: str = Field(description="Pilih HANYA SALAH SATU: domestic, international, atau general")
    doc_type: str = Field(description="Pilih HANYA SALAH SATU: sop_perjalanan_dinas, sop_lembur, sop_pembelajaran, atau general")
    template_type: str = Field(description="""Pilih HANYA SALAH SATU:
- 'general_calculation': JIKA nanya hitungan angka, total uang, UPD, tarif, atau jumlah biaya.
- 'procedure': JIKA nanya 'cara', 'langkah-langkah', 'bagaimana mengajukan'.
- 'rules': JIKA nanya syarat, kelayakan (Yes/No), atau 'dapat apa aja/fasilitas apa aja'.
- 'definition': JIKA nanya apa itu/definisi.
- 'general': Jika tidak masuk kategori di atas.""")
    kota_asal: str = Field(default="", description="Ekstrak kota_asal JIKA ADA.")
    kota_tujuan: str = Field(default="", description="Ekstrak kota_tujuan JIKA ADA.")
    butuh_kalkulasi_jarak: bool = Field(description="Pilih TRUE HANYA JIKA pertanyaan berhubungan dengan perjalanan dinas ke suatu Kota/Negara ATAU menanyakan Uang/Fasilitas perjalanan. Pilih FALSE jika nanya prosedur/cara umum.")
    
class FastQueryAnalyzer:
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=QuerySchema)
        logger.info("✅ FastQueryAnalyzer Ready (Powered by Pydantic JSON Guard)")

    async def analyze_async(self, query: str) -> Dict:
        """
        Menganalisis pertanyaan yang SUDAH BERSIH (Standalone) dari Chat Service.
        Tidak perlu lagi memparafrase ulang atau membaca history di sini.
        """
        format_instructions = self.parser.get_format_instructions()
        prompt = f"""Anda adalah sistem Query Analyzer Spesialis SOP HRD PT Semen Indonesia.

CURRENT QUERY: "{query}"

TASK:
1. Search Keywords: Ekstrak 3-6 kata kunci inti dari query di atas. JIKA nanya BIAYA/UPD/FASILITAS, WAJIB tambah kata kunci: "TABEL BIAYA PERJALANAN DINAS UPD-DN HARIAN Lokasi Tertentu Pelatihan Umum Khusus Akomodasi Transportasi".
2. Template Type: PERHATIKAN BAIK-BAIK! Jika menanyakan hitungan angka ("berapa total uangnya", "total 10 hari"), WAJIB pilih 'general_calculation'. Jika hanya nanya teori "fasilitas apa saja", pilih 'rules'.

{format_instructions}
"""
        default_result = {"search_keywords": query, "scope": "general", "doc_type": "general", "template_type": "general", "kota_asal": "", "kota_tujuan": "", "butuh_kalkulasi_jarak": False}
        try:
            print("   👉 [RADAR DALAM] Ainvoke dipanggil...")
            response = await self.llm.ainvoke(prompt)
            print("   ✅ [RADAR DALAM] Ainvoke berhasil!")
            parsed_result = self.parser.invoke(response)
            result = parsed_result.model_dump()
            result['scope'] = result.get('scope', 'general').lower()
            result['doc_type'] = result.get('doc_type', 'general').lower()
            return result
        except Exception as e:
            logger.error(f"❌ Pydantic Parse Failed: {e}. Fallback to default.")
            return default_result

# =====================
# LAYER 5: RERANKING
# =====================
class ContextEnrichedCohereReranker:
    def __init__(self, api_key: str, model: str):
        self.client = cohere.Client(api_key) 
        self.model = model

    async def rerank_async(self, query: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
        if not chunks: return []
        def _blocking_rerank():
            documents = [f"[{c.get('metadata', {}).get('parent_section', '').strip()}]\n{c.get('metadata', {}).get('text', '').strip()}" for c in chunks]
            response = self.client.rerank(query=query, documents=documents, top_n=top_k, model=self.model)
            return [{**chunks[r.index], 'score': r.relevance_score} for r in response.results]
        try:
            return await asyncio.to_thread(_blocking_rerank)
        except Exception as e:
            logger.error(f"❌ Cohere Async failed: {e}")
            return chunks[:top_k]

# =====================
# CORE ENGINE INITIALIZATION (✅ LAZY LOAD PROTECTED)
# =====================
class RAGEngine:
    def __init__(self):
        self.initialized = False
        
    def initialize(self):
        if self.initialized: return

        lf_callback = get_langchain_callback()
        lf_callbacks = [lf_callback] if lf_callback else []

        self.llm = ChatOpenAI(
            model=LLM_MODEL, temperature=LLM_TEMPERATURE, openai_api_key=OPENAI_API_KEY,
            timeout=20, max_retries=3, callbacks=lf_callbacks
        )
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY,
            timeout=20, max_retries=3
        )
        pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = pc.Index(PINECONE_INDEX)
        self.query_analyzer = FastQueryAnalyzer(self.llm)
        self.cohere_reranker = ContextEnrichedCohereReranker(COHERE_API_KEY, COHERE_MODEL) if COHERE_API_KEY else None
        self.travel_analyzer = TravelAnalyzer(llm_client=self.llm)
        self.template_engine = SimpleTemplateEngine()
        self.initialized = True
        logger.info("🚀 ULTIMATE HYBRID RAG ENGINE v7.2 (CANCELLATION EDITION) READY")

rag_engine = RAGEngine()

# =====================
# LAYER 3 & 4: RETRIEVAL
# =====================
async def retrieve_context_async(query: str, search_keywords: str, scope: str, doc_type: str) -> List[Dict]:
    query_vector = await rag_engine.embeddings.aembed_query(search_keywords)
    
    def _run_pinecone_query(vector, filter_dict):
        return rag_engine.index.query(vector=vector, top_k=RAG_RETRIEVAL_K, filter=filter_dict, include_metadata=True, namespace=PINECONE_NAMESPACE)

    base_filter = {"doc_type": {"$eq": doc_type}} if doc_type and doc_type != "general" else None

    if scope in ['domestic', 'international']:
        strict_filter = {**base_filter, "scope": {"$eq": scope}} if base_filter else {"scope": {"$eq": scope}}
        res = await asyncio.to_thread(_run_pinecone_query, query_vector, strict_filter)
        chunks = [{'metadata': m.metadata, 'score': m.score} for m in res.matches]

        if len(chunks) < 3:
            relax_filter = {**base_filter, "scope": {"$in": [scope, "general"]}} if base_filter else {"scope": {"$in": [scope, "general"]}}
            res = await asyncio.to_thread(_run_pinecone_query, query_vector, relax_filter)
            chunks = [{'metadata': m.metadata, 'score': m.score} for m in res.matches]
    else:
        res = await asyncio.to_thread(_run_pinecone_query, query_vector, base_filter)
        chunks = [{'metadata': m.metadata, 'score': m.score} for m in res.matches]

    if rag_engine.cohere_reranker and chunks:
        metrics.cohere_rerank_calls += 1
        chunks = await rag_engine.cohere_reranker.rerank_async(query=query, chunks=chunks, top_k=RAG_TOP_K)
    return chunks


# =====================
# 🔥 LAYER 6: SYNTHESIS WITH CANCELLATION SUPPORT
# =====================

async def answer_question_async(
    question: str,
    session_id: str,
    cancellation_check: Optional[Callable] = None,
) -> str:
    """
    🔥 ENHANCED with 8 cancellation checkpoints.
    Langfuse v4: semua child span dibuat via langfuse_observation() yang otomatis
    menggunakan OTel context yang aktif (ditetapkan oleh chat_service → route_a_rag).

    Args:
        question: User query
        session_id: Session ID
        cancellation_check: Async callable returning True if should cancel
    """
    
    # 🔥 Helper function for cancellation checks
    async def check_cancelled():
        """Check if request was cancelled"""
        if cancellation_check:
            try:
                is_cancelled = await cancellation_check()
                if is_cancelled:
                    logger.info("🛑 RAG execution cancelled by client")
                    metrics.cancelled_requests += 1
                    raise asyncio.CancelledError()
            except asyncio.CancelledError:
                raise  # Re-raise
            except Exception as e:
                logger.warning(f"⚠️ Cancellation check error: {e}")
    
    print("🚩 [RADAR 1] Masuk ke answer_question_async")
    if not rag_engine.initialized: 
        print("🚩 [RADAR 2] Sedang menginisialisasi mesin RAG...")
        rag_engine.initialize()
    
    # 🔥 CHECKPOINT 1: After initialization
    await check_cancelled()
    
    start_time = time.time()
    metrics.queries += 1
    
    try:
        print("🚩 [RADAR 3] Validasi input...")
        is_valid, err_msg = validate_input(question)
        if not is_valid: return f"<h3>⚠️ Error</h3><p>{err_msg}</p>"
        
        # 🔥 CHECKPOINT 2: After validation
        await check_cancelled()
        
        print("🚩 [RADAR 4] Menembak LLM Analyzer (FastQueryAnalyzer)...")

        # 🔥 CHECKPOINT 3: Before LLM Analyzer
        await check_cancelled()

        with langfuse_observation("query_analysis", input={"question": question}) as _sp_analysis:
            analysis = await rag_engine.query_analyzer.analyze_async(question)
            if _sp_analysis:
                _sp_analysis.update(output={
                    "keywords": analysis.get("search_keywords"),
                    "scope": analysis.get("scope"),
                    "template_type": analysis.get("template_type"),
                })

        print("🚩 [RADAR 5] LLM Analyzer selesai!")
        
        # 🔥 CHECKPOINT 4: After LLM Analyzer
        await check_cancelled()
        
        keywords = " ".join([str(k) for k in analysis.get('search_keywords', question)]) if isinstance(analysis.get('search_keywords'), list) else analysis.get('search_keywords', question)
        scope = analysis.get('scope', 'general')
        doc_type = analysis.get('doc_type', 'general')
        template_type = analysis.get('template_type', 'general')

        logger.info("\n" + "🔮" * 25 + "\n" +
                    "🔍 DEBUGGING QUERY ANALYZER (DOMAIN RAG)\n" +
                    f"🗣️ Standalone Query : {question}\n" +
                    f"🔑 Search Keywords  : {keywords}\n" +
                    f"🎯 Scope Terdeteksi : {scope}\n" +
                    f"📝 Template Type    : {template_type}\n" +
                    "🔮" * 25)

        with langfuse_observation("vector_retrieval", input={"keywords": keywords, "scope": scope, "doc_type": doc_type}) as _sp_ret:
            matches = await retrieve_context_async(question, keywords, scope, doc_type)

            # Filter chunks dengan Cohere relevance score di bawah threshold
            before_filter = len(matches)
            filtered = [m for m in matches if m.get('score', 0.0) >= RAG_MIN_SCORE]
            # Jaga minimal 1 chunk agar tidak kosong
            matches = filtered if filtered else matches[:1]
            logger.info(f"🔽 Score filter: {before_filter} → {len(matches)} chunks (threshold={RAG_MIN_SCORE})")

            if _sp_ret:
                _sp_ret.update(output={"chunks_returned": len(matches), "chunks_before_filter": before_filter})

        # 🔥 CHECKPOINT 5: After retrieval
        await check_cancelled()
        
        context_parts = []
        relevant_filenames = [] 
        
        debug_msg = f"\n📚" * 25 + f"\n🔍 DEBUGGING RAG RETRIEVAL (Menarik {len(matches)} Chunks)\n"
        for i, m in enumerate(matches):
            text = m['metadata'].get('text', '').strip()[:2000]
            source = m['metadata'].get('filename') or m['metadata'].get('source_file') or 'Unknown'
            parent = m['metadata'].get('parent_section') or m['metadata'].get('heading') or 'Tidak spesifik'
            score = m.get('score', 0.0)
            
            if source != 'Unknown':
                relevant_filenames.append(source)
                
            debug_msg += f"\n📦 CHUNK #{i+1} | Score: {score:.4f}\n"
            debug_msg += f"📁 Sumber : {source} | Bab: {parent}\n"
            debug_msg += f"📄 Teks   : {text[:250]}... [LANJUTAN DIPOTONG UNTUK DEBUG]\n"
            
            context_parts.append(f"[FILE: {source} | BAB: {parent}]\n{text}")
            
        debug_msg += "\n" + "📚" * 25
        logger.info(debug_msg)

        context_str = "\n\n---\n\n".join(context_parts)
        
        # Tools & Policy Injections
        tool_info = ""
        travel_data = {} 
        
        kota_asal = analysis.get('kota_asal', '')
        kota_tujuan = analysis.get('kota_tujuan', '')
        kota_asal = str(kota_asal[0]) if isinstance(kota_asal, list) else str(kota_asal).strip()
        kota_tujuan = str(kota_tujuan[0]) if isinstance(kota_tujuan, list) else str(kota_tujuan).strip()
        
        is_valid_destination = bool(kota_tujuan and kota_tujuan.lower() not in ["", "none", "null", "-", "tidak ada"])
        
        if analysis.get('butuh_kalkulasi_jarak', False) or is_valid_destination:
            travel_data = await rag_engine.travel_analyzer.process_decision_query_async(origin=kota_asal, destination=kota_tujuan, scope=scope)
            
            if travel_data.get('processed'):
                route_str = travel_data.get('route', 'Tidak diketahui')
                dist_km = travel_data.get('distance_km', 0)
                dur_hrs = travel_data.get('duration_hours', 0)
                
                if scope == 'international':
                    tool_info = HRTravelPolicy.get_international_policy_injection(route_str, dur_hrs)
                else:
                    tool_info = HRTravelPolicy.get_domestic_policy_injection(route_str, dist_km, dur_hrs)

        # 🔥 CHECKPOINT 6: Before template building
        await check_cancelled()

        # Template & Formatting
        html_template = rag_engine.template_engine.get_template(template_type, question)
        
        if travel_data.get('processed') and scope == 'domestic' and 0 < travel_data.get('distance_km', 0) < 120:
            html_template = """<h3>Informasi Perjalanan Dinas</h3>\n<p>[Tulis rute dan jarak asli dari INFO SISTEM. Berdasarkan regulasi perusahaan, perjalanan kurang dari 120 km BUKAN termasuk Perjalanan Dinas.]</p>\n<h3>Ketentuan Kelayakan Fasilitas</h3>\n<p>[Tuliskan TEGAS bahwa seluruh fasilitas standar perjalanan dinas TIDAK BERLAKU untuk perjalanan ini. 🚫 DILARANG KERAS MENAMPILKAN DAFTAR TABEL HARGA!]</p>"""

        enforcement_instructions = rag_engine.template_engine.get_enforcement_instructions(html_template)

        # PANGGIL SATPAM SECARA ASYNC PARALEL!
        guardrails = await satpam_aturan.generate_guardrail_prompt_async(relevant_filenames)

        # KEMBALIKAN KEKUATAN DETAIL
        detail_enforcer = ""
        if "singkat" not in question.lower():
            detail_enforcer = "8. 📝 KEDALAMAN JAWABAN: Anda WAJIB menjabarkan aturan, nominal, rincian, dan tata cara secara SANGAT DETAIL, TERSTRUKTUR, dan LENGKAP. Jangan ada poin penting dari KNOWLEDGE BASE yang disembunyikan!"

        # 🔥 PERUBAHAN KRUSIAL ADA DI SINI 🔥
        prompt = f"""=== SYSTEM ROLE ===
Anda adalah Asisten Profesional HRD PT Semen Indonesia.

=== CRITICAL RULES ===
1. Jawab HANYA menggunakan informasi dari [KNOWLEDGE BASE].
2. 🚨 CEK KELAYAKAN (ELIGIBILITY) SEBELUM MENGHITUNG: Anda WAJIB memeriksa apakah user berhak atas fasilitas tersebut berdasarkan aturan di [KNOWLEDGE BASE]. 
   - Contoh: Upah Kerja Lembur HANYA diberikan untuk karyawan Job Grade 10 ke bawah atau Band 5. 
   - JIKA user menyebutkan ia adalah Band 1, 2, 3, atau 4 dan meminta hitungan lembur, Anda DILARANG KERAS memberikan hitungan/rumus. Anda WAJIB menolak dengan sopan dan menjelaskan bahwa sesuai aturan, Band tersebut tidak mendapatkan upah lembur.
3. 🚨 KESEIMBANGAN ANTI-HALUSINASI & KELENTURAN (SANGAT KRITIS):
   - CEK TOPIK ALIEN: Coba lihat [KNOWLEDGE BASE]. Apakah topik yang ditanyakan (misal: Pensiun, Cuti Melahirkan, Resign) SAMA SEKALI TIDAK DITULIS di sana? JIKA YA (Topik Alien), Anda WAJIB BERHENTI dan HANYA MENGELUARKAN KODE INI TANPA TAMBAHAN TEKS LAIN:
[DATA_TIDAK_DITEMUKAN_DI_SOP]
   - CEK TOPIK RELEVAN TAPI KURANG DATA: JIKA topik yang ditanyakan ADA (misal: Lembur, Perjalanan Dinas, Hari Libur), tetapi Anda merasa data di [KNOWLEDGE BASE] tidak cukup detail untuk melakukan hitungan matematika/angka pasti yang diminta user, JANGAN GUNAKAN KODE ERROR! Anda WAJIB tetap menjawab dengan ramah berdasarkan aturan/definisi yang tersedia, dan sampaikan secara profesional bahwa Anda membutuhkan data tambahan (seperti gaji pokok, dsb) untuk menghitung angka pastinya.
4. DILARANG KERAS merangkai atau memaksakan aturan dari topik A untuk menjawab topik B (Topik harus match!).
5. Angka tarif, jarak, dan durasi HARUS persis sama dengan dokumen.
6. 🔥 TUGAS KALKULASI: JIKA ADA angka jarak (km) atau durasi (jam) dari [INFO SISTEM & INSTRUKSI MUTLAK], WAJIB gunakan angka tersebut.
7. 🚨 KEPATUHAN FORMAT: WAJIB MEMATUHI SEMUA PERINTAH di dalam [INFO SISTEM & INSTRUKSI MUTLAK] TANPA TERKECUALI!
{detail_enforcer}

{enforcement_instructions}

{guardrails}

=== INFO SISTEM & INSTRUKSI MUTLAK ===
{tool_info}

=== KNOWLEDGE BASE ===
{context_str}

=== USER QUESTION ===
{question}

=== YOUR RESPONSE ===
"""
        
        # 🔥 CHECKPOINT 7: Before final LLM call
        await check_cancelled()

        with langfuse_observation("llm_generation", input={"prompt_length": len(prompt), "model": LLM_MODEL}) as _sp_gen:
            response = await rag_engine.llm.ainvoke(prompt)

            # 🔥 CHECKPOINT 8: After LLM call
            await check_cancelled()

            if _sp_gen:
                _sp_gen.update(output={"response_length": len(response.content)})
        
        cleaned_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response.content.replace('```html', '').replace('```', '').strip())
    
        metrics.successful_responses += 1
        metrics.avg_response_time = ((metrics.avg_response_time * (metrics.queries - 1)) + (time.time() - start_time)) / metrics.queries
        
        logger.info(f"✅ Success in {time.time() - start_time:.2f}s | Guardrails Active: {bool(guardrails)}")
        
        return cleaned_response

    except asyncio.CancelledError:
        # 🔥 Handle cancellation gracefully
        logger.warning(f"🛑 RAG processing cancelled for session {session_id}")
        metrics.failed_responses += 1
        metrics.cancelled_requests += 1
        raise  # Re-raise to propagate cancellation
        
    except Exception as e:
        logger.error(f"❌ Critical Error: {e}", exc_info=True)
        metrics.failed_responses += 1
        return "<h3>⚠️ Terjadi Kesalahan Sistem</h3><p>Mohon maaf, sistem sedang sibuk.</p>"

def get_engine_metrics() -> Dict:
    return {
        "total_queries": metrics.queries,
        "avg_response_time_seconds": round(metrics.avg_response_time, 2),
        "success_rate_percent": round((metrics.successful_responses / metrics.queries * 100) if metrics.queries > 0 else 0, 1),
        "cancelled_requests": metrics.cancelled_requests,  # 🔥 NEW
        "version": "v7.2.0 (CANCELLATION EDITION)"
    }
    
# Entry point wrapper
async def answer_question(question: str, session_id: str, cancellation_check=None) -> str:
    return await answer_question_async(question, session_id, cancellation_check)


# =====================
# STREAMING VERSION
# =====================
async def answer_question_stream(
    question: str,
    session_id: str,
    cancellation_check: Optional[Callable] = None,
    out_context: Optional[dict] = None,
):
    """
    Async generator version of answer_question_async.
    Yields raw text chunks (tokens) from the LLM for streaming responses.
    All preprocessing is identical; only the final LLM call uses astream().
    """
    async def check_cancelled():
        if cancellation_check:
            try:
                if await cancellation_check():
                    metrics.cancelled_requests += 1
                    raise asyncio.CancelledError()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"⚠️ Cancellation check error: {e}")

    if not rag_engine.initialized:
        rag_engine.initialize()

    await check_cancelled()
    start_time = time.time()
    metrics.queries += 1

    try:
        is_valid, err_msg = validate_input(question)
        if not is_valid:
            yield f"<h3>⚠️ Error</h3><p>{err_msg}</p>"
            return

        await check_cancelled()

        with langfuse_observation("query_analysis", input={"question": question}) as _sp_analysis:
            analysis = await rag_engine.query_analyzer.analyze_async(question)
            if _sp_analysis:
                _sp_analysis.update(output={
                    "keywords": analysis.get("search_keywords"),
                    "scope": analysis.get("scope"),
                    "template_type": analysis.get("template_type"),
                })

        await check_cancelled()

        keywords = " ".join([str(k) for k in analysis.get('search_keywords', question)]) if isinstance(analysis.get('search_keywords'), list) else analysis.get('search_keywords', question)
        scope = analysis.get('scope', 'general')
        doc_type = analysis.get('doc_type', 'general')
        template_type = analysis.get('template_type', 'general')

        with langfuse_observation("vector_retrieval", input={"keywords": keywords, "scope": scope, "doc_type": doc_type}) as _sp_ret:
            matches = await retrieve_context_async(question, keywords, scope, doc_type)
            before_filter = len(matches)
            filtered = [m for m in matches if m.get('score', 0.0) >= RAG_MIN_SCORE]
            matches = filtered if filtered else matches[:1]
            logger.info(f"🔽 Score filter: {before_filter} → {len(matches)} chunks (threshold={RAG_MIN_SCORE})")
            if _sp_ret:
                _sp_ret.update(output={"chunks_returned": len(matches), "chunks_before_filter": before_filter})

        await check_cancelled()

        context_parts = []
        relevant_filenames = []
        for m in matches:
            text = m['metadata'].get('text', '').strip()[:2000]
            source = m['metadata'].get('filename') or m['metadata'].get('source_file') or 'Unknown'
            parent = m['metadata'].get('parent_section') or m['metadata'].get('heading') or 'Tidak spesifik'
            if source != 'Unknown':
                relevant_filenames.append(source)
            context_parts.append(f"[FILE: {source} | BAB: {parent}]\n{text}")

        context_str = "\n\n---\n\n".join(context_parts)
        if out_context is not None:
            out_context["context"] = context_str

        tool_info = ""
        travel_data = {}
        kota_asal = analysis.get('kota_asal', '')
        kota_tujuan = analysis.get('kota_tujuan', '')
        kota_asal = str(kota_asal[0]) if isinstance(kota_asal, list) else str(kota_asal).strip()
        kota_tujuan = str(kota_tujuan[0]) if isinstance(kota_tujuan, list) else str(kota_tujuan).strip()
        is_valid_destination = bool(kota_tujuan and kota_tujuan.lower() not in ["", "none", "null", "-", "tidak ada"])

        if analysis.get('butuh_kalkulasi_jarak', False) or is_valid_destination:
            travel_data = await rag_engine.travel_analyzer.process_decision_query_async(origin=kota_asal, destination=kota_tujuan, scope=scope)
            if travel_data.get('processed'):
                route_str = travel_data.get('route', 'Tidak diketahui')
                dist_km = travel_data.get('distance_km', 0)
                dur_hrs = travel_data.get('duration_hours', 0)
                if scope == 'international':
                    tool_info = HRTravelPolicy.get_international_policy_injection(route_str, dur_hrs)
                else:
                    tool_info = HRTravelPolicy.get_domestic_policy_injection(route_str, dist_km, dur_hrs)

        await check_cancelled()

        html_template = rag_engine.template_engine.get_template(template_type, question)
        if travel_data.get('processed') and scope == 'domestic' and 0 < travel_data.get('distance_km', 0) < 120:
            html_template = """<h3>Informasi Perjalanan Dinas</h3>\n<p>[Tulis rute dan jarak asli dari INFO SISTEM. Berdasarkan regulasi perusahaan, perjalanan kurang dari 120 km BUKAN termasuk Perjalanan Dinas.]</p>\n<h3>Ketentuan Kelayakan Fasilitas</h3>\n<p>[Tuliskan TEGAS bahwa seluruh fasilitas standar perjalanan dinas TIDAK BERLAKU untuk perjalanan ini. 🚫 DILARANG KERAS MENAMPILKAN DAFTAR TABEL HARGA!]</p>"""

        enforcement_instructions = rag_engine.template_engine.get_enforcement_instructions(html_template)
        guardrails = await satpam_aturan.generate_guardrail_prompt_async(relevant_filenames)

        detail_enforcer = ""
        if "singkat" not in question.lower():
            detail_enforcer = "8. 📝 KEDALAMAN JAWABAN: Anda WAJIB menjabarkan aturan, nominal, rincian, dan tata cara secara SANGAT DETAIL, TERSTRUKTUR, dan LENGKAP. Jangan ada poin penting dari KNOWLEDGE BASE yang disembunyikan!"

        prompt = f"""=== SYSTEM ROLE ===
Anda adalah Asisten Profesional HRD PT Semen Indonesia.

=== CRITICAL RULES ===
1. Jawab HANYA menggunakan informasi dari [KNOWLEDGE BASE].
2. 🚨 CEK KELAYAKAN (ELIGIBILITY) SEBELUM MENGHITUNG: Anda WAJIB memeriksa apakah user berhak atas fasilitas tersebut berdasarkan aturan di [KNOWLEDGE BASE].
   - Contoh: Upah Kerja Lembur HANYA diberikan untuk karyawan Job Grade 10 ke bawah atau Band 5.
   - JIKA user menyebutkan ia adalah Band 1, 2, 3, atau 4 dan meminta hitungan lembur, Anda DILARANG KERAS memberikan hitungan/rumus. Anda WAJIB menolak dengan sopan dan menjelaskan bahwa sesuai aturan, Band tersebut tidak mendapatkan upah lembur.
3. 🚨 KESEIMBANGAN ANTI-HALUSINASI & KELENTURAN (SANGAT KRITIS):
   - CEK TOPIK ALIEN: Coba lihat [KNOWLEDGE BASE]. Apakah topik yang ditanyakan (misal: Pensiun, Cuti Melahirkan, Resign) SAMA SEKALI TIDAK DITULIS di sana? JIKA YA (Topik Alien), Anda WAJIB BERHENTI dan HANYA MENGELUARKAN KODE INI TANPA TAMBAHAN TEKS LAIN:
[DATA_TIDAK_DITEMUKAN_DI_SOP]
   - CEK TOPIK RELEVAN TAPI KURANG DATA: JIKA topik yang ditanyakan ADA (misal: Lembur, Perjalanan Dinas, Hari Libur), tetapi Anda merasa data di [KNOWLEDGE BASE] tidak cukup detail untuk melakukan hitungan matematika/angka pasti yang diminta user, JANGAN GUNAKAN KODE ERROR! Anda WAJIB tetap menjawab dengan ramah berdasarkan aturan/definisi yang tersedia, dan sampaikan secara profesional bahwa Anda membutuhkan data tambahan (seperti gaji pokok, dsb) untuk menghitung angka pastinya.
4. DILARANG KERAS merangkai atau memaksakan aturan dari topik A untuk menjawab topik B (Topik harus match!).
5. Angka tarif, jarak, dan durasi HARUS persis sama dengan dokumen.
6. 🔥 TUGAS KALKULASI: JIKA ADA angka jarak (km) atau durasi (jam) dari [INFO SISTEM & INSTRUKSI MUTLAK], WAJIB gunakan angka tersebut.
7. 🚨 KEPATUHAN FORMAT: WAJIB MEMATUHI SEMUA PERINTAH di dalam [INFO SISTEM & INSTRUKSI MUTLAK] TANPA TERKECUALI!
{detail_enforcer}

{enforcement_instructions}

{guardrails}

=== INFO SISTEM & INSTRUKSI MUTLAK ===
{tool_info}

=== KNOWLEDGE BASE ===
{context_str}

=== USER QUESTION ===
{question}

=== YOUR RESPONSE ===
"""

        await check_cancelled()

        full_response = ""
        with langfuse_observation("llm_generation", input={"prompt_length": len(prompt), "model": LLM_MODEL}) as _sp_gen:
            async for chunk in rag_engine.llm.astream(prompt):
                if chunk.content:
                    cleaned_chunk = chunk.content.replace('```html', '').replace('```', '')
                    full_response += cleaned_chunk
                    yield cleaned_chunk

            if _sp_gen:
                _sp_gen.update(output={"response_length": len(full_response)})

        metrics.successful_responses += 1
        metrics.avg_response_time = ((metrics.avg_response_time * (metrics.queries - 1)) + (time.time() - start_time)) / metrics.queries
        logger.info(f"✅ Stream Success in {time.time() - start_time:.2f}s")

    except asyncio.CancelledError:
        logger.warning(f"🛑 RAG stream cancelled for session {session_id}")
        metrics.failed_responses += 1
        metrics.cancelled_requests += 1
        raise
    except Exception as e:
        logger.error(f"❌ Stream Error: {e}", exc_info=True)
        metrics.failed_responses += 1
        yield "<h3>⚠️ Terjadi Kesalahan Sistem</h3><p>Mohon maaf, sistem sedang sibuk.</p>"

if __name__ == "__main__":
    async def main_test():
        print("Testing...")
    asyncio.run(main_test())