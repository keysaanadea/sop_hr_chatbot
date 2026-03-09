"""
DENAI Text Utils
Text cleaning and processing utilities for TTS and chat
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# TTS text cleaning constants
TTS_EMOJIS_TO_REMOVE = [
    '✅', '❌', '🔒', '⏰', '❓', '🌐', '📞', '💰', '🎯', 
    '🚀', '🤖', '📊', '📈', '📉', '💡', '🔥', '🎤', '🔊',
    '📌', '🗑️', '🧹', '✨', '🕵️‍♂️'
]

# Pattern HTML & Rujukan Dokumen
HTML_TAG_PATTERNS = [
    r'<[^>]+>',  # Remove all HTML tags safely
]

TEXT_CLEANUP_PATTERNS = [
    # Hapus bagian rujukan dokumen ke bawah (agar tidak dibaca robot TTS)
    (r'Rujukan Dokumen.*$', ''),
    (r'Sumber:.*$', ''),
    (r'Bagian:.*$', ''),
    (r'[•\-\*]\s*', ''),  # Remove bullet points
    (r'\s{2,}', ' '),     # Multiple spaces to single space
    (r'\n{2,}', '\n'),    # Multiple newlines to single newline
]


def clean_text_for_tts(html_text: str, preserve_structure: bool = False) -> str:
    """
    Clean HTML text for natural TTS speech
    Menghapus tag HTML, emoji, dan bagian rujukan dokumen.
    """
    if not html_text:
        return ""
    
    logger.debug("🧹 Cleaning text for natural TTS")
    text = html_text
    
    # Remove HTML tags
    for pattern in HTML_TAG_PATTERNS:
        text = re.sub(pattern, ' ', text)
    
    # Hapus rujukan dokumen menggunakan regex multi-line
    for pattern, replacement in TEXT_CLEANUP_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.DOTALL)
    
    # Remove problematic emojis
    for emoji in TTS_EMOJIS_TO_REMOVE:
        text = text.replace(emoji, '')
    
    # Final cleanup
    text = text.strip()
    logger.debug(f"Text cleaned: {len(html_text)} → {len(text)} chars")
    
    return text


def clean_text_for_display(text: str) -> str:
    """
    Clean text for display purposes (minimal cleaning)
    """
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def truncate_for_mode(text: str, mode: str = "chat", max_length: int = None) -> str:
    """
    Truncate text based on conversation mode
    """
    if not text:
        return ""
    
    max_len = max_length if max_length is not None else (150 if mode == "call" else 2000)
    
    if len(text) <= max_len:
        return text
    
    if mode == "call":
        return text[:max_len-15].strip() + "... Butuh detail?"
    return text[:max_len-3].strip() + "..."


def truncate_for_call_mode(text: str) -> str:
    """Convenience function for call mode truncation"""
    return truncate_for_mode(text, mode="call")


def validate_text_length(text: str, max_chars: int = 5000) -> Tuple[bool, str]:
    """
    Validate text length for processing
    """
    if not text or not text.strip():
        return False, "Text is empty"
    
    if len(text) > max_chars:
        return False, f"Text too long: {len(text)} chars (max {max_chars})"
    
    return True, ""