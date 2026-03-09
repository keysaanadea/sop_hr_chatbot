"""
DENAI Utils Module
Text processing and speech utility functions
"""

# ✅ Mengambil fungsi-fungsi MURNI dari text_utils yang sudah kita bersihkan
from .text_utils import (
    clean_text_for_tts,
    clean_text_for_display,
    truncate_for_mode,
    truncate_for_call_mode,
    validate_text_length
)

# ✅ Mendaftarkan fungsi dari speech_utils sekalian agar modul ini lengkap
from .speech_utils import (
    rewrite_for_speech
)

__all__ = [
    # Text Utils
    "clean_text_for_tts",
    "clean_text_for_display", 
    "truncate_for_mode",
    "truncate_for_call_mode",
    "validate_text_length",
    
    # Speech Utils
    "rewrite_for_speech"
]