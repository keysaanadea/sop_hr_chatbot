import re
from typing import Optional

# =====================
# HARD RULE CONFIG
# =====================
ALLOWED_LEMBUR_BANDS = {"5"}

# =====================
# SOP HARD RULES
# =====================
def apply_hard_rules(question: str) -> Optional[str]:
    """
    Hard rules khusus SOP.
    Jika rule terpenuhi → langsung return jawaban SOP.
    Jika tidak → return None (lanjut ke RAG).
    """
    q = question.lower()

    # Rule: lembur + band
    match = re.search(r"band\s*(\d+)", q)
    if match and "lembur" in q:
        band = match.group(1)
        if band not in ALLOWED_LEMBUR_BANDS:
            return (
                "Berdasarkan ketentuan SOP perusahaan, hanya karyawan Band 5 "
                "yang berhak menerima Upah Kerja Lembur. "
                "Karyawan pada band selain Band 5 tidak berhak menerima "
                "Upah Kerja Lembur."
            )

    return None


# =====================
# HR ACCESS RULE
# =====================
def is_hr_allowed(user: dict) -> bool:
    """
    Rule akses HR Mode.
    """
    return user.get("role") == "HR"
