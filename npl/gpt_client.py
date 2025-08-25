# npl/gpt_client.py

from openai import OpenAI
from config import OPENAI_API_KEY

class GPTClient:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def chat_completion(self, system_prompt: str, user_prompt: str, model="gpt-4o-mini", temperature=0.0):
        """
        Envía un prompt al modelo y devuelve la respuesta en texto.
        """
        system = {"role": "system", "content": system_prompt}
        user = {"role": "user", "content": user_prompt}

        response = self.client.chat.completions.create(
            model=model,
            messages=[system, user],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
