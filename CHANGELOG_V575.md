# Econia v5.7.5 — Arabic generalisation and French non-regression

## Root causes corrected

- RTL PDF text can serialize percent signs, dates, currencies and sentence punctuation in a different order from the visible page.
- Arabic semantic heads were not robust to common Alef/Hamza extraction variants.
- Ordered country lists and shared-period sibling series needed explicit clause-level alignment.
- Arabic tables flattened by PDF extraction were assigning every cell to the last visible year.
- Indicator context had to cross a genuine Arabic page break, while remaining isolated from French text on mixed-language pages.
- Arabic chart ticks and econometric coefficients needed dedicated noise classification.

## Architectural changes

- Arabic-only RTL normalization in `pdf_reader.py`.
- Arabic indicator, currency, month and quarter coverage in the registries and deterministic binder.
- Numerical reconciliation for Arabic clauses with displaced shared percent signs.
- Ordered geography and period-sequence binding.
- RTL flattened-table year-header alignment.
- Language-dominance gates: Arabic repairs cannot alter French candidate selection.
- New permanent regression tests in `tests/test_v575_rtl_generalization_nonregression.py`.

## Verified results

- Full pytest suite: **221 passed, 0 failed, 0 skipped** in 65.63 s.
- French competitiveness report: **377 events**, exactly identical as a semantic multiset to v5.7.3; 373 Tunisia, 2 PECO, 2 Asian competitors.
- Synthetic Arabic Morocco PDF: **32 rows**, 0 unresolved numerical tokens, runtime 8.54 s in the validation run.
- Independent synthetic Arabic Algeria PDF: **44 rows**, 0 unresolved numerical tokens; chart ticks excluded; three policy-rate dates recovered across a page break.

## Honest limitation

These regression results do not prove reliability on every possible PDF. Scanned/image-only PDFs still require OCR, and arbitrary charts cannot be reconstructed reliably from text alone. Precision, recall and F1 are not reported because no complete independent holdout GOLD annotation was available for these two Arabic PDFs.
