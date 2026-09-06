# EcoLingua-TN v4.6 — Observation Type & Explainable Validation

## Scope
This release does not replace the extraction engine. It adds a business-facing distinction between observed, estimated and forecast values, and makes internal confidence auditable.

## Changes
- Atomic observation nature: `observed`, `estimate`, `forecast`.
- Local modal-scope detection so a forecast value and its historical comparison in the same sentence are classified independently.
- Added French estimate markers: estimation, estimé(e), provisoire, préliminaire.
- Fixed target-year resolution for constructions such as `En Tunisie, pour 2025, ...`.
- Confidence now records explicit evidence and warnings instead of exposing an unexplained fixed score.
- Evidence distinguishes explicit vs contextual indicator, period, unit/currency and country.
- Dashboard shows `Nature` as Observé / Estimé / Prévision.
- Traceability panel explains confidence evidence and explicitly states that confidence is not model accuracy.
- Added four v4.6 regression tests.

## Reproducible checks
- `pytest -q`: 30 passed.
- Fixed 14-event gold benchmark: 14 predictions, 14 TP, 0 FP, 0 FN; Precision/Recall/F1/Exact Match = 1.0 on this regression benchmark only.
- Observation-type accuracy on the fixed 14-event gold benchmark = 1.0.
- Synthetic 41-page stress document: 500 extracted events; 470 observed, 20 forecast, 10 estimate; 0 unit/currency `nan` rows.
- Confidence on the stress document uses 8 distinct score values in this run rather than the earlier nearly fixed 80/92/97 buckets. Note: repeated contradictory synthetic observations are intentionally capped and sent to review.

## Interpretation warning
The 100% values above apply only to the fixed 14-event regression set. They are not a claim of general extraction performance. A larger real-document gold corpus is required for CV-grade generalization metrics.
