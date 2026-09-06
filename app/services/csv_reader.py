from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import pandas as pd

from app.models.article_document import ArticleDocument
from app.services.language_detector import detect_language
from app.services.text_cleaner import clean_text
from app.services.schema_detector import detect_csv_schema


class CSVReadError(Exception):
    pass


def load_csv_dataframe(uploaded_file: BinaryIO) -> pd.DataFrame:
    """
    Lit un CSV avec plusieurs encodages et détecte automatiquement
    le séparateur grâce au moteur Python de pandas.
    """

    raw = uploaded_file.getvalue()

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    ]

    last_error: Exception | None = None

    for encoding in encodings:
        try:
            return pd.read_csv(
                BytesIO(raw),
                encoding=encoding,
                sep=None,
                engine="python",
            )
        except Exception as exc:
            last_error = exc

    raise CSVReadError(
        "Impossible de lire le CSV. Vérifiez son encodage, son séparateur "
        f"et sa structure. Détail : {last_error}"
    )


def dataframe_to_documents(
    df: pd.DataFrame,
    text_column: str,
    title_column: str | None = None,
    source_column: str | None = None,
    date_column: str | None = None,
    country_column: str | None = None,
    url_column: str | None = None,
    id_column: str | None = None,
    filename: str | None = None,
) -> list[ArticleDocument]:

    if text_column not in df.columns:
        raise CSVReadError("La colonne texte sélectionnée n'existe pas.")

    documents: list[ArticleDocument] = []

    for index, row in df.iterrows():
        raw_text = row.get(text_column)

        if pd.isna(raw_text):
            continue

        text = clean_text(str(raw_text))

        if not text:
            continue

        def optional_value(column_name: str | None) -> str | None:
            if not column_name or column_name not in df.columns:
                return None

            value = row.get(column_name)
            return None if pd.isna(value) else str(value).strip()

        documents.append(
            ArticleDocument(
                text=text,
                input_type="csv",
                title=optional_value(title_column) or f"Article CSV #{index + 1}",
                source=optional_value(source_column),
                publication_date=optional_value(date_column),
                language=detect_language(text),
                filename=filename,
                country=optional_value(country_column),
                source_url=optional_value(url_column),
                document_id=optional_value(id_column) or "",
            )
        )

    return documents



def dataframe_to_documents_auto(
    df: pd.DataFrame,
    filename: str | None = None,
) -> tuple[list[ArticleDocument], object]:
    schema = detect_csv_schema(df)

    documents = dataframe_to_documents(
        df=df,
        text_column=schema.text_column,
        title_column=schema.title_column,
        source_column=schema.source_column,
        date_column=schema.date_column,
        country_column=schema.country_column,
        url_column=schema.url_column,
        id_column=schema.id_column,
        filename=filename,
    )

    return documents, schema
