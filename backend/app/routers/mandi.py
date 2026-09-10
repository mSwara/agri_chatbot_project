from fastapi import APIRouter
from app.models.schemas import MandiPriceRequest, MandiPriceResponse
from app.services.mandi_service import get_mandi_price_response

router = APIRouter(tags=["mandi"])


@router.post("/get-mandi-prices", response_model=MandiPriceResponse)
def get_mandi_prices_endpoint(payload: MandiPriceRequest):
    result = get_mandi_price_response(payload.query)
    return MandiPriceResponse(**result)
