from app.services.multi_agent_pipeline import run_multi_agent


def extract(text):
    return run_multi_agent({'document_id':'v45','text':text,'language':'fr','country':'Tunisie','source':'benchmark'})


def test_primary_balance_inherits_percent_of_gdp():
    rows = extract("Le solde budgétaire primaire s’est établi à -1,7 % du PIB en 2021. Il s’est amélioré à -0,8 % l’année suivante.")
    got = {(r['current_year'], r['current_value'], r['current_unit']) for r in rows if r['indicator_code']=='primary_balance'}
    assert (2021, -1.7, '% du PIB') in got
    assert (2022, -0.8, '% du PIB') in got


def test_public_debt_ratio_keeps_semantic_unit_in_coreference():
    rows = extract("La dette publique représentait 63,8 % du PIB en 2021. L’année précédente, ce ratio était de 62,5 %.")
    got = {(r['current_year'], r['current_value'], r['current_unit']) for r in rows if r['indicator_code']=='public_debt_ratio'}
    assert (2021, 63.8, '% du PIB') in got
    assert (2020, 62.5, '% du PIB') in got


def test_no_percent_of_gdp_leak_to_inflation():
    rows = extract("La dette publique représentait 63,8 % du PIB en 2021. En 2022, le taux d’inflation a atteint 7,2 %.")
    inflation = [r for r in rows if r['indicator_code']=='inflation_rate']
    assert inflation and inflation[0]['current_unit'] == '%'


def test_monetary_debt_coreference_stays_stock_not_ratio():
    rows = extract("La dette publique s’élevait à 94,2 milliards de dinars, soit 67,5 % du PIB en 2021. Elle atteindrait 98,7 milliards de dinars en 2022, tandis que le ratio serait estimé à 66,8 % du PIB.")
    monetary = [r for r in rows if r['current_value'] == 98.7]
    ratio = [r for r in rows if r['current_value'] == 66.8]
    assert monetary and monetary[0]['indicator_code'] == 'public_debt_stock'
    assert ratio and ratio[0]['indicator_code'] == 'public_debt_ratio'
    assert ratio[0]['current_unit'] == '% du PIB'
