import pandas as pd

from app.services.evidence_validation import finalize_status, VALIDATION_WEIGHTS
from app.services.multi_agent_pipeline import run_multi_agent
from app.services.series_analytics import observations_export, simple_series_export, simple_statistics_export


def doc(text):
    return {"document_id":"v47", "language":"fr", "text":text, "source":"benchmark"}


def test_weights_are_centralized_and_bounded():
    assert "base" in VALIDATION_WEIGHTS
    assert "conflict" in VALIDATION_WEIGHTS


def test_validated_status_is_explicit():
    rows = run_multi_agent(doc("En Tunisie, le taux d'inflation des prix à la consommation s'est établi à 7,0 % en 2024."))
    assert rows[0]["validation_status"] == "Validé"
    assert rows[0]["needs_review"] is False


def test_contextual_previous_year_keeps_evidence_warning():
    rows = run_multi_agent(doc("En Tunisie, le taux d'inflation atteint 6,2 % en 2026. L'année précédente, il s'établissait à 7,1 %."))
    second = next(r for r in rows if r["current_year"] == 2025)
    assert "period_resolved" in second["validation_warnings"]
    assert any("période" in x for x in second["confidence_warnings"])


def test_conflict_forces_review_even_with_high_confidence():
    row = {"confidence": .97, "validation_warnings": [], "conflict_status": True, "fact_type":"observed"}
    finalize_status(row)
    assert row["validation_status"] == "À vérifier"
    assert row["needs_review"] is True
    assert "conflict" in row["validation_warnings"]


def test_critical_unit_mismatch_forces_rejection():
    row = {"confidence": .95, "validation_warnings": ["critical_unit_mismatch"], "conflict_status": False, "fact_type":"observed"}
    finalize_status(row)
    assert row["validation_status"] == "Rejeté"


def test_forecast_and_observed_same_sentence_have_different_types():
    rows = run_multi_agent(doc("En Tunisie, pour 2025, le taux de croissance du PIB devrait atteindre 2,1 %, après 1,4 % en 2024."))
    by_year = {r["current_year"]: r for r in rows}
    assert by_year[2025]["observation_type"] == "forecast"
    assert by_year[2024]["observation_type"] == "observed"


def test_estimate_type_is_exposed():
    rows = run_multi_agent(doc("En Tunisie, le taux de croissance du PIB est estimé à 2,3 % en 2025."))
    assert rows[0]["observation_type"] == "estimate"


def test_duplicate_is_not_conflict():
    rows = run_multi_agent(doc("En Tunisie, l'inflation atteint 7,0 % en 2024. En Tunisie, l'inflation atteint 7,0 % en 2024."))
    assert len(rows) == 1
    assert rows[0]["conflict_status"] is False


def test_distinct_values_same_series_period_are_conflict():
    rows = run_multi_agent(doc("En Tunisie, l'inflation atteint 7,0 % en 2024. En Tunisie, l'inflation atteint 7,8 % en 2024."))
    assert len(rows) == 2
    assert all(r["conflict_status"] for r in rows)
    assert all(r["validation_status"] == "À vérifier" for r in rows)


def _frame():
    return pd.DataFrame([
        {"country":"Tunisie","indicator":"Taux de croissance du PIB (variation annuelle)","indicator_code":"gdp_growth","series_id":"s","current_value":1.4,"current_unit":"%","current_scale":None,"current_currency":None,"current_year":2024,"current_quarter":None,"current_month":None,"fact_type":"observed","observation_type":"observed","validation_status":"Validé","needs_review":False,"confidence":.95,"source":"A","sentence":"historique"},
        {"country":"Tunisie","indicator":"Taux de croissance du PIB (variation annuelle)","indicator_code":"gdp_growth","series_id":"s","current_value":2.1,"current_unit":"%","current_scale":None,"current_currency":None,"current_year":2025,"current_quarter":None,"current_month":None,"fact_type":"forecast","observation_type":"forecast","validation_status":"À vérifier","needs_review":True,"confidence":.80,"source":"A","sentence":"prévision"},
        {"country":"Tunisie","indicator":"Taux de croissance du PIB (variation annuelle)","indicator_code":"gdp_growth","series_id":"s","current_value":9.9,"current_unit":"%","current_scale":None,"current_currency":None,"current_year":2026,"current_quarter":None,"current_month":None,"fact_type":"observed","observation_type":"observed","validation_status":"Rejeté","needs_review":True,"confidence":.30,"source":"A","sentence":"rejet"},
    ])


def test_observations_export_contains_business_validation_fields():
    out = observations_export(_frame())
    assert list(out.columns) == ["Pays","Indicateur","Valeur","Unité","Période","Type","Source","Phrase","Confiance","Statut"]
    assert set(out["Type"]) == {"Observé","Prévision"}
    assert set(out["Statut"]) == {"Validé","À vérifier","Rejeté"}


def test_series_keeps_review_but_excludes_rejected():
    out = simple_series_export(_frame())
    assert set(out["Année"]) == {2024, 2025}
    assert "À vérifier" in set(out["Statut"])
    assert "Rejeté" not in set(out["Statut"])


def test_statistics_exclude_forecasts_and_rejected_points():
    out = simple_statistics_export(_frame())
    assert len(out) == 1
    assert float(out.iloc[0]["Min"]) == 1.4
    assert float(out.iloc[0]["Max"]) == 1.4
    assert int(out.iloc[0]["Première période"]) == 2024
    assert int(out.iloc[0]["Dernière période"]) == 2024


def test_no_nan_units_on_reference_case():
    rows = run_multi_agent(doc("En Tunisie, l'encours de la dette publique s'est élevé à 126,5 milliards de dinars en 2024, soit 79,8 % du PIB."))
    out = observations_export(pd.DataFrame(rows))
    assert not out["Unité"].astype(str).str.contains("nan", case=False).any()


def test_econometric_noise_remains_rejected():
    rows = run_multi_agent(doc("Le coefficient associé à l'inflation est de 0,43 avec une p-value de 0,02. Le modèle présente un R² de 0,71 et une statistique t égale à 2,18."))
    assert rows == []
