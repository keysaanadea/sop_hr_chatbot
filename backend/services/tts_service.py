"""
DENAI TTS Service
Text-to-speech functionality with ElevenLabs and OpenAI support
"""

import logging
import asyncio
import requests
import io
from openai import OpenAI

# Langsung import dari app.config
from app.config import (
    OPENAI_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID_INDONESIAN,
    TTS_PRIMARY_ENGINE, TTS_FALLBACK_ENGINE, ELEVENLABS_SETTINGS,
    OPENAI_TTS_SETTINGS, API_TIMEOUT_TTS, FEATURE_NATURAL_TTS
)

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-speech service with multiple engine support"""
    
    def __init__(self):
        # Inisialisasi client HANYA di dalam instance
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.elevenlabs_configured = bool(ELEVENLABS_API_KEY)
        self.primary_engine = TTS_PRIMARY_ENGINE
        self.fallback_engine = TTS_FALLBACK_ENGINE
    
    async def generate_audio(self, text: str, force_elevenlabs: bool = False) -> tuple[bytes, str]:
        """Generate TTS audio with improved engine handling"""
        if not text or not text.strip():
            raise ValueError("No text to convert")
        
        logger.info(f"🔊 Generating TTS (force_elevenlabs={force_elevenlabs}): {text[:50]}...")
        
        # Try ElevenLabs first if it's primary or forced
        if (self.primary_engine == "elevenlabs" or force_elevenlabs) and self.elevenlabs_configured:
            try:
                return await self._generate_elevenlabs(text)
            except Exception as e:
                logger.warning(f"⚠️ ElevenLabs failed: {e}")
                if force_elevenlabs:
                    logger.info("🔄 Forced ElevenLabs failed, falling back to OpenAI")
        
        # Fallback to OpenAI
        logger.info("🔄 Using OpenAI TTS fallback")
        return await self._generate_openai(text)
    
    async def _generate_elevenlabs(self, text: str) -> tuple[bytes, str]:
        """Generate TTS using ElevenLabs API"""
        if not ELEVENLABS_API_KEY:
            raise ValueError("ElevenLabs API key not configured")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID_INDONESIAN}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        
        payload = {
            "text": text,
            "model_id": ELEVENLABS_SETTINGS["model"],
            "voice_settings": {
                "stability": ELEVENLABS_SETTINGS["stability"],
                "similarity_boost": ELEVENLABS_SETTINGS["similarity_boost"],
                "style": ELEVENLABS_SETTINGS["style"],
                "use_speaker_boost": ELEVENLABS_SETTINGS["use_speaker_boost"]
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT_TTS)
            if response.status_code == 200:
                logger.info(f"✅ ElevenLabs success ({len(response.content)} bytes)")
                return response.content, "elevenlabs"
            else:
                logger.error(f"❌ ElevenLabs API error: {response.status_code} - {response.text}")
                raise ValueError(f"ElevenLabs API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise ValueError("ElevenLabs timeout")
        except requests.exceptions.ConnectionError:
            raise ValueError("ElevenLabs connection failed")
        except Exception as e:
            raise ValueError(f"ElevenLabs error: {e}")
    
    async def _generate_openai(self, text: str) -> tuple[bytes, str]:
        """Generate TTS using OpenAI API"""
        try:
            response = await asyncio.to_thread(
                self.client.audio.speech.create,
                model="tts-1",
                voice=OPENAI_TTS_SETTINGS["voice"],
                input=text,
                response_format="mp3",
                speed=OPENAI_TTS_SETTINGS["speed"]
            )
            logger.info("✅ OpenAI TTS success")
            return response.content, "openai"
        except Exception as e:
            logger.error(f"❌ OpenAI TTS error: {e}")
            raise
    
    def create_audio_stream(self, audio_content: bytes) -> io.BytesIO:
        """Create an audio stream from bytes"""
        return io.BytesIO(audio_content)
    
    def get_engine_info(self) -> dict:
        return {
            "primary_engine": self.primary_engine,
            "fallback_engine": self.fallback_engine,
            "elevenlabs_configured": self.elevenlabs_configured,
            "elevenlabs_voice_id": ELEVENLABS_VOICE_ID_INDONESIAN,
            "elevenlabs_model": ELEVENLABS_SETTINGS["model"],
            "openai_voice": OPENAI_TTS_SETTINGS["voice"],
            "natural_speech": FEATURE_NATURAL_TTS
        }