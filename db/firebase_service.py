# /db/firebase_service.py
import json
import re
import time
from datetime import datetime
from npl.listening_test import EVAL_SYSTEM_PROMPT


class FirebaseService:
    def __init__(self, db_client, gpt_client, users_collection: str = "users", sessions_collection: str = "sessions"):
        self.users_collection = users_collection
        self.sessions_collection = sessions_collection
        self.db = db_client
        self.gpt = gpt_client

    def save_user_progress(self, user_id: str, texto_usuario: str, respuesta_asistente: str,
                           frases_objetivo: list, feedback: dict):
        """
        Guarda el progreso general del usuario y registra la interacción en historial.
        """
        progress_data = {
            "last_input": texto_usuario,
            "last_response": respuesta_asistente,
            "target_phrases": frases_objetivo,
            "feedback": feedback,
            "last_update": datetime.utcnow()
        }

        # Actualiza progreso general del usuario
        self.db.collection(self.users_collection).document(user_id).set(progress_data, merge=True)

        # Guarda la sesión individual en historial
        session_data = {
            "user_id": user_id,
            "transcript": texto_usuario,
            "ai_response": respuesta_asistente,
            "feedback": feedback,
            "target_phrases": frases_objetivo,
            "timestamp": datetime.utcnow()
        }
        self.db.collection(self.sessions_collection).add(session_data)

        return True

    def get_user_progress(self, user_id: str):
        """
        Obtiene el progreso actual del usuario.
        """
        doc = self.db.collection(self.users_collection).document(user_id).get()
        return doc.to_dict() if doc.exists else None

    def get_user_history(self, user_id: str, limit: int = 10):
        """
        Obtiene el historial más reciente del usuario.
        """
        sessions_ref = self.db.collection(self.sessions_collection)\
                         .where("user_id", "==", user_id)\
                         .order_by("timestamp", direction="DESCENDING")\
                         .limit(limit)
        results = sessions_ref.stream()
        return [s.to_dict() for s in results]

    def delete_user_data(self, user_id: str):
        """
        Elimina todo el progreso e historial del usuario.
        """
        # Borra progreso general
        self.db.collection(self.users_collection).document(user_id).delete()

        # Borra sesiones
        sessions = self.db.collection(self.sessions_collection).where("user_id", "==", user_id).stream()
        for s in sessions:
            self.db.collection(self.sessions_collection).document(s.id).delete()

        return True

    def initialize_global_listening_phrases(self, num_phrases=80):
        """
        Genera un abanico de frases para el test de listening y lo guarda en Firestore.
        Solo se ejecuta una vez.
        """
        # Verificar si ya existe
        doc_ref = self.db.collection("global_listening_phrases").document("default")
        if doc_ref.get().exists:
            print("✅ Las frases de listening global ya están inicializadas.")
            return

        # Generar prompt para GPT
        prompt = (
            f"Genera {num_phrases} frases cortas en inglés para practicar listening, "
            "niveles A1-B1, con vocabulario y estructuras variadas, "
            "sin traducción. Devuelve solo un JSON con campo 'phrases', "
            "lista de objetos con 'id' y 'text'. Ejemplo: "
            '{"phrases":[{"id":1,"text":"Hello, how are you?"},...]}'
        )

        # Llamada a GPT
        raw = self.gpt.chat_completion(system_prompt=EVAL_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.0)

        # Limpiar JSON de posibles ```json ``` y parsear
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        try:
            data = json.loads(raw)
            phrases = data.get("phrases", [])
        except Exception as e:
            print("❌ Error parseando JSON de GPT:", e)
            return

        # Guardar en Firestore
        doc_ref.set({
            "phrases": phrases,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        print(f"✅ Frases de listening inicializadas: {len(phrases)} frases.")

