from fastapi import APIRouter
from app.models.schemas import SchemeInfoRequest, SchemeInfoResponse
from app.services.schemes_service import get_scheme_answer

router = APIRouter(tags=["schemes"])


@router.post("/get-scheme-info", response_model=SchemeInfoResponse)
def get_scheme_info_endpoint(payload: SchemeInfoRequest):
    result = get_scheme_answer(payload.query)
    return SchemeInfoResponse(**result)
