# services/initial_test/listening_service.py
import random
import time
from npl.listening_test import ListeningTest  # si ya tienes la clase ListeningTest
from queue import Queue, Empty

class ListeningService:
    def __init__(self, firestore, tts, stt, gpt_client, num_questions=8):
        """
        firestore: instancia de FirebaseDB o servicio equivalente
        tts: instancia de VoiceAssistant TTS
        stt: instancia de SpeechRecognizer
        gpt_client: cliente GPT para evaluar respuestas
        num_questions: cuántas frases se usan por test
        """
        self.firestore = firestore
        self.tts = tts
        self.stt = stt
        self.gpt = gpt_client
        self.num_questions = num_questions
        self.listening_test = ListeningTest(tts=self.tts, stt=self.stt, firestore=self.firestore)

    def start_listening_test(self, user_id):
        """
        Ejecuta el test inicial de listening:
        1. Selecciona frases aleatorias
        2. Reproduce la frase
        3. Captura la respuesta del alumno
        4. Evalúa con GPT
        5. Retorna evaluación y resultados
        """
        phrases = self.firestore.get_listening_phrases(8)
        print(f"Seleccionadas {len(phrases)} frases para listening.")

        # Preparar items para ListeningTest
        listening_items = []
        for idx, phrase in enumerate(phrases, start=1):
            item = {
                "id": idx,
                "text_audio": phrase,  # frase que se va a reproducir
                "questions": [
                    {
                        "q": f"Please repeat the sentence: '{phrase}'",
                        "expected": [phrase]
                    },
                    {
                        "q": f"What does the sentence mean? (try to answer in English or Spanish)",
                        "expected": []  # opcional, GPT puede evaluar
                    }
                ]
            }
            listening_items.append(item)

        # Ejecutar la prueba usando ListeningTest
        evaluation = self.listening_test.run_test(
            user_id=user_id,
            listening_items=listening_items
        )

        return evaluation
