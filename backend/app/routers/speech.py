import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File
from app.models.schemas import (
    TextToSpeechRequest, TextToSpeechResponse, SpeechToTextResponse,
)
from app.services.speech_service import text_to_speech, speech_to_text

router = APIRouter(tags=["speech"])


@router.post("/text-to-speech", response_model=TextToSpeechResponse)
def text_to_speech_endpoint(payload: TextToSpeechRequest):
    audio_url = text_to_speech(payload.text, payload.language)
    return TextToSpeechResponse(audio_url=audio_url)


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text_endpoint(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name
    try:
        result = speech_to_text(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return SpeechToTextResponse(**result)
