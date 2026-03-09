"""
DENAI Speech API Routes
Text-to-speech and speech-to-text endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import io

from backend.models.requests import TTSRequest, STTResponse
from backend.services.tts_service import TTSService
from backend.services.stt_service import STTService
from backend.utils.text_utils import clean_text_for_tts
from backend.utils.speech_utils import rewrite_for_speech

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
tts_service = TTSService()
stt_service = STTService()


@router.post("/text-to-speech")
async def text_to_speech_natural(tts_request: TTSRequest):
    """
    Convert text to natural speech with answer-first optimization
    
    🎯 STRATEGY:
    - Short text (<200 chars): Read as-is
    - Long text (>=200 chars): Reorder to answer question FIRST, then supporting details
    - Uses original question as context for smart reordering
    - User still sees full text in chat, but voice is optimized for listening
    """
    try:
        text = tts_request.text
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text required")
        
        # Clean text for natural speech
        clean_text = clean_text_for_tts(text)
        if not clean_text or len(clean_text.strip()) < 5:
            raise HTTPException(status_code=400, detail="No valid text after cleaning")
        
        was_optimized = False
        original_length = len(clean_text)
        
        # 🎯 ANSWER-FIRST OPTIMIZATION: Threshold 200 chars
        OPTIMIZATION_THRESHOLD = 200
        
        if len(clean_text) > OPTIMIZATION_THRESHOLD:
            # Get question from request if available
            question = getattr(tts_request, 'question', '') or ''
            
            logger.info(f"🔊 TTS request (OPTIMIZING - ANSWER FIRST)... | Orig: {original_length} chars")
            if question:
                logger.info(f"   📝 Question context: {question[:100]}...")
            
            try:
                # ✅ REORDER dengan context pertanyaan
                voice_text = await rewrite_for_speech(clean_text, question)
                logger.info(f"   ✅ Optimized for voice: {len(voice_text)} chars")
                clean_text = voice_text
                was_optimized = True
            except Exception as rewrite_error:
                logger.warning(f"   ⚠️ Optimization failed, using original: {rewrite_error}")
                was_optimized = False
        else:
            logger.info(f"🔊 TTS request (SHORT - NO OPTIMIZATION): {clean_text[:50]}...")
        
        # Force ElevenLabs for TTS API endpoint
        audio_content, engine = await tts_service.generate_audio(clean_text, force_elevenlabs=True)
        
        return StreamingResponse(
            iter([audio_content]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=denai_voice.mp3",
                "Cache-Control": "no-cache",
                "X-Voice": "Indonesian-Natural",
                "X-Engine": engine,
                "X-Answer-First": "true" if was_optimized else "false",
                "X-Original-Length": str(original_length),
                "X-Voice-Length": str(len(clean_text))
            }
        )
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speech-to-text", response_model=STTResponse)
async def speech_to_text_optimized(audio_file: UploadFile = File(...)):
    """Convert speech to text using OpenAI Whisper"""
    try:
        logger.info(f"🎤 STT request: {audio_file.filename}")
        
        audio_content = await audio_file.read()
        file_size = len(audio_content)
        
        is_valid, error_msg = stt_service.validate_audio_file(audio_file.filename or "audio.wav", file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        transcript = await stt_service.transcribe_file_upload(audio_content, audio_file.filename)
        logger.info(f"✅ STT result: {transcript[:50]}...")
        
        return STTResponse(
            transcript=transcript,
            language=stt_service.default_language,
            confidence="high",
            status="success",
            engine="whisper"
        )
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"❌ STT Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def speech_system_status():
    """Get speech system status and configuration"""
    try:
        return {
            "speech_recognition": {"available": True, **stt_service.get_service_info()},
            "text_to_speech": {
                "available": True, 
                **tts_service.get_engine_info(),
                "answer_first_optimization": True,
                "optimization_threshold": 200,
                "strategy": "Answer question first, then supporting details"
            },
            "status": "active",
            "version": "9.1.0"
        }
    except Exception as e:
        logger.error(f"❌ Speech status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engines")
async def list_speech_engines():
    """List available speech engines and their capabilities"""
    return {
        "tts_engines": {
            "elevenlabs": {
                "configured": tts_service.elevenlabs_configured,
                "voice_quality": "high", "languages": ["id", "en"],
                "natural_speech": True, "smart_summarization": True
            },
            "openai": {
                "configured": True,
                "voice_quality": "good", "languages": ["id", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "natural_speech": True, "smart_summarization": True
            }
        },
        "stt_engines": {
            "whisper": {"configured": True, "accuracy": "high", "languages": stt_service.get_service_info()["supported_languages"]}
        },
        "recommended": {"tts": "elevenlabs" if tts_service.elevenlabs_configured else "openai", "stt": "whisper"},
        "features": {
            "answer_first_optimization": {
                "enabled": True, 
                "threshold": 200,
                "approach": "Answer-first",
                "description": "Voice answers the question directly first, then provides supporting details. Full text remains in chat."
            }
        }
    }


@router.get("/test")
async def test_speech_system():
    """Test speech system functionality including auto-summarization"""
    try:
        test_text = "Halo, ini adalah tes sistem speech DEN AI."
        test_long_text = ("Ini adalah teks yang sangat panjang untuk menguji fitur "
                         "auto-summarization pada sistem text-to-speech. Fitur ini akan "
                         "secara otomatis merangkum teks panjang menjadi versi yang lebih ringkas.")
        
        # Test TTS
        try:
            audio_content, engine = await tts_service.generate_audio(test_text)
            tts_test = {"status": "success", "engine": engine, "audio_size": len(audio_content)}
        except Exception as e:
            tts_test = {"status": "failed", "error": str(e)}
        
        # Test Summarization
        try:
            # ⚡ FIX: Tambahkan await dan hapus limit parameter
            summarized = await rewrite_for_speech(test_long_text)
            summarization_test = {
                "status": "success", "original_length": len(test_long_text),
                "summarized_length": len(summarized),
                "reduction_percent": round((1 - len(summarized)/len(test_long_text)) * 100, 1)
            }
        except Exception as e:
            summarization_test = {"status": "failed", "error": str(e)}
        
        stt_test = {"status": "ready", "service_info": stt_service.get_service_info()}
        
        is_healthy = tts_test["status"] == "success" and summarization_test["status"] == "success"
        
        return {
            "tts_test": tts_test,
            "stt_test": stt_test,
            "summarization_test": summarization_test,
            "overall_status": "healthy" if is_healthy else "partial"
        }
        
    except Exception as e:
        logger.error(f"❌ Speech test error: {e}")
        return {
            "tts_test": {"status": "error", "error": str(e)}, "stt_test": {"status": "error", "error": str(e)},
            "summarization_test": {"status": "error", "error": str(e)}, "overall_status": "error"
        }