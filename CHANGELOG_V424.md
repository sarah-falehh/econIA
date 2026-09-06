# EcoLingua-TN v4.24 — Dynamic Country Registry

## Problem fixed
The country detector was based on a small hand-written dictionary. Any new country not explicitly listed could become `None`, even when the country name was clearly present in the document.

## Architecture change
- Added `app/services/country_registry.py`.
- Country names are now built dynamically from ISO-3166 (`pycountry`) and Babel territory labels.
- French, English and Arabic country names are indexed automatically.
- ISO3 codes are accepted as document metadata, but are **not** searched in free text to avoid false matches such as `EST`, `FIN`, and `SUR`.
- Demonyms are maintained as a separate extensible alias layer instead of being mixed with ISO country names.
- `indicator_registry`, `multi_agent_pipeline`, and the legacy extractor now use the same country registry.

## Gold v4 smoke test
All seven Gold-v4 documents resolve their document country without a missing country:
- Mexico → MEX
- Turkey → TUR
- Indonesia → IDN
- Chile → CHL
- Norway → NOR
- Ghana → GHA
- South Korea → KOR

The smoke test also checked countries not used to develop the feature (Argentina, Thailand, Malaysia).

## Safety / non-regression
- Free-text false positives caused by ISO3 codes were explicitly prevented.
- Existing multi-country local value binding remains active.
- Existing country metadata fallback remains active.
- Full test suite: **123 passed**.

## Important limitation
Demonyms are linguistic, not part of ISO-3166. Country *names* are now dynamic; rare demonyms may still require aliases. When a document title or metadata contains the country name, the dynamic registry provides the country context without requiring a demonym rule.
