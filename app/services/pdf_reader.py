from __future__ import annotations

from io import BytesIO
from typing import BinaryIO
import re

import pymupdf

from app.models.article_document import ArticleDocument
from app.services.language_detector import detect_language
from app.services.text_cleaner import clean_text
from app.services.metadata_detector import detect_date_from_text, detect_source_from_text, detect_title_from_text


class PDFReadError(Exception):
    pass


_FRONT_PATTERNS = re.compile(
    r"^(?:table\s+des\s+mati[eè]res|sommaire|liste\s+des\s+(?:tableaux|graphiques|figures|encadr[eé]s)|"
    r"copyright|le\s+pr[eé]sent\s+rapport\s+est\s+la\s+propri[eé]t[eé])\b",
    re.I,
)
_BACK_PATTERNS = re.compile(r"^(?:annexe(?:s)?(?:\s+\d+)?|bibliographie|r[eé]f[eé]rences\s+bibliographiques|appendix)\b", re.I)


def _first_meaningful_line(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in (text or "").splitlines() if line.strip()]
    while lines and re.fullmatch(r"\d{1,3}", lines[0]):
        lines.pop(0)
    return lines[0] if lines else ""


def _looks_front_matter(text: str, page_number: int) -> bool:
    heading = _first_meaningful_line(text)
    if _FRONT_PATTERNS.search(heading):
        return True
    # Do not discard a short first page merely because it is compact. Many
    # official notes and one-page economic briefs are shorter than 900 chars.
    # Explicit front-matter headings above remain excluded; downstream content
    # selection handles non-economic cover text safely.
    return False


def _looks_back_matter(text: str, page_number: int, total_pages: int) -> bool:
    heading = _first_meaningful_line(text)
    # Product rule: annex/appendix content is never analysed, even when the
    # annex contains valid macroeconomic tables. This keeps the business output
    # focused on the report body and avoids accidental ingestion of technical
    # appendices.
    if _BACK_PATTERNS.search(heading):
        return True
    if page_number <= max(6, total_pages // 2):
        return False
    return bool(re.match(r"^(?:bibliographie|r[eé]f[eé]rences\s+bibliographiques|appendix\s+references)\b", heading, re.I))


def _merge_overlapping_tokens(left: str, right: str) -> str:
    if left.lower() in right.lower() and len(left) <= len(right):
        return right
    if right.lower() in left.lower() and len(right) <= len(left):
        return left
    max_overlap = min(len(left), len(right))
    for size in range(max_overlap, 0, -1):
        if left[-size:].lower() == right[:size].lower():
            return left + right[size:]
    return left + right


def _truncate_inline_annex(text: str) -> str:
    """Drop inline Annex/Appendix content while preserving body text before it."""
    if not text:
        return text
    # Match an actual annex heading, not prose such as "exclusion des annexes".
    match = re.search(r"\b(?:Annexe(?:\s+(?:[A-Z0-9]+|technique|statistique|methodologique|méthodologique|compl[eé]mentaire))?|Appendix(?:\s+(?:[A-Z0-9]+|technical|statistics?|robustness))?)\b(?:\s*[-–—:]|\s+(?:Scenario|Scénario|This|Regression|Donn[ée]es))", text, re.I)
    if match and match.start() > 80:
        return text[:match.start()].strip()
    return text


def _extract_page_text(page: pymupdf.Page, excluded_bboxes: list[list[float]] | None = None) -> str:
    """Reconstruct visual lines from words, repairing duplicated text layers.

    Several economic reports contain two overlapping text layers. PyMuPDF then
    returns fragments such as ``p`` + ``publique`` or ``l'en`` + ``nsemble``.
    This routine merges overlapping words by geometry and string overlap.
    """
    raw_text = page.get_text("text", sort=False)
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", raw_text or ""))
    letters = len(re.findall(r"[A-Za-zÀ-ÿ\u0600-\u06FF]", raw_text or ""))
    if letters and arabic_chars / letters >= 0.35:
        # PyMuPDF already preserves the logical character order inside Arabic
        # spans. Re-sorting its words from left to right reverses every RTL
        # line, so Arabic pages deliberately use the native text stream.
        # Keep visual line boundaries. Arabic headings are hard semantic
        # boundaries and must not be flattened into the surrounding paragraph.
        text = raw_text
        # RTL streams may serialize ``value in YEAR.`` as
        # ``value\n.YEAR in``. Join the detached date before punctuation-based
        # sentence splitting so the forecast/observation keeps its period.
        text = re.sub(
            r"([-+]?\d+(?:[.,]\d+)?\s*%?)\s*\n?\.\s*((?:19|20)\d{2})\s+في",
            r"\1 في \2.", text,
        )
        # Canonicalise the recurrent RTL extraction order where the percent
        # sign is emitted after the Arabic preposition (``3.1 في% 2024``).
        text = re.sub(r"\s+في\s*[٪%]", " % في", text)
        text = text.replace("٪", "%")
        text = re.sub(r"%\s*((?!(?:19|20)\d{2}\b)[-+]?\d+(?:[.,]\d+)?)", r"\1%", text)
        text = re.sub(
            r"([-+]?\d+(?:[.,]\d+)?)\s+(في\s+الربع\s+\S+\s+من|حتى\s+\S+|في\s+\S+)\s*%\s*((?:19|20)\d{2})",
            r"\1% \2 \3", text,
        )
        text = re.sub(r"([-+]?\d+(?:[.,]\d+)?)\s+(قبل|بعد)\s*%", r"\1% \2", text)
        text = re.sub(r"([-+]?\d+(?:[.,]\d+)?)\s+في\s+الربع\s*%\s+(السابق|التالي)", r"\1% في الربع \2", text)
        text = re.sub(r"([-+]?\d+(?:[.,]\d+)?)\s*%?\s*\.\s*(قبل\s+ثلاث(?:ة)?\s+أشهر)\s*%", r"\1% \2.", text)
        # Some RTL writers emit ``value . in COUNTRY %`` although visually the
        # percent belongs to the value. Restore the atomic value before normal
        # sentence segmentation; the country name remains untouched.
        text = re.sub(
            r"([-+]?\d+(?:[.,]\d+)?)\s*%?\s*\.\s*في\s+([\u0600-\u06FF]+)(?:\s*[،,]\s*على\s+الترتيب)?\s*%",
            r"\1% في \2.", text,
        )
        text = re.sub(
            r"([-+]?\d+(?:[.,]\d+)?)\s+((?:من\s+الناتج\s+المحلي\s+\S*جمالي|"
            r"في\s+(?:الربع\s+\S+(?:\s+من)?|(?:يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر))|"
            r"حتى\s+(?:يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر)))\s*%",
            r"\1% \2", text,
        )
        text = re.sub(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(مليار|مليون|نقطة\s+مئوية)", r"\1 \2", text)
        text = re.sub(r"(مليار|مليون)\s+(درهم|دينار|دولار|دوالر)\s*(\d+(?:[.,]\d+)?)", r"\3 \1 \2", text)
        text = re.sub(r"([-+]?\d+(?:[.,]\d+)?)\s*\.\s*(مليار|مليون)\s+(درهم|دينار|دولار|دوالر)", r"\1 \2 \3", text)
        text = re.sub(r"(نقطة\s+مئوية)\s*(\d+(?:[.,]\d+)?)", r"\2 \1", text)
        text = re.sub(r"\b(19|20)(\d{2})\s+في\b", r"في \1\2", text)
        text = re.sub(r"(?<=[\u0600-\u06FF])(?=\d)", " ", text)
        text = re.sub(r"(?<=\d)(?=[\u0600-\u06FF])", " ", text)
        # Arabic vocalisation marks vary between publishers and must not make
        # identical economic vocabulary look like different tokens.
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        text = re.sub(r"([.!؟])(?=[\u0600-\u06FF])", r"\1 ", text)
        return clean_text(text)

    words = page.get_text("words", sort=False)
    excluded_bboxes = excluded_bboxes or []
    rows: list[list[tuple[float, float, str]]] = []
    row_y: list[float] = []
    for x0, y0, x1, y1, token, *_ in sorted(words, key=lambda w: (round(w[1], 1), w[0])):
        cx, cy = (float(x0) + float(x1)) / 2, (float(y0) + float(y1)) / 2
        if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in excluded_bboxes):
            continue
        token = str(token or "").strip()
        if not token:
            continue
        target = None
        for idx, y in enumerate(row_y):
            if abs(float(y0) - y) <= 2.5:
                target = idx
                break
        if target is None:
            row_y.append(float(y0))
            rows.append([(float(x0), float(x1), token)])
        else:
            rows[target].append((float(x0), float(x1), token))

    lines: list[str] = []
    for row in rows:
        ordered = sorted(row, key=lambda item: (item[0], -(item[1] - item[0])))
        merged: list[list[object]] = []
        for x0, x1, token in ordered:
            if re.fullmatch(r"\d{1,3}", token) and len(row) == 1:
                continue
            if not merged:
                merged.append([x0, x1, token])
                continue
            prev_x0, prev_x1, prev_token = merged[-1]
            if x0 <= float(prev_x1) + 0.8:
                merged[-1][1] = max(float(prev_x1), x1)
                merged[-1][2] = _merge_overlapping_tokens(str(prev_token), token)
            else:
                merged.append([x0, x1, token])
        line = " ".join(str(item[2]) for item in merged)
        line = re.sub(r"\s+", " ", line).strip()
        if line and not re.fullmatch(r"\d{1,3}", line):
            lines.append(line)
    # Preserve visual line boundaries: headings are structural evidence.
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return clean_text(text)


def _extract_page_tables(page: pymupdf.Page, page_number: int) -> list[dict]:
    """Return geometry-backed table grids without flattening them into prose.

    The semantic table layer consumes this neutral representation.  Keeping the
    raw row/column grid here makes ingestion independent from any indicator,
    country, page number or report-specific vocabulary.
    """
    tables: list[dict] = []
    try:
        found = page.find_tables()
    except Exception:
        return tables
    for index, table in enumerate(found.tables):
        grid = table.extract()
        if not grid or len(grid) < 2:
            continue
        nonempty = sum(1 for row in grid for cell in row if cell not in (None, ""))
        if nonempty < 4:
            continue
        bbox = [round(float(x), 2) for x in table.bbox]
        tables.append({
            "page": page_number,
            "table_index": index,
            "bbox": bbox,
            "rows": grid,
        })
    return tables


def read_pdf(
    uploaded_file: BinaryIO,
    source: str | None = None,
    publication_date: str | None = None,
    narrative_only: bool = True,
) -> list[ArticleDocument]:
    try:
        raw = uploaded_file.getvalue()
        pdf = pymupdf.open(stream=BytesIO(raw), filetype="pdf")
    except Exception as exc:
        raise PDFReadError(f"Impossible d'ouvrir le PDF : {exc}") from exc

    total_pages = len(pdf)
    pages: list[tuple[int, str]] = []
    structured_tables: list[dict] = []
    for index, page in enumerate(pdf, start=1):
        page_tables = _extract_page_tables(page, index)
        text = _extract_page_text(page, [t["bbox"] for t in page_tables])
        if narrative_only:
            text = _truncate_inline_annex(text)
        if not text:
            continue
        if narrative_only and _looks_front_matter(text, index):
            continue
        if narrative_only and _looks_back_matter(text, index, total_pages):
            heading = _first_meaningful_line(text)
            if re.match(r"^(?:bibliographie|r[eé]f[eé]rences\s+bibliographiques)\b", heading, re.I):
                break
            continue
        pages.append((index, text))
        structured_tables.extend(page_tables)
    pdf.close()

    if not pages:
        raise PDFReadError("Aucun texte exploitable n'a été trouvé. Le PDF est peut-être scanné ou protégé.")

    full_text = "\n\n".join(f"[[PAGE {page_no}]]\n{text}" for page_no, text in pages)
    auto_title = detect_title_from_text(full_text, fallback=getattr(uploaded_file, "name", "Document PDF"))
    auto_source = detect_source_from_text(full_text, fallback=source)
    auto_date = detect_date_from_text(full_text) or publication_date

    document = ArticleDocument(
        text=full_text,
        input_type="pdf",
        title=auto_title,
        source=auto_source,
        publication_date=auto_date,
        language=detect_language(full_text),
        filename=getattr(uploaded_file, "name", None),
        page_number=None,
        structured_tables=structured_tables,
    )
    document.page_count = total_pages
    document.kept_page_count = len(pages)
    document.kept_page_numbers = [p for p, _ in pages]
    return [document]
