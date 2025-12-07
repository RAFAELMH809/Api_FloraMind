import base64
import requests
import json

# --- CONFIGURACIÓN ---
# OJO: Pon aquí la URL de tu Cloud Run / FastAPI, NO la de Render (TF Serving)
# El endpoint que definiste en main.py es "/predict"
API_URL = "https://api-flowers-latest.onrender.com/predict" 
IMAGE_PATH = "../../data/albahaca/Mg.jpeg"

# Necesitas un token válido porque tu API tiene 'verify_firebase_bearer'
# Opción A: Pega aquí un token que imprimas desde tu app Flutter
ID_TOKEN = "PEGA_AQUI_TU_TOKEN_LARGO_DE_FIREBASE"

# Opción B (Pro): Función para loguearte y obtener token al vuelo
# Necesitas tu API Key de la consola de Firebase -> Project Settings -> General -> Web API Key
FIREBASE_API_KEY = "TU_WEB_API_KEY" 

def get_token_automatico(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={AIzaSyBo-_tIowLcIt_NlDlNEgTRpwT14kNtZxE}"
    resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    if resp.status_code == 200:
        return resp.json()['idToken']
    else:
        print("Error logueando:", resp.text)
        return None

# Descomenta esto si quieres usar la Opción B:
ID_TOKEN = get_token_automatico("urielbitsgreat@gmail.com", "12345678910gg1")

# --- PASO 1: Codificar Imagen a Base64 ---
# Ya no usamos cv2 ni numpy. Mandamos el archivo "crudo" codificado.
# Es como enviar una carta sellada en lugar de enviar el papel picado.
try:
    with open(IMAGE_PATH, "rb") as img_file:
        # Leemos bytes -> Codificamos b64 -> Convertimos a string UTF-8
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
except FileNotFoundError:
    print(f"❌ No encontré la imagen en {IMAGE_PATH}")
    exit()

# --- PASO 2: Preparar Payload ---
# Tu Pydantic model espera: class PredictRequest(BaseModel): image: str
data = {
    "image": b64_string
}

# --- PASO 3: Enviar Request ---
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ID_TOKEN}" # El guardia de seguridad (Auth header)
}

print(f"Enviando a {API_URL}...")

try:
    response = requests.post(API_URL, json=data, headers=headers)
    
    if response.status_code == 200:
        print("✅ Respuesta exitosa:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Error {response.status_code}:")
        print(response.text)

except Exception as e:
    print(f"💥 Error de conexión: {e}")
