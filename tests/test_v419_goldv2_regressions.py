from pathlib import Path
from app.services.pdf_reader import read_pdf
from app.services.indicator_registry import detect_country
from app.services.multi_agent_pipeline import _unit_fields, _extract_observations
from app.services.context_resolver import DocumentContext

class Upload:
    def __init__(self, path):
        self.path = Path(path); self.name = self.path.name
    def getvalue(self):
        return self.path.read_bytes()

def test_short_economic_pdf_is_not_rejected_as_front_matter(tmp_path):
    # Regression is covered structurally: a compact economic first page must not
    # be classified as front matter solely because it is <900 characters.
    import app.services.pdf_reader as pr
    text = "Dossier de cohérence - Algérie Inflation 5,4 % en 2024. Dette publique 48,1 % du PIB en 2024."
    assert not pr._looks_front_matter(text, 1)

def test_inline_word_annexes_does_not_truncate_body():
    import app.services.pdf_reader as pr
    text = "Rapport - exclusion stricte des annexes. En 2024, inflation 7,2 %."
    assert pr._truncate_inline_annex(text) == text

def test_new_country_ontology():
    assert detect_country("Au Sénégal, la croissance progresse.")[1] == "SEN"
    assert detect_country("les exportations portugaises progressent")[1] == "PRT"
    assert detect_country("les exportations espagnoles progressent")[1] == "ESP"

def test_fcfa_normalizes_to_xof():
    assert _unit_fields("5 420 milliards de francs CFA")[2] == "XOF"

def test_comparison_year_binding_after_previous_year():
    c = DocumentContext(); c.current_year = 2024; c.document_year = 2019
    obs = _extract_observations("Les importations ont atteint 612,4 milliards de dirhams en 2024 après 584,1 milliards l'année précédente.", context=c)
    assert [(o['value'], o['year']) for o in obs] == [(612.4, 2024), (584.1, 2023)]

def test_previous_sentence_year_propagates_to_explicit_indicators():
    c = DocumentContext(); c.current_year = 2020
    obs = _extract_observations("Le taux de chômage a atteint 11,9 % et la dette publique représentait 72,2 % du PIB.", context=c)
    assert {o['year'] for o in obs} == {2020}
