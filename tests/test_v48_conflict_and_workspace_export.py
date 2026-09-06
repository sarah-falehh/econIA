import pandas as pd

from app.services.multi_agent_pipeline import run_multi_agent
from app.services.series_analytics import observations_export


def test_same_period_different_observation_types_are_not_conflict():
    text = (
        "En Tunisie, l'inflation s'est établie à 7,0 % en 2024. "
        "Pour 2024, l'inflation devrait atteindre 7,4 %."
    )
    rows = run_multi_agent({"document_id":"v48-types","text":text,"language":"fr","country":"Tunisie"})
    inflation = [r for r in rows if "inflation" in (r.get("indicator") or "").lower() and r.get("current_year") == 2024]
    assert len(inflation) >= 2
    assert {r.get("fact_type") for r in inflation} >= {"observed", "forecast"}
    assert not any(r.get("conflict_status") for r in inflation)


def test_same_period_same_type_distinct_values_still_conflict():
    text = (
        "En Tunisie, l'inflation s'est établie à 7,0 % en 2024. "
        "Une autre source indique que l'inflation s'est établie à 7,4 % en 2024."
    )
    rows = run_multi_agent({"document_id":"v48-real-conflict","text":text,"language":"fr","country":"Tunisie"})
    inflation = [r for r in rows if "inflation" in (r.get("indicator") or "").lower() and r.get("current_year") == 2024]
    assert len(inflation) >= 2
    assert all(r.get("conflict_status") for r in inflation)
    assert all(r.get("validation_status") == "À vérifier" for r in inflation)


def test_canonical_user_export_preserves_type_and_rejected_status():
    df = pd.DataFrame([
        {"country":"Tunisie","indicator":"Taux de chômage","current_value":16.0,"current_unit":"%","current_scale":None,"current_currency":None,"current_year":2024,"current_quarter":None,"current_month":None,"source":"Test","sentence":"Phrase", "confidence":0.91,"fact_type":"forecast","observation_type":"forecast","validation_status":"Rejeté","needs_review":True},
        {"country":"Tunisie","indicator":"Taux de chômage","current_value":15.0,"current_unit":"%","current_scale":None,"current_currency":None,"current_year":2023,"current_quarter":None,"current_month":None,"source":"Test","sentence":"Phrase 2", "confidence":0.93,"fact_type":"observed","observation_type":"observed","validation_status":"Validé","needs_review":False},
    ])
    out = observations_export(df)
    assert "Type" in out.columns
    assert set(out["Type"]) == {"Prévision", "Observé"}
    assert set(out["Statut"]) == {"Rejeté", "Validé"}


def test_user_export_never_leaks_nan_in_unit_labels():
    df = pd.DataFrame([
        {"country":"Tunisie","indicator":"Taux d'inflation des prix à la consommation","current_value":7.0,"current_unit":"%","current_scale":float("nan"),"current_currency":float("nan"),"current_year":2024,"current_quarter":None,"current_month":None,"source":"Test","sentence":"Inflation 7 %", "confidence":0.93,"fact_type":"observed","observation_type":"observed","validation_status":"Validé","needs_review":False},
        {"country":"Tunisie","indicator":"Encours de la dette publique","current_value":127.3,"current_unit":float("nan"),"current_scale":"milliard","current_currency":"TND","current_year":2024,"current_quarter":None,"current_month":None,"source":"Test","sentence":"Dette 127,3 milliards TND", "confidence":0.93,"fact_type":"observed","observation_type":"observed","validation_status":"Validé","needs_review":False},
        {"country":"Tunisie","indicator":"Dette publique (% du PIB)","current_value":80.1,"current_unit":"% du PIB","current_scale":float("nan"),"current_currency":float("nan"),"current_year":2024,"current_quarter":None,"current_month":None,"source":"Test","sentence":"Dette 80,1 % du PIB", "confidence":0.93,"fact_type":"observed","observation_type":"observed","validation_status":"Validé","needs_review":False},
    ])
    out = observations_export(df)
    assert out["Unité"].tolist() == ["%", "milliard TND", "% du PIB"]
    assert not out["Unité"].astype(str).str.contains(r"\\bnan\\b", case=False, regex=True).any()


def test_series_export_never_leaks_nan_in_unit_labels():
    from app.services.series_analytics import simple_series_export
    df = pd.DataFrame([
        {"country":"Maroc","series_id":"MAR|DEBT","indicator":"Encours de la dette publique","current_value":100.0,"current_unit":float("nan"),"current_scale":"milliard","current_currency":"MAD","current_year":2023,"current_quarter":None,"current_month":None,"source":"Test","sentence":"Dette", "confidence":0.90,"fact_type":"observed","observation_type":"observed","validation_status":"Validé","needs_review":False},
        {"country":"Maroc","series_id":"MAR|DEBT","indicator":"Encours de la dette publique","current_value":105.0,"current_unit":float("nan"),"current_scale":"milliard","current_currency":"MAD","current_year":2024,"current_quarter":None,"current_month":None,"source":"Test","sentence":"Dette", "confidence":0.90,"fact_type":"observed","observation_type":"observed","validation_status":"Validé","needs_review":False},
    ])
    out = simple_series_export(df)
    assert set(out["Unité"]) == {"milliard MAD"}
    assert not out["Unité"].astype(str).str.contains(r"\\bnan\\b", case=False, regex=True).any()

