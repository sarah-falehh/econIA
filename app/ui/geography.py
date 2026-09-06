from __future__ import annotations

COUNTRY_CODES = {
    "algérie": "DZ", "algerie": "DZ", "الجزائر": "DZ", "tunisie": "TN", "تونس": "TN",
    "maroc": "MA", "المغرب": "MA", "france": "FR", "portugal": "PT", "espagne": "ES",
    "italie": "IT", "allemagne": "DE", "royaume-uni": "GB", "états-unis": "US",
    "etats-unis": "US", "chine": "CN", "japon": "JP", "thaïlande": "TH", "thailande": "TH",
    "argentine": "AR", "égypte": "EG", "egypte": "EG", "arabie saoudite": "SA",
    "turquie": "TR", "inde": "IN", "brésil": "BR", "bresil": "BR",
}

GEOGRAPHY_LABELS = {
    "country": "Pays", "economic_group": "Groupe économique", "region": "Région",
    "partner": "Partenaire", "unknown": "Non précisé",
}


def _flag(code: str | None) -> str:
    code = str(code or "").upper()
    if len(code) != 2 or not code.isalpha():
        return ""
    return "".join(chr(127397 + ord(letter)) for letter in code)


def geography_display(name, kind="country") -> str:
    """Render a geography as a recognisable visual identity, without changing its data value."""
    raw = str(name or "Géographie inconnue").strip()
    kind = str(kind or "country")
    if kind == "country":
        code = COUNTRY_CODES.get(raw.casefold())
        if not code:
            try:
                import pycountry
                code = pycountry.countries.lookup(raw).alpha_2
            except (LookupError, AttributeError):
                code = None
        return f"{_flag(code)}  {raw}" if code else f"◉  {raw}"
    symbol = {"economic_group": "🌐", "region": "⌖", "partner": "⇄"}.get(kind, "◇")
    return f"{symbol}  {raw}"
