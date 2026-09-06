# EcoLingua-TN v4.25 — Consolidated Generalization Engine

## Goal
Consolidate all previous reliability fixes while removing the remaining hard-coded country/currency/table assumptions exposed by Gold v4.

## Added
- `app/services/currency_registry.py`: dynamic ISO-4217/CLDR currency registry.
- Country-to-current-currency resolution through CLDR territory currency history.
- Generic body-table schema detection based on economic column semantics instead of country-specific layouts.
- Regression coverage for unseen currencies, semantic continuity, relative periods, conflict-safe estimates and generic tables.

## Changed
- Monetary extraction no longer depends on a fixed TND/MAD/DZD/... list.
- Generic currency denominations (peso, dinar, shilling, rupee, krone, cedi, won, yen, real, etc.) are disambiguated from document country.
- Explicit ISO currency codes remain supported without turning ordinary words such as TRY into false currency matches.
- Currency detection now uses a compact measurement regex plus dynamic local resolution, avoiding a giant CLDR regex on every sentence.
- Structured body-table extraction now supports variable macroeconomic column subsets and remains disabled for Annex/Appendix sections.
- Relative temporal vocabulary extended: `trimestre d'avant`, `un mois auparavant`, `deux années auparavant`, `six mois plus tôt`.
- Explicit quarter/month granularity overrides stale contextual month/quarter state.
- Current-account deficits are normalized as negative balances while budget-deficit conventions remain unchanged.
- Headline year-on-year inflation no longer inherits the `annual average` subtype from a previous sentence.
- Legacy `economic_extractor.py` now uses the shared dynamic currency detector for explicit currency names.

## Preserved / Non-regression
- Dynamic ISO country registry.
- Multi-event stock + ratio extraction.
- Clause-aware indicator/value binding.
- Multi-country local binding.
- Annual/monthly/quarterly period separation.
- Temporal Anchor Graph.
- Observed / Estimated / Forecast event-level classification.
- `nan`-safe unit serialization.
- Conflict vs duplicate vs rounding-equivalent semantics.
- Annex/Appendix exclusion.
- Econometric noise filtering.
- Safe-context validation and missing-country review guard.
- Review Desk / Intelligence Workspace behavior.
- Excel export NaN-safety.

## Verification
- `pytest -q`: 134 passed, 0 failed.
- Gold v4 regression corpus after fixes: 94 predicted events for 94 gold events; strict canonical event matching 94 TP / 0 FP / 0 FN.
- Important: Gold v4 has been used for development and is therefore a regression corpus, not a blind generalization score for CV claims.

## Known limitations
- Long-document end-to-end throughput still needs a dedicated performance benchmark independent of correctness tests.
- Rare demonyms and ambiguous currency common nouns may still require linguistic aliases; standard country names and ISO currencies are dynamic.
