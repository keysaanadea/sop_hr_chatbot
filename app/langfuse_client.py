"""
Langfuse Client - Observability & Tracing Helper (v4)
=====================================================
Helper untuk Langfuse v4+ yang digunakan di seluruh aplikasi.
Mendukung @observe decorator dan LangChain CallbackHandler.
"""
import os
import logging

logger = logging.getLogger(__name__)

LANGFUSE_ENABLED = False

try:
    from app.config import LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL

    if LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY:
        # Set env vars — Langfuse v4 membaca ini secara otomatis
        os.environ.setdefault("LANGFUSE_SECRET_KEY", LANGFUSE_SECRET_KEY)
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", LANGFUSE_PUBLIC_KEY)
        os.environ.setdefault("LANGFUSE_HOST", LANGFUSE_BASE_URL)

        # Inisialisasi client singleton (get_client() juga valid di v4)
        from langfuse import Langfuse
        langfuse = Langfuse(
            secret_key=LANGFUSE_SECRET_KEY,
            public_key=LANGFUSE_PUBLIC_KEY,
            host=LANGFUSE_BASE_URL,
        )
        LANGFUSE_ENABLED = True
        logger.info(f"✅ Langfuse v4 tracing enabled → {LANGFUSE_BASE_URL}")
    else:
        logger.warning("⚠️ Langfuse keys not set — tracing disabled")

except ImportError:
    logger.warning("⚠️ langfuse package not installed — run: pip install 'langfuse>=2.0.0'")
except Exception as e:
    logger.error(f"❌ Langfuse init failed: {e}")


def get_langchain_callback():
    """
    Buat LangChain CallbackHandler baru untuk satu trace/request.
    Langfuse v4: from langfuse.langchain import CallbackHandler
    Kembalikan None jika Langfuse tidak aktif.
    """
    if not LANGFUSE_ENABLED:
        return None
    try:
        from langfuse.langchain import CallbackHandler
        # v4: CallbackHandler membaca LANGFUSE_* dari env vars yang sudah di-set di atas
        return CallbackHandler()
    except Exception as e:
        logger.warning(f"⚠️ Tidak bisa membuat LangChain CallbackHandler: {e}")
        return None
