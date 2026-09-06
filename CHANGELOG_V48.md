# EcoLingua-TN v4.8 — Conflict Semantics & Export Integrity

## Fixed
- Conflict grouping now includes the observation nature (`observed`, `estimate`, `forecast`).
- An observed value and a forecast for the same country/indicator/period/unit are no longer treated as contradictory solely because their values differ.
- Exact-deduplication also respects observation type.
- The main workspace export now uses the canonical business schema from `observations_export`.
- `Rejeté` is no longer collapsed into `À vérifier` in `tableau_economique.csv`.
- `Type` is now present in the main user-facing table and CSV export.
- Main workspace filters include observation Type.
- Validation colors are consistent in the immediate post-analysis table: green Validé, amber À vérifier, red Rejeté; observation type uses separate neutral/violet/cobalt semantics.
- Dashboard cards no longer present mean confidence as a quality KPI; they show Validées and À vérifier counts instead.

## Tests
- 47 automated tests pass (44 in v4.7 + 3 v4.8 regression tests).
- Fixed 14-event regression gold remains 14/14 exact, Precision/Recall/F1 = 100% on that small fixed regression benchmark only.

## Synthetic stress test
- 41-page synthetic PDF: 500 events, unchanged extraction volume.
- Observation types: 470 observed / 20 forecast / 10 estimate.
- Conflicts: 383 in v4.7 -> 345 in v4.8 after separating epistemic type (-38 rows, -9.9%).
- Statuses in v4.8: 150 Validé / 345 À vérifier / 5 Rejeté.
- User export preserves all three statuses and all three observation types.
- `nan` units: 0.

## Interpretation
The remaining 345 conflict-marked rows on the synthetic stress PDF are not assumed to be false positives: the synthetic document deliberately repeats several same country/indicator/period series with different values across chapters. A real hand-annotated conflict gold set is required before reporting conflict precision/recall.
