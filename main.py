import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_CPP_VERBOSITY"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Si usas TensorFlow en algún lado

import signal
import sys

from utils.audio_utils import AudioUtils
from voice_assistant import VoiceAssistant
from db.firebase_db import FirebaseDB
from db.firebase_service import FirebaseService
from npl.gpt_client import GPTClient

# =========================
# CONFIGURACIÓN GLOBAL
# =========================
RATE = 16000
CHANNELS = 1
CHUNK = int(RATE / 10)  # 100ms

# =========================
# INSTANCIAS DE MÓDULOS
# =========================
audio_utils = AudioUtils(rate=RATE, chunk=CHUNK)
firestore = FirebaseDB()
gpt = GPTClient()

assistant = VoiceAssistant(
    language_code="es-419",
    firestore=firestore
)

# =========================
# MANEJO DE CTRL+C
# =========================
def signal_handler(sig, frame):
    global is_running
    print("\n🛑 Finalizando asistente...")
    is_running = False
    audio_utils.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# =========================
# MAIN LOOP
# =========================
def main():
    print("Micrófono encendido. Presiona Ctrl+C para salir.")
    try:
        firebase_service = FirebaseService(db_client=firestore.db, gpt_client=gpt)
        firebase_service.initialize_global_listening_phrases(num_phrases=80)
        print(firestore.get_listening_phrases(8))
        #assistant.start()
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        pass
    finally:
        print("Finally: Asistente detenido.")

if __name__ == "__main__":
    main()
