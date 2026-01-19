"""
DENAI API Models
Pydantic request/response models for type safety and validation
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# =====================
# REQUEST MODELS
# =====================

class QuestionRequest(BaseModel):
    """Standard chat question request"""
    question: str
    session_id: Optional[str] = None
    user_role: Optional[str] = None


class HRAnalyticsRequest(BaseModel):
    """HR analytics with visualization request"""
    question: str
    session_id: Optional[str] = None
    user_role: Optional[str] = "Employee"
    enable_visualization: Optional[bool] = True


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
# RESPONSE MODELS
# =====================

class StandardResponse(BaseModel):
    """Standard API response"""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class QuestionResponse(BaseModel):
    """Chat question response"""
    answer: str
    session_id: str
    tool_called: Optional[str] = None
    authorized: bool = True
    error: Optional[str] = None


class HRAnalyticsResponse(BaseModel):
    """HR analytics with visualization response"""
    text_response: str
    has_visualization: bool
    chart_config: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None
    visualization_reasoning: Optional[str] = None
    session_id: Optional[str] = None
    query_info: Optional[Dict[str, Any]] = None
    authorized: bool = True
    error: Optional[str] = None


class TTSResponse(BaseModel):
    """Text-to-speech response metadata"""
    engine: str
    voice: str
    language: str
    duration: Optional[float] = None
    status: str = "success"


class STTResponse(BaseModel):
    """Speech-to-text response"""
    transcript: str
    language: str
    confidence: str
    status: str
    engine: str


class SessionResponse(BaseModel):
    """Session operation response"""
    success: bool
    session_id: Optional[str] = None
    message: Optional[str] = None
    pinned: Optional[bool] = None


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    title: str
    created_at: str
    pinned: bool = False
    message_count: Optional[int] = None


class MessageInfo(BaseModel):
    """Message information"""
    role: str
    message: str
    timestamp: str


class UserRoleResponse(BaseModel):
    """User role and permissions response"""
    role: str
    is_hr: bool
    permissions: Dict[str, bool]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    features: List[str]
    config_status: Dict[str, Any]


class SpeechStatusResponse(BaseModel):
    """Speech system status response"""
    speech_recognition: Dict[str, Any]
    text_to_speech: Dict[str, Any]
    ai_model: Dict[str, Any]


class VisualizationStatusResponse(BaseModel):
    """HR visualization system status"""
    status: str
    hr_engine: bool
    visualization_engine: bool
    features: Optional[List[str]] = None
    supported_charts: Optional[List[str]] = None
    color_scheme: Optional[Dict[str, str]] = None
    endpoint: Optional[str] = None
    requirements: Optional[List[str]] = None
    error: Optional[str] = None


# =====================
# UTILITY MODELS
# =====================

class APIError(BaseModel):
    """Standard API error response"""
    error: str
    detail: Optional[str] = None
    status_code: int = 500
    timestamp: Optional[str] = None


class FileUploadResponse(BaseModel):
    """File upload response"""
    filename: str
    size: int
    content_type: str
    status: str
    message: Optional[str] = None


# =====================
# CONFIG MODELS (Development)
# =====================

class ModelConfig(BaseModel):
    """AI model configuration"""
    llm_model: str
    temperature: float
    max_tokens: int


class SpeechConfig(BaseModel):
    """Speech system configuration"""
    language: str
    primary_tts: str
    fallback_tts: str
    elevenlabs_settings: Dict[str, Any]
    openai_settings: Dict[str, Any]


class TimeoutConfig(BaseModel):
    """API timeout configuration"""
    default: float
    call_mode: float
    tts: float


class ModeConfig(BaseModel):
    """Mode-specific configuration"""
    call_temperature: float
    chat_temperature: float
    call_max_tokens: int
    chat_max_tokens: int


class FeatureFlags(BaseModel):
    """Feature flag configuration"""
    natural_tts: bool
    verbose_logging: bool


class ConfigResponse(BaseModel):
    """Full configuration response (development only)"""
    ai_model_config: ModelConfig
    speech_config: SpeechConfig
    timeout_config: TimeoutConfig
    mode_config: ModeConfig
    feature_flags: FeatureFlags
    environment: str