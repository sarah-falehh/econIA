from app.services.context_resolver import DocumentContext
from app.services.multi_agent_pipeline import run_multi_agent


def test_sibling_year_relations_use_explicit_anchor_not_previous_relative_result():
    ctx = DocumentContext(anchor_year=2024, current_year=2024, discourse_year=2024)
    m, q, y = ctx.resolve_period("L'année d'avant, elle était de 5,7 %.", None, None, None)
    assert (m, q, y) == (None, None, 2023)
    # Simulate the relative result becoming the current event.
    ctx.remember_explicit_period(None, None, 2023)
    m, q, y = ctx.resolve_period("Deux ans plus tôt, elle atteignait 7,2 %.", None, None, None)
    assert (m, q, y) == (None, None, 2022)


def test_sibling_quarter_relations_use_explicit_anchor():
    ctx = DocumentContext(anchor_year=2025, current_year=2025, current_quarter=2,
                          discourse_year=2025, discourse_quarter=2)
    m, q, y = ctx.resolve_period("Au trimestre qui précédait, ce taux était de 5,0 %.", None, None, None)
    assert (m, q, y) == (None, 1, 2025)
    ctx.remember_explicit_period(None, 1, 2025)
    m, q, y = ctx.resolve_period("Trois mois plus tard, il atteindrait 5,3 %.", None, None, None)
    assert (m, q, y) == (None, 3, 2025)


def test_new_zealand_temporal_anchor_sequence_end_to_end():
    doc = {"document_id":"v423-anchor", "source":"test", "language":"fr", "title":"Nouvelle-Zélande 2025",
           "text": "En 2024, l'inflation s'est établie à 2,9 %. L'année d'avant, elle était de 5,7 %. Deux ans plus tôt, elle atteignait 7,2 %."}
    rows = run_multi_agent(doc)
    got = {(round(float(r['current_value']), 1), r.get('current_year')) for r in rows if r.get('indicator') and 'inflation' in r['indicator'].lower()}
    assert (2.9, 2024) in got
    assert (5.7, 2023) in got
    assert (7.2, 2022) in got
