# /db/firebase_service.py
from db.firebase_db import FirebaseDB
from datetime import datetime

db = FirebaseDB()

class FirebaseService:
    def __init__(self, users_collection: str = "users", sessions_collection: str = "sessions"):
        self.users_collection = users_collection
        self.sessions_collection = sessions_collection

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
        db.collection(self.users_collection).document(user_id).set(progress_data, merge=True)

        # Guarda la sesión individual en historial
        session_data = {
            "user_id": user_id,
            "transcript": texto_usuario,
            "ai_response": respuesta_asistente,
            "feedback": feedback,
            "target_phrases": frases_objetivo,
            "timestamp": datetime.utcnow()
        }
        db.collection(self.sessions_collection).add(session_data)

        return True

    def get_user_progress(self, user_id: str):
        """
        Obtiene el progreso actual del usuario.
        """
        doc = db.collection(self.users_collection).document(user_id).get()
        return doc.to_dict() if doc.exists else None

    def get_user_history(self, user_id: str, limit: int = 10):
        """
        Obtiene el historial más reciente del usuario.
        """
        sessions_ref = db.collection(self.sessions_collection)\
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
        db.collection(self.users_collection).document(user_id).delete()

        # Borra sesiones
        sessions = db.collection(self.sessions_collection).where("user_id", "==", user_id).stream()
        for s in sessions:
            db.collection(self.sessions_collection).document(s.id).delete()

        return True
