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
<p>[Berikan 1 kalimat pengantar singkat saja. DILARANG KERAS menulis rumus/angka/aturan di sini!]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>Rincian Perhitungan / Kalkulasi</h3>
<ul>
  <li>[Jabarkan syarat kelayakannya secara detail. WAJIB akhiri dengan nomor sitasi gaya akademik, contoh: [1]]</li>
  <li>[Jabarkan rumus dan rincian angkanya. WAJIB perhatikan INFO SISTEM jika ini perjalanan dinas! WAJIB akhiri dengan nomor sitasi, contoh: [2]]</li>
</ul>
<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>[{N}] Sumber:</strong> [Nama File] | <strong>Bagian:</strong> [Pasal/Bab spesifik dari file tersebut]</li>
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
  <li><strong>[{N}] Sumber:</strong> [Nama File] | <strong>Bagian:</strong> [Pasal/Bab spesifik dari file tersebut]</li>
</ul>"""

    def _get_rules_template(self) -> str:
        return """<h3>[Tulis Judul Aturan / Fasilitas]</h3>
<p>[Berikan 1 kalimat pengantar singkat saja. DILARANG KERAS menulis rincian aturan/angka di sini!]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>Rincian Ketentuan / Fasilitas</h3>
<ul>
  <li>[Jabarkan aturan kelayakan atau syarat utama. WAJIB akhiri dengan nomor sitasi, contoh: [1]]</li>
  <li>[Jabarkan nominal atau detail fasilitas selanjutnya. WAJIB akhiri dengan nomor sitasi, contoh: [2]]</li>
</ul>
<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>[{N}] Sumber:</strong> [Nama File] | <strong>Bagian:</strong> [Pasal/Bab spesifik dari file tersebut]</li>
</ul>"""

    def _get_definition_template(self) -> str:
        return """<h3>[Tulis Istilah / Definisi]</h3>
<p>[Penjelasan komprehensif sesuai dokumen]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>[{N}] Sumber:</strong> [Nama File] | <strong>Bagian:</strong> [Pasal/Bab spesifik dari file tersebut]</li>
</ul>"""

    def _get_general_template(self) -> str:
        return """<h3>[Tulis Topik Pertanyaan]</h3>
<p>[Berikan 1 kalimat pengantar singkat saja. DILARANG KERAS menulis rincian aturan/angka di sini!]</p>

[KOTAK_PERINGATAN_KOREKSI]

<h3>[Sesuaikan Judul Poin-Poin]</h3>
<ul>
  <li>[Jabarkan poin informasi pertama. WAJIB akhiri dengan nomor sitasi, contoh: [1]]</li>
  <li>[Jabarkan poin informasi kedua (jika ada). WAJIB akhiri dengan nomor sitasi, contoh: [2]]</li>
</ul>
<h3>Rujukan Dokumen</h3>
<ul>
  <li><strong>[{N}] Sumber:</strong> [Nama File] | <strong>Bagian:</strong> [Pasal/Bab spesifik dari file tersebut]</li>
</ul>"""
    
    def get_enforcement_instructions(self, template: str) -> str:
        return f"""=== FORMAT OUTPUT (WAJIB DIIKUTI) ===
🚨 OUTPUT ANDA HARUS BERUPA HTML MURNI — BUKAN PLAIN TEXT. Gunakan tag <h3>, <p>, <ul>, <li>, <ol>, <strong> sesuai struktur template di bawah ini. DILARANG menulis paragraf teks biasa tanpa tag HTML.

Kerangka HTML yang WAJIB Anda ikuti strukturnya:

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
10. 🔎 ELIGIBILITY CHECK (WAJIB!): Untuk pertanyaan "apakah saya wajib/berhak/eligible/dapat", BACA daftar yang eligible KATA PER KATA dari dokumen. JANGAN generalisasi antar entitas yang berbeda. Contoh: "Karyawan Band-1 AP Semen" adalah entitas berbeda dari "Karyawan Band-1 AP Non Semen" — keduanya TIDAK bisa disamakan meskipun sama-sama Band-1. Jika entitas yang ditanyakan user TIDAK muncul PERSIS di daftar → jawab TIDAK WAJIB / TIDAK BERHAK dengan tegas sejak kalimat pertama.
6. 🏨 ATURAN KALKULASI HOTEL/AKOMODASI (WAJIB!): Jika user meminta total hitungan biaya hotel/penginapan untuk N hari, maka jumlah malam pengalinya WAJIB dikurangi 1 (N - 1 malam). Contoh: Jika dinas 5 hari, maka biaya hotel dikalikan 4 malam!
7. ⚠️ TAMPILAN KOREKSI (HUKUM BESI — TIDAK BOLEH DILANGGAR): Teks literal "[KOTAK_PERINGATAN_KOREKSI]" DILARANG KERAS muncul di output final Anda. Anda WAJIB memilih salah satu dari dua tindakan berikut:
   a) JIKA Anda mengoreksi/menyesuaikan asumsi atau aturan dari pertanyaan user → GANTI [KOTAK_PERINGATAN_KOREKSI] dengan kode HTML berikut (isi bagian [Tuliskan...] dengan penjelasan koreksi Anda):
<div style="background-color: #fff9f0; border: 1px solid rgba(245,225,192,0.35); border-radius: 16px; padding: 28px 32px; margin-bottom: 20px; position: relative; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);"><div style="position: absolute; top: -40px; right: -40px; width: 120px; height: 120px; background-color: #fde68a; opacity: 0.15; border-radius: 50%;"></div><div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;"><span class="material-symbols-outlined" style="color: #d97706; font-size: 18px; font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;">gavel</span><span style="font-size: 11px; font-weight: 800; color: #92400e; text-transform: uppercase; letter-spacing: 0.2em;">Penyesuaian Aturan</span></div><div style="color: #78350f; font-size: 14px; line-height: 1.7;">[Tuliskan penjelasan koreksi Anda di sini]</div></div>
   b) JIKA tidak ada koreksi → HAPUS teks [KOTAK_PERINGATAN_KOREKSI] sepenuhnya.
   🚫 PILIHAN KETIGA TIDAK ADA — membiarkan [KOTAK_PERINGATAN_KOREKSI] apa adanya adalah KESALAHAN FATAL.
8. 📎 ATURAN RUJUKAN DOKUMEN (WAJIB!): Bagian `<h3>Rujukan Dokumen</h3>` adalah tempat Anda menjabarkan sumber dari sitasi yang Anda pasang di paragraf atas. Format wajib per baris: `<li><strong>[{{N}}] Sumber:</strong> [Nama File] | <strong>Bagian:</strong> [Pasal/Bab spesifik dari file tersebut]</li>`.
   - 🌟 GANTI `{{N}}` dengan nomor urut [1], [2], dst., dimulai dari angka 1. Urutan ini HARUS SINKRON dengan nomor sitasi yang Anda tulis di paragraf. Jangan cetak angka yang melompat (misal tiba-tiba [4]) tanpa ada [1], [2], [3] sebelumnya.
   - Pasal/Bab yang ditulis harus memang berasal dari file tersebut — jangan campur pasal lintas file dalam satu baris.
   - JIKA Anda tidak menggunakan dokumen apa pun dari [KNOWLEDGE BASE] — HAPUS SELURUH blok Rujukan Dokumen.
9. 🔄 KONSISTENSI WAJIB (KRITIS!): Narasi pembuka/pengantar HARUS KONSISTEN dengan rincian di bawahnya. DILARANG KERAS menulis pernyataan umum di pengantar yang bertentangan dengan rincian spesifik dari dokumen. Khusus untuk pertanyaan ELIGIBILITAS (siapa yang berhak): tulis siapa yang berhak dengan tepat sejak kalimat pertama — jangan tulis "diberikan kepada A dan B" di pengantar lalu "hanya untuk B" di rincian. Baca dulu seluruh chunk, tentukan jawabannya, baru tulis dari awal secara konsisten.
11. 📋 KELENGKAPAN JAWABAN (WAJIB!): Anda WAJIB menyampaikan SELURUH informasi yang relevan dari [KNOWLEDGE BASE] untuk menjawab pertanyaan user. DILARANG memotong, meringkas berlebihan, atau menghilangkan poin-poin penting yang ada di dokumen. Setiap aturan, syarat, pengecualian, angka, dan ketentuan yang relevan HARUS dicantumkan — tidak ada yang boleh di-skip. Jika dokumen menyebut beberapa kondisi atau kategori, SEMUA kondisi dan kategori tersebut wajib dijelaskan. Lebih baik jawaban panjang dan lengkap daripada jawaban singkat yang kehilangan informasi penting.
"""