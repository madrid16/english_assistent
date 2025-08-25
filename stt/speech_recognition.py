import queue
import threading
import sounddevice as sd
from google.cloud import speech

class SpeechRecognizer:
    """
    Reconocimiento de voz en streaming usando Google Speech-to-Text.
    Usa sounddevice para capturar audio y soporta resultados intermedios.
    """

    def __init__(self, language_code="en-US", rate=16000, chunk_duration_ms=100):
        self.language_code = language_code
        self.rate = rate
        self.chunk_size = int(rate * chunk_duration_ms / 1000)
        self.client = speech.SpeechClient()

        self.audio_queue = queue.Queue()
        self.running = False
        self.callback = None

    def start(self, callback):
        """Inicia captura de audio y reconocimiento en streaming."""
        self.callback = callback
        self.running = True

        threading.Thread(target=self._capture_audio).start()
        threading.Thread(target=self._streaming_recognition).start()
        print("🎙️ SpeechRecognizer: iniciando captura de audio... (interim results ON)")

    def stop(self):
        """Detiene la captura y el streaming."""
        self.running = False
        self.audio_queue.put(None)

    def _capture_audio(self):
        """Captura audio del micrófono con sounddevice y lo pone en la cola."""

        def callback(indata, frames, time, status):
            if not self.running:
                raise sd.CallbackStop()
            self.audio_queue.put(indata.tobytes())

        with sd.InputStream(channels=1, samplerate=self.rate, callback=callback,
                            blocksize=self.chunk_size, dtype='int16'):
            while self.running:
                sd.sleep(100)  # Bloqueo activo


    def _audio_generator(self):
        """Generador que produce chunks de audio para Google STT."""
        while self.running:
            chunk = self.audio_queue.get()
            if chunk is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    def _streaming_recognition(self):
        """Envia audio a Google STT y procesa resultados intermedios y finales."""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code=self.language_code,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )

        requests = self._audio_generator()
        responses = self.client.streaming_recognize(streaming_config, requests)

        try:
            for response in responses:
                if not response.results:
                    continue

                result = response.results[0]
                transcript = result.alternatives[0].transcript.strip()

                if result.is_final:
                    print(f"\n✅ Usuario (final): {transcript}")
                    if self.callback:
                        self.callback(transcript)
                else:
                    print(f"\r📝 Usuario (hablando): {transcript}", end="")
        except Exception as e:
            if self.running:
                print(f"\n⚠️ Error en streaming STT: {e}")
