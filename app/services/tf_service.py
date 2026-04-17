import base64
import io
import numpy as np
import httpx
from PIL import Image
from fastapi import HTTPException
from app.core.config import TF_SERVING_URL, IMG_SIZE

try:
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    TF_PREPROCESS_AVAILABLE = True
except Exception:
    TF_PREPROCESS_AVAILABLE = False


def decode_and_preprocess_jpeg(base64_jpeg: str) -> np.ndarray:
    jpg_bytes = base64.b64decode(base64_jpeg)

    try:
        img = Image.open(io.BytesIO(jpg_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Imagen inválida: {e}")

    if img.size != (IMG_SIZE, IMG_SIZE):
        img = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)

    arr = np.asarray(img).astype(np.float32)

    if TF_PREPROCESS_AVAILABLE:
        arr = preprocess_input(arr)
    else:
        arr = (arr / 127.5) - 1.0

    return arr


async def call_tf_serving(payload: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TF_SERVING_URL, json=payload, timeout=20.0)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="El modelo tardó demasiado en responder")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error de conexión con el modelo: {e}")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TF Serving error: {response.text}")

    return response.json()