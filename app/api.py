"""
DENAI API - FINAL BALANCED VERSION
Clean code with smart configuration (not over-engineered)
"""

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import json
import os
import logging
import asyncio
import io
import requests
import re
from openai import OpenAI

# Import balanced configuration
from app.config import (
    OPENAI_API_KEY, 
    ELEVENLABS_API_KEY, 
    ELEVENLABS_VOICE_ID_INDONESIAN,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    TTS_PRIMARY_ENGINE,
    TTS_FALLBACK_ENGINE,
    SPEECH_LANGUAGE_DEFAULT,
    ELEVENLABS_SETTINGS,
    OPENAI_TTS_SETTINGS,
    API_TIMEOUT_DEFAULT,
    API_TIMEOUT_CALL_MODE,
    API_TIMEOUT_TTS,
    CALL_MODE_TEMPERATURE,
    CHAT_MODE_TEMPERATURE,
    CALL_MODE_MAX_TOKENS,
    CHAT_MODE_MAX_TOKENS,
    FEATURE_NATURAL_TTS,
    FEATURE_VERBOSE_LOGGING,
    ENVIRONMENT
)

# Import tools and memory
try:
    from app.tools import TOOLS_SCHEMA, TOOL_FUNCTIONS, HR_TOOLS
except ImportError:
    TOOLS_SCHEMA = []
    TOOL_FUNCTIONS = {}
    HR_TOOLS = []

from app.rules import is_hr_allowed
from memory.memory_supabase import (
    get_sessions, get_recent_history, save_message, save_session,
    toggle_pin_session, delete_session_and_messages
)

# Setup
logging.basicConfig(
    level=logging.DEBUG if FEATURE_VERBOSE_LOGGING else logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI(title="DENAI - Natural TTS", version="6.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)

# =====================
# CONSTANTS
# =====================

# TTS text cleaning constants
TTS_EMOJIS_TO_REMOVE = ['✅', '❌', '🔒', '⏰', '❓', '🌐', '📞', '💰', '🎯', '🚀', '🤖']

# =====================
# MODELS
# =====================

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    user_role: Optional[str] = None

# =====================
# CORE FUNCTIONS
# =====================

def clean_text_for_tts(html_text: str) -> str:
    """Clean HTML for natural TTS speech."""
    if not html_text or not FEATURE_NATURAL_TTS:
        return html_text
    
    logger.debug("🧹 Cleaning text for natural TTS")
    
    text = html_text
    
    # Remove section titles and HTML tags
    text = re.sub(r'<h3>.*?</h3>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]*>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[•\-\*]\s*', '', text)
    
    # Remove problematic emojis using constant list
    for emoji in TTS_EMOJIS_TO_REMOVE:
        text = text.replace(emoji, '')
    
    # Remove document references
    text = re.sub(r'Rujukan Dokumen.*', '', text, flags=re.DOTALL)
    text = re.sub(r'Sumber:.*?(?=\n|$)', '', text)
    text = re.sub(r'Bagian:.*?(?=\n|$)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    if FEATURE_VERBOSE_LOGGING:
        logger.debug(f"Text cleaned: {len(html_text)} → {len(text)} chars")
    
    return text


async def run_chat_completion(
    messages: list, 
    tools: Optional[list] = None, 
    timeout: float = API_TIMEOUT_DEFAULT,
    max_tokens: Optional[int] = None,
    temperature: float = LLM_TEMPERATURE,
    mode: str = "chat"
):
    """Unified chat completion with mode-specific settings."""
    try:
        # Use mode-specific settings
        if mode == "call":
            actual_timeout = API_TIMEOUT_CALL_MODE
            actual_max_tokens = CALL_MODE_MAX_TOKENS
            actual_temperature = CALL_MODE_TEMPERATURE
        else:
            actual_timeout = timeout
            actual_max_tokens = max_tokens or CHAT_MODE_MAX_TOKENS
            actual_temperature = temperature
        
        return await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.completions.create,
                model=LLM_MODEL,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=actual_temperature,
                max_tokens=actual_max_tokens
            ),
            timeout=actual_timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Chat completion timeout after {actual_timeout}s")
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_tts_audio(text: str):
    """Generate TTS audio with clean config-based settings."""
    if not text or len(text.strip()) == 0:
        raise ValueError("No text to convert")
    
    logger.info(f"🔊 Generating TTS: {text[:50]}...")
    
    # Try primary TTS engine
    if TTS_PRIMARY_ENGINE == "elevenlabs" and ELEVENLABS_API_KEY:
        try:
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
            
            response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT_TTS)
            
            if response.status_code == 200:
                logger.info(f"✅ ElevenLabs success ({len(response.content)} bytes)")
                return response.content, "elevenlabs"
            else:
                logger.warning(f"ElevenLabs failed: {response.status_code}")
                
        except requests.RequestException as e:
            # Network-specific exception handling
            logger.warning(f"ElevenLabs network error: {e}")
        except Exception as e:
            # Fallback for non-network errors
            logger.warning(f"ElevenLabs error: {e}")
    
    # Fallback to secondary engine
    logger.info(f"🔄 Using {TTS_FALLBACK_ENGINE.upper()} TTS fallback")
    try:
        response = await asyncio.to_thread(
            client.audio.speech.create,
            model="tts-1",
            voice=OPENAI_TTS_SETTINGS["voice"],
            input=text,
            response_format="mp3",
            speed=OPENAI_TTS_SETTINGS["speed"]
        )
        
        logger.info("✅ OpenAI TTS success")
        return response.content, "openai"
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise


async def process_stt(audio_file_obj) -> str:
    """Process Speech-to-Text with configured language."""
    try:
        transcript_response = await asyncio.to_thread(
            client.audio.transcriptions.create,
            model="whisper-1",
            file=audio_file_obj,
            language=SPEECH_LANGUAGE_DEFAULT,
            response_format="text"
        )
        
        transcript = transcript_response if isinstance(transcript_response, str) else transcript_response.text
        return transcript.strip()
        
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise


async def handle_tool_execution(
    tool_call, 
    session_id: str, 
    user_role: str, 
    original_question: str,
    mode: str = "chat"
):
    """Unified tool execution with mode awareness."""
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    
    user = {"role": user_role or "Employee"}
    is_hr = is_hr_allowed(user)
    
    # Check HR authorization
    if function_name in HR_TOOLS and not is_hr:
        return "🔒 Data karyawan hanya dapat diakses oleh tim HR."
    
    # Execute function
    if function_name not in TOOL_FUNCTIONS:
        return "Maaf, fungsi tidak tersedia."
    
    try:
        tool_function = TOOL_FUNCTIONS[function_name]
        
        if function_name == "search_sop":
            function_args["session_id"] = session_id
        
        tool_result = tool_function(**function_args)
        
        # Handle direct SOP response
        if function_name == "search_sop" and isinstance(tool_result, str):
            if mode == "call" and len(tool_result) > 150:
                return tool_result[:130] + "... Butuh detail lengkap?"
            return tool_result
        
        # Get AI response based on tool result
        final_response = await run_chat_completion(
            messages=[
                {"role": "user", "content": original_question},
                {"role": "assistant", "content": None, "tool_calls": [tool_call]},
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)[:500 if mode == "call" else 2000]
                }
            ],
            mode=mode
        )
        
        return final_response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return "Maaf, terjadi gangguan sistem."


# =====================
# API ENDPOINTS
# =====================

@app.post("/speech/text-to-speech")
async def text_to_speech_natural(request: Request, text: str):
    """Convert text to natural speech."""
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text required")
        
        # Clean text for natural speech
        clean_text = clean_text_for_tts(text)
        
        if not clean_text or len(clean_text.strip()) < 5:
            raise HTTPException(status_code=400, detail="No valid text after cleaning")
        
        # Generate TTS
        audio_content, engine = await generate_tts_audio(clean_text)
        
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


@app.post("/speech/speech-to-text")
async def speech_to_text_optimized(
    request: Request,
    audio_file: UploadFile = File(...)
):
    """Speech to text with configured language."""
    try:
        logger.info(f"🎤 STT request: {audio_file.filename}")
        
        # Read and process audio
        audio_content = await audio_file.read()
        audio_file_obj = io.BytesIO(audio_content)
        audio_file_obj.name = audio_file.filename or "audio.wav"
        
        transcript = await process_stt(audio_file_obj)
        logger.info(f"✅ STT result: {transcript[:50]}...")
        
        return {
            "transcript": transcript,
            "language": SPEECH_LANGUAGE_DEFAULT,
            "confidence": "high",
            "status": "success",
            "engine": "whisper"
        }
        
    except Exception as e:
        logger.error(f"STT Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/call/process")
async def call_mode_natural(
    request: Request,
    audio_file: UploadFile = File(...),
    session_id: str = None,
    user_role: Optional[str] = None
):
    """Call mode with natural TTS and optimized flow."""
    try:
        logger.info("📞 Call mode processing...")
        
        # Process audio input
        audio_content = await audio_file.read()
        audio_file_obj = io.BytesIO(audio_content)
        audio_file_obj.name = "call.wav"
        
        transcript = await process_stt(audio_file_obj)
        logger.info(f"📞 User: {transcript}")
        
        if not transcript:
            error_response = "Maaf, saya tidak mendengar dengan jelas. Bisa diulangi?"
            clean_error = clean_text_for_tts(error_response)
            audio_content, _ = await generate_tts_audio(clean_error)
            return StreamingResponse(io.BytesIO(audio_content), media_type="audio/mpeg")
        
        # Setup session
        if not session_id:
            session_id = str(uuid.uuid4())
            save_session(session_id, "📞 Call")
        
        save_message(session_id, "user", transcript)
        
        # Prepare AI conversation with concise prompt
        system_prompt = """DENAI, asisten AI perusahaan. Mode panggilan.

Jawaban: RINGKAS, SOPAN, NATURAL (max 2 kalimat).

Tools:
🚀 search_sop - Kebijakan perusahaan  
🤖 search_hr_data - Data HR (HR only)"""
        
        # Get recent history and build messages
        history = get_recent_history(session_id, limit=1)
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            h = history[-1]
            role = h["role"] if h["role"] in ["user", "assistant"] else "user"
            content = h["message"][:100]
            messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": transcript})
        
        # Get AI response using call mode settings
        response = await run_chat_completion(
            messages=messages,
            tools=TOOLS_SCHEMA if TOOLS_SCHEMA else None,
            mode="call"
        )
        
        message = response.choices[0].message
        answer = None
        
        # Handle tool calls or direct response
        if message.tool_calls and TOOL_FUNCTIONS:
            answer = await handle_tool_execution(
                tool_call=message.tool_calls[0],
                session_id=session_id,
                user_role=user_role or "Employee",
                original_question=transcript,
                mode="call"
            )
        else:
            answer = message.content
        
        if not answer:
            answer = "Maaf, tidak bisa memproses permintaan."
        
        # Save and generate TTS
        save_message(session_id, "assistant", answer)
        
        # Clean text and generate natural TTS
        clean_text = clean_text_for_tts(answer)
        audio_content, engine = await generate_tts_audio(clean_text)
        
        logger.info(f"📞 DENAI: {answer[:50]}...")
        
        def generate():
            yield audio_content
        
        return StreamingResponse(
            generate(),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "X-Session-ID": session_id,
                "X-Voice": "Indonesian-Natural",
                "X-Engine": engine,
                "X-Natural-TTS": "true"
            }
        )
        
    except Exception as e:
        logger.error(f"📞 Call error: {e}")
        error_msg = "Maaf, terjadi gangguan."
        try:
            clean_error = clean_text_for_tts(error_msg)
            audio_content, _ = await generate_tts_audio(clean_error)
            return StreamingResponse(io.BytesIO(audio_content), media_type="audio/mpeg")
        except:
            raise HTTPException(status_code=500, detail="Call processing failed")


@app.post("/ask")
async def ask_question(request: Request, req: QuestionRequest):
    """Text-based question answering with HTML output preservation."""
    try:
        if not req.session_id:
            req.session_id = str(uuid.uuid4())
        
        user_role = req.user_role or os.getenv("USER_ROLE", "Employee")
        logger.info(f"📝 Question: {req.question[:50]}...")
        
        # Setup session
        existing = get_recent_history(req.session_id, limit=1)
        if not existing:
            title = req.question[:50] + "..."
            save_session(req.session_id, title)
        
        save_message(req.session_id, "user", req.question)
        
        # Prepare conversation
        system_prompt = """DENAI, asisten AI perusahaan. Jawab dalam bahasa Indonesia yang jelas.

🚀 search_sop - Dokumen perusahaan (umum)
🤖 search_hr_data - Database HR (khusus HR)

Berikan jawaban akurat dan membantu."""

        # Build messages with history
        history = get_recent_history(req.session_id, limit=4)
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for h in history[-3:]:
                role = h["role"] if h["role"] in ["user", "assistant"] else "user"
                content = h["message"][:300]
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": req.question})
        
        # Get AI response using chat mode settings
        response = await run_chat_completion(
            messages=messages,
            tools=TOOLS_SCHEMA if TOOLS_SCHEMA else None,
            mode="chat"
        )
        
        message = response.choices[0].message
        
        # Handle function calls or direct response
        if message.tool_calls and TOOL_FUNCTIONS:
            user = {"role": user_role}
            is_hr = is_hr_allowed(user)
            
            # Check HR authorization
            function_name = message.tool_calls[0].function.name
            if function_name in HR_TOOLS and not is_hr:
                answer = "🔒 Data karyawan hanya dapat diakses oleh tim HR."
                save_message(req.session_id, "assistant", answer)
                return {
                    "answer": answer,
                    "session_id": req.session_id,
                    "authorized": False
                }
            
            # Execute tool
            answer = await handle_tool_execution(
                tool_call=message.tool_calls[0],
                session_id=req.session_id,
                user_role=user_role,
                original_question=req.question,
                mode="chat"
            )
            
            save_message(req.session_id, "assistant", answer)
            return {
                "answer": answer,  # HTML format preserved
                "session_id": req.session_id,
                "tool_called": function_name,
                "authorized": True
            }
        
        # Direct response
        answer = message.content
        save_message(req.session_id, "assistant", answer)
        
        return {
            "answer": answer,  # HTML format preserved
            "session_id": req.session_id,
            "tool_called": None
        }
        
    except Exception as e:
        logger.error(f"Ask error: {e}")
        error_msg = "Server error. Silakan coba lagi."
        return {"error": error_msg, "session_id": req.session_id}


# =====================
# SESSION MANAGEMENT
# =====================

@app.post("/sessions/{session_id}/pin")
async def pin_session_endpoint(session_id: str):
    """Toggle pin status for a session"""
    try:
        pinned = toggle_pin_session(session_id)
        logger.info(f"📌 Session pinned={pinned}")
        return {"success": True, "pinned": pinned}
    except Exception as e:
        logger.error(f"Pin session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete session and all its messages"""
    try:
        delete_session_and_messages(session_id)
        logger.info(f"🗑️ Session deleted: {session_id[:8]}...")
        return {"success": True, "message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# INFO ENDPOINTS
# =====================

@app.get("/")
def read_root():
    return {
        "status": "active",
        "service": "DENAI - Natural TTS",
        "version": "6.2.0",
        "configuration": {
            "llm_model": LLM_MODEL,
            "tts_primary": TTS_PRIMARY_ENGINE,
            "tts_fallback": TTS_FALLBACK_ENGINE,
            "language": SPEECH_LANGUAGE_DEFAULT,
            "natural_tts": FEATURE_NATURAL_TTS
        },
        "improvements": [
            "✅ Balanced configuration (no over-engineering)",
            "✅ Grouped TTS settings for cleaner config",
            "✅ Mode-specific constants (call vs chat)",
            "✅ Essential feature flags only",
            "✅ Production-ready structure"
        ]
    }


@app.get("/sessions")
def list_sessions():
    try:
        return get_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{session_id}")
def load_history(session_id: str):
    try:
        return get_recent_history(session_id, limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/role")
def get_user_role():
    role = os.getenv("USER_ROLE", "Employee")
    is_hr = role.upper() == "HR"
    
    return {
        "role": role,
        "is_hr": is_hr,
        "permissions": {
            "access_hr_data": is_hr,
            "access_sop": True,
            "speech_features": True,
            "natural_tts": FEATURE_NATURAL_TTS
        }
    }


@app.get("/speech/status")
def speech_status():
    return {
        "speech_recognition": {
            "available": True,
            "engine": "OpenAI Whisper",
            "language": SPEECH_LANGUAGE_DEFAULT,
            "model": "whisper-1"
        },
        "text_to_speech": {
            "available": True,
            "primary_engine": TTS_PRIMARY_ENGINE,
            "fallback_engine": TTS_FALLBACK_ENGINE,
            "voice_id": ELEVENLABS_VOICE_ID_INDONESIAN,
            "elevenlabs_model": ELEVENLABS_SETTINGS["model"],
            "openai_voice": OPENAI_TTS_SETTINGS["voice"],
            "natural_speech": FEATURE_NATURAL_TTS
        },
        "ai_model": {
            "model": LLM_MODEL,
            "chat_temperature": CHAT_MODE_TEMPERATURE,
            "call_temperature": CALL_MODE_TEMPERATURE,
            "max_tokens_chat": CHAT_MODE_MAX_TOKENS,
            "max_tokens_call": CALL_MODE_MAX_TOKENS
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "6.2.0",
        "environment": ENVIRONMENT,
        "features": [
            "🎤 Natural conversational TTS",
            "📱 HTML text output preserved", 
            "🔊 Smart text cleaning for speech",
            "💰 Cost-optimized configuration",
            "📌 Session management",
            "⚙️ Balanced config (no over-engineering)"
        ],
        "config_status": {
            "openai_configured": bool(OPENAI_API_KEY),
            "elevenlabs_configured": bool(ELEVENLABS_API_KEY),
            "model": LLM_MODEL,
            "tts_engines": f"{TTS_PRIMARY_ENGINE} → {TTS_FALLBACK_ENGINE}",
            "natural_tts": FEATURE_NATURAL_TTS,
            "verbose_logging": FEATURE_VERBOSE_LOGGING
        }
    }


# =====================
# 🔒 DEVELOPMENT-ONLY ENDPOINTS
# =====================

if ENVIRONMENT == "development":
    @app.get("/config")
    def get_current_config():
        """Development-only endpoint to inspect configuration"""
        return {
            "model_config": {
                "llm_model": LLM_MODEL,
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS
            },
            "speech_config": {
                "language": SPEECH_LANGUAGE_DEFAULT,
                "primary_tts": TTS_PRIMARY_ENGINE,
                "fallback_tts": TTS_FALLBACK_ENGINE,
                "elevenlabs_settings": ELEVENLABS_SETTINGS,
                "openai_settings": OPENAI_TTS_SETTINGS
            },
            "timeout_config": {
                "default": API_TIMEOUT_DEFAULT,
                "call_mode": API_TIMEOUT_CALL_MODE,
                "tts": API_TIMEOUT_TTS
            },
            "mode_config": {
                "call_temperature": CALL_MODE_TEMPERATURE,
                "chat_temperature": CHAT_MODE_TEMPERATURE,
                "call_max_tokens": CALL_MODE_MAX_TOKENS,
                "chat_max_tokens": CHAT_MODE_MAX_TOKENS
            },
            "feature_flags": {
                "natural_tts": FEATURE_NATURAL_TTS,
                "verbose_logging": FEATURE_VERBOSE_LOGGING
            },
            "environment": ENVIRONMENT
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)