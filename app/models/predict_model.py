import base64
import io
from pydantic import BaseModel, field_validator
from PIL import Image


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
            raise ValueError("Imagen base64 inválida") from e
        return v


class PredictResponse(BaseModel):
    plant: str
    confidence: float