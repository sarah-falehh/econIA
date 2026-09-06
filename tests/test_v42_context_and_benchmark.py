from app.services.multi_agent_pipeline import run_multi_agent


def _run(text):
    return run_multi_agent({"document_id":"t","text":text,"source":"test","language":"fr","title":"test"})


def test_short_coreference_sentence_keeps_inflation_context():
    rows=_run("En 2024, le taux d’inflation a atteint 7,0 %. En 2023, il atteignait 8,3 %.")
    got={(r["indicator_code"],r["current_year"],r["current_value"]) for r in rows}
    assert ("inflation_rate",2024,7.0) in got
    assert ("inflation_rate",2023,8.3) in got


def test_quarter_context_is_resolved_but_not_leaked_to_next_indicator():
    rows=_run("Le taux de chômage a atteint 16,4 % au quatrième trimestre 2024. Au trimestre précédent, il s’établissait à 16,0 %. Les IDE ont atteint 2,8 milliards de dinars en 2024. Ils s’étaient établis à 2,4 milliards de dinars l’année précédente.")
    unemployment=[r for r in rows if r["indicator_code"]=="unemployment_rate"]
    assert {(r["current_year"],r["current_quarter"],r["current_value"]) for r in unemployment}=={(2024,4,16.4),(2024,3,16.0)}
    ide=[r for r in rows if r["indicator_code"]=="foreign_direct_investment"]
    assert {(r["current_year"],r["current_quarter"],r["current_value"]) for r in ide}=={(2024,None,2.8),(2023,None,2.4)}


def test_forecast_target_year_and_historical_comparison_type():
    rows=_run("Pour 2025, la croissance du PIB devrait atteindre 2,1 %, après 1,4 % en 2024.")
    got={(r["current_value"],r["current_year"],r["fact_type"]) for r in rows}
    assert (2.1,2025,"forecast") in got
    assert (1.4,2024,"observed") in got
