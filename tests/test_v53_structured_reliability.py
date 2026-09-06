from app.services.multi_agent_pipeline import _extract_observations, get_last_trace, run_multi_agent
from app.services.structured_table_extractor import extract_structured_table_events
from app.services.context_resolver import DocumentContext
from app.services.series_analytics import auditable_observations_export
import pandas as pd


def base_doc(text="Texte économique de test suffisamment long."):
    return {"document_id":"v53","text":text,"input_type":"manual","language":"fr",
            "country":"Tunisie","country_iso3":"TUN","source":"Test"}


def test_multilevel_sector_table_preserves_every_cell_and_range():
    doc=base_doc()
    doc["structured_tables"]=[{"page":2,"table_index":0,"bbox":[0,0,100,100],"rows":[
        ["", "CSU nominal", "", "Taux de salaire", ""],
        ["Secteur", "2001-2010", "2011-2016", "2001-2010", "2011-2016"],
        ["Agriculture", "6,3", "3,7", "6,4", "9,5"],
        ["Industrie", "4,8", "8,3", "6,0", "7,9"],
    ]}]
    events,audit=extract_structured_table_events(doc)
    assert len(events)==8
    assert {e["sector"] for e in events}=={"Agriculture","Industrie"}
    assert {e["period_label"] for e in events}=={"2001-2010","2011-2016"}
    assert audit[0]["status"]=="extracted"


def test_sector_block_table_preserves_indicator_period_and_sector():
    doc=base_doc(); doc["structured_tables"]=[{"page":3,"table_index":0,"bbox":[0,0,1,1],"rows":[
        ["", "", "2001-2016", "2009-2016"],
        ["Agriculture", "", "", ""],
        ["", "Productivité du travail", "2,1", "3,7"],
        ["", "Taux de salaire", "7,6", "9,1"],
    ]}]
    events,_=extract_structured_table_events(doc)
    assert len(events)==4
    assert {e["code"] for e in events}=={"labor_productivity","nominal_wage_rate"}
    assert {e["sector"] for e in events}=={"Agriculture"}


def test_period_range_is_not_reduced_to_terminal_year():
    obs=_extract_observations("Durant la période 2001-2016, la productivité du travail a progressé de 2,1 % en moyenne par an.")
    assert obs and obs[0]["year"] is None
    assert obs[0]["period_type"]=="average_range"
    assert (obs[0]["period_start"],obs[0]["period_end"])==("2001","2016")


def test_undated_annual_average_does_not_inherit_stale_year():
    from app.services.context_resolver import DocumentContext
    ctx=DocumentContext(anchor_year=2019,current_year=2019,discourse_year=2019)
    obs=_extract_observations("Les prix alimentaires ont augmenté de 4,4 % en moyenne par an.",context=ctx)
    assert obs and obs[0]["year"] is None
    assert obs[0]["period_type"]=="annual_average_unknown_range"


def test_geography_groups_align_respectively_without_becoming_tunisia():
    text="Les PECO, les concurrents asiatiques et la Tunisie affichaient respectivement 1,3 %, 3,2 % et 5,5 % d'inflation en 2018."
    rows=run_multi_agent(base_doc(text))
    by={round(float(r["current_value"]),1):(r["country"],r["geography_type"]) for r in rows}
    assert by[1.3]==("PECO","economic_group")
    assert by[3.2]==("Concurrents asiatiques","economic_group")
    assert by[5.5]==("Tunisie","country")


def test_numerical_coverage_reports_unbound_numbers():
    run_multi_agent(base_doc("L'inflation a atteint 7,0 % en 2024, avec un indice technique de 12 sans unité."))
    trace=get_last_trace()["numerical_coverage"]
    assert any(x["raw_token"]=="7,0" and x["outcome"]=="extracted" for x in trace)
    assert any(x["raw_token"]=="12" and x["outcome"]=="unresolved" for x in trace)


def test_specialized_indicators_have_readable_official_labels():
    rows=run_multi_agent(base_doc("Le taux directeur a atteint 7,75 % en 2019."))
    assert rows[0]["indicator"]=="Taux directeur de la banque centrale"
    assert rows[0]["indicator"]!="policy_rate"


def test_semantic_carrier_prevents_generic_growth_from_becoming_gdp():
    text=("Le pouvoir d'achat des ménages est mesuré par le revenu disponible réel. "
          "Son évolution a ralenti durant la période 2011-2016 pour atteindre 2,2 % en moyenne.")
    rows=run_multi_agent(base_doc(text))
    assert rows and {r["indicator_code"] for r in rows}=={"purchasing_power_growth"}


def test_two_average_ranges_align_with_two_values_respectively():
    obs=_extract_observations("La productivité avait un rythme moyen de 2,2 % contre 4,4 % pour les périodes 2011-2016 et 2000-2010 respectivement.")
    by={round(float(o["value"]),1):o["period_label"] for o in obs}
    assert by=={2.2:"2011-2016",4.4:"2000-2010"}


def test_shared_unit_range_keeps_both_cost_bounds_without_inventing_exchange_rate():
    obs=_extract_observations("Les coûts économiques variaient entre 23 et 80 % selon les secteurs en 2018.")
    assert {round(float(o["value"]),1) for o in obs}=={23.0,80.0}
    assert {o["code"] for o in obs}=={"economic_cost_level"}


def test_bilateral_exchange_values_share_the_local_year_and_indicator():
    s="Le dinar s'est déprécié de 10,3 % face au dollar contre une appréciation de 7,6 % face à l'euro en 2015."
    obs=_extract_observations(s)
    assert {o["code"] for o in obs}=={"exchange_rate_change"}
    assert {o["year"] for o in obs}=={2015}


def test_bilateral_exchange_explicit_year_beats_stale_context_anchor():
    context=DocumentContext(anchor_year=2016,current_year=2016,discourse_year=2016)
    s="En 2015, année durant laquelle le dinar s'est déprécié de 10,3 % face au dollar et s'est apprécié de 7,6 % face à l'euro."
    obs=_extract_observations(s,context=context)
    assert {round(float(o["value"]),1) for o in obs}=={10.3,7.6}
    assert {o["code"] for o in obs}=={"exchange_rate_change"}
    assert {o["year"] for o in obs}=={2015}


def test_explicit_exchange_series_overrides_stale_tmm_context_for_all_siblings():
    context=DocumentContext(
        anchor_year=2016,current_year=2016,discourse_year=2016,
        last_indicators=[("real_money_market_rate","TMM réel")],
    )
    s=("Elle a été tirée par l’évolution du taux de change en 2015, année durant laquelle "
       "le dinar s’est déprécié de 10.3% par rapport au dollar contre une appréciation "
       "de 7.6% face à l’euro.")
    obs=_extract_observations(s,fallback_indicators=context.last_indicators,context=context)
    assert {(round(float(o["value"]),1),o["year"],o["code"]) for o in obs}=={
        (10.3,2015,"exchange_rate_change"),(7.6,2015,"exchange_rate_change")
    }


def test_pasted_text_gdp_negation_and_activity_coreference_keep_four_values():
    text=("Après avoir progressé de 2,6 % en 2023, le PIB réel n'a augmenté que de 1,9 % en 2024. "
          "Pour 2025, l'activité serait en hausse de 2,2 %, avant une accélération projetée à 2,4 % en 2026.")
    rows=run_multi_agent({**base_doc(text),"country":"Portugal"})
    assert {(r["current_value"],r["current_period_label"],r["fact_type"]) for r in rows}=={
        (2.6,"2023","observed"),(1.9,"2024","observed"),
        (2.2,"2025","forecast"),(2.4,"2026","forecast"),
    }
    assert {r["indicator_code"] for r in rows}=={"gdp_growth"}


def test_wide_country_year_table_is_structured_not_narrative():
    doc=base_doc();doc["structured_tables"]=[{"page":1,"table_index":0,"bbox":[0,0,1,1],"rows":[
        ["Pays","Année","PIB réel (%)","Inflation moyenne (%)","Dette publique (% PIB)","Type"],
        ["Portugal","2025","2,2","2,3","92,8","Prévision"],
    ]}]
    events,_=extract_structured_table_events(doc)
    assert len(events)==3
    assert {e["code"] for e in events}=={"gdp_growth","inflation_annual_average","public_debt_ratio"}
    assert {e["status"] for e in events}=={"forecast"}


def test_long_table_preserves_month_quarter_and_fact_type():
    doc=base_doc();doc["structured_tables"]=[{"page":1,"table_index":0,"bbox":[0,0,1,1],"rows":[
        ["Pays","Période","Indicateur","Valeur","Unité","Nature"],
        ["Thaïlande","2025-M02","Taux directeur","2,00","%","Observé"],
        ["Portugal","2025-Q2","Chômage","3,1","%","Estimé"],
    ]}]
    events,_=extract_structured_table_events(doc)
    assert len(events)==2
    assert (events[0]["year"],events[0]["month"],events[0]["quarter"])==(2025,2,None)
    assert (events[1]["year"],events[1]["month"],events[1]["quarter"])==(2025,None,2)
    assert events[1]["status"]=="estimate"


def test_multicountry_table_rows_override_surrounding_document_country():
    doc=base_doc("Portugal - conjoncture. La croissance a atteint 1,9 % en 2024.")
    doc["country"]="Portugal";doc["country_iso3"]="PRT"
    doc["structured_tables"]=[{"page":3,"table_index":0,"bbox":[0,0,1,1],"rows":[
        ["Pays","Année","PIB réel (%)","Inflation moyenne (%)","Dette publique (% PIB)","Type"],
        ["Portugal","2024","1,9","2,6","95,7","Observé"],
        ["Thaïlande","2024","2,5","0,7","63,1","Observé"],
        ["Argentine","2024","-1,7","118,3","83,2","Observé"],
    ]}]
    rows=run_multi_agent(doc)
    table=[r for r in rows if r.get("table_source")=="geometry_table"]
    assert len(table)==9
    assert {(r["country"],r["country_iso3"]) for r in table}=={
        ("Portugal","PRT"),("Thaïlande","THA"),("Argentine","ARG")
    }


def test_auditable_export_preserves_sector_partner_and_table_provenance():
    frame=pd.DataFrame([{
        "country":"Tunisie","geography_type":"country","indicator":"Variation de la productivité",
        "current_value":0.6,"current_unit":"%","current_year":2016,"fact_type":"observed",
        "source":"rapport","sentence":"preuve","confidence":.9,"validation_status":"Validé",
        "sector":"Industries manufacturières","subsector":"Textile","partner_geography":"Zone euro",
        "table_page":20,"table_index":2,"table_row_label":"Textile","table_column_label":"Productivité 2016",
        "period_resolution_source":"table_header","validation_warnings":[],
    }])
    out=auditable_observations_export(frame)
    assert out.loc[0,"Secteur"]=="Industries manufacturières"
    assert out.loc[0,"Partenaire"]=="Zone euro"
    assert out.loc[0,"Page"]==20
    assert out.loc[0,"Ligne du tableau"]=="Textile"


def test_policy_rate_sequence_keeps_all_values_and_local_months():
    text=("Le taux directeur, maintenu à 2,50 % jusqu'en septembre 2024, "
          "a été abaissé à 2,25 % en octobre puis à 2,00 % en février 2025.")
    obs=_extract_observations(text)
    assert {(o["value"],o["period_label"]) for o in obs}=={
        (2.5,"2024-M09"),(2.25,"2024-M10"),(2.0,"2025-M02")
    }
    assert {o["code"] for o in obs}=={"policy_rate"}


def test_year_on_year_inflation_coreference_keeps_three_monthly_values():
    context=DocumentContext(anchor_year=2024,current_year=2024,last_indicators=[
        ("inflation_annual_average","Inflation moyenne")
    ])
    text=("Le rythme sur douze mois est passé de 211,4 % en décembre 2023 "
          "à 117,8 % en juin 2024 puis à 82,1 % en décembre 2024.")
    obs=_extract_observations(text,fallback_indicators=context.last_indicators,context=context)
    assert {(o["value"],o["period_label"]) for o in obs}=={
        (211.4,"2023-M12"),(117.8,"2024-M06"),(82.1,"2024-M12")
    }
    assert {o["code"] for o in obs}=={"inflation_rate"}


def test_contraction_then_forecast_preserves_sign_and_fact_types():
    obs=_extract_observations(
        "Après une contraction de 1,7 % en 2024, le PIB réel devrait rebondir de 4,8 % en 2025."
    )
    assert {(o["value"],o["year"],o["status"]) for o in obs}=={
        (-1.7,2024,"observed"),(4.8,2025,"forecast")
    }


def test_specific_price_heads_and_respectively_years_win():
    core=_extract_observations(
        "En 2017 et 2018, l'inflation sous-jacente a atteint 5,4 % et 7,4 % respectivement."
    )
    assert {(o["code"],o["value"],o["year"]) for o in core}=={
        ("core_inflation",5.4,2017),("core_inflation",7.4,2018)
    }
    products=_extract_observations(
        "Les prix alimentaires ont augmenté de 4,4 %, puis les prix manufacturiers de 3,8 %."
    )
    assert [(o["code"],o["value"]) for o in products]==[
        ("food_inflation",4.4),("manufactured_goods_inflation",3.8)
    ]


def test_context_accepts_year_on_year_rhythm_and_bounded_gdp_pronoun():
    inflation=DocumentContext(last_indicators=[("inflation_annual_average","Inflation moyenne")])
    assert inflation.contextual_indicators("Le rythme sur douze mois est passé de 10 % à 8 %.")
    gdp=DocumentContext(last_indicators=[("gdp_growth","Croissance du PIB")])
    assert gdp.contextual_indicators("Avec le redressement attendu, elle pourrait atteindre 6,7 %.")


def test_scenario_verbs_are_forecasts_and_specialist_subject_controls_scope():
    scenario=_extract_observations("Le scénario de référence prévoit 3,2 % en 2025 et retient 2,4 % en 2026.",
                                   fallback_indicators=[("gdp_growth","Croissance du PIB")])
    assert {o["status"] for o in scenario}=={"forecast"}
    effective=_extract_observations(
        "Le taux de change effectif réel s'est déprécié de 7,6 %, sous l'effet du dinar."
    )
    assert {o["code"] for o in effective}=={"real_effective_exchange_rate"}
    competitors=_extract_observations(
        "Le prix des concurrents a progressé de 5,9 %, puis de 6,9 % avec le change."
    )
    assert {o["code"] for o in competitors}=={"competitor_prices"}
