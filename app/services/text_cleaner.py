from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Nettoie le texte sans supprimer les caractères arabes."""

    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\ufeff", " ")
    text = text.replace("\u200f", "")
    text = text.replace("\u200e", "")

    # Réunir les mots coupés en fin de ligne dans les PDF.
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Normaliser les retours à la ligne.
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Nettoyer les espaces autour des signes de ponctuation.
    text = re.sub(r" +([,.;:!?%])", r"\1", text)

    return text.strip()


def count_words(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\b[\w\u0600-\u06FF]+\b", text, flags=re.UNICODE))
