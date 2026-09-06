from __future__ import annotations

import re
from urllib.parse import urlparse


URL_PATTERN = re.compile(r"https?://[^\s)\]>]+", re.IGNORECASE)

DATE_PATTERNS = [
    r"\b(\d{4}-\d{2}-\d{2})\b",
    r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
    r"\b(\d{1,2}-\d{1,2}-\d{4})\b",
]


def detect_source_from_text(text: str, fallback: str | None = None) -> str | None:
    match = URL_PATTERN.search(text or "")
    if match:
        try:
            domain = urlparse(match.group(0)).netloc.lower()
            return domain.removeprefix("www.")
        except Exception:
            pass

    return fallback


def detect_date_from_text(text: str) -> str | None:
    sample = (text or "")[:3000]

    for pattern in DATE_PATTERNS:
        match = re.search(pattern, sample)
        if match:
            return match.group(1)

    return None


def detect_title_from_text(text: str, fallback: str | None = None) -> str | None:
    lines = [
        line.strip()
        for line in (text or "").splitlines()
        if line.strip()
    ]

    for line in lines[:8]:
        if 15 <= len(line) <= 180 and not URL_PATTERN.fullmatch(line):
            return line

    return fallback
