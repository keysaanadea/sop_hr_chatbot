"""
Endpoint untuk membuka dokumen PDF dari folder documents/ dan documents_global/.
Mendukung fuzzy matching: nama dari Pinecone metadata tidak harus persis sama dengan nama file PDF.
"""

import os
import re
import unicodedata
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Folder dokumen yang dicari (urutan prioritas)
_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC_DIRS = [
    os.path.join(_BASE, "documents"),
    os.path.join(_BASE, "documents_global"),
]


def _normalize(name: str) -> str:
    """Normalisasi nama: hapus ekstensi, lowercase, collapse whitespace/simbol."""
    name = os.path.splitext(name)[0]                          # buang .pdf
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")     # buang karakter non-ASCII
    name = name.lower()
    name = re.sub(r"[\s_\-&,\.()]+", " ", name).strip()       # normalisasi pemisah
    return name


def find_pdf(query: str) -> str | None:
    """
    Cari PDF yang cocok dengan query (nama dari LLM / Pinecone metadata).
    Urutan pencarian:
      1. Exact normalized match
      2. Query adalah substring dari nama file
      3. Nama file adalah substring dari query
      4. Token overlap terbanyak (minimal 2 token sama)
    """
    q_norm = _normalize(query)
    logger.info(f"🔍 Mencari dokumen: '{query}' → normalized: '{q_norm}'")

    candidates = []
    for d in DOC_DIRS:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.lower().endswith(".pdf"):
                continue
            f_norm = _normalize(fname)
            candidates.append((os.path.join(d, fname), fname, f_norm))

    if not candidates:
        logger.warning("Tidak ada file PDF ditemukan di folder documents/")
        return None

    # 1. Exact normalized match
    for path, fname, f_norm in candidates:
        if f_norm == q_norm:
            logger.info(f"✅ Exact match: {fname}")
            return path

    # 2. Query substring dari nama file
    for path, fname, f_norm in candidates:
        if q_norm in f_norm:
            logger.info(f"✅ Query in filename: {fname}")
            return path

    # 3. Nama file substring dari query
    for path, fname, f_norm in candidates:
        if f_norm in q_norm:
            logger.info(f"✅ Filename in query: {fname}")
            return path

    # 4. Token overlap
    q_tokens = set(q_norm.split())
    best_overlap = 0
    best_path = None
    for path, fname, f_norm in candidates:
        f_tokens = set(f_norm.split())
        overlap = len(q_tokens & f_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_path = path

    if best_overlap >= 2:
        logger.info(f"✅ Token overlap ({best_overlap}): {best_path}")
        return best_path

    logger.warning(f"❌ Tidak ditemukan dokumen untuk: '{query}'")
    return None


@router.get("/api/docs/preview")
async def preview_document(name: str):
    """
    Kembalikan metadata + cuplikan teks dari PDF untuk ditampilkan di panel samping.
    """
    path = find_pdf(name)
    if not path:
        raise HTTPException(status_code=404, detail=f"Dokumen '{name}' tidak ditemukan.")

    filename = os.path.basename(path)
    preview_text = ""

    try:
        import pypdf
        reader = pypdf.PdfReader(path)
        num_pages = len(reader.pages)
        # Ambil teks dari halaman pertama (maks 600 karakter)
        for page in reader.pages[:3]:
            text = (page.extract_text() or "").strip()
            if text:
                preview_text += text + " "
            if len(preview_text) >= 600:
                break
        preview_text = preview_text.strip()[:600]
        if len(preview_text) == 600:
            preview_text += "..."
    except Exception as e:
        logger.warning(f"Gagal extract teks PDF: {e}")
        num_pages = 0

    return {
        "filename": filename,
        "num_pages": num_pages,
        "preview_text": preview_text,
        "open_url": f"/api/docs/open?name={name}",
    }


@router.get("/api/docs/open")
async def open_document(name: str):
    """
    Buka / serve PDF berdasarkan nama (dari Pinecone metadata / LLM citation).
    Fuzzy match otomatis — nama tidak harus persis sama dengan nama file di disk.
    """
    path = find_pdf(name)
    if not path:
        raise HTTPException(
            status_code=404,
            detail=f"Dokumen '{name}' tidak ditemukan di server."
        )
    filename = os.path.basename(path)
    return FileResponse(
        path=path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{filename}\""},
    )
