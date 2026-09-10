"""
Language detection & translation.

The report specifies Google Cloud Translate for detection/translation. To keep
AgriBot runnable without a billed Google Cloud project, this module uses the
free `langdetect` + `deep-translator` (Google Translate web front-end) stack
by default. If you provision Google Cloud credentials, swap the
`_translate_via_google_cloud` / detection calls back in — the function
signatures below are the integration seam.
"""
from langdetect import detect_langs, DetectorFactory
from deep_translator import GoogleTranslator
from app.logger import get_logger

DetectorFactory.seed = 0  # deterministic langdetect results
logger = get_logger(__name__)

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil",
    "te": "Telugu", "kn": "Kannada", "gu": "Gujarati", "bn": "Bengali",
    "pa": "Punjabi", "ml": "Malayalam", "or": "Odia", "ur": "Urdu",
    "as": "Assamese",
}


_CONFIDENCE_THRESHOLD = 0.85


def detect_language(text: str) -> str:
    """
    Returns an ISO-639-1 language code, defaulting to English on failure.

    langdetect is a statistical n-gram detector and is notoriously unreliable
    on very short strings (e.g. "Hello, how are you?" can score higher for
    Somali than English). To keep AgriBot's UX solid on short chat messages,
    we only trust the top guess when it's confident; otherwise, if English is
    among the candidates at all, we prefer it (the app's default/majority
    language), else fall back to the top guess.
    """
    text = (text or "").strip()
    if not text:
        return "en"
    try:
        candidates = detect_langs(text)
        if not candidates:
            return "en"
        best = candidates[0]
        if best.prob >= _CONFIDENCE_THRESHOLD:
            return best.lang
        for cand in candidates:
            if cand.lang == "en":
                return "en"
        return best.lang
    except Exception as exc:  # noqa: BLE001
        logger.warning("Language detection failed (%s); defaulting to English.", exc)
        return "en"


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def translate_text(text: str, target_language: str, source_language: str = "auto") -> str:
    """
    Translate text using GoogleTranslator (deep-translator). No API key required.

    The underlying free endpoint occasionally hiccups and hands back an HTML
    error page instead of raising — retried once before falling back to the
    original text.
    """
    text = (text or "").strip()
    if not text:
        return text
    if source_language == target_language:
        return text
    for attempt in range(2):
        try:
            result = GoogleTranslator(source=source_language, target=target_language).translate(text)
            if result and "That’s an error" not in result and "That's an error" not in result:
                return result
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Translation attempt %d failed (%s -> %s): %s",
                attempt + 1, source_language, target_language, exc,
            )
    logger.error("Translation failed (%s -> %s) after retries; returning original text.",
                 source_language, target_language)
    return text


def translate_to_english(text: str) -> str:
    return translate_text(text, target_language="en")


def translate_from_english(text: str, target_language: str) -> str:
    return translate_text(text, source_language="en", target_language=target_language)
