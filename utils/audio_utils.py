import numpy as np
import queue
import sounddevice as sd
import wave

class AudioUtils:
    def __init__(self, rate=16000, chunk=1024, channels=1):
        """
        rate: Frecuencia de muestreo (16000 recomendado para STT)
        chunk: Tamaño del buffer de audio en frames
        channels: Número de canales (1 = mono)
        format: Formato de audio (paInt16 = PCM 16-bit)
        """
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.q = queue.Queue()

    def _callback(self, indata, frames, time, status):
        """Callback de sounddevice que guarda el audio en la cola"""
        if status:
            print(f"⚠️ Status de audio: {status}")
        self.q.put(indata.copy())

    def start_recording(self):
        """Inicia grabación en segundo plano con callback"""
        self.stream = sd.InputStream(
            samplerate=self.rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.chunk,
            callback=self._callback
        )
        self.stream.start()
        print("🎙️ Grabación iniciada...")

    def stop_recording(self):
        """Detiene la grabación"""
        if hasattr(self, "stream"):
            self.stream.stop()
            self.stream.close()
            print("🛑 Grabación detenida")

    def get_audio_chunk(self):
        """Obtiene el siguiente bloque de audio desde la cola"""
        try:
            data = self.q.get(timeout=1)
            return data.flatten()  # numpy array
        except queue.Empty:
            return None

    def record_seconds(self, seconds=3):
        """Graba un audio corto y lo devuelve como array numpy"""
        print(f"🎤 Grabando {seconds} segundos...")
        recording = sd.rec(int(seconds * self.rate), samplerate=self.rate,
                           channels=self.channels, dtype="int16")
        sd.wait()
        return recording.flatten()

    def save_wav(self, filename, audio_data):
        """Guarda un numpy array en archivo WAV"""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(self.rate)
            wf.writeframes(audio_data.tobytes())
        print(f"💾 Audio guardado en {filename}")

    def detect_silence(self, audio_chunk, threshold=500):
        """Detecta si un bloque es silencio según RMS"""
        rms = np.sqrt(np.mean(np.square(audio_chunk.astype(np.float32))))
        return rms < threshold