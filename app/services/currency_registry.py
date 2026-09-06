from __future__ import annotations

"""Dynamic ISO-4217 currency registry.

The extractor must not need one new hard-coded regex every time a new country
appears.  Currency names are generated from Babel/CLDR and ISO-4217 metadata,
then disambiguated with the document country when the denomination is generic
(e.g. ``peso``, ``dinar``, ``dollar``).
"""

from functools import lru_cache
import re
import unicodedata
from typing import Iterable

try:
    import pycountry
except Exception:  # pragma: no cover
    pycountry = None

try:
    from babel.core import get_global
    from babel.numbers import get_currency_name
except Exception:  # pragma: no cover
    get_global = None
    get_currency_name = None


def _fold(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").replace("’", "'"))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    text = re.sub(r"[-_/]+", " ", text)
    text = re.sub(r"[^\w' ]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


# Common natural-language denominations which CLDR sometimes exposes only in a
# country-specific form.  The value is deliberately a *family*, not a currency
# code; the document country chooses the actual ISO-4217 currency.
DENOMINATION_FAMILIES: dict[str, str] = {
    "peso": "peso", "pesos": "peso",
    "dinar": "dinar", "dinars": "dinar",
    "dirham": "dirham", "dirhams": "dirham",
    "dollar": "dollar", "dollars": "dollar",
    "roupie": "rupee", "roupies": "rupee", "rupiah": "rupee",
    "shilling": "shilling", "shillings": "shilling",
    "couronne": "krone", "couronnes": "krone", "krone": "krone", "kroner": "krone",
    "cedi": "cedi", "cedis": "cedi", "cedi ghaneen": "cedi", "cedis ghaneens": "cedi",
    "won": "won", "wons": "won",
    "yen": "yen", "yens": "yen",
    "real": "real", "reais": "real",
    "livre": "pound", "livres": "pound", "pound": "pound", "pounds": "pound",
    "franc cfa": "cfa", "francs cfa": "cfa", "fcfa": "cfa", "f cfa": "cfa",
    "درهم": "dirham", "دراهم": "dirham",
    "دينار": "dinar", "دنانير": "dinar",
    "دولار": "dollar", "دولارات": "dollar",
    "دوالر": "dollar", "دوالرات": "dollar",
}


def _currency_family(code: str) -> str | None:
    names: list[str] = []
    if get_currency_name:
        for loc in ("fr", "en"):
            for count in (1, 2):
                try:
                    names.append(_fold(get_currency_name(code, count=count, locale=loc)))
                except Exception:
                    pass
    joined = " ".join(names)
    for token, family in DENOMINATION_FAMILIES.items():
        if re.search(rf"(?<!\w){re.escape(token)}(?!\w)", joined):
            return family
    return None


@lru_cache(maxsize=1)
def country_currency_map() -> dict[str, str]:
    """ISO3 -> current tender currency code using CLDR territory history."""
    out: dict[str, str] = {}
    if not (pycountry and get_global):
        return out
    territory_currencies = get_global("territory_currencies") or {}
    for country in pycountry.countries:
        candidates = territory_currencies.get(country.alpha_2) or []
        current = [x for x in candidates if len(x) >= 4 and x[2] is None and bool(x[3])]
        if current:
            out[country.alpha_3] = current[-1][0]
    return out


@lru_cache(maxsize=1)
def currency_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    if pycountry:
        for cur in pycountry.currencies:
            code = getattr(cur, "alpha_3", None)
            if not code:
                continue
            for name in {getattr(cur, "name", "")}:
                if name:
                    aliases.setdefault(_fold(name), code)
            if get_currency_name:
                for loc in ("fr", "en", "ar"):
                    for count in (1, 2):
                        try:
                            name = get_currency_name(code, count=count, locale=loc)
                        except Exception:
                            continue
                        if name:
                            aliases.setdefault(_fold(name), code)

    # High-value aliases that appear often in official reports and abbreviations.
    explicit = {
        "franc cfa": "XOF", "francs cfa": "XOF", "fcfa": "XOF", "f cfa": "XOF",
        "dinar tunisien": "TND", "dinars tunisiens": "TND",
        "dinar algerien": "DZD", "dinars algeriens": "DZD",
        "dirham marocain": "MAD", "dirhams marocains": "MAD",
        "livre egyptienne": "EGP", "livres egyptiennes": "EGP",
        "shilling kenyan": "KES", "shillings kenyans": "KES",
        "roupie indonesienne": "IDR", "roupies indonesiennes": "IDR",
        "peso mexicain": "MXN", "pesos mexicains": "MXN",
        "couronne norvegienne": "NOK", "couronnes norvegiennes": "NOK",
        "cedi ghaneen": "GHS", "cedis ghaneens": "GHS",
        "won sud coreen": "KRW", "wons sud coreens": "KRW",
        "yen japonais": "JPY", "yens japonais": "JPY",
        "real bresilien": "BRL", "reais bresiliens": "BRL",
        "dollar neo zelandais": "NZD", "dollars neo zelandais": "NZD",
        "dollar canadien": "CAD", "dollars canadiens": "CAD",
        "dollar us": "USD", "dollars us": "USD", "dollar americain": "USD", "dollars americains": "USD",
        "rand sud africain": "ZAR", "rands sud africains": "ZAR",
    }
    aliases.update({_fold(k): v for k, v in explicit.items()})
    return aliases


ALIASES = currency_aliases()
COUNTRY_CURRENCY = country_currency_map()


@lru_cache(maxsize=1)
def _regex_aliases() -> tuple[str, ...]:
    values: set[str] = set(ALIASES) | set(DENOMINATION_FAMILIES)
    if pycountry and get_currency_name:
        for cur in pycountry.currencies:
            code = getattr(cur, "alpha_3", None)
            if not code:
                continue
            for loc in ("fr", "en"):
                for count in (1, 2):
                    try:
                        name = str(get_currency_name(code, count=count, locale=loc) or "").strip().casefold()
                    except Exception:
                        name = ""
                    if len(name) >= 3:
                        values.add(name)
    # Include explicit human aliases in their accented/original form too.
    values.update({
        "franc cfa", "francs cfa", "dinars tunisiens", "dinars algériens",
        "dirhams marocains", "livres égyptiennes", "shillings kenyans",
        "roupies indonésiennes", "pesos mexicains", "couronnes norvégiennes",
        "cédis ghanéens", "wons sud-coréens", "yens japonais",
        "reais brésiliens", "dollars néo-zélandais", "dollars canadiens", "dollars US", "dollars américains",
        "rands sud-africains",
    })
    return tuple(sorted(values, key=len, reverse=True))


def currency_text_pattern() -> str:
    """Regex fragment for currency names. ISO codes remain case-sensitive."""
    # Restrict to human-readable aliases of at least 3 chars.  Folded aliases
    # are accent-free; the extractor also normalizes its text before matching.
    names = _regex_aliases()
    name_alt = "|".join(re.escape(x) for x in names)
    codes = sorted(set(ALIASES.values()) | set(COUNTRY_CURRENCY.values()))
    code_alt = "|".join(re.escape(c) for c in codes)
    return rf"(?:(?-i:{code_alt})|{name_alt})"


def detect_currency(text: str | None, country_iso3: str | None = None) -> str | None:
    raw = str(text or "")
    # ISO codes are safe only as uppercase free-text tokens; this avoids TRY
    # matching the ordinary English verb "try".
    for code in sorted(set(ALIASES.values()) | set(COUNTRY_CURRENCY.values()), key=len, reverse=True):
        if re.search(rf"(?<![A-Z]){re.escape(code)}(?![A-Z])", raw):
            return code

    folded = _fold(raw)
    for alias in sorted(ALIASES, key=len, reverse=True):
        if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", folded):
            return ALIASES[alias]

    # Generic denomination + known country => current national currency.
    if country_iso3 and country_iso3 in COUNTRY_CURRENCY:
        for alias, family in DENOMINATION_FAMILIES.items():
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", folded):
                expected = COUNTRY_CURRENCY[country_iso3]
                if _currency_family(expected) == family:
                    return expected
    return None


def current_currency_for_country(country_iso3: str | None) -> str | None:
    return COUNTRY_CURRENCY.get(str(country_iso3 or "").upper())
