# EconIntel AI v5.6 — Engineering Validation

## Scope

This release introduces the persistent central analysis/observation repository, full human observation editing with audit history, multi-analysis aggregation, duplicate/conflict handling, admin-only account management, bootstrap administrator authentication, and user-facing rebranding to EconIntel AI.

## Automated test result

- Tests collected: 200
- Tests passed: 200
- Tests failed: 0
- Tests skipped: 0
- Runtime: 33.61 s
- Command: `pytest -q`

The suite includes the 193 pre-existing regression tests plus 7 v5.6 tests covering bootstrap authentication, password hashing behavior, role authorization, admin-only account creation, multi-analysis persistence, exact duplicate deduplication, conflict detection, stable observation IDs, persistent human corrections, and correction attribution.

## Dependency installation note

`pip install -r requirements.txt` was attempted in the execution environment. It could not reach the Python package index because outbound network/DNS access is unavailable in this sandbox. This is an environment limitation, not a requirements resolution error. The available environment contained the core test dependencies and the full automated suite passed; Streamlit itself was not installed in this sandbox, so an interactive browser smoke-test could not be launched here.

## Static UI checks

The application source was scanned to verify that the user-facing application code contains no `Review Desk`, public `Créer un compte` / `Sign up`, numbered navigation formatter, or old `EcoLingua-TN` / `EcoLingua TN` branding.

## Launch

From the project root:

```bash
pip install -r requirements.txt
streamlit run app/dashboard.py
```
