# File: engines/sop/policy_injector.py

class HRTravelPolicy:
    """
    Pusat semua aturan logika dan matematika HRD untuk Perjalanan Dinas.
    Jika ada perubahan kebijakan perusahaan, cukup ubah angka di file ini.
    """
    
    @staticmethod
    def get_domestic_policy_injection(route_str: str, dist_km: float, dur_hrs: float) -> str:
        # Inisialisasi dasar
        tool_info = f"\n\n=== INFO SISTEM (ESTIMASI GOOGLE MAPS) ===\nRute: {route_str}\nJarak Asli: {dist_km} km\nDurasi Perjalanan Darat: {dur_hrs} jam\n"
        
        tool_info += f"ℹ️ INFO SISTEM sudah mencantumkan jarak {dist_km} km untuk rute {route_str}. Gunakan angka ini jika perlu menyebutkan jarak.\n"
                
        # 1. LOGIKA JARAK & PENOLAKAN
        if dist_km < 120:
            tool_info += "🚨 HUKUM MUTLAK PERUSAHAAN: Perjalanan < 120 km BUKAN TERMASUK PERJALANAN DINAS. Karyawan TIDAK BERHAK mendapatkan UPD, Akomodasi, atau Fasilitas. JIKA jarak < 120 km, Anda WAJIB menolak pengajuannya dan JANGAN TAMPILKAN fasilitas apapun!\n"
        
        elif 120 <= dist_km <= 240:
            tool_info += """💡 ATURAN UPD (120 - 240 km): Karyawan ini masuk dalam kategori jarak menengah. JIKA Anda membahas Uang Perjalanan Dinas (UPD), Anda WAJIB menjabarkannya dalam bentuk poin-poin dan HANYA BOLEH menampilkan 2 opsi ini:
1. Kategori "Dalam Negeri Khusus"
2. Kategori "Tujuan Pelatihan/Training/Workshop"
🚨 ATURAN DEFAULT HITUNGAN: JIKA user meminta total kalkulasi uang TAPI tidak menyebutkan tujuan spesifik (seperti pelatihan), WAJIB GUNAKAN tarif "Dalam Negeri Khusus" sebagai default hitungan! DILARANG menggunakan tarif Umum/Lokasi Tertentu!\n"""
        
        else: # Jarak > 240 km
            tool_info += """💡 ATURAN UPD (> 240 km): Karyawan ini masuk kategori jarak jauh. JIKA Anda membahas Uang Perjalanan Dinas (UPD), WAJIB MENAMPILKAN KETIGA OPSI INI SECARA LENGKAP agar karyawan bisa memilih:
1. "Dalam Negeri Umum"
2. "Lokasi Tertentu" (Pabrik/Kantor SIG)
3. "Tujuan Pelatihan/Training/Workshop"
🚨 ATURAN DEFAULT HITUNGAN: JIKA user meminta total kalkulasi uang TAPI tidak secara spesifik menyebut tujuannya ke pabrik SIG atau pelatihan, WAJIB MENGGUNAKAN tarif "Dalam Negeri Umum" sebagai DEFAULT perhitungan akhir!\n"""

        # 2. RUMUS MATEMATIKA ANTI-RUGI (HOTEL)
        tool_info += """🧮 ATURAN MATEMATIKA AKOMODASI (HOTEL): JIKA Anda menghitung total biaya akomodasi/hotel berdasarkan jumlah hari, INGAT RUMUS MUTLAK INI: Jumlah Malam = (Jumlah Hari - 1). JADI, kalikan tarif plafon hotel dengan (Jumlah Hari - 1 malam)!\n"""


        return tool_info
        
    @staticmethod
    def get_international_policy_injection(route_str: str, dur_hrs: float, idr_rate: float = 0.0) -> str:
        _currency_note = ""
        if idr_rate and idr_rate > 0:
            _currency_note = (
                f"\n   Kurs saat ini: 1 USD = Rp {idr_rate:,.0f} (diperbarui otomatis)."
                f"\n   Tampilkan setiap nominal dalam format: US $X (≈ Rp Y) agar karyawan mudah memahami."
            ).replace(",", ".")
        return f"""\n\n=== INFO SISTEM (ESTIMASI PENERBANGAN LUAR NEGERI) ===
Rute: {route_str}
Estimasi Durasi Terbang: {dur_hrs} jam

🚨 INSTRUKSI MUTLAK LUAR NEGERI (WAJIB PATUH TANPA TERKECUALI!):
1. WAJIB AWALI JAWABAN dengan menyebutkan Rute dan Estimasi Durasi Terbang dari INFO SISTEM ini, lalu terapkan aturan kelas pesawat dari [KNOWLEDGE BASE] berdasarkan durasi {dur_hrs} jam tersebut dan sebutkan hasilnya secara eksplisit.
2. MATA UANG: Ini LUAR NEGERI! Tarif UPD-LN dalam US $.{_currency_note}
3. 👥 TAMPILAN UPD WAJIB — SELALU TAMPILKAN 2 OPSI BERIKUT untuk SEMUA Band (Band 1, Band 2, Band 3-5):
   a. UPD Umum (tarif penuh sesuai tabel)
   b. UPD Pelatihan/Training/Workshop = TEPAT 50% dari tarif UPD Umum (hitung dan tampilkan angkanya per Band)
   🚨 KEDUA OPSI INI WAJIB SELALU DITAMPILKAN meski user tidak minta — agar karyawan tahu perbedaannya!
4. ANTI-HALUSINASI NEGARA: Cari tarif sesuai negara di tabel. Jika tidak ada, gunakan tarif "Negara Terdekat".
"""