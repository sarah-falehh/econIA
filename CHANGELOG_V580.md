# Econia v5.8.0 — Immersive interactive interface

## Scope

This release changes presentation and interaction only. The extraction, semantic binding, temporal resolution, Arabic handling, validation and persistence logic are unchanged from v5.7.5.

## Visual system

- New glass-like hero panels with restrained depth and responsive background accents.
- Modern navy-to-teal navigation with a live-status cue and clearer active states.
- Page icons while preserving the same internal route names and permissions.
- Animated page entry, card elevation and accessible focus states.
- Larger 16 px table typography and stronger header contrast.
- Rounded, elevated containers, inputs, popovers and Plotly surfaces.
- Unified accessible Plotly template with high-contrast labels and hover cards.

## Interaction

- Smooth spline rendering for time series and comparison charts.
- More visible markers, lightweight area emphasis and horizontal legends.
- Unified hover inspection and clearer forecast differentiation.
- Existing one-click Streamlit navigation and all business controls are preserved.

## Non-regression boundary

No extraction service was modified. A clean Python syntax compilation succeeded. The complete suite reports **223 passed, 0 failed, 0 skipped** in 69.88 seconds: the 221-test extraction baseline plus two new permanent UI regression tests.
