from __future__ import annotations
from pathlib import Path
import io, sys, pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from app.services.pdf_reader import read_pdf
from app.services.csv_reader import load_csv_dataframe, dataframe_to_documents_auto
from app.services.multi_agent_pipeline import run_multi_agent

EVAL_DIR=Path(__file__).resolve().parent
class NamedBytes(io.BytesIO):
    def __init__(self,data:bytes,name:str): super().__init__(data); self.name=name
    def getvalue(self): return super().getvalue()

def run_pdf():
    p=EVAL_DIR/'datasets'/'stress_test_40_pages.pdf'; f=NamedBytes(p.read_bytes(),p.name)
    rows=[]
    for d in read_pdf(f): rows += run_multi_agent(d.to_dict())
    df=pd.DataFrame(rows); labels=df['current_period_label'].fillna('').astype(str)
    return {
        'events':len(df), 'm12':int(labels.str.endswith('-M12').sum()),
        'missing_source':int((df['source'].fillna('').astype(str).str.strip()=='').sum()),
        'nan_unit_tokens':int(df.apply(lambda r:'nan' in ' '.join(str(r.get(c) or '') for c in ['current_unit','current_scale','current_currency']).lower(),axis=1).sum()),
        'econometric_noise':int(df['sentence'].str.contains(r'coefficient|p-value|R²|statistique t|erreur standard|F-statistic',case=False,regex=True,na=False).sum()),
    }

def run_multisource():
    p=EVAL_DIR/'datasets'/'multisource_articles_test.csv'; f=NamedBytes(p.read_bytes(),p.name)
    raw=load_csv_dataframe(f); docs,_=dataframe_to_documents_auto(raw,filename=p.name)
    rows=[]
    for d in docs: rows += run_multi_agent(d.to_dict())
    df=pd.DataFrame(rows)
    return {'events':len(df),'missing_country':int(df['country'].isna().sum()),'document_ids':int(df['document_id'].nunique())}

if __name__=='__main__':
    print({'pdf':run_pdf(),'multisource':run_multisource()})
