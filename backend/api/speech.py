"""
DENAI Speech API Routes
Text-to-speech and speech-to-text endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from models.requests import TTSRequest, STTResponse
from services.tts_service import TTSService
from services.stt_service import STTService
from utils.text_utils import clean_text_for_tts

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
tts_service = TTSService()
stt_service = STTService()


@router.post("/text-to-speech")
async def text_to_speech_natural(tts_request: TTSRequest):
    """
    Convert text to natural speech with better ElevenLabs support
    
    Args:
        tts_request: Text-to-speech request with text and options
        
    Returns:
        StreamingResponse: Audio stream (MP3)
    """
    try:
        text = tts_request.text
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text required")
        
        # Clean text for natural speech
        clean_text = clean_text_for_tts(text)
        
        if not clean_text or len(clean_text.strip()) < 5:
            raise HTTPException(status_code=400, detail="No valid text after cleaning")
        
        logger.info(f"🔊 TTS request: {clean_text[:50]}...")
        
        # Force ElevenLabs for TTS API endpoint
        audio_content, engine = await tts_service.generate_audio(
            clean_text, 
            force_elevenlabs=True
        )
        
        def generate():
            yield audio_content
        
        return StreamingResponse(
            generate(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=denai_natural.mp3",
                "Cache-Control": "no-cache",
                "X-Voice": "Indonesian-Natural",
                "X-Engine": engine,
                "X-Natural-Speech": "true"
            }
        )
        
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speech-to-text")
async def speech_to_text_optimized(audio_file: UploadFile = File(...)):
    """
    Convert speech to text using OpenAI Whisper
    
    Args:
        audio_file: Uploaded audio file
        
    Returns:
        STTResponse: Transcription result with metadata
    """
    try:
        logger.info(f"🎤 STT request: {audio_file.filename}")
        
        # Validate file
        file_size = 0
        audio_content = await audio_file.read()
        file_size = len(audio_content)
        
        is_valid, error_msg = stt_service.validate_audio_file(
            audio_file.filename or "audio.wav", 
            file_size
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Transcribe audio
        transcript = await stt_service.transcribe_file_upload(
            audio_content, 
            audio_file.filename
        )
        
        logger.info(f"✅ STT result: {transcript[:50]}...")
        
        return STTResponse(
            transcript=transcript,
            language=stt_service.default_language,
            confidence="high",
            status="success",
            engine="whisper"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def speech_system_status():
    """
    Get speech system status and configuration
    
    Returns:
        dict: Complete speech system status
    """
    try:
        return {
            "speech_recognition": {
                "available": True,
                **stt_service.get_service_info()
            },
            "text_to_speech": {
                "available": True,
                **tts_service.get_engine_info()
            },
            "status": "active",
            "version": "7.0.0"
        }
        
    except Exception as e:
        logger.error(f"Speech status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engines")
async def list_speech_engines():
    """
    List available speech engines and their capabilities
    
    Returns:
        dict: Available engines information
    """
    return {
        "tts_engines": {
            "elevenlabs": {
                "configured": tts_service.elevenlabs_configured,
                "voice_quality": "high",
                "languages": ["id", "en"],
                "natural_speech": True
            },
            "openai": {
                "configured": True,
                "voice_quality": "good",
                "languages": ["id", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "natural_speech": True
            }
        },
        "stt_engines": {
            "whisper": {
                "configured": True,
                "accuracy": "high",
                "languages": stt_service.get_service_info()["supported_languages"]
            }
        },
        "recommended": {
            "tts": "elevenlabs" if tts_service.elevenlabs_configured else "openai",
            "stt": "whisper"
        }
    }


@router.get("/test")
async def test_speech_system():
    """
    Test speech system functionality
    
    Returns:
        dict: Test results
    """
    try:
        test_text = "Halo, ini adalah tes sistem speech DEN AI."
        
        # Test TTS
        try:
            audio_content, engine = await tts_service.generate_audio(test_text)
            tts_test = {
                "status": "success",
                "engine": engine,
                "audio_size": len(audio_content)
            }
        except Exception as e:
            tts_test = {
                "status": "failed",
                "error": str(e)
            }
        
        # STT would require actual audio file, so just check service
        stt_test = {
            "status": "ready",
            "service_info": stt_service.get_service_info()
        }
        
        return {
            "tts_test": tts_test,
            "stt_test": stt_test,
            "overall_status": "healthy" if tts_test["status"] == "success" else "partial"
        }
        
    except Exception as e:
        logger.error(f"Speech test error: {e}")
        return {
            "tts_test": {"status": "error", "error": str(e)},
            "stt_test": {"status": "error", "error": str(e)},
            "overall_status": "error"
        }