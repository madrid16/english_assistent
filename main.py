import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_CPP_VERBOSITY"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Si usas TensorFlow en algún lado

import signal
import sys

from utils.audio_utils import AudioUtils
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
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        pass
    finally:
        print("Finally: Asistente detenido.")

if __name__ == "__main__":
    main()
