"""
Mandi (Market) Price Module (see report section 4.2b).

Flow: LLM extracts crop/state/district from free text -> query the
Government of India Agmarknet dataset (via data.gov.in's open API) ->
if no data at district level, fall back to state level, then all-India,
then finally list available crops. A bundled CSV (`data/mandi_sample.csv`)
is used automatically whenever DATA_GOV_API_KEY is not configured, so the
module still demonstrates the same fallback logic offline.
"""
import csv
import requests
from app.config import settings, DATA_DIR
from app.logger import get_logger
from app.services.llm_service import extract_entities

logger = get_logger(__name__)

AGMARKNET_URL = "https://api.data.gov.in/resource/{resource_id}"
SAMPLE_CSV = DATA_DIR / "mandi_sample.csv"

# data.gov.in silently stalls (rather than rejects) requests carrying Python's
# default "python-requests/x.y" User-Agent — a curl-like one avoids the hang.
_REQUEST_HEADERS = {"User-Agent": "curl/8.4.0", "Accept": "*/*"}


def _load_sample_rows() -> list[dict]:
    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _extract_query_fields(query: str) -> dict:
    return extract_entities(
        query, ["crop", "state", "district"],
        instructions="These refer to an agricultural commodity and an Indian state/district. "
        "Normalize state/district names to standard English spelling.",
    )


def _query_live_api(crop: str, state: str | None, district: str | None) -> list[dict]:
    filters = {"filters[commodity]": crop}
    if state:
        filters["filters[state]"] = state
    if district:
        filters["filters[district]"] = district
    try:
        resp = requests.get(
            AGMARKNET_URL.format(resource_id=settings.agmarknet_resource_id),
            params={
                "api-key": settings.data_gov_api_key,
                "format": "json",
                "limit": 20,
                **filters,
            },
            headers=_REQUEST_HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("records", [])
    except Exception as exc:  # noqa: BLE001
        logger.error("Agmarknet API request failed: %s", exc)
        return []


def _query_sample(crop: str, state: str | None = None, district: str | None = None) -> list[dict]:
    rows = _load_sample_rows()
    crop_l = crop.lower()
    matches = [r for r in rows if crop_l in r["commodity"].lower()]
    if district:
        d = [r for r in matches if r["district"].lower() == district.lower()]
        if d:
            return d
    if state:
        s = [r for r in matches if r["state"].lower() == state.lower()]
        if s:
            return s
    return matches


def get_mandi_price_response(query: str) -> dict:
    fields = _extract_query_fields(query)
    crop = fields.get("crop")
    state = fields.get("state")
    district = fields.get("district")

    if not crop:
        return {
            "crop": "unknown", "state": state, "district": district,
            "level": "not_found", "prices": [],
            "message": "I couldn't identify which crop you're asking about. "
                       "Could you name the crop, e.g. 'onion price in Nashik'?",
        }

    use_live = bool(settings.data_gov_api_key)

    # 1. District level
    level = "district"
    if district:
        prices = (_query_live_api(crop, state, district) if use_live
                  else _query_sample(crop, state, district))
        if prices:
            return _build_response(crop, state, district, level, prices)

    # 2. State level
    level = "state"
    if state:
        prices = (_query_live_api(crop, state, None) if use_live
                  else _query_sample(crop, state, None))
        if prices:
            return _build_response(crop, state, None, level, prices)

    # 3. All-India level
    level = "all_india"
    prices = _query_live_api(crop, None, None) if use_live else _query_sample(crop)
    if prices:
        return _build_response(crop, None, None, level, prices)

    # 4. Nothing found -> list available crops to guide the user
    rows = [] if use_live else _load_sample_rows()
    available = sorted({r["commodity"] for r in rows}) if rows else []
    message = f"I couldn't find any price data for '{crop}'."
    if available:
        message += " Crops I do have data for: " + ", ".join(available) + "."
    return {"crop": crop, "state": state, "district": district, "level": "not_found",
            "prices": [], "message": message}


def _build_response(crop, state, district, level, prices) -> dict:
    scope = district or state or "all-India"
    message = f"Latest {crop} prices ({level.replace('_', ' ')} — {scope}):"
    return {
        "crop": crop, "state": state, "district": district,
        "level": level, "prices": prices[:10], "message": message,
    }
