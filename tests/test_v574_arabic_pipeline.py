from app.services.multi_agent_pipeline import _candidate_sentences, run_multi_agent, get_last_trace
from app.services.pdf_reader import _extract_page_text


class _ArabicPage:
    def get_text(self, kind, sort=False):
        if kind == "text":
            return "بلغ التضخم 3.4% في 2024.\n"
        raise AssertionError("Arabic RTL reconstruction must not sort words left-to-right")


def test_arabic_pdf_text_uses_logical_stream_not_ltr_word_sorting():
    assert _extract_page_text(_ArabicPage()) == "بلغ التضخم 3.4% في 2024."


def test_arabic_sentence_selection_keeps_numeric_economic_sentences():
    text = "بلغ التضخم 3.4% في 2024. ومن المتوقع أن ينخفض إلى 2.9% في 2025."
    candidates = _candidate_sentences(text)
    assert len(candidates) == 2


def test_arabic_atomic_extraction_and_french_non_regression_contract():
    document = {
        "document_id": "arabic-regression",
        "language": "ar",
        "country": "Maroc",
        "country_iso3": "MAR",
        "source": "اختبار",
        "text": (
            "سجل الناتج المحلي الإجمالي الحقيقي نموا قدره 3.4% في 2023، "
            "بينما يتوقع أن يرتفع إلى 3.7% في 2026. "
            "بلغ متوسط التضخم السنوي 6.1% في 2023 قبل أن ينخفض إلى 3.4% في 2024. "
            "بلغت صادرات السلع 455.2 مليار درهم في 2024. "
            "بلغت احتياطيات النقد الأجنبي 372.5 مليار درهم في نهاية 2024."
        ),
    }
    rows = run_multi_agent(document)
    events = {(row["indicator_code"], row["current_value"], row["current_year"]) for row in rows}
    assert ("gdp_growth", 3.4, 2023) in events
    assert ("gdp_growth", 3.7, 2026) in events
    assert ("inflation_annual_average", 6.1, 2023) in events
    assert ("inflation_annual_average", 3.4, 2024) in events
    assert ("exports", 455.2, 2024) in events
    assert ("foreign_exchange_reserves", 372.5, 2024) in events
    assert all(row.get("country") == "Maroc" for row in rows)
    assert any(row.get("current_currency") == "MAD" for row in rows)
    assert get_last_trace()["unresolved_numeric_count"] == 0


def test_arabic_percentage_point_is_not_accepted_as_a_level():
    rows = run_multi_agent({
        "document_id": "arabic-change",
        "language": "ar",
        "country": "Maroc",
        "text": "كان نمو الناتج المحلي الإجمالي أقل بـ 0.6 نقطة مئوية عن العام السابق.",
    })
    assert not any(
        row.get("current_value") == 0.6 and row.get("validation_status") != "Rejeté"
        for row in rows
    )


def test_arabic_relative_month_quarter_and_year_resolution():
    rows = run_multi_agent({
        "document_id": "arabic-relative-periods",
        "language": "ar", "country": "Maroc", "country_iso3": "MAR",
        "text": (
            "وفي ديسمبر 2024 بلغ التضخم 2.9%، مقابل 3.2% قبل ثلاثة أشهر. "
            "استقر معدل البطالة عند 13.0% في الربع الرابع من 2024، "
            "مقارنة بـ 13.4% في الربع السابق و12.8% قبل عام. "
            "بلغت صادرات السلع 455.2 مليار درهم في 2024 مقابل "
            "429.6 مليار درهم في العام السابق."
        ),
    })
    points = {(r["indicator_code"], r["current_value"]): (r["current_year"], r.get("current_month"), r.get("current_quarter")) for r in rows}
    assert points[("inflation_rate", 2.9)] == (2024, 12, None)
    assert points[("inflation_rate", 3.2)] == (2024, 9, None)
    assert points[("unemployment_rate", 13.4)] == (2024, None, 3)
    assert points[("unemployment_rate", 12.8)] == (2023, None, 4)
    assert points[("exports", 429.6)][0] == 2023
