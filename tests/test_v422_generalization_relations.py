from app.services.multi_agent_pipeline import run_multi_agent


def _run(text, title="Benchmark"):
    return run_multi_agent({
        "document_id": "v422-test",
        "title": title,
        "text": text,
        "source": "benchmark.pdf",
        "language": "fr",
    })


def _by_value(rows, value):
    return next(r for r in rows if abs(float(r["current_value"]) - float(value)) < 1e-9)


def test_canada_mixed_frequency_and_recall():
    rows = _run(
        "Au Canada, le PIB reel a augmente de 1,7 % en 2024. "
        "Au dernier trimestre de l'annee, il a progresse de 0,5 % par rapport au trimestre precedent. "
        "L'indice des prix a la consommation a augmente de 2,4 % en moyenne en 2024, contre 3,9 % en 2023. "
        "En novembre 2024, la hausse sur douze mois etait de 1,9 %. "
        "Le taux de chomage s'est etabli a 6,7 % en decembre 2024. Un mois plus tot, il etait de 6,8 %. "
        "La dette brute des administrations publiques representait 107,5 % du PIB en 2024. "
        "Le solde budgetaire etait estime a -1,2 % du PIB. "
        "En 2025, la croissance devrait ralentir a 1,4 %. Pour 2026, elle remonterait a 1,8 %. "
        "L'inflation serait proche de 2,0 % en 2025.",
        "Canada",
    )
    assert len(rows) >= 12
    q4 = _by_value(rows, 0.5)
    assert (q4["current_year"], q4["current_quarter"]) == (2024, 4)
    assert "trimestrielle" in q4["indicator"].lower()
    avg = _by_value(rows, 2.4)
    assert "moyenne annuelle" in avg["indicator"].lower()
    nov = _by_value(rows, 1.9)
    assert (nov["current_year"], nov["current_month"]) == (2024, 11)
    prev_month = _by_value(rows, 6.8)
    assert (prev_month["current_year"], prev_month["current_month"]) == (2024, 11)
    assert _by_value(rows, -1.2)["fact_type"] == "estimate"
    assert _by_value(rows, 1.8)["fact_type"] == "forecast"


def test_relative_year_and_currency_new_zealand():
    rows = _run(
        "Les exportations ont atteint 92,6 milliards de dollars neo-zelandais en 2024. "
        "Elles etaient de 88,1 milliards l'annee precedente. "
        "Les IDE se sont etablis a 6,4 milliards NZD en 2024. Leur niveau est estime a 7,1 milliards en 2025.",
        "Nouvelle-Zelande",
    )
    old = _by_value(rows, 88.1)
    assert old["current_year"] == 2023
    assert old["current_currency"] == "NZD"
    fdi = _by_value(rows, 7.1)
    assert fdi["indicator_code"] == "foreign_direct_investment"
    assert fdi["fact_type"] == "estimate"


def test_quarter_frequency_inherits_to_following_sentence():
    rows = _run(
        "Au premier trimestre 2025, le PIB a augmente de 0,7 % par rapport au trimestre precedent. "
        "Au trimestre suivant, la progression est estimee a 0,4 %.",
        "Bresil",
    )
    first = _by_value(rows, 0.7)
    second = _by_value(rows, 0.4)
    assert (first["current_year"], first["current_quarter"]) == (2025, 1)
    assert (second["current_year"], second["current_quarter"]) == (2025, 2)
    assert "trimestrielle" in second["indicator"].lower()
    assert second["fact_type"] == "estimate"


def test_heading_word_previsions_does_not_flip_observed_value():
    rows = _run(
        "Blind v3 - doublons, conflits, JPY et previsions Japon - reconciliation des publications "
        "Le rapport principal indique une inflation de 2,7 % en 2024.",
        "Dossier Japon",
    )
    assert _by_value(rows, 2.7)["fact_type"] == "observed"


def test_country_prefixed_coreference_keeps_export_growth_indicator():
    rows = _run(
        "Les exportations hongroises ont recule de 1,4 % en 2024, tandis que les exportations polonaises ont progresse de 2,1 %. "
        "En Republique tcheque, elles ont augmente de 3,0 %.",
        "Europe centrale",
    )
    czech = _by_value(rows, 3.0)
    assert czech["country"] == "République tchèque"
    assert czech["indicator_code"] == "exports_growth"
