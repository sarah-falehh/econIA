from __future__ import annotations

import argparse
from io import BytesIO
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.multi_agent_pipeline import get_last_trace, run_multi_agent
from app.services.pdf_reader import read_pdf
from app.services.series_analytics import auditable_observations_export


def validate_pdf(path: Path, output_dir: Path) -> dict:
    start = time.perf_counter()
    documents = read_pdf(BytesIO(path.read_bytes()), source=path.name)
    rows: list[dict] = []
    coverage: list[dict] = []
    table_audit: list[dict] = []
    for document in documents:
        rows.extend(run_multi_agent(document.to_dict()))
        trace = get_last_trace()
        coverage.extend(trace.get("numerical_coverage", []))
        table_audit.extend(trace.get("structured_table_audit", []))
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    technical = pd.DataFrame(rows)
    technical.to_csv(output_dir / f"{stem}_technical.csv", index=False, encoding="utf-8-sig")
    auditable_observations_export(technical).to_csv(
        output_dir / f"{stem}_business.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(coverage).to_csv(output_dir / f"{stem}_numerical_coverage.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(table_audit).to_csv(output_dir / f"{stem}_table_audit.csv", index=False, encoding="utf-8-sig")
    statuses = technical.get("validation_status", pd.Series(dtype=str)).value_counts().to_dict()
    return {
        "document": path.name,
        "events": len(rows),
        "table_events": int(technical.get("table_source", pd.Series(dtype=object)).notna().sum()),
        "sector_events": int(technical.get("sector", pd.Series(dtype=object)).notna().sum()),
        "validated": int(statuses.get("Validé", 0)),
        "needs_review": int(statuses.get("À vérifier", 0)),
        "rejected": int(statuses.get("Rejeté", 0)),
        "numeric_mentions": len(coverage),
        "unresolved_numeric_mentions": sum(item.get("outcome") == "unresolved" for item in coverage),
        "runtime_seconds": round(time.perf_counter() - start, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("validation_outputs/v53"))
    args = parser.parse_args()
    results = [validate_pdf(path, args.output_dir) for path in args.pdf]
    (args.output_dir / "run_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
