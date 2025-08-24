import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_CPP_VERBOSITY"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Si usas TensorFlow en algún lado

import signal
import sys

from stt.google_stt import GoogleSTT
from tts.eleven_tts import ElevenLabsTTS
from npl.dialog_manager import DialogManager
from npl.pronunciation import PronunciationEvaluator
from utils.audio_utils import AudioUtils
from db.firebase_service import FirebaseService

# =========================
# CONFIGURACIÓN GLOBAL
# =========================
RATE = 16000
CHUNK = 1024
CHANNELS = 1
CHUNK = int(RATE / 10)  # 100ms

# =========================
# INSTANCIAS DE MÓDULOS
# =========================
audio_utils = AudioUtils(rate=RATE, chunk=CHUNK)
stt = GoogleSTT(rate=RATE)
tts = ElevenLabsTTS()
dialog_manager = DialogManager()
pronunciation_eval = PronunciationEvaluator()
firebase = FirebaseService()
is_running = True
pending_target = None  # frase que el usuario debe practicar

# =========================
# PROCESAMIENTO DE AUDIO EN TIEMPO REAL
# =========================
def process_audio_stream(user_id="usuario_demo"):
    """
    Captura audio en tiempo real, lo envía a Google STT,
    procesa la respuesta con GPT, evalúa pronunciación,
    da feedback y guarda todo en Firebase.
    """

    def on_final_transcription(text):
        """Callback cuando se detecta una frase completa."""
        global pending_target
        user_input = text.strip()
        print(f"\n👤 Usuario: {user_input}")

        if user_input.lower() == "salir":
            global is_running
            is_running = False
            stt.stop_streaming()
            return
        
        if pending_target:
            # 2. Evaluación de pronunciación (comparando con la frase objetivo)
            # 🔹 Ahora sí: evaluar pronunciación contra la frase pendiente
            feedback = pronunciation_eval.evaluate(user_input, pending_target)
            print(f"📊 Feedback pronunciación: {feedback}")
            pending_target = None  # limpiar después de evaluar
        else:
            # 1. Respuesta del diálogo con GPT
            # 🔹 Nuevo turno: generar respuesta de GPT
            respuesta, frase_objetivo, es_larga = dialog_manager.generate_response(user_input)

        # 3. Guardar en Firebase
        firebase.save_user_progress(
            usuario_id=user_id,
            texto_usuario=user_input,
            respuesta_asistente=respuesta,
            frases_objetivo=frase_objetivo,
            feedback=feedback
        )

        # 4. Reproducir respuesta por TTS
        tts.speak(respuesta)
        # Guardamos la frase objetivo para el próximo turno
        pending_target = frase_objetivo

    # 🔹 Inicia STT con callbacks
    print("🎙️ Asistente escuchando. Di 'salir' para terminar.")
    try:
        stt.audio_utils.start_recording()
        stt.start_streaming(
            on_update=lambda x: print(f"⏳ {x}", end="\r"),
            on_final=on_final_transcription,
            single_utterance=False,  # mantiene una sesión continua
        )
    finally:
        stt.stop_streaming()

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
    global is_running
    print("Micrófono encendido. Presiona Ctrl+C para salir.")
    try:
        process_audio_stream()
    except KeyboardInterrupt:
        pass
    finally:
        # No cierres 'stream' (no existe); 'stop_streaming()' ya se llamó
        print("Asistente detenido.")

if __name__ == "__main__":
    main()
