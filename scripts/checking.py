import os
from pathlib import Path

def reset_and_verify_db(db_path: str = "engines/hr/employees.db"):
    print(f"🔍 Mengecek keberadaan database di: {db_path}")
    
    # 1. Proses Penghapusan
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"✅ File {db_path} berhasil dihapus.")
        except Exception as e:
            print(f"❌ Gagal menghapus file: {e}")
            return
    else:
        print("ℹ️ File tidak ditemukan, asumsi sudah kosong.")

    # 2. Verifikasi Akhir
    if not os.path.exists(db_path):
        print("🎯 VERIFIKASI: Database bener-bener KOSONG (File sudah tidak ada).")
        print("🚀 Anda bisa menjalankan 'enhanced_csv_integration.py' sekarang.")
    else:
        print("⚠️ VERIFIKASI GAGAL: File masih terdeteksi.")

if __name__ == "__main__":
    # Sesuaikan path sesuai folder di screenshot Anda
    reset_and_verify_db()