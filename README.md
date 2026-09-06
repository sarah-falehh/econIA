<div align="center">
<img src="docs/assets/diagrams/banner.png" alt="Econia — Economic Document Intelligence" width="100%">

# Econia
### Multilingual Economic Document Intelligence
**Transform economic documents into atomic, traceable and reviewable observations.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](#installation)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?logo=streamlit&logoColor=white)](#run-econia)
[![Languages](https://img.shields.io/badge/Languages-FR%20%7C%20AR%20%7C%20EN-1059B5)](#multilingual-processing)
[![Tests](https://img.shields.io/badge/Regression-225%20passed-16865C)](#evaluation-protocol)
[![CI](https://github.com/sarah-falehh/Econia/actions/workflows/tests.yml/badge.svg)](https://github.com/sarah-falehh/Econia/actions/workflows/tests.yml)
[![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20NLP-082B50)](#architecture)
[![Runtime](https://img.shields.io/badge/Runtime-CPU--friendly-ED1C2E)](#engineering-principles)

[Impact](#engineering-impact) · [Screenshots](#product-tour) · [Architecture](#architecture) · [Evaluation](#evaluation-protocol) · [Install](#installation) · [Roadmap](#roadmap)
</div>

---

## Overview

Econia is a production-oriented Python/Streamlit workspace designed for the ITCEQ economic-analysis workflow. It reads PDF, CSV and pasted text in French, Arabic and English, then converts narrative passages and structured tables into **atomic economic observations** with source evidence, confidence and validation status.

```text
Geography + Indicator + Value + Unit + Period + Fact type
          + Source + Original sentence + Quality + Status
```

Econia uses an auditable hybrid pipeline: deterministic parsing, configurable economic ontologies, geometry-aware table reconstruction, finite-state temporal resolution and lightweight NLP. A large local LLM is not required.

> [!IMPORTANT]
> Passing tests does not prove universal reliability on every possible PDF. Econia reports ambiguity and preserves evidence for human review. Scanned PDFs still require OCR, and arbitrary chart data cannot always be reconstructed safely.

## Engineering impact

Econia turns an experimental document-extraction prototype into a **testable economic information system**. The main contribution is not a single model score: it is the combination of semantic coverage, structured evidence, regression protection and CPU-efficient execution.

<table>
<tr><th>Measured outcome</th><th>Result</th><th>Why it matters</th></tr>
<tr><td><b>Regression protection</b></td><td><b>225/225 tests passed</b></td><td>Previously corrected semantic cases remain protected across French, Arabic, tables, periods, conflicts and exports.</td></tr>
<tr><td><b>Frozen GOLD benchmark</b></td><td><b>14 TP · 0 FP · 0 FN</b></td><td>Exact extraction on the fixed regression corpus, including indicator, value, unit, period, country and fact type.</td></tr>
<tr><td><b>Benchmark quality</b></td><td><b>Precision 100% · Recall 100% · F1 100%</b></td><td>Measured only on the 14-event frozen GOLD set; reported with its scope to avoid inflated claims.</td></tr>
<tr><td><b>Benchmark efficiency</b></td><td><b>1.669 s · 8.39 events/s</b></td><td>CPU execution without a large generative model.</td></tr>
<tr><td><b>Benchmark memory</b></td><td><b>26,420 KiB peak RSS</b></td><td>Lightweight enough for a standard laptop in the recorded Linux environment.</td></tr>
<tr><td><b>Arabic numerical coverage</b></td><td><b>0 unresolved tokens</b></td><td>Recorded on two synthetic Arabic validation PDFs producing 32 and 44 rows.</td></tr>
</table>

### PFE-level technical contribution

- Designed a **multilingual economic event schema** rather than returning unstructured text or summaries.
- Implemented a **clause-aware semantic binder** for many-to-many indicator/value/period relations, shared units and ordered comparisons.
- Added **finite-state temporal reasoning** for years, quarters, months, ranges, averages and relative periods.
- Built a **geometry-aware table path** that preserves row headers, column headers, sectors, periods and source coordinates.
- Isolated **Arabic RTL normalization** behind language gates to prevent regressions in the French pipeline.
- Introduced a **numerical reconciliation invariant** so unlinked economic numbers are reported rather than silently discarded.
- Developed **confidence-aware validation**, explicit review states, contradiction detection and evidence provenance.
- Established a **GOLD evaluation and permanent regression methodology** instead of evaluating against the application's own CSV output.
- Delivered an analyst-facing Streamlit product with authentication, role-based access, human validation, series, comparisons and export.

## Product tour

### Secure institutional access
<img src="docs/assets/screenshots/01-login-hd.png" alt="Econia secure login" width="100%">

### Document analysis workspace
<img src="docs/assets/screenshots/02-new-analysis-hd.png" alt="Econia document analysis" width="100%">

### Operational overview
<img src="docs/assets/screenshots/03-overview-hd.png" alt="Econia overview" width="100%">

<table><tr><td width="50%"><img src="docs/assets/screenshots/04-observations-hd.png" alt="Atomic observations"></td><td width="50%"><img src="docs/assets/screenshots/05-time-series-hd.png" alt="Time series"></td></tr><tr><td align="center"><b>Traceable observations</b></td><td align="center"><b>Validated time series</b></td></tr></table>

### Multi-indicator and multi-geography comparison
<img src="docs/assets/screenshots/06-comparison-hd.png" alt="Economic comparison" width="100%">

## Capabilities

| Capability | Engineering behavior |
| --- | --- |
| Multiformat ingestion | PDF, CSV and pasted-text paths. |
| Multilingual extraction | French, Arabic and English, including RTL normalization. |
| Atomic events | One indicator, value, period and complete semantic context per event. |
| Clause-level binding | Coordinated values, indicators, periods, units and geographies. |
| Temporal resolution | Years, months, quarters, ranges, averages and relative periods. |
| Structured tables | PDF geometry, headers, rows, columns and analytical dimensions. |
| Geography modelling | Countries, regions, partners and economic groups such as PECO. |
| Numerical reconciliation | Each economic-looking number is extracted, reviewed or excluded with a reason. |
| Human validation | Review and correction with an auditable history. |
| Analytics | Time series, duplicate-period resolution, comparisons and exports. |

## Technical stack and methods

| Layer | Technology / method | Role in the system |
| --- | --- | --- |
| PDF ingestion | **PyMuPDF** | Text blocks, pages, coordinates and table geometry. |
| Data processing | **pandas · NumPy** | Event normalization, reconciliation, series and exports. |
| Language routing | **langdetect + Unicode/RTL rules** | Language dominance and isolated Arabic normalization. |
| Lightweight ML | **word TF-IDF (1–2 grams) + character TF-IDF (3–5 grams) + balanced Logistic Regression** | Classifies economic sentences with multilingual lexical and morphological signals. |
| Semantic NLP | **Economic ontology + local relation rules** | Indicator heads, aliases, units, currencies and semantic binding. |
| Temporal NLP | **Finite-state resolver** | Absolute, ranged and relative periods with controlled inheritance. |
| Structured extraction | **Geometry-aware intermediate table representation** | Cell-to-header binding without flattening tables into prose. |
| Quality control | **Constraint validation + reconciliation** | Confidence, warnings, review decisions and unexplained-number detection. |
| Persistence | **SQLite** | Analyses, events, corrections, users and audit logs. |
| Product layer | **Streamlit + Plotly** | Interactive validation, time series, comparison and export. |
| Verification | **pytest + frozen GOLD matcher** | Non-regression and event/field-level evaluation. |

### Why a hybrid NLP architecture?

A large LLM can produce fluent output while silently changing a value, period or unit. Econia therefore assigns critical bindings through deterministic, inspectable components and uses lightweight ML only where it is measurable and reproducible. This provides lower hardware cost, stable inference and direct error attribution—important properties for institutional economic data.

### Lightweight classifier design

The serialized scikit-learn pipeline combines a word-level TF-IDF space capped at 12,000 features with a character `char_wb` TF-IDF space capped at 18,000 features. Word bigrams capture expressions such as economic indicator names, while 3–5 character grams improve robustness to inflection, accents and multilingual spelling variation. A class-balanced Logistic Regression classifier (`C=4.0`, `max_iter=2500`, fixed random seed) provides deterministic CPU inference. This classifier supports content selection; it does not generate values or override evidence-based semantic validation.

## Architecture

<div align="center"><img src="docs/assets/diagrams/architecture.svg" alt="Econia architecture" width="100%"></div>

The stages remain separate so a correction in Arabic normalization, table reading or the interface cannot silently change French semantic binding:

1. **Ingestion** preserves pages and source identity.
2. **Normalization** retains lines, blocks, coordinates and reading order.
3. **Structure detection** separates narrative, headings, tables, charts, annexes and noise.
4. **Content inventory** traces clauses and numerical mentions.
5. **Segmentation** creates atomic propositions.
6. **Semantic binding** links indicator, value, unit, geography, sector and period.
7. **Context resolution** permits local continuity and expires it at topic boundaries.
8. **Validation** assigns confidence, warnings and status.
9. **Persistence and analytics** store events, revisions, series and comparisons.

## Reliability workflow

<div align="center"><img src="docs/assets/diagrams/workflow.svg" alt="Econia numerical coverage workflow" width="100%"></div>

Every numerical mention receives a trace outcome: extracted, retained as **Needs review**, rejected with an explicit reason, or classified as documented noise. Chart ticks, page numbers, bibliographic years and econometric coefficients must not become observations.

## Atomic event model

<div align="center"><img src="docs/assets/diagrams/event-schema.svg" alt="Atomic event schema" width="100%"></div>

> After increasing by 2.6% in 2023, real GDP grew by only 1.9% in 2024. Activity is expected to expand by 2.2% in 2025 before accelerating to 2.4% in 2026.

| Geography | Indicator | Value | Unit | Period | Fact type |
| --- | --- | ---: | --- | --- | --- |
| Context country | Real GDP growth | 2.6 | % | 2023 | Observed |
| Context country | Real GDP growth | 1.9 | % | 2024 | Observed |
| Context country | Real GDP growth | 2.2 | % | 2025 | Forecast |
| Context country | Real GDP growth | 2.4 | % | 2026 | Forecast |

“0.7 percentage point lower” is traced as a relative variation, not stored as another GDP level.

## Multilingual processing

Arabic processing is isolated behind language-dominance gates so RTL repairs cannot alter French selection. It handles Arabic-Indic and Western digits, displaced percentage/currency signs, Arabic economic terminology, ordered geography lists, shared periods and flattened RTL tables. Image-only documents require OCR.

## Evaluation protocol

These measurements are regression evidence, not a universal accuracy claim.

| Validation | Measured result |
| --- | ---: |
| Full regression suite before v6.1 visual changes | **225 passed** |
| French competitiveness report | **377 events**, protected semantic baseline preserved |
| Arabic Morocco synthetic PDF | **32 rows; 0 unresolved numerical tokens** |
| Arabic Algeria independent synthetic PDF | **44 rows; 0 unresolved numerical tokens** |
| Frozen regression GOLD | **14/14 exact events** |
| GOLD precision / recall / F1 / exact match | **100% / 100% / 100% / 100%** on this small fixed corpus only |
| GOLD field accuracy | **100%** for country, indicator, value, unit, period and fact type |
| GOLD execution | **1.669 s · 8.39 events/s · 26,420 KiB peak RSS** |

See [`evaluation/README.md`](evaluation/README.md) for matching rules. Never use an application-generated CSV as GOLD; freeze manually verified annotations and keep unseen documents in a holdout corpus.

The repository separates three kinds of evidence:

1. **unit and regression tests** for permanent behavior protection;
2. **frozen GOLD annotations** for exact event and field-level metrics;
3. **document-level validation runs** for numerical coverage, statuses, runtime and unresolved mentions.

Precision, recall and F1 are not reported for a document until its independent manual GOLD annotation is complete. Event count alone is never presented as extraction accuracy.

```bash
python evaluation/evaluate.py --version v5.5
```

## Installation

Requirements: Python 3.11+, Windows/Linux/macOS, no GPU.

```bash
git clone https://github.com/sarah-falehh/Econia.git
cd Econia
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run Econia

```bash
streamlit run app/dashboard.py
```

Windows users can also run `run_windows.bat`. The local SQLite database is created under `data/ecolinguatn.db`; the historical filename is retained for compatibility.

### Local development account

```text
Email: admin@itceq.tn
Password: Admin123!
```

Change this bootstrap credential before any shared or network deployment.

## Tests

```bash
python -m pytest -q
```

## Repository map

```text
.
├── app/
│   ├── dashboard.py          # Streamlit entry point
│   ├── services/             # Parsing, binding, validation, analytics
│   ├── views/                # Product screens
│   ├── ui/                   # ITCEQ/Econia identity and theme
│   └── models/               # Domain objects
├── data/models/              # Lightweight NLP artefact
├── docs/assets/              # Banner, diagrams and screenshots
├── evaluation/               # GOLD, matching and benchmark results
├── tests/                    # Permanent non-regression suite
├── .github/workflows/        # Automated regression checks
├── requirements.txt
└── run_windows.bat
```

## Engineering principles

- **Generalize by error family.** PDFs reveal weaknesses; they are not hard-coded targets.
- **Protect previous behavior.** Every correction passes the historical suite.
- **Trace every number.** Extract, review, reject with a reason or classify as noise.
- **Keep tables structured.** Detectable tables use geometry and headers.
- **Prefer explainable CPU-friendly methods.** Deterministic and lightweight NLP first.
- **Keep evidence attached.** Every event remains auditable from dashboard to source.

## Known limitations

- Scanned/image-only PDFs require confidence-aware OCR.
- Arbitrary charts cannot be reliably digitized from text layers alone.
- Broken or highly irregular table geometry may require review.
- The ontology is extensible but not exhaustive across every domain.
- The current GOLD corpus is too small for a universal reliability claim.

## Roadmap

- confidence-aware OCR for French, Arabic and English;
- larger manually annotated development and holdout corpora;
- document-level precision, recall and coverage dashboards;
- richer continuation-table and multi-level-header reconstruction;
- institution-specific ontology packages;
- CI, deployment hardening and secure bootstrap configuration.

## Project evolution

Econia is the rebuilt successor to the original [Eco-Lingua](https://github.com/sarah-falehh/Eco-Lingua) prototype. It replaces the earlier broad LLM/RAG positioning with an auditable engine centred on atomic evidence, structured tables, numerical reconciliation and regression safety.

## Author

Developed by [Sarah Faleh](https://github.com/sarah-falehh) for an ITCEQ-oriented economic document intelligence project.

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing an extraction change and [SECURITY.md](SECURITY.md) for responsible vulnerability reporting.

---
<div align="center"><b>Economic evidence should be usable — and defensible.</b></div>
