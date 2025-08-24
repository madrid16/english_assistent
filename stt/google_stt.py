import pyaudio
import queue
import time
from google.cloud import speech

class GoogleSTT:
    def __init__(self, silence_seconds=3, rate=16000, chunk=1024):
        """
        silence_seconds: tiempo máximo de silencio antes de cortar la grabación
        rate: frecuencia de muestreo (Hz)
        chunk: tamaño del buffer de audio
        """
        self.silence_seconds = silence_seconds
        self.rate = rate
        self.chunk = chunk

        self.client = speech.SpeechClient()
        self.audio_interface = pyaudio.PyAudio()
        self.audio_queue = queue.Queue()
        self.listening = False

    def _audio_callback(self, in_data, frame_count, time_info, status_flags):
        """Callback de PyAudio que envía audio al queue."""
        self.audio_queue.put(in_data)
        return None, pyaudio.paContinue

    def _stream_generator(self):
        """Generador que envía datos al API de Google."""
        while self.listening:
            data = self.audio_queue.get()
            if data is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=data)

    def listen_and_transcribe(self, language_code="en-US"):
        """
        Captura audio en tiempo real, detecta silencio y retorna la transcripción final.
        """
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code=language_code,
            enable_automatic_punctuation=True
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True  # Permite recibir resultados parciales
        )

        # Inicia captura de audio
        self.listening = True
        stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            stream_callback=self._audio_callback
        )

        requests = self._stream_generator()
        responses = self.client.streaming_recognize(streaming_config, requests)

        print("🎙️ Habla ahora (di 'salir' para terminar)...")

        final_text = ""
        last_speech_time = time.time()

        try:
            for response in responses:
                if not response.results:
                    continue

                result = response.results[0]
                transcript = result.alternatives[0].transcript.strip()

                if result.is_final:
                    print(f"📝 Final: {transcript}")
                    final_text += " " + transcript
                    last_speech_time = time.time()
                else:
                    print(f"... {transcript}", end="\r")
                    last_speech_time = time.time()

                # Detecta silencio prolongado
                if time.time() - last_speech_time > self.silence_seconds:
                    print("\n⏹️ Silencio detectado, finalizando...")
                    break

        finally:
            self.listening = False
            self.audio_queue.put(None)
            stream.stop_stream()
            stream.close()

        return final_text.strip()

    def close(self):
        """Cierra la interfaz de audio."""
        self.audio_interface.terminate()
