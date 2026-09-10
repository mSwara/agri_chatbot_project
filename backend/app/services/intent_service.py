"""
Intent detection: routes a (English-translated) user query to the correct
functional module — weather / mandi_price / scheme_info / crop_care /
greeting / general — mirroring the report's /detect-intent endpoint.

A fast keyword pre-filter handles the obvious cases for free; anything
ambiguous is resolved by the LLM.
"""
import re
from app.services.llm_service import chat_completion
from app.logger import get_logger

logger = get_logger(__name__)

_KEYWORDS = {
    "weather": ["weather", "rain", "temperature", "forecast", "humidity", "climate"],
    "mandi_price": ["price", "mandi", "market rate", "rate of", "sell", "quintal", "cost of"],
    "scheme_info": ["scheme", "subsidy", "yojana", "government scheme", "pm-kisan", "kisan credit"],
    "crop_care": ["disease", "pest", "fertilizer", "sowing", "irrigation", "crop care",
                  "pesticide", "leaf", "seed", "harvest"],
    "greeting": ["hello", "hi", "hey", "namaste", "good morning", "good evening"],
}

VALID_INTENTS = {"weather", "mandi_price", "scheme_info", "crop_care", "general", "greeting"}


def _keyword_match(text: str) -> str | None:
    lowered = text.lower()
    for intent, keywords in _KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", lowered) for kw in keywords):
            return intent
    return None


def detect_intent(text: str) -> dict:
    match = _keyword_match(text)
    if match:
        return {"intent": match, "confidence": 0.85}

    system_prompt = (
        "Classify the farmer's message into exactly one of: weather, mandi_price, "
        "scheme_info, crop_care, greeting, general. Respond with only the single label."
    )
    label = chat_completion(system_prompt, text, temperature=0.0).strip().lower()
    label = label.strip(". ")
    if label not in VALID_INTENTS:
        logger.info("LLM intent '%s' not recognized, defaulting to 'general'.", label)
        label = "general"
    return {"intent": label, "confidence": 0.6}
