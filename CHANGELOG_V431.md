# EcoLingua-TN v4.31 — Consolidated Stable Baseline

## Fixed
- Six-month relative quarter references now resolve from the primary explicit quarter anchor (Q4 -> Q2), not from a sibling relative value.
- Same-sentence explicit annual anchors now dominate stale document context for expressions such as "deux ans auparavant".
- Country changes inside semicolon-delimited comparison clauses remain authoritative for all coordinated values in that clause.
- Generic `respectivement` alignment maps the second country's values to the indicator sequence introduced in the first clause.
- Overlapping indicator mentions are collapsed toward the most specific concept (e.g. annual-average inflation).
- GDP labels are derived from the atomic event frequency, preventing a quarter elsewhere in the sentence from relabelling an annual GDP observation.
- All v4.30 and earlier fixes remain covered by regression tests.

## Verification
- Full automated suite: 149 passed, 0 failed.
- Exact complex 6-page stress PDF re-run in a fresh Python process:
  - 89 extracted observations
  - 54 Validé / 28 À vérifier / 7 Rejeté
  - 0 missing countries
  - 0 annex observations from 2032-2035
  - 0 econometric-noise rows
- Verified target cases:
  - Portugal unemployment: 2024-Q4 6.4, 2024-Q3 6.6, 2024-Q2 6.8
  - Portugal current account: 2022 -1.2%, 2024 -0.4%
  - Thailand reserves: 237.4bn USD 2024-M12, 241.1bn USD 2025-M03
  - Multi-country `respectivement`: values remain bound to Poland, not Portugal
  - Annual Portugal GDP in the mixed-frequency sentence remains annual
