from fastapi import APIRouter, Header
from app.controllers.predict_controller import predict_controller
from app.models.predict_model import PredictRequest, PredictResponse

router = APIRouter(prefix="/predict", tags=["Prediction"])

@router.post("/", response_model=PredictResponse)
async def predict(
    data: PredictRequest,
    authorization: str | None = Header(None)
):
    return await predict_controller(data, authorization)