from __future__ import annotations

"""Country registry used by the extraction engine.

The previous implementation kept a small, hand-written list of countries.
That made a new country silently become ``None`` until it was manually added.
This module builds the base registry from ISO-3166 (pycountry) and Babel's
French/English territory names, then layers a small extensible demonym/alias
map on top. Country *names* therefore do not need to be added per benchmark.
"""

import re
import unicodedata
from functools import lru_cache
from typing import Iterable

try:
    import pycountry
except Exception:  # pragma: no cover - defensive fallback
    pycountry = None

try:
    from babel import Locale
except Exception:  # pragma: no cover
    Locale = None


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold().replace("’", "'")
    value = re.sub(r"[-_/]", " ", value)
    value = re.sub(r"[^\w\s']", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


# Demonyms are not part of ISO-3166. This layer is intentionally separate
# from the country-name registry, so adding a demonym never changes ISO data.
# It covers the languages used by EcoLingua and can be expanded independently.
DEMONYM_ISO3: dict[str, str] = {
    # North Africa / Europe existing coverage
    "tunisien":"TUN", "tunisienne":"TUN", "tunisiennes":"TUN", "tunisian":"TUN",
    "marocain":"MAR", "marocaine":"MAR", "marocaines":"MAR", "moroccan":"MAR",
    "algerien":"DZA", "algerienne":"DZA", "algeriennes":"DZA", "algerian":"DZA",
    "egyptien":"EGY", "egyptienne":"EGY", "egyptian":"EGY",
    "francais":"FRA", "francaise":"FRA", "french":"FRA",
    "italien":"ITA", "italienne":"ITA", "italiennes":"ITA", "italian":"ITA",
    "espagnol":"ESP", "espagnole":"ESP", "espagnoles":"ESP", "spanish":"ESP",
    "portugais":"PRT", "portugaise":"PRT", "portugaises":"PRT", "portuguese":"PRT",
    "allemand":"DEU", "allemande":"DEU", "german":"DEU",
    "senegalais":"SEN", "senegalaise":"SEN", "senegalese":"SEN",
    # Gold-v3 / v4 and broadly useful additions
    "canadien":"CAN", "canadienne":"CAN", "canadian":"CAN",
    "kenyan":"KEN", "kenyane":"KEN",
    "polonais":"POL", "polonaise":"POL", "polish":"POL",
    "tcheque":"CZE", "czech":"CZE",
    "hongrois":"HUN", "hongroise":"HUN", "hungarian":"HUN",
    "sud africain":"ZAF", "sud africaine":"ZAF", "south african":"ZAF",
    "japonais":"JPN", "japonaise":"JPN", "japanese":"JPN",
    "bresilien":"BRA", "bresilienne":"BRA", "brazilian":"BRA",
    "neo zelandais":"NZL", "neo zelandaise":"NZL", "new zealander":"NZL",
    "mexicain":"MEX", "mexicaine":"MEX", "mexicains":"MEX", "mexicaines":"MEX", "mexican":"MEX",
    "turc":"TUR", "turque":"TUR", "turkish":"TUR",
    "indonesien":"IDN", "indonesienne":"IDN", "indonesian":"IDN",
    "chilien":"CHL", "chilienne":"CHL", "chilean":"CHL",
    "norvegien":"NOR", "norvegienne":"NOR", "norwegian":"NOR",
    "ghaneen":"GHA", "ghaneenne":"GHA", "ghanaian":"GHA",
    "coreen":"KOR", "coreenne":"KOR", "south korean":"KOR", "korean":"KOR",
}

# Common geopolitical spelling aliases not always represented by the primary
# pycountry/Babel label.
DISPLAY_OVERRIDES = {"CZE": "République tchèque", "KOR": "Corée du Sud", "TUR": "Turquie"}

EXTRA_NAME_ISO3: dict[str, str] = {
    "coree du sud":"KOR", "republique de coree":"KOR", "south korea":"KOR",
    "coree du nord":"PRK", "north korea":"PRK",
    "republique tcheque":"CZE", "tchequie":"CZE", "czech republic":"CZE",
    "turquie":"TUR", "turkiye":"TUR",
    "etats unis":"USA", "etats unis d amerique":"USA", "united states":"USA", "usa":"USA",
    "royaume uni":"GBR", "united kingdom":"GBR", "uk":"GBR",
    "russie":"RUS", "russian federation":"RUS",
    "cote d ivoire":"CIV", "ivory coast":"CIV",
    "viet nam":"VNM", "vietnam":"VNM",
}


@lru_cache(maxsize=1)
def _registries() -> tuple[dict[str, tuple[str, str]], dict[str, list[str]]]:
    alias_to_country: dict[str, tuple[str, str]] = {}
    canonical_variants: dict[str, list[str]] = {}

    fr = Locale.parse("fr") if Locale else None
    en = Locale.parse("en") if Locale else None
    ar = Locale.parse("ar") if Locale else None

    iso_objects = list(pycountry.countries) if pycountry else []
    by_iso3 = {c.alpha_3: c for c in iso_objects}

    def display_for(iso3: str, fallback: str) -> str:
        if iso3 in DISPLAY_OVERRIDES:
            return DISPLAY_OVERRIDES[iso3]
        obj = by_iso3.get(iso3)
        alpha2 = getattr(obj, "alpha_2", None)
        if fr and alpha2:
            return str(fr.territories.get(alpha2) or fallback)
        return fallback

    def add(alias: str, iso3: str, display: str) -> None:
        folded = _fold(alias)
        if len(folded) < 3 and folded not in {"uk", "usa"}:
            return
        alias_to_country.setdefault(folded, (display, iso3))
        variants = canonical_variants.setdefault(display, [])
        for form in {alias.strip().casefold(), folded}:
            if form and form not in variants:
                variants.append(form)

    for c in iso_objects:
        iso3 = c.alpha_3
        display = display_for(iso3, c.name)
        # Never index alpha-3 codes as free-text aliases: codes such as EST, FIN
        # and SUR are ordinary French words (est/fin/sur) and caused false countries.
        candidates = {c.name, getattr(c, "official_name", "")}
        if fr:
            candidates.add(str(fr.territories.get(c.alpha_2) or ""))
        if en:
            candidates.add(str(en.territories.get(c.alpha_2) or ""))
        if ar:
            candidates.add(str(ar.territories.get(c.alpha_2) or ""))
        for alias in candidates:
            if alias:
                add(alias, iso3, display)

    for alias, iso3 in EXTRA_NAME_ISO3.items():
        obj = by_iso3.get(iso3)
        display = display_for(iso3, obj.name if obj else alias.title())
        add(alias, iso3, display)

    for alias, iso3 in DEMONYM_ISO3.items():
        obj = by_iso3.get(iso3)
        display = display_for(iso3, obj.name if obj else alias.title())
        add(alias, iso3, display)

    return alias_to_country, canonical_variants


ALIAS_TO_COUNTRY, CANONICAL_VARIANTS = _registries()


def detect_country(text: str, fallback: str | None = None) -> tuple[str | None, str | None]:
    folded = _fold(text)
    # Longest aliases first; word boundaries prevent accidental substring hits.
    for alias in sorted(ALIAS_TO_COUNTRY, key=len, reverse=True):
        if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", folded, re.I):
            return ALIAS_TO_COUNTRY[alias]

    if fallback:
        fb = _fold(str(fallback))
        if fb in ALIAS_TO_COUNTRY:
            return ALIAS_TO_COUNTRY[fb]
        # Support ISO3 supplied by metadata without exposing ISO3 codes to
        # free-text matching (EST/FIN/SUR are common French words).
        if len(fb) == 3 and pycountry:
            obj = pycountry.countries.get(alpha_3=fb.upper())
            if obj:
                fr = Locale.parse("fr") if Locale else None
                display = DISPLAY_OVERRIDES.get(obj.alpha_3) or (str(fr.territories.get(obj.alpha_2)) if fr else obj.name)
                return display, obj.alpha_3
        # Preserve explicit external metadata rather than inventing an ISO code.
        return str(fallback), None
    return None, None


def _fold_for_spans(value: str) -> str:
    """Accent/case normalize while keeping one output character per input char."""
    out: list[str] = []
    for ch in value or "":
        decomp = unicodedata.normalize("NFKD", ch)
        base = "".join(c for c in decomp if not unicodedata.combining(c))
        # Country names in our supported scripts resolve to one Latin base char;
        # keep the first char defensively to preserve source offsets.
        c = (base[:1] or ch).casefold().replace("’", "'")
        if c in "-_/" or (not c.isalnum() and c not in {"'", " "}):
            c = " "
        out.append(c)
    return "".join(out)


def country_mentions(text: str) -> list[tuple[int, int, str, str]]:
    """Return country mentions with approximate spans in normalized text.

    NFKD accent folding preserves the character count for the Latin country
    names used here, which keeps spans suitable for local value-country binding.
    """
    folded = _fold_for_spans(text)
    found: list[tuple[int, int, str, str]] = []
    for alias in sorted(ALIAS_TO_COUNTRY, key=len, reverse=True):
        for m in re.finditer(rf"(?<!\w){re.escape(alias)}(?!\w)", folded, re.I):
            name, iso3 = ALIAS_TO_COUNTRY[alias]
            found.append((m.start(), m.end(), name, iso3))
    out: list[tuple[int, int, str, str]] = []
    for item in sorted(found, key=lambda x: (x[0], -(x[1] - x[0]))):
        if any(item[0] >= x[0] and item[1] <= x[1] for x in out):
            continue
        out.append(item)
    return sorted(out)
