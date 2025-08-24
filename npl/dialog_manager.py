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
        Devuelve: respuesta del asistente, frase objetivo, y si la respuesta es larga.
        """
        print("🤖 Generando respuesta...")

        keywords_expansion = ["explica", "explícame", "detallado", "dame un ejemplo", "más detalle", "más largo"]
        breve = not any(kw in user_input.lower() for kw in keywords_expansion)

        if breve:
            system_prompt = (
                f"Eres un asistente de inglés. Da respuestas claras y breves (máx. 40 palabras). "
                f"Usa vocabulario adecuado al nivel A2-B1. "
                f"Además, siempre proporciona una frase corta en inglés para que el usuario practique pronunciación. "
                f"Responde en JSON con dos claves: 'reply' y 'frase_objetivo'."
            )
        else:
            system_prompt = (
                f"Eres un asistente de inglés que da explicaciones completas, con ejemplos y correcciones detalladas "
                f"cuando el usuario pide más información. "
                f"Además, siempre proporciona una frase corta en inglés para que el usuario practique pronunciación. "
                f"Responde en JSON con dos claves: 'reply' y 'frase_objetivo'."
            )

        self.context.append({"role": "user", "content": user_input})

        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}] + self.context,
            temperature=0.7
        )

        raw_reply = response.choices[0].message.content.strip()

        # Intentamos parsear JSON
        import json
        try:
            data = json.loads(raw_reply)
            reply = data.get("reply", "").strip()
            frase_objetivo = data.get("frase_objetivo", "").strip()
        except Exception:
            # fallback si el modelo no devuelve JSON válido
            reply = raw_reply
            frase_objetivo = reply.split(".")[0]  # tomar primera frase como target

        # Chequeo de longitud
        word_count = len(reply.split())
        es_larga = word_count > 50

        self.context.append({"role": "assistant", "content": reply})

        print(f"🤖 Asistente: {reply} (palabras: {word_count})")
        print(f"🎯 Frase objetivo: {frase_objetivo}")

        return reply, frase_objetivo, es_larga


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
