from app.services.multi_agent_pipeline import run_multi_agent


def doc(text):
    return {"document_id":"v46-test", "language":"fr", "text":text, "source":"test"}


def test_forecast_and_historical_comparison_are_separated():
    rows = run_multi_agent(doc("En Tunisie, pour 2025, le taux de croissance du PIB devrait atteindre 2,1 %, après 1,4 % en 2024."))
    vals = {(round(r["current_value"],1), r["current_year"]): r["fact_type"] for r in rows}
    assert vals[(2.1, 2025)] == "forecast"
    assert vals[(1.4, 2024)] == "observed"


def test_estimate_is_classified():
    rows = run_multi_agent(doc("En Tunisie, selon une estimation provisoire, le taux de croissance du PIB est estimé à 2,3 % en 2025."))
    assert rows
    assert rows[0]["fact_type"] == "estimate"


def test_confidence_is_explainable_and_not_accuracy():
    rows = run_multi_agent(doc("En Tunisie, le taux d'inflation des prix à la consommation s'est établi à 7,0 % en 2024."))
    assert rows
    r = rows[0]
    assert 0 < r["confidence"] <= 0.98
    assert isinstance(r["confidence_evidence"], list)
    assert "indicateur explicite" in r["confidence_evidence"]
    assert "période explicite" in r["confidence_evidence"]
    assert "unité/devise explicite" in r["confidence_evidence"]


def test_contextual_period_has_warning_and_lower_evidence_strength():
    rows = run_multi_agent(doc("En Tunisie, le taux d'inflation atteint 6,2 % en 2026. L'année précédente, il s'établissait à 7,1 %."))
    second = next(r for r in rows if round(r["current_value"],1) == 7.1)
    assert second["current_year"] == 2025
    assert any("période" in w for w in second.get("confidence_warnings", []))
