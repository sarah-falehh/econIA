# Contributing to Econia

Thank you for helping improve Econia.

## Reliability rule

A supplied document is a test case, not a target for document-specific patches. Every extraction defect must be handled as a general error family:

1. reproduce the defect;
2. identify the responsible pipeline component;
3. add a generalized regression test;
4. implement the smallest architectural correction;
5. run the complete historical suite;
6. evaluate representative documents in French, Arabic and English;
7. document any remaining limitation.

Do not weaken or delete an existing test to make a new change pass. Do not add rules containing document-specific values, page numbers or sentences.

## Local validation

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

Keep generated databases, user exports, uploaded documents, credentials and local virtual environments out of commits.

## Pull requests

Describe the error family, root cause, affected modules, new tests, complete test result and measured document-level impact. Never report invented precision, recall or F1 values.
