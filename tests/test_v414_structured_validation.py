from app.services.multi_agent_pipeline import run_multi_agent

def doc(text): return {"document_id":"v414","language":"fr","text":text,"source":"benchmark","country":"Tunisie"}

def test_deterministic_comparison_is_validated_without_threshold_hack():
    rows=run_multi_agent(doc("En 2021, le taux d’inflation des prix à la consommation de Tunisie s’est établi à 4,7 %, contre 5,9 % en 2020."))
    assert len(rows)==2
    assert all(r["validation_status"]=="Validé" for r in rows)
    assert all("deterministic_association" in r["validation_evidence"] for r in rows)
    assert all("validation_dimensions" in r for r in rows)

def test_contextual_pronoun_remains_reviewable_when_association_is_weak():
    rows=run_multi_agent(doc("En 2021, le taux d’inflation atteint 4,7 %. En 2019, il atteignait 6,4 %."))
    old=next(r for r in rows if r["current_year"]==2019)
    assert old["validation_status"] in {"Validé","À vérifier"}
    assert old["validation_dimensions"]["indicator"] < 1.0

def test_export_percentage_growth_is_not_rejected_as_monetary_level():
    rows=run_multi_agent(doc("Les exportations de biens et services ont progressé de 6,4 % en 2022."))
    assert len(rows)==1
    assert rows[0]["indicator_code"]=="exports_growth"
    assert rows[0]["current_unit"]=="%"
    assert rows[0]["validation_status"]!="Rejeté"

def test_true_conflict_still_forces_review():
    rows=run_multi_agent(doc("En 2024, l’inflation atteint 7,0 %. Un autre passage indique une inflation de 7,8 % en 2024."))
    assert len(rows)==2
    assert all(r["conflict_status"] for r in rows)
    assert all(r["validation_status"]=="À vérifier" for r in rows)
