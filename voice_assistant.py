import threading
import queue

from stt.speech_recognition import SpeechRecognizer
from tts.eleven_tts import ElevenLabsTTS
from npl.dialog_manager import DialogManager


class VoiceAssistant:
    def __init__(self, language_code="en-US", vad_aggressiveness=2, keywords_expansion=False):
        self.language_code = language_code
        self.keywords_expansion = keywords_expansion

        # Inicializa componentes
        self.stt = SpeechRecognizer(language_code="en-US", rate=16000, chunk_duration_ms=100)
        self.tts = ElevenLabsTTS()
        self.dialog_manager = DialogManager()

        # Control de ejecución
        self.response_queue = queue.Queue()
        self.speaking = False
        self.running = False

    def start(self):
        """Inicia el asistente de voz"""
        print("🔊 Iniciando asistente de voz...")
        self.running = True

        # Hilo para procesar respuestas y hablar
        threading.Thread(target=self._process_responses, daemon=True).start()

        # Inicia reconocimiento de voz
        self.stt.start(callback=self.on_user_speech)

    def stop(self):
        """Detiene el asistente"""
        self.running = False
        self.stt.stop()
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

        # Obtiene respuesta del diálogo
        response = self.dialog_manager.generate_response(text)
        self.response_queue.put(response)

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
        print(f"🤖 Asistente: {text}")
        self.tts.speak(text)
        self.speaking = False
