"""
DENAI API Models
Pydantic request/response models for type safety and validation.
UPDATED: Supports Universal Analytics Response & Clean Architecture.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# =====================
# REQUEST MODELS
# =====================

class QuestionRequest(BaseModel):
    """Standard unified chat request"""
    question: str
    session_id: Optional[str] = None
    user_role: Optional[str] = "Employee"
    mode: Optional[str] = "chat"  # Added to support call/chat mode differentiation

class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    language: Optional[str] = "id"
    voice: Optional[str] = "indonesian"
    slow: Optional[bool] = False

class CallModeRequest(BaseModel):
    """Call mode processing request"""
    session_id: Optional[str] = None
    user_role: Optional[str] = None


# =====================
# RESPONSE MODELS (UNIVERSAL)
# =====================

class StandardResponse(BaseModel):
    """Standard API response"""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class QuestionResponse(BaseModel):
    """
    Unified Chat Response
    Automatically adapts for both pure text (SOP) and rich data (HR Analytics/SQL).
    """
    answer: str
    authorized: bool = True
    tool_called: Optional[str] = None
    intent: Optional[str] = None
    error: Optional[str] = None
    cancelled: Optional[bool] = None
    session_id: Optional[str] = None

    # Langfuse trace ID — returned to frontend for human feedback
    trace_id: Optional[str] = None

    # 🌟 NEW UNIVERSAL ANALYTICS FIELDS (From chat_service.py)
    message_type: Optional[str] = None
    domain: Optional[str] = None
    data: Optional[Dict[str, Any]] = None           # Contains 'columns' and 'rows'
    visualization_available: Optional[bool] = None
    conversation_id: Optional[str] = None
    turn_id: Optional[str] = None
    chart_hints: Optional[Dict[str, Any]] = None
    sql_query: Optional[str] = None                 # Transparency feature
    sql_explanation: Optional[str] = None           # Transparency feature
    
    # Legacy fallbacks just in case
    data_type: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


# =====================
# SERVICE STATUS & INFO MODELS
# =====================

class TTSResponse(BaseModel):
    engine: str
    voice: str
    language: str
    duration: Optional[float] = None
    status: str = "success"

class STTResponse(BaseModel):
    transcript: str
    language: str
    confidence: str
    status: str
    engine: str

class SessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    message: Optional[str] = None
    pinned: Optional[bool] = None

class SessionInfo(BaseModel):
    session_id: str
    title: str
    created_at: str
    last_message_at: Optional[str] = None
    pinned: bool = False
    message_count: Optional[int] = None

class MessageInfo(BaseModel):
    role: str
    message: str
    timestamp: Optional[str] = None

class UserRoleResponse(BaseModel):
    role: str
    is_hr: bool
    permissions: Dict[str, bool]

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    features: List[str]
    config_status: Dict[str, Any]

class SpeechStatusResponse(BaseModel):
    speech_recognition: Dict[str, Any]
    text_to_speech: Dict[str, Any]
    ai_model: Dict[str, Any]


# =====================
# UTILITY MODELS
# =====================

class APIError(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int = 500
    timestamp: Optional[str] = None

class FileUploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str
    status: str
    message: Optional[str] = None


# =====================
# CONFIG MODELS (Development)
# =====================

class ModelConfig(BaseModel):
    llm_model: str
    temperature: float
    max_tokens: int

class SpeechConfig(BaseModel):
    language: str
    primary_tts: str
    fallback_tts: str
    elevenlabs_settings: Dict[str, Any]
    openai_settings: Dict[str, Any]

class TimeoutConfig(BaseModel):
    default: float
    call_mode: float
    tts: float

class ModeConfig(BaseModel):
    call_temperature: float
    chat_temperature: float
    call_max_tokens: int
    chat_max_tokens: int

class FeatureFlags(BaseModel):
    natural_tts: bool
    verbose_logging: bool

class ConfigResponse(BaseModel):
    ai_model_config: ModelConfig
    speech_config: SpeechConfig
    timeout_config: TimeoutConfig
    mode_config: ModeConfig
    feature_flags: FeatureFlags
    environment: str