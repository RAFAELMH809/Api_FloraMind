import base64
import io
import json
import os
import asyncio  # <--- 1. Importar asyncio
import httpx    # <--- 2. Importar httpx (pip install httpx)

import firebase_admin
from firebase_admin import auth, credentials

import numpy as np
from PIL import Image
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, field_validator

# ----------------- Config -----------------
TF_SERVING_URL = "https://flowersv1-latest.onrender.com/v1/models/flowers:predict"
CLASSES = [
    "albahaca", "floripondio", "hierbabuena", "oregano",
    "ruda", "sacateLimon", "tomillo", "violeta",
]

IMG_SIZE = 224

# --- CONFIGURACIÓN DE LA COLA ---
# Define cuántas predicciones SIMULTÁNEAS quieres permitir.
# Si TF Serving es CPU-only, un número bajo (2-5) es mejor para evitar que se congele.
MAX_CONCURRENT_PREDICTIONS = 3 
semaphore = asyncio.Semaphore(MAX_CONCURRENT_PREDICTIONS)

# Inicializa Firebase
cred_path = "floramind.json"
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin_initialized = False

app = FastAPI(title="Plant Identifier API")

# ----------------- Schema de entrada -----------------
class PredictRequest(BaseModel):
    image: str

    @field_validator("image")
    @classmethod
    def validate_base64_jpeg(cls, v: str) -> str:
        try:
            decoded = base64.b64decode(v)
            img = Image.open(io.BytesIO(decoded))
            img.verify()
        except Exception as e:
            raise ValueError("Imagen base64 inválida o no es JPEG/PNG decodificable") from e
        return v

# ----------------- Helpers -----------------
def verify_firebase_bearer(auth_header: str | None):
    if not auth_header:
        raise HTTPException(status_code=401, detail="Falta Authorization header")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization debe ser 'Bearer <token>'")
    token = auth_header.split(" ", 1)[1]
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")

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

# ----------------- Endpoint -----------------
@app.post("/predict")
async def predict(data: PredictRequest, authorization: str | None = Header(None)):
    # 1) Validar token (rápido, no necesita semáforo)
    user = verify_firebase_bearer(authorization)

    # --- INICIO DEL CUELLO DE BOTELLA ---
    # Usamos 'async with semaphore' para hacer cola.
    # Si ya hay 3 personas procesando, la 4ta persona espera aquí sin consumir CPU.
    try:
        async with semaphore:
            
            # 2) Procesamiento de imagen (CPU Bound)
            # Nota: Idealmente esto se corre en un thread pool, pero para este caso está bien aquí.
            arr = decode_and_preprocess_jpeg(data.image) 
            payload = {"instances": [arr.tolist()]}

            # 3) Llamada a TF Serving (IO Bound)
            # CAMBIO IMPORTANTE: Usamos httpx.AsyncClient en lugar de requests
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(TF_SERVING_URL, json=payload, timeout=20.0)
                except httpx.TimeoutException:
                    raise HTTPException(status_code=504, detail="El modelo tardó demasiado en responder")
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"Error de conexión con el modelo: {e}")

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"TF Serving error: {response.text}")

            result = response.json()

    except asyncio.TimeoutError:
        # Esto ocurre si la espera en la cola (el semáforo) es excesiva
        raise HTTPException(status_code=503, detail="El servidor está saturado, intenta de nuevo")
    
    # --- FIN DEL CUELLO DE BOTELLA ---

    if "predictions" not in result:
        raise HTTPException(status_code=502, detail="Respuesta inválida del modelo")

    pred = np.array(result["predictions"][0], dtype=float)
    pred_idx = int(np.argmax(pred))
    prob = float(pred[pred_idx])

    if prob < 0.10:
        return {"plant": "NoPlant", "confidence": 0.0}

    return {"plant": CLASSES[pred_idx], "confidence": round(prob, 4)}
