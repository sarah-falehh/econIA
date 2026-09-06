from app.services.multi_agent_pipeline import _candidate_sentences, run_multi_agent


def doc(text):
    return {"document_id": "v52", "text": text, "language": "fr", "country": "Tunisie", "country_iso3": "TUN", "source": "regression"}


def test_chart_axis_ticks_are_not_observations():
    text = "Graphique 1: Evolution de l'inflation 8,0% 7,0% 6,0% 5,0% 4,0% 3,0% 2,0% 1,0% 0,0% 2001 2002 2003 2004 2005 2006 2007 2008."
    assert _candidate_sentences(text) == []
    no_percent = "Graphique 6: Evolution du TMM 8,00 7,00 6,69 6,00 5,00 4,25 4,00 3,75 3,00 2,96 2,00 2012 2013 2014 2015 2016 2017 2018."
    assert _candidate_sentences(no_percent) == []


def test_growth_of_food_prices_is_not_gdp_growth():
    rows = run_multi_agent(doc("La croissance des prix des produits alimentaires a atteint 4,4 % en moyenne en 2016."))
    assert rows
    assert all(r["indicator_code"] != "gdp_growth" for r in rows)


def test_competitiveness_indicator_families_bind_locally():
    cases = [
        ("Le taux directeur a atteint 7,75 % en 2019.", "policy_rate"),
        ("Le TMM réel a atteint -0,81 % en 2018.", "real_money_market_rate"),
        ("Le coût salarial unitaire a progressé de 6,7 % en 2016.", "unit_labor_cost"),
        ("La productivité du travail a augmenté de 4,1 % en 2016.", "labor_productivity"),
        ("L'indicateur synthétique de compétitivité a reculé de 0,2 % en 2016.", "competitiveness_index"),
    ]
    for text, expected in cases:
        rows = run_multi_agent(doc(text))
        assert rows and rows[0]["indicator_code"] == expected


def test_specialized_context_does_not_fall_back_to_inflation():
    rows = run_multi_agent(doc("Le TMM réel était de -0,81 % en 2018. Ce taux atteignait 0,52 % en 2016."))
    assert rows
    assert {r["indicator_code"] for r in rows} == {"real_money_market_rate"}


def test_parenthetical_comparison_preserves_concept_order():
    rows = run_multi_agent(doc("La rémunération moyenne a progressé plus vite que la productivité du travail (8,8 % contre 0,6 %)."))
    by_value = {round(float(r["current_value"]), 1): r["indicator_code"] for r in rows}
    assert by_value == {8.8: "nominal_wage_rate", 0.6: "labor_productivity"}


def test_bilateral_exchange_rate_change_beats_prior_context():
    rows = run_multi_agent(doc("Le dinar s'est déprécié de 10,3 % face au dollar contre une appréciation de 7,6 % face à l'euro en 2015."))
    assert rows and {r["indicator_code"] for r in rows} == {"exchange_rate_change"}
