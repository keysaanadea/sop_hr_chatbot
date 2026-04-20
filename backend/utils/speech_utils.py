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

    is_calculation_heavy = any(marker in text.lower() for marker in [
        "rincian perhitungan", "kalkulasi", "tarif lembur", "uang lembur",
        "1/173", "=", " x ", " kali ", "ditambah", "sama dengan"
    ])

    # Build context-aware prompt
    if question and question.strip():
        context_info = f"""
PERTANYAAN USER:
"{question}"

Fokus jawab pertanyaan ini dulu, baru kasih supporting details!
"""
    else:
        context_info = ""

    calculation_rules = ""
    if is_calculation_heavy:
        calculation_rules = """

ATURAN TAMBAHAN KHUSUS TEKS KALKULASI:
8. Jika teks berisi rumus atau perhitungan, JANGAN bacakan simbol, operator, atau persamaan satu per satu seperti robot.
9. Ubah rumus menjadi penjelasan kontekstual yang natural.
10. Jelaskan dengan urutan seperti orang menjelaskan lewat telepon:
   - sebut dulu hasil akhirnya,
   - lalu jelaskan cara hitungnya secara singkat,
   - lalu sebut angka pentingnya.
11. Boleh menyebut langkah hitung, tapi dalam kalimat natural.
12. Hindari gaya seperti:
   - "satu per seratus tujuh puluh tiga dikali..."
   - "sama dengan..."
   - "buka kurung... tutup kurung..."
13. Untuk lembur, jelaskan contohnya seperti:
   - "Per jam nilainya sekitar ..."
   - "Jam pertama dibayar satu setengah kali tarif per jam"
   - "Jam berikutnya dibayar dua kali tarif per jam"
   - "Jadi total untuk tiga jam sekitar ..."

CONTOH GAYA YANG DIINGINKAN:
❌ BURUK: "Tarif lembur standar satu per seratus tujuh puluh tiga kali lima juta tujuh ratus ribu sama dengan ..."
✅ BAGUS: "Kalau gaji pokok Anda lima juta tujuh ratus ribu, tarif lembur per jamnya sekitar tiga puluh dua ribu sembilan ratus rupiah. Jam pertama dibayar satu setengah kali tarif itu, lalu dua jam berikutnya dibayar dua kali tarif per jam. Jadi total lembur untuk tiga jam sekitar seratus lima belas ribu rupiah."
"""

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
6. Bunyikan jawaban seperti orang sedang menjelaskan lewat telepon, bukan membaca dokumen
7. Jangan sebut nomor sitasi, label rujukan, atau judul bagian seperti "Rujukan Dokumen"
8. Jika ada angka penting, nominal uang, jumlah hari, jumlah jam, tarif, atau total, tuliskan dalam BENTUK KATA-KATA bahasa Indonesia, jangan pakai digit angka.
9. Contoh: 65.800 menjadi "enam puluh lima ribu delapan ratus", 115.151 menjadi "seratus lima belas ribu seratus lima puluh satu".
{calculation_rules}

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
        result = " ".join(result.split())
        logger.info(f"   📝 Answer-first rewrite: {len(text)} → {len(result)} chars (with question context)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to rewrite for speech: {e}")
        return text.replace('\n', ' ')
