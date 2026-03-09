"""
DENAI Speech Utilities
Helper functions for speech processing and text normalization
"""

import logging
import asyncio
from openai import OpenAI

# ✅ FIX BUG: Import dari config
from app.config import OPENAI_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

# Inisialisasi client
client = OpenAI(api_key=OPENAI_API_KEY)

async def rewrite_for_speech(text: str, question: str = "") -> str:
    """
    🎯 ANSWER-FIRST APPROACH FOR VOICE:
    - JAWAB pertanyaan langsung di awal
    - Tetap lengkap tapi to the point
    - Hilangkan intro bertele-tele
    - Fokus pada apa yang ditanya
    
    Args:
        text: Jawaban lengkap dari backend
        question: Pertanyaan asli dari user (untuk context!)
    """
    if not text or not text.strip():
        return ""

    # Build context-aware prompt
    if question and question.strip():
        context_info = f"""
PERTANYAAN USER:
"{question}"

Fokus jawab pertanyaan ini dulu, baru kasih supporting details!
"""
    else:
        context_info = ""

    prompt = f"""
Kamu adalah asisten suara yang harus menjawab LANGSUNG ke pertanyaan user.

{context_info}

ATURAN WAJIB:
1. JAWAB PERTANYAAN DULU di kalimat pertama - langsung to the point!
2. Tetap lengkap dan detail, tapi:
   - Hilangkan intro/pembukaan yang ga perlu
   - Hilangkan syarat-syarat yang ga ditanya
   - Hilangkan background info yang ga urgent
3. Urutkan informasi dari yang PALING RELEVAN ke yang supporting
4. Gunakan bahasa lisan yang natural tapi jelas
5. Tetap profesional dan akurat

CONTOH TRANSFORMASI:
Pertanyaan: "Denda telat pajak berapa?"
❌ BURUK: "Untuk pajak, ada beberapa syarat. Pertama harus punya NPWP... (5 paragraf)... Oh ya dendanya 2%"
✅ BAGUS: "Dendanya 2% per bulan. Jadi kalau pajaknya 1 juta, kena denda 20 ribu. Sebaiknya segera dibayar ya."

TEKS ASLI (lengkap):
{text}

INSTRUKSI: Jawab LANGSUNG apa yang ditanya, tetap lengkap tapi tanpa bertele-tele. Prioritaskan informasi paling penting untuk pertanyaan ini.
"""

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        logger.info(f"   📝 Answer-first rewrite: {len(text)} → {len(result)} chars (with question context)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to rewrite for speech: {e}")
        return text.replace('\n', ' ')