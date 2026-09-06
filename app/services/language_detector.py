from __future__ import annotations

import re
try:
    from langdetect import detect, DetectorFactory, LangDetectException
    DetectorFactory.seed = 42
except Exception:
    detect = None
    class LangDetectException(Exception):
        pass

SUPPORTED_LANGUAGES = {
    "fr": "Français",
    "ar": "Arabe",
    "en": "Anglais",
}


def contains_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def detect_language(text: str) -> str:
    """
    Détecte fr/ar/en.
    Retourne 'unknown' si la langue n'est pas fiable ou non prise en charge.
    """

    text = (text or "").strip()

    if len(text) < 20:
        return "unknown"

    # L'arabe est détecté directement pour éviter certaines erreurs de langdetect.
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    alpha_chars = len(re.findall(r"[A-Za-zÀ-ÿ\u0600-\u06FF]", text))

    if alpha_chars and arabic_chars / alpha_chars > 0.25:
        return "ar"

    if detect is None:
        low = text.lower()
        if re.search(r"\b(?:the|and|of|with|for|was|were)\b", low): return "en"
        if re.search(r"\b(?:le|la|les|des|de|du|en|avec|pour|est|sont)\b", low): return "fr"
        return "unknown"
    try:
        language = detect(text[:5000])
    except LangDetectException:
        return "unknown"

    return language if language in SUPPORTED_LANGUAGES else "unknown"


def language_label(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, "Inconnue")
