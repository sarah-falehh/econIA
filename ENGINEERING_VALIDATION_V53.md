# EcoLingua-TN v5.3 — engineering validation

## Release position

This is a materially improved deterministic/CPU-oriented release. It is **not** described as universally reliable for every PDF. The only frozen independent GOLD set currently contains 14 events; it is useful for regression protection but is not representative enough to support a universal claim.

## Reproducible environment and baseline

- Python: 3.12.13, Linux x86_64 (validation host).
- Dependencies installed from `requirements.txt`, including PyMuPDF, pycountry, Babel and pytest.
- Unmodified v5.2 baseline after dependency installation: **169 passed, 0 failed**.
- Final v5.3 suite: **185 passed, 0 failed, 0 skipped in 33.70 s**.
- No existing test was deleted or weakened.

## Root causes and generalized corrections

| Root cause | General correction | Regression protection |
|---|---|---|
| Detectable PDF tables were flattened into narrative text | Geometry-backed neutral table grids; table bounding boxes excluded from narrative reconstruction; dedicated semantic table parser | Wide, long, matrix, multi-header, sector and range tests |
| One-dimensional event schema caused sector values to collide | Added sector, geography type, range-period and table provenance dimensions to technical events and deduplication keys | Sector × indicator × period tests |
| “growth” over-selected GDP | Explicit semantic heads for food prices, wages, productivity, purchasing power, CSU, competitor prices and competitiveness | Competitiveness semantic tests |
| Stale indicator/country/date context contaminated later clauses | Heading boundaries, constrained coreferences, forward-only section geography and explicit-series precedence | TMM→exchange reset, pronoun and group tests |
| Ranges were collapsed to their last year | First-class `period_type`, `period_start`, `period_end`, `frequency` and resolution source | Average/range and paired-range tests |
| Country groups were fabricated as Tunisia | Economic-group geography type and ordered “respectively” binding | PECO / Asian competitors / Tunisia test |
| Shared units and coordinated values lost the first value | Clause-level shared-unit and coordinated-sibling binding | Range, bilateral exchange and multi-value tests |
| Numeric omissions were silent | Numerical coverage trace with extracted/excluded/unresolved outcome and reason | Unexplained-number test |
| Chart ticks became observations | Axis-sequence exclusion and unresolved-chart policy | Chart-axis regression test |
| Internal indicator codes leaked to users | Official French labels retained separately from stable internal codes | Readable-label export test |
| Negated GDP phrasing and “activity” coreference were missed in pasted text | GDP negation support plus narrow GDP→activity continuity | Four-event pasted-text test |

## End-to-end results

| Input | Events | Structured-table events | Sector events | Validated | Needs review | Rejected | Numeric mentions | Unresolved | Runtime |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Competitiveness report PDF | 372 | 333 | 250 | 354 | 17 | 1 | 437 | 33 | 26.917 s |
| Synthetic complex PDF | 156 | 65 | 0 | 84 | 69 | 3 | 261 | 17 | 13.268 s |
| Generated CSV (first 20 of 96 rows) | 36 | — | — | — | — | — | — | — | 4.584 s |
| Representative pasted text | 4 | — | — | — | — | — | 4 economic values | 0 | 0.453 s |

The competitiveness checks now bind:

- 10.3% depreciation and 7.6% appreciation to bilateral exchange-rate change, both in 2015;
- 7.57% (Q1 2019) and 4.86% (2017) to nominal TMM;
- 0.52% (2016) to real TMM, marked Needs review because context is inherited;
- 0.6% to labour productivity rather than GDP;
- the 23–80% cost range to a cost concept marked Needs review, never to exchange rates;
- PECO, Asian competitors and Tunisia as three distinct geographic entities;
- 333 structured table cells, including 250 sector-dimension events.

## Frozen GOLD regression benchmark

Dataset: `evaluation/datasets/gold_dataset.csv`, manually verified and frozen before v5.3 evaluation.

- GOLD events: 14; predictions: 14.
- TP 14, FP 0, FN 0.
- Precision 1.000; Recall 1.000; F1 1.000.
- Event Exact Match 1.000, including fact type.
- Indicator, value, unit, period, geography and fact-type accuracy: 1.000.
- Runtime: 1.739 s; peak RSS reported by the host: 26,400 KiB.

These figures describe only this small regression GOLD. Precision/Recall/F1 for the complete real report are **not calculated**, because complete independent manual annotation is not yet available.

## Numerical coverage policy

Each candidate numeric token receives a trace record containing page, clause, raw token, evidence, structure, outcome, linked event hint and reason. Remaining unresolved entries are exported rather than silently discarded. Period tokens, table structure, chart ticks and other layout/noise categories are excluded with a reason.

## Known limitations

1. The competitiveness PDF still has 33 unresolved numeric mentions and the synthetic PDF 17. They require manual audit/annotation before a complete real-report recall figure can be claimed.
2. Charts whose data cannot be reconstructed reliably from text and geometry remain unresolved structured blocks; no values are fabricated.
3. Scanned/image-only PDFs require OCR, which is not bundled in this CPU-light release.
4. Very irregular or visually merged tables can remain unresolved; the raw table audit is preserved.
5. Publication/revision version is traceable in evidence and conflicts, but full versioned-series analytics remains incomplete.
6. The 14-event GOLD is a regression corpus, not a representative holdout. A larger development/regression/holdout annotation campaign is still required.

## Reproduction

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python evaluation/evaluate.py --version v5.3 --output evaluation/results/v5.3.json
python evaluation/validate_v53_documents.py path/to/report.pdf path/to/synthetic.pdf
```

On Windows, run `run_windows.bat` after installing Python 3.11+; it creates/uses the application environment and starts Streamlit.
