from app.services.multi_agent_pipeline import _sentences, _candidate_sentences, _extract_observations
from app.services.context_resolver import DocumentContext

def test_country_heading_updates_next_sentence_context_without_joining_backward():
    text = """Les réserves atteignaient 49,1 milliards USD fin 2024.
Thaïlande - conjoncture et perspectives
Le PIB a progressé de 2,5 % en 2024."""
    parts = _sentences(text)
    assert "Thaïlande" not in parts[0]
    candidates = _candidate_sentences(text)
    thailand = [x for x in candidates if "2,5 %" in x["text"]][0]
    assert thailand["section_country"] == "Thaïlande"
    assert thailand["section_country_iso3"] == "THA"

def test_quarter_scope_does_not_leak_to_prior_values():
    ctx=DocumentContext(anchor_year=2024,current_year=2024,discourse_year=2024)
    sentence="En 2024, le Portugal a enregistré une croissance de 1,9 %, une inflation moyenne de 2,6 % et un chômage de 6,4 % au quatrième trimestre."
    obs=_extract_observations(sentence, context=ctx)
    by={round(float(o["value"]),1):o for o in obs}
    assert by[1.9]["quarter"] is None
    assert by[2.6]["quarter"] is None
    assert by[6.4]["quarter"] == 4

def test_reserve_absolute_change_is_not_emitted_as_level_and_initial_level_is_recovered():
    ctx=DocumentContext(anchor_year=2024,current_year=2024,discourse_year=2024,last_country="Thaïlande",last_country_iso3="THA")
    sentence="En Thaïlande, les réserves de change ont augmenté de 3,7 milliards USD entre fin décembre 2024 et fin mars 2025, passant de 237,4 à 241,1 milliards USD."
    obs=_extract_observations(sentence, context=ctx)
    vals=sorted(round(float(o["value"]),1) for o in obs if o["code"]=="foreign_exchange_reserves")
    assert vals == [237.4,241.1]
    periods={(round(float(o["value"]),1),o.get("year"),o.get("month")) for o in obs if o["code"]=="foreign_exchange_reserves"}
    assert (237.4,2024,12) in periods
    assert (241.1,2025,3) in periods
