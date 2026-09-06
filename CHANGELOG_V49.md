# EcoLingua-TN v4.9 — Canonical Unit Serialization

## Fixed
- Removed the pandas `NaN` truthiness bug in the canonical user-facing unit serializer.
- `current_unit`, `current_scale`, and `current_currency` are now normalized through one missing-value-safe helper before labels are built.
- Monetary labels now render as `milliard TND`, `milliard MAD`, `milliard DZD`, `milliard EGP` instead of `milliard nan`.
- Ratio labels remain `% du PIB` instead of `nan % du PIB`.
- Rate labels remain `%` instead of `nan %`.
- `observations.csv` and `series.csv` now share the same safe measurement-label builder.
- The legacy immediate workspace table now delegates to the same canonical `observations_export` serializer, removing UI/export drift.

## Regression tests
- Added integration-level tests using actual pandas `NaN` values, not only `None`.
- Added coverage for percentage, `% du PIB`, and monetary currency/scale labels.
- Added series-export regression coverage.
- 49 automated tests pass.

## Fixed regression benchmark
- 14 gold events / 14 predictions.
- Precision = 100%, Recall = 100%, F1 = 100%, Event Exact Match = 100%, Observation Type Accuracy = 100% on the small fixed regression benchmark only.
- No extraction-quality improvement is claimed from this serializer fix.

## Stress-export replay
Using the same 500-event v4.8 technical stress output as input to the corrected canonical serializer:
- 500 observations serialized.
- `nan` in observation-unit labels: 500 -> 0.
- `nan` in series-unit labels: 0 after correction.
- Statuses preserved: 150 Validé / 345 À vérifier / 5 Rejeté.
- Types preserved: 470 Observé / 20 Prévision / 10 Estimé.
- Unit distribution after correction: 205 `%`, 95 `% du PIB`, 52 `milliard TND`, 52 `milliard MAD`, 49 `milliard DZD`, 47 `milliard EGP`.

## Root cause
`float('nan')` is truthy in Python. Expressions such as:

```python
row.get("current_unit") or row.get("current_currency")
```

therefore selected a pandas/NumPy NaN value before the valid currency fallback. The fix explicitly normalizes missing values before choosing the semantic unit/currency.
