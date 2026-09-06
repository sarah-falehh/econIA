# Reproducible evaluation

Run the fixed benchmark:

```bash
python evaluation/evaluate.py --version v4.2
```

Compare two stored runs:

```bash
python evaluation/benchmark_report.py evaluation/results/v4.1.json evaluation/results/v4.2.json
```

## Metrics
- Event Precision / Recall / F1
- Event Exact Match
- Country / Indicator / Value / Unit / Period accuracy
- Observation type accuracy
- Review rate
- Processing time
- Events per second
- Peak RSS where available

An event is an exact match only when country, normalized indicator, value, compatible unit and period are all correct. Observation type can also be evaluated separately.

## Important interpretation rule
`gold_dataset.csv` is frozen before evaluating a new version. Never edit gold labels to make a prediction look correct. The current benchmark contains only 14 deliberately difficult events and is a regression suite, not a claim of general-world 100% accuracy. Expand it with unseen documents before using general performance claims on a CV.
