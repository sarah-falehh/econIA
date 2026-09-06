# EcoLingua-TN v5.5 — Engineering validation

## Scope

This release hardens general extraction families revealed by the synthetic
multi-country corpus and the Tunisian competitiveness report. It is not a
claim of universal PDF reliability. A representative independent holdout GOLD
corpus is still required before such a claim could be supported.

## Baseline and regression protection

- Baseline before the v5.5 changes: 185/185 tests passed.
- Final complete suite: 193 collected, 193 passed, 0 failed, 0 skipped.
- Runtime: 35.51 seconds (Python 3.12.13, Linux x86_64).
- Existing tests were not deleted or weakened.

## Root causes corrected

1. Structured-table row geography was overwritten by document geography.
   Row-local geography now has priority and groups retain their geography type.
2. The user export discarded sector, partner, period provenance and table
   evidence. The auditable export now preserves these fields and readable
   French indicator labels.
3. Month binding in coordinated policy-rate sequences used a remote month.
   Each value now uses its local following month.
4. Specific inflation concepts collided with generic inflation. Overlapping
   generic mentions are removed and explicit subject scope is respected.
5. Context continuation was too narrow for bounded GDP pronouns and
   year-on-year inflation coreferences. The resolver now permits these only
   with a compatible preceding series and local economic predicate.
6. Forecast nouns and scenario verbs were inconsistently scoped. Local
   `prévisions`, `prévoit` and `retient` now classify the associated value,
   while a remote heading containing “prévisions” cannot flip an observation.
7. Generic bilateral exchange-rate change could eclipse TCER/TCEN. The
   explicit effective-rate series now wins.
8. Negative GDP contractions, “respectively” year alignment and structured
   sector dimensions received permanent generalized regression tests.

## End-to-end document runs

| Document | Events | Table events | Sector events | Validated | Needs review | Rejected | Numeric mentions | Unresolved | Runtime |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Competitiveness report | 377 | 333 | 250 | 352 | 24 | 1 | 437 | 28 | 27.742 s |
| Synthetic complex PDF | 170 | 65 | 0 | 144 | 22 | 4 | 272 | 9 | 14.905 s |

The synthetic run now preserves all three Argentina year-on-year inflation
values (211.4, 117.8 and 82.1), the complete Thai policy-rate sequence, both
Senegal GDP forecasts (8.4 and 6.7), and multi-country table row geography.

The competitiveness run now extracts 333 structured table cells, including
250 sector-dimensional events. Core inflation 5.4/7.4 is no longer exported as
headline inflation, and the report's aggregate 7.6 TCER change is no longer
relabelled as a generic bilateral change.

## GOLD benchmark

The bundled small regression GOLD contains 14 manually defined events:
TP=14, FP=0, FN=0, precision=1.0, recall=1.0, F1=1.0 and exact match=1.0.
This measures only that small regression set and must not be presented as a
representative real-report quality score.

## Known limitations

- 28 and 9 numerical mentions respectively remain unresolved. They are present
  in the numerical coverage CSV with evidence and exclusion/review outcome;
  they do not disappear silently.
- Some narrative continuation periods in the competitiveness report remain
  ambiguous (notably prose that continues a multi-year average without
  repeating its range). Structured table counterparts retain the proper range.
- Partner/counterpart extraction for every bilateral exchange-rate phrasing is
  incomplete.
- Chart curves are not digitized. Axis ticks are excluded; unresolved charts
  require review/OCR rather than fabricated events.
- The existing GOLD dataset is too small and not a final independent holdout.
  No universal “all PDFs” reliability claim is justified yet.

## Reproducibility

```bash
python -m pytest -q
python evaluation/evaluate.py --version v5.5 --output evaluation/results/v5.5.json
python evaluation/validate_v53_documents.py PDF1 PDF2 --output-dir validation_outputs/v55
```
