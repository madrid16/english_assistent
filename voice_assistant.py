import threading
from datetime import datetime
import difflib
import time
import queue

class VoiceAssistant:
    def __init__(self, stt, tts, dialog_manager, pronunciation_eval, firebase_service, user_id="usuario_demo"):
        self.stt = stt
        self.tts = tts
        self.dialog_manager = dialog_manager
        self.pronunciation_eval = pronunciation_eval
        self.firebase = firebase_service
        self.user_id = user_id

        self.pending_target = None
        self.is_running = False

        # Flags para TTS
        self.tts_queue = queue.Queue()
        self.tts_lock = threading.Lock()
        self.is_playing_tts = False
        self.user_interrupt = threading.Event()
        self.last_tts_text = ""

    # --------------------------------
    # UTILIDADES INTERNAS
    # --------------------------------
    def _is_echo(self, text):
        if not self.last_tts_text:
            return False
        ratio = difflib.SequenceMatcher(None, text.lower(), self.last_tts_text.lower()).ratio()
        return ratio > 0.85

    def _play_tts_worker(self):
        while self.is_running:
            try:
                text = self.tts_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            with self.tts_lock:
                self.is_playing_tts = True
                self.user_interrupt.clear()
                self.last_tts_text = text
                self.tts.speak(text)
                self.is_playing_tts = False

    # --------------------------------
    # CALLBACK DE TRANSCRIPCIÓN FINAL
    # --------------------------------
    def on_final_transcription(self, text):
        user_input = text.strip()
        if not user_input:
            return

        # Ignorar posibles ecos
        if self._is_echo(user_input):
            return

        print(f"\n👤 Usuario: {user_input}")

        if user_input.lower() == "salir":
            print("🛑 Comando salir detectado.")
            self.is_running = False
            self.stt.stop_streaming()
            self.user_interrupt.set()
            return

        # Interrupción de TTS si el usuario habla
        if self.is_playing_tts:
            print("⏹️ Usuario interrumpe TTS")
            self.user_interrupt.set()
            time.sleep(0.1)

        # Evaluación pronunciación
        if self.pending_target:
            feedback = self.pronunciation_eval.evaluate(user_input, self.pending_target)
            print(f"📊 Feedback pronunciación: {feedback}")
            self.firebase.save_user_progress(
                user_id=self.user_id,
                progress={
                    "texto_usuario": user_input,
                    "respuesta_asistente": self.last_tts_text,
                    "frases_objetivo": self.pending_target,
                    "feedback": feedback,
                    "last_update": datetime.utcnow()
                }
            )
            self.pending_target = None
        else:
            # Turno normal GPT
            respuesta, frase_objetivo, _ = self.dialog_manager.generate_response(user_input)
            self.pending_target = frase_objetivo if frase_objetivo else None
            self.last_tts_text = respuesta
            # Agregar respuesta a la cola de TTS
            self.tts_queue.put(respuesta)

    # --------------------------------
    # INICIO DEL ASISTENTE
    # --------------------------------
    def start(self):
        print("🎙️ Asistente escuchando. Di 'salir' para terminar.")
        self.is_running = True

        # Hilo para reproducir TTS en segundo plano
        tts_thread = threading.Thread(target=self._play_tts_worker, daemon=True)
        tts_thread.start()

        # Iniciar streaming STT
        self.stt.start_streaming(
            on_update=lambda x: print(f"⏳ {x}", end="\r"),
            on_final=self.on_final_transcription,
            single_utterance=False
        )

        # Mantener hilo principal vivo
        while self.is_running:
            time.sleep(0.2)

        print("🎙️ Asistente detenido.")
