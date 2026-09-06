# EcoLingua-TN v4.22 — Temporal Relations & Semantic Scope

## Added
- Generic temporal relation coverage for unaccented French PDF text (`annee precedente`, `annee d'avant`, `un mois plus tot`, `trimestre qui precedait`, `trois mois plus tard`).
- Country-prefixed coreference support such as `En Republique tcheque, elles...`.
- Regression tests for Canada mixed-frequency extraction, New Zealand relative periods/currency, Brazil quarterly frequency inheritance, Japan observation-type scope, and Czech export-growth binding.

## Changed
- Explicit quarter/month evidence now takes precedence over comparison phrases such as `par rapport au trimestre precedent`.
- Forecast scope no longer treats a generic heading containing `previsions` as evidence that an observed value is a forecast.
- Frequency-aware GDP labeling now recognizes relative quarter phrases (`trimestre suivant`, `trimestre qui precedait`, `trois mois plus tard`).
- CPI annual-average and monthly-change semantics are distinguished more carefully.
- Safe-context validation recognizes unaccented PDF forms and deterministic month/year coreference.

## Fixed
- Canada blind baseline recall: the supplied Gold v3 Canada PDF rises from 5 extracted events in v4.21 to 12 events in v4.22 on the same document.
- `Au dernier trimestre de l'annee ... +0,5 %` is represented as 2024-Q4 quarterly GDP growth.
- `Un mois plus tot, il etait de 6,8 %` resolves to 2024-M11.
- `Le solde budgetaire etait estime a -1,2 % du PIB` is retained as an estimated fiscal observation.
- `Pour 2026, elle remonterait a 1,8 %` is classified as a forecast.
- `Elles etaient ... l'annee precedente` keeps the inherited monetary currency and shifts the year.
- A title/header containing the word `previsions` no longer flips a later explicit 2024 observation to forecast.

## Verification
- `pytest -q`: 116 passed.
- Canada Gold v3 document, engine run: 12 events, 12 Validé, 0 À vérifier.

## Methodological note
Gold v3 has already been inspected and used to design v4.21/v4.22. It is therefore a regression corpus now, not a blind generalization benchmark. No general F1 claim is made from this release.
