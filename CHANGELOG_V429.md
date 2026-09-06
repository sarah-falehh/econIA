# EcoLingua-TN v4.29 — Series Safety Hotfix

## Fixed
- Fixed `KeyError: ['Valeur affichée', 'Évolution absolue', 'Évolution %', 'Sens'] not in index` in the analysis workspace.
- Rejected observations no longer create time-series selector entries or feed series/statistics/graphs.
- `build_indicator_series()` now guarantees a stable derived-column schema even when validation filtering leaves an empty series.
- Workspace expanders skip empty series and use safe `reindex` instead of fragile hard column indexing.
- Numeric formatting is now tolerant of optional/missing derived values.

## Preserved
- v4.27 extraction engine and section-boundary stabilization.
- v4.28 Analyst Workspace exports and comparison features.
- Dynamic country/currency registries, temporal resolution, table parsing, conflicts, annex filtering and econometric-noise protection.

## Validation
- Full suite: 141 passed, 0 failed.
- Two new regression tests cover rejected-only and empty-series schemas.
