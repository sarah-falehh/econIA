# EcoLingua-TN v4.23

## Added
- Stable Temporal Anchor Graph (`discourse_year`, `discourse_quarter`, `discourse_month`).
- Automatic multi-document gold-corpus evaluator: `evaluation/evaluate_corpus.py`.
- Month-aware strict matching in `evaluation/matcher.py`.
- Regression tests for sibling year and quarter relations.

## Fixed
- `2024 → année d'avant → deux ans plus tôt` now resolves to `2024 → 2023 → 2022`.
- `Q2 → trimestre précédent → trois mois plus tard` now resolves to `Q2 → Q1 → Q3`, rather than chaining from Q1.

## Tests
- `pytest -q`: 119 passed, 0 failed.

## Benchmark policy
- No new generalization metric is claimed from Gold v3 because its failures informed v4.23.
- Future blind corpora must be scored before any rule modification.
