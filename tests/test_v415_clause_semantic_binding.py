import pandas as pd

from app.services.multi_agent_pipeline import run_multi_agent
from app.services.series_analytics import to_excel_bytes


def doc(text, country="Tunisie"):
    return {"document_id":"v415","language":"fr","text":text,"source":"benchmark","country":country}


def test_pronoun_value_keeps_previous_indicator_before_new_clause_indicator():
    rows = run_multi_agent(doc(
        "Le taux de chômage a atteint 16,1 % au troisième trimestre 2024. "
        "Au trimestre précédent, il s'établissait à 16,0 %, tandis que le taux d'activité était de 46,2 %."
    ))
    u = [r for r in rows if r["indicator_code"] == "unemployment_rate"]
    a = [r for r in rows if r["indicator_code"] == "activity_rate"]
    assert {(r["current_period_label"], r["current_value"]) for r in u} == {("2024-Q3",16.1),("2024-Q2",16.0)}
    assert {(r["current_period_label"], r["current_value"]) for r in a} == {("2024-Q2",46.2)}


def test_multi_country_value_binding_and_conditional_forecast():
    rows = run_multi_agent(doc(
        "Pour 2025, la croissance serait de 3,8 % au Maroc, 3,5 % en Algérie, 4,2 % en Égypte et 2,3 % en Tunisie."
    ))
    got = {(r["country"], r["current_value"], r["fact_type"]) for r in rows}
    assert got == {
        ("Maroc",3.8,"forecast"),("Algérie",3.5,"forecast"),
        ("Égypte",4.2,"forecast"),("Tunisie",2.3,"forecast"),
    }


def test_demonym_country_and_same_period_year_are_bound_locally():
    rows = run_multi_agent(doc(
        "Les exportations marocaines ont progressé de 5,8 % en 2024, alors que les importations ont augmenté de 6,4 %. "
        "En Algérie, les exportations d'hydrocarbures ont reculé de 3,2 % sur la même période."
    ))
    maroc = [r for r in rows if r["country"] == "Maroc"]
    alg = [r for r in rows if r["country"] == "Algérie"]
    assert {r["indicator_code"] for r in maroc} == {"exports_growth","imports_growth"}
    assert all(r["current_year"] == 2024 for r in maroc)
    assert len(alg) == 1 and alg[0]["current_year"] == 2024 and alg[0]["current_value"] == -3.2


def test_contextual_fdi_level_switches_from_growth_to_stock_and_inherits_current_year():
    rows = run_multi_agent(doc(
        "Les investissements directs étrangers ont progressé de 12,5 % en 2024. "
        "Leur niveau s'est établi à 3,1 milliards de dinars, contre 2,8 milliards en 2023."
    ))
    growth = [r for r in rows if r["indicator_code"] == "fdi_growth"]
    levels = [r for r in rows if r["indicator_code"] == "foreign_direct_investment"]
    assert len(growth) == 1 and growth[0]["current_year"] == 2024
    assert {(r["current_year"],r["current_value"],r["current_currency"]) for r in levels} == {(2024,3.1,"TND"),(2023,2.8,"TND")}


def test_between_years_de_a_a_b_pairing():
    rows = run_multi_agent(doc("Entre 2020 et 2024, l'inflation est passée de 5,6 % à 7,2 %."))
    assert {(r["current_year"],r["current_value"]) for r in rows} == {(2020,5.6),(2024,7.2)}


def test_excel_export_is_nan_safe():
    df = pd.DataFrame({"indicator":[None], "current_year":[None], "current_value":[None], "country":[None], "source":[None]})
    payload = to_excel_bytes(df)
    assert isinstance(payload, (bytes, bytearray)) and len(payload) > 100


def test_annex_is_excluded_even_when_it_contains_macroeconomic_values():
    rows = run_multi_agent(doc("[[PAGE 2]] Annexe A - Commerce extérieur 2024 64,8 milliards TND 72,6 milliards TND"))
    assert rows == []


def test_body_macro_table_is_parsed_but_inline_annex_not_needed():
    text = (
        "[[PAGE 1]] Tableau 1 - Principaux indicateurs Année Inflation (%) Chômage (%) Dette publique (% PIB) Réserves (Mds TND) "
        "2020 5,6 16,2 75,4 21,8 2021 6,1 16,8 78,2 23,4"
    )
    rows = run_multi_agent(doc(text, country=None))
    table = [r for r in rows if r.get("table_source") == "body_table"]
    assert len(table) == 8
    assert not any(r.get("indicator_code") == "trade_balance" for r in table)
