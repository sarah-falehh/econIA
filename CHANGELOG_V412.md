# EcoLingua-TN v4.12 — Consolidated Reliability

## Purpose
v4.12 is a consolidation release. It fixes regressions without sacrificing previously corrected behavior and adds cross-input non-regression locks for both the multi-source CSV and the large synthetic PDF.

## Fixed
- Temporal granularity precedence: explicit sentence period > relative period > context > document metadata fallback.
- Removed stale month propagation that turned annual/quarterly events into December (`M12`).
- Preserved month granularity for strong expressions such as `un an auparavant` after a monthly event.
- Added `cette même année` / `la même année` context resolution.
- Added `projetait` / `projetaient` to event-local forecast scope.
- Preserved quarter granularity for `même période de l'année précédente`.
- Split IMF-style annual-average inflation and end-of-period inflation into distinct indicators.
- PDF source falls back to the imported filename when no institution/source is embedded.
- CSV business IDs (`id`, `document_id`, etc.) are preserved as stable document IDs.
- Added trade balance, trade coverage ratio, and monthly CPI change as first-class indicators.
- Trade deficits are normalized as signed trade balances while retaining the source sentence.
- Article-title/document year can safely anchor a primary comparison value when only the historical reference year is written in the sentence.

## Regression locks
- 75 automated tests pass.
- Large PDF: 500 events; 60 `M12` periods; 0 missing sources; 0 `nan` unit tokens; 0 econometric false positives in the targeted noise pages.
- Multi-source CSV: country metadata remains complete; document IDs are stable; known forecast/period cases are covered by tests.

## Measured comparison with v4.11 (same environment/input)
- Stress PDF events: 505 → 500 (restores the pre-regression event count).
- `M12` labels: 493 → 60 (-87.8%); the remaining 60 are the December reserves/current + one-year-earlier monthly observations in this synthetic corpus.
- Missing PDF source: 505 → 0.
- Automated tests: 60 → 75 (+15).

No general accuracy/F1 claim is made from these counts. Real-world F1 requires a matching source corpus and frozen gold annotations.
