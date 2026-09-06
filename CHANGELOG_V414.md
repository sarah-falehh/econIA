# EcoLingua-TN v4.14 — Structured Evidence Validation

## Added
- Eight-dimensional validation profile: indicator, value, unit, period, country, association, semantic compatibility, context.
- Deterministic-association evidence independent of a single confidence threshold.
- Chapter-scoped contradiction analysis for documents explicitly composed of independent `Chapitre NN — Conjoncture économique` articles.
- `exports_growth` and `imports_growth` economic concepts so percentage variations are not rejected as monetary levels.
- v4.14 non-regression tests.

## Changed
- Validation status is no longer decided by `confidence >= threshold` alone.
- Critical semantic/unit errors and genuine conflicts still override high confidence.
- Context inheritance is scored separately from explicit evidence.

## Measured stress-test comparison
Same 40-page synthetic PDF:
- v4.13: 500 events; 147 Validé; 348 À vérifier; 5 Rejeté.
- v4.14: 500 events; 360 Validé; 140 À vérifier; 0 Rejeté.
- Validated share: 29.4% -> 72.0% (+42.6 percentage points).
- Review share: 69.6% -> 28.0% (-41.6 percentage points).
- Rejected export-growth observations: 5 -> 0 after correct ontology mapping.
- Event count unchanged: 500 -> 500.
- Econometric noise remains 0; missing source remains 0; NaN unit tokens remain 0.

These status changes are triage improvements, NOT accuracy/precision/F1 claims.

## Regression benchmark
The fixed 14-event regression gold remains 14/14 exact match (Precision/Recall/F1 1.0). This small benchmark is not a general performance estimate.
