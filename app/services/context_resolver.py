from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")

PREVIOUS_YEAR_PATTERNS = (
    r"\bl['’]année précédente\b", r"\bannée précédente\b", r"\bl['’]annee precedente\b", r"\bannee precedente\b",
    r"\bl['’]année d['’]avant\b", r"\bl['’]annee d['’]avant\b", r"\bun an auparavant\b",
    r"\bun an plus tôt\b", r"\bun an plus tot\b", r"\bl['’]année dernière\b", r"\bl['’]annee derniere\b", r"\bl['’]an dernier\b",
    r"\bprevious year\b", r"\blast year\b", r"\ba year earlier\b", r"\bone year earlier\b",
    r"\bsame period last year\b", r"العام السابق", r"السنة السابقة", r"العام الماضي", r"السنة الماضية",
)
SAME_POINT_PREVIOUS_YEAR_PATTERNS = (
    r"\bun an auparavant\b", r"\bun an plus tôt\b", r"\bun an plus tot\b",
    r"\bl['’]année précédente\b", r"\bl['’]annee precedente\b", r"\bl['’]année d['’]avant\b", r"\bl['’]annee d['’]avant\b",
    r"\ba year earlier\b", r"\bone year earlier\b",
)
SAME_POINT_NEXT_YEAR_PATTERNS = (
    r"\bun an plus tard\b", r"\bone year later\b",
)

NEXT_YEAR_PATTERNS = (
    r"\bl['’]année suivante\b", r"\bannée suivante\b", r"\bun an plus tard\b",
    r"\bnext year\b", r"\bthe following year\b", r"\bone year later\b",
    r"العام التالي", r"السنة التالية", r"العام الموالي", r"السنة الموالية",
)
CURRENT_YEAR_PATTERNS = (
    r"\bcette année\b", r"\bcette même année\b", r"\bla même année\b",
    r"\bl['’]année en cours\b", r"\bthis year\b", r"\bthis same year\b", r"\bthe same year\b",
    r"هذه السنة", r"هذا العام",
)
PREVIOUS_QUARTER_PATTERNS = (
    r"\btrimestre précédent\b", r"\btrimestre precedent\b", r"\btrimestre d['’]avant\b", r"\btrimestre d'avant\b", r"\btrimestre qui précédait\b", r"\btrimestre qui precedait\b",
    r"\btrois mois auparavant\b", r"\btrois mois plus tôt\b", r"\btrois mois plus tot\b",
    r"\bthree months earlier\b", r"\bprevious quarter\b", r"الربع السابق")
NEXT_QUARTER_PATTERNS = (
    r"\btrimestre suivant\b", r"\btrimestre qui suivait\b", r"\btrois mois plus tard\b",
    r"\bnext quarter\b", r"\bfollowing quarter\b", r"الربع التالي")
PREVIOUS_MONTH_PATTERNS = (
    r"\bmois précédent\b", r"\bmois precedent\b", r"\bun mois auparavant\b", r"\bun mois plus tôt\b", r"\bun mois plus tot\b", r"\bmois dernier\b",
    r"\bprevious month\b", r"\blast month\b", r"الشهر السابق", r"الشهر الماضي")
NEXT_MONTH_PATTERNS = (r"\bmois suivant\b", r"\bun mois plus tard\b", r"\bnext month\b", r"\bfollowing month\b", r"الشهر التالي")
TWO_YEARS_EARLIER_PATTERNS = (r"\bdeux ans plus tôt\b", r"\bdeux ans plus tot\b", r"\bdeux ans auparavant\b", r"\bdeux années auparavant\b", r"\bdeux annees auparavant\b", r"\btwo years earlier\b")
SIX_MONTHS_EARLIER_PATTERNS = (r"\bsix mois plus tôt\b", r"\bsix mois plus tot\b", r"\bsix months earlier\b")

COREFERENCE_HINTS = re.compile(
    r"^(?:\s|[,;:])*(?:elles?|ils?|elle|il|leur(?:s)?(?:\s+niveau)?|ce taux|ce niveau|cette valeur|ce chiffre|ce dernier|"
    r"cette dernière|cette hausse|cette baisse|celui-ci|celle-ci|une seconde source|une autre source|"
    r"une estimation (?:provisoire|préliminaire|preliminaire)|the rate|this rate|this level|it|they|these|those|"
    r"هذا المعدل|هذه النسبة|هذا المستوى|هي|هو|هم)\b", re.I,
)

PERIOD_PREFIX_COREFERENCE = re.compile(
    r"^\s*(?:(?:en|pour)\s+(?:19|20)\d{2}|en\s+(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)(?:\s+(?:19|20)\d{2})?|au\s+(?:premier|deuxième|troisième|quatrième|[1-4](?:er|e|ème)?)\s+trimestre)\s*,?\s*(?:elles?|ils?|elle|il)\b",
    re.I,
)
COUNTRY_PREFIX_COREFERENCE = re.compile(
    r"^\s*(?:en|au|aux)\s+[A-Za-zÀ-ÿ'’ -]{2,45},\s*(?:elles?|ils?|elle|il|ce taux|ce ratio|ce niveau|leur niveau)\b",
    re.I,
)
TEMPORAL_PREFIX_COREFERENCE = re.compile(
    r"^\s*(?:au\s+dernier\s+trimestre(?:\s+de\s+l['’]année)?|au\s+trimestre\s+(?:suivant|précédent|precedent)|au\s+trimestre\s+qui\s+(?:précédait|precedait|suivait)|un\s+mois\s+plus\s+(?:tôt|tot)|trois\s+mois\s+plus\s+tard|l['’]année\s+d['’]avant|l['’]annee\s+d['’]avant|deux\s+(?:ans|années|annees)\s+(?:auparavant|plus\s+(?:tôt|tot))|six\s+mois\s+plus\s+(?:tôt|tot)|un\s+mois\s+auparavant),?\s*(?:elles?|ils?|elle|il|ce taux|ce ratio|ce niveau)\b",
    re.I,
)
RELATIVE_PERIOD_HINTS = re.compile(
    r"(?:année précédente|annee precedente|année suivante|annee suivante|cette année|cette annee|cette même année|cette meme annee|la même année|la meme annee|an dernier|un an auparavant|un an plus tôt|un an plus tot|deux ans plus tôt|deux ans plus tot|un an plus tard|"
    r"previous year|last year|next year|following year|deux ans auparavant|deux années auparavant|deux annees auparavant|même période|meme periode|same period|trimestre précédent|trimestre precedent|trimestre qui précédait|trimestre qui precedait|trimestre suivant|trois mois plus tard|"
    r"previous quarter|trimestre d['’]avant|trois mois auparavant|trois mois plus tôt|trois mois plus tot|six mois plus tôt|six mois plus tot|three months earlier|six months earlier|next quarter|mois précédent|mois precedent|un mois plus tôt|un mois plus tot|mois suivant|un mois plus tard|previous month|next month|"
    r"\b(?:deux|2|trois|3|quatre|4|cinq|5|six|6|sept|7|huit|8|neuf|9|dix|10|onze|11|douze|12)\s+mois\s+(?:plus\s+(?:tôt|tot|tard)|auparavant)\b|"\
    r"العام السابق|السنة السابقة|العام التالي|السنة التالية|الربع السابق|الربع التالي|الشهر السابق|الشهر التالي)", re.I,
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.I) for pattern in patterns)



TITLE_MONTHS = {
    "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12,
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
}

def publication_month(document: dict) -> int | None:
    title = str(document.get("title") or "").lower()
    for word, month in TITLE_MONTHS.items():
        if re.search(rf"\b{re.escape(word)}\b", title):
            return month
    return None

def publication_year(document: dict) -> int | None:
    # A year explicitly named in the article title is usually the statistical
    # reference period and is stronger than the website publication timestamp.
    title = str(document.get("title") or "")
    match = YEAR_RE.search(title)
    if match:
        return int(match.group(1))
    raw = str(document.get("publication_date") or "").strip()
    if raw:
        match = YEAR_RE.search(raw)
        if match:
            return int(match.group(1))
        try:
            return datetime.fromisoformat(raw).year
        except ValueError:
            pass
    return None


def first_explicit_year(text: str) -> int | None:
    match = YEAR_RE.search(text or "")
    return int(match.group(1)) if match else None


def shift_quarter(year: int | None, quarter: int | None, delta: int) -> tuple[int | None, int | None]:
    if quarter is None:
        return year, None
    if year is None:
        return None, ((quarter - 1 + delta) % 4) + 1
    index = year * 4 + (quarter - 1) + delta
    return index // 4, index % 4 + 1


def shift_month(year: int | None, month: int | None, delta: int) -> tuple[int | None, int | None]:
    if month is None:
        return year, None
    if year is None:
        return None, ((month - 1 + delta) % 12) + 1
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


@dataclass
class DocumentContext:
    anchor_year: int | None = None
    document_year: int | None = None
    document_month: int | None = None
    current_year: int | None = None
    current_quarter: int | None = None
    current_month: int | None = None
    # v4.23: stable discourse anchor. Relative expressions are resolved from
    # the last explicitly stated period, not from another relative result.
    discourse_year: int | None = None
    discourse_quarter: int | None = None
    discourse_month: int | None = None
    last_indicators: list[tuple[str, str]] = field(default_factory=list)
    last_country: str | None = None
    last_country_iso3: str | None = None
    last_unit: str | None = None
    last_scale: str | None = None
    last_currency: str | None = None
    last_value: float | None = None

    @classmethod
    def from_document(cls, document: dict) -> "DocumentContext":
        anchor = publication_year(document) or first_explicit_year(document.get("text", ""))
        month = publication_month(document)
        # Document metadata is a fallback, not the active sentence period.
        # Keeping it separate prevents a title such as "décembre 2025" (or a
        # previously seen December event) from turning later annual values into
        # 2025-M12.
        return cls(anchor_year=anchor, document_year=anchor, document_month=month, current_year=anchor, discourse_year=anchor)

    def remember_explicit_period(self, month: int | None, quarter: int | None, year: int | None) -> None:
        if year is not None:
            self.current_year = year
        # Granularity is mutually exclusive. An explicitly annual event clears
        # stale month/quarter context; a quarter clears stale month; a month
        # clears stale quarter. This is the main non-regression guard against
        # accidental M12 propagation across unrelated sentences.
        if month is not None:
            self.current_month = month
            self.current_quarter = None
        elif quarter is not None:
            self.current_quarter = quarter
            self.current_month = None
        elif year is not None:
            self.current_quarter = None
            self.current_month = None

    def remember_discourse_anchor(self, month: int | None, quarter: int | None, year: int | None) -> None:
        """Remember an explicitly stated discourse period.

        Unlike ``current_*``, this anchor is never moved by a relative phrase.
        Thus ``En 2024 ... L'année d'avant ... Deux ans plus tôt ...`` resolves
        to 2024, 2023, 2022 instead of chaining 2024 -> 2023 -> 2021.
        """
        if year is not None:
            self.discourse_year = year
        if month is not None:
            self.discourse_month = month
            self.discourse_quarter = None
        elif quarter is not None:
            self.discourse_quarter = quarter
            self.discourse_month = None
        elif year is not None:
            self.discourse_month = None
            self.discourse_quarter = None

    def remember_event(self, *, code: str, label: str, value: float | None, unit: str | None,
                       scale: str | None, currency: str | None, month: int | None,
                       quarter: int | None, year: int | None) -> None:
        self.last_indicators = [(code, label)]
        self.last_value = value
        self.last_unit = unit
        self.last_scale = scale
        self.last_currency = currency
        self.remember_explicit_period(month, quarter, year)

    def resolve_period(self, fragment: str, month: int | None, quarter: int | None, year: int | None,
                       *, inherit: bool = True) -> tuple[int | None, int | None, int | None]:
        text = fragment or ""
        is_relative = bool(RELATIVE_PERIOD_HINTS.search(text))
        base_year = (self.discourse_year if is_relative else self.current_year) or self.anchor_year
        base_quarter = self.discourse_quarter if is_relative else self.current_quarter
        base_month = self.discourse_month if is_relative else self.current_month
        resolved_year, resolved_quarter, resolved_month = year, quarter, month

        if _matches_any(text, TWO_YEARS_EARLIER_PATTERNS):
            resolved_year = base_year - 2 if base_year is not None else None
            if resolved_month is None and base_month is not None:
                resolved_month = base_month
            if resolved_quarter is None and base_quarter is not None:
                resolved_quarter = base_quarter
        elif _matches_any(text, PREVIOUS_YEAR_PATTERNS):
            resolved_year = base_year - 1 if base_year is not None else None
            if _matches_any(text, SAME_POINT_PREVIOUS_YEAR_PATTERNS):
                if resolved_month is None and base_month is not None:
                    resolved_month = base_month
                if resolved_quarter is None and base_quarter is not None:
                    resolved_quarter = base_quarter
        elif _matches_any(text, NEXT_YEAR_PATTERNS):
            resolved_year = base_year + 1 if base_year is not None else None
            if _matches_any(text, SAME_POINT_NEXT_YEAR_PATTERNS):
                if resolved_month is None and base_month is not None:
                    resolved_month = base_month
                if resolved_quarter is None and base_quarter is not None:
                    resolved_quarter = base_quarter
        elif _matches_any(text, CURRENT_YEAR_PATTERNS):
            resolved_year = base_year
        elif re.search(r"\b(?:même période|same period)\b", text, re.I):
            resolved_year = resolved_year or base_year
            if resolved_month is None and base_month is not None:
                resolved_month = base_month
            if resolved_quarter is None and base_quarter is not None:
                resolved_quarter = base_quarter
        elif resolved_year is None and inherit:
            resolved_year = base_year

        if resolved_quarter is None and _matches_any(text, SIX_MONTHS_EARLIER_PATTERNS):
            resolved_year, resolved_quarter = shift_quarter(resolved_year or base_year, base_quarter, -2)
        elif resolved_quarter is None and _matches_any(text, PREVIOUS_QUARTER_PATTERNS):
            resolved_year, resolved_quarter = shift_quarter(resolved_year or base_year, base_quarter, -1)
        elif resolved_quarter is None and _matches_any(text, NEXT_QUARTER_PATTERNS):
            resolved_year, resolved_quarter = shift_quarter(resolved_year or base_year, base_quarter, 1)
        elif resolved_quarter is None:
            resolved_quarter = None

        # Generic month offsets (2..12) share one arithmetic primitive instead
        # of one regex per benchmark phrase.
        month_words = {
            "deux":2,"2":2,"trois":3,"3":3,"quatre":4,"4":4,"cinq":5,"5":5,
            "six":6,"6":6,"sept":7,"7":7,"huit":8,"8":8,"neuf":9,"9":9,
            "dix":10,"10":10,"onze":11,"11":11,"douze":12,"12":12,
        }
        generic_month = re.search(
            r"\b(deux|2|trois|3|quatre|4|cinq|5|six|6|sept|7|huit|8|neuf|9|dix|10|onze|11|douze|12)\s+mois\s+"
            r"(plus\s+(tôt|tot|tard)|auparavant)\b", text, re.I
        )
        if resolved_month is None and generic_month and base_month is not None:
            n = month_words[generic_month.group(1).lower()]
            direction = 1 if "tard" in generic_month.group(2).lower() else -1
            resolved_year, resolved_month = shift_month(resolved_year or base_year, base_month, direction*n)
        elif resolved_month is None and _matches_any(text, PREVIOUS_MONTH_PATTERNS):
            resolved_year, resolved_month = shift_month(resolved_year or base_year, base_month, -1)
        elif resolved_month is None and _matches_any(text, NEXT_MONTH_PATTERNS):
            resolved_year, resolved_month = shift_month(resolved_year or base_year, base_month, 1)
        elif resolved_month is None:
            resolved_month = None

        return resolved_month, resolved_quarter, resolved_year

    def contextual_indicators(self, sentence: str) -> list[tuple[str, str]]:
        if not self.last_indicators:
            return []
        last_code = self.last_indicators[0][0]
        if last_code == "gdp_growth" and re.search(
            r"\b(?:l['’])?activit[ée]\b.{0,55}\b(?:cro[iî]tre|croissance|hausse|progress|acc[ée]l[ée]r|ralent)",
            sentence or "", re.I,
        ):
            # In macroeconomic prose, "activity" is a valid local GDP-growth
            # coreference only after an explicit GDP series and an economic
            # change predicate.  It is not treated as GDP in isolation.
            return list(self.last_indicators)
        if last_code == "gdp_growth" and re.search(
            r"\bsc[ée]nario\b.{0,80}\b(?:pr[ée]voit|retient|projection|projet[ée])",
            sentence or "", re.I,
        ):
            return list(self.last_indicators)
        if last_code == "gdp_growth" and re.search(
            r"^.{0,90}\b(?:elle|il)\b.{0,90}\b(?:devrait|pourrait|serait|atteindrait|reviendrait|progresserait|reculerait)",
            sentence or "", re.I,
        ):
            # A bounded pronoun + macro-change modal is a legitimate
            # continuation even when a short introductory phrase precedes it.
            return list(self.last_indicators)
        if last_code == "current_account_balance" and re.search(
            r"\b(?:le\s+)?solde\b.{0,55}\b(?:exc[ée]dentaire|d[ée]ficitaire|positif|n[ée]gatif)",
            sentence or "", re.I,
        ):
            return list(self.last_indicators)
        if re.search(r"\b(?:ce|le)\s+taux\b", sentence or "", re.I):
            return list(self.last_indicators)
        if re.match(
            r"\s*(?:une\s+)?(?:premi[èe]re\s+)?(?:estimation|publication|version|donn[ée]es?\s+r[ée]vis[ée]es?)\b",
            sentence or "", re.I,
        ):
            return list(self.last_indicators)
        if last_code in {"public_revenue", "public_expenditure"}:
            if re.search(r"\brecettes?\b", sentence or "", re.I):
                return [("public_revenue", "Recettes publiques")]
            if re.search(r"\bd[eé]penses?\b", sentence or "", re.I):
                return [("public_expenditure", "Dépenses publiques")]
        temporal_pronoun = bool(re.search(
            r"^\s*(?:(?:sur|au|en|pour|à|a)\b.{0,100})?\b(?:elle|elles|il|ils|ce taux|ce niveau|ce ratio|leur niveau)\b",
            sentence or "", re.I
        ))
        if (COREFERENCE_HINTS.search(sentence) or PERIOD_PREFIX_COREFERENCE.search(sentence)
                or COUNTRY_PREFIX_COREFERENCE.search(sentence) or TEMPORAL_PREFIX_COREFERENCE.search(sentence)
                or RELATIVE_PERIOD_HINTS.search(sentence) or temporal_pronoun):
            return list(self.last_indicators)
        # Economic discourse often abbreviates a previously explicit inflation
        # series as “la hausse sur douze mois”. Allow inheritance only when the
        # immediately preceding series is inflation, never as a generic guess.
        if self.last_indicators and self.last_indicators[0][0] in {
            "inflation_rate", "inflation_annual_average", "inflation_end_period"
        } and re.search(
            r"\b(?:la\s+)?(?:hausse(?:\s+des\s+prix)?|rythme|taux)\s+sur\s+(?:douze|12)\s+mois\b",
            sentence, re.I,
        ):
            return list(self.last_indicators)
        return []
