from app.services.multi_agent_pipeline import _extract_observations
from app.services.context_resolver import DocumentContext

def _ctx(country="Portugal", iso="PRT", year=2024, quarter=None):
    c=DocumentContext(anchor_year=year,current_year=year,current_quarter=quarter,
                      discourse_year=year,discourse_quarter=quarter,
                      last_country=country,last_country_iso3=iso)
    return c

def test_six_months_earlier_uses_primary_q4_anchor_not_relative_q3():
    c=_ctx(quarter=4)
    c.last_indicators=[("unemployment_rate","Taux de chômage")]
    s="Le chômage s'est établi à 6,4 % au quatrième trimestre 2024, contre 6,6 % au trimestre précédent et 6,8 % six mois plus tôt."
    obs=_extract_observations(s,context=c)
    by={round(float(o["value"]),1):o for o in obs}
    assert (by[6.4]["year"],by[6.4]["quarter"])==(2024,4)
    assert (by[6.6]["year"],by[6.6]["quarter"])==(2024,3)
    assert (by[6.8]["year"],by[6.8]["quarter"])==(2024,2)

def test_explicit_year_after_value_beats_sibling_relative_phrase():
    c=_ctx()
    c.last_indicators=[("current_account_balance","Solde du compte courant")]
    s="Le déficit du compte courant, qui représentait 1,2 % du PIB deux ans auparavant, a été ramené à 0,4 % en 2024."
    obs=_extract_observations(s,context=c)
    by={round(abs(float(o["value"])),1):o for o in obs}
    assert by[1.2]["year"]==2022
    assert by[0.4]["year"]==2024

def test_country_change_after_semicolon_persists_for_coordinated_values():
    c=_ctx()
    s="En 2024, le Portugal a enregistré une croissance de 1,9 %, une inflation moyenne de 2,6 % et un chômage de 6,4 % au quatrième trimestre ; la Pologne affichait respectivement 2,9 %, 3,7 % et 3,1 % pour le chômage au deuxième trimestre 2025."
    obs=_extract_observations(s,context=c)
    pol=[o for o in obs if round(float(o["value"]),1) in {2.9,3.7,3.1}]
    assert pol
    assert all(o["country_iso3"]=="POL" for o in pol)


def test_same_sentence_2024_anchor_drives_two_years_earlier():
    c=_ctx(year=2025)
    c.discourse_year=2025
    c.last_indicators=[("current_account_balance","Solde du compte courant")]
    s="Le déficit du compte courant, qui représentait 1,2 % du PIB deux ans auparavant, a été ramené à 0,4 % en 2024."
    obs=_extract_observations(s,context=c)
    by={round(abs(float(o["value"])),1):o for o in obs}
    assert by[1.2]["year"]==2022
    assert by[0.4]["year"]==2024

def test_respectively_maps_same_indicator_sequence_to_second_country():
    c=_ctx()
    s="En 2024, le Portugal a enregistré une croissance de 1,9 %, une inflation moyenne de 2,6 % et un chômage de 6,4 % au quatrième trimestre ; la Pologne affichait respectivement 2,9 %, 3,7 % et 3,1 % pour le chômage au deuxième trimestre 2025."
    obs=_extract_observations(s,context=c)
    by={round(float(o["value"]),1):o for o in obs if o.get("country_iso3")=="POL"}
    assert by[2.9]["code"]=="gdp_growth"
    assert by[2.9]["year"]==2024 and by[2.9]["quarter"] is None
    assert by[3.7]["code"]=="inflation_annual_average"
    assert by[3.7]["year"]==2024 and by[3.7]["quarter"] is None
    assert by[3.1]["code"]=="unemployment_rate"
    assert by[3.1]["year"]==2025 and by[3.1]["quarter"]==2
