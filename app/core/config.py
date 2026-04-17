import os
from dotenv import load_dotenv

load_dotenv()

TF_SERVING_URL = os.getenv(
    "TF_SERVING_URL",
    "https://flowersv1-latest.onrender.com/v1/models/flowers:predict"
)

IMG_SIZE = 224

CLASSES = [
    "albahaca", "floripondio", "hierbabuena", "oregano",
    "ruda", "sacateLimon", "tomillo", "violeta",
]

MAX_CONCURRENT_PREDICTIONS = int(os.getenv("MAX_CONCURRENT_PREDICTIONS", 3))

FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "floramind.json")