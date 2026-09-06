from app.services.multi_agent_pipeline import run_multi_agent


def _run(text, title="Article 2025"):
    return run_multi_agent({"document_id":"v411","title":title,"country":"Tunisie","language":"fr","text":text})


def test_explicit_activity_rate_overrides_unemployment_context():
    rows=_run("Le taux de chômage a atteint 15,2 % au quatrième trimestre 2025. Le taux d’activité a reculé à 45,9 %, après 46,1 % au trimestre précédent.")
    activity=[r for r in rows if r["indicator_code"]=="activity_rate"]
    assert {r["current_value"] for r in activity} == {45.9,46.1}
    assert all(r["indicator"]=="Taux d’activité" for r in activity)
    by={r["current_value"]:r for r in activity}
    assert (by[45.9]["current_year"],by[45.9]["current_quarter"])==(2025,4)
    assert (by[46.1]["current_year"],by[46.1]["current_quarter"])==(2025,3)


def test_projection_scope_is_event_local():
    rows=_run("La croissance réelle du PIB est donnée à 1,6 % en 2024 et 2,6 % en 2025, puis projette 2,5 % en 2026 et 2,2 % en 2027.")
    by={(r["current_year"],r["current_value"]):r["observation_type"] for r in rows if r["indicator_code"]=="gdp_growth"}
    assert by[(2024,1.6)]=="observed"
    assert by[(2025,2.6)]=="observed"
    assert by[(2026,2.5)]=="forecast"
    assert by[(2027,2.2)]=="forecast"


def test_imf_projette_is_forecast():
    rows=_run("Le FMI projette une croissance réelle du PIB de 2,1 % en 2026.")
    assert len(rows)==1 and rows[0]["observation_type"]=="forecast"


def test_current_account_and_fdi_variation_are_separate_events():
    rows=_run("Le déficit courant atteignait 2,0 % du PIB au premier semestre 2025, tandis que les investissements directs étrangers avaient progressé de 41 % sur les sept premiers mois.")
    by={r["indicator_code"]:r for r in rows}
    assert by["current_account_balance"]["current_value"]==2.0
    assert by["current_account_balance"]["current_unit"]=="% du PIB"
    assert by["fdi_growth"]["current_value"]==41.0


def test_core_inflation_first_value_uses_document_month_not_later_measure_month():
    rows=_run("L’inflation sous-jacente a atteint 4,9 %, après 5,0 % en novembre.", title="Indice des prix à la consommation — décembre 2025")
    by={r["current_value"]:r for r in rows if r["indicator_code"]=="core_inflation"}
    assert (by[4.9]["current_year"],by[4.9]["current_month"])==(2025,12)
    assert (by[5.0]["current_year"],by[5.0]["current_month"])==(2025,11)


def test_monetary_comparison_propagates_currency():
    rows=_run("Durant l’année 2025, les exportations tunisiennes ont atteint 63 695,1 millions de dinars, contre 62 077,6 millions en 2024.")
    exports=[r for r in rows if r["indicator_code"]=="exports"]
    assert len(exports)==2
    assert all(r["current_currency"]=="TND" for r in exports)

def test_projection_noun_scope_marks_only_future_values():
    rows=_run("L’inflation IPC est donnée à 7,0 % en 2024 et 5,7 % en 2025, avec des projections de 5,2 % en 2026 et 4,8 % en 2027.")
    by={(r["current_year"],r["current_value"]):r["observation_type"] for r in rows if r["indicator_code"]=="inflation_rate"}
    assert by[(2024,7.0)]=="observed"
    assert by[(2025,5.7)]=="observed"
    assert by[(2026,5.2)]=="forecast"
    assert by[(2027,4.8)]=="forecast"


def test_cumulative_periods_are_value_local():
    rows=_run("Le déficit courant atteignait 2,0 % du PIB au premier semestre 2025, tandis que les investissements directs étrangers avaient progressé de 41 % sur les sept premiers mois.")
    by={r["indicator_code"]:r for r in rows}
    assert by["current_account_balance"]["current_period_label"]=="2025-H1"
    assert by["fdi_growth"]["current_period_label"]=="2025-M01:M07"
    assert by["current_account_balance"]["current_month"] is None
    assert by["fdi_growth"]["current_month"] is None
