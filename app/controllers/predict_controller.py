import numpy as np
from fastapi import Header, HTTPException
from app.services.auth_service import verify_firebase_bearer
from app.services.tf_service import decode_and_preprocess_jpeg, call_tf_serving
from app.services.queue_service import semaphore
from app.core.config import CLASSES
from app.models.predict_model import PredictRequest, PredictResponse


async def predict_controller(data: PredictRequest, authorization: str | None):

    verify_firebase_bearer(authorization)

    try:
        async with semaphore:
            arr = decode_and_preprocess_jpeg(data.image)
            payload = {"instances": [arr.tolist()]}

            result = await call_tf_serving(payload)

    except Exception as e:
        raise e

    if "predictions" not in result:
        raise HTTPException(status_code=502, detail="Respuesta inválida del modelo")

    pred = np.array(result["predictions"][0], dtype=float)
    pred_idx = int(np.argmax(pred))
    prob = float(pred[pred_idx])

    if prob < 0.10:
        return PredictResponse(plant="NoPlant", confidence=0.0)

    return PredictResponse(
        plant=CLASSES[pred_idx],
        confidence=round(prob, 4)
    )