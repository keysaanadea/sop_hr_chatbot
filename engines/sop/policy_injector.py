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
        
        # 👇 TAMBAHKAN KALIMAT INI 👇
        tool_info += "🚨 INSTRUKSI TAMPILAN: Anda WAJIB mengawali jawaban Anda dengan menyebutkan Rute dan Estimasi Jarak (km) dari INFO SISTEM ini agar user tahu sistem telah mengeceknya!\n"
                
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
    def get_international_policy_injection(route_str: str, dur_hrs: float) -> str:
        return f"""\n\n=== INFO SISTEM (ESTIMASI PENERBANGAN LUAR NEGERI) ===
Rute: {route_str}
Estimasi Durasi Terbang: {dur_hrs} jam

🚨 INSTRUKSI MUTLAK LUAR NEGERI (WAJIB PATUH!):
1. KELAS PESAWAT: Gunakan angka durasi terbang ({dur_hrs} jam) untuk menentukan hak kelas pesawat (Ekonomi jika < 6 jam, Bisnis jika > 6 jam).
2. MATA UANG: Ini LUAR NEGERI! WAJIB gunakan mata uang asing (US $). DILARANG KERAS MENGGUNAKAN RUPIAH (Rp)!
3. 👥 ATURAN BAND & PELATIHAN (SANGAT PENTING):
   - JIKA user TIDAK menyebutkan Band (jabatan) secara spesifik, Anda WAJIB menjabarkan tarif UPD untuk SEMUA Band (Band 1, Band 2, Band 3-5) secara lengkap!
   - 🧮 RUMUS PELATIHAN (DISKON 50%): Tarif UPD-LN untuk "Tujuan Pelatihan/Training" adalah TEPAT 50% (setengah) dari tarif UPD-LN Umum. Anda WAJIB menghitung diskon 50% ini dan menampilkannya untuk setiap Band!
4. ANTI-HALUSINASI NEGARA: Cari tarif sesuai negara di tabel. Jika tidak ada, gunakan tarif "Negara Terdekat".
"""