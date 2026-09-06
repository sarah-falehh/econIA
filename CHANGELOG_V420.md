# EcoLingua-TN v4.20 — Structured Table Evidence & Frequency-Aware Indicators

## Added
- Structured-table evidence is now an explicit validation signal.
- GDP growth nomenclature distinguishes annual from quarterly variation when the source period is quarterly.
- Regression tests for table evidence, annual/quarterly GDP naming, and `ressortait` contextual relations.

## Changed
- `explicit_table` indicator/unit/period evidence is treated as explicit evidence rather than inherited evidence.
- Strong economic predicate detection includes `ressort/ressortait`.

## Safety
- No global confidence threshold was lowered.
- Missing country, conflict, ambiguous context and critical unit mismatch rules remain unchanged.
- Annex exclusion remains unchanged.
- Forecast/estimate logic remains unchanged.

## Tests
- 111 tests pass on the complete suite.

## Benchmark policy
Gold v2 has already been inspected and is a regression corpus. v4.20 results on it must not be reported as blind generalization performance. A new untouched Gold v3 is required for CV/generalization metrics.
