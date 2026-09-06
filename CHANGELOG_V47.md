# EcoLingua-TN v4.7 — Evidence-Based Validation & Professional UX

## Added
- Centralized evidence-based validation in `app/services/evidence_validation.py`.
- Business statuses: `Validé`, `À vérifier`, `Rejeté`.
- Explicit `conflict_status` and event-level `observation_type`.
- Evidence/warning lists that explain the confidence score.
- Observation filters by country, indicator, type, status, confidence and conflicts.
- Professional green/amber/red validation language across the UI.
- Type-aware charts: historical/estimated points and dashed forecasts.
- Export fields `Type`, `Confiance`, `Statut`.
- `evaluation/datasets/regression_gold.csv` and `evaluation/datasets/real_gold/` scaffold.
- 14 v4.7-specific automated tests.

## Changed
- Confidence is an evidence-quality triage score, not an accuracy estimate.
- Critical unit incompatibilities override a high score and can produce `Rejeté`.
- Conflicts always force `À vérifier`.
- Review observations remain in time series; rejected observations are excluded.
- Historical statistics use observed, non-rejected points by default and do not silently mix forecasts.
- Dashboard cards now separate `Validées` and `À vérifier`.

## Fixed
- Forecast/observed status is retained in series and exports.
- Duplicate observations are not treated as conflicts.
- Validation status is persisted in the business fact schema.
- Existing `nan` unit protections and econometric-noise rejection remain intact.

## Benchmarks
### Regression gold (14 events)
- Precision: 100%
- Recall: 100%
- F1: 100%
- Event exact match: 100%
- Observation type accuracy: 100%

These figures apply only to the fixed 14-event regression benchmark and are not a general performance claim.

### Synthetic 41-page stress test
- 500 extracted events
- 112 Validé
- 383 À vérifier
- 5 Rejeté
- 470 Observé / 10 Estimé / 20 Prévision
- 0 `nan` units
- 0 econometric false positives detected by the stress-test checks
- 60 foreign-exchange reserve events
- 10 primary-balance events
- Engine-only runtime in the test environment: ~0.44 s (PDF reading/UI excluded)

The synthetic document deliberately contains repeated conflicting country/indicator/period combinations, so conflict counts must not be interpreted as an error rate.

## Known limitations
- The confidence score is deterministic evidence triage and is not calibrated as a probability.
- General Precision/Recall/F1 still require a larger real manually annotated corpus.
- The synthetic stress-test is useful for regression but cannot replace evaluation on real reports.
