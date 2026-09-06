import pandas as pd
from app.services.csv_reader import dataframe_to_documents_auto
from app.services.multi_agent_pipeline import run_multi_agent


def test_csv_country_metadata_is_propagated():
    df = pd.DataFrame([{
        "titre": "x",
        "source": "INS",
        "date": "2025-01-01",
        "pays": "Tunisie",
        "texte": "Les importations ont atteint 20 millions de dinars en 2025.",
        "url": "https://example.org",
    }])
    docs, schema = dataframe_to_documents_auto(df)
    d = docs[0].to_dict()
    assert d["country"] == "Tunisie"
    assert d["source_url"] == "https://example.org"
    rows = run_multi_agent(d)
    assert rows and all(r["country"] == "Tunisie" for r in rows)


def test_value_period_alignment_comparison():
    d = {
        "document_id": "x",
        "text": "Durant l’année 2025, les exportations tunisiennes ont atteint 63 695,1 millions de dinars, contre 62 077,6 millions en 2024.",
        "country": "Tunisie",
        "language": "fr",
    }
    rows = run_multi_agent(d)
    vals = {round(r["current_value"], 1): r["current_year"] for r in rows}
    assert vals[63695.1] == 2025
    assert vals[62077.6] == 2024


def test_monthly_periods_and_specific_inflation():
    d = {
        "document_id": "x",
        "text": "En janvier 2025, le taux d’inflation s’est replié à 6,0 %, contre 6,2 % en décembre 2024. L’inflation sous-jacente a atteint 4,9 % en novembre 2025.",
        "country": "Tunisie",
        "language": "fr",
    }
    rows = run_multi_agent(d)
    by_val = {round(r["current_value"], 1): r for r in rows}
    assert (by_val[6.0]["current_year"], by_val[6.0]["current_month"]) == (2025, 1)
    assert (by_val[6.2]["current_year"], by_val[6.2]["current_month"]) == (2024, 12)
    assert by_val[4.9]["indicator_code"] == "core_inflation"
