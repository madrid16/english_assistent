from google.cloud import texttospeech
import pyaudio
import wave
import os


class GoogleTTS:
    def __init__(self, language_code="en-US", voice_name=None, speaking_rate=1.0):
        """
        language_code: Código de idioma (ej: "en-US", "es-ES", "es-CL")
        voice_name: Nombre específico de la voz (opcional)
        speaking_rate: Velocidad de habla (1.0 = normal)
        """
        self.client = texttospeech.TextToSpeechClient()
        self.language_code = language_code
        self.voice_name = voice_name
        self.speaking_rate = speaking_rate

    def synthesize(self, text, output_file="output.wav"):
        """
        Convierte texto en voz, guarda en archivo WAV y lo retorna.
        """
        input_text = texttospeech.SynthesisInput(text=text)

        # Configuración de voz
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name or "",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Configuración de salida
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=self.speaking_rate
        )

        # Solicitud a la API de Google
        response = self.client.synthesize_speech(
            input=input_text,
            voice=voice_params,
            audio_config=audio_config
        )

        # Guardar archivo WAV
        with open(output_file, "wb") as out:
            out.write(response.audio_content)

        return output_file

    def play(self, file_path):
        """
        Reproduce un archivo WAV.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        wf = wave.open(file_path, 'rb')
        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)

        stream.stop_stream()
        stream.close()
        p.terminate()

    def speak(self, text):
        """
        Convierte texto en voz y lo reproduce directamente (sin guardar archivo permanente).
        """
        temp_file = "temp_tts.wav"
        self.synthesize(text, temp_file)
        self.play(temp_file)
        os.remove(temp_file)
