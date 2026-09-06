from app.services.multi_agent_pipeline import run_multi_agent


def _run(text: str, language: str = "ar"):
    return run_multi_agent({
        "document_id": "v575-general",
        "language": language,
        "country": "Algérie" if language == "ar" else "Tunisie",
        "country_iso3": "DZA" if language == "ar" else "TUN",
        "source": "regression",
        "text": text,
    })


def test_arabic_multi_value_clause_has_complete_numeric_coverage():
    rows = _run(
        "سجل الناتج المحلي الإجمالي الحقيقي نموا قدره 3.1% في 2022، "
        "ثم تسارع إلى 4.2% في 2023 قبل أن يتباطأ إلى 3.6% في 2024."
    )
    assert {(r["current_value"], r["current_year"]) for r in rows} == {
        (3.1, 2022), (4.2, 2023), (3.6, 2024)
    }


def test_arabic_geography_value_list_binds_in_order():
    rows = _run(
        "في 2024 بلغ التضخم 5.4% في الجزائر، مقابل 3.8% في المغرب و7.1% في تونس."
    )
    assert {(r["country"], r["current_value"]) for r in rows} == {
        ("Algérie", 5.4), ("Maroc", 3.8), ("Tunisie", 7.1)
    }


def test_arabic_same_period_is_shared_between_sibling_series():
    rows = _run(
        "ارتفعت الصادرات من 61.8 مليار دولار في 2023 إلى 66.4 مليار دولار في 2024، "
        "بينما زادت الواردات من 47.2 إلى 50.6 مليار دولار خلال الفترة نفسها."
    )
    imports = {(r["current_value"], r["current_year"]) for r in rows if r["indicator_code"] == "imports"}
    assert imports == {(47.2, 2023), (50.6, 2024)}


def test_arabic_chart_ticks_are_not_economic_events():
    rows = _run(
        "في الرسم تظهر تدريجات المحور 0% و2% و4% و6% و8% و10%. "
        "هذه القيم مجرد تدريجات وليست ملاحظات اقتصادية."
    )
    assert rows == []


def test_french_pipeline_contract_remains_unchanged():
    rows = _run(
        "En Tunisie, la croissance du PIB réel a atteint 2,6 % en 2023, "
        "puis 1,9 % en 2024.", language="fr"
    )
    assert [(r["current_value"], r["current_year"]) for r in rows] == [(2.6, 2023), (1.9, 2024)]
