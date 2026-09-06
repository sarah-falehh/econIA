# EcoLingua-TN — Experimental log

No performance claim is accepted without a reproducible benchmark result committed under `evaluation/results/`.

## EXP-001 — v4.1 baseline
- Problem: establish the first fixed event-extraction baseline.
- Dataset: `benchmark_v1.txt` with 14 manually annotated gold events.
- Modification: none; measurement of the deterministic context-aware engine.
- Metrics: Precision **76.92%**, Recall **71.43%**, F1 **74.07%**, Event Exact Match **71.43%**; 13 predictions for 14 gold events. See `results/v4.1.json`.
- Known limitations: the benchmark is deliberately small and must be expanded with independent reports before CV-level generalization claims.

## EXP-002 — v4.2 productization
- Problem: schema robustness, professional navigation, reproducible evaluation and user-facing exports.
- Dataset: same fixed 14-event benchmark for regression comparability.
- Extraction engine: intentionally unchanged until the baseline is frozen.
- Metrics: Precision **100.00%**, Recall **100.00%**, F1 **100.00%**, Event Exact Match **100.00%** on this 14-event regression benchmark. See `results/v4.2.json`.
- Gain vs v4.1: **+25.93 F1 percentage points** (**+35.00% relative**).
- Important: this is a deliberately small regression set, not yet evidence of 100% general performance on unseen economic reports.
- Interpretation: UI/product changes must not be presented as extraction-quality gains.

## EXP-V44-01 — Unit and ontology reliability
- Date: 2026-08-21
- Version: v4.4
- Problem: exported `nan %` / `milliard nan`; missing official reserves and primary balance; missing `un an auparavant` context.
- Changes: currency normalization, safe export formatting, ontology phrase expansion, temporal context expansion, evidence-based confidence.
- Regression benchmark: 14 gold events.
- Result: 14/14 exact matches; Precision 100%; Recall 100%; F1 100%.
- Automated tests: 22 passed.
- Synthetic stress test: 41 pages; 500 predicted events; 60 reserves events; 10 primary-balance events; 0 events from econometric-noise phrases; engine pass ~0.258 s excluding PDF text extraction/UI.
- Limitation: the 41-page stress corpus is synthetic and does not yet have a complete hand-annotated gold set, so no valid full-document Precision/Recall/F1 is claimed.

## EXP-V45-SEMANTIC-UNITS — v4.5
- Problem: coreferential ratio observations could lose `% du PIB` and split one economic series into incompatible unit groups; monetary debt coreferences could inherit a ratio indicator.
- Hypothesis: conservative same-indicator semantic-unit inheritance plus monetary-vs-ratio type constraints will remove these inconsistencies without leaking `% du PIB` to unrelated indicators.
- Changes: same-indicator `% du PIB` inheritance; canonical debt-ratio units; monetary debt coreference forced to stock; regression tests.
- Regression tests: 26 passed.
- Fixed gold benchmark: 14/14 exact events; Precision=1.0, Recall=1.0, F1=1.0, Exact Match=1.0.
- 41-page synthetic stress corpus: 500 events; `nan` unit/currency occurrences=0; public debt ratio with wrong semantic unit=0.
- Runtime: ~0.24 s extraction on pre-extracted corpus text in the test environment; excludes PDF I/O and UI.
- Limitation: stress corpus is not yet fully hand-annotated, therefore no corpus-wide extraction F1 is reported.

## EXP-V46-01 — Observation type + explainable validation
- Version: v4.6
- Problem: forecast/estimate/observed nature was not clearly exposed to users; confidence scores were insufficiently explainable.
- Hypothesis: local modal-scope classification plus evidence-based confidence will improve auditability without regressing atomic event extraction.
- Changes: per-value observation type, estimate markers, target-year fix, explicit/contextual evidence labels, dashboard Nature badges/labels and confidence explanation.
- Regression dataset: fixed 14-event gold dataset (unchanged).
- Result: 14/14 exact event matches; Precision=1.0, Recall=1.0, F1=1.0; observation_type_accuracy=1.0.
- Test suite: 30 passed (26 prior + 4 v4.6 tests).
- Stress corpus: synthetic 41-page PDF, 500 events; 470 observed, 20 forecast, 10 estimate; 0 unit/currency NaN rows.
- Review-rate note: stricter explainable triage can increase `À vérifier`; this is not treated as an extraction-quality regression because reliability is prioritized over quantity. Review-rate calibration must be evaluated on a real annotated corpus.
- Limitation: confidence is an evidence/triage score, not a calibrated probability of correctness.

## v4.7 — Evidence-Based Validation & Professional UX

**Problem**  
The v4.6 pipeline extracted reliable atomic events but validation was difficult to audit in the user interface. `Type` was not consistently exposed in business exports, conflicts were not a first-class field, and historical statistics could mix forecasts with realized values.

**Hypothesis**  
Centralizing evidence weights and making critical warnings/conflicts override a numeric score will improve auditability without changing the fixed extraction regression benchmark.

**Changes**
- Centralized `VALIDATION_WEIGHTS`.
- Added `validation_status`, `validation_evidence`, `validation_warnings`, `conflict_status`, `observation_type`.
- Green Validé / amber À vérifier / red Rejeté UX.
- Type/status/confidence exports.
- Forecast-aware series and observed-only historical statistics.
- Conflict != duplicate logic covered by tests.

**Automated tests**  
v4.6: 30 passed  
v4.7: 44 passed (+14 tests, +46.7% test-count increase; this is test coverage quantity, not model performance).

**Fixed regression gold**  
14 gold events / 14 predictions. Precision 100%, Recall 100%, F1 100%, Event Exact Match 100%, Observation Type Accuracy 100%. No change versus v4.6 on this fixed regression set.

**Synthetic 41-page stress test**
- Events: 500 (same extraction volume as v4.6 baseline)
- Validé: 112 (22.4%)
- À vérifier: 383 (76.6%)
- Rejeté: 5 (1.0%)
- Types: 470 observed / 10 estimated / 20 forecast
- `nan` units: 0
- Econometric false positives detected by the stress check: 0
- Foreign exchange reserves: 60
- Primary balance: 10
- Engine-only processing: ~0.44 s (~0.0107 s/page), excluding PDF text extraction and Streamlit rendering.

**Comparison with v4.6 stress baseline**  
Validé: 77 -> 112 (+35 observations, +45.5% relative).  
À vérifier: 423 -> 383 (-40 observations, -9.5% relative).  
Rejeté: 0 -> 5 because v4.7 introduces an explicit critical-rejection state.  
These changes are triage-distribution changes, NOT Precision/Recall/Accuracy improvements.

**Conclusion**  
The regression extraction benchmark remains stable while validation becomes more auditable and business-facing outputs preserve event type/status. A larger real gold corpus remains necessary for general performance claims.

## EXP-V48-01 — Conflict semantics and export integrity
- Version: v4.8
- Problem: v4.7 conflict grouping did not distinguish observed/estimated/forecast values; the legacy workspace export collapsed `Rejeté` into `À vérifier` and omitted `Type`.
- Hypothesis: adding observation nature to contradiction/dedup keys and routing the workspace through the canonical business export will remove epistemic false conflicts and restore export integrity without changing extraction output.
- Automated tests: 47 passed (v4.7: 44).
- Fixed regression gold: 14/14 predictions; Precision=1.0, Recall=1.0, F1=1.0, Event Exact Match=1.0, Observation Type Accuracy=1.0. This remains a small regression benchmark, not a general performance claim.
- 41-page synthetic stress PDF: 500 events; 470 observed / 20 forecast / 10 estimate; 0 unit `nan` rows.
- Conflict rows: 383 (v4.7) -> 345 (v4.8), -38 rows (-9.9%) by separating observation nature.
- v4.8 triage distribution: 150 Validé / 345 À vérifier / 5 Rejeté.
- Export verification: `Type` present; statuses preserve Validé / À vérifier / Rejeté.
- Important limitation: the remaining conflicts are not labeled as true/false because the synthetic corpus contains intentionally overlapping and contradictory same-period values. No conflict Precision/Recall is claimed until a hand-annotated conflict gold set exists.

## EXP-V49-01 — Canonical unit serialization regression fix
- Version: v4.9
- Problem: the real v4.8 user export supplied from the Streamlit workflow contained corrupted units on 500/500 rows (`nan %`, `nan % du PIB`, `milliard nan`) even though an earlier internal stress check reported zero. The discrepancy revealed that different UI/export paths were serializing missing pandas values differently.
- Root cause: pandas/NumPy `NaN` is truthy, so `row.get("current_unit") or row.get("current_currency")` could select `NaN` instead of a valid fallback currency. The legacy workspace also maintained a second formatter, allowing UI/export drift.
- Changes: introduced one missing-value-safe measurement label builder; routed `observations.csv` and `series.csv` through it; routed the legacy business workspace table through the canonical observations serializer; added real-NaN regression tests.
- Automated tests: 49 passed (v4.8: 47).
- Fixed 14-event regression gold: unchanged at Precision=1.0, Recall=1.0, F1=1.0, Exact Match=1.0, Observation Type Accuracy=1.0. No extraction-performance gain is claimed.
- Replayed the exact 500-event v4.8 technical stress output through the corrected serializer: corrupted user-facing unit labels 500/500 -> 0/500 (100% elimination of this serialization defect on that output).
- Correct unit distribution: 205 `%`; 95 `% du PIB`; 52 `milliard TND`; 52 `milliard MAD`; 49 `milliard DZD`; 47 `milliard EGP`.
- Triage preserved: 150 Validé / 345 À vérifier / 5 Rejeté. Types preserved: 470 Observé / 20 Prévision / 10 Estimé.
- Limitation: full PDF end-to-end replay was not executed in the current container because the optional runtime dependency `langdetect` is unavailable and internet installation is disabled. The corrected serializer was instead replayed on the exact 500-event technical output generated from the same stress PDF, which directly tests the failing user-export path.


## v4.10 — Document context & period alignment
- Baseline: v4.9 multisource CSV output: 45 extracted events, 37/45 (82.2%) without country metadata.
- Change: CSV `pays` metadata is now carried into ArticleDocument and used as document-level fallback.
- Same input after change: 46 extracted events, 0/46 without country.
- Verified regression cases: `2025 ... X, contre Y en 2024`, January/December comparisons, explicit core inflation.
- Important: 46 vs 45 is not treated as an accuracy improvement. Precision/Recall/F1 require the frozen gold corpus.

## EXP-V411-CLAUSE-AWARE — v4.10 → v4.11

- **Problem:** explicit new indicators could be overwritten by context; forecast modality leaked at sentence level; coordinated clauses could merge distinct concepts; cumulative periods and comparison currencies were not fully local to each value.
- **Hypothesis:** local indicator/value/period/type association will remove these semantic errors without changing stable extraction volume.
- **Changes:** activity-rate/current-account/FDI-variation ontology entries; event-local forecast scope; value-local cumulative periods; safe document-month anchor; currency propagation within monetary comparisons.
- **Dataset:** unchanged multi-source articles test + unchanged 14-event regression gold.
- **Multi-source events:** 46 → 46 (no volume inflation).
- **Missing country:** 0 → 0 (v4.10 fix preserved).
- **Specific corrected cases:** activity rate 45.9/46.1; GDP forecasts 2026/2027; IMF `projette`; current-account 2.0% GDP vs FDI +41%; core inflation December/November; comparison currency propagation.
- **Observation types on multi-source test:** v4.11 = 36 observed / 9 forecast / 1 estimate.
- **Validation triage:** v4.11 = 43 Validé / 3 À vérifier / 0 Rejeté on this test corpus.
- **Regression gold:** Precision=1.0, Recall=1.0, F1=1.0, Exact Match=1.0, Type Accuracy=1.0.
- **Tests:** 60 passed.
- **Conclusion:** semantic association improved on the identified failure classes while the fixed regression benchmark remained unchanged.
- **Limitation:** do not generalize the 14-event score; a larger frozen real gold corpus is still required.

## v4.12 — Consolidated Reliability / regression lock
- Problem: v4.11 fixed clause semantics but regressed temporal granularity on the large PDF (493/505 events ended in M12) and left PDF source empty.
- Hypothesis: document-level month and sentence-level active month were conflated; fixes must be guarded jointly against CSV and PDF regressions.
- Changes: separated document month fallback from active sentence period; explicit/relative/context precedence; source filename fallback; `cette même année`; `projetait`; same-period quarter preservation; inflation average/end-period semantics; stable CSV document IDs; trade balance/coverage/monthly CPI concepts.
- Tests: 75 passed (v4.11 baseline: 60 passed).
- Stress PDF: 505 → 500 events; M12 493 → 60; missing source 505 → 0; econometric noise 0; unit `nan` 0.
- Multi-source regression: country remains complete; Q1 comparisons and forecast scope are explicitly tested.
- Limitation: this development corpus has been used to discover errors; it is not an unbiased held-out set for general F1 claims.

## v4.13 — Real PDF Reliability & Structured Macro Tables

**Problem.** A real 34-page ITCEQ public-debt report exposed four reliability gaps not covered by the synthetic regression set: stale month leakage, stale exported period labels after `de...à...` reassignment, semantically wrong `% du PIB` for a debt-share concept, and total exclusion of a useful macroeconomic annex table.

**Changes.** Added local-month distance guards, canonical period-label recomputation, share-unit correction, safe source normalization, rounding-aware conflict semantics, and a strongly typed parser for the public-debt evolution annex. Generic/econometric annexes remain excluded.

**Baseline v4.12 on the same real PDF.** 27 events; 4 erroneous M01 period labels; 2 wrong `% du PIB` share units; stale exported period for 56.47%; 0 structured Annex-2 events.

**v4.13 on the same real PDF.** 238 events, including 211 unique structured macro-table events after deduplication; 0 erroneous M01 for the identified annual case; 0 wrong state-share units; 56.47% exported as 2001; true 1986 contradiction retained; rounding-only discrepancies not flagged as conflicts.

**Interpretation.** The event-count increase measures coverage only. It is not reported as Precision, Recall, F1 or Accuracy. Existing regression matrices remain green.

## v4.14 — Structured Evidence Validation
- Problem: v4.13 produced 147 Validé / 348 À vérifier / 5 Rejeté on the 500-event stress PDF; many deterministic events were reviewed because validation depended too heavily on an additive score and document-wide conflicts across independent synthetic chapters.
- Hypothesis: dimensional evidence + chapter-aware conflict scope + variation indicators will reduce unnecessary review without changing extraction volume or weakening critical conflict/unit rules.
- Changes: 8 validation dimensions; deterministic association decision; independent-chapter conflict scope; export/import growth ontology.
- Stress dataset: `stress_test_40_pages.pdf`, 500 extracted events both before and after.
- Before: 147 Validé, 348 À vérifier, 5 Rejeté.
- After: 360 Validé, 140 À vérifier, 0 Rejeté.
- Validated share: 29.4% -> 72.0% (+42.6 pp).
- Review share: 69.6% -> 28.0% (-41.6 pp).
- Rejected share: 1.0% -> 0% (-1.0 pp).
- Regression matrix: 500 events, 60 M12, 0 missing source, 0 NaN unit tokens, 0 econometric noise; multisource 55 events, 0 missing country.
- Tests: 87 passed.
- Gold regression: 14/14 exact match, Precision=Recall=F1=1.0 on the fixed 14-event dataset only.
- Limitation: status quality still requires evaluation against a larger held-out manually annotated corpus; validated share is not accuracy.

## v4.15 — Clause-Aware Semantic Binding

**Problem.** The first independent heldout-v1 run exposed structural errors: local country/value binding, clause-level indicator binding, period propagation, modal scope, annex policy, and an Excel NaN crash.

**Baseline (v4.14, heldout-v1, 116 manually specified expected events).**
- TP: 48
- FP: 43
- FN: 68
- Precision: 52.75%
- Recall: 41.38%
- F1: 46.38%

**v4.15 result on the same suite after fixes.**
- TP: 116
- FP: 0
- FN: 0
- Precision: 100%
- Recall: 100%
- F1: 100%

**Important limitation.** This is now a regression benchmark, not a held-out generalization benchmark, because its errors were inspected and used to implement v4.15. Do not use the 100% result as a CV/general performance claim. Generate a fresh heldout-v2 corpus before reporting generalization.

**Non-regression.** 95 tests pass. Legacy 500-event stress test remains 500 events with 0 `nan` units. Annex/Appendix extraction was intentionally disabled according to the updated product requirement.

## v4.18 — Deterministic Coreference Validation

- Problem: v4.17 still sent three correctly resolved contextual observations to review (`il atteignait`, `ce ratio était`, `elles atteignaient`).
- Hypothesis: the relation scorer under-recognized French imperfect/coreferential predicates even when the resolver supplied a unique antecedent.
- Change: extended local relation evidence for imperfect `atteign-` forms and nominal coreference; added an explicit ambiguous-context review override.
- Regression tests: 101 passed.
- Targeted sentence checks: 3/3 audited cases now return `Validé`; deliberately ambiguous counterexample remains `À vérifier`.
- Global Precision/Recall/F1: not claimed here. A new independent gold corpus is still required for generalization metrics.
- Limitation: safe-context validation depends on the upstream resolver correctly setting `ambiguous_context` when multiple antecedents are plausible.

## v4.19 — Gold v2 generalization error fixes
- Baseline: frozen v4.18 first run on Gold Corpus v2.
- Problems exposed: short-PDF rejection, Senegal/Portugal ontology gaps, FCFA/XOF normalization, multi-country clause leakage, period propagation, comparative year inversion, body-table schema rigidity.
- Changes: targeted deterministic fixes only; no heavy LLM and no global confidence-threshold reduction.
- Regression tests after changes: 107 passed.
- Important: Gold v2 is now a development/regression corpus. No post-fix Gold v2 score is claimed as held-out generalization performance.

## v4.20 — Structured Table Evidence & Frequency-Aware Indicators

**Problem.** Gold v2 regression analysis showed two conceptual weaknesses: deterministic body-table cells remained in review despite explicit row/column evidence, and quarterly activity/GDP changes could inherit the annual GDP-growth label. A monthly inflation observation using `ressortait` was also unnecessarily reviewed.

**Hypothesis.** Treating structured table coordinates as explicit evidence, preserving frequency in GDP-growth nomenclature, and recognizing `ressortait` as a strong economic predicate should improve business-status calibration and semantic naming without lowering global validation thresholds.

**Changes.** `explicit_table` is now explicit validation evidence; structured table events receive a dedicated evidence signal; GDP growth is labeled `variation trimestrielle` when quarterly language is explicit; `ressort*` is recognized as a strong value relation.

**Tests.** 111 passed. No blind generalization metric is claimed because Gold v2 was used to identify these issues.

## EXP-V422 — Temporal Relations & Semantic Scope

- **Version:** v4.22
- **Problem:** v4.21 still missed or misbound mixed-frequency and relative-period events on Gold v3 (Canada/New Zealand/Brazil/Japan/Europe centrale).
- **Hypothesis:** the remaining errors came from temporal-relation scope, unaccented PDF language, frequency inheritance, and overly broad forecast scope rather than from validation thresholds.
- **Changes:** expanded relative-period resolver; explicit-period precedence; frequency-aware quarter inheritance; narrower forecast scope; safe contextual coreference; CPI semantic disambiguation.
- **Regression suite:** 116 tests passed.
- **Measured Canada check:** v4.21 user export = 5 events; v4.22 engine on the same supplied PDF = 12 events. This is a recall/coverage correction on a known regression document, not a blind performance result.
- **Regressions:** none detected by pytest.
- **Limitations:** Gold v3 is no longer blind because its errors were used for development. A new untouched corpus is still required for defensible generalization metrics.

## v4.23 — Temporal Anchor Graph + automatic corpus scoring
- Problem: v4.22 chained relative periods through the immediately previous resolved event (2024 → 2023 → 2021; Q2 → Q1 → Q2).
- Hypothesis: sibling relative expressions must resolve from the last explicitly stated discourse period.
- Change: added a stable discourse year/quarter/month anchor that is updated only by explicit periods; relative results do not move it.
- Evaluation tooling: corpus evaluator now supports document-level gold CSVs and includes month in strict event identity/period accuracy.
- Regression tests: 119 passed.
- Known limitation: Gold v3 is a regression corpus after development; a new untouched corpus is required for a generalization claim.

## v4.24 — Dynamic Country Registry
- **Problem:** unseen country names could become `None` because country coverage was hard-coded.
- **Hypothesis:** build country-name coverage from ISO-3166 + Babel instead of benchmark-specific lists.
- **Change:** dynamic FR/EN/AR country registry; separate demonym aliases; ISO3 accepted only as metadata; shared detector across extraction paths.
- **Regression:** 123 tests passed.
- **Gold-v4 smoke check:** Mexico, Turkey, Indonesia, Chile, Norway, Ghana, and South Korea all resolved with 0 missing-country events in the extracted output.
- **Out-of-benchmark checks:** Argentina, Thailand, and Malaysia were resolved without adding benchmark-specific entries.
- **Limitation:** rare demonyms remain an alias-layer problem; canonical country names no longer require code changes.


## v4.25 — Consolidated Generalization Engine

- **Problem:** Gold v4 exposed recurring `None` currencies, hard-coded ISO currency support, a Chile body-table recall failure, temporal phrasing gaps, and semantic continuity errors.
- **Hypothesis:** country/currency/table behavior must be schema/registry-driven rather than benchmark-specific.
- **Changes:** dynamic ISO-4217 + CLDR currency registry; compact local currency resolution; generic body-table schema parser; extended temporal relations; explicit-frequency precedence; current-account sign normalization; inflation subtype continuity fix.
- **Regression suite:** 134 tests passed, 0 failed.
- **Gold v4 development regression:** v4.24 strict canonical event matching = 58 TP / 19 FP / 36 FN (Precision 75.3%, Recall 61.7%, F1 67.8%); v4.25 after development = 94 TP / 0 FP / 0 FN on 94 annotated events.
- **Interpretation:** this is a regression improvement, **not** a blind generalization result, because Gold v4 errors were used to develop v4.25.
- **Limitation:** a new unseen Gold corpus is still required for defensible generalization metrics.


## v4.26 — Stabilisation globale
- Base: v4.25.
- Problème: le parser de tableaux multi-pays pouvait utiliser le pays du chapitre pour les lignes suivantes.
- Hypothèse: une hiérarchie de contexte local-first empêche cette contamination.
- Changement: pays explicite de ligne prioritaire et devise implicite résolue avec ce pays.
- Tests: 136 passed, 0 failed.
- Limitation: ce résultat est une non-régression logicielle, pas une mesure de généralisation sur un nouveau Gold blind.
