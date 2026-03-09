"""
DENAI Chat API Routes - ULTIMATE CANCELLATION (DELAYED INSERTION)
Integration with existing chat_service.py and memory system
"""

import logging
import uuid
import io
import json
import urllib.parse
import asyncio
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from pydantic import BaseModel

from backend.models.requests import QuestionRequest, QuestionResponse
from backend.services.chat_service import ChatService
from backend.services.tts_service import TTSService
from backend.services.stt_service import STTService
from backend.utils.text_utils import clean_text_for_tts

from memory.memory_hybrid import (
    get_hybrid_history, 
    save_hybrid_message, 
    setup_hybrid_session,
    MEMORY_AVAILABLE,
    REDIS_AVAILABLE
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
chat_service = ChatService()
tts_service = TTSService()
stt_service = STTService()

# Track active requests for cancellation
active_requests = {}

class StoppedRequest(BaseModel):
    last_query: str


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: Request, req: QuestionRequest):
    """
    Enhanced endpoint with proper cancellation handling.
    """
    try:
        req.session_id = req.session_id or str(uuid.uuid4())
        user_role = req.user_role or "Employee"
        logger.info(f"🔍 Question: {req.question[:50]}...")
        
        # Cancel previous request for this session
        if req.session_id in active_requests:
            old_task = active_requests[req.session_id]
            if not old_task.done():
                logger.warning(f"🛑 Cancelling previous request for session {req.session_id}")
                old_task.cancel()
                try:
                    await old_task
                except asyncio.CancelledError:
                    logger.info(f"✅ Previous request cancelled successfully")
        
        # Create new task with cancellation support
        task = asyncio.create_task(
            process_question_with_cancellation(
                question=req.question,
                session_id=req.session_id,
                user_role=user_role,
                request=request
            )
        )
        
        active_requests[req.session_id] = task
        
        try:
            result = await task
            return QuestionResponse(**result)
            
        except asyncio.CancelledError:
            logger.warning(f"🛑 Request cancelled by client: {req.session_id}")
            return QuestionResponse(
                answer="Request was cancelled",
                session_id=req.session_id,
                cancelled=True,
                authorized=True
            )
        
    except Exception as e:
        logger.error(f"❌ Ask endpoint error: {e}", exc_info=True)
        return QuestionResponse(
            answer="Server error. Silakan coba lagi.",
            session_id=req.session_id or str(uuid.uuid4()),
            error=str(e),
            authorized=True
        )
    
    finally:
        if req.session_id and req.session_id in active_requests:
            del active_requests[req.session_id]


async def process_question_with_cancellation(
    question: str,
    session_id: str,
    user_role: str,
    request: Request
) -> dict:
    """
    Core processing logic with DELAYED DB INSERTION.
    Pertanyaan user tidak akan dimasukkan ke DB sampai AI benar-benar selesai menjawab!
    """
    
    # Checkpoint 1: Before starting
    if await request.is_disconnected():
        logger.info("🛑 Client disconnected before processing started")
        raise asyncio.CancelledError()
    
    # Get history (✅ FIX: Use await)
    history = await get_hybrid_history(session_id, limit=4)
    
    # Setup session (✅ FIX: Use await)
    await setup_hybrid_session(session_id, question)
    
    # Checkpoint 2: Before AI processing
    if await request.is_disconnected():
        logger.info("🛑 Client disconnected before AI processing")
        raise asyncio.CancelledError()
    
    # Pass cancellation callback to chat_service
    result = await chat_service.process_question(
        question=question,
        user_role=user_role,
        session_id=session_id,
        history=history,
        mode="chat",
        cancellation_check=lambda: request.is_disconnected()
    )
    
    # Checkpoint 3: After processing
    if await request.is_disconnected():
        logger.info("🛑 Client disconnected after processing")
        raise asyncio.CancelledError()
    
    # 🔥 JIKA SUKSES & TIDAK DIBATALKAN, BARU KITA SAVE KEDUANYA!
    # Simpan pertanyaan user (✅ FIX: Use await)
    await save_hybrid_message(session_id, "user", question)
    
    # Simpan jawaban AI
    if result.get("answer"):
        text_to_save = result["answer"]
        
        if result.get("data"):
            try:
                json_str = json.dumps(result["data"])
                safe_json = urllib.parse.quote(json_str)
                text_to_save += f'\n\n<span class="denai-hidden-payload" data-payload="{safe_json}" style="display:none;"></span>'
            except Exception as e:
                logger.error(f"❌ JSON parse error: {e}")

        # (✅ FIX: Use await)
        await save_hybrid_message(session_id, "assistant", text_to_save)
    
    if "session_id" not in result:
        result["session_id"] = session_id
    
    return result


@router.post("/call/process")
async def call_mode_natural(
    request: Request,
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = None,
    user_role: Optional[str] = None
):
    try:
        logger.info("📞 Call mode processing...")
        if await request.is_disconnected():
            return await _generate_call_audio_response("Request cancelled", None)
        
        audio_content = await audio_file.read()
        transcript = await stt_service.transcribe_file_upload(audio_content, "call.wav")
        
        if not transcript:
            return await _generate_call_audio_response("Maaf, saya tidak mendengar dengan jelas.", session_id)
        
        session_id = session_id or str(uuid.uuid4())
        
        if await request.is_disconnected():
            raise asyncio.CancelledError()
        
        # (✅ FIX: Use await)
        history = await get_hybrid_history(session_id, limit=1)
        await setup_hybrid_session(session_id, "📞 Call")
        
        result = await chat_service.process_question(
            question=transcript,
            user_role=user_role or "Employee",
            session_id=session_id,
            history=history,
            mode="call"
        )
        
        if await request.is_disconnected():
            raise asyncio.CancelledError()
        
        # Delayed insertion untuk call mode juga (✅ FIX: Use await)
        await save_hybrid_message(session_id, "user", transcript)
        answer = result.get("answer", "Maaf, tidak bisa memproses permintaan.")
        await save_hybrid_message(session_id, "assistant", answer)
        
        return await _generate_call_audio_response(answer, session_id)
        
    except asyncio.CancelledError:
        logger.warning("🛑 Call mode cancelled")
        return await _generate_call_audio_response("Request cancelled", None)
    except Exception as e:
        logger.error(f"❌ Call endpoint error: {e}", exc_info=True)
        return await _generate_call_audio_response("Maaf, terjadi gangguan.", None)


async def _generate_call_audio_response(text: str, session_id: Optional[str] = None) -> StreamingResponse:
    try:
        clean_text = clean_text_for_tts(text)
        audio_content, engine = await tts_service.generate_audio(clean_text, force_elevenlabs=True)
        
        headers = {
            "Cache-Control": "no-cache",
            "X-Voice": "Indonesian-Natural",
            "X-Engine": engine,
            "X-Natural-TTS": "true"
        }
        if session_id:
            headers["X-Session-ID"] = session_id
        
        return StreamingResponse(iter([audio_content]), media_type="audio/mpeg", headers=headers)
        
    except Exception as e:
        logger.error(f"❌ Call audio generation error: {e}")
        return StreamingResponse(io.BytesIO(b'\x00' * 1024), media_type="audio/mpeg")


@router.get("/tools")
async def list_available_tools():
    return chat_service.get_tools_info()


@router.get("/status")
async def chat_system_status():
    return {
        "service": "chat",
        "status": "active",
        "supabase_memory_available": MEMORY_AVAILABLE,
        "redis_memory_available": REDIS_AVAILABLE,
        "cancellation_support": True
    }


@router.get("/debug/active-requests")
async def debug_active_requests():
    return {
        "active_sessions": list(active_requests.keys()),
        "count": len(active_requests)
    }


@router.post("/history/{session_id}/stopped")
async def save_stopped_state(session_id: str, req: StoppedRequest):
    """
    🔥 REVISI: Karena kita pakai sistem "Delayed Insertion", kita TIDAK BOLEH menyimpan
    pesan batal ini ke DB agar riwayat tetap bersih saat di-refresh.
    Kita hanya merespons status sukses untuk menyenangkan Frontend.
    """
    logger.info(f"📝 User membatalkan request. DB dibiarkan bersih (No Trace).")
    return {"status": "success", "message": "Ignored in DB by design"}