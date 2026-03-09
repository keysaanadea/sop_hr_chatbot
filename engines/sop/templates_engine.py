"""
SIMPLE TEMPLATE ENGINE (LLM POWERED)
======================================================
Template HTML dinamis Minimalis (Tanpa Hardcode Domestic/International).
Dilengkapi dengan Placeholder Peringatan/Koreksi Otomatis.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

class SimpleTemplateEngine:
    def __init__(self):
        logger.info("✅ SimpleTemplateEngine (Ultra-Minimalist Edition + Guardrail UI) initialized")
    
    def get_template(self, template_type: str, query: str = "") -> str:
        safe_type = str(template_type).strip().lower()
        logger.info(f"📝 LLM meminta template tipe: {safe_type}")
        
        templates = {
            'general_calculation': self._get_general_calculation_template(),
            'procedure': self._get_procedure_template(),
            'definition': self._get_definition_template(),
            'rules': self._get_rules_template(),
            'general': self._get_general_template()
        }
        
        return templates.get(safe_type, templates['general'])

    # ==========================================
    # KOLEKSI TEMPLATE HTML (SISA 5 SAJA)
    # ==========================================

    def _get_general_calculation_template(self) -> str:
        return """<h3>[Tulis Judul Topik Perhitungan]</h3>
<p>[Berikan pengantar singkat.]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>Rincian Perhitungan / Kalkulasi</h3>
<ul>
  <li>[Jabarkan rumus dan rincian angkanya secara detail. WAJIB perhatikan INFO SISTEM jika ini perhitungan perjalanan dinas!]</li>
</ul>
<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>Sumber:</strong> [Nama File Asli]</li>
  <li><strong>Bagian:</strong> [Bab / Halaman / Lampiran]</li>
</ul>"""
    
    def _get_procedure_template(self) -> str:
        return """<h3>[Tulis Judul Prosedur]</h3>
<p>[Deskripsi singkat tentang prosedur tersebut]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>Langkah-langkah Prosedur</h3>
<ol>
  <li>[Langkah 1]</li>
</ol>
<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>Sumber:</strong> [Nama File Asli]</li>
  <li><strong>Bagian:</strong> [Bab / Halaman / Lampiran]</li>
</ul>"""

    def _get_rules_template(self) -> str:
        return """<h3>[Tulis Judul Aturan / Fasilitas]</h3>
<p>[Berikan penjelasan naratif singkat]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>Rincian Ketentuan / Fasilitas</h3>
<ul>
  <li>[Jabarkan poin-poin fasilitas atau aturan secara SANGAT DETAIL sesuai dokumen. Gunakan sub-bullet jika perlu.]</li>
</ul>
<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>Sumber:</strong> [Nama File Asli]</li>
  <li><strong>Bagian:</strong> [Bab / Halaman / Lampiran]</li>
</ul>"""

    def _get_definition_template(self) -> str:
        return """<h3>[Tulis Istilah / Definisi]</h3>
<p>[Penjelasan komprehensif sesuai dokumen]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>Sumber:</strong> [Nama File Asli]</li>
  <li><strong>Bagian:</strong> [Bab / Halaman / Lampiran]</li>
</ul>"""

    def _get_general_template(self) -> str:
        return """<h3>[Tulis Topik Pertanyaan]</h3>
<p>[Penjelasan naratif berdasarkan dokumen]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>[Sesuaikan Judul Poin-Poin]</h3>
<ul>
  <li>[Poin informasi 1]</li>
</ul>
<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>Sumber:</strong> [Nama File Asli]</li>
  <li><strong>Bagian:</strong> [Bab / Halaman / Lampiran]</li>
</ul>"""
    
    def get_enforcement_instructions(self, template: str) -> str:
        return f"""=== FORMAT & FLEKSIBILITAS JAWABAN ===
Anda diberikan referensi kerangka HTML di bawah ini:

{template}

🚨 ATURAN MUTLAK (SANGAT PENTING):
1. 🌟 JAWABAN DETAIL & NATURAL: JIKA ditanya "Fasilitas apa saja", JABARKAN SEMUA FASILITAS secara terstruktur layaknya standar HRD profesional!
2. 📏 ATURAN JARAK & PENOLAKAN: JIKA jarak < 120 km (Dalam Negeri), TOLAK pengajuan dan hapus rincian fasilitas.
3. 💰 PENJABARAN UPD (WAJIB PATUH!): JIKA membahas Uang Perjalanan Dinas (UPD), WAJIB bedakan kategori Umum, Lokasi Tertentu, dan Pelatihan.
4. 💱 ATURAN MATA UANG, BAND, & PELATIHAN (HARAM DILANGGAR): 
   - 🇮🇩 DALAM NEGERI: Selalu gunakan Rupiah (Rp).
   - 🌍 LUAR NEGERI: WAJIB MATA UANG ASING (US $).
   - 👥 TAMPILKAN SEMUA BAND: JIKA user TIDAK menyebutkan spesifik Band-nya, Anda WAJIB menjabarkan tarif untuk SEMUA Band (Band 1, 2, 3, 4, 5) tanpa terkecuali!
   - 🎓 DISKON PELATIHAN 50%: Tarif untuk tujuan Pelatihan/Training adalah TEPAT 50% (setengah) dari tarif Umum. Anda WAJIB menuliskannya di rincian UPD!
5. 🚫 DILARANG MENULIS 'TIDAK BERLAKU': Jika suatu aturan tidak relevan, HAPUS saja bagian HTML tersebut!
6. 🏨 ATURAN KALKULASI HOTEL/AKOMODASI (WAJIB!): Jika user meminta total hitungan biaya hotel/penginapan untuk N hari, maka jumlah malam pengalinya WAJIB dikurangi 1 (N - 1 malam). Contoh: Jika dinas 5 hari, maka biaya hotel dikalikan 4 malam!
7. ⚠️ TAMPILAN KOREKSI (WAJIB!): JIKA Anda mengoreksi batas maksimal/aturan dari input user, Anda WAJIB MENGGANTI teks [KOTAK_PERINGATAN_KOREKSI] dengan kode HTML persis di bawah ini:
<div style="background-color: #fff3cd; color: #856404; padding: 15px; border-left: 6px solid #ffeeba; margin-bottom: 20px; border-radius: 4px;"><strong>⚠️ PENYESUAIAN ATURAN:</strong> [Tuliskan penjelasan koreksi Anda di sini]</div>
Sebaliknya, JIKA TIDAK ADA KOREKSI, Anda WAJIB MENGHAPUS teks [KOTAK_PERINGATAN_KOREKSI] tersebut agar tidak muncul di jawaban!
"""