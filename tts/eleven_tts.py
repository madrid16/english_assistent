import os
import hashlib
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from elevenlabs import save as save_audio
from config import ELEVEN_API_KEY

CACHE_DIR = "tts_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class ElevenLabsTTS:
    def __init__(self, voice_id="XrExE9yKIg1WjnnlVkGX", model_id="eleven_multilingual_v2", output_format="mp3_44100_128"):
        self.client = ElevenLabs(api_key=ELEVEN_API_KEY)
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_format = output_format

    def _get_cache_path(self, text):
        """Genera un nombre de archivo único para cada texto"""
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        return os.path.join(CACHE_DIR, f"{h}.mp3")

    def synthesize_to_file(self, text, output_file="tts_out.mp3"):
        response = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format=self.output_format
        )
        with open(output_file, "wb") as f:
            for chunk in response:
                f.write(chunk)
        return output_file

    def speak(self, text):
        if not text.strip():
            return
        
        cache_file = self._get_cache_path(text)
        # Si ya existe en caché, reproducimos directamente
        if os.path.exists(cache_file):
            print(f"Archivo en cache {cache_file}")
            try:
                print(f"🔊 Reproduciendo desde caché: {text}")
                with open(cache_file, "rb") as f:
                    audio_bytes = f.read()
                play(audio_bytes)
                return
            except Exception:
                print("⚠️ Error al reproducir desde caché, regenerando audio...")
        
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format=self.output_format
        )
        play(audio)
        # Guardar audio en caché
        with open(cache_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        # Reproducir directamente

    def save(self, text, filename):
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format=self.output_format
        )
        with open(filename, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return filename
