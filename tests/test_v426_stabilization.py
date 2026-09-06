from app.services.multi_agent_pipeline import _structured_body_table_rows


def _doc(text):
    return {"text": text, "source_name": "test.pdf", "document_id": "v426-test"}


def test_multicountry_table_row_country_overrides_document_country():
    text = """Pays Année Inflation (%) Chômage (%) Dette publique (% PIB)\nTunisie 2024 7,0 16,0 79,0\nCanada 2024 2,4 6,7 107,5\nMexique 2024 4,7 2,8 49,3"""
    rows = _structured_body_table_rows(_doc(text), {"country":"Tunisie", "country_iso3":"TUN"})
    got={(r["country_iso3"], r["current_year"], r["indicator"]):r["current_value"] for r in rows}
    assert got[("TUN", 2024, "Taux d’inflation des prix à la consommation")] == 7.0
    assert got[("CAN", 2024, "Taux d’inflation des prix à la consommation")] == 2.4
    assert got[("MEX", 2024, "Dette publique (% du PIB)")] == 49.3


def test_table_row_currency_uses_row_country_not_document_country():
    text = """Pays Année Exportations (milliards) Importations (milliards)\nTunisie 2024 63,0 70,0\nCanada 2024 900,0 850,0"""
    rows = _structured_body_table_rows(_doc(text), {"country":"Tunisie", "country_iso3":"TUN"})
    by_country={}
    for r in rows:
        by_country.setdefault(r["country_iso3"], set()).add(r.get("current_currency"))
    assert "TND" in by_country["TUN"]
    assert "CAD" in by_country["CAN"]
