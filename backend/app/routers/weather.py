from fastapi import APIRouter
from app.models.schemas import WeatherRequest, WeatherResponse
from app.services.weather_service import get_weather_response

router = APIRouter(tags=["weather"])


@router.post("/get-weather", response_model=WeatherResponse)
def get_weather_endpoint(payload: WeatherRequest):
    result = get_weather_response(payload.query)
    return WeatherResponse(**result)
