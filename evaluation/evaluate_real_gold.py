from __future__ import annotations
import argparse, json, re, unicodedata
from pathlib import Path
import pandas as pd

ALIASES = {
    "exportations de biens": "exportations de biens et services",
    "importations de biens": "importations de biens et services",
    "taux d'inflation des prix a la consommation - alimentation": "taux d'inflation des produits alimentaires",
}
COUNTRY = {"tun":"tunisie", "tunisia":"tunisie"}

def nt(x):
    if x is None or (isinstance(x,float) and pd.isna(x)): return ""
    s=unicodedata.normalize("NFKD",str(x)).encode("ascii","ignore").decode().lower().replace("’","'")
    return re.sub(r"\s+"," ",s).strip()

def indicator(x):
    s=nt(x); return ALIASES.get(s,s)

def country(x):
    s=nt(x); return COUNTRY.get(s,s)

def unit_gold(x):
    s=nt(x).replace("millions","million").replace("milliards","milliard")
    return s

def unit_pred(r):
    parts=[]
    if pd.notna(r.get("current_scale")): parts.append(nt(r.get("current_scale")).replace("millions","million").replace("milliards","milliard"))
    if pd.notna(r.get("current_currency")): parts.append(str(r.get("current_currency")).lower())
    if pd.notna(r.get("current_unit")): parts.append(nt(r.get("current_unit")))
    return " ".join(parts).strip()

def key_gold(r, include_type=True):
    base=(country(r['country']),indicator(r['indicator']),round(float(r['value']),6),unit_gold(r['unit']),str(r['period']))
    return base+(nt(r['observation_type']),) if include_type else base

def key_pred(r, include_type=True):
    base=(country(r['country']),indicator(r['indicator']),round(float(r['current_value']),6),unit_pred(r),str(r['current_period_label']))
    return base+(nt(r.get('observation_type') or r.get('fact_type')),) if include_type else base

def evaluate(gold,pred):
    # Restrict predictions to documents represented in gold when IDs are available.
    docs=set(gold['document_id'].astype(str))
    if 'document_id' in pred and pred['document_id'].astype(str).isin(docs).any():
        pred=pred[pred['document_id'].astype(str).isin(docs)].copy()
    gs=[key_gold(r) for _,r in gold.iterrows()]
    ps=[key_pred(r) for _,r in pred.iterrows()]
    remaining=list(range(len(ps))); tp=0
    for g in gs:
        hit=next((i for i in remaining if ps[i]==g),None)
        if hit is not None:
            tp+=1; remaining.remove(hit)
    fp=len(ps)-tp; fn=len(gs)-tp
    precision=tp/len(ps) if ps else 0.0; recall=tp/len(gs) if gs else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    return {"gold_events":len(gs),"predicted_events":len(ps),"tp":tp,"fp":fp,"fn":fn,"precision":precision,"recall":recall,"f1":f1,"exact_match":tp/len(gs) if gs else 0.0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--gold',required=True); ap.add_argument('--predictions',required=True); ap.add_argument('--out')
    a=ap.parse_args(); res=evaluate(pd.read_csv(a.gold),pd.read_csv(a.predictions)); print(json.dumps(res,ensure_ascii=False,indent=2))
    if a.out: Path(a.out).write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
