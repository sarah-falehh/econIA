# Econia v5.7.2 - UI validation

## Scope

This update changes navigation and presentation only. The extraction engine,
indicator ontology, PDF/CSV readers, validation logic, context resolution and
deduplication implementation are unchanged from the supplied v5.7.1 archive.

## Implemented behavior

- Sidebar navigation uses one stable Streamlit widget key and changes page on
  the first click.
- Numeric presentation removes trailing zeroes without rounding away useful
  decimals.
- Duplicate years expose an explicit value selector. The selected point is the
  only point used by the chart, statistics, horizontal table and downloads.
- Series and comparison charts use black labels, ticks, axis titles and legend
  text, with integer annual ticks.
- Comparison supports countries, regions, partners and economic groups, and
  displays each geography type explicitly.

## Verification

- Full suite: 208 passed, 0 failed, 0 skipped in 37.10 seconds.
- New UI regression tests: 5 passed.
- Python compilation passed for all modified Python files.
- Streamlit server startup completed successfully.
- Recursive comparison of `app/services` against the supplied v5.7.1 archive:
  no source-file difference.

## Files intentionally modified

- `app/dashboard.py`
- `app/views/professional_views.py`
- `app/views/workspace.py`
- `app/ui/branding.py`
- `tests/test_v571_ui_reliability.py`
- release documentation
