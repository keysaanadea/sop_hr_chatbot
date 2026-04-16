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

UNICODE_FRACTION_WORDS = {
    "¼": "seperempat",
    "½": "setengah",
    "¾": "tiga perempat",
    "⅓": "sepertiga",
    "⅔": "dua pertiga",
    "⅛": "seperdelapan",
    "⅜": "tiga perdelapan",
    "⅝": "lima perdelapan",
    "⅞": "tujuh perdelapan",
}

MONTH_NAMES_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}

# Pattern HTML & Rujukan Dokumen
HTML_TAG_PATTERNS = [
    r'<[^>]+>',  # Remove all HTML tags safely
]

TEXT_CLEANUP_PATTERNS = [
    # Hapus bagian rujukan dokumen ke bawah (agar tidak dibaca robot TTS)
    (r'Rujukan Dokumen.*$', ''),
    (r'Sumber:.*$', ''),
    (r'Bagian:.*$', ''),
    (r'\[\d+\]', ''),
    (r'^[•\-\*]\s*', ''),  # Remove bullet points only at line start
    (r'\s{2,}', ' '),     # Multiple spaces to single space
    (r'\n{2,}', '\n'),    # Multiple newlines to single newline
]


def _number_to_indonesian_words(value: int) -> str:
    basic = [
        "", "satu", "dua", "tiga", "empat", "lima",
        "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"
    ]

    if value < 12:
        return basic[value]
    if value < 20:
        return f"{_number_to_indonesian_words(value - 10)} belas"
    if value < 100:
        tens = value // 10
        rest = value % 10
        return f"{_number_to_indonesian_words(tens)} puluh" + (f" {_number_to_indonesian_words(rest)}" if rest else "")
    if value < 200:
        return "seratus" + (f" {_number_to_indonesian_words(value - 100)}" if value > 100 else "")
    if value < 1000:
        hundreds = value // 100
        rest = value % 100
        return f"{_number_to_indonesian_words(hundreds)} ratus" + (f" {_number_to_indonesian_words(rest)}" if rest else "")
    if value < 2000:
        return "seribu" + (f" {_number_to_indonesian_words(value - 1000)}" if value > 1000 else "")
    if value < 1_000_000:
        thousands = value // 1000
        rest = value % 1000
        return f"{_number_to_indonesian_words(thousands)} ribu" + (f" {_number_to_indonesian_words(rest)}" if rest else "")
    if value < 1_000_000_000:
        millions = value // 1_000_000
        rest = value % 1_000_000
        return f"{_number_to_indonesian_words(millions)} juta" + (f" {_number_to_indonesian_words(rest)}" if rest else "")
    if value < 1_000_000_000_000:
        billions = value // 1_000_000_000
        rest = value % 1_000_000_000
        return f"{_number_to_indonesian_words(billions)} miliar" + (f" {_number_to_indonesian_words(rest)}" if rest else "")
    trillions = value // 1_000_000_000_000
    rest = value % 1_000_000_000_000
    return f"{_number_to_indonesian_words(trillions)} triliun" + (f" {_number_to_indonesian_words(rest)}" if rest else "")


def _parse_indonesian_number(raw: str) -> tuple[int, str]:
    normalized = (raw or "").strip().replace(" ", "")
    if not normalized:
        return 0, ""

    if "," in normalized:
        integer_part, decimal_part = normalized.split(",", 1)
    elif normalized.count(".") == 1 and re.fullmatch(r"\d+\.\d+", normalized):
        integer_part, decimal_part = normalized.split(".", 1)
    else:
        integer_part, decimal_part = normalized, ""

    integer_digits = re.sub(r"[^\d]", "", integer_part)
    decimal_digits = re.sub(r"[^\d]", "", decimal_part)
    return int(integer_digits or "0"), decimal_digits


def _decimal_to_indonesian_words(decimal_digits: str) -> str:
    digit_words = ["nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"]
    return " ".join(digit_words[int(d)] for d in decimal_digits if d.isdigit())


def _format_number_for_tts(raw: str) -> str:
    integer_value, decimal_digits = _parse_indonesian_number(raw)
    spoken = _number_to_indonesian_words(integer_value).strip() if integer_value else "nol"

    if decimal_digits and any(ch != "0" for ch in decimal_digits):
        spoken_decimal = _decimal_to_indonesian_words(decimal_digits)
        if spoken_decimal:
            return f"{spoken} koma {spoken_decimal}"

    return spoken


def _normalize_rupiah_for_tts(text: str) -> str:
    def repl(match: re.Match) -> str:
        raw_amount = match.group(1) or ""
        amount, _decimal = _parse_indonesian_number(raw_amount)
        if amount == 0 and not re.search(r"\d", raw_amount):
            return match.group(0)

        if amount == 0:
            return "nol rupiah"

        spoken = _number_to_indonesian_words(amount).strip()
        return f"{spoken} rupiah"

    return re.sub(r"\bRp\s*([0-9][0-9\.\,]*)\b", repl, text, flags=re.IGNORECASE)


def _normalize_compact_amounts_for_tts(text: str) -> str:
    suffix_multipliers = {
        "k": 1_000,
        "rb": 1_000,
        "ribu": 1_000,
        "jt": 1_000_000,
        "juta": 1_000_000,
        "mlyr": 1_000_000_000,
        "miliar": 1_000_000_000,
        "b": 1_000_000_000,
    }

    def repl(match: re.Match) -> str:
        raw_number = match.group(1)
        suffix = match.group(2).lower()
        integer_value, decimal_digits = _parse_indonesian_number(raw_number)
        numeric_value = float(f"{integer_value}.{decimal_digits}") if decimal_digits else float(integer_value)
        expanded_value = int(round(numeric_value * suffix_multipliers[suffix]))
        spoken = _number_to_indonesian_words(expanded_value).strip()
        return spoken

    return re.sub(
        r"\b(\d[\d\.,]*)\s*(k|rb|ribu|jt|juta|mlyr|miliar|b)\b",
        repl,
        text,
        flags=re.IGNORECASE,
    )


def _normalize_dates_and_codes_for_tts(text: str) -> str:
    def repl_date(match: re.Match) -> str:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        month_name = MONTH_NAMES_ID.get(month)
        if not month_name:
            return match.group(0)
        return (
            f"tanggal {_number_to_indonesian_words(day)} "
            f"{month_name} {_number_to_indonesian_words(year)}"
        )

    text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", repl_date, text)

    def repl_code(match: re.Match) -> str:
        value = match.group(0)
        return re.sub(r"\s*/\s*", " garis miring ", value)

    text = re.sub(r"\b(?:[A-Za-z0-9]+/){2,}[A-Za-z0-9]+\b", repl_code, text)
    text = re.sub(r"\b[A-Za-z]+/\d+\b", repl_code, text)
    return text


def _normalize_numbered_units_for_tts(text: str) -> str:
    unit_map = {
        "km": "kilometer",
        "kg": "kilogram",
        "gr": "gram",
        "g": "gram",
        "cm": "sentimeter",
        "mm": "milimeter",
        "m": "meter",
        "jam": "jam",
        "hari": "hari",
        "bulan": "bulan",
        "tahun": "tahun",
        "%": "persen",
        "band": "band",
    }

    def repl_range(match: re.Match) -> str:
        start_raw = match.group(1)
        end_raw = match.group(2)
        unit_raw = match.group(3).lower()
        unit_spoken = unit_map.get(unit_raw, unit_raw)
        start_spoken = _format_number_for_tts(start_raw)
        end_spoken = _format_number_for_tts(end_raw)
        return f"{start_spoken} sampai {end_spoken} {unit_spoken}"

    text = re.sub(
        r"\b(\d[\d\.\,]*)\s*[-–]\s*(\d[\d\.\,]*)\s*(km|kg|gr|g|cm|mm|m|jam|hari|bulan|tahun|band|%)\b",
        repl_range,
        text,
        flags=re.IGNORECASE,
    )

    def repl_unit(match: re.Match) -> str:
        raw_number = match.group(1)
        unit_raw = match.group(2).lower()
        unit_spoken = unit_map.get(unit_raw, unit_raw)
        return f"{_format_number_for_tts(raw_number)} {unit_spoken}"

    return re.sub(
        r"\b(\d[\d\.\,]*)\s*(km|kg|gr|g|cm|mm|m|jam|hari|bulan|tahun|band|%)\b",
        repl_unit,
        text,
        flags=re.IGNORECASE,
    )


def _normalize_remaining_numbers_for_tts(text: str) -> str:
    def repl(match: re.Match) -> str:
        raw_number = match.group(0)
        return _format_number_for_tts(raw_number)

    return re.sub(r"\b\d[\d\.\,]*\b", repl, text)


def _fraction_to_indonesian_words(numerator_raw: str, denominator_raw: str) -> str:
    numerator = _format_number_for_tts(numerator_raw)
    denominator = _format_number_for_tts(denominator_raw)

    special_map = {
        ("1", "2"): "setengah",
        ("1", "3"): "sepertiga",
        ("2", "3"): "dua pertiga",
        ("1", "4"): "seperempat",
        ("3", "4"): "tiga perempat",
        ("1", "8"): "seperdelapan",
        ("3", "8"): "tiga perdelapan",
        ("5", "8"): "lima perdelapan",
        ("7", "8"): "tujuh perdelapan",
    }
    special = special_map.get((numerator_raw.strip(), denominator_raw.strip()))
    if special:
        return special

    return f"{numerator} per {denominator}"


def _normalize_math_expressions_for_tts(text: str) -> str:
    def repl_mixed_unicode_fraction(match: re.Match) -> str:
        whole = _format_number_for_tts(match.group(1))
        fraction = UNICODE_FRACTION_WORDS.get(match.group(2), match.group(2))
        return f"{whole} {fraction}"

    text = re.sub(r"(\d+)\s*([¼½¾⅓⅔⅛⅜⅝⅞])", repl_mixed_unicode_fraction, text)

    def repl_unicode_fraction(match: re.Match) -> str:
        return UNICODE_FRACTION_WORDS.get(match.group(1), match.group(1))

    text = re.sub(r"(?<!\d)([¼½¾⅓⅔⅛⅜⅝⅞])", repl_unicode_fraction, text)

    def repl_mixed_fraction(match: re.Match) -> str:
        whole = _format_number_for_tts(match.group(1))
        fraction = _fraction_to_indonesian_words(match.group(2), match.group(3))
        return f"{whole} {fraction}"

    text = re.sub(r"\b(\d+)\s+(\d+)\s*/\s*(\d+)\b", repl_mixed_fraction, text)

    def repl_fraction(match: re.Match) -> str:
        return _fraction_to_indonesian_words(match.group(1), match.group(2))

    text = re.sub(r"(?<!\d)(\d+)\s*/\s*(\d+)(?!\s*/\s*\d)", repl_fraction, text)

    text = re.sub(r"(?<=[\d\w\)])\s*[x×]\s*(?=[\d\w\(])", " kali ", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<=[\d\w\)])\s*÷\s*(?=[\d\w\(])", " dibagi ", text)
    text = re.sub(r"(?<=[\d\w\)])\s*\+\s*(?=[\d\w\(])", " ditambah ", text)
    text = re.sub(r"(?<=[\d\w\)])\s*=\s*(?=[\d\w\(])", " sama dengan ", text)
    text = re.sub(r"≤", " kurang dari atau sama dengan ", text)
    text = re.sub(r"≥", " lebih dari atau sama dengan ", text)
    text = re.sub(r"±", " plus minus ", text)
    text = re.sub(r"≈", " kurang lebih ", text)
    text = re.sub(r"(?<=\d)\s+-\s+(?=\d)", " kurang ", text)
    text = text.replace("(", " buka kurung ").replace(")", " tutup kurung ")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


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

    # Baca nominal dan angka dengan natural dalam bahasa Indonesia
    text = _normalize_dates_and_codes_for_tts(text)
    text = _normalize_rupiah_for_tts(text)
    text = _normalize_compact_amounts_for_tts(text)
    text = _normalize_math_expressions_for_tts(text)
    text = _normalize_numbered_units_for_tts(text)
    text = _normalize_remaining_numbers_for_tts(text)
    text = re.sub(r"%", " persen", text)
    text = re.sub(r"\s{2,}", " ", text)

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
