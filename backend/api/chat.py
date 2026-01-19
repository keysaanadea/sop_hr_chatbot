"""
DENAI Chat API Routes
Pure FastAPI endpoints - minimal logic, delegates to chat_service
"""

import logging
import uuid
import io
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional

logger = logging.getLogger(__name__)

from backend.models.requests import QuestionRequest, QuestionResponse
from backend.services.chat_service import ChatService
from backend.services.tts_service import TTSService
from backend.services.stt_service import STTService
from backend.utils.text_utils import clean_text_for_tts

# Import session management
try:
    from memory.memory_supabase import (
        get_recent_history, save_message, save_session
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("⚠️ Memory system not available")

router = APIRouter()

# Initialize services
chat_service = ChatService()
tts_service = TTSService()
stt_service = STTService()


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: Request, req: QuestionRequest):
    """
    Text-based question answering endpoint
    PURE ORCHESTRATION - delegates to chat_service
    """
    try:
        # Setup session
        if not req.session_id:
            req.session_id = str(uuid.uuid4())
        
        user_role = req.user_role or "Employee"
        logger.info(f"🔍 Question: {req.question[:50]}...")
        
        # Handle session management
        if MEMORY_AVAILABLE:
            existing = get_recent_history(req.session_id, limit=1)
            if not existing:
                title = req.question[:50] + "..."
                save_session(req.session_id, title)
            
            save_message(req.session_id, "user", req.question)
            history = get_recent_history(req.session_id, limit=4)
        else:
            history = []
        
        # DELEGATE to chat service - all logic there
        result = await chat_service.process_question(
            question=req.question,
            user_role=user_role,
            session_id=req.session_id,
            history=history,
            mode="chat"
        )
        
        # Save assistant response
        if MEMORY_AVAILABLE and result.get("answer"):
            save_message(req.session_id, "assistant", result["answer"])
        
        # Build API response
        return QuestionResponse(
            answer=result.get("answer", "Server error."),
            session_id=req.session_id,
            tool_called=result.get("tool_called"),
            authorized=result.get("authorized", True),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Ask endpoint error: {e}")
        return QuestionResponse(
            answer="Server error. Silakan coba lagi.",
            session_id=req.session_id or str(uuid.uuid4()),
            error=str(e),
            authorized=True
        )


@router.post("/call/process")
async def call_mode_natural(
    request: Request,
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = None,
    user_role: Optional[str] = None
):
    """
    Voice call mode endpoint
    PURE ORCHESTRATION - handles I/O, delegates processing to services
    """
    try:
        logger.info("📞 Call mode processing...")
        
        # Process audio input via STT service
        audio_content = await audio_file.read()
        transcript = await stt_service.transcribe_file_upload(
            audio_content, 
            "call.wav"
        )
        
        logger.info(f"📞 User: {transcript}")
        
        if not transcript:
            error_response = "Maaf, saya tidak mendengar dengan jelas. Bisa diulangi?"
            return await _generate_call_audio_response(error_response, session_id)
        
        # Setup session
        if not session_id:
            session_id = str(uuid.uuid4())
            if MEMORY_AVAILABLE:
                save_session(session_id, "📞 Call")
        
        # Handle session management
        if MEMORY_AVAILABLE:
            save_message(session_id, "user", transcript)
            history = get_recent_history(session_id, limit=1)
        else:
            history = []
        
        # DELEGATE to chat service - all logic there
        result = await chat_service.process_question(
            question=transcript,
            user_role=user_role or "Employee",
            session_id=session_id,
            history=history,
            mode="call"
        )
        
        answer = result.get("answer", "Maaf, tidak bisa memproses permintaan.")
        
        # Save assistant response
        if MEMORY_AVAILABLE:
            save_message(session_id, "assistant", answer)
        
        # Generate audio response via TTS service
        return await _generate_call_audio_response(answer, session_id)
        
    except Exception as e:
        logger.error(f"📞 Call endpoint error: {e}")
        error_msg = "Maaf, terjadi gangguan."
        return await _generate_call_audio_response(error_msg, None)


async def _generate_call_audio_response(
    text: str, 
    session_id: Optional[str] = None
) -> StreamingResponse:
    """
    Generate audio response for call mode
    PURE I/O PROCESSING - delegates to TTS service
    """
    try:
        # Clean text and generate TTS with ElevenLabs priority
        clean_text = clean_text_for_tts(text)
        audio_content, engine = await tts_service.generate_audio(
            clean_text, 
            force_elevenlabs=True
        )
        
        logger.info(f"📞 DENAI: {text[:50]}... (engine: {engine})")
        
        def generate():
            yield audio_content
        
        headers = {
            "Cache-Control": "no-cache",
            "X-Voice": "Indonesian-Natural",
            "X-Engine": engine,
            "X-Natural-TTS": "true"
        }
        
        if session_id:
            headers["X-Session-ID"] = session_id
        
        return StreamingResponse(
            generate(),
            media_type="audio/mpeg",
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Call audio generation error: {e}")
        # Return silent audio on error
        silence = b'\x00' * 1024
        return StreamingResponse(
            io.BytesIO(silence),
            media_type="audio/mpeg"
        )


@router.get("/tools")
async def list_available_tools():
    """
    List available chat tools and capabilities
    DELEGATES to chat service
    """
    return chat_service.get_tools_info()


@router.get("/status")
async def chat_system_status():
    """
    Get chat system status and configuration
    DELEGATES to chat service
    """
    return {
        "service": "chat",
        "status": "active",
        "memory_available": MEMORY_AVAILABLE,
        **chat_service.get_service_info()
    }