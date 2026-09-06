from __future__ import annotations

import argparse, csv, json, os, platform, resource, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from app.services.multi_agent_pipeline import run_multi_agent
from evaluation.matcher import evaluate


def read_gold(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def run(version: str, output: Path | None = None) -> dict:
    text=(ROOT/"evaluation/datasets/benchmark_v1.txt").read_text(encoding="utf-8")
    gold=read_gold(ROOT/"evaluation/datasets/gold_dataset.csv")
    doc={"document_id":"benchmark_v1","text":text,"source":"benchmark interne","language":"fr","title":"Benchmark v1"}
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0=time.perf_counter(); predicted=run_multi_agent(doc); elapsed=time.perf_counter()-t0
    after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    metrics=evaluate(gold,predicted)
    metrics.update({"version":version,"processing_seconds":elapsed,"events_per_second":len(predicted)/elapsed if elapsed else None,
                    "peak_rss_kb":max(before,after),"python":platform.python_version(),"platform":platform.platform()})
    target=output or ROOT/f"evaluation/results/{version}.json"; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf-8")
    return metrics

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--version",default="v4.2"); ap.add_argument("--output",type=Path)
    args=ap.parse_args(); result=run(args.version,args.output)
    print(json.dumps(result,ensure_ascii=False,indent=2))
