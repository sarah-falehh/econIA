# EcoLingua-TN v4.15 — Clause-Aware Semantic Binding

## Added
- Local country-value binding inside multi-country sentences.
- Demonym support (tunisien(ne)(s), marocain(e)(s), algérien(ne)(s), égyptien(ne)(s), etc.).
- Coordinated-clause period propagation when a period is uniquely inherited.
- Conditional forecast detection (`serait`, `atteindrait`, `s’élèverait`, etc.).
- Contextual FDI level recovery after a previous FDI growth sentence.
- Strict body-table parser for high-confidence macro tables.
- Canonical monetary duplicate normalization across million/billion scale equivalents.
- Regression tests for Excel export with all-NaN/empty columns.

## Changed
- Annex/Appendix content is now excluded by product rule, even when it contains useful macro tables.
- Report-body tables remain eligible when they match a strong economic schema.
- Local explicit country evidence now overrides sentence/document context.
- Coreferential values bind to the previous indicator before later clause indicators are considered.
- `same period` now inherits the active period safely.
- Negative change verbs on growth indicators are stored with a negative signed value.

## Fixed
- `ValueError: cannot convert float NaN to integer` in Excel column-width calculation.
- `16.0 %` unemployment being reassigned to activity rate by a later clause.
- Regional forecast lists assigning all values to Tunisia.
- `marocaines`/other demonyms not being recognized as country evidence.
- `serait` and related conditionals being classified as observed.
- Missing year propagation in coordinated clauses.
- FDI stock values after `Leur niveau...` being misclassified as FDI growth.
- `Entre 2020 et 2024 ... de A à B` period pairing.
- Equivalent monetary values expressed in million vs billion not being deduplicated.

## Verification
- 95 automated tests passed.
- 500-event legacy stress test preserved: 360 Validé / 140 À vérifier, 0 `nan` units.
- Real ITCEQ PDF: annexes excluded by new product rule; narrative extraction remains stable.
- Heldout-v1 regression suite (now a regression suite after error-driven tuning): 116/116 exact events recovered.

## Methodological note
The 100% heldout-v1 result must **not** be presented as a generalization score because those documents were inspected and used to drive v4.15 fixes. A fresh unseen heldout-v2 corpus is required for a defensible generalization metric.
