from app.services.evidence_validation import score_event, finalize_status
from app.services.indicator_registry import indicator_metadata


def test_structured_body_table_is_deterministic_evidence():
    cur={"code":"inflation_rate","value":7.2,"unit":"%","currency":None,"scale":None,
         "year":2024,"month":None,"quarter":None,"period_label":"2024","status":"observed",
         "indicator_source":"explicit_table","unit_source":"explicit_table","period_source":"explicit_table"}
    scored=score_event(cur, "Tableau principal - année 2024: inflation.", {"country":"Tunisie"}, explicit_country=False)
    row={**scored,"conflict_status":False,"fact_type":"observed"}
    row=finalize_status(row)
    assert row["validation_status"] == "Validé"
    assert "structured_table_evidence" in row["validation_evidence"]


def test_quarterly_gdp_label_not_annual():
    meta=indicator_metadata("gdp_growth", "Au quatrième trimestre, l'activité a augmenté de 0,2 % par rapport au trimestre précédent.")
    assert meta["official_name_fr"] == "Taux de croissance du PIB (variation trimestrielle)"


def test_annual_gdp_label_stays_annual():
    meta=indicator_metadata("gdp_growth", "En 2024, le PIB a progressé de 1,1 %.")
    assert meta["official_name_fr"] == "Taux de croissance du PIB (variation annuelle)"


def test_ressortait_is_strong_context_relation():
    cur={"code":"inflation_rate","value":1.3,"unit":"%","currency":None,"scale":None,
         "year":2024,"month":12,"quarter":None,"period_label":"2024-M12","status":"observed",
         "indicator_source":"context","unit_source":"explicit","period_source":"explicit"}
    scored=score_event(cur, "En décembre 2024, il ressortait à 1,3 % sur un an.", {"country":"France"}, explicit_country=False)
    assert "linguistic_relation" in scored["validation_evidence"]
