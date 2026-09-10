"""
/chat — the primary endpoint (report section 4.2f).

Manages the full end-to-end interaction: language detection, translation to
English for processing, intent recognition, dispatch to the right functional
module, translation of the reply back to the user's language, and TTS audio
generation.
"""
from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.services.language_service import (
    detect_language, translate_to_english, translate_from_english,
)
from app.services.intent_service import detect_intent
from app.services.weather_service import get_weather_response
from app.services.mandi_service import get_mandi_price_response
from app.services.schemes_service import get_scheme_answer
from app.services.crop_care_service import get_crop_care_answer
from app.services.llm_service import chat_completion
from app.services.speech_service import text_to_speech
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])


def _handle_general(query_en: str) -> str:
    system_prompt = (
        "You are AgriBot, a friendly voice-enabled assistant for Indian farmers. "
        "Answer briefly and helpfully."
    )
    return chat_completion(system_prompt, query_en)


def _format_mandi_reply(result: dict) -> str:
    lines = [result["message"]]
    for row in result["prices"][:5]:
        modal = row.get("modal_price") or row.get("Modal_x0020_Price") or "N/A"
        market = row.get("market") or row.get("Market") or ""
        lines.append(f"- {market}: ₹{modal}/quintal")
    return "\n".join(lines)


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    user_text = payload.message.strip()

    # 1. Language detection
    detected_lang = detect_language(user_text)

    # 2. Translate to English for internal processing (no-op if already English)
    query_en = translate_to_english(user_text) if detected_lang != "en" else user_text

    # 3. Intent recognition
    intent_result = detect_intent(query_en)
    intent = intent_result["intent"]

    # 4. Dispatch to the right module
    if intent == "greeting":
        reply_en = "Namaste! I'm AgriBot 🌾 — ask me about weather, mandi prices, government schemes, or crop care."
    elif intent == "weather":
        weather = get_weather_response(query_en)
        reply_en = f"{weather['summary']} {weather['advice']}"
    elif intent == "mandi_price":
        reply_en = _format_mandi_reply(get_mandi_price_response(query_en))
    elif intent == "scheme_info":
        reply_en = get_scheme_answer(query_en)["answer"]
    elif intent == "crop_care":
        reply_en = get_crop_care_answer(query_en)["answer"]
    else:
        reply_en = _handle_general(query_en)

    # 5. Translate reply back to the user's language
    reply_native = (
        translate_from_english(reply_en, detected_lang) if detected_lang != "en" else reply_en
    )

    # 6. Voice synthesis
    audio_url = text_to_speech(reply_native, detected_lang)

    return ChatResponse(
        response=reply_native,
        response_en=reply_en if detected_lang != "en" else None,
        audio_url=audio_url,
        detected_language=detected_lang,
        intent=intent,
    )
