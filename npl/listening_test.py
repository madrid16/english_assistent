# npl/listening_test.py
import time
import json
import openai
import random
import re
from config import OPENAI_API_KEY


# ------------------------------
# Prompt template para evaluación (C)
# ------------------------------
EVAL_SYSTEM_PROMPT = """
Eres un profesor de inglés que evalúa respuestas de comprensión oral (listening).
Recibirás una lista de ítems. Para cada ítem tendrás:
- id: identificador del ítem
- audio_text: el texto original del audio (para contexto)
- question: la pregunta que se hizo al alumno
- expected: lista de respuestas aceptables (palabras clave o frases)
- student_answer: la transcripción que dio el alumno (texto)

Devuelve UN ÚNICO JSON con la siguiente estructura exacta:
{
"items": [
    {
    "id": "L1",
    "question": "...",
    "expected": ["..."],
    "student_answer": "...",
    "score": 0.0,        // 0.0, 0.5, 1.0
    "feedback": "frase breve en inglés o español"
    },
    ...
],
"total_score": number,
"max_score": number,
"percentage": number,   // 0..100
"estimated_level": "A1|A2|B1|B2|C1|C2",
"recommendation": "Breve plan de siguientes pasos (3-4 bullets)"
}

CRITERIOS:
- Para preguntas factuales (short_answer): exact match (ignorando mayúsculas/puntuación) => 1.0.
Respuesta parcialmente correcta (falta detalle o palabra clave) => 0.5.
Incorrecta o vacía => 0.0.
- Sé conciso en feedback (máx 2 frases).
- Calcula total_score, max_score (1 por pregunta), percentage y asigna estimated_level según %:
0-30% -> A1, 31-50% -> A2, 51-70% -> B1-, 71-85% -> B1, 86-95% -> B2, 96-100% -> C1-C2.
"""

class ListeningTest:
    def __init__(self, tts, stt, firestore):
        """
        gpt_client: instancia para comunicarse con GPT
        tts: instancia para text-to-speech (Ej: ElevenLabs)
        recognizer: instancia para reconocimiento de voz
        """
        openai.api_key = OPENAI_API_KEY
        self.gpt = openai
        self.tts = tts
        self.stt = stt
        self.recognizer = stt
        self.last_transcript = ""
        self.result = None
        self.firestore = firestore

    # -----------------------------
    # Métodos públicos
    # -----------------------------
    def run_test(self, listening_items: list):
        results = []
        for item in listening_items:
            sentence = item.get("text_audio", "")
            if not sentence:
                continue
            # 1️⃣ Dar instrucciones
            instructions = f"Listen carefully and repeat the following sentence: '{sentence}'"
            print("📢 Instrucciones (Listening):", instructions)
            self.tts.speak(instructions)

            # 2️⃣ Capturar la respuesta del usuario
            print("🎤 Tu turno...")
            user_response = self.wait_for_final_transcript_once()
            print("✅ Usuario (final):", user_response)

            # 3️⃣ Evaluar con GPT
            prompt = (
                f"{EVAL_SYSTEM_PROMPT}\nFrase objetivo: '{sentence}'\n"
                f"Respuesta del usuario: '{user_response}'"
            )
            evaluation_json = self.generate_response(prompt)
            feedback, score = self.clean_json_block(evaluation_json)

            result = {"sentence": sentence, "user_response": user_response, "feedback": feedback, "score": score}
            results.append(result)
            print("📝 Evaluación Listening:", result)

        self.result = results
        return self.result

    
    def generate_response(self, prompt):
        # Ajusta aquí la llamada según tu cliente (OpenAI/Responses/Chat completions)
        system = {"role": "system", "content": EVAL_SYSTEM_PROMPT}
        user = {"role": "user", "content": prompt}
        response = self.gpt.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system, user],
            temperature=0.0
        )
        return response

    # -----------------------------
    # Métodos internos
    # -----------------------------
    def wait_for_final_transcript_once(self, timeout=30):
        """
        Espera un único transcript final del recognizer (modo bloqueante)
        """
        start_time = time.time()
        self.last_transcript = ""
        while True:
            if time.time() - start_time > timeout:
                break
            transcript = self.recognizer.get_final_transcript()  # debe devolver texto
            if transcript and transcript != self.last_transcript:
                self.last_transcript = transcript
                break
            time.sleep(0.1)
        return self.last_transcript

    def clean_json_block(self, raw_text):
        """
        Recibe un bloque de texto que debería ser JSON y devuelve feedback y score
        """
        try:
            # Extrae bloque JSON de cualquier texto
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                feedback = data.get("feedback", "")
                score = data.get("score", 0)
                return feedback, score
        except Exception as e:
            print("⚠️ Error al parsear JSON:", e)
        # fallback
        return raw_text, 0

# -----------------------------
# Ejemplo de prueba
# -----------------------------
if __name__ == "__main__":
    # Dummy clients para prueba
    class DummyGPT:
        def generate_response(self, prompt):
            # Simula respuesta JSON
            return '{"feedback": "Buen trabajo, solo mejora la entonación.", "score": 85}'

    class DummyTTS:
        def speak(self, text):
            print(f"(TTS): {text}")

    class DummyRecognizer:
        def get_final_transcript(self):
            return "The weather is nice today"

    test = ListeningTest(DummyGPT(), DummyTTS(), DummyRecognizer())
    test.start_test("The weather is nice today")