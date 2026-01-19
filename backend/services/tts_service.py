"""
DENAI TTS Service
Text-to-speech functionality with ElevenLabs and OpenAI support
"""

import logging
import asyncio
import requests
import io
from openai import OpenAI
import sys
import os
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import (
    OPENAI_API_KEY,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID_INDONESIAN,
    TTS_PRIMARY_ENGINE,
    TTS_FALLBACK_ENGINE,
    ELEVENLABS_SETTINGS,
    OPENAI_TTS_SETTINGS,
    API_TIMEOUT_TTS,
    FEATURE_NATURAL_TTS
)

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


class TTSService:
    """Text-to-speech service with multiple engine support"""
    
    def __init__(self):
        self.client = client
        self.elevenlabs_configured = bool(ELEVENLABS_API_KEY)
        self.primary_engine = TTS_PRIMARY_ENGINE
        self.fallback_engine = TTS_FALLBACK_ENGINE
    
    async def generate_audio(
        self, 
        text: str, 
        force_elevenlabs: bool = False
    ) -> tuple[bytes, str]:
        """
        Generate TTS audio with improved engine handling
        
        Args:
            text: Text to convert to speech
            force_elevenlabs: Force use of ElevenLabs engine
            
        Returns:
            tuple[bytes, str]: Audio content and engine used
        """
        if not text or len(text.strip()) == 0:
            raise ValueError("No text to convert")
        
        logger.info(f"🔊 Generating TTS (force_elevenlabs={force_elevenlabs}): {text[:50]}...")
        
        # Try ElevenLabs first if it's primary or forced
        if (self.primary_engine == "elevenlabs" or force_elevenlabs) and self.elevenlabs_configured:
            try:
                return await self._generate_elevenlabs(text)
            except Exception as e:
                logger.warning(f"ElevenLabs failed: {e}")
                if force_elevenlabs:
                    logger.info("Forced ElevenLabs failed, falling back to OpenAI")
        
        # Fallback to OpenAI
        logger.info("🔄 Using OpenAI TTS fallback")
        return await self._generate_openai(text)
    
    async def _generate_elevenlabs(self, text: str) -> tuple[bytes, str]:
        """Generate TTS using ElevenLabs API"""
        if not ELEVENLABS_API_KEY:
            raise ValueError("ElevenLabs API key not configured")
        
        logger.info(f"🔊 ElevenLabs TTS: {text[:50]}...")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID_INDONESIAN}"
        
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        
        # Use grouped settings from config
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
        
        logger.debug(f"🔊 ElevenLabs payload: {payload}")
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=API_TIMEOUT_TTS
            )
            
            logger.info(f"🔊 ElevenLabs response: {response.status_code}")
            
            if response.status_code == 200:
                audio_content = response.content
                logger.info(f"✅ ElevenLabs success ({len(audio_content)} bytes)")
                return audio_content, "elevenlabs"
            else:
                logger.warning(f"ElevenLabs failed: {response.status_code} - {response.text}")
                raise ValueError(f"ElevenLabs API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning("ElevenLabs request timeout")
            raise ValueError("ElevenLabs timeout")
        except requests.exceptions.ConnectionError:
            logger.warning("ElevenLabs connection error")
            raise ValueError("ElevenLabs connection failed")
        except Exception as e:
            logger.warning(f"ElevenLabs error: {e}")
            raise ValueError(f"ElevenLabs error: {e}")
    
    async def _generate_openai(self, text: str) -> tuple[bytes, str]:
        """Generate TTS using OpenAI API"""
        logger.info(f"🔊 OpenAI TTS: {text[:50]}...")
        
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
            logger.error(f"OpenAI TTS error: {e}")
            raise
    
    def create_audio_stream(self, audio_content: bytes) -> io.BytesIO:
        """Create an audio stream from bytes"""
        return io.BytesIO(audio_content)
    
    def get_engine_info(self) -> dict:
        """Get information about available TTS engines"""
        return {
            "primary_engine": self.primary_engine,
            "fallback_engine": self.fallback_engine,
            "elevenlabs_configured": self.elevenlabs_configured,
            "elevenlabs_voice_id": ELEVENLABS_VOICE_ID_INDONESIAN,
            "elevenlabs_model": ELEVENLABS_SETTINGS["model"],
            "openai_voice": OPENAI_TTS_SETTINGS["voice"],
            "natural_speech": FEATURE_NATURAL_TTS
        }