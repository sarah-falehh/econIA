# Econia v6.0.0 — ITCEQ institutional workspace

## Design direction

The interface has been rebuilt around the visual language observable in ITCEQ's public identity: institutional blue, structural grey, white working surfaces and a dynamic red curve. This is an application interpretation, not a claim that an unpublished official design manual was reproduced.

- White institutional sidebar with a CSS-rendered ITCEQ-inspired emblem.
- Compact Econia lockup and red motion accent.
- Dense analyst-oriented navigation and active states.
- Compact page headers instead of oversized decorative hero panels.
- Low-noise cards, tables, inputs and chart surfaces.
- White dashboard canvas with blue information hierarchy and restrained red accents.
- Existing country flags and economic-group identities are preserved.
- Analytical-table and visual-card modes are preserved.

## Comparator regression fix

The geography selector no longer derives its options from the current selection or only from the current indicator. It uses the complete non-rejected geography catalogue, so countries, PECO, Asian competitors, regions and partners remain discoverable. The chart still displays only real dated observations and never fabricates a missing series.

## Extraction boundary

No ingestion, extraction, semantic-binding, temporal-resolution, Arabic-processing, table-processing or evidence-validation component was changed.

## Verification

- Final full suite: **224 passed, 0 failed, 0 skipped** in 65.97 seconds.
- Focused navigation, geography and UI regression suite: **11 passed**.
- Python compilation: passed.
