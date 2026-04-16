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
from engines.sop.utils.currency import get_usd_idr_rate

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
    if len(question) > 2000:
        return False, "Pertanyaan terlalu panjang (maksimal 2000 karakter)."
    return True, ""


# =====================
# LAYER 2: QUERY UNDERSTANDING (Robust Pydantic & Async)
# =====================
class QuerySchema(BaseModel):
    sop_topic: str = Field(description="""LANGKAH PERTAMA — Identifikasi topik SOP mana yang paling relevan.
Pilih TEPAT SATU dari daftar berikut berdasarkan ISI pertanyaan, BUKAN nama kota/angka:
- 'perjalanan_dinas'   : perjalanan dinas, business trip, UPD, uang harian dinas, transportasi dinas
- 'lembur'             : lembur, overtime, upah kerja lembur, jam lembur
- 'pembelajaran'       : pelatihan, training, sertifikasi, pembelajaran, beasiswa
- 'relokasi'           : relokasi, penempatan, pindah, mutasi, POH, POA, fasilitas pindah, biaya pindah
- 'tunjangan'          : tunjangan domisili, bantuan sewa rumah, ongkos pindah, tunjangan jabatan, THR, remunerasi, fasilitas alat kerja, fasilitas komunikasi, sumbangan perkawinan
- 'karir'              : manajemen karir, promosi, rotasi, pengembangan karir, kompetensi, kinerja, talenta, evaluasi jabatan, suksesi
- 'phk'                : PHK, pemutusan hubungan kerja, pesangon, pensiun, terminasi, dana pensiun
- 'cuti'               : cuti tahunan, cuti sakit, cuti melahirkan, dispensasi, izin tidak masuk
- 'kesehatan'          : fasilitas kesehatan, BPJS kesehatan, BPJS ketenagakerjaan, asuransi kesejahteraan, employee well-being, manfaat kesehatan
- 'rumah_dinas'        : rumah dinas, penghunian rumah dinas, fasilitas hunian, listrik rumah dinas
- 'disiplin'           : disiplin karyawan, surat peringatan, pelanggaran, whistleblowing, RWP, respectful workplace, perilaku kerja
- 'general'            : topik lain yang tidak masuk kategori di atas
""")
    search_keywords: str = Field(description="""Kata kunci pencarian Vector DB. WAJIB ikuti aturan ini:
- Selalu sertakan nama topik SOP (dari sop_topic) sebagai kata kunci pertama.
- Contoh: sop_topic='relokasi' → keywords dimulai dengan 'relokasi penempatan karyawan ...'
- Contoh: sop_topic='perjalanan_dinas' → keywords dimulai dengan 'perjalanan dinas UPD ...'
- Tambahkan detail spesifik dari pertanyaan setelahnya (band, nominal, fasilitas, dll).
- JIKA ada prefix '[..., Band: <angka>, ...]' dalam query, WAJIB sertakan 'Band <angka>' dalam keywords (contoh: 'perjalanan dinas Band 3 hotel UPD').""")
    user_band: str = Field(default="", description="Ekstrak angka band user dari prefix konteks '[..., Band: <angka>, ...]' jika ada. Contoh: '[Band: 3]' → '3'. Kosongkan jika tidak ada prefix band.")
    scope: str = Field(description="Pilih HANYA SALAH SATU: domestic, international, atau general")
    doc_type: str = Field(default="general", description="Selalu isi 'general'. Field ini tidak digunakan sebagai filter — hanya dipertahankan untuk kompatibilitas schema.")
    template_type: str = Field(description="""Pilih HANYA SALAH SATU:
- 'general_calculation': JIKA nanya hitungan angka, total uang, UPD, tarif, atau jumlah biaya.
- 'procedure': JIKA nanya 'cara', 'langkah-langkah', 'bagaimana mengajukan'.
- 'rules': JIKA nanya syarat, kelayakan (Yes/No), atau 'dapat apa aja/fasilitas apa aja'.
- 'definition': JIKA nanya apa itu/definisi.
- 'general': Jika tidak masuk kategori di atas.""")
    kota_asal: str = Field(default="", description="Ekstrak kota_asal JIKA ADA dan sop_topic='perjalanan_dinas'. Jika pertanyaan tidak menyebut kota asal secara eksplisit, cek prefix konteks user: jika ada '[...Lokasi saat ini: <kota>...]' maka gunakan <kota> tsb sebagai kota_asal. Kosongkan untuk topik lain.")
    kota_tujuan: str = Field(default="", description="Ekstrak kota_tujuan JIKA ADA dan sop_topic='perjalanan_dinas'. Kosongkan untuk topik lain.")
    butuh_kalkulasi_jarak: bool = Field(description="TRUE HANYA JIKA sop_topic='perjalanan_dinas' DAN pertanyaan menanyakan biaya/fasilitas perjalanan ke kota tertentu (kota_tujuan terdeteksi). FALSE untuk semua topik lain termasuk relokasi.")

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

TUGAS UTAMA:
LANGKAH 1 — Tentukan sop_topic: Baca pertanyaan dengan cermat. Identifikasi topik SOP mana yang ditanyakan.
  ⚠️ PERHATIAN: Adanya nama kota (Gresik, Jakarta, dll) TIDAK otomatis berarti perjalanan dinas!
  - Jika ada kata "penempatan", "pindah", "mutasi", "relokasi" → sop_topic = 'relokasi'
  - Jika ada kata "perjalanan dinas", "UPD", "dinas ke", "uang harian" → sop_topic = 'perjalanan_dinas'

LANGKAH 2 — Buat search_keywords: Mulai dengan nama topik SOP, lalu tambahkan detail dari pertanyaan.
  JIKA nanya BIAYA PERJALANAN DINAS: WAJIB tambah "TABEL BIAYA PERJALANAN DINAS UPD-DN HARIAN".
  ⚠️ UNTUK sop_topic='perjalanan_dinas': JANGAN PERNAH masukkan nama kota (Jakarta, Surabaya, dll) ke keywords!
  Nama kota sudah ditangani di field kota_asal/kota_tujuan — bukan di keywords.
  Keywords harus fokus pada KONTEN dokumen: tarif, band, fasilitas, UPD, hotel, akomodasi.

LANGKAH 3 — Ekstrak konteks user dari prefix (jika ada pola "[Nama: X, Band: Y, Lokasi saat ini: Z]"):
  - user_band: angka band dari prefix, contoh "[Band: 3]" → user_band = "3"
  - Sertakan "Band <angka>" dalam search_keywords jika sop_topic = 'perjalanan_dinas' atau topik tunjangan/fasilitas

LANGKAH 4 — Isi field kota_asal dan kota_tujuan (hanya untuk sop_topic='perjalanan_dinas'):
  - kota_tujuan: kota yang disebut setelah "ke", "menuju", "tujuan", "di" dalam konteks dinas.
  - kota_asal: kota yang disebut setelah "dari", "berangkat dari" DALAM TEKS PERTANYAAN,
    ATAU — jika tidak ada dalam teks — ambil dari prefix konteks user jika ada pola "[..., Lokasi saat ini: <kota>, ...]".
    Contoh 1: query "perjalanan dinas dari Jakarta ke Surabaya fasilitas apa"
    → kota_asal = "Jakarta", kota_tujuan = "Surabaya"
    → search_keywords = "perjalanan dinas hotel fasilitas UPD"  (JANGAN masukkan nama kota ke keywords!)
    Contoh 2: query "[Nama: RAHMAD, Band: 3, Lokasi saat ini: Jakarta] dinas ke Surabaya"
    → user_band = "3", kota_asal = "Jakarta", kota_tujuan = "Surabaya"
    → search_keywords = "perjalanan dinas Band 3 hotel fasilitas UPD"  (nama kota TIDAK perlu di keywords)

LANGKAH 5 — Isi field lainnya sesuai panduan di setiap field.

{format_instructions}
"""
        default_result = {"sop_topic": "general", "search_keywords": query, "scope": "general", "doc_type": "general", "template_type": "general", "kota_asal": "", "kota_tujuan": "", "butuh_kalkulasi_jarak": False}
        try:
            print("   👉 [RADAR DALAM] Ainvoke dipanggil...")
            response = await self.llm.ainvoke(prompt)
            print("   ✅ [RADAR DALAM] Ainvoke berhasil!")
            parsed_result = self.parser.invoke(response)
            result = parsed_result.model_dump()
            result['scope'] = result.get('scope', 'general').lower()
            result['doc_type'] = result.get('doc_type', 'general').lower()
            logger.info(f"🏷️  sop_topic: {result.get('sop_topic')} | doc_type: {result.get('doc_type')}")
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
            timeout=30, max_retries=1, callbacks=lf_callbacks
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
# LAYER 3 & 4: RETRIEVAL (Multi-Query)
# =====================
async def _generate_multi_queries(question: str, sop_topic: str) -> List[str]:
    """Generate 3 alternative search queries: aspect-expanded and synonym variation."""
    prompt = f"""Kamu adalah asisten pencarian dokumen regulasi HR perusahaan.
Tugasmu: buat TEPAT 3 query pencarian LENGKAP dan BERBEDA ASPEK dari pertanyaan berikut.

Topik: {sop_topic}
Pertanyaan: {question}

Panduan:
1. [ASPEK LENGKAP] Setiap query harus menyebutkan aspek yang LEBIH SPESIFIK dan LENGKAP dari pertanyaan asli.
   Contoh topik perjalanan_dinas: satu query tentang tarif hotel/akomodasi per Band jabatan,
   satu tentang uang harian (UPD) dan kategorinya, satu tentang transportasi dan biaya lain.
2. [SINONIM FORMAL] Gunakan istilah yang lazim di dokumen regulasi/SK Direksi.
   Contoh: "hotel" → "plafon akomodasi" / "tarif penginapan per Band"
   Contoh: "uang jalan" → "Uang Perjalanan Dinas Dalam Negeri (UPD-DN)"
3. [ENTITAS LENGKAP] Gunakan nama entitas/jabatan secara lengkap dan spesifik.
4. [ANTI FABRIKASI] Jika user TIDAK menyebut pasal, nomor SK, atau tahun, JANGAN menambahkannya.

Tulis HANYA 3 baris, satu query per baris, tanpa nomor atau label apapun."""
    try:
        response = await rag_engine.llm.ainvoke(prompt)
        queries = [q.strip() for q in response.content.strip().split('\n') if q.strip()][:3]
        logger.info(f"🔀 Multi-query alternatives: {queries}")
        return queries
    except Exception as e:
        logger.warning(f"⚠️ Multi-query generation failed: {e}. Fallback to single query.")
        return []


async def retrieve_context_async(query: str, search_keywords: str, scope: str, sop_topic: str = "general") -> List[Dict]:
    # Step 1: Generate alternative queries + embed primary secara paralel
    alt_queries, primary_vector = await asyncio.gather(
        _generate_multi_queries(query, sop_topic),
        rag_engine.embeddings.aembed_query(search_keywords)
    )

    # Step 2: Embed alternative queries secara paralel
    # Untuk perjalanan_dinas, tambahkan guaranteed query untuk tabel hotel + UPD
    # agar chunk tarif akomodasi per Band selalu masuk pool Pinecone (bukan LLM call)
    _guaranteed_queries: List[str] = []
    if sop_topic == 'perjalanan_dinas':
        _guaranteed_queries = [
            "tabel tarif plafon hotel akomodasi per Band jabatan perjalanan dinas dalam negeri",
            "TABEL BIAYA PERJALANAN DINAS UPD-DN HARIAN kategori nominal per hari",
        ]

    embed_tasks = [rag_engine.embeddings.aembed_query(q) for q in alt_queries + _guaranteed_queries]
    all_extra_vectors = list(await asyncio.gather(*embed_tasks)) if embed_tasks else []

    alt_vectors = all_extra_vectors[:len(alt_queries)]
    guaranteed_vectors = all_extra_vectors[len(alt_queries):]

    all_vectors = [primary_vector] + alt_vectors + guaranteed_vectors

    def _run_pinecone_query(vector, filter_dict, top_k):
        return rag_engine.index.query(
            vector=vector, top_k=top_k, filter=filter_dict,
            include_metadata=True, namespace=PINECONE_NAMESPACE
        )

    # Step 3: Tentukan filter berdasarkan scope
    if scope in ['domestic', 'international']:
        main_filter = {"scope": {"$eq": scope}}
        fallback_filter = {"scope": {"$in": [scope, "general"]}}
    else:
        main_filter = None
        fallback_filter = None

    # Step 4: Jalankan semua Pinecone query secara paralel
    # Primary pakai RAG_RETRIEVAL_K penuh, alternatif cukup 5 per query
    tasks = [
        asyncio.to_thread(_run_pinecone_query, vec, main_filter, RAG_RETRIEVAL_K if i == 0 else 5)
        for i, vec in enumerate(all_vectors)
    ]
    results = await asyncio.gather(*tasks)

    # Step 5: Fallback scope untuk primary query jika hasil < 3
    primary_matches = results[0].matches
    if scope in ['domestic', 'international'] and len(primary_matches) < 3:
        fallback_res = await asyncio.to_thread(
            _run_pinecone_query, primary_vector, fallback_filter, RAG_RETRIEVAL_K
        )
        primary_matches = fallback_res.matches

    # Step 6: Merge + deduplikasi by vector ID, simpan score tertinggi
    seen: Dict[str, Dict] = {}
    all_matches = list(primary_matches) + [m for res in results[1:] for m in res.matches]
    for m in all_matches:
        vid = m.id
        if vid not in seen or m.score > seen[vid]['score']:
            seen[vid] = {'id': vid, 'metadata': m.metadata, 'score': m.score}

    merged = list(seen.values())
    logger.info(f"🔀 Multi-query: {len(all_vectors)} queries ({len(alt_queries)} LLM alts + {len(_guaranteed_queries)} guaranteed) → {len(merged)} unique chunks sebelum rerank")

    # Step 7: Cohere rerank dari pool yang lebih besar
    if rag_engine.cohere_reranker and merged:
        metrics.cohere_rerank_calls += 1
        _base = f"[Topik: {sop_topic}] {query}" if sop_topic and sop_topic != "general" else query
        _alts = " | ".join(alt_queries) if alt_queries else ""
        rerank_query = f"{_base} | {_alts}" if _alts else _base
        logger.info(f"🔍 Cohere rerank query: {rerank_query}")
        merged = await rag_engine.cohere_reranker.rerank_async(query=rerank_query, chunks=merged, top_k=RAG_TOP_K)

    return merged


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
        _sop_topic_async = analysis.get('sop_topic', 'general')

        # Fallback: kalau LLM tidak inject band ke keywords, ambil dari prefix dan inject manual
        import re as _re_kw
        _band_from_prefix = analysis.get('user_band', '').strip()
        if not _band_from_prefix or _band_from_prefix == "0":
            _band_match = _re_kw.search(r'\[.*?Band:\s*([1-9]\d*)', question)  # hanya angka > 0
            if _band_match:
                _band_from_prefix = _band_match.group(1).strip()
            else:
                _band_from_prefix = ""  # reset jika LLM return "0" (tidak valid)
        # Hanya inject jika band valid (angka > 0) dan belum ada di keywords
        if _band_from_prefix and _band_from_prefix.isdigit() and int(_band_from_prefix) > 0 and f"Band {_band_from_prefix}" not in keywords:
            keywords = f"{keywords} Band {_band_from_prefix}"
            logger.info(f"📍 Band {_band_from_prefix} di-inject ke search keywords")

        # scope filter (domestic/international) hanya relevan untuk perjalanan dinas.
        # Untuk topik lain (relokasi, PHK, karir, dll), Pinecone scope filter akan
        # menyingkirkan dokumen yang di-index dengan scope=general.
        if _sop_topic_async != 'perjalanan_dinas' and scope != 'general':
            logger.info(f"🔧 scope override: '{scope}' → 'general' (sop_topic={_sop_topic_async}, scope filter only for perjalanan dinas)")
            scope = 'general'

        logger.info(
            "\n" + "🔮" * 25 + "\n"
            "🔍 DEBUGGING QUERY ANALYZER (DOMAIN RAG)\n"
            f"🗣️ Standalone Query : {question}\n"
            f"🏷️ SOP Topic        : {_sop_topic_async}\n"
            f"🔑 Search Keywords  : {keywords}\n"
            f"🎯 Scope Terdeteksi : {scope}\n"
            f"📄 Doc Type         : {doc_type}\n"
            f"📝 Template Type    : {template_type}\n"
            f"👤 User Band        : {_band_from_prefix or '-'}\n"
            f"🏙️ Kota Asal        : {analysis.get('kota_asal', '-')}\n"
            f"🏙️ Kota Tujuan      : {analysis.get('kota_tujuan', '-')}\n"
            f"📏 Kalkulasi Jarak  : {analysis.get('butuh_kalkulasi_jarak', False)}\n"
            + "🔮" * 25
        )

        with langfuse_observation("vector_retrieval", input={"keywords": keywords, "scope": scope, "doc_type": doc_type}) as _sp_ret:
            matches = await retrieve_context_async(question, keywords, scope, sop_topic=analysis.get('sop_topic', 'general'))

            # Filter chunks dengan Cohere relevance score di bawah threshold
            before_filter = len(matches)
            filtered = [m for m in matches if m.get('score', 0.0) >= RAG_MIN_SCORE]
            # Jaga minimal 3 chunk agar LLM tidak false-negative "tidak ditemukan"
            if len(filtered) < 3:
                filtered = matches[:max(3, len(filtered))]
            matches = filtered if filtered else matches[:3]
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
            _sec_title = m['metadata'].get('section_title', '') or m['metadata'].get('section_path', '')
            _sec_last  = _sec_title.split('|')[-1].strip() if _sec_title else ''
            parent = m['metadata'].get('heading') or m['metadata'].get('parent_section') or _sec_last or 'Tidak spesifik'
            score = m.get('score', 0.0)
            
            if source != 'Unknown':
                relevant_filenames.append(source)
                
            debug_msg += f"\n📦 CHUNK #{i+1} | Score: {score:.4f}\n"
            debug_msg += f"📁 Sumber : {source} | Bab: {parent}\n"
            debug_msg += f"📄 Teks   : {text[:250]}... [LANJUTAN DIPOTONG UNTUK DEBUG]\n"
            
            context_parts.append(f'<dokumen id="{i+1}" file="{source}" bab="{parent}">\n{text}\n</dokumen>')

        debug_msg += "\n" + "📚" * 25
        logger.info(debug_msg)

        context_str = "\n\n".join(context_parts)
        primary_source = relevant_filenames[0] if relevant_filenames else None
        unique_sources = list(dict.fromkeys(relevant_filenames))  # dedup, preserve order

        # Tools & Policy Injections
        tool_info = ""
        travel_data = {}

        kota_asal = analysis.get('kota_asal', '')
        kota_tujuan = analysis.get('kota_tujuan', '')
        kota_asal = str(kota_asal[0]) if isinstance(kota_asal, list) else str(kota_asal).strip()
        kota_tujuan = str(kota_tujuan[0]) if isinstance(kota_tujuan, list) else str(kota_tujuan).strip()

        # Fallback 1: coba ambil kota_asal dari prefix konteks user "[..., Lokasi saat ini: <kota>, ...]"
        if not kota_asal or kota_asal.lower() in ["", "none", "null", "-", "tidak ada"]:
            import re as _re
            _lokasi_match = _re.search(r'\[.*?Lokasi saat ini:\s*([^,\]]+)', question)
            if _lokasi_match:
                kota_asal = _lokasi_match.group(1).strip()
                logger.info(f"📍 kota_asal di-fallback dari prefix user: {kota_asal}")

        # Fallback 2: coba parse pola "dari <Kota>" langsung dari teks pertanyaan
        # Hanya match kata berawalan huruf kapital untuk menghindari false positive ("dari sini", "dari mana")
        if not kota_asal or kota_asal.lower() in ["", "none", "null", "-", "tidak ada"]:
            _dari_match = _re.search(r'\bdari\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', question)
            if _dari_match:
                kota_asal = _dari_match.group(1).strip()
                logger.info(f"📍 kota_asal di-fallback dari 'dari <Kota>' dalam teks: {kota_asal}")

        is_valid_destination = bool(kota_tujuan and kota_tujuan.lower() not in ["", "none", "null", "-", "tidak ada"])

        # Trigger TravelAnalyzer otomatis jika perjalanan_dinas dengan kota asal+tujuan valid.
        # Tidak bergantung pada flag butuh_kalkulasi_jarak dari LLM karena LLM sering
        # return False untuk pertanyaan "fasilitas apa" meski jarak tetap dibutuhkan.
        # Guard relokasi tetap aktif untuk case "penempatan/mutasi/pindah ke kota X".
        _relokasi_keywords = ["penempatan", "relokasi", "pindah", "mutasi", "dipindahkan"]
        _is_relokasi = any(w in question.lower() for w in _relokasi_keywords)
        _butuh_kalkulasi = analysis.get('butuh_kalkulasi_jarak', False)
        _is_valid_asal = bool(kota_asal and kota_asal.lower() not in ["", "none", "null", "-", "tidak ada"])
        _trigger_travel = is_valid_destination and _is_valid_asal and not _is_relokasi

        logger.info(
            f"🚦 TravelAnalyzer trigger: butuh_kalkulasi={_butuh_kalkulasi} | "
            f"is_valid_destination={is_valid_destination} | is_valid_asal={_is_valid_asal} | is_relokasi={_is_relokasi} | "
            f"→ akan_trigger={_trigger_travel}"
        )

        if _trigger_travel:
            travel_data = await rag_engine.travel_analyzer.process_decision_query_async(origin=kota_asal, destination=kota_tujuan, scope=scope)

            if travel_data.get('processed'):
                route_str = travel_data.get('route', 'Tidak diketahui')
                dist_km = travel_data.get('distance_km', 0)
                dur_hrs = travel_data.get('duration_hours', 0)
                logger.info(f"🛣️ TravelAnalyzer injected: route={route_str}, dist={dist_km}km, dur={dur_hrs}hrs")

                if scope == 'international':
                    _idr_rate = await get_usd_idr_rate()
                    tool_info = HRTravelPolicy.get_international_policy_injection(route_str, dur_hrs, idr_rate=_idr_rate)
                else:
                    tool_info = HRTravelPolicy.get_domestic_policy_injection(route_str, dist_km, dur_hrs)
        else:
            if is_valid_destination:
                logger.info(f"⏭️ TravelAnalyzer SKIPPED (is_relokasi={_is_relokasi}, butuh_kalkulasi={_butuh_kalkulasi})")

        # 🔥 CHECKPOINT 6: Before template building
        await check_cancelled()

        # Template & Formatting
        html_template = rag_engine.template_engine.get_template(template_type, question)
        
        if travel_data.get('processed') and scope == 'domestic':
            _td_dist = travel_data.get('distance_km', 0)
            _td_route = travel_data.get('route', route_str)
            _td_dur = travel_data.get('duration_hours', dur_hrs)
            if 0 < _td_dist < 120:
                html_template = (
                    f"<h3>Informasi Perjalanan Dinas</h3>"
                    f"<p>Rute <strong>{_td_route}</strong> memiliki estimasi jarak <strong>{_td_dist} km</strong>. "
                    f"Berdasarkan regulasi perusahaan, jarak minimal untuk Perjalanan Dinas adalah <strong>120 km</strong> (pergi-pulang).</p>"
                    f"<h3>Ketentuan Kelayakan Fasilitas</h3>"
                    f"<p>Karena jarak perjalanan ini di bawah 120 km, seluruh fasilitas perjalanan dinas — termasuk UPD harian, akomodasi/hotel, dan transportasi — <strong>tidak dapat diberikan</strong>.</p>"
                )
            elif _td_dist >= 120:
                # Prepend route info block — LLM hanya melengkapi sisa template
                _route_header = (
                    f"<p><strong>Rute:</strong> {_td_route} &nbsp;|&nbsp; "
                    f"<strong>Estimasi Jarak:</strong> {_td_dist} km &nbsp;|&nbsp; "
                    f"<strong>Durasi Perjalanan Darat:</strong> {_td_dur:.1f} jam</p>\n"
                )
                html_template = _route_header + html_template

        enforcement_instructions = rag_engine.template_engine.get_enforcement_instructions(html_template)

        # PANGGIL SATPAM SECARA ASYNC PARALEL!
        guardrails = await satpam_aturan.generate_guardrail_prompt_async(relevant_filenames)

        # KEMBALIKAN KEKUATAN DETAIL
        detail_enforcer = ""
        if "singkat" not in question.lower():
            detail_enforcer = (
                "8. 📝 KEDALAMAN JAWABAN: Anda WAJIB menjabarkan aturan, nominal, rincian, dan tata cara secara SANGAT DETAIL, TERSTRUKTUR, dan LENGKAP. "
                "Jangan ada poin penting dari KNOWLEDGE BASE yang disembunyikan! "
                "DILARANG KERAS merangkum menjadi satu kalimat generic seperti 'biaya transportasi ditanggung' — "
                "HARUS dijabarkan MASING-MASING komponen secara spesifik. "
                "Jika [INFO SISTEM] mencantumkan daftar komponen wajib, SEMUA komponen tersebut wajib muncul di jawaban."
            )

        # 🔥 PERUBAHAN KRUSIAL ADA DI SINI 🔥
        prompt = f"""=== SYSTEM ROLE ===
Anda adalah Asisten Profesional HRD PT Semen Indonesia.

=== CRITICAL RULES ===
1. Jawab HANYA menggunakan informasi dari [KNOWLEDGE BASE].
2. 🚨 CEK KELAYAKAN (ELIGIBILITY) SEBELUM MENGHITUNG: Anda WAJIB memeriksa apakah user berhak atas fasilitas tersebut berdasarkan aturan di [KNOWLEDGE BASE].
   - Contoh: Upah Kerja Lembur HANYA diberikan untuk karyawan Job Grade 10 ke bawah atau Band 5.
   - JIKA user menyebutkan ia adalah Band 1, 2, 3, atau 4 dan meminta hitungan lembur, Anda DILARANG KERAS memberikan hitungan/rumus. Anda WAJIB menolak dengan sopan dan menjelaskan bahwa sesuai aturan, Band tersebut tidak mendapatkan upah lembur.
   - [BARU] JIKA user TIDAK MENYEBUTKAN Band/Grade mereka sama sekali, Anda WAJIB: (1) jelaskan terlebih dahulu syarat kelayakannya dari dokumen, KEMUDIAN (2) tetap berikan penjelasan rumus/aturan/tarif sebagai informasi simulasi agar user tahu cara perhitungannya.
3. 🚨 KESEIMBANGAN ANTI-HALUSINASI & KELENTURAN (SANGAT KRITIS):
   - CEK TOPIK ALIEN: Coba lihat [KNOWLEDGE BASE] dengan seksama. Apakah topik yang ditanyakan SAMA SEKALI TIDAK ADA referensinya di sana (bukan hanya mirip topiknya, tapi benar-benar tidak ada sama sekali di seluruh teks)? JIKA YA (Topik Alien), Anda WAJIB BERHENTI dan HANYA MENGELUARKAN KODE INI TANPA TAMBAHAN TEKS LAIN:
[DATA_TIDAK_DITEMUKAN_DI_SOP]
   - CEK TOPIK RELEVAN TAPI KURANG DATA: JIKA topik yang ditanyakan ADA di [KNOWLEDGE BASE] (misal: Lembur, Perjalanan Dinas, Hari Libur, UPD, akomodasi, tunjangan), tetapi data tidak cukup untuk hitungan angka pasti (misal: gaji pokok tidak diketahui), JANGAN GUNAKAN KODE ERROR! Anda WAJIB tetap menjawab dengan ramah berdasarkan aturan/rumus/tarif yang tersedia, dan sampaikan secara profesional bahwa Anda membutuhkan data tambahan untuk menghitung angka pastinya.
   - 🔢 KHUSUS TABEL TARIF (UPD, Lembur, Akomodasi, dll): Jika tabel tarif PER BAND tersedia di [KNOWLEDGE BASE] dan user tidak menyebutkan band-nya, WAJIB tampilkan perhitungan untuk SEMUA band dari tabel. JANGAN gunakan kode error hanya karena band tidak disebutkan — data sudah ada di tabel.
   - CEK TOPIK ADA TAPI DATA TERBATAS: Jika topik ada namun informasinya tidak lengkap, jawab HANYA berdasarkan yang BENAR-BENAR TERTULIS di [KNOWLEDGE BASE]. DILARANG menambahkan informasi dari pengetahuan umum.
4. 🚫 CEK RELEVANSI BERDASARKAN ISI PASAL, BUKAN NAMA FILE:
   Sebelum menggunakan isi sebuah chunk, pastikan ISI TEKS di dalamnya relevan dengan topik kompensasi yang ditanyakan user.
   - 🚨 NAMA FILE BISA MENIPU: Sebuah dokumen dengan nama file "Tunjangan Tugas" BISA SAJA memuat pasal yang secara spesifik mengatur "Kerja Lembur" di dalamnya. Jangan abaikan dokumen hanya karena nama filenya terkesan berbeda — BACA ISI PASALNYA!
   - BEDA KONTEKS = ABAIKAN: Jika user bertanya tentang "Lembur", gunakan HANYA kalimat/pasal yang secara eksplisit menyebut "Lembur", "Kerja Lembur", atau "Tarif Lembur". Jika teks tersebut membahas nominal "Tunjangan Tugas" atau "Shift" tanpa menyebut lembur, DILARANG memaksakan angkanya untuk menjawab Lembur.
   - Contoh lain: user tanya LHKPN → abaikan chunk yang teksnya tentang mobil dinas. User tanya "Dewan Pengawas" → abaikan chunk yang teksnya tentang karyawan umum.
   - 🚨 JIKA setelah menyaring tidak ada chunk yang isinya relevan → WAJIB keluarkan kode ini tanpa teks lain:
[DATA_TIDAK_DITEMUKAN_DI_SOP]
   - ✅ [WAJIB BLEND] JIKA ada beberapa chunk relevan (misal: satu chunk mengatur pengali lembur, chunk lain mengatur syarat Band/Grade yang berhak), Anda WAJIB menggabungkan informasinya agar jawaban utuh.
5. 🚫 DILARANG MERANGKAI ATURAN LINTAS TOPIK: DILARANG KERAS memaksakan angka/aturan dari satu konteks (misal: nominal Tunjangan Tugas) untuk menjawab konteks lain (misal: Upah Lembur), meski berasal dari file yang sama.
6. Angka tarif, jarak, dan durasi HARUS persis sama dengan dokumen.
7. 🔥 TUGAS KALKULASI: JIKA ADA angka jarak (km) atau durasi (jam) dari [INFO SISTEM & INSTRUKSI MUTLAK], WAJIB gunakan angka tersebut.
8. 🚨 KEPATUHAN FORMAT: WAJIB MEMATUHI SEMUA PERINTAH di dalam [INFO SISTEM & INSTRUKSI MUTLAK] TANPA TERKECUALI!
9. 🚨 ATURAN KUTIPAN SUMBER — WAJIB URUT & RAPI (HINDARI OVER-CITATION):
   - 🌟 WAJIB RE-INDEX: Nomor sitasi di dalam teks keluaran Anda WAJIB diurutkan dinamis mulai dari [1], lalu [2], dst., TERLEPAS dari atribut id asli tag <dokumen> di [KNOWLEDGE BASE].
   - 🌟 JANGAN SPAM SITASI: Jika dalam satu paragraf atau satu poin bullet Anda mengambil informasi dari SUMBER YANG SAMA, cukup letakkan nomor sitasi SATU KALI SAJA di akhir paragraf/poin tersebut.
   - ❌ DILARANG: menaruh sitasi di setiap akhir kalimat jika sumbernya sama. Hindari: "Aturan A [1]. Aturan B [1]. Aturan C [1]."
   - ✅ BENAR: "Aturan A. Aturan B. Aturan C [1]." — satu sitasi di akhir poin untuk sumber yang sama.
   - Jika satu paragraf/poin menggabungkan dua dokumen berbeda, baru gabungkan di akhir: [1][2].
   - Pastikan di bagian Rujukan Dokumen, angka [1], [2], dst. dipasangkan dengan Nama File dan Pasal yang tepat sesuai urutan kemunculannya di teks.
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
        # Safety net: hapus placeholder yang tidak diganti LLM
        cleaned_response = cleaned_response.replace('[KOTAK_PERINGATAN_KOREKSI]', '')
    
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
        butuh_kalkulasi = analysis.get('butuh_kalkulasi_jarak', False)

        # sop_topic dari LLM — digunakan untuk scope override dan TravelAnalyzer guard
        _sop_topic = analysis.get('sop_topic', 'general')
        _is_relokasi = _sop_topic in ('relokasi', 'tunjangan', 'karir', 'phk') or \
                       any(w in question.lower() for w in ["penempatan", "relokasi", "pindah", "mutasi", "dipindahkan"])

        # ── Fallback Band (sama dengan path non-stream) ──────────────────────
        # Kalau LLM tidak inject band ke keywords, ambil dari prefix [Band: X]
        import re as _re_kw_s
        _band_from_prefix_s = analysis.get('user_band', '').strip()
        if not _band_from_prefix_s or _band_from_prefix_s == "0":
            _band_match_s = _re_kw_s.search(r'\[.*?Band:\s*([1-9]\d*)', question)
            if _band_match_s:
                _band_from_prefix_s = _band_match_s.group(1).strip()
            else:
                _band_from_prefix_s = ""
        if _band_from_prefix_s and _band_from_prefix_s.isdigit() and int(_band_from_prefix_s) > 0 \
                and f"Band {_band_from_prefix_s}" not in keywords:
            keywords = f"{keywords} Band {_band_from_prefix_s}"
            logger.info(f"📍 [STREAM] Band {_band_from_prefix_s} di-inject ke search keywords")

        # scope filter (domestic/international) hanya relevan untuk perjalanan dinas.
        # Untuk topik lain, Pinecone scope filter menyingkirkan dokumen scope=general.
        if _sop_topic != 'perjalanan_dinas' and scope != 'general':
            logger.info(f"🔧 scope override: '{scope}' → 'general' (sop_topic={_sop_topic})")
            scope = 'general'

        logger.info(
            "\n" + "🔮" * 25 + "\n"
            "🔍 DEBUGGING QUERY ANALYZER (STREAM)\n"
            f"🗣️  Pertanyaan      : {question}\n"
            f"🏷️  SOP Topic       : {_sop_topic}\n"
            f"🔑  Search Keywords : {keywords}\n"
            f"🎯  Scope           : {scope}\n"
            f"📄  Doc Type        : {doc_type}\n"
            f"📝  Template Type   : {template_type}\n"
            f"🏙️  Kota Asal       : {analysis.get('kota_asal', '-')}\n"
            f"🏙️  Kota Tujuan     : {analysis.get('kota_tujuan', '-')}\n"
            f"📏  Kalkulasi Jarak : {butuh_kalkulasi}\n"
            f"👤  User Band       : {_band_from_prefix_s or '-'}\n"
            + "🔮" * 25
        )

        with langfuse_observation("vector_retrieval", input={"keywords": keywords, "scope": scope, "doc_type": doc_type}) as _sp_ret:
            matches = await retrieve_context_async(question, keywords, scope, sop_topic=analysis.get('sop_topic', 'general'))
            before_filter = len(matches)
            filtered = [m for m in matches if m.get('score', 0.0) >= RAG_MIN_SCORE]
            # Jaga minimal 3 chunk agar LLM tidak false-negative "tidak ditemukan"
            if len(filtered) < 3:
                filtered = matches[:max(3, len(filtered))]
            matches = filtered if filtered else matches[:3]
            logger.info(f"🔽 Score filter: {before_filter} → {len(matches)} chunks (threshold={RAG_MIN_SCORE})")
            # Debug: tampilkan semua chunk yang diambil beserta isi teksnya
            sep = "=" * 60
            for i, m in enumerate(matches):
                src = m['metadata'].get('filename') or m['metadata'].get('source_file') or 'Unknown'
                sec = m['metadata'].get('parent_section') or m['metadata'].get('heading') or '-'
                score = m.get('score', 0.0)
                txt = m['metadata'].get('text', '').strip()
                logger.info(
                    f"\n{sep}\n"
                    f"📄 CHUNK #{i+1} | Score: {score:.4f}\n"
                    f"📁 File   : {src}\n"
                    f"📑 Section: {sec}\n"
                    f"📝 Text   :\n{txt}\n"
                    f"{sep}"
                )
            if _sp_ret:
                _sp_ret.update(output={"chunks_returned": len(matches), "chunks_before_filter": before_filter})

        await check_cancelled()

        context_parts = []
        relevant_filenames = []
        for i, m in enumerate(matches):
            text = m['metadata'].get('text', '').strip()[:2000]
            source = m['metadata'].get('filename') or m['metadata'].get('source_file') or 'Unknown'
            _sec_title = m['metadata'].get('section_title', '') or m['metadata'].get('section_path', '')
            _sec_last  = _sec_title.split('|')[-1].strip() if _sec_title else ''
            parent = m['metadata'].get('heading') or m['metadata'].get('parent_section') or _sec_last or 'Tidak spesifik'
            if source != 'Unknown':
                relevant_filenames.append(source)
            context_parts.append(f'<dokumen id="{i+1}" file="{source}" bab="{parent}">\n{text}\n</dokumen>')

        context_str = "\n\n".join(context_parts)
        primary_source = relevant_filenames[0] if relevant_filenames else None
        unique_sources = list(dict.fromkeys(relevant_filenames))  # dedup, preserve order
        if out_context is not None:
            out_context["context"] = context_str
            out_context["sop_topic"] = _sop_topic

        tool_info = ""
        travel_data = {}
        kota_asal = analysis.get('kota_asal', '')
        kota_tujuan = analysis.get('kota_tujuan', '')
        kota_asal = str(kota_asal[0]) if isinstance(kota_asal, list) else str(kota_asal).strip()
        kota_tujuan = str(kota_tujuan[0]) if isinstance(kota_tujuan, list) else str(kota_tujuan).strip()

        # ── Fallback Lokasi (sama dengan path non-stream) ────────────────────
        # Fallback 1: coba ambil kota_asal dari prefix [Lokasi saat ini: ...]
        if not kota_asal or kota_asal.lower() in ["", "none", "null", "-", "tidak ada"]:
            import re as _re_s
            _lokasi_match_s = _re_s.search(r'\[.*?Lokasi saat ini:\s*([^,\]]+)', question)
            if _lokasi_match_s:
                kota_asal = _lokasi_match_s.group(1).strip()
                logger.info(f"📍 [STREAM] kota_asal di-fallback dari prefix user: {kota_asal}")

        # Fallback 2: parse pola "dari <Kota>" langsung dari teks pertanyaan
        if not kota_asal or kota_asal.lower() in ["", "none", "null", "-", "tidak ada"]:
            _dari_match_s = _re_s.search(r'\bdari\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', question)
            if _dari_match_s:
                kota_asal = _dari_match_s.group(1).strip()
                logger.info(f"📍 [STREAM] kota_asal di-fallback dari 'dari <Kota>' dalam teks: {kota_asal}")

        is_valid_destination = bool(kota_tujuan and kota_tujuan.lower() not in ["", "none", "null", "-", "tidak ada"])

        # Trigger TravelAnalyzer otomatis jika perjalanan_dinas dengan kota asal+tujuan valid.
        # Tidak bergantung pada flag butuh_kalkulasi_jarak dari LLM karena LLM sering
        # return False untuk pertanyaan "fasilitas apa" meski jarak tetap dibutuhkan.
        # Guard relokasi tetap aktif untuk case "penempatan/mutasi/pindah ke kota X".
        _relokasi_keywords = ["penempatan", "relokasi", "pindah", "mutasi", "dipindahkan"]
        _is_relokasi = any(w in question.lower() for w in _relokasi_keywords)
        _is_valid_asal = bool(kota_asal and kota_asal.lower() not in ["", "none", "null", "-", "tidak ada"])
        _trigger_travel = is_valid_destination and _is_valid_asal and not _is_relokasi

        logger.info(
            f"🚦 TravelAnalyzer trigger: butuh_kalkulasi={butuh_kalkulasi} | "
            f"is_valid_destination={is_valid_destination} | is_valid_asal={_is_valid_asal} | is_relokasi={_is_relokasi} | "
            f"→ akan_trigger={_trigger_travel}"
        )

        if _trigger_travel:
            travel_data = await rag_engine.travel_analyzer.process_decision_query_async(origin=kota_asal, destination=kota_tujuan, scope=scope)
            if travel_data.get('processed'):
                route_str = travel_data.get('route', 'Tidak diketahui')
                dist_km = travel_data.get('distance_km', 0)
                dur_hrs = travel_data.get('duration_hours', 0)
                logger.info(f"🛣️  TravelAnalyzer injected: route={route_str}, dist={dist_km}km, dur={dur_hrs}hrs")
                if scope == 'international':
                    _idr_rate = await get_usd_idr_rate()
                    tool_info = HRTravelPolicy.get_international_policy_injection(route_str, dur_hrs, idr_rate=_idr_rate)
                else:
                    tool_info = HRTravelPolicy.get_domestic_policy_injection(route_str, dist_km, dur_hrs)
        else:
            if is_valid_destination and not _trigger_travel:
                logger.info(f"⏭️  TravelAnalyzer SKIPPED (is_relokasi={_is_relokasi}, butuh_kalkulasi={butuh_kalkulasi})")

        await check_cancelled()

        html_template = rag_engine.template_engine.get_template(template_type, question)
        if travel_data.get('processed') and scope == 'domestic':
            _td_dist = travel_data.get('distance_km', 0)
            _td_route = travel_data.get('route', route_str)
            _td_dur = travel_data.get('duration_hours', dur_hrs)
            if 0 < _td_dist < 120:
                html_template = (
                    f"<h3>Informasi Perjalanan Dinas</h3>"
                    f"<p>Rute <strong>{_td_route}</strong> memiliki estimasi jarak <strong>{_td_dist} km</strong>. "
                    f"Berdasarkan regulasi perusahaan, jarak minimal untuk Perjalanan Dinas adalah <strong>120 km</strong> (pergi-pulang).</p>"
                    f"<h3>Ketentuan Kelayakan Fasilitas</h3>"
                    f"<p>Karena jarak perjalanan ini di bawah 120 km, seluruh fasilitas perjalanan dinas — termasuk UPD harian, akomodasi/hotel, dan transportasi — <strong>tidak dapat diberikan</strong>.</p>"
                )
            elif _td_dist >= 120:
                _route_header = (
                    f"<p><strong>Rute:</strong> {_td_route} &nbsp;|&nbsp; "
                    f"<strong>Estimasi Jarak:</strong> {_td_dist} km &nbsp;|&nbsp; "
                    f"<strong>Durasi Perjalanan Darat:</strong> {_td_dur:.1f} jam</p>\n"
                )
                html_template = _route_header + html_template

        enforcement_instructions = rag_engine.template_engine.get_enforcement_instructions(html_template)
        guardrails = await satpam_aturan.generate_guardrail_prompt_async(relevant_filenames)

        detail_enforcer = ""
        if "singkat" not in question.lower():
            detail_enforcer = (
                "8. 📝 KEDALAMAN JAWABAN: Anda WAJIB menjabarkan aturan, nominal, rincian, dan tata cara secara SANGAT DETAIL, TERSTRUKTUR, dan LENGKAP. "
                "Jangan ada poin penting dari KNOWLEDGE BASE yang disembunyikan! "
                "DILARANG KERAS merangkum menjadi satu kalimat generic seperti 'biaya transportasi ditanggung' — "
                "HARUS dijabarkan MASING-MASING komponen secara spesifik. "
                "Jika [INFO SISTEM] mencantumkan daftar komponen wajib, SEMUA komponen tersebut wajib muncul di jawaban."
            )

        prompt = f"""=== SYSTEM ROLE ===
Anda adalah Asisten Profesional HRD PT Semen Indonesia.

=== CRITICAL RULES ===
1. Jawab HANYA menggunakan informasi dari [KNOWLEDGE BASE].
2. 🚨 CEK KELAYAKAN (ELIGIBILITY) SEBELUM MENGHITUNG: Anda WAJIB memeriksa apakah user berhak atas fasilitas tersebut berdasarkan aturan di [KNOWLEDGE BASE].
   - Contoh: Upah Kerja Lembur HANYA diberikan untuk karyawan Job Grade 10 ke bawah atau Band 5.
   - JIKA user menyebutkan ia adalah Band 1, 2, 3, atau 4 dan meminta hitungan lembur, Anda DILARANG KERAS memberikan hitungan/rumus. Anda WAJIB menolak dengan sopan dan menjelaskan bahwa sesuai aturan, Band tersebut tidak mendapatkan upah lembur.
3. 🚨 KESEIMBANGAN ANTI-HALUSINASI & KELENTURAN (SANGAT KRITIS):
   - CEK TOPIK ALIEN: Coba lihat [KNOWLEDGE BASE] dengan seksama. Apakah topik yang ditanyakan SAMA SEKALI TIDAK ADA referensinya di sana (bukan hanya mirip topiknya, tapi benar-benar tidak ada sama sekali di seluruh teks)? JIKA YA (Topik Alien), Anda WAJIB BERHENTI dan HANYA MENGELUARKAN KODE INI TANPA TAMBAHAN TEKS LAIN:
[DATA_TIDAK_DITEMUKAN_DI_SOP]
   - CEK TOPIK RELEVAN TAPI KURANG DATA: JIKA topik yang ditanyakan ADA di [KNOWLEDGE BASE] (misal: Lembur, Perjalanan Dinas, Hari Libur, UPD, akomodasi, tunjangan), tetapi data tidak cukup untuk hitungan angka pasti (misal: gaji pokok tidak diketahui), JANGAN GUNAKAN KODE ERROR! Anda WAJIB tetap menjawab dengan ramah berdasarkan aturan/rumus/tarif yang tersedia, dan sampaikan secara profesional bahwa Anda membutuhkan data tambahan untuk menghitung angka pastinya.
   - 🔢 KHUSUS TABEL TARIF (UPD, Lembur, Akomodasi, dll): Jika tabel tarif PER BAND tersedia di [KNOWLEDGE BASE] dan user tidak menyebutkan band-nya, WAJIB tampilkan perhitungan untuk SEMUA band dari tabel. JANGAN gunakan kode error hanya karena band tidak disebutkan — data sudah ada di tabel.
   - CEK TOPIK ADA TAPI DATA TERBATAS: Jika topik ada namun informasinya tidak lengkap, jawab HANYA berdasarkan yang BENAR-BENAR TERTULIS di [KNOWLEDGE BASE]. DILARANG menambahkan informasi dari pengetahuan umum.
4. 🚫 CEK RELEVANSI BERDASARKAN ISI PASAL, BUKAN NAMA FILE:
   Sebelum menggunakan isi sebuah chunk, pastikan ISI TEKS di dalamnya relevan dengan topik kompensasi yang ditanyakan user.
   - 🚨 NAMA FILE BISA MENIPU: Sebuah dokumen dengan nama file "Tunjangan Tugas" BISA SAJA memuat pasal yang secara spesifik mengatur "Kerja Lembur" di dalamnya. Jangan abaikan dokumen hanya karena nama filenya terkesan berbeda — BACA ISI PASALNYA!
   - BEDA KONTEKS = ABAIKAN: Jika user bertanya tentang "Lembur", gunakan HANYA kalimat/pasal yang secara eksplisit menyebut "Lembur", "Kerja Lembur", atau "Tarif Lembur". Jika teks tersebut membahas nominal "Tunjangan Tugas" atau "Shift" tanpa menyebut lembur, DILARANG memaksakan angkanya untuk menjawab Lembur.
   - Contoh lain: user tanya LHKPN → abaikan chunk yang teksnya tentang mobil dinas. User tanya "Dewan Pengawas" → abaikan chunk yang teksnya tentang karyawan umum.
   - 🚨 JIKA setelah menyaring tidak ada chunk yang isinya relevan → WAJIB keluarkan kode ini tanpa teks lain:
[DATA_TIDAK_DITEMUKAN_DI_SOP]
   - ✅ [WAJIB BLEND] JIKA ada beberapa chunk relevan (misal: satu chunk mengatur pengali lembur, chunk lain mengatur syarat Band/Grade yang berhak), Anda WAJIB menggabungkan informasinya agar jawaban utuh.
5. 🚫 DILARANG MERANGKAI ATURAN LINTAS TOPIK: DILARANG KERAS memaksakan angka/aturan dari satu konteks (misal: nominal Tunjangan Tugas) untuk menjawab konteks lain (misal: Upah Lembur), meski berasal dari file yang sama.
6. Angka tarif, jarak, dan durasi HARUS persis sama dengan dokumen.
7. 🔥 TUGAS KALKULASI: JIKA ADA angka jarak (km) atau durasi (jam) dari [INFO SISTEM & INSTRUKSI MUTLAK], WAJIB gunakan angka tersebut.
8. 🚨 KEPATUHAN FORMAT: WAJIB MEMATUHI SEMUA PERINTAH di dalam [INFO SISTEM & INSTRUKSI MUTLAK] TANPA TERKECUALI!
9. 🚨 ATURAN KUTIPAN SUMBER — WAJIB URUT & RAPI (HINDARI OVER-CITATION):
   - 🌟 WAJIB RE-INDEX: Nomor sitasi di dalam teks keluaran Anda WAJIB diurutkan dinamis mulai dari [1], lalu [2], dst., TERLEPAS dari atribut id asli tag <dokumen> di [KNOWLEDGE BASE].
   - 🌟 JANGAN SPAM SITASI: Jika dalam satu paragraf atau satu poin bullet Anda mengambil informasi dari SUMBER YANG SAMA, cukup letakkan nomor sitasi SATU KALI SAJA di akhir paragraf/poin tersebut.
   - ❌ DILARANG: menaruh sitasi di setiap akhir kalimat jika sumbernya sama. Hindari: "Aturan A [1]. Aturan B [1]. Aturan C [1]."
   - ✅ BENAR: "Aturan A. Aturan B. Aturan C [1]." — satu sitasi di akhir poin untuk sumber yang sama.
   - Jika satu paragraf/poin menggabungkan dua dokumen berbeda, baru gabungkan di akhir: [1][2].
   - Pastikan di bagian Rujukan Dokumen, angka [1], [2], dst. dipasangkan dengan Nama File dan Pasal yang tepat sesuai urutan kemunculannya di teks.
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

            # Safety net log: jika LLM tidak mengganti placeholder (tidak bisa di-fix post-stream)
            if '[KOTAK_PERINGATAN_KOREKSI]' in full_response:
                logger.warning("⚠️ [KOTAK_PERINGATAN_KOREKSI] lolos ke stream — prompt fix seharusnya mencegah ini")

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
