# EcoLingua-TN v4.10 — Document Context & Period Alignment

## Fixed
- CSV country metadata is propagated into every document/event.
- CSV URL metadata is preserved.
- Comparison-aware value↔period alignment (`2025 ... X, contre Y en 2024`).
- Monthly period recognition and normalized period labels.
- Cumulative period labels for 11/9/7 first months and H1.
- Explicit `inflation sous-jacente` and `prix alimentaires` concepts override inherited generic inflation.

## Evaluation discipline
The v4.9 multisource output remains the baseline. No gold annotations are rewritten after prediction.
