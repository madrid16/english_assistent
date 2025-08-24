import difflib

class PronunciationEvaluator:
    def __init__(self, threshold=0.75):
        """
        threshold: nivel mínimo de similitud para considerar correcta la pronunciación (0-1).
        """
        self.threshold = threshold

    def evaluate(self, target_phrase, user_speech):
        """
        Compara la frase objetivo con lo que dijo el usuario usando similitud de strings.
        Retorna puntaje (0-100) y feedback.
        """
        target_clean = target_phrase.lower().strip()
        user_clean = user_speech.lower().strip()

        similarity = difflib.SequenceMatcher(None, target_clean, user_clean).ratio()
        score = round(similarity * 100)

        if similarity >= self.threshold:
            feedback = f"¡Bien! Pronunciaste '{target_phrase}' bastante bien. (Puntaje: {score}%)"
        else:
            feedback = f"Necesitas mejorar: dijiste '{user_speech}' en lugar de '{target_phrase}'. (Puntaje: {score}%)"

        return score, feedback

    def batch_evaluate(self, target_phrases, user_speeches):
        """
        Evalúa varias frases al mismo tiempo.
        Retorna lista de (frase, puntaje, feedback).
        """
        results = []
        for target, user in zip(target_phrases, user_speeches):
            score, feedback = self.evaluate(target, user)
            results.append((target, score, feedback))
        return results
