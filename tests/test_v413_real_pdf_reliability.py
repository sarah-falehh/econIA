from app.services.context_resolver import DocumentContext
from app.services.multi_agent_pipeline import _extract_observations, run_multi_agent


def test_old_month_does_not_refine_later_annual_debt_values():
    s=("La révolution tunisienne du 14 janvier 2011 a entraîné une hausse de la dette. "
       "Le stock de la dette publique a enregistré 36.616 MD en 2013, soit 47,2% du PIB et un montant prévu "
       "de 41.754 MD en 2014, soit 49,1% du PIB.")
    obs=_extract_observations(s, context=DocumentContext(anchor_year=2013,current_year=2013))
    relevant=[o for o in obs if o['value'] in {36616.0,47.2,41754.0,49.1}]
    assert relevant
    assert all(o['month'] is None for o in relevant)
    assert {o['period_label'] for o in relevant} == {'2013','2014'}


def test_range_from_to_recomputes_period_labels():
    s=("Entre 2001 et 2010 une baisse du taux d’endettement public a été enregistrée "
       "passant de 56,47% à seulement 40,4%.")
    obs=_extract_observations(s, context=DocumentContext(anchor_year=2013,current_year=2013))
    vals={o['value']:o for o in obs}
    assert vals[56.47]['year'] == 2001
    assert vals[56.47]['period_label'] == '2001'
    assert vals[40.4]['year'] == 2010
    assert vals[40.4]['period_label'] == '2010'


def test_state_debt_share_is_not_percent_of_gdp():
    s=("La part de la dette publique dans la dette de l’État est passée de 27% en 1986 "
       "à 39,26% en 2000.")
    obs=_extract_observations(s, context=DocumentContext(anchor_year=2000,current_year=2000))
    shares=[o for o in obs if o['code']=='public_debt_state_share']
    assert len(shares)==2
    assert all(o['unit']=='%' for o in shares)


def test_real_document_conflict_same_series_period_is_preserved():
    doc={
        'document_id':'conflict-test','text':(
            'En 1986, le taux d’endettement public a atteint 52,22% du PIB. '
            'Selon un autre passage, le taux d’endettement public est passé de 57,22% en 1986 à 56,07% en 2000.'
        ),'country':'Tunisie','source':'Source test','language':'fr'
    }
    rows=run_multi_agent(doc)
    y1986=[r for r in rows if r['indicator_code']=='public_debt_ratio' and r['current_year']==1986]
    assert {round(r['current_value'],2) for r in y1986} == {52.22,57.22}
    assert all(r['conflict_status'] for r in y1986)
    assert all(r['validation_status']=='À vérifier' for r in y1986)


def test_annex_tables_are_excluded_by_product_rule():
    text='[[PAGE 31]]\nAnnexe 2 : Evolution de la dette publique Encours de la dette (MDT) EDPI EDPE (% de l’EDP) (% du PIB)\n1986 4109,3 1109,4 2999,9 27,0 73,0 14,1 38,1 52,2\n1987 4473,4 1257,4 3216,0 28,1 71,9 14,2 36,4 50,6\nSource : Ministère des finances'
    rows=run_multi_agent({'document_id':'annex','text':text,'country':'Tunisie','source':'Ministère des finances','language':'fr'})
    assert rows == []


def test_rounding_difference_is_not_a_conflict_but_real_difference_is():
    doc={'document_id':'rounding','country':'Tunisie','source':'Ministère des finances','language':'fr','text':(
        'En 1986, le taux d’endettement public a atteint 52,22% du PIB. '
        'Le tableau récapitulatif indique 52,2% en 1986. '
        'Une autre source indique un taux d’endettement public de 57,22% en 1986.'
    )}
    rows=run_multi_agent(doc)
    vals={round(r['current_value'],2):r for r in rows if r['indicator_code']=='public_debt_ratio'}
    assert vals[52.22]['conflict_status'] is True  # genuine 57.22 contradiction still affects group
    assert vals[57.22]['conflict_status'] is True


def test_rounding_only_group_is_not_conflict():
    doc={'document_id':'rounding-only','country':'Tunisie','source':'Ministère des finances','language':'fr','text':(
        'En 2012, le taux d’endettement public a atteint 46,15% du PIB. '
        'Le taux d’endettement public était de 46,2% en 2012.'
    )}
    rows=run_multi_agent(doc)
    relevant=[r for r in rows if r['indicator_code']=='public_debt_ratio' and r['current_year']==2012]
    assert len(relevant)==2
    assert not any(r['conflict_status'] for r in relevant)


def test_source_metadata_spillover_is_shortened():
    from app.services.multi_agent_pipeline import _context
    ctx=_context({'source':'Ministère des finances Le taux d’endettement public de la Tunisie est passé de 52,2%','filename':'rapport.pdf'}, [])
    assert ctx['source']=='Ministère des finances'
