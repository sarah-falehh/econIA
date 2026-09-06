# EcoLingua-TN v4.17 — Safe Context Resolution & Bulk Review

## Added
- Safe-context validation signal for unique local pronoun/relative references (`il`, `elle`, `elles`, `ce ratio`, `un an auparavant`, prospective conditionals).
- Review Desk cause summary: missing country, conflict, context/other.
- Bulk human country assignment for a batch of missing-country observations, with explicit human evidence and session audit decision.
- Regression tests for safe contextual inheritance and mandatory review when country is absent.

## Changed
- `missing_country` is now a review-critical warning: an otherwise complete event cannot be auto-validated without a country.
- Safe contextual inheritance raises association/context dimensions only when indicator, value, unit, period and country are present and semantic compatibility is not violated.
- Existing contextual warnings remain visible for auditability even when the event can be validated.

## Safety / reliability
- No validation threshold was lowered.
- Conflicts still force `À vérifier`.
- Critical unit mismatch and suspicious sections still force rejection.
- Human bulk assignment never guesses a country automatically; the user must explicitly choose it.

## Tests
- 97 passed.
