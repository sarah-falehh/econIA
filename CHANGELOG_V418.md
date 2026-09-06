# EcoLingua-TN v4.18 — Deterministic Coreference Validation

## Fixed
- Extended deterministic contextual validation to French imperfect forms such as `atteignait/atteignaient`.
- Recognizes short nominal coreference patterns such as `ce ratio était de ...` when the indicator resolver has already supplied a unique compatible antecedent.
- Explicit `ambiguous_context` now forces `À vérifier`; a strong verb can no longer accidentally validate a genuinely ambiguous inherited indicator.

## Preserved
- Missing country remains `À vérifier`.
- Conflicts remain `À vérifier`.
- Annex exclusion, clause-aware binding, multi-country binding, forecast typing, series construction and exports are unchanged.
- Validation thresholds were not lowered globally.

## Tests
- Added regressions for `il atteignait`, `ce ratio était`, `elles atteignaient`, and an ambiguous-pronoun counterexample.
- Full suite: 101 passed.

## Scope
This release targets the three unnecessary contextual reviews identified during the v4.17 audit. It is a regression release, not a new claim of general model accuracy.
