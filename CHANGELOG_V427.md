# EcoLingua-TN v4.27 — Section Boundary Stabilization

## Fixed
- Preserve PDF visual line boundaries instead of flattening every page into one string.
- Treat short country/section headings as hard extraction boundaries.
- Prevent a country mention belonging to the next section from retroactively changing the previous event.
- Update inherited country context only from an event actually bound by the extractor.
- Keep all v4.26 country, currency, temporal, table, conflict, annex and econometric protections.

## Regression
- Full suite: 139 passed, 0 failed.
- Large 10-page stress PDF: 271 extracted events.
- Foreign-exchange-reserve sequence is now bound to the intended 14 countries in document order.
- No annex/econometric extraction regression observed in the smoke run.

## Important
Validation status is not an accuracy metric. This release is a stabilization/regression release, not a new blind benchmark.
