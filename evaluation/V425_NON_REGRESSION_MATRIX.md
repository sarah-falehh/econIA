# v4.25 Non-regression matrix

| Capability | Guard |
|---|---|
| Multi-value sentence extraction | Existing v4.x event tests |
| Debt stock vs debt ratio | v4.5 / v4.11 / v4.13 tests |
| Previous/next year and Temporal Anchor Graph | v4.10 / v4.23 / v4.25 tests |
| Previous quarter / month | v4.15 / v4.22 / v4.25 tests |
| Multi-country value binding | v4.15 / v4.19 tests |
| Dynamic country registry | v4.24 tests |
| Dynamic currency registry | v4.25 tests |
| Currency propagation across comparisons | v4.11 / v4.22 / v4.25 tests |
| Observed / estimated / forecast | v4.11+ tests |
| Conflict != duplicate | v4.7+ tests |
| Rounding-equivalent != conflict | v4.13 tests |
| Missing country forces review | v4.17 tests |
| Safe context inheritance | v4.17 / v4.18 tests |
| Body macro tables | v4.20 / v4.25 tests |
| Annex/Appendix exclusion | v4.15 / v4.25 tests |
| Econometric noise rejection | v4.4+ regression tests |
| User export Type/Status/Confidence | v4.7+ tests |
| NaN-safe units / Excel export | v4.9 / v4.15 tests |

All rows are covered by the complete `pytest -q` run; v4.25 passes 134 tests.
