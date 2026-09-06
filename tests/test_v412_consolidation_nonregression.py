from app.services.multi_agent_pipeline import run_multi_agent


def _run(text, **meta):
    doc={"document_id":"v412","country":"Tunisie","language":"fr","text":text, **meta}
    return run_multi_agent(doc)


def test_annual_period_does_not_inherit_stale_december():
    rows=_run(
        "Les réserves officielles de change ont atteint 20,0 milliards de dinars en décembre 2021. "
        "En 2022, le taux d’inflation s’est établi à 5,3 %, contre 6,5 % en 2021."
    )
    infl=[r for r in rows if r["indicator_code"]=="inflation_rate"]
    by={r["current_value"]:r for r in infl}
    assert by[5.3]["current_period_label"]=="2022"
    assert by[6.5]["current_period_label"]=="2021"
    assert by[5.3]["current_month"] is None
    assert by[6.5]["current_month"] is None


def test_quarter_period_does_not_collapse_to_december():
    rows=_run(
        "Les réserves officielles de change ont atteint 20,0 milliards de dinars en décembre 2021. "
        "Le taux de chômage a atteint 12,1 % au quatrième trimestre 2022. "
        "Au trimestre précédent, il s’établissait à 11,6 %."
    )
    u=[r for r in rows if r["indicator_code"]=="unemployment_rate"]
    by={r["current_value"]:r for r in u}
    assert by[12.1]["current_period_label"]=="2022-Q4"
    assert by[11.6]["current_period_label"]=="2022-Q3"


def test_document_month_fallback_is_narrow_and_preserved():
    rows=_run(
        "L’inflation sous-jacente a atteint 4,9 %, après 5,0 % en novembre.",
        title="Indice des prix à la consommation — décembre 2025",
    )
    by={r["current_value"]:r for r in rows if r["indicator_code"]=="core_inflation"}
    assert by[4.9]["current_period_label"]=="2025-M12"
    assert by[5.0]["current_period_label"]=="2025-M11"


def test_cette_meme_annee_resolves_to_previous_sentence_year():
    rows=_run(
        "La croissance annuelle du PIB est indiquée à 2,5 % en 2025. "
        "L’inflation des prix à la consommation est indiquée à 5,2 % pour cette même année."
    )
    inf=[r for r in rows if r["indicator_code"]=="inflation_rate"]
    assert inf and inf[0]["current_year"]==2025


def test_projetait_is_forecast():
    rows=_run("Elle projetait alors une croissance de 1,9 % en 2025.")
    assert len(rows)==1
    assert rows[0]["indicator_code"]=="gdp_growth"
    assert rows[0]["observation_type"]=="forecast"


def test_same_period_previous_year_preserves_quarter():
    rows=_run(
        "Au premier trimestre 2025, les exportations ont atteint 15 325,1 millions de dinars. "
        "Les importations ont atteint 20 375,5 millions de dinars, contre 19 315,3 millions sur la même période de l’année précédente."
    )
    im=[r for r in rows if r["indicator_code"]=="imports"]
    by={round(r["current_value"],1):r for r in im}
    assert by[20375.5]["current_period_label"]=="2025-Q1"
    assert by[19315.3]["current_period_label"]=="2024-Q1"


def test_imf_average_and_end_period_inflation_are_distinct():
    rows=_run(
        "L’inflation moyenne des prix à la consommation est projetée à 6,5 % en 2026, "
        "tandis que l’inflation en fin de période est indiquée à 7,0 %."
    )
    codes={r["indicator_code"] for r in rows}
    assert "inflation_annual_average" in codes
    assert "inflation_end_period" in codes


def test_pdf_source_falls_back_to_filename():
    rows=_run("En 2024, le taux de chômage s’est établi à 15,2 %.", filename="rapport_test.pdf")
    assert rows and rows[0]["source"]=="rapport_test.pdf"

def test_one_year_earlier_preserves_month_granularity():
    rows=_run(
        "Les réserves officielles de change ont atteint 18,9 milliards de dinars en décembre 2021. "
        "Un an auparavant, elles s’élevaient à 17,5 milliards de dinars."
    )
    res=[r for r in rows if r["indicator_code"]=="foreign_exchange_reserves"]
    by={r["current_value"]:r for r in res}
    assert by[18.9]["current_period_label"]=="2021-M12"
    assert by[17.5]["current_period_label"]=="2020-M12"

def test_trade_balance_and_coverage_are_first_class_indicators():
    rows=_run(
        "Le déficit commercial a atteint 21 800,3 millions de dinars en 2025. "
        "Le taux de couverture s’est établi à 74,5 % en 2025."
    )
    codes={r['indicator_code'] for r in rows}
    assert 'trade_balance' in codes
    assert 'trade_coverage_ratio' in codes


def test_monthly_cpi_change_is_not_general_annual_inflation():
    rows=_run("Sur un mois, l’indice des prix à la consommation a augmenté de 0,2 % en décembre 2025.")
    assert rows and rows[0]['indicator_code']=='cpi_monthly_change'

def test_document_year_anchors_primary_trade_comparison_value():
    rows=_run(
        "Le déficit commercial a atteint 21 800,3 millions de dinars contre 18 927,6 millions en 2024.",
        title="Commerce extérieur — année 2025",
    )
    bal=[r for r in rows if r['indicator_code']=='trade_balance']
    by={round(abs(r['current_value']),1):r for r in bal}
    assert by[21800.3]['current_period_label']=='2025'
    assert by[18927.6]['current_period_label']=='2024'
    assert by[21800.3]['current_value'] < 0 and by[18927.6]['current_value'] < 0


def test_document_year_anchors_primary_coverage_ratio():
    rows=_run(
        "Le taux de couverture s’est établi à 74,5 %, contre 76,6 % en 2024.",
        title="Commerce extérieur — année 2025",
    )
    cov=[r for r in rows if r['indicator_code']=='trade_coverage_ratio']
    by={r['current_value']:r for r in cov}
    assert by[74.5]['current_period_label']=='2025'
    assert by[76.6]['current_period_label']=='2024'

def test_document_year_anchors_primary_after_comparison_value():
    rows=_run(
        "Le déficit commercial s’est établi à 5 050,5 millions de dinars, après 3 027,4 millions au premier trimestre 2024.",
        title="Commerce extérieur — premier trimestre 2025",
    )
    bal=[r for r in rows if r['indicator_code']=='trade_balance']
    by={round(abs(r['current_value']),1):r for r in bal}
    assert by[5050.5]['current_period_label']=='2025-Q1'
    assert by[3027.4]['current_period_label']=='2024-Q1'
