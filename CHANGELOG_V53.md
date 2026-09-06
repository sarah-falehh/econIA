# Changelog v5.3

- Added geometry-preserving PDF table ingestion and dedicated structured-table event generation.
- Added multi-level header, wide, long, matrix, sector-block and continued-table support.
- Prevented detectable tables and chart-axis sequences from entering the narrative extractor.
- Added complete numerical coverage tracing and clause reconciliation.
- Added sector, geography type, period range and table-provenance fields.
- Added PECO/economic-group support without fabricating countries.
- Added official French labels for competitiveness, exchange, labour-market and monetary indicators.
- Corrected semantic binding for food prices, wages, productivity, purchasing power, TMM/real TMM and bilateral/effective exchange rates.
- Corrected explicit 2015 exchange-rate scope and protected it from stale TMM context.
- Corrected GDP negation and constrained “activity” coreference.
- Added 16 generalized v5.3 tests; final suite is 185/185.
- Added reproducible PDF validation exports and v5.3 benchmark results.
