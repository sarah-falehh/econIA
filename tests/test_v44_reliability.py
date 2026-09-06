from app.services.multi_agent_pipeline import run_multi_agent


def extract(text):
    return run_multi_agent({'document_id':'v44','text':text,'language':'fr','country':'Tunisie','source':'benchmark'})


def test_official_reserves_and_previous_year():
    rows=extract("Les réserves officielles de change ont atteint 25,4 milliards de dinars en décembre 2024. Un an auparavant, elles s’élevaient à 23,1 milliards de dinars.")
    vals={(r['indicator_code'],r['current_year'],r['current_value']) for r in rows}
    assert ('foreign_exchange_reserves',2024,25.4) in vals
    assert ('foreign_exchange_reserves',2023,23.1) in vals


def test_primary_budget_balance():
    rows=extract("Le solde budgétaire primaire s’est établi à -1,7 % du PIB en 2023. Il s’est amélioré à -0,8 % l’année suivante.")
    vals={(r['indicator_code'],r['current_year'],r['current_value']) for r in rows}
    assert ('primary_balance',2023,-1.7) in vals
    assert ('primary_balance',2024,-0.8) in vals


def test_currency_normalization_for_magreb_and_egypt():
    cases=[('Maroc','12,4 milliards de dirhams en 2024','MAD'),('Algérie','12,4 milliards de dinars algériens en 2024','DZD'),('Égypte','12,4 milliards de livres égyptiennes en 2024','EGP')]
    for country, amount, code in cases:
        rows=run_multi_agent({'document_id':'v44','text':f"Au {country}, les exportations ont atteint {amount}.",'language':'fr','country':country,'source':'benchmark'})
        assert rows and rows[0]['current_currency']==code


