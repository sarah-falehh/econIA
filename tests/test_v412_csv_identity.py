import pandas as pd
from app.services.csv_reader import dataframe_to_documents_auto


def test_csv_business_id_is_preserved_as_document_id():
    df=pd.DataFrame([{
        'id':'INS_TEST_001','titre':'Test','source':'INS','date':'2025-01-01','pays':'Tunisie',
        'texte':'En 2025, le taux de chômage atteint 15,2 %.','url':'https://example.org'
    }])
    docs,schema=dataframe_to_documents_auto(df, filename='input.csv')
    assert schema.id_column=='id'
    assert docs[0].document_id=='INS_TEST_001'
