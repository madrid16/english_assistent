import pyaudio
import wave
import numpy as np

class AudioUtils:
    def __init__(self, rate=16000, chunk=1024, channels=1, format=pyaudio.paInt16):
        """
        rate: Frecuencia de muestreo (16000 recomendado para STT)
        chunk: Tamaño del buffer de audio en frames
        channels: Número de canales (1 = mono)
        format: Formato de audio (paInt16 = PCM 16-bit)
        """
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.format = format
        self.audio_interface = pyaudio.PyAudio()

    def start_stream(self, input_device_index=None, callback=None):
        """
        Inicia un stream de audio desde el micrófono.
        callback: función que procesa los frames de audio en tiempo real.
        """
        return self.audio_interface.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            input_device_index=input_device_index,
            stream_callback=callback
        )

    def stop_stream(self, stream):
        """
        Detiene y cierra el stream de audio.
        """
        if stream.is_active():
            stream.stop_stream()
        stream.close()

    def save_wav(self, filename, audio_frames):
        """
        Guarda audio capturado en formato WAV.
        """
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio_interface.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(audio_frames))

    def pcm_to_numpy(self, pcm_data):
        """
        Convierte datos PCM a array NumPy.
        """
        return np.frombuffer(pcm_data, dtype=np.int16)

    def numpy_to_pcm(self, numpy_array):
        """
        Convierte un array NumPy a bytes PCM.
        """
        return numpy_array.astype(np.int16).tobytes()

    def terminate(self):
        """
        Libera recursos de PyAudio.
        """
        self.audio_interface.terminate()
