"""
Topics API — frekuensi topik RAG untuk greeting suggestions (per-role)
"""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

# Mapping sop_topic → display label + icon Material Symbols
# Harus sinkron dengan QuerySchema di rag_engine.py
TOPIC_DISPLAY = {
    "lembur":           {"title": "Kerja Lembur",         "sub": "Aturan, tarif & cara hitung",        "icon": "schedule"},
    "perjalanan_dinas": {"title": "Perjalanan Dinas",      "sub": "Prosedur & reimbursement",           "icon": "flight_takeoff"},
    "tunjangan":        {"title": "Tunjangan & Fasilitas", "sub": "Rincian hak & benefit",              "icon": "payments"},
    "relokasi":         {"title": "Relokasi",              "sub": "Tunjangan penempatan baru",          "icon": "map"},
    "karir":            {"title": "Karir & Mutasi",        "sub": "Kenaikan jabatan & rotasi",          "icon": "trending_up"},
    "phk":              {"title": "PHK & Pensiun",         "sub": "Prosedur & hak karyawan",            "icon": "work_off"},
    "pembelajaran":     {"title": "Pelatihan & Beasiswa",  "sub": "Training & sertifikasi",             "icon": "school"},
    "cuti":             {"title": "Cuti & Dispensasi",     "sub": "Jenis cuti & prosedur pengajuan",    "icon": "event_available"},
    "kesehatan":        {"title": "Fasilitas Kesehatan",   "sub": "BPJS, asuransi & well-being",        "icon": "health_and_safety"},
    "rumah_dinas":      {"title": "Rumah Dinas",           "sub": "Hak hunian & fasilitas tempat tinggal", "icon": "home_work"},
    "disiplin":         {"title": "Disiplin & Etika",      "sub": "Peraturan perilaku & whistleblowing","icon": "gavel"},
    "general":          {"title": "Info HR Umum",          "sub": "Kebijakan & prosedur perusahaan",    "icon": "info"},
}

# Default fallback per role (kalau Redis belum punya data)
DEFAULT_TOPICS_EMPLOYEE = ["lembur", "perjalanan_dinas", "tunjangan", "cuti"]
DEFAULT_TOPICS_HC       = ["karir", "disiplin", "cuti", "phk"]

# Redis key per role
_REDIS_KEY_EMPLOYEE = "denai:topic_freq:employee"
_REDIS_KEY_HC       = "denai:topic_freq:hc"

_HC_ROLES = {"hc", "hr", "admin", "manager"}


@router.get("/api/topics/popular")
async def get_popular_topics(limit: int = 4, role: str = "employee"):
    """Return top N topik paling sering ditanya, dipisah per role (employee / hc)."""
    is_hc = role.lower() in _HC_ROLES
    redis_key   = _REDIS_KEY_HC if is_hc else _REDIS_KEY_EMPLOYEE
    default_list = DEFAULT_TOPICS_HC if is_hc else DEFAULT_TOPICS_EMPLOYEE

    try:
        from memory.memory_hybrid import redis_client, REDIS_AVAILABLE
        if REDIS_AVAILABLE and redis_client:
            raw = await redis_client.zrevrange(redis_key, 0, limit - 1, withscores=True)
            if raw:
                topics = []
                for item in raw:
                    topic_key = item[0] if isinstance(item, (list, tuple)) else item.get("member", "")
                    if isinstance(topic_key, bytes):
                        topic_key = topic_key.decode()
                    display = TOPIC_DISPLAY.get(topic_key, {
                        "title": topic_key.replace("_", " ").title(),
                        "sub": "Informasi & kebijakan",
                        "icon": "help_outline"
                    })
                    topics.append({"topic": topic_key, **display})

                # Pad dengan default kalau kurang dari limit
                if len(topics) < limit:
                    existing = {t["topic"] for t in topics}
                    for t in default_list:
                        if t not in existing and len(topics) < limit:
                            topics.append({"topic": t, **TOPIC_DISPLAY[t]})

                return {"topics": topics}
    except Exception as e:
        logger.debug(f"Topic freq read skipped: {e}")

    # Fallback: return default topics sesuai role
    return {"topics": [{"topic": t, **TOPIC_DISPLAY[t]} for t in default_list[:limit]]}
