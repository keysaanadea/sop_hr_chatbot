"""
ENHANCED DENAI Configuration - WITH DOCUMENT INGESTION SUPPORT
==============================================================
Clean infrastructure config + Document ingestion pipeline support
UPDATED: Added complete RAG document processing configuration + Google Maps API + Cohere Reranker
"""
import os
import logging
from dotenv import load_dotenv

# Setup basic logger for config
logger = logging.getLogger("config")
load_dotenv()

# ======================================================
# CORE API KEYS (REQUIRED FOR FULL FUNCTIONALITY)
# ======================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# ======================================================
# SUPABASE DATABASE CONFIGURATION (HR CSV INGESTION)
# ======================================================
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_CONNECTION_STRING")

# ======================================================
# OPTIONAL EXTERNAL SERVICES
# ======================================================
# Pinecone (SOP RAG)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
PINECONE_GLOBAL_INDEX = os.getenv("PINECONE_GLOBAL_INDEX", "global-knowledge")

# ⚡ Upstash Redis (Chat History Cache)
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN")

# Cohere Reranker
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_MODEL = os.getenv("COHERE_MODEL", "rerank-multilingual-v3.0")

# Google Maps API
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ElevenLabs (Natural TTS)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID_INDONESIAN = os.getenv("ELEVENLABS_VOICE_ID_INDONESIAN", "iWydkXKoiVtvdn4vLKp9")

# ======================================================
# MODEL CONFIGURATION
# ======================================================
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2000))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ======================================================
# DOCUMENT INGESTION CONFIGURATION (RAG PIPELINE)
# ======================================================
PROJECT_ROOT = os.getenv("PROJECT_ROOT", os.getcwd())

# 🌟 FIX BUG: Alias direktori kini konsisten dan tidak saling timpa!
PDF_DIR = os.path.join(PROJECT_ROOT, "documents")
CHUNK_DIR = os.path.join(PROJECT_ROOT, "chunks") 
EMBEDDINGS_DIR = os.path.join(PROJECT_ROOT, "embeddings")

DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", PDF_DIR)
CHUNKS_DIR = os.getenv("CHUNKS_DIR", CHUNK_DIR)

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

# Chunking Limits
CHUNK_MAX_TOKENS = int(os.getenv("CHUNK_MAX_TOKENS", 450))
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", 400))
CHUNK_MIN_CHARS = int(os.getenv("CHUNK_MIN_CHARS", 80))

# Behavior
ENABLE_MERGE = os.getenv("ENABLE_MERGE", "true").lower() == "true"
REMOVE_DUPLICATES = os.getenv("REMOVE_DUPLICATES", "true").lower() == "true"

HEADER_PATTERNS = {
    'pasal': r'^Pasal\s+\d+',
    'bab_romawi': r'^([IVX]+)\.\s+[A-Z]',
    'section_alpha': r'^[A-Z]\.\s+[A-Z]',
    'numbered': r'^\d+\.\s+[A-Z]',
    'sub_alpha': r'^[a-z]\.\s+[a-z]',
    'sub_numbered': r'^\d+\)\s+',
    'konsiderans': r'^(Menimbang|Mengingat|MEMUTUSKAN|Menetapkan)\s*:?',
    'considerations': r'^[a-z]\.\s+bahwa'
}

EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 25))
EMBEDDING_MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", 3))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", 0.2))

PINECONE_BATCH_SIZE = int(os.getenv("PINECONE_BATCH_SIZE", 100))
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "documents")

# ======================================================
# RAG CONFIGURATION (SOP ENGINE)
# ======================================================
RAG_TOP_K = int(os.getenv("RAG_TOP_K", 8))
RAG_RETRIEVAL_K = int(os.getenv("RAG_RETRIEVAL_K", 15))
RAG_GLOBAL_TOP_K = int(os.getenv("RAG_GLOBAL_TOP_K", 3))
RAG_STRICT_MODE = True

RAG_CACHE_TTL = int(os.getenv("RAG_CACHE_TTL", 300))
RAG_CACHE_MAX_SIZE = int(os.getenv("RAG_CACHE_MAX_SIZE", 100))

RAG_MAX_CONTEXT_LENGTH = int(os.getenv("RAG_MAX_CONTEXT_LENGTH", 6500))
RAG_MAX_CHUNK_LENGTH = int(os.getenv("RAG_MAX_CHUNK_LENGTH", 1800))

RAG_ENABLE_RERANKING = os.getenv("RAG_ENABLE_RERANKING", "true").lower() == "true"
RAG_RERANK_MULTIPLIER = float(os.getenv("RAG_RERANK_MULTIPLIER", 3.0))

RAG_ENABLE_LLM_FALLBACK = os.getenv("RAG_ENABLE_LLM_FALLBACK", "true").lower() == "true"
RAG_FALLBACK_MAX_CHARS = int(os.getenv("RAG_FALLBACK_MAX_CHARS", 500))

# ======================================================
# MEMORY & SPEECH CONFIGURATION
# ======================================================
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", 8))
SESSION_CLEANUP_DAYS = int(os.getenv("SESSION_CLEANUP_DAYS", 30))

SPEECH_LANGUAGE_DEFAULT = os.getenv("SPEECH_LANGUAGE_DEFAULT", "id")
TTS_PRIMARY_ENGINE = os.getenv("TTS_PRIMARY_ENGINE", "elevenlabs")
TTS_FALLBACK_ENGINE = os.getenv("TTS_FALLBACK_ENGINE", "openai")

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
# TIMEOUT & MODE SPECIFICS
# ======================================================
API_TIMEOUT_DEFAULT = int(os.getenv("API_TIMEOUT_DEFAULT", 60))
API_TIMEOUT_CALL_MODE = int(os.getenv("API_TIMEOUT_CALL_MODE", 15))
API_TIMEOUT_TTS = int(os.getenv("API_TIMEOUT_TTS", 8))

CALL_MODE_TEMPERATURE = 0.0
CHAT_MODE_TEMPERATURE = 0.1
CALL_MODE_MAX_TOKENS = 150
CHAT_MODE_MAX_TOKENS = 2000

# ======================================================
# FEATURE FLAGS & ENV
# ======================================================
FEATURE_NATURAL_TTS = os.getenv("FEATURE_NATURAL_TTS", "true").lower() == "true"
FEATURE_VERBOSE_LOGGING = os.getenv("FEATURE_VERBOSE_LOGGING", "false").lower() == "true"

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if ENVIRONMENT == "production" else "DEBUG")

# Semantic Router Configuration
SEMANTIC_ROUTER_ENABLED = os.getenv("SEMANTIC_ROUTER_ENABLED", "true").lower() == "true"
SEMANTIC_ROUTER_THRESHOLD = float(os.getenv("SEMANTIC_ROUTER_THRESHOLD", "0.75"))
SEMANTIC_ROUTER_ENCODER = os.getenv("SEMANTIC_ROUTER_ENCODER", "text-embedding-3-small")  # ✅ BENAR

# LLM Configuration for Intent Classification
INTENT_CLASSIFIER_MODEL = os.getenv("INTENT_CLASSIFIER_MODEL", "gpt-4o-mini")  # Cheap & fast model for fallback
INTENT_CLASSIFIER_TEMPERATURE = float(os.getenv("INTENT_CLASSIFIER_TEMPERATURE", "0"))  # Deterministic
INTENT_CLASSIFIER_MAX_TOKENS = int(os.getenv("INTENT_CLASSIFIER_MAX_TOKENS", "1"))  # Just need A or B

# ======================================================
# SAFE VALIDATION & INIT (NON-BREAKING)
# ======================================================
if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY not configured - LLM and embedding features disabled")
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️ Supabase not configured - database features disabled")
if not PINECONE_API_KEY or not PINECONE_INDEX:
    print("⚠️ Pinecone not configured - SOP RAG will be unavailable")
if not COHERE_API_KEY:
    print(f"⚠️ Cohere API not configured - reranking will be disabled (falling back to Pinecone scores)\n   Using model: {COHERE_MODEL}")
if not GOOGLE_MAPS_API_KEY:
    print("⚠️ Google Maps API not configured - distance calculation will use LLM fallback")
if not ELEVENLABS_API_KEY:
    print("⚠️ ElevenLabs not configured - using OpenAI TTS fallback")
# Tambahkan ini:
if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
    print("⚠️ Upstash Redis not configured - chat history caching will use Supabase fallback")
if not SUPABASE_DB_PASSWORD and not SUPABASE_CONNECTION_STRING:
    print("⚠️ Supabase database not configured - HR CSV ingestion will be unavailable\n   Set SUPABASE_DB_PASSWORD or SUPABASE_CONNECTION_STRING")

# Document ingestion directory setup
try:
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    if FEATURE_VERBOSE_LOGGING:
        print(f"✅ Document directories ready: {DOCUMENTS_DIR}, {CHUNKS_DIR}, {EMBEDDINGS_DIR}")
except Exception as e:
    print(f"⚠️ Could not create document directories: {e}")

# Validasi Sukses
print("✅ Enhanced config loaded successfully (v4.2 - with Cohere Reranker support)")
print(f"   RAG Settings: Top-K={RAG_TOP_K}, Retrieval={RAG_RETRIEVAL_K}, Reranking={'Enabled' if RAG_ENABLE_RERANKING else 'Disabled'}")
print(f"   Cohere Model: {COHERE_MODEL}")