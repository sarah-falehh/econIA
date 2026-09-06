# EcoLingua-TN v4.11 — Clause-Aware Economic Event Builder

## Added
- Canonical `activity_rate`, `current_account_balance`, and `fdi_growth` indicators.
- Event-local modal scope for observed / forecast / estimate classification.
- Value-local cumulative periods (`H1`, `M01:M07`, etc.).
- Publication-title month as a safe document-level temporal anchor.
- Monetary comparison currency propagation within one series.

## Fixed
- `Taux d’activité` no longer inherits `Taux de chômage` from the preceding sentence.
- `projette` / `projections` now mark only the values in their modal scope as forecasts.
- Current-account balance and FDI variation in coordinated clauses become separate events.
- A later explicit month no longer leaks backward to a preceding value.
- Current vs previous quarter is resolved for a newly introduced indicator when the current quarter is available from document context.

## Regression evidence
- pytest: 60 passed.
- Fixed 14-event regression gold: Precision/Recall/F1/Exact Match/Type Accuracy remain 1.0.
- Multi-source corpus: 46 events, 0 missing country; observed/forecast/estimate = 36/9/1; 43 Validé, 3 À vérifier.

## Limitations
- The 14-event gold is a regression set, not a general performance estimate.
- Real-corpus Precision/Recall/F1 still require an independently frozen, sufficiently large gold corpus.
