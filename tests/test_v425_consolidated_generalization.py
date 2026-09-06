from io import BytesIO

from app.services.currency_registry import detect_currency, current_currency_for_country
from app.services.multi_agent_pipeline import run_multi_agent
from app.services.pdf_reader import read_pdf


def _doc(text, country=None, iso3=None):
    return {"document_id":"v425","text":text,"language":"fr","country":country,"country_iso3":iso3,"source":"test"}


def test_dynamic_currency_registry_unseen_goldv4_currencies():
    cases = [
        ("4 120 milliards de roupies indonésiennes", "IDN", "IDR"),
        ("245 milliards de cedis", "GHA", "GHS"),
        ("100 milliards de couronnes norvégiennes", "NOR", "NOK"),
        ("80 milliards de pesos", "MEX", "MXN"),
        ("12 milliards de wons sud-coréens", "KOR", "KRW"),
    ]
    for text, iso3, expected in cases:
        assert detect_currency(text, iso3) == expected
        assert current_currency_for_country(iso3) == expected


def test_dynamic_currency_propagates_to_sibling_monetary_comparison():
    rows = run_multi_agent(_doc(
        "En 2024, les exportations du Ghana ont atteint 245 milliards de cedis, "
        "contre 198 milliards en 2023.", "Ghana", "GHA"
    ))
    exports = [r for r in rows if r["indicator_code"] == "exports"]
    assert len(exports) == 2
    assert {r["current_currency"] for r in exports} == {"GHS"}


def test_indonesia_debt_coreference_keeps_debt_indicator_and_relative_year():
    rows = run_multi_agent(_doc(
        "La dette publique représentait 39,2 % du PIB en 2024. "
        "Deux ans auparavant, elle était de 39,7 %.", "Indonésie", "IDN"
    ))
    vals = {(r["current_year"], r["current_value"], r["indicator_code"]) for r in rows}
    assert (2024, 39.2, "public_debt_ratio") in vals
    assert (2022, 39.7, "public_debt_ratio") in vals


def test_generic_body_table_parses_inflation_average_unemployment_debt_without_reserves():
    text = (
        "[[PAGE 1]]\nBulletin économique - Chili. Toutes les valeurs du tableau principal concernent le Chili. "
        "Annee Inflation moyenne (%) Chomage (%) Dette publique (% PIB) "
        "2021 4,5 8,9 36,3 2022 11,6 7,9 38,0 2023 7,6 8,7 39,4 2024 4,3 8,5 41,2"
    )
    rows = run_multi_agent(_doc(text, "Chili", "CHL"))
    table = [r for r in rows if r.get("table_source") == "body_table"]
    assert len(table) == 12
    assert {(r["current_year"], r["indicator_code"]) for r in table} >= {
        (2024, "inflation_annual_average"), (2024, "unemployment_rate"), (2024, "public_debt_ratio")
    }
    assert all(r["country_iso3"] == "CHL" for r in table)


def test_annex_still_excluded_after_generic_table_generalization(tmp_path):
    # This is a direct upstream guard: annex headings remain stop sections.
    from app.services.content_selector import is_structural_page
    assert is_structural_page("Annexe statistique\nAnnee Inflation (%) Chomage (%)\n2024 9,9 8,8")
    assert is_structural_page("Appendix A\nYear Inflation (%) Unemployment (%)\n2024 9.9 8.8")

def test_relative_period_variants_do_not_reuse_stale_granularity():
    rows = run_multi_agent(_doc(
        "En Turquie, l'inflation etait de 44,4 % en decembre 2024. Un mois auparavant, elle atteignait 47,1 %. "
        "Le taux de chomage s'est etabli a 8,5 % au quatrieme trimestre 2024, contre 8,7 % au trimestre precedent.",
        "Turquie", "TUR"
    ))
    by_val={round(float(r['current_value']),1):r for r in rows}
    assert (by_val[44.4]['current_year'],by_val[44.4]['current_month'])==(2024,12)
    assert (by_val[47.1]['current_year'],by_val[47.1]['current_month'])==(2024,11)
    assert (by_val[8.5]['current_year'],by_val[8.5]['current_quarter'],by_val[8.5]['current_month'])==(2024,4,None)
    assert (by_val[8.7]['current_year'],by_val[8.7]['current_quarter'],by_val[8.7]['current_month'])==(2024,3,None)


def test_current_account_deficit_is_negative_balance():
    rows = run_multi_agent(_doc(
        "Le deficit du compte courant a represente 0,8 % du PIB en 2024, alors qu'il atteignait 3,5 % du PIB en 2023.",
        "Turquie", "TUR"
    ))
    vals=sorted((r['current_year'],r['current_value']) for r in rows if r['indicator_code']=='current_account_balance')
    assert vals==[(2023,-3.5),(2024,-0.8)]


def test_korea_two_year_and_six_month_variants_use_discourse_anchor():
    rows = run_multi_agent(_doc(
        "En 2024, la croissance du PIB a atteint 2,0 %. L'annee precedente, elle etait de 1,4 %. Deux annees auparavant, elle s'etablissait a 2,7 %. "
        "Le taux de chomage etait de 3,1 % au troisieme trimestre 2025. Au trimestre precedent, il atteignait 2,8 %. Six mois plus tot, il etait de 3,0 %.",
        "Coree du Sud", "KOR"
    ))
    growth={(r['current_year'],r['current_value']) for r in rows if r['indicator_code']=='gdp_growth'}
    unemp={(r['current_year'],r['current_quarter'],r['current_value']) for r in rows if r['indicator_code']=='unemployment_rate'}
    assert (2022,2.7) in growth
    assert (2025,1,3.0) in unemp


def test_preliminary_estimate_coreference_is_kept_as_estimate():
    rows=run_multi_agent(_doc(
        "Le rapport annuel indique une inflation de 3,1 % en 2024. Une estimation preliminaire mentionnait toutefois 3,6 % pour 2024.",
        "Norvege", "NOR"
    ))
    est=[r for r in rows if round(float(r['current_value']),1)==3.6]
    assert est and est[0]['fact_type']=='estimate' and est[0]['indicator_code']=='inflation_rate'


def test_us_dollar_alias_is_dynamic_currency():
    assert detect_currency("155,2 milliards de dollars US", "TUR") == "USD"

def test_year_on_year_price_increase_does_not_inherit_annual_average_subtype():
    rows = run_multi_agent(_doc(
        "L'inflation moyenne s'est etablie a 4,7 % en 2024. En decembre 2024, la hausse des prix sur douze mois etait de 4,2 %.",
        "Mexique", "MEX"
    ))
    event=[r for r in rows if round(float(r['current_value']),1)==4.2][0]
    assert event['indicator_code']=='inflation_rate'
    assert (event['current_year'],event['current_month'])==(2024,12)
