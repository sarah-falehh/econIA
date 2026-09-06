from __future__ import annotations

"""Document-structure and sentence selection for economic extraction.

This module intentionally runs *before* numeric extraction.  Its job is to
remove tables of contents, appendices, bibliographies, regression tables,
equations, captions and other material that contains many numbers but is not a
narrative economic observation.
"""

import re
from dataclasses import dataclass
from typing import Iterable

from app.services.ollama_client import generate_json, is_available, DEFAULT_MODEL


STRUCTURAL_PAGE_PATTERNS = [
    r"^\s*table\s+des\s+mati[eè]res\b",
    r"^\s*sommaire\b",
    r"^\s*liste\s+des\s+(?:tableaux|graphiques|figures|encadr[eé]s)\b",
    r"^\s*(?:annexe|appendix|الملاحق)\b",
    r"^\s*bibliographie\b",
    r"^\s*r[eé]f[eé]rences\s+bibliographiques\b",
]

STOP_SECTION_PATTERNS = [
    r"^\s*(?:annexe|appendix|الملاحق)\b",
    r"^\s*bibliographie\b",
    r"^\s*r[eé]f[eé]rences\s+bibliographiques\b",
]

NON_NARRATIVE_PATTERNS = [
    r"^\s*(?:tableau|graphique|figure|encadr[eé])\s*\d+\s*[:.-]",
    r"^\s*(?:source|sources)\s*:\s*[^.!?]{0,120}$",
    r"^\s*(?:variable|coefficient|statistique\s+t|significativit[eé])\b",
    r"\b(?:r\s*[²2]|statistique\s+t|p[- ]?value|significativit[eé])\b",
    r"\b(?:constante|coefficient)\s*[-+:=]",
    r"\b(?:tels?\s+que|avec)\s*:\s*[A-Z]{1,8}\b",
    r"\b(?:equation|[ée]quation|mod[eè]le)\s*(?:suivante|s['’]?[ée]crit|:)\b",
    r"(?:[A-Za-z]{1,8}\s*=\s*){2,}",
    r"^\s*\d+\s*$",
    r"^\s*[-–—•▪]+\s*$",
]

BIBLIOGRAPHY_CUES = [
    r"\([12][0-9]{3}\)",
    r"\bvol\.?\s*\d+\b",
    r"\bpp?\.?\s*\d+[-–]\d+\b",
    r"\bworking\s+paper\b",
    r"\bthe\s+(?:american|economic|journal)\b",
]

NARRATIVE_CUES = [
    r"\b(?:a atteint|s['’]est [ée]tabli|est pass[ée] de|a progress[ée]|a recul[ée]|a augment[ée]|a diminu[ée])\b",
    r"\b(?:atteignant|contre|par rapport [àa]|un an auparavant|l['’]ann[ée]e pr[ée]c[ée]dente)\b",
    r"\b(?:stood at|reached|rose to|fell to|increased to|decreased to|compared with|compared to)\b",
    r"(?:بلغ|ارتفع|انخفض|مقارنة|مقابل)",
]


@dataclass
class SelectionReport:
    kept: list[str]
    rejected: list[tuple[str, str]]
    method: str


def is_structural_page(text: str) -> bool:
    sample = (text or "").strip()[:1800]
    return any(re.search(pattern, sample, re.IGNORECASE | re.MULTILINE) for pattern in STRUCTURAL_PAGE_PATTERNS)


def truncate_before_back_matter(pages: list[str]) -> list[str]:
    """Drop annexes/bibliography and everything after their first main heading."""
    kept: list[str] = []
    for page in pages:
        lines = [line.strip() for line in (page or "").splitlines() if line.strip()]
        first_heading = lines[0] if lines else ""
        if any(re.search(pattern, first_heading, re.IGNORECASE) for pattern in STOP_SECTION_PATTERNS):
            break
        if not is_structural_page(page):
            kept.append(page)
    return kept


def _looks_like_table_row(sentence: str) -> bool:
    text = sentence.strip()
    # Rows copied from tables usually contain several short numeric columns.
    numbers = re.findall(r"[-+]?\d+(?:[.,]\d+)?", text)
    words = re.findall(r"[A-Za-zÀ-ÿ\u0600-\u06FF]+", text)
    return len(numbers) >= 3 and len(words) <= 14 and not any(
        re.search(cue, text, re.IGNORECASE) for cue in NARRATIVE_CUES
    )


def sentence_rejection_reason(sentence: str) -> str | None:
    text = re.sub(r"\s+", " ", sentence or "").strip()
    if len(text) < 18:
        return "trop_court"
    if any(re.search(p, text, re.IGNORECASE) for p in NON_NARRATIVE_PATTERNS):
        return "structure_table_equation"
    if _looks_like_table_row(text):
        return "ligne_tableau"
    # Academic citations with no clear economic statement are excluded.
    citation_hits = sum(bool(re.search(p, text, re.IGNORECASE)) for p in BIBLIOGRAPHY_CUES)
    if citation_hits >= 2 and not any(re.search(c, text, re.IGNORECASE) for c in NARRATIVE_CUES):
        return "reference_academique"
    # A sentence must contain a genuine measurement marker, not merely years.
    measurements = re.findall(r"[-+]?\d+(?:[.,]\d+)?\s*(?:%|pour cent|percent|points?|milliards?|millions?|md\b|tnd\b|usd\b|eur\b|jours?)", text, re.IGNORECASE)
    if not measurements:
        return "aucune_mesure_economique"
    return None


def select_sentences_heuristic(sentences: Iterable[str]) -> SelectionReport:
    kept: list[str] = []
    rejected: list[tuple[str, str]] = []
    for sentence in sentences:
        reason = sentence_rejection_reason(sentence)
        if reason:
            rejected.append((sentence, reason))
        else:
            kept.append(sentence)
    return SelectionReport(kept=kept, rejected=rejected, method="heuristic")


def select_sentences_llm(
    sentences: list[str],
    *,
    model: str = DEFAULT_MODEL,
    batch_size: int = 18,
) -> SelectionReport:
    """Use Ollama as a strict gate, while keeping the deterministic extractor.

    The model does not calculate values. It only decides whether a sentence is a
    narrative economic observation suitable for the business table.
    """
    if not is_available():
        return select_sentences_heuristic(sentences)

    schema = {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "keep": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "required": ["id", "keep", "reason"],
                },
            }
        },
        "required": ["decisions"],
    }

    kept: list[str] = []
    rejected: list[tuple[str, str]] = []

    for start in range(0, len(sentences), batch_size):
        batch = sentences[start:start + batch_size]
        numbered = "\n".join(f"[{start+i}] {s}" for i, s in enumerate(batch))
        prompt = f"""
Tu es le filtre qualité d'une application d'extraction économique.
Conserve UNIQUEMENT les phrases narratives qui affirment une observation économique chiffrée réelle ou prévue.
Rejette : tables des matières, annexes, bibliographie, titres/captions, numéros de pages, équations, définitions, listes de variables, coefficients de régression, statistiques t, p-values, exemples théoriques et années citées sans observation.
Une phrase comme « le coefficient de l'inflation est -0,791 » doit être rejetée.
Une phrase comme « la dette est passée de 40,4 % en 2010 à 47 % en 2013 » doit être conservée.
Ne corrige pas et ne réécris pas le texte. Retourne une décision pour chaque identifiant.

PHRASES :
{numbered}
"""
        try:
            payload = generate_json(prompt, model=model, schema=schema)
            decisions = {int(d["id"]): d for d in payload.get("decisions", [])}
        except Exception:
            fallback = select_sentences_heuristic(batch)
            kept.extend(fallback.kept)
            rejected.extend(fallback.rejected)
            continue

        for local_i, sentence in enumerate(batch):
            idx = start + local_i
            decision = decisions.get(idx)
            heuristic_reason = sentence_rejection_reason(sentence)
            # Safety: deterministic exclusions cannot be overridden by the LLM.
            if heuristic_reason in {"structure_table_equation", "ligne_tableau", "reference_academique"}:
                rejected.append((sentence, heuristic_reason))
            elif decision and bool(decision.get("keep")):
                kept.append(sentence)
            else:
                rejected.append((sentence, (decision or {}).get("reason", heuristic_reason or "rejet_llm")))

    return SelectionReport(kept=kept, rejected=rejected, method=f"ollama:{model}")
