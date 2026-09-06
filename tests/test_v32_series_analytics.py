import pandas as pd
from app.services.series_analytics import build_indicator_series, indicator_statistics, statistics_export


def sample():
    return pd.DataFrame([
        {"indicator":"Inflation", "current_year":2022, "current_value":8.3, "current_unit":"%", "current_scale":None, "current_currency":None, "confidence":.9, "Valeur":"8.3 %"},
        {"indicator":"Inflation", "current_year":2023, "current_value":9.1, "current_unit":"%", "current_scale":None, "current_currency":None, "confidence":.9, "Valeur":"9.1 %"},
        {"indicator":"Inflation", "current_year":2024, "current_value":7.0, "current_unit":"%", "current_scale":None, "current_currency":None, "confidence":.9, "Valeur":"7 %"},
    ])


def test_series_evolution():
    s = build_indicator_series(sample(), "Inflation")
    assert s["Année"].tolist() == [2022, 2023, 2024]
    assert round(float(s.iloc[-1]["Évolution absolue"]), 1) == -2.1


def test_statistics():
    stats = indicator_statistics(build_indicator_series(sample(), "Inflation"))
    assert stats["observations"] == 3
    assert stats["minimum"] == 7.0
    assert stats["maximum"] == 9.1
    assert stats["evolution_absolue"] == -1.3


def test_all_statistics_export():
    out = statistics_export(sample())
    assert out.iloc[0]["Indicateur"] == "Inflation"
