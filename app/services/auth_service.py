import os
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException
from app.core.config import FIREBASE_CRED_PATH

if os.path.exists(FIREBASE_CRED_PATH):
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)

def verify_firebase_bearer(auth_header: str | None):
    if not auth_header:
        raise HTTPException(status_code=401, detail="Falta Authorization header")

    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization debe ser 'Bearer <token>'")

    token = auth_header.split(" ", 1)[1]

    try:
        return auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")