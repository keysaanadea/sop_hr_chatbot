"""
DENAI STT Service
Speech-to-text functionality using OpenAI Whisper
"""

import logging
import asyncio
import io
from openai import OpenAI

# Langsung import dari app.config (tanpa sys.path hack)
from app.config import OPENAI_API_KEY, SPEECH_LANGUAGE_DEFAULT

logger = logging.getLogger(__name__)

class STTService:
    """Speech-to-text service using OpenAI Whisper"""
    
    def __init__(self):
        # Inisialisasi client HANYA di dalam instance
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.default_language = SPEECH_LANGUAGE_DEFAULT
        self.model = "whisper-1"
    
    async def transcribe_audio(self, audio_file_obj: io.BytesIO, language: str = None) -> str:
        """Transcribe audio to text using OpenAI Whisper"""
        try:
            actual_language = language or self.default_language
            logger.info(f"🎤 Transcribing audio (language: {actual_language})")
            
            transcript_response = await asyncio.to_thread(
                self.client.audio.transcriptions.create,
                model=self.model,
                file=audio_file_obj,
                language=actual_language,
                response_format="text"
            )
            
            # Handle different response formats
            transcript = transcript_response if isinstance(transcript_response, str) else transcript_response.text
            result = transcript.strip()
            logger.info(f"✅ STT result: {result[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ STT error: {e}")
            raise
    
    async def transcribe_file_upload(self, file_content: bytes, filename: str = None) -> str:
        """Transcribe uploaded file content"""
        try:
            audio_file_obj = io.BytesIO(file_content)
            audio_file_obj.name = filename or "audio.wav"
            return await self.transcribe_audio(audio_file_obj)
        except Exception as e:
            logger.error(f"❌ File transcription error: {e}")
            raise
    
    def get_service_info(self) -> dict:
        return {
            "model": self.model,
            "default_language": self.default_language,
            "supported_languages": ["id", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
            "supported_formats": ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"],
            "max_file_size": "25MB",
            "engine": "OpenAI Whisper"
        }
    
    def validate_audio_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """Validate audio file format and size"""
        max_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB (max 25MB)"
        
        if not filename:
            return False, "No filename provided"
        
        supported_extensions = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'}
        file_ext = next((ext for ext in supported_extensions if filename.lower().endswith(ext)), None)
        
        if not file_ext:
            return False, f"Unsupported format. Supported: {', '.join(supported_extensions)}"
        
        return True, ""