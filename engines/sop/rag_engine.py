"""
FINAL ANTI-HALLUCINATION RAG ENGINE
Ultra-strict prompting to completely eliminate hallucinations
"""

import re
from typing import Optional

from pinecone import Pinecone
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from memory.memory_supabase import save_message, get_recent_history

try:
    from app.sop_router import infer_doc_type
except ImportError:
    def infer_doc_type(question: str) -> Optional[str]:
        return None

from app.config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX,
    EMBEDDING_MODEL,
)

# Initialize clients
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

embedder = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=OPENAI_API_KEY
)

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4o-mini",
    temperature=0.0,  # SET TO 0 FOR CONSISTENCY!
    max_tokens=2000,
    streaming=False
)

# =====================
# FIXED RETRIEVAL (unchanged - already working)
# =====================
def retrieve_context(query: str, top_k: int = 10, doc_type: Optional[str] = None):
    """Fixed retrieval that handles ScoredVector objects correctly"""
    try:
        print(f"[DEBUG] Retrieving context for: {query}")
        query_vector = embedder.embed_query(query)

        filter_dict = {}
        if doc_type:
            filter_dict["doc_type"] = doc_type
            print(f"[DEBUG] Using doc_type filter: {doc_type}")

        res = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        matches = res.get("matches", [])
        if not matches:
            print("[DEBUG] No matches found in Pinecone")
            return []
        
        print(f"[DEBUG] Found {len(matches)} initial matches")
        
        valid_matches = []
        for i, match in enumerate(matches):
            try:
                match_dict = {
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata
                }
                
                metadata = match_dict['metadata']
                text_content = metadata.get('text', '')
                
                if not text_content or len(text_content.strip()) < 10:
                    print(f"[DEBUG] Skipping match {i+1} - no text content")
                    continue
                
                valid_matches.append(match_dict)
                print(f"[DEBUG] Valid match {i+1}: {len(text_content)} chars, score: {match_dict['score']:.4f}")
                
            except Exception as e:
                print(f"[DEBUG] Error processing match {i+1}: {e}")
                continue
        
        # Apply smart re-ranking
        for match in valid_matches:
            text = match['metadata'].get('text', '').lower()
            original_score = match['score']
            
            if any(indicator in text for indicator in ['band 1', 'band 2', 'usd', 'rp', 'tarif']):
                match['score'] = original_score + 0.15
        
        valid_matches = sorted(valid_matches, key=lambda x: x.get('score', 0), reverse=True)
        return valid_matches[:5]  # TOP 5 ONLY
        
    except Exception as e:
        print(f"[ERROR] Retrieve context error: {e}")
        return []

# =====================
# ENHANCED CONTEXT BUILDING - ANTI-HALLUCINATION
# =====================
def build_context_anti_hallucination(matches: list) -> str:
    """Build context with anti-hallucination structure"""
    if not matches:
        return "Tidak ada informasi yang relevan ditemukan di dokumen SOP."
    
    # Group by document to avoid mixing
    context_parts = []
    
    for i, match in enumerate(matches):
        try:
            metadata = match.get("metadata", {})
            text_content = metadata.get("text", "")
            
            if not text_content:
                continue
            
            doc_type = metadata.get("doc_type", "")
            source_file = metadata.get("source_file", "")
            pasal = metadata.get("pasal", "")
            
            # CRITICAL: Clean and structure content to prevent hallucination
            clean_text = text_content.strip()
            
            # Structure untuk anti-hallucination
            structured_block = f"""DOKUMEN_{i+1}:
FILE: {source_file}
BAGIAN: {pasal}
KONTEN_EKSPLISIT:
{clean_text}
---"""
            
            context_parts.append(structured_block)
            
        except Exception as e:
            print(f"[ERROR] Error building context for match {i+1}: {e}")
            continue
    
    final_context = "\n".join(context_parts)
    return final_context

# =====================
# ENHANCED QUESTION REPHRASING (unchanged)
# =====================
def rephrase_question_with_context(question: str, history: list) -> str:
    """Enhanced rephrasing (already working)"""
    try:
        if not history or len(history) < 2:
            return question
        
        recent_history = history[-8:] if len(history) > 8 else history
        
        history_parts = []
        for h in recent_history:
            try:
                if isinstance(h, dict) and "role" in h and "message" in h:
                    role = h.get("role", "unknown")
                    message = h.get("message", "")
                    if message:
                        context_length = 400 if any(term in message.lower() 
                                                  for term in ['rumah dinas', 'fasilitas', 'akomodasi', 'reimburse', 'reimbursement']) else 200
                        history_parts.append(f"{role}: {message[:context_length]}")
            except Exception as e:
                print(f"[DEBUG] Error processing history item: {e}")
                continue
        
        if not history_parts:
            return question
        
        history_text = "\n".join(history_parts)
        
        rephrase_prompt = f"""Anda bertugas mengubah pertanyaan follow-up menjadi pertanyaan standalone sambil MEMPERTAHANKAN semua konteks penting.

ATURAN WAJIB:
1. Jika pertanyaan sudah lengkap, kembalikan PERSIS seperti aslinya
2. WAJIB pertahankan konteks penting seperti: rumah dinas, fasilitas, kondisi khusus, reimburse/reimbursement
3. Gabungkan dengan topik dari chat history yang relevan
4. JANGAN hilangkan detail yang bisa mempengaruhi jawaban
5. Gunakan bahasa Indonesia yang natural

RIWAYAT PERCAKAPAN:
{history_text}

PERTANYAAN FOLLOW-UP:
{question}

PERTANYAAN STANDALONE (hanya pertanyaan, tanpa penjelasan):"""

        response = llm.invoke(rephrase_prompt)
        rephrased = response.content.strip()
        
        print("===== ENHANCED QUESTION REPHRASING =====")
        print("ORIGINAL:", question)
        print("REPHRASED:", rephrased)
        print("========================================")
        
        return rephrased
        
    except Exception as e:
        print(f"❌ Enhanced rephrasing error: {e}")
        return question

# =====================
# ANTI-HALLUCINATION MAIN ANSWER FUNCTION
# =====================
def answer_question(question: str, session_id: str):
    """ANTI-HALLUCINATION answer function with ultra-strict prompting"""
    try:
        print(f"[DEBUG] Starting ANTI-HALLUCINATION answer_question for: {question}")
        
        # Get history
        try:
            history = get_recent_history(session_id)
            print(f"[DEBUG] History length: {len(history) if history else 0}")
        except Exception as e:
            print(f"[ERROR] History retrieval error: {e}")
            history = []
        
        # Rephrase question
        try:
            standalone_question = rephrase_question_with_context(question, history)
        except Exception as e:
            print(f"[ERROR] Question rephrasing error: {e}")
            standalone_question = question
        
        # Infer doc type
        try:
            doc_type = infer_doc_type(standalone_question)
        except Exception as e:
            print(f"[ERROR] Doc type inference error: {e}")
            doc_type = None
        
        # Retrieve context
        try:
            matches = retrieve_context(standalone_question, doc_type=doc_type)
        except Exception as e:
            print(f"[ERROR] Context retrieval error: {e}")
            matches = []
        
        # Build ANTI-HALLUCINATION context
        try:
            context = build_context_anti_hallucination(matches)
        except Exception as e:
            print(f"[ERROR] Context building error: {e}")
            context = "Terjadi kesalahan dalam memproses dokumen SOP."
        
        # Build history text
        try:
            history_text = ""
            if history:
                recent_history = history[-6:] if len(history) > 6 else history  # Shorter history
                history_parts = []
                for h in recent_history:
                    try:
                        if isinstance(h, dict) and "role" in h and "message" in h:
                            role = h.get("role", "").upper()
                            message = h.get("message", "")
                            if role and message:
                                history_parts.append(f"{role}: {message[:150]}")  # Shorter context
                    except:
                        continue
                history_text = "\n".join(history_parts)
        except Exception as e:
            print(f"[ERROR] History building error: {e}")
            history_text = ""

        # BALANCED ANTI-HALLUCINATION PROMPT - NATURAL BUT NO HALLUCINATION
        prompt = f"""
Anda adalah Asisten SOP profesional yang memberikan jawaban natural dan akurat.

====================
🎯 ATURAN BALANCED ACCURACY
====================

STRICT PADA FAKTA (NON-NEGOTIABLE):
1. SEMUA angka, nominal, spesifikasi HARUS persis sama dengan dokumen
2. TIDAK boleh menyebutkan jabatan/posisi yang TIDAK disebutkan dalam dokumen
3. TIDAK boleh menambahkan prosedur yang tidak ada dalam konteks
4. Jika informasi tidak ada, katakan "tidak disebutkan dalam dokumen"

FLEXIBLE PADA PRESENTASI:
1. BOLEH menyusun informasi dengan struktur yang logis dan natural
2. BOLEH menggunakan bahasa yang mudah dipahami dan tidak kaku
3. BOLEH mengelompokkan informasi terkait dalam satu bagian
4. BOLEH membuat penjelasan yang user-friendly ASALKAN berdasarkan dokumen

====================
CONTOH BALANCED APPROACH:
====================

❌ TERLALU KAKU: "Berdasarkan poin 2b dokumen tersebut menyebutkan..."
✅ BALANCED: "Untuk penggunaan kendaraan pribadi, terdapat ketentuan jarak..."

❌ HALUSINASI: "Dengan persetujuan General Manager" (tidak ada di dokumen)
✅ BALANCED: "Dengan persetujuan Atasan minimal Band 1" (sesuai dokumen)

❌ TERLALU TEKNIS: "Sesuai dengan prosedur IK/SIG/HCM/50064900/008..."
✅ BALANCED: "Sesuai dengan prosedur yang ditetapkan dalam dokumen..."

====================
FORMAT NATURAL (HTML):
====================

<h3>Informasi [Topik yang Natural]</h3>
<p>[Penjelasan pembuka yang natural berdasarkan dokumen]</p>

<h3>Ketentuan dan Syarat</h3>
<ul>
<li>[Penjelasan natural tapi akurat - angka PERSIS]</li>
<li>[Logical flow tapi berdasarkan dokumen]</li>
</ul>

<h3>Prosedur dan Persetujuan</h3>
<ul>
<li>[User-friendly explanation berdasarkan dokumen]</li>
</ul>

<h3>Catatan Penting</h3>
<p>[Jika ada informasi yang tidak lengkap atau perlu klarifikasi]</p>

<h3>Rujukan Dokumen</h3>
<ul>
<li><strong>Sumber:</strong> [Nama file dari konteks]</li>
<li><strong>Bagian:</strong> [Bagian dari konteks]</li>
</ul>

====================
RIWAYAT PERCAKAPAN:
====================
{history_text if history_text else "Tidak ada riwayat percakapan sebelumnya."}

====================
KONTEKS SOP (SUMBER KEBENARAN):
====================
{context}

====================
PERTANYAAN:
====================
{question}

====================
BALANCED GUIDELINES:
====================
- Akurat pada fakta, natural pada presentasi
- Jika ragu tentang detail, lebih baik tidak sebutkan
- Prioritaskan kejelasan dan kegunaan untuk user
- Professional tapi tidak kaku
- JANGAN PERNAH tambahkan info yang tidak ada dalam konteks

JAWABAN NATURAL & AKURAT:
"""

        print("===== ANTI-HALLUCINATION DEBUG =====")
        print("ORIGINAL:", question)
        print("STANDALONE:", standalone_question)
        print("DOC TYPE:", doc_type)
        print("MATCHES:", len(matches))
        print("CONTEXT LENGTH:", len(context))
        print("=====================================")
        
        # Generate response with ZERO temperature
        try:
            response_obj = llm.invoke(prompt)
            response_text = response_obj.content.strip()
            
            print("\n===== RAW LLM RESPONSE =====")
            print(response_text[:400])
            print("============================\n")
            
        except Exception as e:
            print(f"[ERROR] LLM response generation error: {e}")
            response_text = f"""
<h3>❌ Error Sistem</h3>
<p>Terjadi kesalahan dalam memproses pertanyaan Anda: {str(e)}</p>
<p>Silakan coba lagi dalam beberapa saat.</p>
"""
        
        # Clean up response
        try:
            response_text = cleanup_numbered_lists(response_text)
        except Exception as e:
            print(f"[ERROR] Response cleanup error: {e}")
        
        # Save message
        try:
            save_message(session_id, "assistant", response_text)
        except Exception as e:
            print(f"[ERROR] Message save error: {e}")
        
        return response_text
        
    except Exception as e:
        print(f"[ERROR] Critical error in ANTI-HALLUCINATION answer_question: {e}")
        error_response = f"""
<h3>❌ Error Sistem</h3>
<p>Terjadi kesalahan sistem yang tidak terduga: {str(e)}</p>
<p>Silakan hubungi administrator atau coba lagi nanti.</p>
"""
        
        try:
            save_message(session_id, "assistant", error_response)
        except:
            pass
        
        return error_response

# =====================
# CLEANUP FUNCTION (unchanged)
# =====================
def cleanup_numbered_lists(text: str) -> str:
    """Safe cleanup function"""
    try:
        text = text.replace('```html', '').replace('```', '')
        text = re.sub(r'<br\s*/?\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        lines = text.split('\n')
        cleaned_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            if not line and in_list:
                continue
            if re.match(r'^\d+\.\s+', line):
                line = re.sub(r'^\d+\.\s+(.*)', r'<li>\1</li>', line)
                if not in_list:
                    cleaned_lines.append('<ul>')
                    in_list = True
                cleaned_lines.append(line)
            else:
                if in_list and line:
                    cleaned_lines.append('</ul>')
                    in_list = False
                if line:
                    cleaned_lines.append(line)
        
        if in_list:
            cleaned_lines.append('</ul>')
        
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Cleanup function error: {e}")
        return text

if __name__ == "__main__":
    print("🚫 Testing ANTI-HALLUCINATION RAG engine...")
    test_result = answer_question("apa tools yang digunakan untuk perjalanan dinas", "test_session")
    print(f"Test result length: {len(test_result)}")