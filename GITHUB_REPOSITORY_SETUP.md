# GitHub repository setup

## Recommended identity

- Repository name: `econia-economic-intelligence`
- Display name: `Econia — Multilingual Economic Document Intelligence`
- Short description: `CPU-friendly multilingual NLP pipeline that extracts traceable economic events from PDF, CSV and text in French, Arabic and English.`
- Website: add the Streamlit deployment URL when a public demo is ready.
- Visibility: choose Public only after removing private reports, local databases, credentials and personal exports.

Suggested topics:

```text
nlp economic-data document-intelligence information-extraction
multilingual-nlp arabic-nlp french-nlp pdf-extraction streamlit
table-extraction temporal-reasoning human-in-the-loop python
```

## Before the first push

1. Change the initial administrator password mechanism for any public deployment.
2. Ensure `data/ecolinguatn.db`, uploaded documents and generated user exports are ignored.
3. Decide on a license. Do not add an open-source license unless you intend to grant those rights.
4. Replace `YOUR-USERNAME/YOUR-NEW-REPOSITORY` in `README.md` with the final URL.
5. Run `pytest -q` and commit the generated test report only if it contains no private paths or documents.
6. Use `docs/assets/econia-banner-background.png` as the README banner and `docs/assets/econia-mark.svg` as the repository/avatar mark.

## Create and push the new repository

Create an empty repository on GitHub without an automatically generated README, then run from this project folder:

```bash
git init
git branch -M main
git add .
git commit -m "feat: publish Econia multilingual extraction platform"
git remote add origin https://github.com/YOUR-USERNAME/econia-economic-intelligence.git
git push -u origin main
```

## Suggested first release

- Tag: `v5.7.5`
- Title: `Econia v5.7.5 — Multilingual extraction baseline`
- Release notes: reuse `CHANGELOG_V575.md`, then link the exact test and benchmark artefacts.

## Social preview

In GitHub, open **Settings → General → Social preview** and upload the banner image. Check the crop before saving because GitHub's social card aspect ratio differs from the full README banner.
