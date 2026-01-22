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
from utils.speech_utils import rewrite_for_speech  # ✅ ADDED FOR AUTO-SUMMARIZATION

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
tts_service = TTSService()
stt_service = STTService()


@router.post("/text-to-speech")
async def text_to_speech_natural(tts_request: TTSRequest):
    """
    Convert text to natural speech with auto-summarization for long texts
    
    This endpoint automatically summarizes long responses to make them
    more suitable for voice output, improving user experience.
    
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
        
        # ✅ AUTO-SUMMARIZE: If text is long, rewrite for speech
        # This happens when user clicks voice button on a long text response
        was_summarized = False
        original_length = len(clean_text)
        
        if len(clean_text) > 150:  # Threshold: 150 characters
            logger.info(f"🔊 TTS request (LONG TEXT - will summarize): {clean_text[:50]}...")
            logger.info(f"   Original length: {original_length} chars")
            
            # Rewrite for speech to make it concise
            try:
                voice_text = rewrite_for_speech(clean_text, max_sentences=2)
                logger.info(f"   ✅ Summarized to: {len(voice_text)} chars")
                logger.info(f"   Voice text: {voice_text[:100]}...")
                clean_text = voice_text
                was_summarized = True
            except Exception as rewrite_error:
                logger.warning(f"   ⚠️ Rewrite failed, using truncation: {rewrite_error}")
                # Fallback: simple truncation with ellipsis
                clean_text = clean_text[:200].rsplit(' ', 1)[0] + "..."
                was_summarized = True
        else:
            logger.info(f"🔊 TTS request (short): {clean_text[:50]}...")
        
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
                "X-Natural-Speech": "true",
                "X-Summarized": "true" if was_summarized else "false",  # ✅ Indicator
                "X-Original-Length": str(original_length),
                "X-Final-Length": str(len(clean_text))
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
                **tts_service.get_engine_info(),
                "auto_summarization": True,  # ✅ New feature indicator
                "summarization_threshold": 150
            },
            "status": "active",
            "version": "7.1.0"  # ✅ Bumped version
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
                "natural_speech": True,
                "auto_summarization": True  # ✅ Feature indicator
            },
            "openai": {
                "configured": True,
                "voice_quality": "good",
                "languages": ["id", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "natural_speech": True,
                "auto_summarization": True  # ✅ Feature indicator
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
        },
        "features": {
            "auto_summarization": {
                "enabled": True,
                "threshold": 150,
                "max_sentences": 2,
                "description": "Automatically summarizes long texts for better voice output"
            }
        }
    }


@router.get("/test")
async def test_speech_system():
    """
    Test speech system functionality including auto-summarization
    
    Returns:
        dict: Test results
    """
    try:
        test_text = "Halo, ini adalah tes sistem speech DEN AI."
        test_long_text = ("Ini adalah teks yang sangat panjang untuk menguji fitur "
                         "auto-summarization pada sistem text-to-speech. Fitur ini akan "
                         "secara otomatis merangkum teks panjang menjadi versi yang lebih "
                         "ringkas dan mudah didengar.")
        
        # Test TTS with short text
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
        
        # Test auto-summarization
        try:
            summarized = rewrite_for_speech(test_long_text, max_sentences=2)
            summarization_test = {
                "status": "success",
                "original_length": len(test_long_text),
                "summarized_length": len(summarized),
                "reduction_percent": round((1 - len(summarized)/len(test_long_text)) * 100, 1)
            }
        except Exception as e:
            summarization_test = {
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
            "summarization_test": summarization_test,
            "overall_status": "healthy" if (tts_test["status"] == "success" and 
                                           summarization_test["status"] == "success") else "partial"
        }
        
    except Exception as e:
        logger.error(f"Speech test error: {e}")
        return {
            "tts_test": {"status": "error", "error": str(e)},
            "stt_test": {"status": "error", "error": str(e)},
            "summarization_test": {"status": "error", "error": str(e)},
            "overall_status": "error"
        }