import queue
import signal
import sys
import threading
import time

from stt.google_stt import GoogleSTT
from tts.google_tts import GoogleTTS
from npl.dialog_manager import DialogManager
from npl.pronunciation import PronunciationEvaluator
from utils.audio_utils import AudioUtils
#from firebase_service import FirebaseService

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
tts = GoogleTTS()
dialog_manager = DialogManager()
pronunciation_eval = PronunciationEvaluator()
#firebase = FirebaseService()

# Cola para manejar audio entrante en tiempo real
audio_queue = queue.Queue()
is_running = True

# =========================
# CALLBACK DEL MICRÓFONO
# =========================
def audio_callback(in_data, frame_count, time_info, status):
    audio_queue.put(in_data)
    return (None, pyaudio.paContinue)

# =========================
# PROCESAMIENTO DE AUDIO EN TIEMPO REAL
# =========================
def process_audio_stream(user_id="usuario_demo"):
    """
    Captura audio en tiempo real, lo envía a Google STT,
    procesa la respuesta con GPT, evalúa pronunciación,
    da feedback y guarda todo en Firebase.
    """
    stt.listen_and_transcribe()

    print("🎙️ Asistente iniciado. Habla en cualquier momento (di 'salir' para terminar).")

    while is_running:
        if not audio_queue.empty():
            pcm_data = audio_queue.get()
            text_partial, is_final = stt.process_streaming(pcm_data)

            if text_partial:
                print(f"(Escuchando...) {text_partial}", end="\r")

            if is_final:
                user_input = text_partial.strip()
                print(f"\n👤 Usuario: {user_input}")

                if user_input.lower() == "salir":
                    break

                # 1. Respuesta del diálogo
                respuesta, frases_objetivo = dialog_manager.get_response(user_input)

                # 2. Evaluación de pronunciación (en vivo sobre la frase objetivo)
                feedback = pronunciation_eval.evaluate(user_input, frases_objetivo)
                print(f"🤖 Asistente: {respuesta}")
                print(f"📊 Feedback pronunciación: {feedback}")

                # 3. Guardar en Firebase
                #firebase.guardar_progreso(
                #    usuario_id=user_id,
                #    texto_usuario=user_input,
                #    respuesta_asistente=respuesta,
                #    frases_objetivo=frases_objetivo,
                #    feedback=feedback
                #)

                # 4. Reproducir respuesta por TTS
                tts.speak(respuesta)

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

    # Iniciar captura de audio
    stream = audio_utils.start_recording()
    print("Micrófono encendido. Presiona Ctrl+C para salir.")

    try:
        process_audio_stream()
    finally:
        stream.stop_stream()
        stream.close()
        audio_utils.terminate()
        print("Asistente detenido.")

if __name__ == "__main__":
    main()
