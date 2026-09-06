

def test_v417_safe_context_inheritance_can_validate_unique_pronoun():
    from app.services.evidence_validation import score_event, finalize_status
    cur={"code":"gdp_growth","indicator_source":"context","value":2.7,"unit":"%","unit_source":"explicit","year":2026,"period_source":"explicit","status":"forecast"}
    scored=score_event(cur,"Elle serait ensuite de 2,7 % en 2026.",{"country":"Tunisie"},explicit_country=False)
    row=finalize_status({**cur,**scored,"conflict_status":False})
    assert "safe_context_inheritance" in row["validation_evidence"]
    assert row["validation_status"] == "Validé"


def test_v417_missing_country_forces_review():
    from app.services.evidence_validation import score_event, finalize_status
    cur={"code":"inflation_rate","indicator_source":"explicit","value":6.1,"unit":"%","unit_source":"explicit","year":2021,"period_source":"explicit","status":"observed"}
    scored=score_event(cur,"En 2021, l'inflation était de 6,1 %.",{},explicit_country=False)
    row=finalize_status({**cur,**scored,"conflict_status":False})
    assert row["validation_status"] == "À vérifier"
    assert "missing_country" in row["validation_warnings"]


def _validate_context_case(sentence, code, value, year, unit="%", currency=None, scale=None):
    from app.services.evidence_validation import score_event, finalize_status
    cur={"code":code,"indicator_source":"context","value":value,"unit":unit,"unit_source":"explicit",
         "year":year,"period_source":"resolved","status":"observed","currency":currency,"scale":scale}
    scored=score_event(cur,sentence,{"country":"Tunisie"},explicit_country=False)
    return finalize_status({**cur,**scored,"conflict_status":False})

def test_v418_safe_context_il_atteignait_is_validated():
    row=_validate_context_case("En 2022, il atteignait encore 8,3 %.","inflation_rate",8.3,2022)
    assert row["validation_status"] == "Validé"
    assert "safe_context_inheritance" in row["validation_evidence"]

def test_v418_safe_context_ce_ratio_etait_is_validated():
    row=_validate_context_case("Un an auparavant, ce ratio était de 79,9 %.","public_debt_ratio",79.9,2023)
    assert row["validation_status"] == "Validé"
    assert "safe_context_inheritance" in row["validation_evidence"]

def test_v418_safe_context_elles_atteignaient_is_validated():
    row=_validate_context_case("Un an auparavant, elles atteignaient 23,1 milliards de dinars.",
                               "foreign_exchange_reserves",23.1,2023,"milliards TND","TND","milliards")
    assert row["validation_status"] == "Validé"
    assert "safe_context_inheritance" in row["validation_evidence"]

def test_v418_ambiguous_context_still_forces_review():
    from app.services.evidence_validation import score_event, finalize_status
    cur={"code":"inflation_rate","indicator_source":"context","value":4.2,"unit":"%","unit_source":"explicit",
         "year":2024,"period_source":"resolved","status":"observed","ambiguous_context":True}
    scored=score_event(cur,"Elle atteignait 4,2 % en 2024.",{"country":"Tunisie"},explicit_country=False)
    row=finalize_status({**cur,**scored,"conflict_status":False})
    assert row["validation_status"] == "À vérifier"
    assert "safe_context_inheritance" not in row["validation_evidence"]
