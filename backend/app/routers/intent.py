from fastapi import APIRouter
from app.models.schemas import DetectIntentRequest, DetectIntentResponse
from app.services.intent_service import detect_intent

router = APIRouter(tags=["intent"])


@router.post("/detect-intent", response_model=DetectIntentResponse)
def detect_intent_endpoint(payload: DetectIntentRequest):
    result = detect_intent(payload.text)
    return DetectIntentResponse(**result)
