from __future__ import annotations

import re
import time
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Callable

from app.services.indicator_registry import indicator_metadata, detect_country, build_series_id, COUNTRIES
from app.services.country_registry import country_mentions
from app.services.currency_registry import detect_currency, currency_text_pattern, current_currency_for_country
from app.services.context_resolver import DocumentContext, COREFERENCE_HINTS, RELATIVE_PERIOD_HINTS
from app.services.evidence_validation import score_event, finalize_status
from app.services.event_segmenter import split_economic_clauses
from app.services.structured_table_extractor import extract_structured_table_events

_LAST_TRACE: dict[str, Any] = {}

INDICATOR_LABELS = {
    "public_debt_ratio": "Dette publique (% du PIB)",
    "public_debt_stock": "Encours de la dette publique",
    "external_debt_ratio": "Dette publique extérieure (% du PIB)",
    "internal_debt_stock": "Encours de la dette publique intérieure",
    "external_debt_stock": "Encours de la dette publique extérieure",
    "internal_debt_ratio": "Dette publique intérieure (% du PIB)",
    "budget_deficit": "Déficit budgétaire",
    "primary_balance": "Solde budgétaire primaire",
    "gdp_growth": "Taux de croissance du PIB (variation annuelle)",
    "inflation_rate": "Taux d’inflation des prix à la consommation",
    "inflation_annual_average": "Taux d’inflation des prix à la consommation (moyenne annuelle)",
    "inflation_end_period": "Taux d’inflation des prix à la consommation (fin de période)",
    "core_inflation": "Taux d’inflation sous-jacente",
    "food_inflation": "Taux d’inflation des produits alimentaires",
    "manufactured_goods_inflation": "Variation des prix des produits manufacturés",
    "trade_balance": "Solde commercial",
    "trade_coverage_ratio": "Taux de couverture des importations par les exportations",
    "cpi_monthly_change": "Variation mensuelle de l’indice des prix à la consommation",
    "exports": "Exportations de biens et services",
    "imports": "Importations de biens et services",
    "unemployment_rate": "Taux de chômage",
    "activity_rate": "Taux d’activité",
    "current_account_balance": "Solde du compte courant (% du PIB)",
    "fdi_growth": "Variation des investissements directs étrangers (IDE)",
    "exports_growth": "Taux de variation des exportations de biens et services",
    "imports_growth": "Taux de variation des importations de biens et services",
    "foreign_direct_investment": "Investissements directs étrangers (IDE)",
    "foreign_exchange_reserves": "Réserves officielles de change",
    "public_spending_ratio": "Dépenses publiques en % du PIB",
    "public_revenue": "Recettes publiques",
    "public_expenditure": "Dépenses publiques",
    "external_debt_share": "Part de la dette extérieure dans l’encours public",
    "internal_debt_share": "Part de la dette intérieure dans l’encours public",
    "public_debt_state_share": "Part de la dette publique dans la dette de l’État",
    "policy_rate": "Taux directeur de la banque centrale",
    "money_market_rate": "Taux moyen du marché monétaire (TMM)",
    "real_money_market_rate": "Taux moyen du marché monétaire réel",
    "nominal_effective_exchange_rate": "Variation du taux de change effectif nominal (TCEN)",
    "real_effective_exchange_rate": "Variation du taux de change effectif réel (TCER)",
    "unit_labor_cost": "Variation du coût salarial unitaire (CSU)",
    "nominal_wage_rate": "Variation du taux de salaire nominal",
    "labor_productivity": "Variation de la productivité du travail",
    "wage_cost_margin": "Variation de la marge sur coût salarial",
    "competitiveness_index": "Variation de l’indicateur synthétique de compétitivité",
    "competitor_prices": "Variation des prix des concurrents",
    "exchange_rate_change": "Variation du taux de change bilatéral",
    "value_added_price": "Variation du prix de la valeur ajoutée",
    "relative_price_change": "Variation des prix relatifs",
    "unit_labor_cost_level": "Coût salarial unitaire",
    "purchasing_power_growth": "Variation du pouvoir d’achat des ménages",
    "economic_cost_level": "Niveau de coût économique (concept à préciser)",
}

TOPICS = {
    "public_debt_ratio": "dette_publique",
    "public_debt_stock": "dette_publique",
    "external_debt_ratio": "dette_exterieure",
    "internal_debt_stock": "dette_interieure",
    "external_debt_stock": "dette_exterieure",
    "internal_debt_ratio": "dette_interieure",
    "budget_deficit": "finances_publiques",
    "primary_balance": "finances_publiques",
    "gdp_growth": "croissance",
    "inflation_rate": "prix",
    "inflation_annual_average": "prix",
    "inflation_end_period": "prix",
    "core_inflation": "prix",
    "food_inflation": "prix",
    "trade_balance": "commerce_exterieur",
    "trade_coverage_ratio": "commerce_exterieur",
    "cpi_monthly_change": "prix",
    "exports": "commerce_exterieur",
    "imports": "commerce_exterieur",
    "unemployment_rate": "emploi",
    "activity_rate": "emploi",
    "current_account_balance": "secteur_exterieur",
    "fdi_growth": "investissement",
    "foreign_direct_investment": "investissement",
    "foreign_exchange_reserves": "reserves_de_change",
    "public_spending_ratio": "finances_publiques",
    "public_revenue": "finances_publiques",
    "public_expenditure": "finances_publiques",
    "external_debt_share": "dette_exterieure",
    "internal_debt_share": "dette_interieure",
    "public_debt_state_share": "dette_publique",
    "policy_rate": "politique_monetaire", "money_market_rate": "politique_monetaire",
    "real_money_market_rate": "politique_monetaire",
    "nominal_effective_exchange_rate": "taux_de_change", "real_effective_exchange_rate": "taux_de_change",
    "exchange_rate_change": "taux_de_change", "unit_labor_cost": "competitivite",
    "nominal_wage_rate": "competitivite", "labor_productivity": "competitivite",
    "wage_cost_margin": "competitivite", "competitiveness_index": "competitivite",
    "competitor_prices": "competitivite",
    "value_added_price": "competitivite",
    "relative_price_change": "taux_de_change", "unit_labor_cost_level": "competitivite",
    "purchasing_power_growth": "revenus_menages",
    "economic_cost_level": "competitivite",
}

_PAGE_MARKER = re.compile(r"\[\[PAGE\s+(\d+)\]\]")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_NUMBER_TOKEN = r"(?:\d{1,3}(?:[.\s\u00a0\u202f]\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)"
_ISO_CURRENCY_CODES = r"(?-i:[A-Z]{3})"
_GENERIC_CURRENCY_WORDS = (
    r"(?:dollars?|dinars?|dirhams?|pesos?|roupies?|rupiah|shillings?|couronnes?|kroner?|"
    r"c[eé]dis?|wons?|yens?|reais?|livres?|rands?|francs?\s+CFA|FCFA|F\s*CFA|"
    r"دراهم?|درهم|دنانير|دينار|دولارات?|دولار|دوالرات?|دوالر)"
)
_MEASURE = re.compile(
    rf"(?P<num>[-+]?{_NUMBER_TOKEN})\s*"
    r"(?P<scale>milliards?|millions?|MD|مليارات?|مليار|ملايين|مليون)?\s*"
    rf"(?:de\s+)?(?P<currency>{_ISO_CURRENCY_CODES}|{_GENERIC_CURRENCY_WORDS}(?:\s+(?!(?:en|au|aux|du|de|dans|pour|contre|apres|après|avant|sur)\b)[A-Za-zÀ-ÿ'’.-]+){{0,2}})?\s*"
    r"(?P<unit>%\s*(?:du\s+PIB)?|points?(?:\s+de\s+pourcentage)?|jours?(?:\s+d['’]importation)?|نقطة\s+مئوية|أيام?)?",
    re.I,
)


_REJECT = re.compile(
    r"(?:table\s+des\s+mati[eè]res|liste\s+des\s+(?:tableaux|graphiques|figures)|"
    r"bibliographie|r[eé]f[eé]rences\s+bibliographiques|annexe\s+\d+|"
    r"tableau\s+\d+\s*:\s*estimation|coefficient|statistique\s+t|significativit[eé]|"
    r"racine\s+unitaire|dickey\s+fuller|mod[eè]le\s+quadratique|"
    r"l['’]équation\s+suivante|tels\s+que\s*:|constante\s+à\s+d[eé]terminer|"
    r"courbe\s+d['’]armey|proportion\s+optimale|seuil\s+optimal|"
    r"une\s+augmentation\s+d['’]un\s+point|R\s*[²2]\s*=|TCROH\s*=|"
    r"au-del[àa]\s+d['’]un\s+seuil|seuil\s+bien\s+pr[eé]cis|investigations\s+r[eé]alis[eé]es|"
    r"تدريجات\s+المحور|معامل\s+الانحدار|قيمة\s*R\s*[²2])",
    re.I,
)

_NARRATIVE = re.compile(
    r"\b(?:atteint|atteindre|atteignait|atteignaient|etait|etaient|[ée]tait|[ée]taient|indique|indiquait|pass[ée]s?\s+de|passant\s+de|s['’]est\s+[ée]tabli|"
    r"s['’][ée]levait|se\s+sont\s+(?:[ée]tablis|etablis)|a\s+enregistr[ée]|repr[ée]sentait|[ée]quivalent|pr[ée]vu|"
    r"estim[ée]|estimee|contre|respectivement|augment[ée]|augmente|diminu[ée]|diminue|recul[ée]|recule|progress[ée]|progresse|progression|"
    r"baiss[ée]|abaiss[ée]|maintenu(?:e|s)?|relev[ée]|pr[ée]voit|retient|hausse|baisse|ressortait|ressort|remonterait|ralentirait|serait|devrait|pour\s+atteindre|"
    r"بلغ(?:ت)?|سجل(?:ت)?|استقر|ارتفع(?:ت)?|انخفض(?:ت)?|تباطأ|تراجع|تحول|قُ?درت|خفض(?:ه)?|أبقى|يتوقع|المتوقع|مقابل|مقارنة)",
    re.I,
)


def get_last_trace() -> dict[str, Any]:
    return _LAST_TRACE


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _arabic_dominant(text: str, threshold: float = 0.35) -> bool:
    arabic = len(re.findall(r"[\u0600-\u06FF]", text or ""))
    letters = len(re.findall(r"[A-Za-zÀ-ÿ\u0600-\u06FF]", text or ""))
    return bool(letters and arabic / letters >= threshold)


def _parse_number(raw: str) -> float | None:
    token_match = re.search(rf"[-+]?{_NUMBER_TOKEN}", raw or "")
    if not token_match:
        return None
    token = re.sub(r"[\s\u00a0\u202f]", "", token_match.group(0))
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        token = token.replace(",", ".")
    elif "." in token:
        parts = token.split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]) and len(parts[0]) <= 3:
            token = "".join(parts)
    try:
        return float(Decimal(token))
    except (InvalidOperation, ValueError):
        return None


def _split_pages(text: str) -> list[tuple[int | None, str]]:
    matches = list(_PAGE_MARKER.finditer(text or ""))
    if not matches:
        return [(None, (text or "").strip())]
    out: list[tuple[int | None, str]] = []
    for idx, match in enumerate(matches):
        page = int(match.group(1))
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        out.append((page, (text[match.end():end] or "").strip()))
    return out


def _looks_like_heading(line: str) -> bool:
    """Conservative hard boundary detector for PDF section headings."""
    t = re.sub(r"\s+", " ", line or "").strip()
    if not t or len(t) > 110 or re.search(r"[.!?]$", t) or _MEASURE.search(t):
        return False
    mentions = _country_mentions(t)
    if mentions and len(re.findall(r"\b\w+\b", t, re.UNICODE)) <= 10:
        if re.search(r"[\u0600-\u06FF]", t):
            # A short RTL line ending in a country is often merely the wrapped
            # tail of a comparison ("... in Morocco and Tunisia"), not a
            # country heading. Only an essentially standalone name is a reset.
            remainder = t
            for start, end, _, _ in reversed(mentions):
                remainder = remainder[:start] + remainder[end:]
            remainder = re.sub(r"[^\u0600-\u06FF]+", " ", remainder).strip()
            if re.search(r"\b(?:في|مقابل|من|إلى|الى|و)\b", remainder) or len(re.findall(r"[\u0600-\u06FF]+", remainder)) > 2:
                return False
        return True
    return bool(re.match(
        r"^(?:chapitre\s+\d+|perspectives?|activité|activite|prix|emploi|"
        r"finances? publiques?|secteur extérieur|secteur exterieur|commerce|"
        r"investissement|tableau structuré|tableau structure|méthodologie|methodologie|"
        r"النمو\s+والأسعار|سوق\s+العمل|القطاع\s+الخارجي|السياسة\s+النقدية|المالية\s+العامة)\b",
        t, re.I))


def _sentences(text: str) -> list[str]:
    """Segment sentences and carry a country heading into the next body sentence.

    Headings are hard boundaries (they never join backward) but they are also
    useful context. A compact internal marker is attached to the first sentence
    after a country heading and stripped by ``_candidate_sentences``.
    """
    units: list[str] = []
    buffer = ""
    pending_country: tuple[str, str] | None = None

    def emit(chunk: str) -> None:
        nonlocal pending_country
        arabic = bool(re.search(r"[\u0600-\u06FF]", chunk))
        boundary = r"(?<=[.!?؟])\s+" if arabic else r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-ÞÉÈÊÎÔÛÇ])"
        parts = [p.strip() for p in re.split(boundary, chunk) if p.strip()]
        for part in parts:
            if pending_country is not None:
                name, iso3 = pending_country
                units.append(f"[[SECTION_COUNTRY:{iso3}:{name}]] {part}")
                pending_country = None
            else:
                units.append(part)

    for raw_line in (text or "").splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            continue
        if _looks_like_heading(line):
            if buffer:
                emit(buffer)
                buffer = ""
            mentions = _country_mentions(line)
            if mentions:
                _, _, name, iso3 = mentions[0]
                pending_country = (name, iso3)
            continue

        buffer = f"{buffer} {line}".strip() if buffer else line
        boundary = r"(?<=[.!?؟])\s+" if re.search(r"[\u0600-\u06FF]", buffer) else r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-ÞÉÈÊÎÔÛÇ])"
        parts = re.split(boundary, buffer)
        if len(parts) > 1:
            for finished in parts[:-1]:
                emit(finished)
            buffer = parts[-1]

    if buffer:
        emit(buffer)
    return [c.strip() for c in units if len(re.sub(r"^\[\[SECTION_COUNTRY:[^\]]+\]\]\s*", "", c)) >= 18]


def _candidate_sentences(document_text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    arabic_cross_page_carrier: str | None = None
    for page, page_text in _split_pages(document_text):
        page_is_arabic = _arabic_dominant(page_text)
        semantic_carrier: str | None = arabic_cross_page_carrier if page_is_arabic else None
        for sentence in _sentences(page_text):
            arabic_sentence = _arabic_dominant(sentence)
            section_country = section_iso3 = None
            marker = re.match(r"^\[\[SECTION_COUNTRY:([A-Z]{3}):([^\]]+)\]\]\s*", sentence)
            if marker:
                section_iso3, section_country = marker.group(1), marker.group(2)
                sentence = sentence[marker.end():].strip()
            # Detach footnotes that PDF reconstruction appended to a complete
            # narrative sentence. Their citations, issue numbers and dates are
            # audited as document metadata, never bound to the economic fact.
            sentence = re.split(
                r"(?<=[.!?])\s+\d{1,3}\s+(?=(?:Voir|Source|Note|PARIENTY|[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ'’.-]+\s+[A-Z]))",
                sentence, maxsplit=1, flags=re.I
            )[0].strip()
            # PDF headings and footers sometimes merge with the first paragraph.
            # Keep the actual narrative clause beginning with an explicit year.
            narrative_starts = list(re.finditer(r"\bEn\s+(?:19|20)\d{2}\s*,", sentence, re.I))
            if narrative_starts and re.search(r"\b(?:Page|Chapitre|rapport\s+synth[ée]tique)\b", sentence, re.I):
                sentence = sentence[narrative_starts[-1].start():].strip()
            if _REJECT.search(sentence):
                continue
            # PDF chart extraction may flatten a title, all Y-axis ticks and
            # all X-axis years into one pseudo-sentence. Axis ticks are layout
            # metadata, not observations.
            if re.search(r"\b(?:graphique|figure)\s*\d+\s*:", sentence, re.I):
                numeric_tokens = re.findall(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)?(?:\s*%)?", sentence)
                if (len(re.findall(r"[-+]?\d+(?:[.,]\d+)?\s*%", sentence)) >= 5 and len(_YEAR.findall(sentence)) >= 5) or len(numeric_tokens) >= 12:
                    continue
            if re.search(r"\bpoids\s+de\s+cette\s+dette\b", sentence, re.I):
                continue
            measurements = [m for m in _MEASURE.finditer(sentence) if m.group("unit") or m.group("scale") or m.group("currency")]
            if arabic_sentence and "%" in sentence and _indicator_mentions(sentence):
                measurements.extend(m for m in _MEASURE.finditer(sentence)
                                    if not (m.group("unit") or m.group("scale") or m.group("currency"))
                                    and not 1900 <= float(m.group("num").replace(",", ".")) <= 2100)
            if not measurements:
                if _indicator_mentions(sentence):
                    semantic_carrier = sentence
                continue
            temporal_coreference = bool(re.search(
                r"^\s*(?:(?:sur|au|en|pour|à|a)\b.{0,90})?\b(?:elle|elles|il|ils|ce taux|ce niveau|ce ratio|leur niveau)\b",
                sentence, re.I
            ))
            if not _NARRATIVE.search(sentence) and not re.search(
                r"\b(?:dette|endettement|d[eé]ficit|exc[eé]dent|solde|compte\s+courant|inflation|croissance|exportations?|importations?|ch[oô]mage|r[eé]serves|investissements?|ide|recettes?|d[eé]penses?|الناتج|النمو|التضخم|البطالة|الميزانية|الصادرات|الواردات|الحساب\s+الجاري|الاستثمارات|الفائدة|الاحتياطيات)\b",
                sentence,
                re.I,
            ) and not COREFERENCE_HINTS.search(sentence) and not RELATIVE_PERIOD_HINTS.search(sentence) and not temporal_coreference and not (arabic_sentence and semantic_carrier):
                continue
            clauses = split_economic_clauses(sentence)
            for clause in clauses:
                out.append({
                    "page": page,
                    "text": clause.text,
                    "parent_sentence": sentence,
                    "clause_index": clause.index,
                    "section_country": section_country if clause.index == 0 else None,
                    "section_country_iso3": section_iso3 if clause.index == 0 else None,
                    "semantic_context_sentence": semantic_carrier,
                })
                # A heading applies to the section, not merely the first clause.
                # The runtime DocumentContext retains it after clause 0.
            # RTL PDFs frequently detach the semantic head from its numerical
            # continuation. This carrier is deliberately Arabic-only.
            if arabic_sentence and _indicator_mentions(sentence):
                semantic_carrier = sentence
        arabic_cross_page_carrier = semantic_carrier if page_is_arabic else None
    return out




def _country_mentions(sentence: str) -> list[tuple[int, int, str, str]]:
    """Return explicit country/demonym mentions from the dynamic ISO registry."""
    return country_mentions(sentence)


_GEOGRAPHY_GROUPS = [
    (r"\bPECO\b|pays\s+d['’]Europe\s+centrale\s+et\s+orientale", "PECO"),
    (r"\bconcurrents?\s+asiatiques?\b|\bpays\s+asiatiques?\b", "Concurrents asiatiques"),
    (r"\bzone\s+euro\b", "Zone euro"),
    (r"\bUnion\s+europ[ée]enne\b|\bUE\b", "Union européenne"),
    (r"\bMENA\b|Moyen[- ]Orient\s+et\s+Afrique\s+du\s+Nord", "MENA"),
    (r"\bAfrique\s+subsaharienne\b", "Afrique subsaharienne"),
    (r"\bOCDE\b", "OCDE"),
]


def _group_for_measure(sentence: str, start: int, end: int) -> tuple[str | None, str]:
    mentions=[]
    for pattern, name in _GEOGRAPHY_GROUPS:
        mentions.extend((m.start(), m.end(), name) for m in re.finditer(pattern, sentence, re.I))
    if not mentions:
        return None, "missing"
    next_measure = _MEASURE.search(sentence, end)
    next_pos = next_measure.start() if next_measure else len(sentence)
    following = [m for m in mentions if end <= m[0] < next_pos and m[0]-end <= 55]
    if following:
        return min(following, key=lambda m:m[0]-end)[2], "explicit_group_local"
    previous_measure = [m for m in _MEASURE.finditer(sentence) if m.end() <= start]
    boundary = previous_measure[-1].end() if previous_measure else 0
    preceding = [m for m in mentions if boundary <= m[1] <= start]
    if preceding:
        return max(preceding, key=lambda m:m[1])[2], "explicit_group_local"
    return None, "missing"


def _country_for_measure(sentence: str, start: int, end: int, fallback: str | None = None) -> tuple[str | None, str | None, str]:
    """Bind a value to the closest local country, including post-value lists.

    Examples: ``3,8 % au Maroc, 3,5 % en Algérie`` and ``exportations
    marocaines ... 5,8 %``. Explicit local evidence always beats document
    context.
    """
    mentions = _country_mentions(sentence)
    if not mentions:
        name, iso3 = detect_country("", fallback)
        return name, iso3, "context" if name else "missing"
    next_measure = _MEASURE.search(sentence, end)
    next_pos = next_measure.start() if next_measure else len(sentence)
    # A country immediately following the value is the strongest list binding.
    following = [m for m in mentions if end <= m[0] < next_pos and m[0] - end <= 45]
    following = [m for m in following if re.search(r"(?:^|[,;]\s*)(?:en|au|aux)\s*$", sentence[end:m[0]], re.I)]
    if following:
        m = min(following, key=lambda x: x[0] - end)
        return m[2], m[3], "explicit_local"
    # Otherwise use the closest country preceding the current value, but do not
    # cross another numeric measure: this prevents the previous list item from
    # leaking into the next one.
    prev_measure_matches = [m for m in _MEASURE.finditer(sentence) if m.end() <= start]
    prev_end = prev_measure_matches[-1].end() if prev_measure_matches else 0
    preceding = [m for m in mentions if prev_end <= m[1] <= start]
    if preceding:
        m = max(preceding, key=lambda x: x[1])
        return m[2], m[3], "explicit_local"
    # Within a semicolon-delimited clause, the most recent explicit country
    # remains authoritative for subsequent coordinated values. This handles:
    # "... Portugal ... ; la Pologne affichait respectivement 2,9 %, 3,7 % et 3,1 %".
    clause_start = max(sentence.rfind(";", 0, start), sentence.rfind(":", 0, start))
    clause_mentions = [m for m in mentions if m[1] <= start and m[0] > clause_start]
    if clause_mentions:
        m = clause_mentions[-1]
        return m[2], m[3], "explicit_clause"

    # Sentence-level country remains stronger than inherited document context.
    name, iso3 = detect_country(sentence, fallback)
    return name, iso3, "explicit_sentence" if detect_country(sentence, None)[0] else ("context" if name else "missing")


def _clause_semantic_hint(clause: str, parent_sentence: str | None = None) -> list[tuple[str, str]]:
    """Return high-confidence semantic hints from a clause + its parent block.

    This is deliberately domain-based rather than document-specific. It lets a
    split atomic clause keep the semantic frame introduced by its parent
    sentence without inheriting an unrelated previous event.
    """
    text=(clause or "").lower().replace("’", "'")
    parent=(parent_sentence or clause or "").lower().replace("’", "'")
    fiscal=bool(re.search(
        r"\b(?:budget|budg[eé]taire|d[eé]ficit|solde|fiscal|finances? publiques?|recettes? publiques?|d[eé]penses? publiques?)\b",
        parent,re.I
    ))
    if fiscal and re.search(r"\brecettes?\b", text,re.I):
        return [("public_revenue", INDICATOR_LABELS["public_revenue"])]
    if fiscal and re.search(r"\bd[eé]penses?\b", text,re.I):
        return [("public_expenditure", INDICATOR_LABELS["public_expenditure"])]
    return []


def _conditional_forecast(text: str) -> bool:
    return bool(re.search(
        r"\b(?:serait|seraient|atteindrait|atteindraient|s['’][ée]l[eè]verait|s['’][ée]l[eè]veraient|"
        r"reculerait|reculeraient|augmenterait|augmenteraient|progresserait|progresseraient|"
        r"devrait|devraient|pourrait|pourraient)\b",
        text or "", re.I))


def _context(document: dict, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    corpus = " ".join(filter(None, [document.get("title"), (document.get("text") or "")[:1200], " ".join(x["text"] for x in candidates[:20])]))
    country, country_iso3 = detect_country(corpus, document.get("country"))
    if document.get("country_iso3") and not country_iso3:
        country_iso3 = document.get("country_iso3")
    source = document.get("source")
    source_match = re.search(
        r"Source\s*:\s*(Minist[eè]re\s+des\s+finances|Banque\s+centrale[^.;]{0,35}|"
        r"Institut\s+National[^.;]{0,45}|World\s+Development\s+Indicators(?:\s+et\s+Minist[eè]re\s+des\s+finances)?)",
        corpus, re.I
    )
    if not source and source_match:
        source = _norm(source_match.group(1))
    # Reject metadata-detector spillover such as "Ministère des finances Le taux...".
    if source and len(str(source)) > 70:
        short = re.match(r"(Minist[eè]re\s+des\s+finances|Institut\s+National[^.;]{0,40}|Banque\s+centrale[^.;]{0,35})", str(source), re.I)
        source = _norm(short.group(1)) if short else document.get("filename") or document.get("title")
    return {
        "country": country,
        "country_iso3": country_iso3,
        # Prefer a declared institution, then URL, then the imported filename.
        # A PDF without an embedded institutional source must still remain
        # traceable to the file the user actually uploaded.
        "source": source or document.get("source_url") or document.get("filename") or document.get("title"),
        "language": document.get("language") or "fr",
    }


def _nearest_year(sentence: str, start: int, end: int) -> int | None:
    years = [(int(m.group()), m.start(), m.end()) for m in _YEAR.finditer(sentence)]
    if not years:
        return None
    low=sentence.lower().replace("’", "'")
    preceding=[y for y in years if y[2] <= start]
    following=[y for y in years if y[1] >= end]
    left=low[:start]
    last_cmp=max(left.rfind("contre"), left.rfind("après"), left.rfind("apres"), left.rfind("against"), left.rfind("compared"))
    last_boundary=max(left.rfind("."), left.rfind(";"), left.rfind(":"))
    # A compared value normally takes the explicit period that follows it.
    if last_cmp > last_boundary and following:
        close=min(following, key=lambda y:y[1]-end)
        if close[1]-end <= 80:
            return close[0]
    # A compact post-value construction such as "34,05 % en 2000" is explicit.
    if following:
        close=min(following, key=lambda y:y[1]-end)
        between=low[end:close[1]]
        if (close[1]-end <= 45 and re.search(r"\ben\b|\bau\b|\bde\b", between)
                and _MEASURE.search(sentence, end, close[1]) is None):
            return close[0]
    # Otherwise a period introduced before the clause/value has priority.
    if preceding:
        return min(preceding, key=lambda y:start-y[2])[0]
    return min(following, key=lambda y:y[1]-end)[0] if following else None


_MONTH_WORDS = {
    "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12,
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
    "يناير":1,"فبراير":2,"مارس":3,"أبريل":4,"ابريل":4,"مايو":5,"يونيو":6,
    "يوليو":7,"أغسطس":8,"اغسطس":8,"سبتمبر":9,"أكتوبر":10,"اكتوبر":10,"نوفمبر":11,"ديسمبر":12,
}

def _nearest_month(sentence: str, start: int, end: int) -> int | None:
    candidates=[]
    low=sentence.lower()
    for word, month in _MONTH_WORDS.items():
        for m in re.finditer(rf"\b{re.escape(word)}\b", low, re.I):
            candidates.append((month, m.start(), m.end()))
    if not candidates: return None
    left=low[:start]
    last_cmp=max(left.rfind("contre"), left.rfind("après"), left.rfind("apres"), left.rfind("against"), left.rfind("compared"))
    last_boundary=max(left.rfind("."), left.rfind(";"), left.rfind(":"))
    following=[c for c in candidates if c[1]>=end]
    preceding=[c for c in candidates if c[2]<=start]
    if following:
        close=min(following,key=lambda c:c[1]-end)
        between=low[end:close[1]]
        if close[1]-end <= 32 and _MEASURE.search(between) is None and re.fullmatch(r"\s*(?:en|au\s+mois\s+de|في)?\s*", between, re.I):
            return close[0]
    if last_cmp>last_boundary and following:
        close=min(following,key=lambda c:c[1]-end)
        if close[1]-end<=80: return close[0]
    if preceding:
        close=min(preceding,key=lambda c:start-c[2])
        # Never let an old month mentioned earlier in a long PDF sentence
        # refine a later annual value. The month must belong to the local
        # value clause (e.g. "en décembre 2025"), not to unrelated history
        # such as "14 janvier 2011 ... 36 616 MD en 2013".
        if start-close[2] <= 70:
            between=low[close[2]:start]
            if not re.search(r"[.;:]", between):
                return close[0]
    if following:
        close=min(following,key=lambda c:c[1]-end)
        between=sentence[end:close[1]]
        # A month belongs to this value only when no other measurement occurs
        # before it (e.g. "5,0 % en novembre").
        if _MEASURE.search(between) is None and close[1]-end <= 45:
            return close[0]
    return None

def _period_label_for_measure(sentence: str, start: int, end: int, year: int|None, month: int|None, quarter: int|None) -> str | None:
    low=sentence.lower().replace("’", "'")
    cumulative = [
        (r"onze premiers mois", "M01:M11"),
        (r"neuf premiers mois", "M01:M09"),
        (r"sept premiers mois", "M01:M07"),
        (r"(?:premier semestre|six premiers mois)", "H1"),
        (r"النصف الأول", "H1"),
    ]
    matches=[]
    for pattern, suffix in cumulative:
        for m in re.finditer(pattern, low, re.I):
            # Prefer a period phrase in the same local clause/value neighborhood.
            distance = min(abs(m.start()-end), abs(start-m.end()))
            if distance <= 90:
                matches.append((distance, suffix))
    if matches:
        suffix=min(matches,key=lambda x:x[0])[1]
        return f"{year}-{suffix}" if year else suffix
    if month and year: return f"{year}-M{month:02d}"
    if quarter and year: return f"{year}-Q{quarter}"
    return str(year) if year else None


_QUARTER_WORDS = {
    "premier": 1, "1er": 1, "1e": 1, "deuxième": 2, "deuxieme": 2, "second": 2,
    "troisième": 3, "troisieme": 3, "quatrième": 4, "quatrieme": 4,
    "الأول": 1, "الاول": 1, "األول": 1, "االول": 1, "الثاني": 2, "الثالث": 3, "الرابع": 4,
}

def _nearest_quarter(sentence: str, start: int, end: int) -> int | None:
    candidates: list[tuple[int, int, int]] = []
    for m in re.finditer(r"\b(?:dernier|quatri[eè]me|quatrieme)\s+trimestre(?:\s+de\s+l['’](?:ann[ée]e|annee))?\b", sentence, re.I):
        candidates.append((4, m.start(), m.end()))
    for m in re.finditer(r"\bT([1-4])\b", sentence, re.I):
        candidates.append((int(m.group(1)), m.start(), m.end()))
    for word, quarter in _QUARTER_WORDS.items():
        for m in re.finditer(rf"\b{word}\s+trimestre\b", sentence, re.I):
            candidates.append((quarter, m.start(), m.end()))
        for m in re.finditer(rf"\bالربع\s+{word}\b", sentence, re.I):
            candidates.append((quarter, m.start(), m.end()))
    for m in re.finditer(r"\b([1-4])(?:er|e|ème|eme)?\s+trimestre\b", sentence, re.I):
        candidates.append((int(m.group(1)), m.start(), m.end()))
    if not candidates:
        return None
    left=sentence[:start].lower().replace("’", "'")
    last_cmp=max(left.rfind("contre"), left.rfind("après"), left.rfind("apres"), left.rfind("compared"))
    last_boundary=max(left.rfind("."), left.rfind(";"), left.rfind(":"))
    usable=candidates
    if last_cmp > last_boundary:
        # For the compared value, never reuse an explicit quarter that belongs
        # to the first value before the comparison boundary.  Relative phrases
        # such as "au trimestre précédent" are resolved by DocumentContext.
        usable=[c for c in candidates if c[1] > last_cmp]
        if not usable:
            return None
    return min(usable, key=lambda x:min(abs(x[1]-start),abs(x[2]-end)))[0]


def _window(sentence: str, start: int, end: int, radius: int = 100) -> str:
    return sentence[max(0, start - radius): min(len(sentence), end + radius)].lower().replace("’", "'")


def _indicator_mentions(sentence: str) -> list[tuple[int, int, str, str]]:
    patterns = [
        (r"سعر\s+الفائدة\s+(?:الرئيسي|[اأإآ]ل?أساسي)|معدل\s+الفائدة\s+(?:الرئيسي|[اأإآ]ل?أساسي)", "policy_rate", INDICATOR_LABELS["policy_rate"]),
        (r"متوسط\s+التضخم\s+السنوي", "inflation_annual_average", INDICATOR_LABELS["inflation_annual_average"]),
        (r"تضخم\s+أسعار\s+المواد\s+الغذائية|تضخم\s+(?:المواد|السلع)\s+الغذائية", "food_inflation", INDICATOR_LABELS["food_inflation"]),
        (r"تضخم\s+(?:السلع|المواد)\s+غير\s+الغذائية", "inflation_rate", INDICATOR_LABELS["inflation_rate"]),
        (r"التضخم|معدل\s+التضخم", "inflation_rate", INDICATOR_LABELS["inflation_rate"]),
        (r"معدل\s+البطالة|البطالة", "unemployment_rate", INDICATOR_LABELS["unemployment_rate"]),
        (r"عجز\s+الميزانية|العجز\s+المالي", "budget_deficit", INDICATOR_LABELS["budget_deficit"]),
        (r"الدين\s+العام|الدين\s+الحكومي", "public_debt_ratio", INDICATOR_LABELS["public_debt_ratio"]),
        (r"الحساب\s+الجاري", "current_account_balance", INDICATOR_LABELS["current_account_balance"]),
        (r"\S*ستثمارات?\s+\S*جنبية\s+المباشرة", "foreign_direct_investment", INDICATOR_LABELS["foreign_direct_investment"]),
        (r"احتياطيات\s+النقد\s+\S*جنبي|احتياطيات\s+العملات\s+\S*جنبية", "foreign_exchange_reserves", INDICATOR_LABELS["foreign_exchange_reserves"]),
        (r"صادرات(?:\s+السلع)?|الصادرات", "exports", INDICATOR_LABELS["exports"]),
        (r"واردات(?:\s+السلع)?|الواردات", "imports", INDICATOR_LABELS["imports"]),
        (r"الناتج\s+المحلي\s+\S*جمالي(?:\s+الحقيقي)?|النمو\s+\S*قتصادي|نمو\s+(?:بنحو|قدره)|(?:^|[،,.؛]\s*)النمو(?=\s+(?:إلى|بنحو|بلغ|سجل|تباطأ))", "gdp_growth", INDICATOR_LABELS["gdp_growth"]),
        (r"taux\s+directeur", "policy_rate", INDICATOR_LABELS["policy_rate"]),
        (r"taux\s+moyen\s+du\s+march[\u00e9e]\s+mon[\u00e9e]taire\s+r[\u00e9e]el|\bTMM\s+r[\u00e9e]el", "real_money_market_rate", INDICATOR_LABELS["real_money_market_rate"]),
        (r"taux\s+moyen\s+du\s+march[\u00e9e]\s+mon[\u00e9e]taire|\bTMM\b", "money_market_rate", INDICATOR_LABELS["money_market_rate"]),
        (r"taux\s+de\s+change\s+effectif\s+nominal|\bTCEN\b", "nominal_effective_exchange_rate", INDICATOR_LABELS["nominal_effective_exchange_rate"]),
        (r"taux\s+de\s+change\s+effectif\s+r[\u00e9e]el|\bTCER\b", "real_effective_exchange_rate", INDICATOR_LABELS["real_effective_exchange_rate"]),
        (r"co[u\u00fb]ts?\s+salari(?:al|aux)\s+unitaires?|\bCSU\b", "unit_labor_cost", INDICATOR_LABELS["unit_labor_cost"]),
        (r"taux\s+de\s+salaire|salaire\s+nominal|r[\u00e9e]mun[\u00e9e]ration\s+moyenne|\bsalaires?\b|co[u\u00fb]t\s+salarial\s+moyen", "nominal_wage_rate", INDICATOR_LABELS["nominal_wage_rate"]),
        (r"productivit[\u00e9e](?:\s+du\s+travail)?", "labor_productivity", INDICATOR_LABELS["labor_productivity"]),
        (r"marge\s+sur\s+co[u\u00fb]t\s+salarial", "wage_cost_margin", INDICATOR_LABELS["wage_cost_margin"]),
        (r"indicateur\s+synth[\u00e9e]tique\s+de\s+comp[\u00e9e]titivit[\u00e9e]|\bISC\b", "competitiveness_index", INDICATOR_LABELS["competitiveness_index"]),
        (r"prix\s+des\s+concurrents", "competitor_prices", INDICATOR_LABELS["competitor_prices"]),
        (r"prix\s+de\s+la\s+(?:valeur\s+ajout[\u00e9e]e|VA)\b", "value_added_price", INDICATOR_LABELS["value_added_price"]),
        (r"(?:d[\u00e9e]pr[\u00e9e]ciation|appr[\u00e9e]ciation)\s+(?:du\s+)?(?:dinar|taux\s+de\s+change)|(?:dinar|taux\s+de\s+change).{0,25}(?:s['’]est\s+)?(?:d[\u00e9e]pr[\u00e9e]ci[\u00e9e]|appr[\u00e9e]ci[\u00e9e])", "exchange_rate_change", INDICATOR_LABELS["exchange_rate_change"]),
        (r"pouvoir\s+d['’]achat|revenu\s+national\s+disponible\s+brut\s+corrig[\u00e9e]\s+des\s+prix", "purchasing_power_growth", INDICATOR_LABELS["purchasing_power_growth"]),
        (r"\bco[u\u00fb]ts?(?:\s+[A-Za-zÀ-ÿ'’.-]+){0,2}\s+vari(?:ant|aient|e|ent)\b|\bniveaux?\s+de\s+co[u\u00fb]t\b", "economic_cost_level", INDICATOR_LABELS["economic_cost_level"]),
        (r"taux\s+d['’]?endettement\s+ext[eé]rieur|dette\s+ext[eé]rieure", "external_debt_ratio", INDICATOR_LABELS["external_debt_ratio"]),
        (r"taux\s+d['’]?endettement\s+int[eé]rieur|dette\s+int[eé]rieure", "internal_debt_ratio", INDICATOR_LABELS["internal_debt_ratio"]),
        (r"taux\s+d['’]?endettement\s+public|ratio\s+de\s+la\s+dette\s+publique", "public_debt_ratio", INDICATOR_LABELS["public_debt_ratio"]),
        (r"(?:d[eé]ficit|solde)\s+budg[eé]taire|(?:deficit|solde)\s+budgetaire|d[eé]ficit\s+public|solde\s+public", "budget_deficit", INDICATOR_LABELS["budget_deficit"]),
        (r"solde(?:\s+budg[eé]taire)?\s+primaire", "primary_balance", INDICATOR_LABELS["primary_balance"]),
        (r"inflation\s+sous[- ]jacente", "core_inflation", INDICATOR_LABELS["core_inflation"]),
        (r"inflation(?:\s+des\s+prix\s+[àa]\s+la\s+consommation)?\s+(?:moyenne|moyenne\s+annuelle)|inflation\s+moyenne\s+des\s+prix\s+[àa]\s+la\s+consommation", "inflation_annual_average", INDICATOR_LABELS["inflation_annual_average"]),
        (r"inflation(?:\s+des\s+prix\s+[àa]\s+la\s+consommation)?\s+(?:en\s+fin\s+de\s+p[eé]riode|fin\s+de\s+p[eé]riode)", "inflation_end_period", INDICATOR_LABELS["inflation_end_period"]),
        (r"prix\s+(?:des\s+produits\s+)?alimentaires|inflation\s+(?:des\s+)?produits\s+alimentaires", "food_inflation", INDICATOR_LABELS["food_inflation"]),
        (r"prix\s+(?:des\s+produits\s+)?manufactur(?:[ée]s|iers?)|inflation\s+(?:des\s+)?produits\s+manufactur(?:[ée]s|iers?)", "manufactured_goods_inflation", INDICATOR_LABELS["manufactured_goods_inflation"]),
        (r"taux\s+d['’]?inflation|inflation|indice\s+des\s+prix\s+(?:[àa]|a)\s+la\s+consommation", "inflation_rate", INDICATOR_LABELS["inflation_rate"]),
        (r"taux\s+d[’\']activit[eé]|taux\s+de\s+l[’\']activit[eé]", "activity_rate", INDICATOR_LABELS["activity_rate"]),
        (r"(?:(?:solde|d[eé]ficit|exc[eé]dent)\s+(?:du\s+)?)?compte\s+courant|d[eé]ficit\s+courant", "current_account_balance", INDICATOR_LABELS["current_account_balance"]),
        (r"taux\s+de\s+ch[oô]mage|ch[oô]mage", "unemployment_rate", INDICATOR_LABELS["unemployment_rate"]),
        (r"investissements?\s+directs?\s+[ée]trangers?|\bIDE\b", "foreign_direct_investment", INDICATOR_LABELS["foreign_direct_investment"]),
        (r"r[eé]serves?(?:\s+officielles?)?\s+de\s+change", "foreign_exchange_reserves", INDICATOR_LABELS["foreign_exchange_reserves"]),
        (r"(?:solde|d[eé]ficit)\s+commercial", "trade_balance", INDICATOR_LABELS["trade_balance"]),
        (r"taux\s+de\s+couverture", "trade_coverage_ratio", INDICATOR_LABELS["trade_coverage_ratio"]),
        (r"(?:variation\s+mensuelle\s+de\s+l['’]indice\s+des\s+prix|sur\s+un\s+mois.{0,80}indice\s+des\s+prix)", "cpi_monthly_change", INDICATOR_LABELS["cpi_monthly_change"]),
        (r"exportations?", "exports", INDICATOR_LABELS["exports"]),
        (r"importations?", "imports", INDICATOR_LABELS["imports"]),
        (r"recettes?\s+publiques?", "public_revenue", INDICATOR_LABELS["public_revenue"]),
        (r"d[eé]penses?\s+publiques?", "public_expenditure", INDICATOR_LABELS["public_expenditure"]),
        (r"croissance(?:\s+du\s+PIB|\s+[ée]conomique)?|produit\s+int[ée]rieur\s+brut|\bPIB(?:\s+r[ée]el)?(?:\s+(?:de|du|des|en)\s+[A-Za-zÀ-ÿ'’ -]{2,45})?\s+(?:a|n['’]a|est|n['’]est|s['’]est|devrait|pourrait|aurait)\b", "gdp_growth", INDICATOR_LABELS["gdp_growth"]),
        (r"dette\s+publique|dette\s+brute\s+des\s+administrations\s+publiques|dette\s+(?:de|des)\s+(?:l['’])?(?:administration\s+centrale|[ÉE]tat|administrations?\s+publiques?)|stock\s+de\s+la\s+dette|encours\s+de\s+la\s+dette", "public_debt_stock", INDICATOR_LABELS["public_debt_stock"]),
    ]
    mentions=[]
    for pattern, code, label in patterns:
        for m in re.finditer(pattern, sentence, re.I):
            if code == "gdp_growth" and re.fullmatch(r"croissance", m.group(0), re.I):
                tail = sentence[m.end():m.end()+70]
                if re.match(r"\s+(?:moyenne\s+)?(?:des?|du|de\s+la)\s+(?:prix|salaires?|co[u\u00fb]ts?|productivit[\u00e9e]|marges?|indicateur)", tail, re.I):
                    continue
            mentions.append((m.start(), m.end(), code, label))
    # Bare “recettes / dépenses” are ambiguous in isolation. Promote them to
    # public-finance concepts only when the same clause contains a fiscal cue.
    fiscal_cue = bool(re.search(
        r"\b(?:budget|budg[eé]taire|d[eé]ficit|solde|fiscal|finances? publiques?|recettes? publiques?|d[eé]penses? publiques?)\b",
        sentence, re.I
    ))
    if fiscal_cue:
        for m in re.finditer(r"\brecettes?\b", sentence, re.I):
            mentions.append((m.start(),m.end(),"public_revenue",INDICATOR_LABELS["public_revenue"]))
        for m in re.finditer(r"\bd[eé]penses?\b", sentence, re.I):
            mentions.append((m.start(),m.end(),"public_expenditure",INDICATOR_LABELS["public_expenditure"]))
    # Remove a generic inflation mention when it overlaps a more specific
    # inflation head. Otherwise "inflation sous-jacente" can be rewritten as
    # headline inflation merely because the shorter word is closer.
    specific_inflation={"core_inflation","inflation_annual_average","inflation_end_period","food_inflation","manufactured_goods_inflation"}
    filtered=[]
    for mention in mentions:
        if mention[2]=="inflation_rate" and any(
            other[2] in specific_inflation and not (mention[1] <= other[0] or mention[0] >= other[1])
            for other in mentions
        ):
            continue
        filtered.append(mention)
    # A bilateral exchange-rate expression can occur inside a sentence whose
    # semantic head is the real/nominal effective exchange rate.  The generic
    # change mention must not eclipse the more specific series.
    effective={"nominal_effective_exchange_rate", "real_effective_exchange_rate"}
    if any(item[2] in effective for item in filtered):
        filtered=[item for item in filtered if item[2] != "exchange_rate_change"]
    return sorted(filtered)


def _indicator_for(sentence: str, match: re.Match[str]) -> tuple[str, str]:
    raw = match.group(0)
    local = _window(sentence, match.start(), match.end(), 125)
    whole = sentence.lower().replace("’", "'")
    is_percent = "%" in raw or bool(re.search(r"points?", raw, re.I))
    is_money = bool(re.search(r"\b(?:md|million|milliard|dinars?|dirhams?|livres?|tnd|mad|dzd|egp|usd|eur)\b", raw, re.I))

    mentions = _indicator_mentions(sentence)
    preceding = [m for m in mentions if m[1] <= match.start()]
    following = [m for m in mentions if m[0] >= match.end()]

    # Explicit local evidence is the primary source of truth. Context is only a
    # fallback. A candidate may not cross another numeric economic measurement.
    local_candidates = []
    if preceding:
        p = min(preceding, key=lambda m: match.start() - m[1])
        between = sentence[p[1]:match.start()]
        if match.start()-p[1] <= 110 and not any(
            mm.group("unit") or mm.group("scale") or mm.group("currency")
            for mm in _MEASURE.finditer(between)
        ):
            local_candidates.append((match.start()-p[1], p))
    if following:
        f = min(following, key=lambda m: m[0]-match.end())
        between = sentence[match.end():f[0]]
        if f[0]-match.end() <= 55 and not any(
            mm.group("unit") or mm.group("scale") or mm.group("currency")
            for mm in _MEASURE.finditer(between)
        ):
            local_candidates.append((f[0]-match.end()+8, f))

    if local_candidates:
        _, nearest = min(local_candidates, key=lambda x:x[0])
        code, label = nearest[2], nearest[3]
        if code == "public_debt_stock" and is_percent:
            code, label = "public_debt_ratio", INDICATOR_LABELS["public_debt_ratio"]
        elif code.endswith("_ratio") and is_money:
            code, label = "public_debt_stock", INDICATOR_LABELS["public_debt_stock"]
        return code, label

    if re.search(r"endettement\s+ext[eé]rieur|dette\s+ext[eé]rieure", local):
        return ("external_debt_ratio" if is_percent else "public_debt_stock", INDICATOR_LABELS["external_debt_ratio"] if is_percent else "Encours de la dette extérieure")
    if re.search(r"endettement\s+int[eé]rieur|dette\s+int[eé]rieure", local):
        return ("internal_debt_ratio" if is_percent else "public_debt_stock", INDICATOR_LABELS["internal_debt_ratio"] if is_percent else "Encours de la dette intérieure")
    if re.search(r"(?:d[eé]ficit|solde)\s+budg[eé]taire|(?:deficit|solde)\s+budgetaire|d[eé]ficit\s+public|solde\s+public", local):
        return "budget_deficit", INDICATOR_LABELS["budget_deficit"]
    if re.search(r"solde(?:\s+budg[eé]taire)?\s+primaire", local):
        return "primary_balance", INDICATOR_LABELS["primary_balance"]
    if re.search(r"inflation\s+sous[- ]jacente", local):
        return "core_inflation", INDICATOR_LABELS["core_inflation"]
    if re.search(r"inflation(?:\s+des\s+prix\s+[àa]\s+la\s+consommation)?\s+(?:moyenne|moyenne\s+annuelle)|inflation\s+moyenne\s+des\s+prix\s+[àa]\s+la\s+consommation", local):
        return "inflation_annual_average", INDICATOR_LABELS["inflation_annual_average"]
    if re.search(r"inflation(?:\s+des\s+prix\s+[àa]\s+la\s+consommation)?\s+(?:en\s+fin\s+de\s+p[eé]riode|fin\s+de\s+p[eé]riode)", local):
        return "inflation_end_period", INDICATOR_LABELS["inflation_end_period"]
    if re.search(r"prix\s+(?:des\s+produits\s+)?alimentaires|inflation\s+(?:des\s+)?produits\s+alimentaires", local):
        return "food_inflation", INDICATOR_LABELS["food_inflation"]
    if re.search(r"taux\s+d['’]?inflation|inflation|indice\s+des\s+prix\s+(?:[àa]|a)\s+la\s+consommation", local):
        return "inflation_rate", INDICATOR_LABELS["inflation_rate"]
    if re.search(r"taux\s+d[’\']activit[eé]|taux\s+de\s+l[’\']activit[eé]", local):
        return "activity_rate", INDICATOR_LABELS["activity_rate"]
    if re.search(r"(?:(?:solde|d[eé]ficit|exc[eé]dent)\s+(?:du\s+)?)?compte\s+courant|d[eé]ficit\s+courant", local):
        return "current_account_balance", INDICATOR_LABELS["current_account_balance"]
    if re.search(r"taux\s+de\s+ch[oô]mage|ch[oô]mage", local):
        return "unemployment_rate", INDICATOR_LABELS["unemployment_rate"]
    if re.search(r"investissements?\s+directs?\s+[ée]trangers?|\bIDE\b", local, re.I):
        return "foreign_direct_investment", INDICATOR_LABELS["foreign_direct_investment"]
    if re.search(r"r[eé]serves?(?:\s+officielles?)?\s+de\s+change", local):
        return "foreign_exchange_reserves", INDICATOR_LABELS["foreign_exchange_reserves"]
    if re.search(r"(?:solde|d[eé]ficit)\s+commercial", local):
        return "trade_balance", INDICATOR_LABELS["trade_balance"]
    if re.search(r"taux\s+de\s+couverture", local):
        return "trade_coverage_ratio", INDICATOR_LABELS["trade_coverage_ratio"]
    if re.search(r"(?:variation\s+mensuelle\s+de\s+l['’]indice\s+des\s+prix|sur\s+un\s+mois.{0,80}indice\s+des\s+prix)", local):
        return "cpi_monthly_change", INDICATOR_LABELS["cpi_monthly_change"]
    if re.search(r"exportations?", local):
        return "exports", INDICATOR_LABELS["exports"]
    if re.search(r"importations?", local):
        return "imports", INDICATOR_LABELS["imports"]
    if re.search(r"recettes?\s+publiques?", local) or (
        is_money and re.search(r"\brecettes?\b", local, re.I)
        and not re.search(r"touris|export|fiscales?\s+sp[eé]cifiques?", local, re.I)
    ):
        return "public_revenue", INDICATOR_LABELS["public_revenue"]
    if re.search(r"d[eé]penses?\s+publiques?", local) or (
        is_money and re.search(r"\bd[eé]penses?\b", local, re.I)
    ):
        return ("public_spending_ratio", INDICATOR_LABELS["public_spending_ratio"]) if is_percent else ("public_expenditure", INDICATOR_LABELS["public_expenditure"])
    if re.search(r"croissance(?:\s+du\s+PIB|\s+[ée]conomique)?|produit\s+int[ée]rieur\s+brut|PIB\s+a\s+(?:progress[ée]|augment[ée]|recul[ée])", local):
        return "gdp_growth", INDICATOR_LABELS["gdp_growth"]
    if re.search(r"taux\s+d['’]?endettement\s+public|ratio\s+de\s+la\s+dette\s+publique", local):
        return "public_debt_ratio", INDICATOR_LABELS["public_debt_ratio"]
    if re.search(r"dette\s+publique|dette\s+(?:de|des)\s+(?:l['’])?(?:administration\s+centrale|[ée]tat|administrations?\s+publiques?)|stock\s+de\s+la\s+dette|encours\s+de\s+la\s+dette", whole):
        if is_money:
            return "public_debt_stock", INDICATOR_LABELS["public_debt_stock"]
        if is_percent:
            return "public_debt_ratio", INDICATOR_LABELS["public_debt_ratio"]
    return "other", "Indicateur économique"


def _unit_fields(raw: str, country_iso3: str | None = None, context_text: str | None = None) -> tuple[Any, Any, Any]:
    low = raw.lower().replace("’", "'")
    # Measurement units have priority over nearby currency words. This prevents
    # a percent value in the same sentence as a monetary stock from inheriting
    # the stock currency and being misclassified as money.
    if "%" in raw:
        return "% du PIB" if re.search(r"%\s*du\s+pib", low, re.I) else "%", None, None
    if "point" in low or "نقطة مئوية" in low:
        return "point", None, None
    if "jour" in low:
        return "jour", None, None
    currency = detect_currency(f"{raw} {context_text or ''}", country_iso3)
    if re.search(r"\bmd\b", low):
        return None, "million", currency
    if "milliard" in low or re.search(r"مليارات?|مليار", low):
        return None, "milliard", currency
    if "million" in low or re.search(r"ملايين|مليون", low):
        return None, "million", currency
    if currency:
        return None, None, currency
    return None, None, None


def _status(sentence: str, match: re.Match[str]) -> str:
    """Classify the nature of one atomic value, not the whole sentence.

    The window is intentionally local so that a sentence such as
    "Pour 2025 ... devrait atteindre 2,1 %, après 1,4 % en 2024" yields
    forecast for 2.1 and observed for 1.4.
    """
    low = sentence.lower().replace("’", "'")
    left = low[max(0, match.start() - 240):match.start()]
    around = low[max(0, match.start() - 70):min(len(low), match.end() + 45)]

    # A comparison boundary before the current value usually ends the modal
    # scope of a forecast/estimate referring to the first value.
    boundary = max(left.rfind("après"), left.rfind("apres"), left.rfind("contre"))
    scoped_left = left[boundary + 5:] if boundary >= 0 else left
    # Modal scope is determined from text preceding the value. Looking ahead
    # can incorrectly turn an observed 2025 value into a forecast merely
    # because the next clause says "puis projette ... 2026".
    scoped = scoped_left

    forecast_re = r"(?:pr[eé]vu(?:e|s)?|pr[eé]vision(?:nel(?:le)?)?\s+(?:de|[àa])|projection(?:s)?\s+(?:de|[àa])|pr[eé]voit|pr[eé]voient|retient|retiennent|devrait|devraient|pourrait|pourraient|attendu(?:e|s)?|projet[eé](?:e|s)?|projette|projettent|projetait|projetaient|serait|seraient|atteindrait|atteindraient|s['’][ée]l[eè]verait|s['’][ée]l[eè]veraient|reculerait|reculeraient|augmenterait|augmenteraient|progresserait|progresseraient|remonterait|remonteraient|ralentirait|ralentiraient|يُ?توقع|من\s+المتوقع|متوقع)"
    estimate_re = r"(?:estim[eé](?:e|s)?|estimation(?:s)?|provisoire(?:s)?|pr[eé]liminaire(?:s)?|aurait|auraient|التقديرات|تقديرات|قُ?درت|قراءة\s+أولية)"

    local_forecast_noun = bool(re.search(r"\bpr[eé]visions?\b.{0,80}$", scoped, re.I))
    if re.search(forecast_re, scoped, re.I) or local_forecast_noun:
        return "forecast"
    if re.search(estimate_re, scoped, re.I):
        return "estimate"
    return "observed"


def _extract_observations(sentence: str, fallback_indicators: list[tuple[str, str]] | None = None, context: DocumentContext | None = None) -> list[dict[str, Any]]:
    """Return atomic economic events: one value, one indicator, one period.

    A sentence may therefore yield several observations.  Indicator assignment
    is corrected after the first pass using explicit grammatical patterns.
    """
    observations: list[dict[str, Any]] = []
    arabic_shared_percent = bool(re.search(r"[\u0600-\u06FF]", sentence) and "%" in sentence)
    for match in _MEASURE.finditer(sentence):
        raw = _norm(match.group(0))
        value = _parse_number(raw)
        explicit_measure = bool(match.group("unit") or match.group("scale") or match.group("currency"))
        inferred_arabic_percent = bool(arabic_shared_percent and not explicit_measure)
        shared_from: re.Match[str] | None = None
        if not explicit_measure:
            later = _MEASURE.search(sentence, match.end())
            between = sentence[match.end():later.start()] if later else ""
            before = sentence[max(0,match.start()-18):match.start()]
            range_grammar = (
                bool(re.search(r"\bentre\s*$", before, re.I) and re.match(r"\s*et\b", between, re.I))
                or bool(re.search(r"\bde\s*$", before, re.I) and not re.search(r"passant\s+de\s*$", before, re.I) and re.match(r"\s*[àa]\b", between, re.I))
                or bool(re.search(r"من\s*$", before, re.I) and re.match(r"\s*إلى\b", between, re.I))
            )
            if later and range_grammar and (later.group("unit") or later.group("scale") or later.group("currency")):
                shared_from = later
        if value is None or (1900 <= value <= 2100 and not (match.group("unit") or match.group("scale") or match.group("currency"))):
            continue
        if not explicit_measure and shared_from is None and not inferred_arabic_percent:
            continue
        code, label = _indicator_for(sentence, match)
        mentions = _indicator_mentions(sentence)
        preceding_mentions = [m for m in mentions if m[1] <= match.start()]
        # RTL text layers can make a later explicit head look geometrically
        # closer than the head that actually precedes the value. Keep this
        # repair Arabic-only so French and English binding remain unchanged.
        if re.search(r"[\u0600-\u06FF]", sentence) and preceding_mentions:
            prior = preceding_mentions[-1]
            if prior[2] == "gdp_growth":
                balances = [m for m in preceding_mentions if m[2] in {"current_account_balance", "budget_deficit", "public_debt_ratio"}]
                if balances:
                    prior = balances[-1]
            code, label = prior[2], prior[3]
        prefix = sentence[max(0, match.start()-90):match.start()]
        # A later explicit indicator must never rewrite a value introduced by
        # a coreferential pronoun. Example: "il s'établissait à 16 %, tandis
        # que le taux d'activité était de 46 %". The first value inherits the
        # previous unemployment indicator; the second binds to activity.
        if fallback_indicators and not preceding_mentions and re.search(
            r"\b(?:il|elle|ils|elles|ce taux|ce ratio|ce niveau|leur niveau)\b", prefix, re.I
        ):
            code, label = fallback_indicators[0]
            indicator_source = "context_unique"
        else:
            indicator_source = "explicit" if code != "other" else "context"
        if code == "other" and fallback_indicators:
            code, label = fallback_indicators[0]
            indicator_source = "context"
        if code == "other" and observations and re.search(
            r"\bcontre\b|مقابل", sentence[observations[-1]["end_position"]:match.start()], re.I
        ):
            # Keep the sibling long enough for the ordered-comparison pass
            # below to bind it to the second explicit concept.
            code, label = observations[-1]["code"], observations[-1]["label"]
            indicator_source = "comparison_sibling"
        if code == "other" and observations and observations[-1]["code"] == "exchange_rate_change" and re.search(
            r"(?:appr[ée]ci|d[ée]pr[ée]ci).{0,45}$", sentence[max(0, match.start() - 55):match.start()], re.I
        ):
            # Coordinated bilateral movements often state the currency subject
            # only once: "the dinar depreciated X against USD and appreciated
            # Y against EUR".  The second movement is an atomic sibling, not an
            # unrelated bare percentage.
            code, label = "exchange_rate_change", INDICATOR_LABELS["exchange_rate_change"]
            indicator_source = "coordinated_sibling"
        # Never silently trust inherited indicator context in a clause that
        # itself contains multiple explicit economic concepts.
        explicit_codes = {m[2] for m in _indicator_mentions(sentence)}
        if indicator_source.startswith("context") and len(explicit_codes) == 1:
            explicit_code = next(iter(explicit_codes))
            explicit_match = next((m for m in _indicator_mentions(sentence) if m[2] == explicit_code), None)
            if explicit_match and re.search(r"\b(?:contre|et|puis|respectivement)\b", sentence, re.I):
                code, label = explicit_match[2], explicit_match[3]
                indicator_source = "explicit_sentence_series"
        if indicator_source.startswith("context") and len(explicit_codes) > 1:
            indicator_source = "context_ambiguous"
        if code == "other":
            continue
        local_country, local_iso3, country_source = _country_for_measure(
            sentence, match.start(), match.end(), context.last_country if context is not None else None
        )
        geography_group, group_source = _group_for_measure(sentence, match.start(), match.end())
        if geography_group:
            local_country, local_iso3, country_source = geography_group, None, group_source
        currency_context = sentence[max(0, match.start()-25):min(len(sentence), match.end()+65)]
        unit_raw = _norm(shared_from.group(0)) if shared_from is not None else raw
        unit, scale, currency = _unit_fields(
            unit_raw, local_iso3 or (context.last_country_iso3 if context is not None else None), currency_context
        )
        unit_source = "shared_range" if shared_from is not None else "explicit"
        if inferred_arabic_percent and unit is None:
            unit = "%"
            unit_source = "shared_clause"

        # Semantic-unit repair. A bare percent in a coreferential sentence may
        # inherit the economically meaningful denominator from the immediately
        # preceding event of the same series (e.g. primary balance / public debt
        # expressed as % of GDP). This is deliberately narrow: we never inherit
        # across a change of indicator.
        if unit == "%" and context is not None and context.last_indicators:
            last_code = context.last_indicators[0][0]
            if last_code == code and context.last_unit == "% du PIB":
                unit = "% du PIB"
                unit_source = "context"

        # Ratio indicators have an intrinsic denominator. Keeping the canonical
        # unit here prevents one economic series from being split into '%' and
        # '% du PIB' merely because a later sentence says only 'ce ratio ... %'.
        if unit == "%" and code in {
            "public_debt_ratio", "external_debt_ratio", "internal_debt_ratio",
            "current_account_balance"
        }:
            unit = "% du PIB"

        # "Leur niveau" after an FDI growth sentence refers to the FDI stock,
        # not to another percentage variation.
        if code == "fdi_growth" and (scale or currency) and re.search(r"\bleur(?:s)?\s+niveau\b", sentence[:match.start()+1], re.I):
            code, label = "foreign_direct_investment", INDICATOR_LABELS["foreign_direct_investment"]
            indicator_source = "context_unique"

        # Monetary coreference keeps the last known currency for the same
        # indicator when the current value only states a scale (e.g. reserves
        # "23,1 milliards" one year earlier).
        if scale and not currency and context is not None and context.last_indicators:
            last_code = context.last_indicators[0][0]
            if last_code == code and context.last_currency:
                currency = context.last_currency
                unit_source = "context"

        # A monetary value in a debt sentence is always an encours, never a ratio.
        if (scale or currency) and (
            code in {"public_debt_ratio", "public_debt_stock"}
            or re.search(r"dette\s+publique|stock\s+de\s+la\s+dette|encours\s+de\s+la\s+dette|ratio\s+de\s+la\s+dette", _window(sentence, match.start(), match.end(), 90), re.I)
        ):
            code, label = "public_debt_stock", INDICATOR_LABELS["public_debt_stock"]
        nearest_year = _nearest_year(sentence, match.start(), match.end())
        nearest_quarter = _nearest_quarter(sentence, match.start(), match.end())
        nearest_month = _nearest_month(sentence, match.start(), match.end())

        # Event-local temporal precedence: when a relative phrase occurs before
        # this value, a later explicit date belongs to a later sibling event and
        # cannot be pulled backward. Resolve the relative phrase from discourse.
        prefix_fragment = sentence[max(0, match.start()-75):match.start()]
        relative_before = RELATIVE_PERIOD_HINTS.search(prefix_fragment)
        if relative_before:
            rel_tail = prefix_fragment[relative_before.start():]
            if not _YEAR.search(prefix_fragment):
                nearest_year = None
            if not re.search(r"\b(?:T[1-4]|Q[1-4]|premier|deuxi[eè]me|troisi[eè]me|quatri[eè]me)\s+trimestre\b", rel_tail, re.I):
                nearest_quarter = None
            if not any(re.search(rf"\b{re.escape(w)}\b", rel_tail, re.I) for w in _MONTH_WORDS):
                nearest_month = None
        period_source = "explicit" if (nearest_year is not None or nearest_quarter is not None or nearest_month is not None) else "context"
        resolved_month = nearest_month
        resolved_quarter = nearest_quarter
        resolved_year = nearest_year
        if context is not None and (nearest_year is None or nearest_quarter is None or nearest_month is None):
            next_measure = _MEASURE.search(sentence, match.end())
            local_end = next_measure.start() if next_measure else min(len(sentence), match.end() + 120)
            if relative_before:
                # Do not expose a relative event to a later sibling's explicit
                # date; the discourse anchor is the correct reference.
                local_end = min(local_end, match.end() + 18)
            local_fragment = sentence[max(0, match.start() - 80):local_end]
            inherit_period = (
                bool(fallback_indicators)
                or nearest_month is not None
                or nearest_quarter is not None
                or context.current_month is not None
                or context.current_quarter is not None
                or bool(RELATIVE_PERIOD_HINTS.search(sentence))
                # Coordinated indicator clauses commonly share the explicit
                # year introduced by the immediately preceding sentence in the
                # same paragraph/chapter ("Le chômage..., tandis que la dette...").
                or (context.current_year is not None and bool(_indicator_mentions(sentence)))
            )
            cm, cq, cy = context.resolve_period(
                local_fragment, nearest_month, nearest_quarter, nearest_year, inherit=inherit_period
            )
            resolved_month = cm
            resolved_quarter = cq
            resolved_year = cy
        # Explicit frequency wins over inherited granularity. A Q4 value after
        # a December sentence is Q4, never Q4+M12; likewise an explicit month
        # cannot retain an inherited quarter.
        if nearest_quarter is not None:
            resolved_month = None
        if nearest_month is not None:
            resolved_quarter = None
        # A quarter explicitly stated in the document title is a last-resort
        # granularity for an otherwise undated primary value. It must not refine
        # a value that has its own explicit year/month/quarter.
        if (resolved_month is None and resolved_quarter is None and nearest_year is None
                and nearest_month is None and nearest_quarter is None
                and context is not None and getattr(context, "document_quarter", None) is not None):
            resolved_quarter = context.document_quarter
            resolved_year = resolved_year or context.document_year or context.anchor_year
            if period_source == "context":
                period_source = "document_metadata"

        # Document-title month is only a last-resort fallback for an otherwise
        # undated sentence. It must never refine an explicit annual/quarterly
        # period. Example: in a "December 2025" IPC article, "core inflation
        # reached 4.9 %, after 5.0 % in November" maps 4.9 to 2025-M12; but
        # "in 2022 ..." remains 2022, never 2022-M12.
        if (resolved_month is None and resolved_quarter is None and nearest_month is None
                and nearest_quarter is None and not _YEAR.search(sentence)
                and context is not None and context.document_month is not None):
            resolved_month = context.document_month
            resolved_year = resolved_year or context.document_year or context.anchor_year
            if period_source == "context":
                period_source = "document_metadata"

        period_label = _period_label_for_measure(sentence, match.start(), match.end(), resolved_year, resolved_month, resolved_quarter)
        if period_label and ("M01:M" in period_label or period_label.endswith("-H1") or period_label == "H1"):
            resolved_month = None
            resolved_quarter = None
        observations.append({
            "code": code,
            "label": label,
            "value": value,
            "raw": raw,
            "year": resolved_year,
            "month": resolved_month,
            "quarter": resolved_quarter,
            "status": _status(sentence, match),
            "indicator_source": indicator_source,
            "unit_source": unit_source,
            "period_source": period_source,
            "unit": unit,
            "scale": scale,
            "currency": currency,
            "position": match.start(),
            "end_position": match.end(),
            "period_label": period_label,
            "country": local_country,
            "country_iso3": local_iso3,
            "country_source": country_source,
            "geography_type": "economic_group" if geography_group else ("country" if local_country else "unknown"),
            "ambiguous_context": code == "economic_cost_level",
        })

    # Local temporal scope repair for multi-indicator sentences.
    # A quarter/month attached to a later measurement must not refine earlier
    # values in the same sentence.
    for obs in observations:
        if obs.get("quarter") is not None and obs.get("period_source") == "explicit":
            q_positions=[]
            for m in re.finditer(r"\b(?:T([1-4])|Q([1-4])|premier trimestre|deuxi[eè]me trimestre|troisi[eè]me trimestre|quatri[eè]me trimestre)\b", sentence, re.I):
                q_positions.append((m.start(),m.end()))
            if q_positions:
                q=min(q_positions,key=lambda q:min(abs(q[0]-obs["end_position"]),abs(obs["position"]-q[1])))
                if q[0] > obs["end_position"]:
                    between=sentence[obs["end_position"]:q[0]]
                    intervening=sum(1 for m in _MEASURE.finditer(between) if m.group("unit") or m.group("scale") or m.group("currency"))
                    comparison_boundary = bool(re.search(r"\b(?:après|apres|contre|after|compared)\b", between, re.I))
                    if intervening >= 1 and not comparison_boundary:
                        obs["quarter"]=None
                        if obs.get("year") is not None:
                            obs["period_label"]=str(obs["year"])
        if obs.get("month") is not None and obs.get("period_source") == "explicit":
            m_positions=[]
            for word in _MONTH_WORDS:
                for m in re.finditer(rf"\b{re.escape(word)}\b", sentence, re.I):
                    m_positions.append((m.start(),m.end()))
            if m_positions:
                q=min(m_positions,key=lambda q:min(abs(q[0]-obs["end_position"]),abs(obs["position"]-q[1])))
                if q[0] > obs["end_position"]:
                    between=sentence[obs["end_position"]:q[0]]
                    intervening=sum(1 for m in _MEASURE.finditer(between) if m.group("unit") or m.group("scale") or m.group("currency"))
                    comparison_boundary = bool(re.search(r"\b(?:après|apres|contre|after|compared)\b", between, re.I))
                    if intervening >= 1 and not comparison_boundary:
                        obs["month"]=None
                        if obs.get("year") is not None:
                            obs["period_label"]=str(obs["year"])

    low = sentence.lower().replace("’", "'")

    # A leading conditional/modal governs a coordinated value list until an
    # explicit observed/estimate boundary appears. This covers regional lists
    # such as "Pour 2025, la croissance serait de 3,8 % au Maroc, ...".
    if observations and _conditional_forecast(low[:observations[0]["position"] + 1]):
        for obs in observations:
            obs["status"] = "forecast"

    # A current-account *deficit* is a negative balance even when the source
    # prints the magnitude without a minus sign.  Budget deficits remain in the
    # source convention because the product represents them as deficit levels.
    for obs in observations:
        local_before = low[max(0, obs["position"]-120):obs["position"]]
        if obs.get("code") == "current_account_balance" and re.search(r"d[eé]ficit(?:\s+du)?\s+compte\s+courant|deficit(?:\s+du)?\s+compte\s+courant", local_before, re.I):
            obs["value"] = -abs(float(obs["value"]))

    # Ordered comparison binding: when two explicitly named concepts precede
    # a parenthetical ``A contre B``, values inherit the concept order. This is
    # common in analytical reports and avoids nearest-word inversion.
    percent_obs = [o for o in observations if o.get("unit") == "%"]
    if len(percent_obs) == 2 and re.search(r"\([^)]*\bcontre\b[^)]*\)", low):
        first_value = min(o["position"] for o in percent_obs)
        all_mentions=_indicator_mentions(sentence[:first_value])
        ordered_mentions=[]
        seen_codes=set()
        for mention in reversed(all_mentions):
            if mention[2] not in seen_codes:
                ordered_mentions.append(mention);seen_codes.add(mention[2])
            if len(ordered_mentions)==2:break
        ordered_mentions=sorted(ordered_mentions,key=lambda m:m[0])
        if len(ordered_mentions) == 2:
            roles=[(m[2],m[3]) for m in ordered_mentions]
            for obs, role in zip(sorted(percent_obs, key=lambda x: x["position"]), roles):
                obs["code"], obs["label"], obs["indicator_source"] = role[0], role[1], "explicit_ordered_comparison"

    # Negative change verbs carry a signed variation even when the printed
    # magnitude is positive ("a reculé de 3,2 %" -> -3.2 %).
    for obs in observations:
        before = low[max(0, obs["position"]-90):obs["position"]]
        if obs.get("unit") == "%" and obs.get("code") in {"exports_growth", "imports_growth", "fdi_growth", "cpi_monthly_change"} and re.search(r"(?:recul[ée]|diminu[ée]|baiss[ée]).{0,25}$", before, re.I):
            obs["value"] = -abs(float(obs["value"]))
        if obs.get("unit") == "%" and obs.get("code") == "gdp_growth" and re.search(
            r"(?:contraction|recul|baisse).{0,22}(?:de\s+)?$", before, re.I
        ):
            obs["value"] = -abs(float(obs["value"]))

    # Explicit local inflation sub-concepts beat a broader inflation mention.
    for obs in observations:
        local_before = low[max(0, obs["position"]-100):obs["position"]]
        local_scope = low[max(0, obs["position"]-140):min(len(low), obs["end_position"]+80)]
        # A point-in-time year-on-year price increase is headline inflation,
        # even when the previous sentence discussed the annual average.
        if obs.get("code") == "inflation_annual_average" and re.search(
            r"(?:hausse(?:\s+des\s+prix)?|rythme|taux)\s+sur\s+(?:douze|12)\s+mois",
            local_scope, re.I,
        ):
            obs["code"] = "inflation_rate"
            obs["label"] = INDICATOR_LABELS["inflation_rate"]
            obs["indicator_source"] = "context_unique"
        if obs.get("code") == "inflation_rate" and re.search(r"(?:sur\s+un\s+mois|variation\s+mensuelle)", local_scope, re.I) and re.search(r"indice\s+des\s+prix", local_scope, re.I):
            obs["code"] = "cpi_monthly_change"
            obs["label"] = INDICATOR_LABELS["cpi_monthly_change"]
            obs["indicator_source"] = "explicit"
        if re.search(r"inflation\s+(?:de|en)\s+fin\s+de\s+p[ée]riode", local_before, re.I):
            obs["code"] = "inflation_end_period"
            obs["label"] = INDICATOR_LABELS["inflation_end_period"]
            obs["indicator_source"] = "explicit"
        local_after = low[obs["end_position"]:min(len(low), obs["end_position"]+45)]
        local_full = low[max(0, obs["position"]-130):min(len(low), obs["end_position"]+55)]
        if obs.get("code") == "inflation_rate" and (
            re.search(r"inflation\s+moyenne", local_full, re.I)
            or (re.search(r"indice\s+des\s+prix", local_full, re.I) and re.search(r"\ben\s+moyenne\b", local_after, re.I))
        ):
            obs["code"] = "inflation_annual_average"
            obs["label"] = INDICATOR_LABELS["inflation_annual_average"]
            obs["indicator_source"] = "explicit"

    # Clause-aware semantic override: a percentage describing that FDI
    # "progressed/increased by" is a variation, not the FDI stock itself.
    for obs in observations:
        local_before = low[max(0, obs["position"] - 95):obs["position"]]
        if obs["code"] == "foreign_direct_investment" and obs["unit"] == "%" and re.search(
            r"(?:investissements?\s+directs?\s+[ée]trangers?|\bide\b).{0,55}(?:progress[ée]|augment[ée]|hausse|accru).{0,20}$",
            local_before, re.I
        ):
            obs["code"] = "fdi_growth"
            obs["label"] = INDICATOR_LABELS["fdi_growth"]

    # Percentages attached to export/import growth verbs are rates of change, not levels.
    for obs in observations:
        local_before = low[max(0, obs["position"] - 110):obs["position"]]
        if obs.get("unit") == "%" and obs.get("code") in {"exports", "imports"}:
            noun = r"exportations?" if obs["code"] == "exports" else r"importations?"
            if re.search(noun + r".{0,65}(?:progress[ée]s?|progresse(?:nt)?|augment[ée]s?|augmente(?:nt)?|hausse|accru(?:es?)?|recul[ée]s?|recule(?:nt)?|diminu[ée]s?|diminue(?:nt)?).{0,24}$", local_before, re.I):
                obs["code"] = "exports_growth" if obs["code"] == "exports" else "imports_growth"
                obs["label"] = INDICATOR_LABELS[obs["code"]]

    # Apply direction sign after semantic conversion to a growth indicator.
    for obs in observations:
        local_before = low[max(0, obs["position"]-90):obs["position"]]
        if obs.get("code") in {"exports_growth", "imports_growth", "fdi_growth", "cpi_monthly_change"} and re.search(r"(?:recul[ée]|diminu[ée]|baiss[ée]).{0,30}$", local_before, re.I):
            obs["value"] = -abs(float(obs["value"]))

    # Canonical trade balance uses a signed convention. When the source states
    # a positive magnitude as a "déficit commercial", store it as a negative
    # balance while preserving the original sentence/raw value for traceability.
    if re.search(r"d[eé]ficit\s+commercial", low, re.I):
        for obs in observations:
            if obs.get("code") == "trade_balance" and obs.get("value") is not None and obs["value"] > 0:
                obs["value"] = -obs["value"]

    # A year written immediately after a value is authoritative for that value,
    # even if an earlier sibling contains a relative phrase such as
    # "deux ans auparavant". This prevents relative context leaking forward.
    for obs in observations:
        after = sentence[obs["end_position"]:min(len(sentence), obs["end_position"]+36)]
        ym = re.search(r"\b(?:en|pour|fin)\s+((?:19|20)\d{2})\b", after, re.I)
        if ym and _MEASURE.search(after[:ym.start()]) is None:
            obs["year"] = int(ym.group(1))
            obs["period_source"] = "explicit"
            obs["period_label"] = _period_label_for_measure(
                sentence, obs["position"], obs["end_position"],
                obs["year"], obs.get("month"), obs.get("quarter")
            )

    # Sibling temporal relations in one sentence resolve from the primary
    # explicit anchor, not from the immediately preceding relative observation.
    # Q4 -> previous quarter Q3 -> six months earlier Q2.
    if observations and re.search(r"\bsix mois plus (?:tôt|tot)\b|\bsix months earlier\b", sentence, re.I):
        primary = next((o for o in observations if o.get("period_source") == "explicit" and o.get("quarter")), None)
        if primary:
            for obs in observations:
                local = sentence[max(0, obs["position"]-30):min(len(sentence), obs["end_position"]+45)]
                if re.search(r"\bsix mois plus (?:tôt|tot)\b|\bsix months earlier\b", local, re.I):
                    from app.services.context_resolver import shift_quarter
                    yy, qq = shift_quarter(primary.get("year"), primary.get("quarter"), -2)
                    obs["year"], obs["quarter"], obs["month"] = yy, qq, None
                    obs["period_source"] = "relative_context"
                    obs["period_label"] = _period_label_for_measure(
                        sentence, obs["position"], obs["end_position"], yy, None, qq
                    )

    # Monetary "passing from A to B" patterns describe two levels; a preceding
    # "increased by X billion" is an absolute change, not a third level.
    # Example: reserves increased by 3.7bn, passing from 237.4 to 241.1bn.
    passing = re.search(
        rf"(?:passant|pass[eé]s?|pass[ée]e?s?)\s+de\s+(?P<a>{_NUMBER_TOKEN})\s+[àa]\s+(?P<b>{_NUMBER_TOKEN})\s*"
        rf"(?P<scale>milliards?|millions?|MD)?\s*(?:de\s+)?(?P<currency>{_ISO_CURRENCY_CODES}|{_GENERIC_CURRENCY_WORDS})?",
        sentence, re.I
    )
    if passing and observations:
        a_val = _parse_number(passing.group("a"))
        b_val = _parse_number(passing.group("b"))
        # Find the observation representing the terminal B level.
        terminal = min(
            (o for o in observations if b_val is not None and abs(float(o.get("value", 1e99))-float(b_val)) < 1e-9),
            key=lambda o: abs(o["position"]-passing.start("b")),
            default=None,
        )
        if terminal is not None and a_val is not None:
            scale = terminal.get("scale") or _norm(passing.group("scale") or "") or None
            currency = terminal.get("currency") or detect_currency(passing.group("currency") or "", terminal.get("country_iso3"))[0]
            # Parse explicit period anchors around "between ... and ...".
            before = sentence[:passing.start()]
            period_pair = re.search(
                r"entre\s+fin\s+([A-Za-zÀ-ÿ]+)\s+((?:19|20)\d{2})\s+et\s+fin\s+([A-Za-zÀ-ÿ]+)\s+((?:19|20)\d{2})",
                before, re.I
            )
            a_year=a_month=b_year=b_month=None
            if period_pair:
                a_month=_MONTH_WORDS.get(period_pair.group(1).lower())
                a_year=int(period_pair.group(2))
                b_month=_MONTH_WORDS.get(period_pair.group(3).lower())
                b_year=int(period_pair.group(4))
                terminal["year"]=b_year; terminal["month"]=b_month; terminal["quarter"]=None
                terminal["period_source"]="explicit"
                terminal["period_label"]=_period_label_for_measure(sentence,terminal["position"],terminal["end_position"],b_year,b_month,None)
            # Add the initial level if it was not otherwise captured.
            if not any(abs(float(o.get("value",1e99))-float(a_val)) < 1e-9 and o.get("code")==terminal.get("code") for o in observations):
                observations.append({
                    **terminal,
                    "value": a_val,
                    "raw": passing.group("a"),
                    "year": a_year or terminal.get("year"),
                    "month": a_month,
                    "quarter": None if a_month is not None else terminal.get("quarter"),
                    "period_source": "explicit" if a_year else terminal.get("period_source"),
                    "period_label": _period_label_for_measure(sentence,passing.start("a"),passing.end("a"),a_year or terminal.get("year"),a_month,None),
                    "position": passing.start("a"),
                    "end_position": passing.end("a"),
                    "scale": scale,
                    "currency": currency,
                })
            # Suppress an earlier absolute-change amount for the same level series.
            change_match = re.search(
                rf"(?:augment[ée]s?|progress[ée]s?|accru(?:e|es|s)?)\s+de\s+(?P<x>{_NUMBER_TOKEN})\s*(?:milliards?|millions?)",
                sentence[:passing.start()], re.I
            )
            if change_match:
                x_val=_parse_number(change_match.group("x"))
                observations[:] = [
                    o for o in observations
                    if not (x_val is not None and abs(float(o.get("value",1e99))-float(x_val))<1e-9
                            and o.get("code")==terminal.get("code")
                            and o["position"] < passing.start())
                ]
            observations.sort(key=lambda o:o["position"])

    # Public-finance role binding for monetary levels. The noun closest to
    # the value is stronger than a later generic deficit mention or inherited
    # indicator context.
    for obs in observations:
        if not (obs.get("scale") or obs.get("currency")):
            continue
        before = sentence[max(0, obs["position"]-85):obs["position"]].lower().replace("’", "'")
        if re.search(r"\brecettes?(?:\s+publiques?|\s+budg[eé]taires?|\s+fiscales?)?\b.{0,45}$", before, re.I):
            obs["code"], obs["label"] = "public_revenue", INDICATOR_LABELS["public_revenue"]
            obs["indicator_source"] = "explicit_local_role"
        elif re.search(r"\bd[eé]penses?(?:\s+publiques?|\s+budg[eé]taires?)?\b.{0,45}$", before, re.I):
            obs["code"], obs["label"] = "public_expenditure", INDICATOR_LABELS["public_expenditure"]
            obs["indicator_source"] = "explicit_local_role"

    # Monetary comparisons inherit an explicit currency from the sibling value
    # when the sentence clearly describes one monetary series.
    money_obs = [o for o in observations if o.get("scale") and not o.get("unit")]
    currencies = {o.get("currency") for o in money_obs if o.get("currency")}
    if len(currencies) == 1:
        inherited_currency = next(iter(currencies))
        for obs in money_obs:
            if not obs.get("currency"):
                obs["currency"] = inherited_currency
                obs["unit_source"] = "context"

    # If a sentence introduces a new indicator and compares it with "the previous
    # quarter", the first value belongs to the current contextual quarter while
    # the compared value is shifted back one quarter.
    if re.search(r"trimestre (?:précédent|precedent|d['’]avant|d'avant)|previous quarter|الربع السابق", low, re.I) and observations:
        primary = observations[0]
        anchor_q = primary.get("quarter") or (context.current_quarter if context is not None else None)
        anchor_y = primary.get("year") or (context.current_year if context is not None else None)
        if primary.get("quarter") is None and anchor_q is not None:
            primary["quarter"] = anchor_q
            primary["month"] = None
            primary["year"] = anchor_y
            primary["period_label"] = _period_label_for_measure(sentence, primary["position"], primary["end_position"], primary["year"], None, primary["quarter"])
        # If the relative phrase belongs to a compared value in the same
        # sentence, resolve it from the first value's explicit quarter.
        if anchor_q is not None and len(observations) > 1:
            for ref in observations[1:]:
                tail = low[max(0, ref["position"]-35):min(len(low), ref["end_position"]+55)]
                if re.search(r"trimestre (?:précédent|precedent|d['’]avant|d'avant)|previous quarter|الربع السابق", tail, re.I):
                    ry, rq = __import__("app.services.context_resolver", fromlist=["shift_quarter"]).shift_quarter(anchor_y, anchor_q, -1)
                    ref["year"] = ry
                    ref["quarter"] = rq
                    ref["month"] = None
                    ref["period_source"] = "relative_context"
                    ref["period_label"] = _period_label_for_measure(sentence, ref["position"], ref["end_position"], ry, None, rq)

    # A sentence-level relative quarter introduced before all values applies
    # to every coordinated clause unless a value has its own explicit period.
    if context is not None and observations and re.search(r"^\s*Au\s+trimestre\s+pr[ée]c[ée]dent", sentence, re.I):
        target_year, target_quarter = __import__("app.services.context_resolver", fromlist=["shift_quarter"]).shift_quarter(context.current_year, context.current_quarter, -1)
        for obs in observations:
            if obs.get("quarter") is None:
                obs["quarter"] = target_quarter
                obs["month"] = None
                obs["year"] = obs.get("year") or target_year
                obs["period_source"] = "relative_context"
                obs["period_label"] = _period_label_for_measure(sentence, obs["position"], obs["end_position"], obs.get("year"), None, obs.get("quarter"))

    # "same period of the previous year" preserves the active granularity.
    # If the prior event is Q1 2025, a following comparison sentence must map
    # its current and reference values to Q1 2025 and Q1 2024, not merely 2025/2024.
    same_prev = re.search(r"(?:même période|same period).{0,35}(?:année précédente|l['’]année précédente|previous year|last year)|(?:année précédente|previous year).{0,35}(?:même période|same period)", low, re.I)
    if context is not None and same_prev and observations:
        contre_pos = max(low.find("contre"), low.find("compared"))
        current = observations[0]
        if context.current_quarter is not None and current.get("quarter") is None:
            current["quarter"] = context.current_quarter
            current["month"] = None
            current["year"] = current.get("year") or context.current_year
            current["period_label"] = _period_label_for_measure(sentence, current["position"], current["end_position"], current["year"], None, current["quarter"])
        elif context.current_month is not None and current.get("month") is None:
            current["month"] = context.current_month
            current["quarter"] = None
            current["year"] = current.get("year") or context.current_year
            current["period_label"] = _period_label_for_measure(sentence, current["position"], current["end_position"], current["year"], current["month"], None)
        compared = [o for o in observations if contre_pos >= 0 and o["position"] > contre_pos]
        if compared:
            ref = compared[0]
            if context.current_quarter is not None:
                ref["quarter"] = context.current_quarter
                ref["month"] = None
                ref["year"] = (current.get("year") or context.current_year or context.anchor_year) - 1 if (current.get("year") or context.current_year or context.anchor_year) else ref.get("year")
                ref["period_label"] = _period_label_for_measure(sentence, ref["position"], ref["end_position"], ref["year"], None, ref["quarter"])
            elif context.current_month is not None:
                ref["month"] = context.current_month
                ref["quarter"] = None
                ref["year"] = (current.get("year") or context.current_year or context.anchor_year) - 1 if (current.get("year") or context.current_year or context.anchor_year) else ref.get("year")
                ref["period_label"] = _period_label_for_measure(sentence, ref["position"], ref["end_position"], ref["year"], ref["month"], None)

    # Relative periods attached to a specific value inside the same sentence.
    # Only inspect the text after that value and before the next measurement,
    # preventing "47.2 %, contre 49.1 % l'année suivante" from shifting 47.2.
    explicit_anchor = first_year = next((int(m.group()) for m in _YEAR.finditer(sentence)), None)
    if explicit_anchor is not None:
        for i, obs in enumerate(observations):
            next_pos = observations[i + 1]["position"] if i + 1 < len(observations) else min(len(sentence), obs["end_position"] + 80)
            tail = sentence[obs["end_position"]:next_pos]
            if re.search(r"l['’]année suivante|année suivante|un an plus tard|following year|next year", tail, re.I):
                obs["year"] = explicit_anchor + 1
            elif re.search(r"l['’]année précédente|année précédente|un an plus tôt|previous year|last year|العام السابق|السنة السابقة|قبل عام", tail, re.I):
                obs["year"] = explicit_anchor - 1

    # A year introduced at sentence start scopes coordinated economic clauses
    # unless a clause carries its own explicit/relative period.
    leading_scope = re.match(r"\s*(?:en|au cours de l['’]ann[ée]e)\s+((?:19|20)\d{2})\b", low)
    if leading_scope and len(list(_YEAR.finditer(sentence))) == 1 and not re.search(
        r"année précédente|année suivante|un an auparavant|un an plus tôt|un an plus tard|previous year|next year", low, re.I
    ):
        scope_year = int(leading_scope.group(1))
        for obs in observations:
            obs["year"] = scope_year
            obs["period_source"] = "explicit_sentence_scope"
            obs["period_label"] = _period_label_for_measure(sentence, obs["position"], obs["end_position"], scope_year, obs.get("month"), obs.get("quarter"))

    # Explicit chronological constructions override proximity-based year assignment.
    # Example: "En 2024, l'inflation a atteint 7 %, contre 9 % en 2023".
    leading_year = re.match(r"\s*(?:en|au cours de l['’]ann[ée]e)\s+((?:19|20)\d{2})\b", low)
    explicit_years = [int(m.group()) for m in _YEAR.finditer(sentence)]
    if ("respectivement" in low and len(explicit_years) == len(observations)
            and len(observations) > 1 and len(set(explicit_years)) == len(explicit_years)):
        # Parallel lists keep their written order even when the reference year
        # follows the first value list: "en 2017 et 2018 ... 5.3 and 7.5,
        # respectively, against 3.5 in 2011".
        for obs, year in zip(sorted(observations, key=lambda o:o["position"]), explicit_years):
            obs["year"] = year
            obs["month"] = None
            obs["quarter"] = None
            obs["period_source"] = "respectively_year_alignment"
            obs["period_label"] = str(year)
    # "A en 2024 après B l'année précédente": the written year belongs
    # to A and the relative period belongs to B. Do this before any fallback
    # to document metadata, which may merely be the first historical year.
    if len(explicit_years) == 1 and len(observations) >= 2:
        after_positions = [p for p in (low.find("après"), low.find("apres"), low.find("after")) if p >= 0]
        year_match = next(iter(_YEAR.finditer(sentence)), None)
        if after_positions and year_match and year_match.start() < min(after_positions):
            after_pos = min(after_positions)
            if re.search(r"année précédente|l['’]année précédente|un an auparavant|un an plus tôt|un an plus tot|l['’]année d['’]avant|l'annee d'avant|deux ans plus tôt|deux ans plus tot|previous year|last year", low[after_pos:], re.I):
                observations[0]["year"] = explicit_years[0]
                observations[0]["period_source"] = "explicit"
                observations[0]["period_label"] = _period_label_for_measure(sentence, observations[0]["position"], observations[0]["end_position"], explicit_years[0], observations[0].get("month"), observations[0].get("quarter"))
                ref = next((o for o in observations[1:] if o["position"] > after_pos), observations[1])
                ref["year"] = explicit_years[0] - 1
                ref["period_source"] = "relative_context"
                ref["period_label"] = _period_label_for_measure(sentence, ref["position"], ref["end_position"], ref["year"], ref.get("month"), ref.get("quarter"))

    # Arabic relative comparisons use the same discourse arithmetic as their
    # French/English equivalents.
    if len(observations) >= 2 and re.search(r"قبل\s+ثلاث(?:ة)?\s+أشهر", sentence):
        anchor = observations[0]
        if anchor.get("year") and anchor.get("month"):
            from app.services.context_resolver import shift_month
            ref = observations[1]
            ref["year"], ref["month"] = shift_month(anchor["year"], anchor["month"], -3)
            ref["quarter"] = None
            ref["period_source"] = "relative_context"
            ref["period_label"] = _period_label_for_measure(sentence, ref["position"], ref["end_position"], ref["year"], ref["month"], None)

    # A from/to monetary pair following an explicit current-year comparison
    # represents previous then current period unless either value has its own
    # explicit date.
    if re.search(r"من\s+[-+]?\d", sentence) and re.search(r"إلى\s+[-+]?\d", sentence):
        years = [int(m.group()) for m in _YEAR.finditer(sentence)]
        by_code = defaultdict(list)
        for obs in observations:
            by_code[obs.get("code")].append(obs)
        for siblings in by_code.values():
            siblings = sorted(siblings, key=lambda o: o["position"])
            if len(siblings) == 2 and years:
                siblings[0]["year"], siblings[1]["year"] = years[0] - 1, years[0]
                for obs in siblings:
                    obs["period_source"] = "relative_ordered_comparison"
                    obs["period_label"] = str(obs["year"])

    # “deficit X before turning to Y” is an ordered annual balance sequence.
    balance_obs = [o for o in observations if o.get("code") == "current_account_balance"]
    if len(balance_obs) == 2 and re.search(r"قبل\s+أن.*يتحول", sentence):
        balance_obs.sort(key=lambda o: o["position"])
        if balance_obs[0].get("year"):
            balance_obs[1]["year"] = balance_obs[0]["year"] + 1
            balance_obs[1]["period_source"] = "relative_ordered_comparison"
            balance_obs[1]["period_label"] = str(balance_obs[1]["year"])

    # In an article explicitly anchored to year Y, a sentence such as
    # "the deficit reached A, against B in Y-1" has only the reference year
    # written in the sentence. The first value belongs to the document year,
    # not to the trailing comparison year.
    if (context is not None and context.document_year is not None and len(explicit_years) == 1
            and observations and re.search(r"\b(?:contre|apr[eè]s|against|after|compared\s+with|compared\s+to)\b", low, re.I)):
        ref_year = explicit_years[0]
        first = observations[0]
        first_year_pos = next((m.start() for m in _YEAR.finditer(sentence)), -1)
        boundary_positions = [p for p in (low.find("contre"), low.find("après"), low.find("apres"), low.find("against"), low.find("after")) if p >= 0]
        cmp_pos_for_year = min(boundary_positions) if boundary_positions else -1
        if first_year_pos > first["end_position"] and first_year_pos > cmp_pos_for_year >= 0 and ref_year != context.document_year:
            first["year"] = context.document_year
            first["month"] = None if first.get("quarter") is None else first.get("month")
            first["period_source"] = "document_metadata"
            first["period_label"] = _period_label_for_measure(sentence, first["position"], first["end_position"], first["year"], first.get("month"), first.get("quarter"))
            boundary_positions = [p for p in (low.find("contre"), low.find("après"), low.find("apres"), low.find("against"), low.find("after")) if p >= 0]
            cmp_pos = min(boundary_positions) if boundary_positions else -1
            compared = [o for o in observations if o["position"] > cmp_pos] if cmp_pos >= 0 else observations[1:]
            if compared:
                compared[0]["year"] = ref_year
                compared[0]["period_label"] = _period_label_for_measure(sentence, compared[0]["position"], compared[0]["end_position"], ref_year, compared[0].get("month"), compared[0].get("quarter"))

    # A coreferential comparison can inherit the current contextual year for
    # the first value when only the historical reference year is written:
    # "Leur niveau ... 3,1 milliards, contre 2,8 milliards en 2023" after a
    # 2024 sentence -> 3.1 in 2024 and 2.8 in 2023.
    if context is not None and context.current_year is not None and len(explicit_years) == 1 and len(observations) >= 2:
        cmp_positions = [p for p in (low.find("contre"), low.find("après"), low.find("apres")) if p >= 0]
        if cmp_positions:
            cmp_pos = min(cmp_positions)
            ref_year = explicit_years[0]
            first = observations[0]
            year_position = next((m.start() for m in _YEAR.finditer(sentence)), -1)
            if (first["position"] < cmp_pos < year_position and first.get("year") == ref_year
                    and first.get("month") is None and first.get("quarter") is None):
                first["year"] = context.current_year
                first["month"] = context.current_month
                first["quarter"] = context.current_quarter
                first["period_source"] = "context_unique"
                first["period_label"] = _period_label_for_measure(sentence, first["position"], first["end_position"], first["year"], first.get("month"), first.get("quarter"))

    # "Pour 2025, ... devrait atteindre A, après B en 2024".
    target_year = re.search(r"(?:^|[,;:]\s*)(?:pour|en)\s+((?:19|20)\d{2})\b", low[: observations[0]["position"] if observations else len(low)])
    if target_year and observations:
        observations[0]["year"] = int(target_year.group(1))
        observations[0]["period_source"] = "explicit"
    apres_pos = low.find("après") if "après" in low else low.find("apres")
    if apres_pos >= 0 and re.search(r"devrait|prévu|prévision", low):
        modal_positions=[p for p in (low.find("devrait"),low.find("prévu"),low.find("prévision")) if p >= 0]
        modal_pos=min(modal_positions) if modal_positions else -1
        for obs in observations:
            if apres_pos < modal_pos:
                obs["status"] = "forecast" if obs["position"] > modal_pos else "observed"
            else:
                obs["status"] = "forecast" if obs["position"] < apres_pos else "observed"
    if leading_year and "contre" in low and len(observations) >= 2 and len(explicit_years) >= 2:
        observations[0]["year"] = int(leading_year.group(1))
        # The compared value is normally the first measurement after "contre".
        contre_pos = low.find("contre")
        compared = [o for o in observations if o["position"] > contre_pos]
        if compared:
            compared[0]["year"] = explicit_years[-1]

    # "Entre 2020 et 2024, l'inflation est passée de 5,6 % à 7,2 %"
    # pairs the first value with the first boundary year and the second value
    # with the second boundary year.
    between_years = re.search(r"Entre\s+((?:19|20)\d{2})\s+et\s+((?:19|20)\d{2})", sentence, re.I)
    if between_years and len(observations) >= 2 and re.search(r"pass[ée]e?\s+de", low, re.I):
        observations[0]["year"] = int(between_years.group(1))
        observations[1]["year"] = int(between_years.group(2))
        observations[0]["period_source"] = observations[1]["period_source"] = "explicit_pair"

    # Example: "est passé de A en 2020 à B en 2021". Pair measures and years in order.
    if re.search(r"pass[ée]s?\s+de|passant\s+de", low) and len(observations) >= 2 and len(explicit_years) >= 2:
        for obs, year in zip(observations, explicit_years[-len(observations):]):
            obs["year"] = year

    # Explicit parenthesis: public ratio, then internal ratio, then external ratio.
    if re.search(r"taux\s+d['’]?endettement\s+public.*soit.*int[eé]rieur.*ext[eé]rieur", low):
        percents = [o for o in observations if o["unit"] in {"%", "% du PIB"}]
        if len(percents) >= 3:
            roles = [
                ("public_debt_ratio", INDICATOR_LABELS["public_debt_ratio"]),
                ("internal_debt_ratio", INDICATOR_LABELS["internal_debt_ratio"]),
                ("external_debt_ratio", INDICATOR_LABELS["external_debt_ratio"]),
            ]
            for obs, (code, label) in zip(percents[:3], roles):
                obs["code"], obs["label"] = code, label

    # “Entre 2001 et 2010 ... passant de A à B”.
    range_match = re.search(r"entre\s+((?:19|20)\d{2})\s+et\s+((?:19|20)\d{2})", low)
    if range_match and re.search(r"passant\s+de", low):
        public = [o for o in observations if o["code"] == "public_debt_ratio"]
        if len(public) >= 2:
            public[0]["year"] = int(range_match.group(1))
            public[1]["year"] = int(range_match.group(2))

    # “intérieur et extérieur ... respectivement A et B”.
    if "respectivement" in low and re.search(r"endettement\s+int[eé]rieur\s+et\s+ext[eé]rieur", low):
        percent_obs = [o for o in observations if o["unit"] in {"%", "% du PIB"}]
        if len(percent_obs) >= 2:
            percent_obs[-2]["code"], percent_obs[-2]["label"] = "internal_debt_ratio", INDICATOR_LABELS["internal_debt_ratio"]
            percent_obs[-1]["code"], percent_obs[-1]["label"] = "external_debt_ratio", INDICATOR_LABELS["external_debt_ratio"]

    # All percentages in an explicit external-debt sequence belong to that series.
    if re.search(r"taux\s+d['’]?endettement\s+ext[eé]rieur\s+de", low):
        for obs in observations:
            if obs["unit"] in {"%", "% du PIB"}:
                obs["code"], obs["label"] = "external_debt_ratio", INDICATOR_LABELS["external_debt_ratio"]

    if re.search(r"taux\s+d['’]?endettement\s+int[eé]rieur.*passant\s+de", low):
        for obs in observations:
            if obs["unit"] in {"%", "% du PIB"}:
                obs["code"], obs["label"] = "internal_debt_ratio", INDICATOR_LABELS["internal_debt_ratio"]

    # “poids de cette dette” is a share of the stock.
    if re.search(r"poids\s+de\s+cette\s+dette", low) and re.search(r"dette\s+ext[eé]rieure", low):
        for obs in observations:
            if obs["unit"] in {"%", "% du PIB"}:
                obs["code"], obs["label"] = "external_debt_share", INDICATOR_LABELS["external_debt_share"]

    # Equivalent ratios inherit the years of monetary observations in order.
    money = [o for o in observations if o["scale"] or o["currency"]]
    ratios = [o for o in observations if o["unit"] in {"%", "% du PIB"}]
    if money and ratios and re.search(r"[ée]quivalents?", low):
        for ratio, monetary in zip(ratios[-len(money):], money):
            ratio["year"] = monetary["year"]
            if re.search(r"dette\s+publique", low):
                ratio["code"], ratio["label"] = "public_debt_ratio", INDICATOR_LABELS["public_debt_ratio"]

    # In sentences that explain the rise of internal debt, percentages after
    # “part de la dette publique dans la dette de l’État” form a distinct series.
    share_match = re.search(r"part\s+de\s+la\s+dette\s+publique\s+dans\s+la\s+dette\s+de\s+l['’][ée]tat", low)
    if share_match:
        for obs in observations:
            if obs["unit"] in {"%", "% du PIB"} and obs["position"] >= share_match.start():
                obs["code"], obs["label"] = "public_debt_state_share", INDICATOR_LABELS["public_debt_state_share"]
                # This is a share of the State debt stock, not a GDP ratio.
                obs["unit"] = "%"
                obs["unit_source"] = "semantic"

    # All semantic/year overrides above must be reflected in the canonical
    # period label consumed by the UI and CSV export. This prevents a stale
    # label (e.g. 2010) after the event year was correctly reassigned to 2001.
    for obs in observations:
        obs["period_label"] = _period_label_for_measure(
            sentence, obs["position"], obs["end_position"],
            obs.get("year"), obs.get("month"), obs.get("quarter")
        )

    # Same-sentence annual anchor invariant. If one sibling explicitly states
    # "en 2024" and another sibling in the same sentence says "deux ans
    # auparavant", resolve the relative sibling from 2024 rather than stale
    # document context.
    explicit_years = [int(m.group()) for m in _YEAR.finditer(sentence)]
    if observations and len(set(explicit_years)) == 1 and re.search(
        r"\bdeux (?:ans|années|annees) (?:auparavant|plus (?:tôt|tot))\b", sentence, re.I
    ):
        anchor_year = explicit_years[0]
        for obs in observations:
            local = sentence[obs["end_position"]:min(len(sentence), obs["end_position"]+45)]
            if re.search(r"\bdeux (?:ans|années|annees) (?:auparavant|plus (?:tôt|tot))\b", local, re.I):
                obs["year"] = anchor_year - 2
                obs["period_source"] = "relative_context"
                obs["period_label"] = str(anchor_year - 2)

    # Generic "respectivement" alignment across a country comparison clause.
    # If the first clause names N indicators and the second clause supplies N
    # values "respectivement", map the values to those indicators in order.
    if "respectivement" in sentence.lower() and ";" in sentence:
        left_clause, right_clause = sentence.split(";", 1)
        left_mentions = _indicator_mentions(left_clause)
        # Collapse overlapping generic/specific mentions at the same location,
        # preferring the longest span (e.g. "inflation moyenne" over "inflation").
        collapsed=[]
        for mention in left_mentions:
            start_m,end_m,code,label=mention
            overlap=[x for x in collapsed if not (end_m <= x[0] or start_m >= x[1])]
            if overlap:
                best=max(overlap+[mention],key=lambda x:x[1]-x[0])
                collapsed=[x for x in collapsed if x not in overlap]
                collapsed.append(best)
            else:
                collapsed.append(mention)
        collapsed=sorted(collapsed,key=lambda x:x[0])

        indicator_seq=[]
        seen_codes=set()
        for _,_,code,label in collapsed:
            if code not in seen_codes:
                indicator_seq.append((code,label)); seen_codes.add(code)

        right_start = sentence.index(";") + 1
        right_obs = sorted([o for o in observations if o["position"] >= right_start], key=lambda o:o["position"])
        right_mentions=_country_mentions(right_clause)
        right_country=right_mentions[0][2] if right_mentions else None
        right_iso3=right_mentions[0][3] if right_mentions else None
        if right_country:
            for obs in right_obs:
                obs["country"], obs["country_iso3"] = right_country, right_iso3
                obs["country_source"] = "explicit_clause"
        if indicator_seq and len(right_obs) >= len(indicator_seq):
            for obs,(code,label) in zip(right_obs[:len(indicator_seq)], indicator_seq):
                obs["code"], obs["label"] = code, label
                obs["indicator_source"] = "respectively_alignment"
            # The opening annual year in the first clause applies to paired
            # annual values unless a value has its own explicit local period.
            left_years=[int(m.group()) for m in _YEAR.finditer(left_clause)]
            paired_year=left_years[-1] if left_years else None
            if paired_year is not None:
                for obs in right_obs[:len(indicator_seq)]:
                    after=sentence[obs["end_position"]:min(len(sentence),obs["end_position"]+55)]
                    has_own_period=bool(re.search(
                        r"\b(?:19|20)\d{2}\b|\b(?:T[1-4]|Q[1-4]|premier|deuxi[eè]me|troisi[eè]me|quatri[eè]me)\s+trimestre\b",
                        after,re.I
                    ))
                    if not has_own_period:
                        obs["year"]=paired_year
                        obs["quarter"]=None
                        obs["month"]=None
                        obs["period_source"]="context"
                        obs["period_label"]=str(paired_year)

    # Geography lists followed by values "respectively" are aligned in text
    # order. Groups remain groups and are never coerced into the document
    # country.
    arabic_geography_list = bool(re.search(r"[\u0600-\u06FF]", sentence) and re.search(r"\b(?:في|مقابل)\s+(?:الجزائر|المغرب|تونس)\b", sentence))
    if ("respectivement" in sentence.lower() or "على الترتيب" in sentence or arabic_geography_list) and observations:
        geo_mentions: list[tuple[int, str, str | None, str]] = []
        for start, _, name, iso3 in _country_mentions(sentence):
            geo_mentions.append((start, name, iso3, "country"))
        for pattern, name in _GEOGRAPHY_GROUPS:
            for m in re.finditer(pattern, sentence, re.I):
                geo_mentions.append((m.start(), name, None, "economic_group"))
        ordered_geo=[]
        seen_geo=set()
        for _, name, iso3, kind in sorted(geo_mentions):
            key=(name,iso3,kind)
            if key not in seen_geo:
                seen_geo.add(key); ordered_geo.append((name,iso3,kind))
        ordered_obs=sorted(observations,key=lambda o:o["position"])
        if len(ordered_geo) == len(ordered_obs):
            for obs,(name,iso3,kind) in zip(ordered_obs,ordered_geo):
                obs["country"],obs["country_iso3"]=name,iso3
                obs["country_source"]="respectively_geography_alignment"
                obs["geography_type"]=kind

    # In RTL table text, geometry extractors may flatten a conventional
    # ``indicator × year`` matrix into one sentence. Align each indicator's
    # values to the ordered header years instead of assigning every cell the
    # final visible year. This relies on table shape, never on document values.
    if re.search(r"[\u0600-\u06FF]", sentence) and "المؤشر" in sentence and observations:
        header_years = [int(m.group()) for m in _YEAR.finditer(sentence)]
        header_years = list(dict.fromkeys(header_years))
        if len(header_years) >= 2:
            by_code: dict[str, list[dict[str, Any]]] = {}
            for obs in sorted(observations, key=lambda o: o["position"]):
                by_code.setdefault(obs["code"], []).append(obs)
            for group in by_code.values():
                if len(group) == len(header_years):
                    for obs, year in zip(group, header_years):
                        obs["year"] = year
                        obs["month"] = obs["quarter"] = None
                        obs["period_label"] = str(year)
                        obs["period_source"] = "rtl_table_header"

    # ``during the same period`` copies an ordered year sequence from the
    # preceding sibling indicator (exports→imports, revenue→expenditure, etc.).
    if "الفترة نفسها" in sentence and observations:
        ordered_codes = []
        for obs in sorted(observations, key=lambda o: o["position"]):
            if obs["code"] not in ordered_codes:
                ordered_codes.append(obs["code"])
        if len(ordered_codes) >= 2:
            source = [o for o in observations if o["code"] == ordered_codes[0] and o.get("year")]
            target = [o for o in observations if o["code"] == ordered_codes[1]]
            if len(source) == len(target):
                for obs, src in zip(target, source):
                    obs["year"] = src["year"]
                    obs["month"], obs["quarter"] = src.get("month"), src.get("quarter")
                    obs["period_label"] = src.get("period_label")
                    obs["period_source"] = "shared_sibling_period"

    # Final monthly sibling invariant: relative month phrases resolve from the
    # nearest explicit monthly anchor in the same atomic clause, not from a
    # later explicit historical value or stale document context.
    explicit_month_obs = [
        o for o in observations
        if o.get("period_source") == "explicit" and o.get("month") is not None and o.get("year") is not None
    ]
    if explicit_month_obs:
        from app.services.context_resolver import shift_month
        for obs in observations:
            tail = sentence[obs["end_position"]:min(len(sentence), obs["end_position"]+48)]
            rel = re.search(
                r"\b(?:(un|1|deux|2|trois|3|quatre|4|cinq|5|six|6|sept|7|huit|8|neuf|9|dix|10|onze|11|douze|12)\\s+)?"
                r"mois\\s+(?:auparavant|plus\\s+(tôt|tot|tard))\\b", tail, re.I
            )
            if not rel:
                continue
            words={"un":1,"1":1,"deux":2,"2":2,"trois":3,"3":3,"quatre":4,"4":4,
                   "cinq":5,"5":5,"six":6,"6":6,"sept":7,"7":7,"huit":8,"8":8,
                   "neuf":9,"9":9,"dix":10,"10":10,"onze":11,"11":11,"douze":12,"12":12}
            n=words.get((rel.group(1) or "un").lower(),1)
            direction=1 if rel.group(2) and "tard" in rel.group(2).lower() else -1
            # Choose the closest explicit monthly event before this observation;
            # if none exists, use the first explicit monthly anchor in the clause.
            before=[x for x in explicit_month_obs if x["position"] < obs["position"]]
            anchor=max(before,key=lambda x:x["position"]) if before else explicit_month_obs[0]
            yy,mm=shift_month(anchor["year"],anchor["month"],direction*n)
            obs["year"],obs["month"],obs["quarter"]=yy,mm,None
            obs["period_source"]="relative_context"
            obs["period_label"]=_period_label_for_measure(
                sentence,obs["position"],obs["end_position"],yy,mm,None
            )

    # Final temporal invariant: sibling offsets are evaluated from the primary
    # explicit discourse anchor, never from another relative sibling. Keep this
    # at the end of semantic post-processing so later compatibility rules cannot
    # accidentally re-chain Q4 -> Q3 -> Q3.
    if observations and re.search(r"\bsix mois plus (?:tôt|tot)\b|\bsix months earlier\b", sentence, re.I):
        primary = next((o for o in observations if o.get("period_source") == "explicit" and o.get("quarter") is not None), None)
        if primary:
            from app.services.context_resolver import shift_quarter
            for obs in observations:
                tail = sentence[obs["end_position"]:min(len(sentence), obs["end_position"]+40)]
                if re.search(r"\bsix mois plus (?:tôt|tot)\b|\bsix months earlier\b", tail, re.I):
                    yy, qq = shift_quarter(primary.get("year"), primary.get("quarter"), -2)
                    obs["year"], obs["quarter"], obs["month"] = yy, qq, None
                    obs["period_source"] = "relative_context"
                    obs["period_label"] = _period_label_for_measure(
                        sentence, obs["position"], obs["end_position"], yy, None, qq
                    )

    # General local temporal-relation resolver.
    #
    # Relative expressions are bound to the atomic value whose local clause
    # contains them. A relation BEFORE the value has priority; only when none is
    # present do we inspect the text immediately AFTER the value. This prevents
    # a later sibling relation from hijacking the preceding value.
    if observations:
        ordered_by_pos = sorted(observations, key=lambda o:o["position"])
        explicit_anchors = [
            o for o in ordered_by_pos
            if o.get("period_source") == "explicit" and o.get("year") is not None
        ]

        def _anchor_for(obs):
            prior = [o for o in explicit_anchors if o["position"] < obs["position"]]
            if prior:
                a = prior[-1]
                return a.get("year"), a.get("quarter"), a.get("month")
            if explicit_anchors:
                later = [o for o in explicit_anchors if o["position"] > obs["position"]]
                if later:
                    a = later[0]
                    bridge = sentence[obs["end_position"]:a["position"]]
                    # A later explicit date across a contrastive clause belongs
                    # to that sibling clause, not to the current relative value.
                    if not re.search(r"\b(?:tandis que|alors que|whereas|while)\b", bridge, re.I):
                        return a.get("year"), a.get("quarter"), a.get("month")
            if context is not None:
                return (
                    context.discourse_year or context.current_year or context.anchor_year,
                    context.discourse_quarter or context.current_quarter,
                    context.discourse_month or context.current_month,
                )
            return None, None, None

        def _relation(scope: str):
            if re.search(r"\bdeux (?:ans|années|annees) (?:auparavant|plus (?:tôt|tot))\b|\btwo years earlier\b", scope, re.I):
                return -2, "year"
            if re.search(r"\b(?:l['’]année d['’]avant|l['’]annee d['’]avant|année précédente|annee precedente|un an plus tôt|un an plus tot|un an auparavant|previous year|last year)\b", scope, re.I):
                return -1, "year"
            if re.search(r"\b(?:année suivante|annee suivante|un an plus tard|next year|following year)\b", scope, re.I):
                return 1, "year"
            if re.search(r"\bdeux mois plus tard\b|\btwo months later\b", scope, re.I):
                return 2, "month"
            if re.search(r"\btrois mois (?:auparavant|plus (?:tôt|tot))\b|\bthree months earlier\b", scope, re.I):
                return -3, "month"
            if re.search(r"\btrois mois plus tard\b|\bthree months later\b", scope, re.I):
                return 3, "month"
            if re.search(r"\b(?:un mois auparavant|un mois plus (?:tôt|tot)|mois précédent|mois precedent|previous month)\b", scope, re.I):
                return -1, "month"
            if re.search(r"\b(?:un mois plus tard|mois suivant|next month)\b", scope, re.I):
                return 1, "month"
            return None

        for idx, obs in enumerate(ordered_by_pos):
            prev_end = ordered_by_pos[idx-1]["end_position"] if idx > 0 else 0
            next_start = ordered_by_pos[idx+1]["position"] if idx+1 < len(ordered_by_pos) else len(sentence)
            before = sentence[max(prev_end, obs["position"]-100):obs["position"]].lower().replace("’", "'")
            after = sentence[obs["end_position"]:min(next_start, obs["end_position"]+85)].lower().replace("’", "'")

            rel_before = _relation(before)
            rel_after = _relation(after)
            rel = rel_before or rel_after
            if rel is None:
                continue

            # If an explicit period occurs AFTER a relative phrase in the same
            # pre-value window, the explicit period belongs to the current value
            # and the earlier relative phrase belongs to the previous sibling.
            if rel_before is not None:
                rel_marks=list(re.finditer(
                    r"(?:deux (?:ans|années|annees) (?:auparavant|plus (?:tôt|tot))|"
                    r"l['’]année d['’]avant|année précédente|annee precedente|"
                    r"(?:un|deux|trois|six) mois (?:auparavant|plus (?:tôt|tot|tard))|"
                    r"mois précédent|mois precedent|mois suivant|"
                    r"trimestre précédent|trimestre precedent|trimestre suivant)",
                    before,re.I
                ))
                explicit_marks=list(re.finditer(
                    r"(?:\b(?:19|20)\d{2}\b|\b(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\b|\b(?:T|Q)[1-4]\b)",
                    before,re.I
                ))
                if rel_marks and explicit_marks and explicit_marks[-1].start() > rel_marks[-1].start():
                    continue

            # Explicit dates across a contrastive sibling clause do not belong
            # to this value. Only inspect the part of `after` before that boundary.
            local_after = re.split(r"\b(?:tandis que|alors que|whereas|while)\b", after, maxsplit=1, flags=re.I)[0]
            explicit_scope = before + " " + local_after
            has_explicit_local = obs.get("period_source") == "explicit" and bool(re.search(
                r"\b(?:19|20)\d{2}\b|"
                r"\b(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\b|"
                r"\b(?:T|Q)[1-4]\b|"
                r"\b(?:premier|deuxi[eè]me|troisi[eè]me|quatri[eè]me)\s+trimestre\b",
                explicit_scope, re.I
            ))
            # Once a relative expression is bound inside this atomic value
            # window, it is the period instruction for the value. Explicit dates
            # belonging to adjacent sibling values are anchors, not overrides.

            offset, unit = rel
            if rel_before is not None:
                prior = [o for o in explicit_anchors if o["position"] < obs["position"]]
                if prior:
                    a = prior[-1]
                    ay, aq, am = a.get("year"), a.get("quarter"), a.get("month")
                elif context is not None:
                    ay, aq, am = (
                        context.discourse_year or context.current_year or context.anchor_year,
                        context.discourse_quarter or context.current_quarter,
                        context.discourse_month or context.current_month,
                    )
                else:
                    ay, aq, am = None, None, None
            else:
                ay, aq, am = _anchor_for(obs)
            if ay is None:
                continue

            changed = False
            if unit == "year":
                obs["year"] = ay + offset
                # A year offset preserves the anchor's frequency when one exists;
                # this is essential for "same point one year earlier" cases.
                if am is not None:
                    obs["month"], obs["quarter"] = am, None
                elif aq is not None:
                    obs["quarter"], obs["month"] = aq, None
                else:
                    obs["quarter"], obs["month"] = None, None
                changed = True
            elif unit == "quarter" and aq is not None:
                from app.services.context_resolver import shift_quarter
                yy, qq = shift_quarter(ay, aq, offset)
                obs["year"], obs["quarter"], obs["month"] = yy, qq, None
                changed = True
            elif unit == "month":
                from app.services.context_resolver import shift_month, shift_quarter
                if am is not None:
                    yy, mm = shift_month(ay, am, offset)
                    obs["year"], obs["month"], obs["quarter"] = yy, mm, None
                    changed = True
                elif aq is not None and offset % 3 == 0:
                    yy, qq = shift_quarter(ay, aq, offset // 3)
                    obs["year"], obs["quarter"], obs["month"] = yy, qq, None
                    changed = True

            if changed:
                obs["period_source"] = "relative_context"
                obs["period_label"] = _period_label_for_measure(
                    sentence, obs["position"], obs["end_position"],
                    obs.get("year"), obs.get("month"), obs.get("quarter")
                )

    # Final local explicit-period invariant.
    # An explicit year written immediately after an atomic value is always
    # stronger than inherited/document context and relative siblings.
    for obs in observations:
        tail = sentence[obs["end_position"]:min(len(sentence), obs["end_position"]+55)]
        next_genuine = next((m for m in _MEASURE.finditer(tail)
                             if m.group("unit") or m.group("scale") or m.group("currency")), None)
        limit = next_genuine.start() if next_genuine else len(tail)
        local_tail = tail[:limit]

        ym = re.search(r"\b(?:en|pour|fin|à\s+fin|a\s+fin)\s+((?:19|20)\d{2})\b", local_tail, re.I)
        if ym:
            obs["year"] = int(ym.group(1))
            # Do not erase an explicit month/quarter attached to this value.
            obs["period_source"] = "explicit"
            obs["period_label"] = _period_label_for_measure(
                sentence, obs["position"], obs["end_position"],
                obs.get("year"), obs.get("month"), obs.get("quarter")
            )

    # Relative year immediately following a value is local to that value and is
    # resolved from the closest prior explicit annual anchor in the same clause.
    explicit_year_obs=sorted(
        [o for o in observations if o.get("period_source")=="explicit" and o.get("year") is not None],
        key=lambda o:o["position"]
    )
    if explicit_year_obs:
        for obs in observations:
            tail=sentence[obs["end_position"]:min(len(sentence),obs["end_position"]+48)]
            delta=None
            if re.search(r"\b(?:l['’])?ann[ée]e pr[ée]c[ée]dente\\b|\b(?:un an|1 an) (?:auparavant|plus (?:tôt|tot))\\b|\bprevious year\b",tail,re.I):
                delta=-1
            elif re.search(r"\bdeux (?:ans|ann[ée]es) (?:auparavant|plus (?:tôt|tot))\\b|\btwo years earlier\b",tail,re.I):
                delta=-2
            elif re.search(r"\bann[ée]e suivante\\b|\bnext year\b",tail,re.I):
                delta=1
            if delta is None: continue
            anchors=[a for a in explicit_year_obs if a["position"]<obs["position"]]
            if not anchors: continue
            anchor=anchors[-1]
            obs["year"]=anchor["year"]+delta
            # Preserve same-point month/quarter only for explicit same-period
            # wording; plain previous year remains annual.
            obs["month"]=None
            obs["quarter"]=None
            obs["period_source"]="relative_context"
            obs["period_label"]=str(obs["year"])

    # Last temporal normalization pass: a relative phrase immediately following
    # a value is part of that value's event. Resolve it from the closest prior
    # explicit monthly anchor, after all compatibility repairs have run.
    explicit_month_obs = sorted(
        [o for o in observations if o.get("period_source") == "explicit"
         and o.get("month") is not None and o.get("year") is not None],
        key=lambda o:o["position"]
    )
    if explicit_month_obs:
        from app.services.context_resolver import shift_month
        word_n={"un":1,"1":1,"deux":2,"2":2,"trois":3,"3":3,"quatre":4,"4":4,
                "cinq":5,"5":5,"six":6,"6":6,"sept":7,"7":7,"huit":8,"8":8,
                "neuf":9,"9":9,"dix":10,"10":10,"onze":11,"11":11,"douze":12,"12":12}
        for obs in observations:
            tail=sentence[obs["end_position"]:min(len(sentence),obs["end_position"]+42)]
            rel=re.search(
                r"\b(?:(un|1|deux|2|trois|3|quatre|4|cinq|5|six|6|sept|7|huit|8|neuf|9|dix|10|onze|11|douze|12)\\s+)?"
                r"mois\\s+(auparavant|plus\\s+(?:tôt|tot|tard))\\b",tail,re.I
            )
            if not rel: continue
            anchors=[a for a in explicit_month_obs if a["position"] < obs["position"]]
            if not anchors: continue
            anchor=anchors[-1]
            n=word_n.get((rel.group(1) or "un").lower(),1)
            direction=1 if "tard" in rel.group(2).lower() else -1
            yy,mm=shift_month(anchor["year"],anchor["month"],direction*n)
            obs["year"],obs["month"],obs["quarter"]=yy,mm,None
            obs["period_source"]="relative_context"
            obs["period_label"]=_period_label_for_measure(
                sentence,obs["position"],obs["end_position"],yy,mm,None
            )

    # Absolute local dates are the highest temporal authority. Re-apply them
    # last so no relative sibling repair can overwrite "value in December 2023".
    for obs in observations:
        tail=sentence[obs["end_position"]:min(len(sentence),obs["end_position"]+38)]
        local_year=re.search(r"\b((?:19|20)\d{2})\b",tail)
        local_month=None
        for word,num in _MONTH_WORDS.items():
            mm=re.search(rf"\b{re.escape(word)}\b",tail,re.I)
            if mm and (local_month is None or mm.start()<local_month[0]):
                local_month=(mm.start(),num)
        # Only accept a date before another numeric economic measurement.
        next_measure=next(
            (m for m in _MEASURE.finditer(tail) if m.group("unit") or m.group("scale") or m.group("currency")),
            None
        )
        boundary=next_measure.start() if next_measure else len(tail)
        if local_year and local_year.start()<boundary:
            obs["year"]=int(local_year.group(1))
            if local_month and local_month[0]<boundary:
                obs["month"]=local_month[1]; obs["quarter"]=None
            obs["period_source"]="explicit"
            obs["period_label"]=_period_label_for_measure(
                sentence,obs["position"],obs["end_position"],
                obs.get("year"),obs.get("month"),obs.get("quarter")
            )

    # Final relative-year authority (after all compatibility passes).
    anchors=sorted(
        [o for o in observations if o.get("year") is not None and o.get("period_source")=="explicit"],
        key=lambda o:o["position"]
    )
    for obs in observations:
        tail=sentence[obs["end_position"]:min(len(sentence),obs["end_position"]+45)]
        delta = -1 if re.search(r"\b(?:l['’])?année précédente\b|\bprevious year\b",tail,re.I) else (
            -2 if re.search(r"\bdeux (?:ans|années) (?:auparavant|plus tôt)\b|\btwo years earlier\b",tail,re.I) else None
        )
        if delta is None: continue
        prior=[a for a in anchors if a["position"]<obs["position"]]
        if prior:
            obs["year"]=prior[-1]["year"]+delta
            obs["month"]=None; obs["quarter"]=None
            obs["period_source"]="relative_context"; obs["period_label"]=str(obs["year"])

    # Period ranges and averages are first-class periods, never aliases for the
    # terminal year. This applies to any indicator and any document.
    range_match = re.search(
        r"\b(?:moyenne\s+(?:sur\s+)?(?:la\s+)?p[ée]riode|durant\s+(?:la\s+)?p[ée]riode|"
        r"au\s+cours\s+de\s+(?:la\s+)?(?:sous[- ]?)?p[ée]riode|durant\s+la\s+d[ée]cennie|p[ée]riode)\s*"
        r"((?:19|20)\d{2})\s*[-–]\s*((?:19|20)\d{2})\b", sentence, re.I
    )
    since_match = re.search(r"\bdepuis\s+((?:19|20)\d{2})\b", sentence, re.I)
    for obs in observations:
        if range_match:
            start, end = range_match.group(1), range_match.group(2)
            obs["year"] = None; obs["month"] = None; obs["quarter"] = None
            obs["period_type"] = "average_range" if re.search(r"\bmoyenne|rythme\s+(?:annuel\s+)?moyen", sentence, re.I) else "range"
            obs["period_start"], obs["period_end"] = start, end
            obs["frequency"] = "annual"
            obs["period_source"] = "explicit_range"
            obs["period_label"] = f"{start}-{end}"
        elif since_match:
            start = since_match.group(1)
            obs["year"] = None; obs["month"] = None; obs["quarter"] = None
            obs["period_type"] = "since"; obs["period_start"] = start; obs["period_end"] = None
            obs["frequency"] = "annual"; obs["period_source"] = "explicit_open_range"
            obs["period_label"] = f"Depuis {start}"
        elif re.search(r"\ben\s+moyenne\s+par\s+an\b|\brythme\s+annuel\s+moyen\b", sentence, re.I) and obs.get("period_source") != "explicit":
            # A stale discourse year must not turn an undated multi-year
            # average into a point observation.
            obs["year"] = None; obs["month"] = None; obs["quarter"] = None
            obs["period_type"] = "annual_average_unknown_range"
            obs["period_start"] = None; obs["period_end"] = None
            obs["frequency"] = "annual"; obs["period_source"] = "explicit_average_unknown_range"
            obs["period_label"] = "Moyenne annuelle — période non précisée"
    explicit_ranges=[(m.group(1),m.group(2)) for m in re.finditer(r"\b((?:19|20)\d{2})\s*[-–]\s*((?:19|20)\d{2})\b",sentence)]
    if "respectivement" in sentence.lower() and len(explicit_ranges)==len(observations) and len(observations)>1:
        for obs,(start,end) in zip(sorted(observations,key=lambda o:o["position"]),explicit_ranges):
            obs["year"]=None; obs["month"]=None; obs["quarter"]=None
            obs["period_type"]="average_range" if re.search(r"\bmoyenne|rythme\s+(?:annuel\s+)?moyen",sentence,re.I) else "range"
            obs["period_start"],obs["period_end"]=start,end
            obs["frequency"]="annual"; obs["period_source"]="respectively_range_alignment"
            obs["period_label"]=f"{start}-{end}"

    # Final RTL-safe relative-period reconciliation. Run after generic
    # proximity repair so Arabic comparison phrases remain authoritative.
    if re.search(r"[\u0600-\u06FF]", sentence) and observations:
        anchor = observations[0]
        for obs in observations[1:]:
            tail = sentence[obs["end_position"]:min(len(sentence), obs["end_position"] + 55)]
            if re.search(r"الربع\s+السابق", tail) and anchor.get("year") and anchor.get("quarter"):
                from app.services.context_resolver import shift_quarter
                obs["year"], obs["quarter"] = shift_quarter(anchor["year"], anchor["quarter"], -1)
                obs["month"] = None
                obs["period_source"] = "relative_context"
                obs["period_label"] = f"{obs['year']}-Q{obs['quarter']}"
            elif re.search(r"العام\s+السابق|السنة\s+السابقة|قبل\s+عام", tail) and anchor.get("year"):
                obs["year"] = anchor["year"] - 1
                obs["quarter"] = anchor.get("quarter") if re.search(r"قبل\s+عام", tail) else None
                obs["month"] = anchor.get("month") if re.search(r"قبل\s+عام", tail) else None
                obs["period_source"] = "relative_context"
                obs["period_label"] = _period_label_for_measure(sentence, obs["position"], obs["end_position"], obs["year"], obs.get("month"), obs.get("quarter"))

    # Sentence-subject scope: when a specific series is introduced before the
    # first measure, later explanatory words must not relabel its coordinated
    # values. This is intentionally limited to unambiguous specialist heads.
    first_measure = min((o["position"] for o in observations), default=len(sentence))
    subject_scope = low[:first_measure]
    scoped_code = None
    if re.search(r"inflation\s+sous[- ]jacente", subject_scope, re.I):
        scoped_code = "core_inflation"
    elif re.search(r"prix\s+des\s+concurrents", subject_scope, re.I):
        scoped_code = "competitor_prices"
    elif re.search(r"taux\s+de\s+change\s+effectif\s+r[ée]el|\btcer\b", subject_scope, re.I):
        scoped_code = "real_effective_exchange_rate"
    elif re.search(r"taux\s+de\s+change\s+effectif\s+nominal|\btcen\b", subject_scope, re.I):
        scoped_code = "nominal_effective_exchange_rate"
    if scoped_code:
        for obs in observations:
            if obs.get("unit") in {"%", "% du PIB"}:
                obs["code"] = scoped_code
                obs["label"] = INDICATOR_LABELS[scoped_code]
                obs["indicator_source"] = "explicit_subject_scope"

    # Apply same-period sibling alignment last: generic comparison logic above
    # may derive previous years for ``from X to Y`` before learning that the
    # second series explicitly says it covers the same period.
    if "الفترة نفسها" in sentence and observations:
        codes = []
        for obs in sorted(observations, key=lambda o: o["position"]):
            if obs["code"] not in codes:
                codes.append(obs["code"])
        if len(codes) >= 2:
            source = [o for o in observations if o["code"] == codes[0]]
            target = [o for o in observations if o["code"] == codes[1]]
            if len(source) == len(target):
                explicit_years = list(dict.fromkeys(int(m.group()) for m in _YEAR.finditer(sentence)))
                for index, (obs, src) in enumerate(zip(target, source)):
                    shared_year = explicit_years[index] if len(explicit_years) == len(target) else src.get("year")
                    obs["year"], obs["month"], obs["quarter"] = shared_year, src.get("month"), src.get("quarter")
                    obs["period_label"] = str(shared_year) if shared_year is not None else src.get("period_label")
                    obs["period_source"] = "shared_sibling_period"

    # Remove exact duplicates created by overlapping patterns.
    unique: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for obs in observations:
        key = (obs["code"], obs["value"], obs["year"], obs["unit"], obs["scale"], obs["currency"],
               obs.get("period_type"), obs.get("period_start"), obs.get("period_end"), obs.get("sector"))
        if key not in seen:
            seen.add(key)
            unique.append(obs)
    return unique


def _event_confidence(cur: dict[str, Any], sentence: str, context: dict[str, Any]):
    explicit_country, _ = detect_country(sentence, None)
    result = score_event(cur, sentence, context, explicit_country=bool(explicit_country))
    return (
        result["confidence"],
        result["confidence_evidence"],
        result["confidence_warnings"],
        result["validation_evidence"],
        result["validation_warnings"],
        result.get("validation_dimensions", {}),
    )

def _fact_rows(document: dict, sentence: str, observations: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    """Create one database row per atomic observation.

    Comparisons are derived only against the immediately preceding dated value
    for the same indicator and unit inside the sentence. This preserves every
    year in a series instead of collapsing a sentence into one current value.
    """
    grouped: dict[tuple[str, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        grouped[(obs["code"], obs["unit"], obs["scale"], obs["currency"])].append(obs)

    rows: list[dict[str, Any]] = []
    for (code, _, _, _), group in grouped.items():
        ordered = sorted(group, key=lambda o: (o["year"] is None, o["year"] or 9999, o["position"]))
        previous: dict[str, Any] | None = None
        for event_index, cur in enumerate(ordered, start=1):
            ref = previous if previous and previous.get("year") is not None and cur.get("year") is not None else None
            absolute = relative = None
            direction = "unknown"
            if ref is not None:
                absolute = round(cur["value"] - ref["value"], 4)
                relative = None if ref["value"] == 0 else round(absolute / abs(ref["value"]) * 100, 2)
                direction = "increase" if absolute > 0 else "decrease" if absolute < 0 else "stable"
            confidence, confidence_evidence, confidence_warnings, validation_evidence, validation_warnings, validation_dimensions = _event_confidence(cur, sentence, context)
            event_country = cur.get("country") or context.get("country")
            event_iso3 = cur.get("country_iso3") or context.get("country_iso3")
            meta = indicator_metadata(code, sentence)
            # Indicator metadata must reflect the atomic event's frequency.
            # A quarter mentioned for another indicator elsewhere in the same
            # sentence must not relabel an annual GDP observation as quarterly.
            if code == "gdp_growth":
                meta = dict(meta)
                if cur.get("quarter") is not None:
                    meta["official_name_fr"] = "Taux de croissance du PIB (variation trimestrielle)"
                else:
                    meta["official_name_fr"] = "Taux de croissance du PIB (variation annuelle)"
            series_id = build_series_id(event_iso3 or context.get("country_iso3"), meta["indicator_id"], cur["unit"], cur["scale"], cur["currency"])
            rows.append({
                "document_id": document.get("document_id", ""),
                "language": document.get("language") or context.get("language") or "fr",
                "country": event_country or context.get("country"),
                "country_iso3": event_iso3 or context.get("country_iso3"),
                "country_source": cur.get("country_source"),
                "indicator_code": code,
                "indicator_id": meta["indicator_id"],
                "indicator": meta["official_name_fr"],
                "indicator_official_name_fr": meta["official_name_fr"],
                "indicator_official_name_en": meta["official_name_en"],
                "indicator_raw": cur["label"],
                "indicator_category": meta["category"],
                "indicator_definition": meta["definition_fr"],
                "external_standard": meta.get("external_standard"),
                "external_indicator_code": meta.get("external_code"),
                "series_id": series_id,
                "topic": TOPICS.get(code, "autre"),
                "fact_type": cur["status"],
                "value_type": "level",
                "current_value": cur["value"],
                "current_value_raw": cur["raw"],
                "current_unit": cur["unit"],
                "current_scale": cur["scale"],
                "current_currency": cur["currency"],
                "variation_value": None,
                "variation_unit": None,
                "current_month": cur["month"],
                "current_quarter": cur["quarter"],
                "current_year": cur["year"],
                "current_period_label": cur.get("period_label"),
                "period_type": cur.get("period_type") or ("year" if cur.get("year") is not None else None),
                "period_start": cur.get("period_start") or (str(cur.get("year")) if cur.get("year") is not None else None),
                "period_end": cur.get("period_end") or (str(cur.get("year")) if cur.get("year") is not None else None),
                "frequency": cur.get("frequency"),
                "reference_period": cur.get("reference_period"),
                "period_resolution_source": cur.get("period_source"),
                "geography_type": cur.get("geography_type") or ("country" if event_country else "unknown"),
                "sector": cur.get("sector"),
                "subsector": cur.get("subsector"),
                "partner_geography": cur.get("partner_geography"),
                "reference_value": ref["value"] if ref else None,
                "reference_value_raw": ref["raw"] if ref else None,
                "reference_unit": ref["unit"] if ref else None,
                "reference_scale": ref["scale"] if ref else None,
                "reference_currency": ref["currency"] if ref else None,
                "reference_month": ref["month"] if ref else None,
                "reference_quarter": ref["quarter"] if ref else None,
                "reference_year": ref["year"] if ref else None,
                "reference_period_label": ref.get("period_label") if ref else None,
                "absolute_change": absolute,
                "relative_change": relative,
                "direction": direction,
                "comparison_type": "annual" if ref else None,
                "source": context.get("source"),
                "source_url": document.get("source_url"),
                "source_filename": document.get("filename"),
                "sentence": sentence,
                "confidence": confidence,
                "confidence_evidence": confidence_evidence,
                "confidence_warnings": confidence_warnings,
                "validation_evidence": validation_evidence,
                "validation_warnings": validation_warnings,
                "validation_dimensions": validation_dimensions,
                "validation_status": "À vérifier",
                "conflict_status": False,
                "observation_type": cur["status"],
                "needs_review": True,
                "review_reason": None,
                "comparison_index": event_index,
                "comparison_count": len(ordered),
                "event_id": f"{document.get('document_id','')}:{code}:{cur.get('year')}:{cur.get('value')}:{cur.get('position')}",
                "table_page": cur.get("table_page"),
                "table_index": cur.get("table_index"),
                "table_row_label": cur.get("table_row_label"),
                "table_column_label": cur.get("table_column_label"),
                "table_bbox": cur.get("table_bbox"),
            })
            if cur.get("year") is not None:
                previous = cur
    return rows


_DEBT_ANNEX_ROW = re.compile(
    r"\b(?P<year>(?:19|20)\d{2})\s+"
    r"(?P<total>[-+]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<internal>[-+]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<external>[-+]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<int_share>[-+]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<ext_share>[-+]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<int_gdp>[-+]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<ext_gdp>[-+]?\d+(?:[.,]\d+)?)\s+"
    r"(?P<total_gdp>[-+]?\d+(?:[.,]\d+)?)(?=\s+(?:19|20)\d{2}\b|\s+Source\s*:|$)",
    re.I,
)

def _structured_debt_annex_rows(document: dict, context: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract strongly-typed macroeconomic debt series from Annex 2 tables.

    This intentionally does *not* parse generic annexes or regression tables.
    It activates only when the page explicitly identifies the public-debt
    evolution table and the expected 8-column numeric schema is present.
    """
    text=document.get("text") or ""
    pages=_split_pages(text)
    out: list[dict[str, Any]]=[]
    specs=[
        ("total", "public_debt_stock", "million", "TND", None),
        ("internal", "internal_debt_stock", "million", "TND", None),
        ("external", "external_debt_stock", "million", "TND", None),
        ("int_share", "internal_debt_share", None, None, "%"),
        ("ext_share", "external_debt_share", None, None, "%"),
        ("int_gdp", "internal_debt_ratio", None, None, "% du PIB"),
        ("ext_gdp", "external_debt_ratio", None, None, "% du PIB"),
        ("total_gdp", "public_debt_ratio", None, None, "% du PIB"),
    ]
    for page_no,page_text in pages:
        if not re.search(r"Annexe\s*2\s*:\s*Evolution\s+de\s+la\s+dette\s+publique", page_text, re.I):
            continue
        # Require the table schema, not merely the annex title.
        if not (re.search(r"\(MDT\)", page_text, re.I) and re.search(r"%\s*du\s*PIB", page_text, re.I)):
            continue
        page_context=dict(context)
        page_context["source"] = context.get("source") or "Ministère des finances"
        for m in _DEBT_ANNEX_ROW.finditer(page_text):
            year=int(m.group("year"))
            observations=[]
            for idx,(field,code,scale,currency,unit) in enumerate(specs):
                value=_parse_number(m.group(field))
                if value is None: continue
                # Internal/external debt stock have dedicated codes in the
                # structured table layer; registry metadata below maps them.
                label=INDICATOR_LABELS.get(code, code)
                observations.append({
                    "code":code,"label":label,"value":value,"raw":m.group(field),
                    "year":year,"month":None,"quarter":None,"status":"observed",
                    "indicator_source":"explicit","unit_source":"explicit","period_source":"explicit",
                    "unit":unit,"scale":scale,"currency":currency,
                    "position":idx*10,"end_position":idx*10+5,"period_label":str(year),
                })
            synthetic=f"Annexe 2 — Evolution de la dette publique, année {year} (tableau macroéconomique)."
            rows=_fact_rows(document, synthetic, observations, page_context)
            for row in rows:
                row["page_number"] = page_no
                row["extraction_method"] = "structured_macro_table"
                row["confidence"] = max(float(row.get("confidence") or 0), 0.96)
                row["validation_status"] = "Validé"
                row["needs_review"] = False
                row["review_reason"] = None
            out.extend(rows)
    return out

_TABLE_HEADER_SPECS = [
    (r"inflation\s+(?:moyenne|average)", "inflation_annual_average", "%", None, None),
    (r"inflation(?:\s+ipc)?", "inflation_rate", "%", None, None),
    (r"ch[oô]mage|chomage|unemployment", "unemployment_rate", "%", None, None),
    (r"taux\s+d['’]?activit[eé]|activity\s+rate", "activity_rate", "%", None, None),
    (r"dette(?:\s+publique)?\s*\(%\s*(?:du\s+)?PIB\)|public\s+debt\s*\(%\s*GDP\)", "public_debt_ratio", "% du PIB", None, None),
    (r"croissance(?:\s+du\s+PIB)?\s*\(%\)|GDP\s+growth\s*\(%\)", "gdp_growth", "%", None, None),
    (r"r[eé]serves?(?:\s+officielles?)?(?:\s+de\s+change)?", "foreign_exchange_reserves", None, "milliard", None),
    (r"exportations?|exports?", "exports", None, None, None),
    (r"importations?|imports?", "imports", None, None, None),
]


def _generic_table_schema(header: str, country_iso3: str | None = None) -> list[tuple[str, str | None, str | None, str | None]]:
    """Infer ordered economic columns from a table header.

    The parser is deliberately schema-driven instead of country-driven: a new
    country or a different column subset does not require a new branch.  At
    least two recognised economic columns are required to avoid regression
    matrices and arbitrary numeric layouts.
    """
    candidates: list[tuple[int, int, str, str | None, str | None, str | None]] = []
    for pattern, code, unit, scale, currency in _TABLE_HEADER_SPECS:
        matches = list(re.finditer(pattern, header, re.I))
        if not matches:
            continue
        m = matches[-1]
        # Avoid a broader "inflation" duplicate when "inflation moyenne" is present.
        if code == "inflation_rate" and re.search(r"inflation\s+(?:moyenne|average)", m.group(0), re.I):
            continue
        local = header[m.start():min(len(header), m.end()+80)]
        detected_currency = detect_currency(local, country_iso3) or currency
        if scale is None:
            if re.search(r"\b(?:Mds?|milliards?|bn)\b", local, re.I):
                scale = "milliard"
            elif re.search(r"\b(?:millions?|mn)\b", local, re.I):
                scale = "million"
        candidates.append((m.start(), m.end(), code, unit, scale, detected_currency))
    if any(item[2] == "inflation_annual_average" for item in candidates):
        candidates = [item for item in candidates if item[2] != "inflation_rate"]
    ordered=[]
    for item in sorted(candidates, key=lambda x:x[0]):
        code=item[2]
        if any(x[0]==code for x in ordered):
            continue
        ordered.append((code,item[3],item[4],item[5]))
    return ordered


def _structured_body_table_rows(document: dict, context: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse macro tables with row-local context taking precedence.

    Country precedence is deliberately local-first:
    explicit country in the current table row > table/document context.
    This prevents a multi-country table from inheriting the country of the
    surrounding chapter. Annex/Appendix pages are still removed upstream.
    """
    out: list[dict[str, Any]] = []
    for page_no, page_text in _split_pages(document.get("text") or ""):
        years=list(re.finditer(r"\b(?:19|20)\d{2}\b", page_text))
        if not years:
            continue
        first=years[0]
        header=page_text[max(0, first.start()-900):first.start()]
        if not re.search(r"\b(?:Ann[ée]e|Annee|Year|P[ée]riode|Periode)\b", header, re.I):
            continue
        schema=_generic_table_schema(header, context.get("country_iso3"))
        if len(schema) < 2:
            continue
        if re.search(r"coefficient|p[- ]?value|statistique\s+t|t[- ]?stat|R\s*[²2]|erreur\s+std|standard\s+error", header, re.I):
            continue

        previous_end=max(0, first.start()-250)
        for idx, ym in enumerate(years):
            year=int(ym.group(0))
            # The row label (not the chapter) is authoritative when present.
            # Restrict the lookup to text since the previous row/year so a
            # country from an earlier row cannot bleed into this one.
            prefix_start = years[idx-1].end() if idx > 0 else max(0, ym.start()-260)
            row_prefix = page_text[prefix_start:ym.start()]
            mentions = country_mentions(row_prefix)
            if mentions:
                _, _, row_country, row_iso3 = mentions[-1]
                country_source = "explicit_table_row"
            else:
                row_country, row_iso3 = context.get("country"), context.get("country_iso3")
                country_source = "document" if row_country else "missing"

            segment=page_text[ym.end(): years[idx+1].start() if idx+1 < len(years) else min(len(page_text), ym.end()+450)]
            numbers=[]
            cursor=0
            for nm in re.finditer(r"[-+]?\d+(?:[.,]\d+)?", segment):
                prefix=segment[cursor:nm.start()]
                if len(numbers)==0 and len(prefix.strip()) > 15 and re.search(r"[A-Za-zÀ-ÿ]{4,}", prefix):
                    break
                numbers.append(_parse_number(nm.group(0)))
                cursor=nm.end()
                if len(numbers) >= len(schema):
                    break
            if len(numbers) < len(schema) or any(v is None for v in numbers):
                continue
            observations=[]
            for col,(code,unit,scale,currency) in enumerate(schema):
                value=numbers[col]
                local_currency=currency
                if scale and not local_currency:
                    local_currency=current_currency_for_country(row_iso3)
                observations.append({
                    "code":code,"label":INDICATOR_LABELS.get(code, code),"value":value,"raw":str(value),
                    "year":year,"month":None,"quarter":None,"status":"observed",
                    "indicator_source":"explicit_table","unit_source":"explicit_table","period_source":"explicit_table",
                    "unit":unit,"scale":scale,"currency":local_currency,"position":col*10,"end_position":col*10+1,
                    "period_label":str(year),"country":row_country,"country_iso3":row_iso3,
                    "country_source":country_source,
                })
            sentence=f"Tableau macroéconomique principal — {row_country or 'pays non précisé'} — année {year}."
            row_context={**context, "country":row_country, "country_iso3":row_iso3}
            rows=_fact_rows(document,sentence,observations,row_context)
            for row in rows:
                row["page_number"]=page_no
                row["table_source"]="body_table"
                row["conflict_scope"]="document"
            out.extend(rows)
    return out


def _raw_decimal_places(raw: str | None) -> int:
    token = str(raw or "").replace(" ", "")
    m = re.search(r"[-+]?\d+[,.](\d+)", token)
    return len(m.group(1)) if m else 0

def _dedup_key(row: dict[str, Any]) -> tuple[Any, ...]:
    """Canonical duplicate key with monetary-scale normalization."""
    value = row.get("current_value")
    scale = str(row.get("current_scale") or "").lower()
    currency = row.get("current_currency")
    unit = row.get("current_unit")
    if value is not None and currency and scale in {"million", "millions", "milliard", "milliards"}:
        factor = 1_000_000 if scale.startswith("million") else 1_000_000_000
        canonical_value = round(float(value) * factor, 2)
        measure = ("money", currency)
    else:
        canonical_value = round(float(value), 8) if value is not None else None
        measure = (unit, scale, currency)
    return (
        row.get("indicator_code"), canonical_value,
        row.get("current_year"), row.get("current_month"), row.get("current_quarter"),
        measure, row.get("country_iso3") or row.get("country"),
        row.get("fact_type") or row.get("observation_type") or "observed",
        row.get("sector"), row.get("subsector"),
        row.get("period_type"), row.get("period_start"), row.get("period_end"),
        row.get("table_page"), row.get("table_index"), row.get("table_row_label"), row.get("table_column_label"),
    )


def _rounding_equivalent(group: list[dict[str, Any]]) -> bool:
    """Return True when distinct values differ only by published rounding.

    Example: 52.22% in narrative text and 52.2% in an annex table are
    compatible, whereas 52.2% and 57.2% are genuine contradictions.
    """
    vals=[r for r in group if r.get("current_value") is not None]
    if len(vals) < 2:
        return True
    precisions=[]
    for r in vals:
        precisions.append(_raw_decimal_places(r.get("current_value_raw")))
    coarsest=min(precisions) if precisions else 0
    quantum = Decimal("1") if coarsest == 0 else Decimal("1").scaleb(-coarsest)
    rounded={
        Decimal(str(r["current_value"])).quantize(quantum, rounding=ROUND_HALF_UP)
        for r in vals
    }
    return len(rounded) <= 1

def run_multi_agent(
    document: dict,
    model: str | None = None,
    progress_callback: Callable[[str], None] | None = None,
    partial_callback: Callable[[list[dict], int, int], None] | None = None,
) -> list[dict[str, Any]]:
    """Deterministic, context-aware economic extraction pipeline.

    The public name is intentionally preserved for dashboard compatibility.
    No local generative LLM is required. Ambiguous associations are retained
    only when the document context is strong enough; otherwise they are rejected.
    """
    global _LAST_TRACE
    started = time.time()
    progress = progress_callback or (lambda _: None)
    progress("Lecture structurée du document…")
    document_text = document.get("text") or ""
    candidates = _candidate_sentences(document_text)
    # Some benchmark/report bundles contain independent chapter-level articles.
    # In that case contradictions are evaluated inside each chapter/page scope,
    # not across unrelated chapters that happen to reuse the same year/indicator.
    chapter_scoped = len(re.findall(r"Chapitre\s+\d+\s*[—-]\s*Conjoncture\s+[ée]conomique", document_text, re.I)) >= 2
    progress(f"{len(candidates)} passage(s) chiffré(s) pertinent(s) détecté(s)…")
    base_context = _context(document, candidates)
    doc_context = DocumentContext.from_document(document)
    doc_context.last_country = base_context.get("country")
    doc_context.last_country_iso3 = base_context.get("country_iso3")

    rows: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    numerical_coverage: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    total = max(len(candidates), 1)
    last_geography_sequence: list[tuple[str, str | None, str]] = []

    for idx, item in enumerate(candidates, start=1):
        sentence = item["text"]
        source_sentence = item.get("parent_sentence") or sentence
        section_country = item.get("section_country")
        section_iso3 = item.get("section_country_iso3")
        # A heading is a forward-only context boundary: it applies to this and
        # subsequent sentences, never to the event before the heading.
        if section_country:
            doc_context.last_country = section_country
            doc_context.last_country_iso3 = section_iso3
        explicit_country, explicit_iso3 = detect_country(sentence, None)
        semantic_context_sentence = item.get("semantic_context_sentence")
        semantic_hint = _clause_semantic_hint(sentence, f"{semantic_context_sentence or ''} {source_sentence}")
        parent_mentions=_indicator_mentions(source_sentence)
        collapsed_parent=[]
        for mention in parent_mentions:
            overlaps=[x for x in collapsed_parent if not (mention[1] <= x[0] or mention[0] >= x[1])]
            if overlaps:
                best=max(overlaps+[mention],key=lambda x:x[1]-x[0])
                collapsed_parent=[x for x in collapsed_parent if x not in overlaps];collapsed_parent.append(best)
            else:
                collapsed_parent.append(mention)
        parent_codes=[]
        for _,_,parent_code,parent_label in sorted(collapsed_parent):
            if parent_code not in {code for code,_ in parent_codes}:
                parent_codes.append((parent_code,parent_label))
        carrier_mentions = _indicator_mentions(semantic_context_sentence or "")
        carrier_codes: list[tuple[str, str]] = []
        for _,_,carrier_code,carrier_label in carrier_mentions:
            if carrier_code not in {code for code,_ in carrier_codes}:
                carrier_codes.append((carrier_code,carrier_label))
        contextual = doc_context.contextual_indicators(sentence)
        first_explicit_start = min((m[0] for m in parent_mentions), default=len(sentence))
        leading_coreference = re.search(
            r"\b(?:il|elle|ils|elles|ce taux|ce ratio|ce niveau|leur niveau)\b",
            sentence[:first_explicit_start], re.I,
        )
        # An explicit indicator in a later coordinated clause cannot provide
        # backward context for a leading pronoun.  Use discourse context for
        # the pronoun, then let the explicit indicator bind its own value.
        fallback_indicators = (
            semantic_hint
            or (contextual if leading_coreference and contextual else [])
            or (parent_codes if len(parent_codes)==1 else [])
            or (carrier_codes if len(carrier_codes)==1 else [])
            or ([carrier_codes[-1]] if carrier_codes and re.match(r"^\s*(?:وفي|وخلال|خلال|أما)\b", sentence) else [])
            or contextual
        )
        observations = _extract_observations(sentence, fallback_indicators=fallback_indicators, context=doc_context)
        # A clause segmenter may separate the sibling introduced by "while"
        # even though it explicitly reuses the parent sentence's period list.
        # Recover that list from the parent proposition, without relying on a
        # previous global context value.
        if "الفترة نفسها" in sentence and observations:
            parent_years = list(dict.fromkeys(int(m.group()) for m in _YEAR.finditer(source_sentence)))
            ordered = sorted(observations, key=lambda o: o["position"])
            if len(parent_years) == len(ordered):
                for obs, year in zip(ordered, parent_years):
                    obs["year"] = year
                    obs["month"] = obs["quarter"] = None
                    obs["period_label"] = str(year)
                    obs["period_source"] = "shared_parent_period"
        # Some RTL PDF generators split an Arabic sentence at the visual line
        # boundary, leaving the indicator and year in the carrier and the
        # measured value in the continuation. Rejoin that semantic period
        # without changing the stored source evidence.
        if carrier_codes and re.match(r"^\s*(?:وخلال|خلال)\s+النصف\s+الأول", sentence):
            carrier_code = carrier_codes[-1][0]
            carrier_years = [int(m.group()) for m in _YEAR.finditer(semantic_context_sentence or "")]
            for obs in observations:
                if obs.get("code") == carrier_code and carrier_years:
                    obs["year"] = carrier_years[-1]
                    obs["month"] = obs["quarter"] = None
                    obs["period_source"] = "rtl_semantic_carrier"
                    obs["period_label"] = f"{obs['year']}-H1"
                    obs["period_type"] = "semester"
                    obs["period_start"] = f"{obs['year']}-H1"
                    obs["period_end"] = f"{obs['year']}-H1"
                    obs["frequency"] = "semester"
        if carrier_codes and re.search(r"\b(?:son|sa|ses|leur)\s+[ée]volution\b|\bce\s+rythme\b", sentence, re.I):
            carrier_choice=carrier_codes[-1]
            for obs in observations:
                obs["code"], obs["label"] = carrier_choice
                obs["indicator_source"] = "semantic_carrier"
        if re.search(r"\b(?:ces|lesdits?)\s+pays\b", sentence, re.I) and "respectivement" in sentence.lower():
            ordered_for_geo=sorted(observations,key=lambda o:o["position"])
            if last_geography_sequence and len(last_geography_sequence)==len(ordered_for_geo):
                for obs,(name,iso3,kind) in zip(ordered_for_geo,last_geography_sequence):
                    obs["country"],obs["country_iso3"],obs["geography_type"]=name,iso3,kind
                    obs["country_source"]="discourse_geography_sequence"
        for token in re.finditer(rf"[-+]?{_NUMBER_TOKEN}", sentence):
            linked = next((o for o in observations if o.get("position", -1) <= token.start() < o.get("end_position", -1)), None)
            raw_token = token.group(0)
            if linked:
                outcome, reason = "extracted", None
                event_hint = f"{linked.get('code')}:{linked.get('value')}:{linked.get('period_label')}"
            elif re.fullmatch(r"(?:19|20)\d{2}", raw_token):
                outcome, reason, event_hint = "excluded", "period_token", None
            elif re.search(r"\b(?:tableau|graphique|figure|note|source)\s*$", sentence[max(0,token.start()-18):token.start()], re.I):
                outcome, reason, event_hint = "excluded", "structure_number", None
            else:
                outcome, reason, event_hint = "unresolved", "unbound_numeric_token", None
            numerical_coverage.append({
                "page": item.get("page"), "clause_index": item.get("clause_index"),
                "raw_token": raw_token, "evidence": sentence, "structure_type": "narrative",
                "outcome": outcome, "event_hint": event_hint, "reason": reason,
            })
        if not observations:
            rejected.append({**item, "reason": "aucune association indicateur-valeur suffisamment fiable"})
            continue

        sentence_context = dict(base_context)
        sentence_context["country"] = explicit_country or doc_context.last_country or base_context.get("country")
        sentence_context["country_iso3"] = explicit_iso3 or doc_context.last_country_iso3 or base_context.get("country_iso3")
        sentence_rows = _fact_rows(document, sentence, observations, sentence_context)
        for _row in sentence_rows:
            _row["sentence"] = source_sentence
            _row["evidence_clause"] = sentence
            _row["clause_index"] = item.get("clause_index", 0)
            _row["page_number"] = item.get("page")
            _row["conflict_scope"] = f"chapter:{item.get('page')}" if chapter_scoped else "document"

        # Context is updated from the last reliable event in textual order, not
        # from a guessed document-wide indicator. This enables "l'année précédente, elle…".
        ordered_observations = sorted(observations, key=lambda o: o["position"])
        explicit_geographies=[]
        for obs in ordered_observations:
            if obs.get("country") and obs.get("country_source") not in {"context","document","missing"}:
                item_geo=(obs.get("country"),obs.get("country_iso3"),obs.get("geography_type") or "country")
                if item_geo not in explicit_geographies:
                    explicit_geographies.append(item_geo)
        if len(explicit_geographies)>=2:
            last_geography_sequence=explicit_geographies
        for obs in ordered_observations:
            doc_context.remember_event(
                code=obs["code"], label=obs["label"], value=obs["value"],
                unit=obs["unit"], scale=obs["scale"], currency=obs["currency"],
                month=obs["month"], quarter=obs["quarter"], year=obs["year"],
            )
        # Advance country context only from an event that was actually bound.
        if sentence_rows:
            last_row = sentence_rows[-1]
            if last_row.get("country"):
                doc_context.last_country = last_row.get("country")
                doc_context.last_country_iso3 = last_row.get("country_iso3")

        # Comparisons often end on a historical reference. Keep the primary
        # event period as the current period for the next sentence.
        if ordered_observations:
            dated = [o for o in ordered_observations if o.get("year") is not None]
            primary = max(
                dated or ordered_observations,
                key=lambda o:(o.get("year") or -1,o.get("month") or 0,o.get("quarter") or 0),
            )
            doc_context.remember_explicit_period(primary.get("month"), primary.get("quarter"), primary.get("year"))

        # v4.23 Temporal Anchor Graph: update the stable discourse anchor only
        # from a period explicitly written in this sentence. Relative periods
        # must not move this anchor, otherwise sibling relations chain wrongly.
        explicit_candidates=[o for o in ordered_observations if o.get("period_source") == "explicit" and o.get("year") is not None]
        explicit_period_obs=max(
            explicit_candidates,
            key=lambda o:(o.get("year") or -1,o.get("month") or 0,o.get("quarter") or 0),
            default=None,
        )
        if explicit_period_obs is not None:
            doc_context.remember_discourse_anchor(
                explicit_period_obs.get("month"), explicit_period_obs.get("quarter"), explicit_period_obs.get("year")
            )

        for row in sentence_rows:
            # Exact duplicates are only equivalent when the economic nature is
            # also identical. An observed value and a forecast with the same
            # numeric value must remain two distinct events.
            key = _dedup_key(row)
            if key not in seen:
                seen.add(key)
                rows.append(row)
        if partial_callback and (idx % 10 == 0 or idx == len(candidates)):
            partial_callback(rows, idx, total)

    # Product rule v4.15: Annex / Appendix content is excluded entirely.
    # Structured table extraction is allowed only in the report body.

    # Geometry-backed tables take a dedicated semantic path. They never pass
    # through narrative sentence binding, so row/column headers and sector
    # dimensions remain attached to every numeric cell.
    table_events, table_audit = extract_structured_table_events(document)
    for obs in table_events:
        # Row-local geography emitted by the structured parser is authoritative.
        # Only fall back to the document context when the table row genuinely
        # contains no country.  Never overwrite a multi-country table with the
        # country of the surrounding chapter / first narrative section.
        if not obs.get("country"):
            obs["country"] = base_context.get("country")
            obs["country_iso3"] = base_context.get("country_iso3")
            obs["country_source"] = "document_table_context" if obs.get("country") else "missing"
        evidence = (
            f"Tableau {int(obs.get('table_index') or 0) + 1}, page {obs.get('table_page')} — "
            f"{obs.get('table_row_label')} × {obs.get('table_column_label')}"
        )
        table_context = {
            **base_context,
            "country": obs.get("country") or base_context.get("country"),
            "country_iso3": obs.get("country_iso3") or base_context.get("country_iso3"),
        }
        table_rows = _fact_rows(document, evidence, [obs], table_context)
        for row in table_rows:
            row["page_number"] = obs.get("table_page")
            row["table_source"] = "geometry_table"
            row["extraction_method"] = "structured_geometry_table"
            row["evidence_clause"] = evidence
            row["conflict_scope"] = "document"
            key = _dedup_key(row)
            if key not in seen:
                seen.add(key)
                rows.append(row)
        numerical_coverage.append({
            "page": obs.get("table_page"), "clause_index": None,
            "raw_token": obs.get("raw"), "evidence": evidence, "structure_type": "table",
            "outcome": "extracted", "event_hint": f"{obs.get('code')}:{obs.get('value')}:{obs.get('period_label')}",
            "reason": None,
        })

    # Strongly-typed tables in the report body are allowed; Annex/Appendix
    # tables are excluded upstream and never reach this parser.
    for row in _structured_body_table_rows(document, base_context):
        key = _dedup_key(row)
        if key not in seen:
            seen.add(key)
            rows.append(row)

    # Flag contradictions rather than deleting them. Exact duplicates were already
    # removed above; distinct values for the same series/period remain visible.
    by_period: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("current_year") is None:
            continue
        # A contradiction requires the same economic series, the same complete
        # period, compatible measurement *and the same observation nature*.
        # A forecast and an observed value for the same year are not a conflict:
        # they are two different epistemic states and must both remain visible.
        ck = (
            row.get("country_iso3") or row.get("country"),
            row.get("indicator_id"),
            row.get("current_year"), row.get("current_quarter"), row.get("current_month"),
            row.get("current_unit"), row.get("current_scale"), row.get("current_currency"),
            row.get("fact_type") or row.get("observation_type") or "observed",
            row.get("sector"), row.get("period_type"), row.get("period_start"), row.get("period_end"),
            row.get("conflict_scope") if chapter_scoped else None,
        )
        by_period[ck].append(row)
    contradiction_count = 0
    for group in by_period.values():
        distinct = {round(float(r["current_value"]), 10) for r in group if r.get("current_value") is not None}
        if len(distinct) > 1 and not _rounding_equivalent(group):
            contradiction_count += 1
            for row in group:
                row["conflict_status"] = True
                warnings = list(row.get("validation_warnings") or [])
                if "conflict" not in warnings:
                    warnings.append("conflict")
                row["validation_warnings"] = warnings
        elif len(distinct) > 1:
            # Keep both source values for traceability but record that their
            # difference is explained by display precision, not contradiction.
            for row in group:
                ev=list(row.get("validation_evidence") or [])
                if "rounding_compatible" not in ev:
                    ev.append("rounding_compatible")
                row["validation_evidence"] = ev

    # Final status is rule-based: critical inconsistencies and conflicts override
    # a high evidence score. This keeps triage auditable.
    for row in rows:
        finalize_status(row)

    progress("Contrôle des unités, périodes, doublons et contradictions…")
    _LAST_TRACE = {
        "engine": "event_series_v41_context_safe",
        "model": "aucun modèle génératif local",
        "paragraphs_total": len(candidates),
        "kept": candidates,
        "context": {
            "country": doc_context.last_country,
            "country_iso3": doc_context.last_country_iso3,
            "last_indicator": doc_context.last_indicators[0][0] if doc_context.last_indicators else None,
            "last_year": doc_context.current_year,
        },
        "raw_facts": rows,
        "rejected_structure": [],
        "structured_table_audit": table_audit,
        "numerical_coverage": numerical_coverage,
        "unresolved_numeric_count": sum(1 for x in numerical_coverage if x.get("outcome") == "unresolved"),
        "rejected_validation": rejected,
        "validated_count": sum(1 for r in rows if not r.get("needs_review")),
        "contradiction_groups": contradiction_count,
        "llm_calls": 0,
        "elapsed_seconds": time.time() - started,
        "pipeline_warning": None,
    }
    return rows
