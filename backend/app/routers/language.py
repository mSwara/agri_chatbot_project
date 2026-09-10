from fastapi import APIRouter
from app.models.schemas import DetectLanguageRequest, DetectLanguageResponse
from app.services.language_service import detect_language, language_name

router = APIRouter(tags=["language"])


@router.post("/detect-language", response_model=DetectLanguageResponse)
def detect_language_endpoint(payload: DetectLanguageRequest):
    code = detect_language(payload.text)
    return DetectLanguageResponse(language_code=code, language_name=language_name(code))
