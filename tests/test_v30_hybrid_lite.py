from app.services.multi_agent_pipeline import run_multi_agent


def test_debt_comparison_and_no_fake_month():
    text = "[[PAGE 13]] Le taux d’endettement public de la Tunisie est passé de 52,22% en 1986 à 40,4% en 2010."
    rows = run_multi_agent({"document_id": "x", "text": text, "language": "fr", "source": "Ministère des finances"})
    assert len(rows) == 2
    assert [row["current_value"] for row in rows] == [52.22, 40.4]
    assert [row["current_year"] for row in rows] == [1986, 2010]
    assert all(row["current_month"] is None for row in rows)
    assert rows[1]["reference_value"] == 52.22
    assert rows[1]["absolute_change"] == -11.82


def test_cross_sentence_previous_year_and_coreference():
    text = "En 2026, l’inflation atteint 6,2 %. L’année précédente, elle s’établissait à 7,1 %."
    rows = run_multi_agent({"document_id": "ctx", "text": text, "language": "fr", "country": "Tunisie", "source": "Test"})
    assert [(row["current_value"], row["current_year"]) for row in rows] == [(6.2, 2026), (7.1, 2025)]
    assert all(row["indicator_code"] == "inflation_rate" for row in rows)


def test_contradictions_are_preserved_and_flagged():
    text = "En 2024, l’inflation atteint 7,0 %. En 2024, l’inflation atteint 7,8 %."
    rows = run_multi_agent({"document_id": "conflict", "text": text, "language": "fr", "country": "Tunisie"})
    assert len(rows) == 2
    assert {row["current_value"] for row in rows} == {7.0, 7.8}
    assert all(row["needs_review"] for row in rows)
    assert all("contradictoires" in row["review_reason"] for row in rows)
