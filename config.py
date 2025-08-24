import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

# ===========================
# CONFIGURACIÓN DE FIREBASE
# ===========================
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, FIREBASE_CREDENTIALS)
# Google Cloud y Firebase



# ===========================
# CONFIGURACIÓN DE AUDIO
# ===========================
AUDIO_RATE = 16000
AUDIO_CHUNK = 1024

# ===========================
# CONFIGURACIÓN DE GOOGLE APIs
# ===========================
GOOGLE_STT_LANGUAGE = "es-CL"   # Idioma para Speech-to-Text
GOOGLE_TTS_LANGUAGE = "es-CL"   # Idioma para Text-to-Speech
GOOGLE_TTS_VOICE = "es-CL-Standard-B"  # Voz predeterminada

# ===========================
# CONFIGURACIÓN DE IA (GPT)
# ===========================
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7
