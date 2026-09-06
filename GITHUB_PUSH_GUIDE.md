# Publish Econia on GitHub

## 1. Create the repository

Create an empty repository named `Econia` under `sarah-falehh`. Do not initialize it with a README, license or `.gitignore`, because they are already included here.

## 2. Publish this folder

```bash
git init
git branch -M main
git add .
git commit -m "Release Econia v6.1.0"
git remote add origin https://github.com/sarah-falehh/Econia.git
git push -u origin main
```

If the repository already has a remote:

```bash
git remote set-url origin https://github.com/sarah-falehh/Econia.git
git push -u origin main
```

## 3. Recommended GitHub settings

- Description: `Multilingual economic document intelligence for traceable PDF, CSV and text extraction.`
- Topics: `nlp`, `document-ai`, `economic-data`, `streamlit`, `arabic-nlp`, `pdf-extraction`, `python`.
- Default branch: `main`.
- Protect `main` and require the regression-test workflow before merging.
- Do not upload confidential source reports or the local SQLite database.
