from elevenlabs.client import ElevenLabs
from elevenlabs import play
from elevenlabs import save as save_audio
from config import ELEVEN_API_KEY

class ElevenLabsTTS:
    def __init__(self, voice_id="XrExE9yKIg1WjnnlVkGX", model_id="eleven_multilingual_v2", output_format="mp3_44100_128"):
        self.client = ElevenLabs(api_key=ELEVEN_API_KEY)
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_format = output_format

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
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format=self.output_format
        )
        # Reproducir directamente
        from elevenlabs import play
        play(audio)

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
