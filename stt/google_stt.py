import numpy as np
import queue
from google.cloud import speech
import sounddevice as sd
from utils.audio_utils import AudioUtils
from utils.shared_queue import audio_queue  # en lugar de declararlo aquí

class GoogleSTT:
    def __init__(self, rate=16000, chunk=1024, channels=1, language_code="en-ES"):
        """
        silence_seconds: tiempo máximo de silencio antes de cortar la grabación
        rate: frecuencia de muestreo (Hz)
        chunk: tamaño del buffer de audio
        """
        self.language_code = language_code
        self.rate = rate
        self.chunk = chunk
        self.channels = channels

        # Cliente de Google STT
        self.client = speech.SpeechClient()

        # Utilidad de audio (sounddevice)
        self.audio_utils = AudioUtils(rate=rate, chunk=chunk, channels=channels)

        # Cola de audio para enviar a Google
        self.requests = queue.Queue()

    def _generator(self):
        """Generador que envía audio a la API de Google"""
        while True:
            chunk = self.audio_utils.get_audio_chunk()
            if chunk is None:
                continue

            # Asegurar tipo bytes (Google espera PCM lineal 16-bit)
            audio_content = chunk.astype(np.int16).tobytes()
            yield speech.StreamingRecognizeRequest(audio_content=audio_content)

    def listen_and_transcribe(self, on_transcription_update=None):
        """
        Captura audio en streaming y transcribe con Google STT.
        on_transcription_update: callback para texto parcial/final.
        """
        # Configuración de reconocimiento
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code=self.language_code,
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )

        # Iniciar captura de audio
        self.audio_utils.start_recording()

        # Llamada en streaming a Google
        responses = self.client.streaming_recognize(
            config=streaming_config,
            requests=self._generator()
        )

        try:
            for response in responses:
                if not response.results:
                    continue

                result = response.results[0]
                transcript = result.alternatives[0].transcript

                if on_transcription_update:
                    on_transcription_update(transcript, result.is_final)

                if result.is_final:
                    print(f"✅ Final: {transcript}")
                else:
                    print(f"⏳ Parcial: {transcript}")

        except Exception as e:
            print(f"❌ Error en STT: {e}")
        finally:
            self.audio_utils.stop_recording()

    def start_streaming(self, on_update=None, on_final=None, single_utterance=False):
        self._running = True

        stream_config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.rate,
                language_code=self.language_code,
            ),
            interim_results=True,
            single_utterance=single_utterance,
        )

        def request_generator():
            while self._running:
                try:
                    data = audio_queue.get(timeout=1)
                except queue.Empty:
                    continue

                if data is None:  # señal de stop
                    break

                yield speech.StreamingRecognizeRequest(audio_content=data)

        try:
            # 👇 Aquí pasamos stream_config como primer parámetro obligatorio
            responses = self.client.streaming_recognize(stream_config, request_generator())
            for response in responses:
                if not self._running:
                    break
                for result in response.results:
                    if not result.alternatives:
                        continue
                    transcript = result.alternatives[0].transcript
                    if result.is_final:
                        if on_final:
                            on_final(transcript)
                        if single_utterance:
                            self._running = False
                            break
                    else:
                        if on_update:
                            on_update(transcript)
        finally:
            self._running = False
    

    def stop_streaming(self):
        """Detiene el bucle de start_streaming()."""
        self._running = False
