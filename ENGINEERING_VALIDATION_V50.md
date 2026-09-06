# EcoLingua-TN v5.0 — Generalized Event Architecture

## Engineering objective
v5.0 does not optimize for one PDF. The semantic core is format-agnostic and is shared by PDF, CSV and pasted/manual text.

## Architectural changes
1. Normalize input into text blocks/documents.
2. Segment into independent atomic economic clauses before binding values.
3. Bind each measurement to local explicit indicator/country/period evidence first.
4. Use document/discourse context only as fallback.
5. Resolve relative periods with reusable arithmetic primitives (year/month/quarter offsets).
6. Preserve comparison clauses such as `from A to B`, `contre`, and `respectivement`.
7. Split independent coordinated indicator/value pairs such as revenue / expenditure / deficit.
8. Keep absolute local dates as the highest temporal authority.

## Regression coverage
- Full suite: 163 passed, 0 failed.
- Includes legacy regression tests plus v5 tests for:
  - PDF/CSV/manual semantic parity
  - independent multi-indicator clauses
  - local debt vs prior FDI context
  - budget deficit vs prior inflation context
  - 1..12 month relative offsets
  - relative month vs later historical date
  - previous-year sibling anchoring
  - public revenue / expenditure / deficit separation

## End-to-end complex PDF stress test
- 96 extracted observations
- 74 Validé / 20 À vérifier / 2 Rejeté
- 0 missing country
- 0 annex 2032–2035 observations
- 0 econometric-noise observations
- Verified repaired classes:
  - Malaysian central-government debt: 62.9% (2023), 64.1% (2024)
  - Malaysian inflation: Jan-2025 1.7%, Mar-2025 1.9%
  - Thailand inflation: Nov-2024 0.9%, Dec-2023 -0.8%
  - Senegal public revenue and expenditure remain separate indicators

## Important
Passing regression tests is not a claim of universal 100% extraction accuracy.
Unknown real-world layouts and language constructions must still be measured on held-out corpora.
