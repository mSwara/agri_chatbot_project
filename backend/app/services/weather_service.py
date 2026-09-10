"""
Weather Information Module (see report section 4.2a).

Flow: LLM extracts the city/district from the free-text query -> OpenWeatherMap
is called -> the raw meteorological data is turned into farmer-friendly
language with basic crop-protection advice, in the style of a rural
agricultural advisor.
"""
import requests
from app.config import settings
from app.logger import get_logger
from app.services.llm_service import extract_entities, chat_completion

logger = get_logger(__name__)

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


def _extract_location(query: str) -> str:
    entities = extract_entities(
        query, ["location"],
        instructions="The location is an Indian city, town or district mentioned or implied by the user.",
    )
    return entities.get("location") or query


def _fetch_weather(location: str) -> dict | None:
    if not settings.openweather_api_key:
        return None
    try:
        resp = requests.get(
            OWM_URL,
            params={
                "q": f"{location},IN",
                "appid": settings.openweather_api_key,
                "units": "metric",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning("OpenWeatherMap error %s: %s", resp.status_code, resp.text)
            return None
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("OpenWeatherMap request failed: %s", exc)
        return None


def get_weather_response(query: str) -> dict:
    location = _extract_location(query)
    raw = _fetch_weather(location)

    if raw is None:
        summary = (
            f"I couldn't fetch live weather for '{location}' right now "
            "(check that OPENWEATHER_API_KEY is set in backend/.env)."
        )
        advice = "Please try again later, or check a local weather source before spraying or irrigating."
        return {"location": location, "summary": summary, "advice": advice, "raw": None}

    weather_main = raw["weather"][0]["main"]
    weather_desc = raw["weather"][0]["description"]
    temp = raw["main"]["temp"]
    humidity = raw["main"]["humidity"]
    wind = raw["wind"]["speed"]

    system_prompt = (
        "You are a friendly rural agricultural advisor in India talking to a farmer. "
        "Given raw weather data, describe it in one or two simple, encouraging sentences "
        "(e.g. 'light rain', 'humid day') and then give one short, practical crop-protection "
        "tip relevant to these conditions. Keep it under 60 words total, no jargon."
    )
    user_prompt = (
        f"Location: {location}\nCondition: {weather_main} ({weather_desc})\n"
        f"Temperature: {temp} C\nHumidity: {humidity}%\nWind speed: {wind} m/s"
    )
    advisory = chat_completion(system_prompt, user_prompt)

    summary = f"{weather_desc.capitalize()}, {temp}°C, humidity {humidity}%, wind {wind} m/s in {location}."
    return {"location": location, "summary": summary, "advice": advisory, "raw": raw}
