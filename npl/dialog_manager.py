import openai
from config import OPENAI_API_KEY

class DialogManager:
    def __init__(self, model="gpt-4o", language="en"):
        """
        model: Modelo de OpenAI a utilizar (gpt-4o, gpt-4o-mini, gpt-5, etc.)
        language: Idioma principal de la conversación
        """
        openai.api_key = OPENAI_API_KEY
        self.model = model
        self.language = language
        self.context = []

    def generate_response(self, user_input):
        """
        Genera una respuesta en función del input del usuario manteniendo el contexto.
        """
        self.context.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "system", "content": f"You are a friendly AI tutor helping the user practice {self.language}."}] + self.context,
            temperature=0.7
        )

        reply = response["choices"][0]["message"]["content"]
        self.context.append({"role": "assistant", "content": reply})

        return reply

    def get_target_phrases(self, user_input, num_phrases=3):
        """
        Extrae frases cortas del contexto para practicar pronunciación.
        """
        prompt = f"""
        Extrae {num_phrases} frases clave en {self.language} del siguiente texto para que el usuario las practique:
        Texto: "{user_input}"
        Responde solo con una lista, sin explicación.
        """

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "system", "content": "You are a language tutor."},
                      {"role": "user", "content": prompt}]
        )

        phrases = response["choices"][0]["message"]["content"].strip().split("\n")
        phrases = [p.strip("-• ") for p in phrases if p.strip()]

        return phrases[:num_phrases]
