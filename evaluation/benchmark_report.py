from __future__ import annotations
import json, sys
from pathlib import Path

def pct(v): return f"{100*v:.2f}%"
def main(paths):
    rows=[json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]
    for r in rows:
        print(f"{r['version']}: P={pct(r['precision'])} R={pct(r['recall'])} F1={pct(r['f1'])} Exact={pct(r['event_exact_match'])} time={r['processing_seconds']:.4f}s")
    if len(rows)>=2:
        a,b=rows[-2],rows[-1]; d=b['f1']-a['f1']; rel=d/a['f1'] if a['f1'] else None
        print(f"F1 gain: {d*100:+.2f} percentage points" + (f" ({rel*100:+.2f}% relative)" if rel is not None else ""))
if __name__=='__main__': main(sys.argv[1:])
