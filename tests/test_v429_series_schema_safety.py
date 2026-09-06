import pandas as pd

from app.services.series_analytics import build_indicator_series, SERIES_DERIVED_COLUMNS


def test_rejected_only_indicator_returns_empty_stable_schema():
    df = pd.DataFrame([{
        "country": "Portugal",
        "indicator": "Indicateur rejeté",
        "current_year": 2024,
        "current_value": 12.3,
        "validation_status": "Rejeté",
        "needs_review": True,
    }])
    result = build_indicator_series(df, "Indicateur rejeté")
    assert result.empty
    for column in SERIES_DERIVED_COLUMNS:
        assert column in result.columns


def test_empty_input_returns_stable_series_schema():
    df = pd.DataFrame(columns=["country","indicator","current_year","current_value"])
    result = build_indicator_series(df)
    assert result.empty
    for column in SERIES_DERIVED_COLUMNS:
        assert column in result.columns
