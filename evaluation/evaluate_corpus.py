"""Evaluate exported EcoLingua observations against a manually annotated gold CSV.

Gold columns: document_id,country,indicator,value,unit,year,quarter,month,observation_type
Prediction files may be technical exports (preferred) or user CSVs with French columns.
No gold row is ever edited by this script.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from evaluation.matcher import evaluate


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def adapt_user_row(r):
    period=(r.get("Période") or r.get("Periode") or "").strip()
    year=quarter=month=None
    import re
    ym=re.fullmatch(r"(19\d{2}|20\d{2})-M(0?[1-9]|1[0-2])", period)
    yq=re.fullmatch(r"(19\d{2}|20\d{2})-Q([1-4])", period)
    yy=re.fullmatch(r"(19\d{2}|20\d{2})", period)
    if ym: year,month=int(ym.group(1)),int(ym.group(2))
    elif yq: year,quarter=int(yq.group(1)),int(yq.group(2))
    elif yy: year=int(yy.group(1))
    val=str(r.get("Valeur") or r.get("value") or "").replace(" ","").replace(",",".")
    m=re.search(r"[-+]?\d+(?:\.\d+)?", val)
    return {"country":r.get("Pays") or r.get("country"), "indicator":r.get("Indicateur") or r.get("indicator"),
            "current_value":float(m.group()) if m else None, "current_unit":r.get("Unité") or r.get("Unite") or r.get("unit"),
            "current_scale":None,"current_currency":None,"current_year":year,"current_quarter":quarter,"current_month":month,
            "fact_type":r.get("Type") or r.get("observation_type"), "needs_review":str(r.get("Statut") or "").lower().find("vérifier")>=0}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--gold",required=True,type=Path); ap.add_argument("--pred-dir",required=True,type=Path); ap.add_argument("--output",type=Path); ap.add_argument("--version",default="unknown")
    a=ap.parse_args(); gold=read_csv(a.gold)
    docs=sorted({r.get("document_id","") for r in gold}); all_pred=[]; per_doc={}
    for doc in docs:
        files=sorted(a.pred_dir.glob(f"{doc}*.csv"))
        if not files: per_doc[doc]={"error":"prediction file missing"}; continue
        raw=read_csv(files[0]); pred=[r if "current_value" in r else adapt_user_row(r) for r in raw]
        g=[r for r in gold if r.get("document_id")==doc]; per_doc[doc]=evaluate(g,pred); all_pred.extend(pred)
    overall=evaluate(gold,all_pred); result={"version":a.version,"gold_file":str(a.gold),"documents":len(docs),"overall":overall,"per_document":per_doc}
    target=a.output or Path(f"evaluation/results/{a.version}_corpus.json"); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
