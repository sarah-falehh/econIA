from app.services.multi_agent_pipeline import _extract_observations, _fact_rows


def test_one_sentence_creates_several_atomic_events():
    sentence = "La dette extérieure a baissé de 38,12% du PIB en 1986 à 34,05% en 2000 et à 27,08% en 2012."
    obs = _extract_observations(sentence)
    values = [(o["code"], o["value"], o["year"]) for o in obs]
    assert values == [
        ("external_debt_ratio", 38.12, 1986),
        ("external_debt_ratio", 34.05, 2000),
        ("external_debt_ratio", 27.08, 2012),
    ]


def test_debt_stock_and_ratio_are_separated():
    sentence = "La dette publique a atteint 36.616 MD en 2013, soit 47,2% du PIB."
    obs = _extract_observations(sentence)
    assert any(o["code"] == "public_debt_stock" and o["value"] == 36616 for o in obs)
    assert any(o["code"] == "public_debt_ratio" and o["value"] == 47.2 for o in obs)


def test_internal_external_parenthesis_roles():
    sentence = "En 1986, le taux d’endettement public a atteint 52,22% (soit 14,10% comme taux d’endettement intérieur et 38,12% comme taux d’endettement extérieur)."
    obs = _extract_observations(sentence)
    assert [(o["code"], o["value"]) for o in obs] == [
        ("public_debt_ratio", 52.22),
        ("internal_debt_ratio", 14.10),
        ("external_debt_ratio", 38.12),
    ]


def test_fact_rows_keep_every_year():
    sentence = "Le taux d’endettement extérieur est passé de 38,12% en 1986 à 34,05% en 2000 et 27,08% en 2012."
    obs = _extract_observations(sentence)
    rows = _fact_rows({"document_id":"d", "language":"fr"}, sentence, obs, {"country":"Tunisie", "source":"Test", "language":"fr"})
    assert [r["current_year"] for r in rows] == [1986, 2000, 2012]


def test_stock_ratio_and_following_year_are_atomic():
    sentence = "En 2013, l’encours de la dette publique s’est élevé à 36 616 millions de dinars, soit 47,2 % du PIB, contre 49,1 % l’année suivante."
    obs = _extract_observations(sentence)
    assert [(o["code"], o["value"], o["year"]) for o in obs] == [
        ("public_debt_stock", 36616.0, 2013),
        ("public_debt_ratio", 47.2, 2013),
        ("public_debt_ratio", 49.1, 2014),
    ]
