import threading
import queue
import time

from stt.speech_recognition import SpeechRecognizer
from tts.eleven_tts import ElevenLabsTTS
from npl.dialog_manager import DialogManager
from npl.listening_test import ListeningTest


class VoiceAssistant:
    def __init__(self, language_code="en-US", vad_aggressiveness=2, keywords_expansion=False):
        self.language_code = language_code
        self.keywords_expansion = keywords_expansion

        # Inicializa componentes
        self.stt = SpeechRecognizer(language_code=language_code, rate=16000, chunk_duration_ms=100)
        self.tts = ElevenLabsTTS()
        self.dialog_manager = DialogManager()

        self.listening_test = ListeningTest(tts=self.tts, stt=self.stt)

        # Control de ejecución
        self.response_queue = queue.Queue()
        self.speaking = False
        self.running = False
        self.stt.callback = self.on_user_speech

        # Hilos
        self.capture_thread = None
        self.recognition_thread = None

    def start(self):
        """Inicia el asistente de voz"""
        print("🔊 Iniciando asistente de voz...")
        self.running = True
        self.stt.running = True

        # Hilo para procesar respuestas y hablar
        threading.Thread(target=self._process_responses).start()
        # Hilos para STT
        self.capture_thread = threading.Thread(target=self.stt._capture_audio)
        self.recognition_thread = threading.Thread(target=self.stt._streaming_recognition)
        self.capture_thread.start()
        self.recognition_thread.start()
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Detiene el asistente"""
        self.running = False
        self.stt.stop()
        if self.capture_thread:
            self.capture_thread.join()
        if self.recognition_thread:
            self.recognition_thread.join()
        print("🛑 Asistente detenido.")

    def on_user_speech(self, text):
        """
        Callback que se llama cuando el usuario dice algo.
        Procesa el texto y encola una respuesta del asistente.
        """
        text = text.strip().lower()
        if not text:
            return

        print(f"👤 Usuario: {text}")

        if text in ["salir", "exit", "quit"]:
            self.stop()
            return
        
        if text == "start listening test" or "empezar test inicial":
            print("Iniciando prueba de listening...")
            evaluation = self.listening_test.start_test(
                user_id="usuario123",
                listening_items=mi_lista_de_items
            )
            print("Evaluación:", evaluation)
            return

        # Obtiene respuesta del diálogo
        reply, frase_objetivo, es_larga = self.dialog_manager.generate_response(text)

        # Guardamos frase objetivo si existe
        self.pending_target = frase_objetivo if frase_objetivo else None
        self.response_queue.put(reply)

    def _process_responses(self):
        """
        Hilo que reproduce las respuestas del asistente una a una.
        """
        while self.running:
            try:
                response = self.response_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if response:
                self._speak(response)

    def _speak(self, text):
        """
        Reproduce texto en voz.
        Permite interrumpir si el usuario empieza a hablar.
        """
        if self.speaking:
            return

        self.speaking = True
        # Pausar STT
        self.stt.pause()
        print(f"🤖 Asistente: {text}")
        self.tts.speak(text)
        # Reanudar STT
        self.stt.resume()
        self.speaking = False
