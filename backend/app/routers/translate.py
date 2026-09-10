from fastapi import APIRouter
from app.models.schemas import TranslateRequest, TranslateResponse
from app.services.language_service import (
    detect_language, translate_to_english, translate_from_english,
)

router = APIRouter(tags=["translate"])


@router.post("/translate-to-english", response_model=TranslateResponse)
def translate_to_english_endpoint(payload: TranslateRequest):
    source = detect_language(payload.text)
    translated = translate_to_english(payload.text)
    return TranslateResponse(translated_text=translated, source_language=source, target_language="en")


@router.post("/translate-from-english", response_model=TranslateResponse)
def translate_from_english_endpoint(payload: TranslateRequest):
    translated = translate_from_english(payload.text, payload.target_language)
    return TranslateResponse(
        translated_text=translated, source_language="en", target_language=payload.target_language
    )
