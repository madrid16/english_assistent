import pyaudio
import queue
import webrtcvad
import collections
import sys
import time
import threading
from google.cloud import speech

class SpeechRecognizer:
    def __init__(self, language_code="en-ES", vad_aggressiveness=2):
        self.language_code = language_code
        self.client = speech.SpeechClient()

        # Audio config
        self.rate = 16000
        self.channels = 1
        self.chunk_duration_ms = 30
        self.chunk_size = int(self.rate * self.chunk_duration_ms / 1000)
        self.buffer = queue.Queue()

        # VAD config
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.frames = collections.deque(maxlen=10)

        # PyAudio
        self.audio_interface = pyaudio.PyAudio()
        self.stream = None

        self.running = False

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self.buffer.put(in_data)
        return None, pyaudio.paContinue

    def start(self, callback):
        """Inicia la captura de audio y procesa con VAD + Google STT"""
        self.running = True

        self.stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._fill_buffer,
        )

        self.stream.start_stream()

        print("🎙️ Asistente escuchando. Di 'salir' para terminar.")

        audio_generator = self._audio_generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code=self.language_code,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        responses = self.client.streaming_recognize(
            config=streaming_config, requests=requests
        )

        self._listen_print_loop(responses, callback)

    def _audio_generator(self):
        while self.running:
            chunk = self.buffer.get()
            if chunk is None:
                return
            is_speech = self.vad.is_speech(chunk, self.rate)
            if is_speech:
                yield chunk

    def _listen_print_loop(self, responses, callback):
        """Recibe transcripciones de Google y llama al callback cuando hay texto final"""
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if result.is_final:
                transcript = result.alternatives[0].transcript.strip()
                callback(transcript)

    def stop(self):
        """Detiene captura de audio"""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio_interface.terminate()
        print("🛑 Asistente detenido.")
