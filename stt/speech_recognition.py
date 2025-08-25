# stt/speech_recognition.py

import time
import sounddevice as sd
from google.cloud import speech
from google.api_core import exceptions as google_exceptions

class MicrophoneStream:
    """
    Context manager que abre el micrófono con sounddevice y genera chunks de audio en bytes.
    Los chunks respetan chunk_duration_ms (múltiplos de 10 ms recomendados por STT).
    """
    def __init__(self, rate=16000, chunk_duration_ms=100):
        self.rate = rate
        self.chunk_duration_ms = chunk_duration_ms
        self.chunk_size = int(rate * chunk_duration_ms / 1000)  # samples por chunk
        self.stream = None
        self._closed = True

    def __enter__(self):
        # RawInputStream devuelve frames en formato numpy int16; lo convertimos a bytes
        self.stream = sd.RawInputStream(
            samplerate=self.rate,
            blocksize=self.chunk_size,
            dtype='int16',
            channels=1
        )
        self.stream.start()
        self._closed = False
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
        finally:
            self._closed = True

    def generator(self):
        """
        Generador que devuelve bytes de audio (LINEAR16) continuamente.
        Esto mantiene la conexión "viva" y evita timeouts de la API.
        """
        try:
            while not self._closed:
                data, overflow = self.stream.read(self.chunk_size)
                # data es un ndarray (n,1) dtype=int16; convertir a bytes
                yield data.tobytes()
        except Exception:
            # Cuando el stream se cierra desde fuera, salimos limpiamente
            return


class SpeechRecognizer:
    """
    Wrapper de Google Speech-to-Text con resultados parciales y final.
    - start(callback) bloquea y procesa streaming; callback(final_text) se llama en resultados finales.
    - stop() detiene el reconocimiento.
    """
    def __init__(self, language_code="en-US", rate=16000, chunk_duration_ms=100):
        self.language_code = language_code
        self.rate = rate
        self.chunk_duration_ms = chunk_duration_ms
        self.chunk_size = int(rate * chunk_duration_ms / 1000)
        self.client = speech.SpeechClient()
        self._running = False

    def start(self, callback):
        """
        Inicia el streaming y procesa respuestas.
        callback(transcript) se ejecuta solo en resultados finales (is_final).
        Este método BLOQUEA hasta que se llame a stop() o ocurra una excepción no manejada.
        """
        self._running = True
        print("🎙️ SpeechRecognizer: iniciando captura de audio... (interim results ON)")

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code=self.language_code,
            max_alternatives=1,
            enable_word_time_offsets=False
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )

        # Mantener intentos de reconexión ante errores transitorios
        while self._running:
            try:
                with MicrophoneStream(rate=self.rate, chunk_duration_ms=self.chunk_duration_ms) as mic:
                    requests = (speech.StreamingRecognizeRequest(audio_content=chunk)
                                for chunk in mic.generator())

                    responses = self.client.streaming_recognize(config=streaming_config, requests=requests)
                    # Procesar respuestas (parciales y finales)
                    self._listen_print_loop(responses, callback)

            except google_exceptions.OutOfRange as e:
                # Error típico cuando la API cierra el stream por timeout. Lo mostramos y
                # reintentamos después de una pausa corta.
                print(f"\n⚠️ Google STT OutOfRange (timeout). Reintentando... ({e})")
                time.sleep(0.5)
                continue
            except google_exceptions.GoogleAPICallError as e:
                print(f"\n⚠️ Error API STT: {e}. Reintentando en 1s...")
                time.sleep(1.0)
                continue
            except Exception as e:
                print(f"\n❌ Error inesperado en SpeechRecognizer: {e}")
                # Si deseas que el servicio intente reconectar indefinidamente cambia 'break' por continue
                break

        print("🛑 SpeechRecognizer detenido.")

    def _listen_print_loop(self, responses, callback):
        """
        Itera sobre las respuestas devueltas por Google y muestra resultados parciales,
        y llama al callback cuando se confirma un resultado final.
        """
        try:
            for response in responses:
                if not response.results:
                    continue

                # Tomamos el primer resultado (más probable)
                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript.strip()

                if result.is_final:
                    # Imprimimos la línea final (borrando la línea parcial previa)
                    print("\r" + " " * 80, end="\r")
                    print(f"👤 Usuario (final): {transcript}")
                    try:
                        callback(transcript)
                    except Exception as cb_e:
                        print(f"⚠️ Error en callback: {cb_e}")
                else:
                    # Resultado parcial: imprimimos en la misma línea (sin newline)
                    print(f"\r👤 Usuario (hablando): {transcript}", end="", flush=True)
        except Exception as e:
            # Dejar que el loop exterior gestione reconexión si corresponde
            raise e

    def stop(self):
        """Marca para detener el while principal y cerrar canales en la siguiente iteración."""
        self._running = False
        # No hay que hacer mucho más: el contexto MicrophoneStream se cerrará y la función start terminará.
