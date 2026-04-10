"""
DENAI Auth API - SINTA Integration
====================================
Endpoint untuk menerima data user dari SINTA dan membuat session otomatis.
SINTA memanggil POST /auth/sinta setelah user login, lalu kirim data user.
"""

import logging
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.services.user_context import set_user_context, determine_role_from_unit

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request Model (struktur JSON dari SINTA) ──────────────────────────────────
class SintaPosisi(BaseModel):
    IdJabatan: Optional[str] = None
    Jabatan: Optional[str] = None
    IdUnit: Optional[str] = None
    UnitKerja: Optional[str] = None
    Perusahaan: Optional[str] = None
    Band: Optional[str] = None          # e.g. "Band 3 Fungsional"
    BandAngka: Optional[str] = None     # e.g. "3"


class SintaUserData(BaseModel):
    NIK: Optional[str] = None
    Nama: Optional[str] = None
    FirstName: Optional[str] = None
    MiddleName: Optional[str] = None
    LastName: Optional[str] = None
    Email: Optional[str] = None
    Gender: Optional[str] = None
    Roles: Optional[str] = None
    LokasiKaryawan: Optional[str] = None
    Posisi: Optional[SintaPosisi] = None


class SintaAuthRequest(BaseModel):
    """Body JSON yang dikirim SINTA ke Denai."""
    status: Optional[str] = None
    message: Optional[str] = None
    data: SintaUserData


# ── Response Model ────────────────────────────────────────────────────────────
class SintaAuthResponse(BaseModel):
    session_id: str
    role: str           # "hc" atau "karyawan"
    nama: str
    first_name: str
    nik: str
    band: str           # e.g. "Band 3 Fungsional"
    band_angka: str     # e.g. "3"
    unit: str
    jabatan: str
    lokasi: str         # e.g. "Jakarta"


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.post("/auth/sinta", response_model=SintaAuthResponse)
async def auth_from_sinta(req: SintaAuthRequest):
    """
    Terima data user dari SINTA, buat session Denai, tentukan role otomatis.

    Flow:
    1. SINTA POST /auth/sinta dengan data user
    2. Denai generate session_id baru
    3. Simpan context user (nama, nik, band, role) ke session store
    4. Return session_id + info role untuk dipakai frontend Denai
    """
    user = req.data
    posisi = user.Posisi or SintaPosisi()

    nama = user.Nama or "User"
    first_name = user.FirstName or nama.split()[0]
    nik = user.NIK or ""
    unit = posisi.UnitKerja or ""
    band = posisi.Band or ""
    band_angka = posisi.BandAngka or "0"
    jabatan = posisi.Jabatan or ""
    lokasi = user.LokasiKaryawan or ""

    # Tentukan role otomatis berdasarkan unit
    role = determine_role_from_unit(unit)

    # Generate session_id unik untuk user ini
    session_id = str(uuid.uuid4())

    # Simpan ke store
    set_user_context(session_id, {
        "nama": nama,
        "first_name": first_name,
        "nik": nik,
        "unit": unit,
        "band": band,
        "band_angka": band_angka,
        "jabatan": jabatan,
        "lokasi": lokasi,
        "role": role,
        "email": user.Email or "",
    })

    logger.info(
        f"🔐 SINTA Auth | nama={nama} | nik={nik} | unit={unit} | "
        f"lokasi={lokasi} | band={band_angka} | role={role} | session={session_id[:8]}..."
    )

    return SintaAuthResponse(
        session_id=session_id,
        role=role,
        nama=nama,
        first_name=first_name,
        nik=nik,
        band=band,
        band_angka=band_angka,
        unit=unit,
        jabatan=jabatan,
        lokasi=lokasi,
    )
