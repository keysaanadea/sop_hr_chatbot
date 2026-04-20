# File: engines/sop/policy_injector.py

class HRTravelPolicy:
    """
    Facts injector untuk Perjalanan Dinas.
    HANYA menyuntikkan fakta runtime dari tool (rute, jarak, durasi, kurs),
    bukan aturan bisnis / kebijakan perusahaan. Seluruh aturan normatif harus
    diambil dari dokumen hasil retrieval, bukan di-hardcode di file ini.
    """
    
    @staticmethod
    def get_domestic_policy_injection(route_str: str, dist_km: float, dur_hrs: float) -> str:
        return (
            "\n\n=== INFO SISTEM (FAKTA RUNTIME) ===\n"
            f"Rute: {route_str}\n"
            f"Jarak Asli: {dist_km} km\n"
            f"Durasi Perjalanan Darat: {dur_hrs} jam\n"
            "\n"
            "Gunakan fakta runtime di atas hanya sebagai data bantu.\n"
            "Aturan kelayakan, kategori UPD, nominal, akomodasi, dan formula perhitungan\n"
            "WAJIB ditentukan dari [KNOWLEDGE BASE], bukan dari INFO SISTEM ini.\n"
        )
        
    @staticmethod
    def get_international_policy_injection(route_str: str, dur_hrs: float, idr_rate: float = 0.0) -> str:
        _currency_note = ""
        if idr_rate and idr_rate > 0:
            _currency_note = (
                f"\n   Kurs saat ini: 1 USD = Rp {idr_rate:,.0f} (diperbarui otomatis)."
                f"\n   Tampilkan setiap nominal dalam format: US $X (≈ Rp Y) agar karyawan mudah memahami."
            ).replace(",", ".")
        return f"""\n\n=== INFO SISTEM (FAKTA RUNTIME LUAR NEGERI) ===
Rute: {route_str}
Estimasi Durasi Terbang: {dur_hrs} jam

Gunakan fakta runtime di atas hanya sebagai data bantu.{_currency_note}
Aturan kelas pesawat, tarif UPD-LN, kategori perjalanan, dan ketentuan lain
WAJIB diambil dari [KNOWLEDGE BASE], bukan dari INFO SISTEM ini.
"""
