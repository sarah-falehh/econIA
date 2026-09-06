# EcoLingua-TN v4.19 — Gold v2 Generalization Fixes

## Fixed
- Compact one-page economic PDFs are no longer rejected solely because they are shorter than 900 characters.
- Inline prose containing the plural word "annexes" no longer truncates the report body; actual Annex/Appendix headings remain excluded.
- Added Senegal and Portugal country/demonym normalization, plus plural Spanish/Italian demonyms.
- Added FCFA/XOF currency recognition.
- Country context can be recovered from document title/body metadata for body tables.
- Multi-country value binding no longer lets a demonym in the following clause steal the previous value.
- Sentence-initial year/context propagation covers coordinated and immediately following indicator clauses.
- Comparative binding now resolves "A en 2024 après B l'année précédente" as 2024 / 2023 instead of using a stale document year.
- Added GDP wording via "produit intérieur brut" and previous-quarter wording via "trois mois auparavant".
- Body macro tables with Inflation / Chômage / Dette columns are supported without requiring a reserves column.

## Tests
- 107 tests passed.

## Methodology
Gold Corpus v2 run #1 remains the frozen v4.18 baseline. After its errors were inspected, this corpus became a regression/development corpus for v4.19 and must not be reported as an independent held-out v4.19 score. A new unseen Gold v3 is required for a generalization claim.
