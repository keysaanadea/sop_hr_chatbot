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
    from app.config import FEATURE_LANGFUSE, LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL

    if not FEATURE_LANGFUSE:
        logger.warning("⚠️ Langfuse disabled by FEATURE_LANGFUSE=false")
    elif LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY:
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
    Langfuse v4: CallbackHandler tanpa trace_context akan otomatis menggunakan
    OTel context yang aktif saat ini (ditetapkan oleh langfuse_observation()).
    Kembalikan None jika Langfuse tidak aktif.
    """
    if not LANGFUSE_ENABLED:
        return None
    try:
        from langfuse.langchain import CallbackHandler
        return CallbackHandler()
    except Exception as e:
        logger.warning(f"⚠️ Tidak bisa membuat LangChain CallbackHandler: {e}")
        return None


try:
    from contextlib import contextmanager as _contextmanager

    @_contextmanager
    def langfuse_observation(name: str, **kwargs):
        """
        Langfuse v4 span helper — context manager yang membuat observation baru
        sebagai OTel context aktif. Semua panggilan LLM di dalam blok ini
        (langfuse.openai, LangChain CallbackHandler) otomatis menjadi child span.
        No-op jika Langfuse tidak diaktifkan.

        Contoh pemakaian:
            with langfuse_observation("intent_classification", input={...}) as span:
                result = await classify_intent(...)
                if span:
                    span.update(output={"result": result})
        """
        if not LANGFUSE_ENABLED:
            yield None
            return

        # Init Langfuse client di luar yield — kalau gagal, fallback ke no-op
        # tanpa menelan exception yang berasal dari kode user di dalam blok with.
        try:
            from langfuse import get_client
            lf_client = get_client()
        except Exception as _e:
            logger.debug(f"langfuse_observation '{name}' skipped (init): {_e}")
            yield None
            return

        # Biarkan exception dari dalam blok 'with' (misal LLM timeout) propagate normal.
        # Jangan yield lagi setelah exception — itu menyebabkan "generator didn't stop after throw()".
        with lf_client.start_as_current_observation(name=name, **kwargs) as span:
            yield span

except Exception:
    # Fallback no-op jika contextlib tidak tersedia (harusnya tidak terjadi)
    def langfuse_observation(name: str, **kwargs):  # type: ignore[misc]
        from contextlib import nullcontext
        return nullcontext(None)
