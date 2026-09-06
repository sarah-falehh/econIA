import pytest
from app.models.article_document import ArticleDocument
from app.services.event_segmenter import split_economic_clauses
from app.services.context_resolver import DocumentContext
from app.services.multi_agent_pipeline import _extract_observations, run_multi_agent

def ctx(year=2025, month=None, quarter=None, country="Tunisie", iso="TUN"):
    return DocumentContext(anchor_year=year,current_year=year,current_month=month,current_quarter=quarter,
                           discourse_year=year,discourse_month=month,discourse_quarter=quarter,
                           last_country=country,last_country_iso3=iso)

def test_segmenter_splits_independent_indicator_value_pairs_not_comparison():
    s="Les recettes publiques ont atteint 4 120 milliards XOF, les dépenses publiques 5 040 milliards XOF et le déficit budgétaire 4,8 % du PIB."
    clauses=split_economic_clauses(s)
    assert len(clauses) == 3
    assert "recettes" in clauses[0].text.lower()
    assert "dépenses" in clauses[1].text.lower()
    assert "déficit" in clauses[2].text.lower()

def test_segmenter_preserves_from_to_comparison():
    s="Les réserves ont augmenté de 3,7 milliards USD, passant de 237,4 à 241,1 milliards USD."
    clauses=split_economic_clauses(s)
    assert len(clauses) == 1

@pytest.mark.parametrize("phrase,base_month,expected_month",[
    ("Deux mois plus tard, l'inflation était de 1,9 %.",1,3),
    ("trois mois plus tôt, l'inflation était de 1,9 %.",5,2),
    ("six mois plus tard, l'inflation était de 1,9 %.",8,2),
])
def test_generic_n_month_offsets(phrase,base_month,expected_month):
    c=ctx(year=2025,month=base_month)
    c.last_indicators=[("inflation_rate","Inflation")]
    obs=_extract_observations(phrase,fallback_indicators=c.last_indicators,context=c)
    assert obs
    assert obs[0]["month"] == expected_month

def test_local_explicit_debt_beats_prior_fdi_context():
    c=ctx()
    c.last_indicators=[("foreign_direct_investment","IDE")]
    s="La dette de l'administration centrale représentait 64,1 % du PIB en 2024."
    obs=_extract_observations(s,fallback_indicators=c.last_indicators,context=c)
    assert obs and obs[0]["code"] in {"public_debt_ratio","public_debt_stock"}
    assert obs[0]["code"] != "foreign_direct_investment"

def test_local_budget_deficit_beats_prior_inflation_context():
    c=ctx()
    c.last_indicators=[("inflation_rate","Inflation")]
    s="Le déficit public devrait atteindre 5,5 % du PIB en 2025 puis 4,6 % en 2026."
    obs=_extract_observations(s,fallback_indicators=c.last_indicators,context=c)
    assert obs
    assert all(o["code"]=="budget_deficit" for o in obs)

def test_same_semantic_text_is_format_agnostic():
    # The semantic core receives normalized text; source format must not alter
    # clause segmentation or event binding.
    samples=[
        "L'inflation était de 2,1 % en 2024.",
        "L'inflation était de 2,1 % en 2024.",  # CSV cell after normalization
        "L'inflation était de 2,1 % en 2024.",  # pasted text
    ]
    results=[]
    for s in samples:
        c=ctx(year=2024)
        results.append([(o["code"],o["value"],o["year"]) for o in _extract_observations(s,context=c)])
    assert results[0] == results[1] == results[2]



def test_relative_month_before_value_uses_prior_discourse_not_later_contrast_date():
    doc=ArticleDocument(
        text="En décembre 2024, l'inflation en Thaïlande était de 1,2 %. Un mois auparavant elle s'établissait à 0,9 %, tandis qu'en décembre 2023 elle était négative, à -0,8 %.",
        input_type="manual",title="Thaïlande",country="Thaïlande",language="fr"
    )
    rows=run_multi_agent(doc.to_dict())
    by={round(float(r["current_value"]),1):r for r in rows if r.get("indicator_code")=="inflation_rate"}
    assert (by[0.9]["current_year"],by[0.9]["current_month"])==(2024,11)
    assert (by[-0.8]["current_year"],by[-0.8]["current_month"])==(2023,12)


def test_public_finance_context_switches_between_revenue_and_expenditure():
    doc=ArticleDocument(
        text="Les recettes publiques ont atteint 4 120 milliards de francs CFA en 2024, tandis que les dépenses s'élevaient à 5 040 milliards. Pour 2025, les recettes sont projetées à 4 680 milliards.",
        input_type="manual",title="Finances publiques",country="Sénégal",language="fr"
    )
    rows=run_multi_agent(doc.to_dict())
    by={round(float(r["current_value"]),0):r for r in rows}
    assert by[4120]["indicator_code"]=="public_revenue"
    assert by[5040]["indicator_code"]=="public_expenditure"
    assert by[4680]["indicator_code"]=="public_revenue"
    assert by[4680]["fact_type"]=="forecast"


def test_local_revenue_and_expenditure_nouns_beat_later_budget_deficit():
    doc=ArticleDocument(
        text="Les recettes de 4 120 milliards de francs CFA et les dépenses de 5 040 milliards en 2024 coexistent avec un déficit budgétaire de 4,8 % du PIB.",
        input_type="manual",title="Finances publiques",country="Sénégal",language="fr"
    )
    rows=run_multi_agent(doc.to_dict())
    by={round(float(r["current_value"]),1):r for r in rows}
    assert by[4120.0]["indicator_code"]=="public_revenue"
    assert by[5040.0]["indicator_code"]=="public_expenditure"
    assert by[4.8]["indicator_code"]=="budget_deficit"


def test_relative_month_uses_prior_explicit_month_not_later_historical_month():
    c=ctx(year=2024,month=12,country="Thaïlande",iso="THA")
    c.last_indicators=[("inflation_rate","Inflation")]
    s="L'inflation était de 1,2 % en décembre 2024, 0,9 % un mois auparavant et -0,8 % en décembre 2023."
    obs=_extract_observations(s,fallback_indicators=c.last_indicators,context=c)
    by={round(float(o["value"]),1):o for o in obs}
    assert (by[1.2]["year"],by[1.2]["month"])==(2024,12)
    assert (by[0.9]["year"],by[0.9]["month"])==(2024,11)
    assert (by[-0.8]["year"],by[-0.8]["month"])==(2023,12)


def test_previous_year_after_value_resolves_from_prior_explicit_anchor():
    c=ctx(year=2025,country="Malaisie",iso="MYS")
    s="La dette publique représentait 64,1 % du PIB fin 2024, contre 62,9 % l'année précédente."
    obs=_extract_observations(s,context=c)
    by={round(float(o["value"]),1):o for o in obs}
    assert by[64.1]["year"]==2024
    assert by[62.9]["year"]==2023


def test_csv_and_manual_inputs_share_same_event_semantics():
    import pandas as pd
    from app.services.csv_reader import dataframe_to_documents
    sentence="L'inflation était de 2,1 % en 2024."
    manual=ArticleDocument(text=sentence,input_type="manual",title="Test",country="Tunisie",language="fr")
    csvdoc=dataframe_to_documents(pd.DataFrame([{"texte":sentence,"pays":"Tunisie"}]),
                                  text_column="texte",country_column="pays")[0]
    def sig(doc):
        return sorted((r["indicator_code"],round(float(r["current_value"]),3),r["current_year"])
                      for r in run_multi_agent(doc.to_dict()))
    assert sig(manual)==sig(csvdoc)
