from fastapi import APIRouter
from app.models.schemas import AgricultureInfoRequest, AgricultureInfoResponse
from app.services.crop_care_service import get_crop_care_answer

router = APIRouter(tags=["agriculture"])


@router.post("/get-agriculture-info", response_model=AgricultureInfoResponse)
def get_agriculture_info_endpoint(payload: AgricultureInfoRequest):
    result = get_crop_care_answer(payload.query)
    return AgricultureInfoResponse(**result)
