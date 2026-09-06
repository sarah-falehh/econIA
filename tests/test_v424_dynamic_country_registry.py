from app.services.country_registry import detect_country
from app.services.multi_agent_pipeline import _country_for_measure


def test_gold_v4_country_names_are_dynamic():
    cases = {
        'Au Mexique, la croissance atteint 2,1 %.': ('Mexique','MEX'),
        'En Turquie, le déficit recule.': ('Turquie','TUR'),
        'En Indonésie, l inflation ralentit.': ('Indonésie','IDN'),
        'Au Chili, le chômage baisse.': ('Chili','CHL'),
        'En Norvège, la dette reste faible.': ('Norvège','NOR'),
        'Au Ghana, les exportations progressent.': ('Ghana','GHA'),
        'En Corée du Sud, le PIB augmente.': ('Corée du Sud','KOR'),
    }
    for text, expected in cases.items():
        assert detect_country(text) == expected


def test_country_names_not_added_per_benchmark():
    # These countries were never in the old hand-written registry.
    assert detect_country('En Argentine, le PIB progresse.') == ('Argentine','ARG')
    assert detect_country('La croissance en Thaïlande atteint 3 %.') == ('Thaïlande','THA')
    assert detect_country('Economic activity in Malaysia improved.') == ('Malaisie','MYS')


def test_demonyms_are_bound_locally():
    sentence = 'Les exportations mexicaines ont progressé de 4,2 % en 2024.'
    start = sentence.index('4,2')
    country, iso3, source = _country_for_measure(sentence, start, start+3, None)
    assert (country, iso3) == ('Mexique','MEX')
    assert source.startswith('explicit')


def test_document_fallback_accepts_iso3_and_display_name():
    assert detect_country('', 'MEX') == ('Mexique','MEX')
    assert detect_country('', 'Ghana') == ('Ghana','GHA')
