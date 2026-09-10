"""
Speech & Language Modules (report section 4.2e).

- Text-to-Speech: gTTS renders the final response to an .mp3 in
  /static/audio/ and the API returns its URL, voice matched to the response
  language.
- Speech-to-Text: OpenAI Whisper transcribes uploaded audio into text,
  supporting multilingual/Indian-language input. The Whisper model is loaded
  lazily (first request) since it's a large download.
"""
import uuid
from pathlib import Path

from gtts import gTTS

from app.config import AUDIO_DIR
from app.logger import get_logger

logger = get_logger(__name__)

# gTTS uses its own language codes; most Indian languages map 1:1 with ISO codes.
_GTTS_SUPPORTED = {
    "en", "hi", "mr", "ta", "te", "kn", "gu", "bn", "pa", "ml", "ur",
}

_whisper_model = None


def text_to_speech(text: str, language: str = "en") -> str:
    """Generate an mp3 for `text` and return a URL path under /static/audio/."""
    lang = language if language in _GTTS_SUPPORTED else "en"
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath: Path = AUDIO_DIR / filename
    try:
        gTTS(text=text, lang=lang).save(str(filepath))
    except Exception as exc:  # noqa: BLE001
        logger.error("gTTS failed (lang=%s): %s", lang, exc)
        gTTS(text=text, lang="en").save(str(filepath))
    return f"/static/audio/{filename}"


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        logger.info("Loading Whisper 'base' model (first call only) ...")
        _whisper_model = whisper.load_model("base")
    return _whisper_model


def speech_to_text(audio_path: str) -> dict:
    """Transcribe an audio file (any format ffmpeg can decode) using Whisper."""
    try:
        model = _get_whisper_model()
        result = model.transcribe(audio_path)
        return {"text": result.get("text", "").strip(), "detected_language": result.get("language")}
    except Exception as exc:  # noqa: BLE001
        logger.error("Whisper transcription failed: %s", exc)
        return {"text": "", "detected_language": None}
