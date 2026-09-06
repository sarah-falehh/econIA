# EcoLingua-TN v4.13 — Real PDF Reliability & Structured Macro Tables

## Added
- Strong-schema structured extraction for **Annexe 2 — Evolution de la dette publique**.
- New internal concepts for domestic/external public-debt stock and domestic debt share.
- Rounding-aware contradiction handling: values that differ only by source display precision remain traceable without being falsely flagged as contradictory.
- 7 new real-PDF non-regression tests; total suite now 83 tests.

## Fixed
- Historical month leakage: `14 janvier 2011` no longer turns annual 2013/2014 debt observations into `M01`.
- `Entre 2001 et 2010 ... passant de 56,47% à 40,4%` now exports `2001` and `2010` consistently; period labels are recomputed after semantic overrides.
- `Part de la dette publique dans la dette de l’État` now uses `%`, not `% du PIB`.
- Source metadata spillover is normalized (`Ministère des finances` instead of a source plus following narrative text).
- Useful macroeconomic annex tables are retained while generic/econometric annexes remain excluded.

## Measured on the held real PDF used during diagnosis
Baseline v4.12:
- 27 extracted events
- 4 annual observations incorrectly refined to `M01`
- 2 state-debt-share observations with wrong `% du PIB` unit
- 56.47 correctly stored internally as 2001 but exported with stale period label `2010`
- no structured Annex 2 series

v4.13:
- 238 extracted events
- 211 unique events originating from the strongly typed Annex 2 macro table after deduplication against narrative extraction
- 0 erroneous `M01` for the 2013/2014 introduction case
- 0 wrong `% du PIB` units for state-debt-share observations
- `56.47% -> 2001`, `40.4% -> 2010` in both internal year and exported period label
- real contradiction `52.22% vs 57.22%` for 1986 remains visible and marked for review
- rounding-compatible values such as `46.15%` and `46.2%` are not treated as contradictions
- source normalized to `Ministère des finances`

The increase from 27 to 238 observations is **coverage**, not accuracy. No Precision/F1 improvement is claimed from event count alone.

## Non-regression
- Existing synthetic 40-page stress matrix remains: 500 events, 60 legitimate M12 points, 0 missing source, 0 `nan` unit tokens, 0 econometric-noise events.
- Multi-source matrix remains: 55 events, 0 missing country, 11 document IDs.
