from app.services.indicator_registry import indicator_metadata, detect_country, build_series_id
from app.services.multi_agent_pipeline import run_multi_agent


def test_gdp_name_does_not_invent_real():
    meta = indicator_metadata("gdp_growth", "Le PIB a progressé de 2,5 % en 2024.")
    assert meta["official_name_fr"] == "Taux de croissance du PIB (variation annuelle)"
    real = indicator_metadata("gdp_growth", "Le PIB réel a progressé de 2,5 % en 2024.")
    assert "PIB réel" in real["official_name_fr"]


def test_country_detection_for_algeria():
    assert detect_country("En Algérie, l'inflation a atteint 4,2 %.") == ("Algérie", "DZA")


def test_series_id_changes_by_country():
    a = build_series_id("DZA", "ECO.INFLATION_RATE", "%", None, None)
    b = build_series_id("TUN", "ECO.INFLATION_RATE", "%", None, None)
    assert a != b


def test_pipeline_emits_official_metadata_and_country():
    doc = {
        "document_id": "x",
        "language": "fr",
        "source": "Test",
        "text": "En 2024, le taux d'inflation en Algérie a atteint 4,2 %, contre 3,5 % en 2023.",
    }
    rows = run_multi_agent(doc)
    assert len(rows) == 2
    assert all(r["country"] == "Algérie" for r in rows)
    assert all(r["country_iso3"] == "DZA" for r in rows)
    assert all(r["indicator_id"] == "ECO.INFLATION_RATE" for r in rows)
    assert all(r["series_id"].startswith("DZA:") for r in rows)


def test_imf_debt_code_only_when_explicit():
    generic = indicator_metadata("public_debt_ratio", "La dette publique représente 47 % du PIB.")
    assert generic["external_code"] is None
    explicit = indicator_metadata("public_debt_ratio", "La dette brute des administrations publiques représente 47 % du PIB.")
    assert explicit["external_code"] == "GGXWDG_NGDP"
