# EcoLingua-TN v4.5 — Semantic Series Consistency

## Objective
Prevent semantically identical economic series from being split because a coreferential sentence uses a shortened unit (for example `%` after `% du PIB`).

## Changes
- Inherit `% du PIB` only when the immediately preceding event has the same indicator and semantic unit.
- Canonicalize public/internal/external debt ratios to `% du PIB`.
- Preserve ordinary `%` for indicators such as inflation; no cross-indicator unit leakage.
- Monetary public-debt coreferences are forced to `public_debt_stock`, never a debt ratio.
- Updated percentage-role logic so `% du PIB` observations remain eligible for internal/external/public debt role disambiguation.
- Added four regression tests covering semantic-unit inheritance and monetary debt coreference.

## Reproducible checks
- `pytest -q`: 26 passed.
- Fixed 14-event benchmark: Precision 1.0, Recall 1.0, F1 1.0, Event Exact Match 1.0.
- Synthetic 41-page stress corpus: 500 extracted events, 0 `nan` units/currencies, 0 public-debt-ratio events with a non-`% du PIB` unit.
- Extraction-engine runtime observed in the test environment: about 0.24 s for the already-extracted text of the 41-page synthetic corpus. This excludes PDF reading and Streamlit rendering and is not a full end-to-end PDF latency benchmark.

## Methodological note
The 100% score applies only to the fixed 14-event regression benchmark. The 41-page corpus is currently a stress/regression corpus, not a fully manually annotated gold corpus, so no global Precision/Recall/F1 is claimed for it.
