import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_CPP_VERBOSITY"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Si usas TensorFlow en algún lado

import signal
import sys

from stt.speech_recognition import SpeechRecognizer
from tts.eleven_tts import ElevenLabsTTS
from npl.dialog_manager import DialogManager
from npl.pronunciation import PronunciationEvaluator
from utils.audio_utils import AudioUtils
from db.firebase_service import FirebaseService
from voice_assistant import VoiceAssistant

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
stt = SpeechRecognizer(language_code="en-US", vad_aggressiveness=2)
tts = ElevenLabsTTS()
dialog_manager = DialogManager()
pronunciation_eval = PronunciationEvaluator()
firebase = FirebaseService()

assistant = VoiceAssistant(
    language_code="en-US",
    vad_aggressiveness=2,
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
        assistant.start()
    except KeyboardInterrupt:
        pass
    finally:
        # No cierres 'stream' (no existe); 'stop_streaming()' ya se llamó
        print("Asistente detenido.")

if __name__ == "__main__":
    main()
