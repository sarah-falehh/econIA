# EcoLingua-TN v4.21 — Generalization Hardening

## Baseline
v4.20 Gold-v3 first run is preserved as the blind baseline. Gold v3 is now a regression corpus and must not be reported as a new blind score after these fixes.

## Added
- Country/demonym coverage for Canada, Kenya, Poland, Czech Republic, Hungary, South Africa, Japan, Brazil and New Zealand.
- Currency recognition/normalization for KES, JPY, BRL, NZD, CAD and ZAR, while preserving USD/XOF/TND/MAD/DZD/EGP/EUR.
- Accentless French aliases required by PDF text extraction.

## Fixed
- Country propagation no longer leaves all new-country Gold-v3 events without geography.
- Specific currencies are resolved before generic `dollar -> USD`, preventing NZD/CAD from being overwritten.
- South-Africa body tables using `Periode` rather than `Année` are recognized.
- Structured table parser no longer truncates a body page merely because descriptive text contains the word `Appendix`.
- Inline `Annexe technique` / `Appendix ...` back matter is truncated more robustly.
- Monetary reserves are no longer coerced into public-debt stock merely because unrelated debt text occurs elsewhere on the same flattened PDF line.
- Additional relative-year wording is recognized without weakening ambiguity safeguards.

## Verification
- Existing regression suite: 111 passed, 0 failed.
- Gold-v3 smoke re-run after the first hardening pass confirms country ISO3 coverage across all seven documents and currency recognition for KES, USD, JPY, BRL and NZD where present.

## Known limitations
- v4.21 is a regression improvement derived from Gold-v3 errors, not a blind benchmark result.
- Recall for less common prose formulations still requires a future unseen corpus measurement.
- Gold v4 must be created and frozen before any generalization performance claim.
