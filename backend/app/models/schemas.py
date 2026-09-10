from typing import Optional, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="Raw user message, any supported language")
    session_id: Optional[str] = Field(default="default", description="Conversation/session id")


class ChatResponse(BaseModel):
    response: str
    response_en: Optional[str] = None
    audio_url: Optional[str] = None
    detected_language: str
    intent: str


class TranslateRequest(BaseModel):
    text: str
    target_language: str = "en"


class TranslateResponse(BaseModel):
    translated_text: str
    source_language: Optional[str] = None
    target_language: str


class DetectLanguageRequest(BaseModel):
    text: str


class DetectLanguageResponse(BaseModel):
    language_code: str
    language_name: str


IntentType = Literal[
    "weather", "mandi_price", "scheme_info", "crop_care", "general", "greeting"
]


class DetectIntentRequest(BaseModel):
    text: str


class DetectIntentResponse(BaseModel):
    intent: IntentType
    confidence: float


class WeatherRequest(BaseModel):
    query: str = Field(..., description="Natural language query mentioning a location")


class WeatherResponse(BaseModel):
    location: str
    summary: str
    advice: str
    raw: Optional[dict] = None


class MandiPriceRequest(BaseModel):
    query: str = Field(..., description="Natural language query mentioning a crop/location")


class MandiPriceResponse(BaseModel):
    crop: str
    state: Optional[str] = None
    district: Optional[str] = None
    level: str  # district | state | all_india | not_found
    prices: list[dict]
    message: str


class SchemeInfoRequest(BaseModel):
    query: str


class SchemeInfoResponse(BaseModel):
    answer: str
    sources: list[str]


class AgricultureInfoRequest(BaseModel):
    query: str


class AgricultureInfoResponse(BaseModel):
    answer: str
    sources: list[str]


class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "en"


class TextToSpeechResponse(BaseModel):
    audio_url: str


class SpeechToTextResponse(BaseModel):
    text: str
    detected_language: Optional[str] = None
