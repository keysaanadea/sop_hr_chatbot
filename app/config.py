"""
DENAI Configuration - BALANCED VERSION
Production-ready without over-engineering
"""
import os
from dotenv import load_dotenv
load_dotenv()

# ======================================================
# CORE API KEYS (REQUIRED)
# ======================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# ======================================================
# OPTIONAL EXTERNAL SERVICES
# ======================================================
# Pinecone (used for SOP RAG)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

# ElevenLabs (natural TTS)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID_INDONESIAN = os.getenv(
    "ELEVENLABS_VOICE_ID_INDONESIAN",
    "iWydkXKoiVtvdn4vLKp9"  # Cahaya - Indonesian Female
)

# ======================================================
# MODEL CONFIGURATION
# ======================================================
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2000))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ======================================================
# RAG CONFIGURATION (SOP ENGINE)
# ======================================================
RAG_TOP_K = int(os.getenv("RAG_TOP_K", 5))
RAG_STRICT_MODE = True  # Enforce anti-hallucination behavior

# ======================================================
# MEMORY / SESSION CONFIGURATION
# ======================================================
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", 8))
SESSION_CLEANUP_DAYS = int(os.getenv("SESSION_CLEANUP_DAYS", 30))

# ======================================================
# SPEECH CONFIGURATION
# ======================================================
SPEECH_LANGUAGE_DEFAULT = os.getenv("SPEECH_LANGUAGE_DEFAULT", "id")
TTS_PRIMARY_ENGINE = os.getenv("TTS_PRIMARY_ENGINE", "elevenlabs")
TTS_FALLBACK_ENGINE = os.getenv("TTS_FALLBACK_ENGINE", "openai")

# ======================================================
# 🔥 GROUPED TTS SETTINGS (CLEAN APPROACH)
# ======================================================
ELEVENLABS_SETTINGS = {
    "model": os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5"),
    "stability": float(os.getenv("ELEVENLABS_STABILITY", 0.6)),
    "similarity_boost": float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", 0.8)),
    "style": float(os.getenv("ELEVENLABS_STYLE", 0.2)),
    "use_speaker_boost": os.getenv("ELEVENLABS_USE_SPEAKER_BOOST", "true").lower() == "true"
}

OPENAI_TTS_SETTINGS = {
    "voice": os.getenv("OPENAI_TTS_VOICE", "nova"),
    "speed": float(os.getenv("OPENAI_TTS_SPEED", 0.95))
}

# ======================================================
# TIMEOUT CONFIGURATION (ESSENTIAL ONLY)
# ======================================================
API_TIMEOUT_DEFAULT = int(os.getenv("API_TIMEOUT_DEFAULT", 30))
API_TIMEOUT_CALL_MODE = int(os.getenv("API_TIMEOUT_CALL_MODE", 15))
API_TIMEOUT_TTS = int(os.getenv("API_TIMEOUT_TTS", 8))

# ======================================================
# MODE-SPECIFIC CONSTANTS (NOT ENV-CONFIGURABLE)
# ======================================================
# These are behavioral constants, not environment concerns
CALL_MODE_TEMPERATURE = 0.0        # Deterministic for voice calls
CHAT_MODE_TEMPERATURE = 0.1        # Slightly creative for text
CALL_MODE_MAX_TOKENS = 150         # Concise for voice
CHAT_MODE_MAX_TOKENS = 2000        # Full responses for text

# ======================================================
# MINIMAL FEATURE FLAGS (ONLY WHAT MAKES SENSE)
# ======================================================
FEATURE_NATURAL_TTS = os.getenv("FEATURE_NATURAL_TTS", "true").lower() == "true"
FEATURE_VERBOSE_LOGGING = os.getenv("FEATURE_VERBOSE_LOGGING", "false").lower() == "true"

# ======================================================
# ENVIRONMENT INFO
# ======================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if ENVIRONMENT == "production" else "DEBUG")

# ======================================================
# VALIDATION (MINIMAL & SAFE)
# ======================================================
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required")
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Supabase configuration is required")

# Optional service warnings (do NOT crash app)
if not PINECONE_API_KEY or not PINECONE_INDEX:
    print("⚠️ Pinecone not configured - SOP RAG will be unavailable")
if not ELEVENLABS_API_KEY:
    print("⚠️ ElevenLabs not configured - using OpenAI TTS fallback")

# ======================================================
# 🎯 WHAT WE REMOVED (and why):
# ======================================================
"""
❌ REMOVED - Over-engineered feature flags:
FEATURE_SESSION_MANAGEMENT    # Session is core functionality
FEATURE_TOOL_CALLING         # Tool calling is core functionality

❌ REMOVED - Granular behavioral configs:  
CALL_MODE_TEMPERATURE as env # AI personality shouldn't be env-based
CHAT_MODE_TEMPERATURE as env # These are product decisions, not ops

❌ REMOVED - Excessive performance configs:
MAX_CONCURRENT_REQUESTS      # Infrastructure concern, not app config
MAX_CONCURRENT_TTS          # Should be handled by load balancer

✅ KEPT - Essential configs:
- API keys and credentials
- Model selection (cost/performance trade-off)
- Timeouts (operational concern)
- TTS settings grouped cleanly
- Minimal useful feature flags
"""