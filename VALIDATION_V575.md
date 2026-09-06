# Validation report — v5.7.5

## Environment

- Python 3.12
- Deterministic local pipeline; no generative LLM calls
- Dependencies installed from `requirements.txt`

## Test suite

`python -m pytest -q`

- Collected: 221
- Passed: 221
- Failed: 0
- Skipped: 0
- Runtime: 65.63 seconds

## French non-regression gate

The supplied competitiveness PDF was executed with v5.7.3 and v5.7.5. Canonical tuples compared country, indicator code, value, period, unit, observation type and validation status.

- v5.7.3: 377 events
- v5.7.5: 377 events
- Canonical multiset equality: true
- Geography distribution: Tunisia 373; PECO 2; Asian competitors 2

This gate caught and prevented a mixed-language page from changing French context propagation.

## Arabic end-to-end checks

### Morocco test PDF

- Language detected: Arabic
- Events: 32
- Unresolved numeric tokens: 0
- Runtime: 8.54 seconds
- Examples verified: five GDP values, inflation and three-month comparison, unemployment/current and revised values, budget-deficit 2023–2025, exports/imports, current account, FDI, three policy-rate dates and two reserve values.

### Algeria independent test PDF

- Events: 44
- Unresolved numeric tokens: 0
- Regional lists correctly bind Algeria, Morocco and Tunisia.
- Shared import periods reuse the export year sequence.
- Policy-rate values 3.25, 3.50 and 3.75 are recovered across the page break.
- Chart-axis ticks are excluded.
- The 0.6 percentage-point comparison is retained as Rejected rather than accepted as a GDP level.

## Metrics not claimed

No Precision/Recall/F1 or exact-match percentage is published for the Arabic PDFs because a complete independent holdout GOLD file has not yet been manually annotated. Counts above are measured execution results, not estimated metrics.
