from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd


@dataclass
class DetectedSchema:
    text_column: str
    title_column: str | None = None
    source_column: str | None = None
    date_column: str | None = None
    country_column: str | None = None
    url_column: str | None = None
    id_column: str | None = None
    confidence: float = 0.0


TEXT_NAMES = {
    "text", "article", "content", "body", "description", "texte",
    "contenu", "article_text", "article_content", "news", "story",
    "النص", "المقال", "المحتوى"
}

TITLE_NAMES = {
    "title", "headline", "subject", "titre", "nom", "article_title",
    "العنوان", "عنوان"
}

SOURCE_NAMES = {
    "source", "publisher", "media", "website", "site", "domain",
    "journal", "newspaper", "origine", "المصدر"
}

COUNTRY_NAMES = {"country", "pays", "nation", "geography", "geo", "geographie", "géographie", "الدولة", "البلد"}
URL_NAMES = {"url", "link", "lien", "source_url", "article_url", "web_url"}
ID_NAMES = {"id", "document_id", "article_id", "doc_id", "identifiant", "uid", "uuid"}

DATE_NAMES = {
    "date", "publication_date", "published_at", "created_at",
    "datetime", "time", "publication", "jour", "التاريخ"
}


def _normalize_name(name: str) -> str:
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9_\u0600-\u06FF]+", "_", name)
    return name.strip("_")


def _text_score(series: pd.Series, column_name: str) -> float:
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return -1.0

    normalized = _normalize_name(column_name)
    name_bonus = 3.0 if normalized in TEXT_NAMES else 0.0

    avg_len = non_null.str.len().mean()
    long_ratio = (non_null.str.len() >= 120).mean()
    sentence_ratio = non_null.str.contains(r"[.!?؟]", regex=True).mean()
    unique_ratio = non_null.nunique() / max(len(non_null), 1)

    return (
        name_bonus
        + min(avg_len / 500.0, 2.5)
        + long_ratio * 3.0
        + sentence_ratio * 1.5
        + unique_ratio * 0.5
    )


def _name_match(columns: list[str], candidates: set[str]) -> str | None:
    normalized_map = {_normalize_name(col): col for col in columns}

    for candidate in candidates:
        if candidate in normalized_map:
            return normalized_map[candidate]

    for normalized, original in normalized_map.items():
        if any(candidate in normalized for candidate in candidates):
            return original

    return None


def _detect_date_column(df: pd.DataFrame, columns: list[str]) -> str | None:
    named = _name_match(columns, DATE_NAMES)
    if named:
        return named

    best_column = None
    best_ratio = 0.0

    for column in columns:
        series = df[column].dropna()
        if series.empty:
            continue

        parsed = pd.to_datetime(
            series.astype(str).head(100),
            errors="coerce",
            dayfirst=True,
            format="mixed",
        )
        ratio = parsed.notna().mean()

        if ratio > best_ratio and ratio >= 0.65:
            best_ratio = ratio
            best_column = column

    return best_column


def detect_csv_schema(df: pd.DataFrame) -> DetectedSchema:
    if df.empty or not len(df.columns):
        raise ValueError("Le fichier CSV est vide.")

    columns = list(df.columns)

    scored = [
        (column, _text_score(df[column], column))
        for column in columns
    ]
    scored.sort(key=lambda item: item[1], reverse=True)

    text_column, text_score = scored[0]

    if text_score < 1.0:
        raise ValueError(
            "Aucune colonne contenant clairement des articles n'a été détectée."
        )

    title_column = _name_match(
        [c for c in columns if c != text_column],
        TITLE_NAMES,
    )
    source_column = _name_match(
        [c for c in columns if c != text_column],
        SOURCE_NAMES,
    )
    date_column = _detect_date_column(
        df,
        [c for c in columns if c != text_column],
    )
    country_column = _name_match([c for c in columns if c != text_column], COUNTRY_NAMES)
    url_column = _name_match([c for c in columns if c != text_column], URL_NAMES)
    id_column = _name_match([c for c in columns if c != text_column], ID_NAMES)

    confidence = min(max(text_score / 8.0, 0.0), 1.0)

    return DetectedSchema(
        text_column=text_column,
        title_column=title_column,
        source_column=source_column,
        date_column=date_column,
        country_column=country_column,
        url_column=url_column,
        id_column=id_column,
        confidence=round(confidence, 2),
    )
