import hashlib
import os
import re
from elevenlabs.client import ElevenLabs
from elevenlabs import play
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
    
    def normalize_text(self, text: str) -> str:
        # 1. Quitar espacios al inicio y final
        text = text.strip()
        # 2. Convertir saltos de línea y tabs a espacio
        text = re.sub(r"\s+", " ", text)
        # 3. Opcional: pasar todo a minúsculas si quieres unificar cache sin importar mayúsculas
        text = text.lower()
        return text

    def speak(self, text):
        if not text.strip():
            return
        normalized_text = self.normalize_text(text)
        cache_file = self._get_cache_path(normalized_text)
        # Si ya existe en caché, reproducimos directamente
        if os.path.exists(cache_file):
            print(f"Archivo en cache {cache_file}")
            try:
                print(f"🔊 Reproduciendo desde caché")
                play(self.open_audio(cache_file))
                return
            except Exception:
                print("⚠️ Error al reproducir desde caché, regenerando audio...")
        
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=normalized_text,
            model_id=self.model_id,
            output_format=self.output_format
        )
        # 2. Guardar a cache como bytes
        self.save_audio(cache_file, audio)
        
        # 3. Reproducir desde cache
        play(self.open_audio(cache_file))

    def save_audio(self, cache_file, audio):
        with open(cache_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)

    def open_audio(self, cache_file):
        with open(cache_file, "rb") as f:
            audio_bytes = f.read()
        return audio_bytes
