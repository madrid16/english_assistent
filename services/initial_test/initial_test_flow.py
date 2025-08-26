class InitialTestFlow:
    def __init__(self, firestore_db, gpt_client):
        self.firestore = firestore_db
        self.gpt = gpt_client

    def show_welcome(self):
        """
        Muestra la bienvenida del test inicial.
        Podría ser texto plano, HTML (para web) o JSON (para apps).
        """
        return (
            "¡Bienvenido/a al Test Inicial de Inglés!"
            "Este test nos ayudará a conocer tu nivel de inglés para diseñar un plan "
            "de aprendizaje personalizado.\n\n"
            "¿Qué incluye?\n"
            "- Listening: Escucharás y responderás algunas frases.\n"
            "- Reading: Leerás textos cortos y contestarás preguntas.\n"
            "- Speaking: Repetirás algunas frases para evaluar tu pronunciación.\n\n"
            "Importante: No hay respuestas correctas o incorrectas.\n"
            "Duración aproximada: 10-15 minutos."
        )
