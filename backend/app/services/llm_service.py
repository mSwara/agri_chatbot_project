"""
Thin wrapper around the Groq LPU API used for all low-latency chat generation
and entity-extraction tasks across the app. Default model is configurable via
GROQ_MODEL (see backend/.env) — Groq periodically retires/renames models, so
if calls start failing with `model_decommissioned` or `model_not_found`, list
current options with `GET https://api.groq.com/openai/v1/models` and update
GROQ_MODEL accordingly.
"""
import json
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.groq_api_key:
            return None
        from groq import Groq
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def chat_completion(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    """Call the Groq chat model. Falls back to a canned response if no API key is configured."""
    client = _get_client()
    if client is None:
        logger.warning("GROQ_API_KEY not set — returning fallback response.")
        return (
            "I'm currently running without an LLM key configured, so I can't generate "
            "a full answer. Please set GROQ_API_KEY in backend/.env to enable AgriBot's "
            "full intelligence."
        )
    try:
        completion = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:  # noqa: BLE001
        logger.error("Groq call failed: %s", exc)
        return "Sorry, I ran into an error while thinking about that. Please try again."


def extract_entities(user_query: str, fields: list[str], instructions: str = "") -> dict:
    """
    Ask the LLM to extract structured entities (e.g. city, crop, state) from a
    free-text query and return them as a dict. Used by the weather and mandi
    modules exactly as described in the AgriBot report.
    """
    field_list = ", ".join(fields)
    system_prompt = (
        "You are an information-extraction engine for an Indian agricultural assistant. "
        f"Extract the following fields from the user's message: {field_list}. "
        f"{instructions} "
        "Respond ONLY with a compact JSON object with exactly these keys. "
        "Use null for any field you cannot confidently determine."
    )
    raw = chat_completion(system_prompt, user_query, temperature=0.0)
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:  # noqa: BLE001
        logger.warning("Could not parse entity extraction JSON from: %s", raw)
        return {field: None for field in fields}
