from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional
from uuid import uuid4


@dataclass
class ArticleDocument:
    """Structure commune à tous les documents entrants."""

    text: str
    input_type: str
    title: Optional[str] = None
    source: Optional[str] = None
    publication_date: Optional[str] = None
    language: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None
    country: Optional[str] = None
    country_iso3: Optional[str] = None
    source_url: Optional[str] = None
    structured_tables: Optional[list[dict[str, Any]]] = None
    document_id: str = ""

    def __post_init__(self) -> None:
        if not self.document_id:
            self.document_id = str(uuid4())

    def to_dict(self) -> dict:
        return asdict(self)
