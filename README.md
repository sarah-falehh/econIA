<div align="center">

<img src="docs/assets/diagrams/banner.png" alt="EconIA — Economic Document Intelligence" width="100%">

# EconIA

### Multilingual Economic Document Intelligence

**From economic documents to atomic, traceable and reviewable data.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python\&logoColor=white)](#installation)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?logo=streamlit\&logoColor=white)](#run-econia)
[![Languages](https://img.shields.io/badge/Languages-FR%20%7C%20AR%20%7C%20EN-1059B5)](#multilingual-processing)
[![Tests](https://img.shields.io/badge/Regression-225%20passed-16865C)](#evaluation)
[![CI](https://github.com/sarah-falehh/Econia/actions/workflows/tests.yml/badge.svg)](https://github.com/sarah-falehh/Econia/actions/workflows/tests.yml)
[![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20NLP-082B50)](#architecture)
[![Runtime](https://img.shields.io/badge/Runtime-CPU--friendly-ED1C2E)](#engineering-principles)

[Overview](#overview) ·
[Evolution](#from-eco-lingua-to-econia) ·
[Architecture](#architecture) ·
[Evaluation](#evaluation) ·
[Product](#product-tour) ·
[Installation](#installation)

</div>

---

## Overview

**EconIA is a multilingual economic document intelligence system designed to transform heterogeneous economic documents into structured observations that remain traceable to their source.**

It processes:

* PDF reports;
* structured and semi-structured tables;
* CSV files;
* pasted text;
* French, Arabic and English content.

Instead of returning a summary or a free-form LLM answer, EconIA extracts **atomic economic events**.

Each observation represents one economic fact:

```text
Geography
+ Indicator
+ Value
+ Unit
+ Period
+ Fact type
+ Source evidence
+ Confidence
+ Validation status
```

For example:

```text
Tunisia
+ Real GDP growth
+ 1.4
+ %
+ 2024
+ Observed
```

The core extraction pipeline is built around **deterministic and lightweight NLP components**, including economic ontologies, temporal and contextual reasoning, semantic binding, PDF table geometry and explicit validation rules.

**EconIA does not rely on a large LLM for its core extraction pipeline.**

This is a deliberate engineering choice: the objective is not to generate plausible economic information, but to extract structured facts whose origin and interpretation can be inspected.

> [!IMPORTANT]
> EconIA is an engineering and research project, not a claim of universal document understanding.
>
> Passing the regression suite or obtaining perfect results on the current small GOLD benchmark does **not** imply 100% reliability on arbitrary unseen documents.

---

# From Eco-Lingua to EconIA

EconIA is the redesigned successor to the original [Eco-Lingua](https://github.com/sarah-falehh/Eco-Lingua) prototype.

The two projects represent **different stages and different architectural choices**.

### Eco-Lingua

The first prototype explored a broader AI architecture involving:

* embeddings;
* semantic retrieval;
* RAG;
* LLM-assisted processing.

It was useful for experimenting with semantic search and document interaction.

### EconIA

While working with economic reports, the engineering objective changed.

For structured economic extraction, the main requirements became:

* exact value preservation;
* correct indicator ↔ value ↔ period association;
* temporal reasoning;
* table reconstruction;
* reproducibility;
* explicit ambiguity handling;
* traceability;
* regression safety;
* CPU-efficient execution.

The extraction engine was therefore redesigned around a more controlled architecture:

```text
Eco-Lingua
LLM / RAG-oriented experimentation
            │
            │ architectural redesign
            ▼
EconIA
Deterministic + lightweight NLP
            │
            ├── atomic extraction
            ├── temporal reasoning
            ├── semantic binding
            ├── table reconstruction
            ├── numerical reconciliation
            └── explicit validation
```

This evolution reflects an important engineering lesson from the project:

> **The most sophisticated model is not necessarily the most appropriate architecture for every AI problem.**

For EconIA, auditability and deterministic control over critical economic fields were more important than generative flexibility.

---

# The extraction problem

Economic information extraction is harder than detecting numbers.

Consider:

> After increasing by 2.6% in 2023, real GDP grew by only 1.9% in 2024. Activity is expected to expand by 2.2% in 2025 before accelerating to 2.4% in 2026.

The expected representation is:

| Geography         | Indicator       | Value | Unit | Period | Fact type |
| ----------------- | --------------- | ----: | ---- | ------ | --------- |
| Context geography | Real GDP growth |   2.6 | %    | 2023   | Observed  |
| Context geography | Real GDP growth |   1.9 | %    | 2024   | Observed  |
| Context geography | Real GDP growth |   2.2 | %    | 2025   | Forecast  |
| Context geography | Real GDP growth |   2.4 | %    | 2026   | Forecast  |

The system must understand that:

* several values may belong to the same indicator;
* each value may correspond to a different period;
* a unit may be shared across several values;
* an indicator may be omitted in a continuation clause;
* a forecast must not be confused with an observed value;
* a relative variation is not necessarily an economic level.

For example:

```text
"0.7 percentage point lower"
```

must not automatically become another GDP observation.

This is why EconIA treats extraction as a **semantic binding problem**, not simply a number-detection problem.

---

# Architecture

<div align="center">

<img src="docs/assets/diagrams/architecture.svg" alt="EconIA architecture" width="100%">

</div>

The pipeline separates extraction stages so errors can be located and corrected without silently affecting unrelated behavior.

```text
PDF / CSV / Text
        │
        ▼
┌─────────────────────┐
│      Ingestion      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│    Normalization    │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Structure Detection │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Content Selection   │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Atomic Segmentation │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Semantic Binding   │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Context + Temporal  │
│     Resolution      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Validation & Score  │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Persistence         │
│ Analytics           │
│ Human Validation    │
└─────────────────────┘
```

## 1. Ingestion

The ingestion layer accepts PDF, CSV and text inputs while preserving document identity and source information.

For PDFs, **PyMuPDF** is used to access:

* pages;
* text blocks;
* lines;
* coordinates;
* layout information.

The goal is to avoid destroying structural information too early.

---

## 2. Structure detection

Document elements are distinguished before semantic extraction.

Typical structures include:

* narrative paragraphs;
* headings;
* lists;
* structured tables;
* footnotes;
* annexes;
* chart-related content;
* layout noise.

This matters because a value inside a paragraph cannot always be interpreted using the same rules as a value inside a table.

---

## 3. Atomic segmentation

Long sentences are decomposed into smaller semantic propositions before extraction.

This reduces incorrect many-to-many associations between:

* indicators;
* values;
* units;
* periods;
* geographies.

The objective is to make the extraction unit as close as possible to **one economic fact**.

---

## 4. Economic ontology

A configurable ontology represents economic indicators and their aliases.

It supports the normalization of different surface forms toward consistent indicator concepts.

Examples include variations around:

* GDP growth;
* inflation;
* unemployment;
* public debt;
* exports;
* foreign direct investment;
* exchange rates;
* fiscal indicators.

The ontology does not replace context reasoning: it provides the semantic vocabulary used by the binding layer.

---

## 5. Semantic binding

The semantic binder associates:

```text
Indicator ↔ Value ↔ Unit ↔ Period ↔ Geography
```

while handling cases such as:

* several values in one sentence;
* shared units;
* ordered comparisons;
* implicit continuation of an indicator;
* multiple periods;
* multiple geographies.

This layer is one of the central components of EconIA.

---

## 6. Temporal resolution

Economic documents frequently use more than explicit years.

The temporal resolver handles:

* years;
* months;
* quarters;
* ranges;
* averages;
* relative periods;
* controlled period inheritance.

Temporal context is propagated only when the local context supports it and is reset when topic boundaries invalidate the previous context.

---

## 7. Geometry-aware table extraction

Tables are not flattened directly into prose.

When sufficient layout information exists, EconIA preserves relationships between:

* row headers;
* column headers;
* periods;
* indicators;
* values;
* sectors;
* source coordinates.

This allows a numerical cell to be interpreted using its structural context rather than only nearby text.

---

# Lightweight NLP

EconIA also uses lightweight machine learning for **content selection**.

The classifier combines:

* word TF-IDF features;
* character TF-IDF features;
* Logistic Regression.

The current serialized pipeline uses:

```text
Word TF-IDF:
1–2 grams
up to 12,000 features

Character TF-IDF:
char_wb
3–5 grams
up to 18,000 features

Classifier:
class-balanced Logistic Regression
C = 4.0
max_iter = 2500
fixed random seed
```

Word-level features capture recurring economic expressions, while character features improve robustness to morphology, accents and multilingual spelling variation.

Importantly:

> **The classifier selects relevant content. It does not generate economic values and does not override evidence-based semantic validation.**

---

# Multilingual processing

EconIA supports:

* 🇫🇷 French
* 🇹🇳 / 🇲🇦 / 🇩🇿 Arabic
* 🇬🇧 English

Arabic introduces additional document-processing difficulties, especially in PDF text layers:

* RTL ordering;
* Arabic-Indic versus Western digits;
* displaced currency or percentage symbols;
* reordered table content;
* shared periods;
* flattened RTL structures.

Arabic normalization is therefore isolated behind language-specific routing.

This separation prevents an RTL correction from silently changing behavior in French or English extraction.

---

# Numerical reconciliation

One of EconIA's core reliability mechanisms is **numerical coverage**.

The objective is simple:

> **An economically relevant number should not silently disappear from the pipeline.**

Each detected numerical mention receives a trace outcome such as:

```text
Extracted
Needs review
Rejected with reason
Documented noise
```

Noise may include:

* page numbers;
* chart ticks;
* table indices;
* bibliographic years;
* econometric coefficients;
* layout artifacts.

<div align="center">

<img src="docs/assets/diagrams/workflow.svg" alt="EconIA numerical reconciliation workflow" width="100%">

</div>

When a number is not transformed into an economic observation, the trace should explain why.

This mechanism does **not** mean that every number is considered valid economic information.

It means that unexplained disappearance is treated as an engineering issue.

---

# Validation and human review

Extraction results can carry:

* confidence information;
* warnings;
* evidence;
* validation status;
* correction history.

Typical statuses include:

```text
Validated
Needs review
Rejected
```

Ambiguous cases can therefore remain visible instead of being silently accepted or discarded.

This keeps automated extraction and human validation as separate concerns.

---

# Atomic event model

<div align="center">

<img src="docs/assets/diagrams/event-schema.svg" alt="EconIA atomic event schema" width="100%">

</div>

A structured observation can contain:

| Field      | Example                             |
| ---------- | ----------------------------------- |
| Geography  | Tunisia                             |
| Indicator  | Inflation                           |
| Value      | 7.0                                 |
| Unit       | %                                   |
| Period     | 2024                                |
| Fact type  | Observed                            |
| Source     | Source document                     |
| Evidence   | Original sentence / table context   |
| Confidence | Extraction confidence               |
| Status     | Validated / Needs review / Rejected |

The model can also retain analytical dimensions when they are available, such as sector, partner geography or methodology.

---

# Product tour

## Authenticated access

<img src="docs/assets/screenshots/01-login-hd.png" alt="EconIA login" width="100%">

## Document analysis

<img src="docs/assets/screenshots/02-new-analysis-hd.png" alt="EconIA document analysis workspace" width="100%">

## Analysis overview

<img src="docs/assets/screenshots/03-overview-hd.png" alt="EconIA analysis overview" width="100%">

<table>
<tr>
<td width="50%">
<img src="docs/assets/screenshots/04-observations-hd.png" alt="Atomic economic observations">
</td>
<td width="50%">
<img src="docs/assets/screenshots/05-time-series-hd.png" alt="Economic time series">
</td>
</tr>
<tr>
<td align="center"><b>Traceable observations</b></td>
<td align="center"><b>Time-series reconstruction</b></td>
</tr>
</table>

## Economic comparisons

<img src="docs/assets/screenshots/06-comparison-hd.png" alt="Economic comparison interface" width="100%">

A central objective of the application is to turn document extraction into something directly usable by analysts.

Validated observations can therefore be reorganized into **time-series tables and plots**, avoiding repeated manual extraction from long economic reports.

---

# Capabilities

| Capability               | Behavior                                                  |
| ------------------------ | --------------------------------------------------------- |
| Multiformat ingestion    | PDF, CSV and pasted text                                  |
| Multilingual processing  | French, Arabic and English                                |
| Atomic extraction        | One economic fact per observation                         |
| Clause-level binding     | Indicator, value, period, unit and geography associations |
| Temporal reasoning       | Years, quarters, months, ranges and relative periods      |
| Structured tables        | Geometry-aware row/column/header interpretation           |
| Geography modelling      | Countries, regions, partners and economic groups          |
| Numerical reconciliation | Trace outcome for detected numerical mentions             |
| Evidence preservation    | Original sentence or structural context                   |
| Human validation         | Review and correction workflow                            |
| Time series              | Structured historical/forecast representations            |
| Comparison               | Multi-indicator and multi-geography analysis              |
| Export                   | Structured data outputs                                   |

---

# Technical stack

| Layer                 | Technology / method                       |
| --------------------- | ----------------------------------------- |
| Language              | Python 3.11+                              |
| PDF processing        | PyMuPDF                                   |
| Data processing       | pandas, NumPy                             |
| Language routing      | langdetect + Unicode / RTL rules          |
| Lightweight ML        | TF-IDF + Logistic Regression              |
| Semantic NLP          | Economic ontology + relation rules        |
| Temporal reasoning    | Finite-state resolver                     |
| Structured extraction | Geometry-aware table representation       |
| Validation            | Constraints + confidence + reconciliation |
| Persistence           | SQLite                                    |
| Product interface     | Streamlit                                 |
| Visualization         | Plotly                                    |
| Testing               | pytest                                    |
| Evaluation            | Frozen GOLD matcher                       |
| CI                    | GitHub Actions                            |

---

# Evaluation

EconIA deliberately separates **regression testing**, **benchmark evaluation** and **document-level validation**.

These answer different questions.

## 1. Regression tests

Current repository status:

**225 / 225 regression tests passing**

The regression suite protects previously corrected behavior across areas such as:

* semantic binding;
* temporal reasoning;
* Arabic processing;
* tables;
* conflicts;
* validation;
* exports.

A regression test answers:

> **Did a code change break behavior that was already protected?**

It does **not** measure general extraction accuracy.

---

## 2. Frozen GOLD benchmark

The current manually verified GOLD benchmark contains **14 annotated events**.

Measured results:

| Metric            | Result |
| ----------------- | -----: |
| True Positives    |     14 |
| False Positives   |      0 |
| False Negatives   |      0 |
| Precision         |   100% |
| Recall            |   100% |
| F1                |   100% |
| Event Exact Match |   100% |

Field-level matching currently covers:

* country;
* indicator;
* value;
* unit;
* period;
* fact type.

> [!CAUTION]
> These 100% results apply **only to this small 14-event benchmark**.
>
> They do not demonstrate 100% accuracy on unseen economic documents and are not presented as a universal reliability claim.

The benchmark is useful as a controlled evaluation baseline, but expanding manually annotated holdout data remains necessary.

---

## 3. Document-level validation

Additional documents are used to expose new error families and evaluate numerical coverage.

Current validation runs include Arabic documents producing:

* **32 extracted events** on a Moroccan validation document;
* **44 extracted events** on an Algerian validation document;
* **zero unexplained economic numerical tokens** in the recorded coverage traces for those runs.

These values represent **extraction and numerical-coverage observations**.

They are **not precision or recall measurements** unless an independent complete GOLD annotation exists for the document.

---

## Current benchmark runtime

Recorded GOLD evaluation:

```text
Execution time: 1.669 s
Throughput:     8.39 events/s
Peak RSS:       26,420 KiB
```

This benchmark demonstrates lightweight CPU execution in the recorded environment.

It should not be interpreted as a general scalability benchmark.

---

# Evaluation methodology

The project distinguishes three forms of evidence:

### Regression suite

Protects known behavior.

### Frozen GOLD annotations

Measures event-level and field-level extraction against manually verified expected outputs.

### Validation documents

Expose new document structures, languages and numerical-coverage problems.

A PDF failure is treated as an **error family**, not as a document-specific exception.

The workflow is:

```text
Observed failure
      ↓
Identify general error family
      ↓
Create regression test
      ↓
Correct responsible component
      ↓
Run full historical suite
      ↓
Re-evaluate documents
```

Document-specific values, sentences or page numbers should not be hard-coded to make a test file pass.

---

# Why this architecture?

A generative model can be useful when the goal is semantic interaction, summarization or flexible reasoning.

EconIA has a different core requirement.

For economic extraction, errors such as:

```text
2024 → 2025

7.0% → 7.8%

Observed → Forecast

Tunisia → Morocco
```

are not stylistic errors.

They change the economic meaning of the data.

The architecture therefore prioritizes:

* inspectable transformations;
* deterministic critical bindings;
* reproducible inference;
* explicit ambiguity;
* evidence provenance;
* regression protection.

This does not mean that LLMs are inappropriate for document intelligence.

It means that **EconIA uses them only where their trade-offs would be justified rather than making them a mandatory component of the extraction core.**

---

# Engineering principles

### Generalize from error families

Documents expose weaknesses; they are not hard-coded targets.

### Protect previous behavior

A fix should not silently introduce regressions elsewhere.

### Trace numerical information

Numbers should be extracted, reviewed, rejected with a reason, or classified as noise.

### Preserve document structure

Tables should remain structured whenever geometry allows it.

### Keep evidence attached

A structured event should remain traceable to its source context.

### Separate confidence from correctness

A confidence score is an engineering signal, not proof that an observation is true.

### Prefer measurable components

Critical extraction behavior should be testable and reproducible.

---

# Known limitations

EconIA still has important limitations.

* Image-only or scanned PDFs require OCR before reliable extraction.
* Arbitrary charts cannot be safely reconstructed from text layers alone.
* Highly irregular or broken PDF table geometry can require human review.
* The economic ontology is extensible but not exhaustive.
* Ambiguous cross-paragraph references remain difficult.
* Numerical coverage does not imply semantic correctness.
* The current 14-event GOLD corpus is far too small to support broad reliability claims.
* Larger manually annotated and genuinely unseen evaluation corpora are still required.

These limitations are intentionally documented rather than hidden behind an aggregate score.

---

# Installation

### Requirements

* Python 3.11+
* Windows, Linux or macOS
* No GPU required

```bash
git clone https://github.com/sarah-falehh/econIA.git
cd econIA

python -m venv .venv
```

### Windows PowerShell

```bash
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

# Run EconIA

```bash
streamlit run app/dashboard.py
```

Windows users can also use:

```text
run_windows.bat
```

The application uses a local SQLite database for analyses, observations, corrections and user-related application data.

> Do not use default development credentials for shared or network deployments.

---

# Tests

Run the complete regression suite:

```bash
python -m pytest -q
```

Run the GOLD evaluation:

```bash
python evaluation/evaluate.py --version v5.5
```

See [`evaluation/README.md`](evaluation/README.md) for evaluation and matching rules.

---

# Repository structure

```text
.
├── app/
│   ├── dashboard.py
│   ├── services/
│   ├── views/
│   ├── ui/
│   └── models/
│
├── data/
│   └── models/
│
├── docs/
│   └── assets/
│       ├── diagrams/
│       └── screenshots/
│
├── evaluation/
│
├── tests/
│
├── validation_outputs/
│
├── .github/
│   └── workflows/
│
├── requirements.txt
├── pytest.ini
└── run_windows.bat
```

---

# Roadmap

The next engineering priorities are:

* larger manually annotated development and holdout corpora;
* confidence-aware OCR for scanned French, Arabic and English documents;
* richer multi-level and continuation-table reconstruction;
* stronger document-level evaluation dashboards;
* institution-specific ontology extensions;
* broader unseen-document validation;
* deployment and security hardening.

---

# What I learned from building EconIA

EconIA started as a document AI experiment and gradually became an exercise in **reliability engineering for NLP systems**.

The most important lessons were not about maximizing model complexity.

They were about:

* defining exactly what an extraction event means;
* separating retrieval, generation and extraction problems;
* measuring different forms of quality separately;
* making failures reproducible;
* treating ambiguous output explicitly;
* preserving source evidence;
* designing architecture around the actual risk of the application.

The project reinforced a principle that now guides how I approach Applied AI systems:

> **Model choice should follow the problem, the evaluation strategy and the cost of failure — not the other way around.**

---

## Author

**Sarah Faleh**

Data Science & AI Engineering student
Applied AI · NLP · Document Intelligence · RAG · AI Agents · ML Engineering

[GitHub](https://github.com/sarah-falehh) ·
[LinkedIn](https://www.linkedin.com/in/sarah-faleh/)

---

<div align="center">

### Economic data is useful only when its meaning — and its source — can be defended.

</div>
