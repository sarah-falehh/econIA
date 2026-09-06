from __future__ import annotations

from app.services.currency_registry import detect_currency

import re
from dataclasses import asdict, dataclass, fields

from app.services.indicator_catalog import (
    COUNTRIES,
    INDICATORS,
    INDICATOR_LABELS,
    TOPIC_LABELS,
)
from app.services.sentence_classifier import (
    predict_topics,
)
from app.services.semantic_indicator_model import semantic_scores
from app.services.context_resolver import DocumentContext
from app.services.content_selector import select_sentences_heuristic, select_sentences_llm
from app.services.multi_agent_pipeline import run_multi_agent


MONTHS = {
    "janvier": 1, "january": 1, "يناير": 1, "جانفي": 1,
    "février": 2, "february": 2, "فبراير": 2, "فيفري": 2,
    "mars": 3, "march": 3, "مارس": 3,
    "avril": 4, "april": 4, "أبريل": 4, "افريل": 4,
    "mai": 5, "may": 5, "مايو": 5, "ماي": 5,
    "juin": 6, "june": 6, "يونيو": 6, "جوان": 6,
    "juillet": 7, "july": 7, "يوليو": 7, "جويلية": 7,
    "août": 8, "august": 8, "أغسطس": 8, "اوت": 8,
    "septembre": 9, "september": 9, "سبتمبر": 9,
    "octobre": 10, "october": 10, "أكتوبر": 10,
    "novembre": 11, "november": 11, "نوفمبر": 11,
    "décembre": 12, "december": 12, "ديسمبر": 12,
}

QUARTERS = {
    "premier trimestre": 1, "1er trimestre": 1,
    "first quarter": 1, "t1": 1, "q1": 1,
    "الربع الأول": 1, "الربع الاول": 1,

    "deuxième trimestre": 2, "second trimestre": 2,
    "second quarter": 2, "2e trimestre": 2,
    "t2": 2, "q2": 2, "الربع الثاني": 2,

    "troisième trimestre": 3, "third quarter": 3,
    "3e trimestre": 3, "t3": 3, "q3": 3,
    "الربع الثالث": 3,

    "quatrième trimestre": 4, "fourth quarter": 4,
    "4e trimestre": 4, "t4": 4, "q4": 4,
    "الربع الرابع": 4,
}

COMPARISON_MARKERS = [
    "compared with",
    "compared to",
    "higher than",
    "lower than",
    "below",
    "above",
    "whereas",
    "while it stood at",
    "stood at",
    "par rapport à",
    "comparé à",
    "comparée à",
    "contre",
    "مقارنة ب",
    "مقابل",
]

FORECAST_PATTERNS = [
    r"\bexpected to\b",
    r"\bexpect(?:s|ed)?\b",
    r"\bforecast to\b",
    r"\bprojected to\b",
    r"\bis forecast\b",
    r"\bis projected\b",
    r"\bprévu(?:e)?\b",
    r"\bdevrait\b",
    r"\bprojection\b",
    r"\bprévision\b",
    r"متوقع",
    r"من المتوقع",
]

ESTIMATE_PATTERNS = [
    r"\bestimated at\b",
    r"\bestimated that\b",
    r"\bpreliminary estimates\b",
    r"\bestimé(?:e)? à\b",
    r"\bselon les estimations\b",
    r"تقديرات",
]

RELATIVE_CHANGE_PATTERNS = [
    r"\bincreased by\b",
    r"\bgrew by\b",
    r"\bdecreased by\b",
    r"\bfell by\b",
    r"\bdeclined by\b",
    r"\bprogress(?:é|ée)\s+de\b",
    r"\baugment(?:é|ée)\s+de\b",
    r"\bdiminu(?:é|ée)\s+de\b",
    r"\brecul(?:é)?\s+de\b",
    r"ارتفع(?:ت)?\s+بنسبة",
    r"انخفض(?:ت)?\s+بنسبة",
]

DIRECTION_PATTERNS = {
    "increase": [
        r"\bincreased\b", r"\bgrew\b", r"\brose\b",
        r"\bhigher\b", r"\bprogressed\b",
        r"\baugment(?:é|ée)\b", r"\bprogress(?:é|ée)\b",
        r"\bhausse\b", r"ارتفع", r"زيادة",
    ],
    "decrease": [
        r"\bdecreased\b", r"\bfell\b", r"\bdeclined\b",
        r"\blower\b", r"\bnarrowed\b",
        r"\bdiminu(?:é|ée)\b", r"\brecul(?:é)?\b",
        r"\bbaisse\b", r"انخفض", r"تراجع",
    ],
    "stable": [
        r"\bunchanged\b", r"\bremained stable\b",
        r"\bstable\b", r"\bmaintenu\b",
        r"\binchangé\b", r"مستقر", r"دون تغيير",
    ],
}

CONTEXT_BOOSTS = {
    "interest_rate": [
        "central bank", "banque centrale", "policy",
        "key interest rate", "taux directeur",
        "البنك المركزي",
    ],
    "inflation": [
        "food prices", "consumer prices",
        "prix à la consommation", "أسعار",
    ],
    "gdp_growth": [
        "economy expanded", "economic growth",
        "full year", "croissance économique",
        "النمو الاقتصادي",
    ],
    "trade_balance": [
        "trade deficit", "trade surplus",
        "déficit commercial", "balance commerciale",
        "العجز التجاري",
    ],
    "tourism_revenue": [
        "tourism revenues", "tourism receipts",
        "recettes touristiques", "العائدات السياحية",
    ],
    "fdi": [
        "foreign direct investment", "fdi",
        "investissements directs étrangers",
        "الاستثمار الأجنبي المباشر",
    ],
}


@dataclass
class EconomicFact:
    document_id: str
    language: str
    country: str | None

    indicator_code: str
    indicator: str
    indicator_raw: str
    topic: str
    fact_type: str

    value_type: str

    current_value: float | None
    current_value_raw: str | None
    current_unit: str | None
    current_scale: str | None
    current_currency: str | None

    variation_value: float | None
    variation_unit: str | None

    current_month: int | None
    current_quarter: int | None
    current_year: int | None

    reference_value: float | None
    reference_value_raw: str | None
    reference_unit: str | None
    reference_scale: str | None
    reference_currency: str | None

    reference_month: int | None
    reference_quarter: int | None
    reference_year: int | None

    absolute_change: float | None
    relative_change: float | None
    direction: str
    comparison_type: str | None

    source: str | None
    sentence: str
    confidence: float
    needs_review: bool
    review_reason: str | None
    confidence_evidence: list[str] | None = None
    confidence_warnings: list[str] | None = None
    validation_evidence: list[str] | None = None
    validation_warnings: list[str] | None = None
    validation_status: str | None = None
    conflict_status: bool = False
    observation_type: str | None = None
    current_period_label: str | None = None
    reference_period_label: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def split_sentences(text: str) -> list[str]:
    # A single line break in extracted PDFs often occurs in the middle of a
    # sentence. Split only after terminal punctuation or on blank lines.
    normalized = re.sub(r"(?<![.!?؟])\n(?!\n)", " ", text or "")
    chunks = re.split(
        r"(?<=[.!?؟])\s+|\n{2,}",
        normalized,
    )

    return [
        chunk.strip()
        for chunk in chunks
        if len(chunk.strip()) >= 12
    ]



def split_economic_clauses(
    sentence: str,
) -> list[str]:
    """
    Split long sentences when independent indicators
    occur in coordinated clauses, while preserving
    comparison expressions such as 'compared with'.
    """

    separators = [
        r"\s*;\s*",
        r"\s+while\s+(?=[A-Za-z\u0600-\u06FF])",
        r"\s+whereas\s+(?=[A-Za-z\u0600-\u06FF])",
        r"\s+mais\s+(?=[A-Za-zÀ-ÿ\u0600-\u06FF])",
        r"\s+tandis que\s+",
        r"\s+في حين\s+",
        r"\s+بينما\s+",
    ]

    clauses = [sentence]

    for separator in separators:
        next_clauses = []

        for clause in clauses:
            parts = re.split(
                separator,
                clause,
                flags=re.IGNORECASE,
            )

            next_clauses.extend(
                part.strip(" ,;:")
                for part in parts
                if len(part.strip()) >= 12
            )

        clauses = next_clauses or clauses

    return clauses


def normalize_number(raw: str) -> float | None:
    cleaned = raw.replace("\u202f", "").replace(" ", "")
    cleaned = cleaned.replace("٬", "").replace("٫", ".").replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_measurement(
    sentence: str,
    match: re.Match,
) -> dict:
    raw = match.group(0)
    value = normalize_number(raw)

    after = sentence[match.end():match.end() + 65].lower()

    unit = None
    scale = None
    currency = None

    if re.match(
        r"\s*(points? de pourcentage|percentage points?|نقطة مئوية)",
        after,
    ):
        unit = "percentage_point"

    elif re.match(
        r"\s*(%|pour cent|percent|في المائة|بالمائة)",
        after,
    ):
        unit = "%"

    scale_match = re.match(
        r"\s*(billion|billions|milliard|milliards|bn|مليار)",
        after,
    )

    if scale_match:
        scale = "billion"

    else:
        scale_match = re.match(
            r"\s*(million|millions|mn|مليون)",
            after,
        )

        if scale_match:
            scale = "million"

    # Dynamic ISO-4217/CLDR currency detection.  The legacy extractor keeps no
    # country context here, so only explicit/specific currency names are used;
    # the main event pipeline additionally resolves generic denominations from
    # the document country.
    currency = detect_currency(after)

    if currency and not unit:
        unit = currency

    return {
        "raw": raw,
        "value": value,
        "start": match.start(),
        "end": match.end(),
        "unit": unit,
        "scale": scale,
        "currency": currency,
        "is_year": (
            value is not None
            and 1900 <= value <= 2100
            and float(value).is_integer()
        ),
    }


def numeric_mentions(sentence: str) -> list[dict]:
    pattern = (
        r"(?<![\w])[-+]?"
        r"(?:\d{1,3}(?:[ \u202f٬]\d{3})+|\d+)"
        r"(?:[.,٫]\d+)?"
    )

    mentions = []

    for match in re.finditer(pattern, sentence):
        parsed = parse_measurement(sentence, match)

        if parsed["value"] is not None:
            mentions.append(parsed)

    return mentions


def _contains_variant(text: str, variant: str) -> bool:
    escaped = re.escape(variant.lower())

    pattern = (
        rf"(?<![\w\u0600-\u06FF])"
        rf"{escaped}"
        rf"(?![\w\u0600-\u06FF])"
    )

    return bool(
        re.search(
            pattern,
            text.lower(),
            flags=re.UNICODE,
        )
    )


def detect_country(text: str) -> str | None:
    lower = (text or "").lower()

    for country, variants in COUNTRIES.items():
        if any(
            _contains_variant(lower, variant)
            for variant in variants
        ):
            return country

    return None


def candidate_indicators(
    sentence: str,
    language: str,
) -> list[tuple[str, str, float]]:
    lower = sentence.lower()

    language_order = [
        language,
        *[
            lang
            for lang in ("fr", "en", "ar")
            if lang != language
        ],
    ]

    candidates = []

    for code, translations in INDICATORS.items():
        matched_variant = None

        for lang in language_order:
            variants = sorted(
                translations.get(lang, []),
                key=len,
                reverse=True,
            )

            for variant in variants:
                if _contains_variant(sentence, variant):
                    matched_variant = variant
                    break

            if matched_variant:
                break

        if not matched_variant:
            continue

        score = 1.0 + len(matched_variant) / 100

        for context_word in CONTEXT_BOOSTS.get(code, []):
            if context_word in lower:
                score += 0.7

        candidates.append(
            (
                code,
                matched_variant,
                score,
            )
        )

    return candidates


def choose_indicators(
    sentence: str,
    language: str,
) -> list[tuple[str, str]]:
    candidates = candidate_indicators(
        sentence,
        language,
    )

    ai_predictions = predict_topics(
        sentence,
        top_k=3,
    )

    ai_scores = {
        prediction.label: prediction.confidence
        for prediction in ai_predictions
        if prediction.label != "other"
    }

    if not candidates:
        return []

    # Stronger multilingual semantic signal. The transformer is used only
    # among lexically plausible candidates, which keeps the system precise
    # and avoids attaching every number to a vaguely related indicator.
    semantic = semantic_scores(
        sentence,
        [code for code, _, _ in candidates],
    )

    candidate_map = {}

    for code, variant, lexical_score in candidates:
        ai_confidence = ai_scores.get(
            code,
            0.0,
        )
        semantic_confidence = max(0.0, semantic.get(code, 0.0))

        combined_score = (
            lexical_score
            + 1.0 * ai_confidence
            + 2.2 * semantic_confidence
        )

        candidate_map[code] = (
            variant,
            combined_score,
        )

    # FDI is more specific than generic investment.
    if "fdi" in candidate_map:
        candidate_map.pop(
            "investment",
            None,
        )

    # Tourism revenues are more specific than tourism.
    if "tourism_revenue" in candidate_map:
        candidate_map.pop(
            "tourism",
            None,
        )

    # GDP appearing only as denominator is not a GDP observation.
    if re.search(
        r"%\s*(?:of\s+)?gdp\b|%\s*du\s*pib\b",
        sentence.lower(),
    ):
        if len(candidate_map) > 1:
            candidate_map.pop(
                "gdp_growth",
                None,
            )

    # Trade balance without a numeric value near it is qualitative only.
    # Keep exports/imports, but do not attach their numeric value to trade balance.
    if (
        "trade_balance" in candidate_map
        and (
            "exports" in candidate_map
            or "imports" in candidate_map
        )
    ):
        candidate_map.pop(
            "trade_balance",
            None,
        )

    ranked = sorted(
        candidate_map.items(),
        key=lambda item: item[1][1],
        reverse=True,
    )

    if ranked:
        best_score = ranked[0][1][1]

        ranked = [
            item
            for item in ranked
            if (
                item[1][1] >= best_score - 0.85
                or ai_scores.get(
                    item[0],
                    0.0,
                ) >= 0.20
            )
        ]

    return [
        (code, variant_score[0])
        for code, variant_score in ranked
    ]


def extract_period(
    fragment: str,
) -> tuple[int | None, int | None, int | None]:
    lower = (fragment or "").lower()

    month = next(
        (
            number
            for name, number in MONTHS.items()
            if _contains_variant(lower, name)
        ),
        None,
    )

    quarter = next(
        (
            number
            for name, number in QUARTERS.items()
            if _contains_variant(lower, name)
        ),
        None,
    )

    years = re.findall(
        r"\b(?:19|20)\d{2}\b",
        lower,
    )

    year = int(years[0]) if years else None

    return month, quarter, year


def detect_fact_type(sentence: str) -> str:
    lower = sentence.lower()

    for pattern in FORECAST_PATTERNS:
        if re.search(pattern, lower):
            return "forecast"

    for pattern in ESTIMATE_PATTERNS:
        if re.search(pattern, lower):
            return "estimate"

    return "observed"


def detect_direction(sentence: str) -> str:
    lower = sentence.lower()

    for direction, patterns in DIRECTION_PATTERNS.items():
        if any(
            re.search(pattern, lower)
            for pattern in patterns
        ):
            return direction

    return "unknown"


def split_comparison(
    sentence: str,
) -> tuple[str, str | None, str | None]:
    lower = sentence.lower()

    for marker in COMPARISON_MARKERS:
        index = lower.find(marker)

        if index >= 0:
            return (
                sentence[:index].strip(" ,;:"),
                sentence[
                    index + len(marker):
                ].strip(" ,;:"),
                marker,
            )

    from_to = re.search(
        r"\bfrom\b(.+?)\bto\b(.+)",
        sentence,
        flags=re.IGNORECASE,
    )

    if from_to:
        return (
            from_to.group(2).strip(),
            from_to.group(1).strip(),
            "from_to",
        )

    return sentence, None, None


def nearest_value(
    fragment: str | None,
    indicator_raw: str | None = None,
) -> dict | None:
    if not fragment:
        return None

    mentions = [
        mention
        for mention in numeric_mentions(fragment)
        if not mention["is_year"]
    ]

    if not mentions:
        return None

    if not indicator_raw:
        return mentions[0]

    indicator_position = fragment.lower().find(
        indicator_raw.lower()
    )

    if indicator_position < 0:
        return mentions[0]

    return min(
        mentions,
        key=lambda mention: abs(
            mention["start"] - indicator_position
        ),
    )


def detect_value_type(
    sentence: str,
    reference_value: float | None,
    current_unit: str | None,
) -> str:
    lower = sentence.lower()

    if current_unit == "percentage_point":
        return "absolute_change"

    if (
        current_unit == "%"
        and reference_value is None
        and any(
            re.search(pattern, lower)
            for pattern in RELATIVE_CHANGE_PATTERNS
        )
    ):
        return "relative_change"

    return "level"


def compute_changes(
    current_value: float | None,
    reference_value: float | None,
) -> tuple[float | None, float | None, str]:
    if current_value is None or reference_value is None:
        return None, None, "unknown"

    absolute_change = round(
        current_value - reference_value,
        4,
    )

    relative_change = (
        None
        if reference_value == 0
        else round(
            (
                absolute_change
                / abs(reference_value)
            )
            * 100,
            2,
        )
    )

    if absolute_change > 0:
        direction = "increase"

    elif absolute_change < 0:
        direction = "decrease"

    else:
        direction = "stable"

    return (
        absolute_change,
        relative_change,
        direction,
    )


def detect_comparison_type(
    reference_month: int | None,
    reference_quarter: int | None,
    reference_year: int | None,
    sentence: str,
) -> str | None:
    lower = sentence.lower()

    if (
        "year-on-year" in lower
        or "same period last year" in lower
        or "one year earlier" in lower
        or "glissement annuel" in lower
    ):
        return "year_over_year"

    if reference_month is not None:
        return "monthly"

    if reference_quarter is not None:
        return "quarterly"

    if reference_year is not None:
        return "annual"

    return None


def confidence_score(
    indicator_code: str,
    indicator_raw: str,
    country: str | None,
    value_found: bool,
    unit_found: bool,
    period_found: bool,
    reference_found: bool,
    source: str | None,
    sentence: str,
) -> float:
    score = 0.30

    score += 0.18 if value_found else 0
    score += 0.10 if unit_found else 0
    score += 0.08 if period_found else 0
    score += 0.08 if reference_found else 0
    score += 0.07 if country else 0
    score += 0.04 if source else 0
    score += min(
        len(indicator_raw) / 200,
        0.08,
    )

    if any(
        context_word in sentence.lower()
        for context_word in CONTEXT_BOOSTS.get(
            indicator_code,
            [],
        )
    ):
        score += 0.07

    return round(
        min(score, 0.96),
        2,
    )


def review_status(
    value_type: str,
    country: str | None,
    value_found: bool,
    unit_found: bool,
    current_period_found: bool,
    comparison_marker: str | None,
    reference_value: float | None,
    confidence: float,
    fact_type: str,
) -> tuple[bool, str | None]:
    """Flag only records that truly block business use.

    Missing country, unit or period are useful warnings but are not sufficient
    on their own to send hundreds of otherwise readable facts to manual review.
    Forecasts are valid facts and are labelled as such instead of being rejected.
    """
    blocking = []
    warnings = []

    if not value_found:
        blocking.append("Valeur non détectée")

    if (
        comparison_marker
        and value_type == "level"
        and reference_value is None
    ):
        blocking.append("Comparaison incomplète")

    if confidence < 0.64:
        blocking.append("Confiance insuffisante")

    if country is None:
        warnings.append("Pays non détecté")
    if not unit_found:
        warnings.append("Unité non détectée")
    if not current_period_found:
        warnings.append("Période non précisée")
    if fact_type == "forecast":
        warnings.append("Prévision")

    reasons = blocking + warnings
    return bool(blocking), "; ".join(reasons) if reasons else None


def extract_facts_from_document(
    document: dict,
    *,
    selection_mode: str = "strict",
    ollama_model: str = "qwen2.5:7b",
) -> list[EconomicFact]:
    text = document.get("text", "")
    language = document.get("language") or "fr"

    if selection_mode == "multi_agent":
        allowed = {field.name for field in fields(EconomicFact)}
        return [EconomicFact(**{key: value for key, value in row.items() if key in allowed})
                for row in run_multi_agent(document, model=ollama_model)]
    document_id = document.get("document_id", "")
    source = document.get("source")

    global_country = detect_country(
        f"{document.get('title', '')} {text[:1800]}"
    )
    context = DocumentContext.from_document(document)
    context.last_country = global_country

    facts = []

    raw_sentences = split_sentences(text)
    if selection_mode == "ollama":
        selection = select_sentences_llm(raw_sentences, model=ollama_model)
    elif selection_mode == "legacy":
        selection = None
    else:
        selection = select_sentences_heuristic(raw_sentences)
    selected_sentences = raw_sentences if selection is None else selection.kept

    for full_sentence in selected_sentences:
        # An explicit period updates the document memory before clauses are read.
        sentence_period = extract_period(full_sentence)
        context.remember_explicit_period(*sentence_period)

        clauses = split_economic_clauses(full_sentence)

        for sentence in clauses:
            indicators = choose_indicators(sentence, language)

            # Resolve simple inter-sentence coreference such as
            # "L'année précédente, elles..." after "les exportations...".
            if not indicators:
                indicators = context.contextual_indicators(sentence)

            if not indicators:
                continue

            sentence_country = (
                detect_country(sentence)
                or detect_country(full_sentence)
                or context.last_country
                or global_country
            )
            if sentence_country:
                context.last_country = sentence_country

            fact_type = detect_fact_type(sentence)
            current_part, reference_part, marker = split_comparison(sentence)

            for indicator_code, indicator_raw in indicators:
                current_mention = nearest_value(current_part, indicator_raw)

                if indicator_code == "trade_balance" and current_mention is None:
                    continue
                if current_mention is None:
                    continue

                reference_mention = nearest_value(reference_part)

                current_period_raw = extract_period(current_part)
                reference_period_raw = extract_period(reference_part or "")

                current_month, current_quarter, current_year = context.resolve_period(
                    current_part,
                    *current_period_raw,
                    inherit=True,
                )

                # Reference periods inherit the current period, then relative
                # expressions are applied only to the reference fragment.
                saved_year = context.current_year
                saved_quarter = context.current_quarter
                saved_month = context.current_month
                context.current_year = current_year or context.current_year
                context.current_quarter = current_quarter or context.current_quarter
                context.current_month = current_month or context.current_month
                reference_month, reference_quarter, reference_year = context.resolve_period(
                    reference_part or "",
                    *reference_period_raw,
                    inherit=reference_part is not None,
                )
                context.current_year = saved_year
                context.current_quarter = saved_quarter
                context.current_month = saved_month

                current_value = current_mention["value"]
                current_unit = current_mention["unit"]
                current_scale = current_mention["scale"]
                current_currency = current_mention["currency"]

                reference_value = reference_mention["value"] if reference_mention else None
                reference_unit = reference_mention["unit"] if reference_mention else None
                reference_scale = reference_mention["scale"] if reference_mention else None
                reference_currency = reference_mention["currency"] if reference_mention else None

                value_type = detect_value_type(sentence, reference_value, current_unit)
                variation_value = None
                variation_unit = None

                if value_type in {"relative_change", "absolute_change"}:
                    variation_value = current_value
                    variation_unit = current_unit
                    current_value = None
                    current_unit = None

                absolute_change, relative_change, numeric_direction = compute_changes(
                    current_value,
                    reference_value,
                )
                direction = numeric_direction
                if direction == "unknown":
                    direction = detect_direction(sentence)
                if value_type == "relative_change":
                    relative_change = variation_value
                if value_type == "absolute_change":
                    absolute_change = variation_value

                comparison_type = detect_comparison_type(
                    reference_month,
                    reference_quarter,
                    reference_year,
                    sentence,
                )
                current_period_found = any([current_month, current_quarter, current_year])
                value_found = current_value is not None or variation_value is not None
                unit_found = any([current_unit, variation_unit, current_scale, current_currency])

                confidence = confidence_score(
                    indicator_code=indicator_code,
                    indicator_raw=indicator_raw,
                    country=sentence_country,
                    value_found=value_found,
                    unit_found=unit_found,
                    period_found=current_period_found,
                    reference_found=reference_value is not None,
                    source=source,
                    sentence=sentence,
                )

                # Context resolution is useful but slightly less certain than an
                # explicit lexical mention of the indicator.
                if (indicator_code, indicator_raw) in context.last_indicators and not choose_indicators(sentence, language):
                    confidence = round(max(0.0, confidence - 0.06), 2)

                needs_review, review_reason = review_status(
                    value_type=value_type,
                    country=sentence_country,
                    value_found=value_found,
                    unit_found=unit_found,
                    current_period_found=current_period_found,
                    comparison_marker=marker,
                    reference_value=reference_value,
                    confidence=confidence,
                    fact_type=fact_type,
                )

                display_language = language if language in ("fr", "en", "ar") else "fr"

                facts.append(EconomicFact(
                    document_id=document_id,
                    language=language,
                    country=sentence_country,
                    indicator_code=indicator_code,
                    indicator=INDICATOR_LABELS[indicator_code][display_language],
                    indicator_raw=indicator_raw,
                    topic=TOPIC_LABELS.get(indicator_code, "Autre"),
                    fact_type=fact_type,
                    value_type=value_type,
                    current_value=current_value,
                    current_value_raw=current_mention["raw"] if value_type == "level" else None,
                    current_unit=current_unit,
                    current_scale=current_scale,
                    current_currency=current_currency,
                    variation_value=variation_value,
                    variation_unit=variation_unit,
                    current_month=current_month,
                    current_quarter=current_quarter,
                    current_year=current_year,
                    reference_value=reference_value,
                    reference_value_raw=reference_mention["raw"] if reference_mention else None,
                    reference_unit=reference_unit,
                    reference_scale=reference_scale,
                    reference_currency=reference_currency,
                    reference_month=reference_month,
                    reference_quarter=reference_quarter,
                    reference_year=reference_year,
                    absolute_change=absolute_change,
                    relative_change=relative_change,
                    direction=direction,
                    comparison_type=comparison_type,
                    source=source,
                    sentence=sentence,
                    confidence=confidence,
                    needs_review=needs_review,
                    review_reason=review_reason,
                ))

            # Remember only explicit indicators after the whole clause has been processed.
            explicit_indicators = choose_indicators(sentence, language)
            if explicit_indicators:
                context.last_indicators = explicit_indicators
            context.remember_explicit_period(*extract_period(sentence))

    return facts

