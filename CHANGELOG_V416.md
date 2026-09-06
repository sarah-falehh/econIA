# EcoLingua-TN v4.16 — Intelligence Workspace

## Added
- Review Desk human-in-the-loop queue for observations requiring review or carrying conflicts.
- Evidence-first review cards with source sentence, semantic binding, confidence evidence and warnings.
- Session-scoped human decisions (validate / keep review / reject) without silently mutating raw extraction.
- Document X-Ray on Overview: paragraphs when available, countries, periods, forecasts, conflicts and validation spectrum.
- Analysis rail for Document → Extraction → Validation → Series.
- Morning Brief overview focused on operational review instead of generic dashboard cards.

## Changed
- Navigation now exposes Review Desk as a first-class control workflow.
- Visual identity strengthened toward editorial financial intelligence rather than generic Streamlit dashboard.
- Version label updated to v4.16.

## Reliability
- Extraction engine from v4.15 is intentionally unchanged in this UI release.
- Existing regression suite must remain green.
