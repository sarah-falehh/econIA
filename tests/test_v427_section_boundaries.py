from app.services.multi_agent_pipeline import _sentences, _country_for_measure, _MEASURE
from app.services.context_resolver import DocumentContext

def test_heading_is_hard_boundary():
    text = "Les réserves officielles de change s'élevaient à 44,4 milliards USD à fin décembre 2024.\nMexique — situation macroéconomique\nEn 2024, la croissance du PIB s'est établie à 1,5 %."
    parts = _sentences(text)
    assert any("44,4" in p and "Mexique" not in p for p in parts)
    assert any("1,5" in p for p in parts)

def test_trailing_new_country_cannot_steal_prior_measure():
    sentence = "Les réserves officielles de change du Canada s'élevaient à 44,4 milliards USD à fin décembre 2024."
    m = next(m for m in _MEASURE.finditer(sentence) if "44,4" in m.group(0))
    country, iso3, source = _country_for_measure(sentence, m.start(), m.end(), "Mexique")
    assert iso3 == "CAN"

def test_visual_heading_without_period_is_not_joined_backward():
    text = "Les réserves atteignaient 63,2 milliards USD en 2024.\nCorée du Sud\nEn 2025, la croissance devrait atteindre 2,2 %."
    parts = _sentences(text)
    assert "Corée du Sud" not in parts[0]
