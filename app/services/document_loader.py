from __future__ import annotations

from app.models.article_document import ArticleDocument
from app.services.language_detector import detect_language
from app.services.text_cleaner import clean_text
from app.services.metadata_detector import (
    detect_date_from_text,
    detect_source_from_text,
    detect_title_from_text,
)


def create_manual_document(
    text: str,
    title: str | None = None,
    source: str | None = None,
    publication_date: str | None = None,
) -> ArticleDocument:

    cleaned_text = clean_text(text)

    if len(cleaned_text) < 30:
        raise ValueError("Le texte est trop court. Ajoutez un article plus complet.")

    auto_title = title or detect_title_from_text(
        cleaned_text,
        fallback="Article saisi manuellement",
    )
    auto_source = source or detect_source_from_text(cleaned_text)
    auto_date = publication_date or detect_date_from_text(cleaned_text)

    return ArticleDocument(
        text=cleaned_text,
        input_type="manual",
        title=auto_title,
        source=auto_source,
        publication_date=auto_date,
        language=detect_language(cleaned_text),
    )
