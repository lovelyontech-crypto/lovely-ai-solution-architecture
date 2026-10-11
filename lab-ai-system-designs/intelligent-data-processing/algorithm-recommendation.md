# AI Algorithm & Model Recommendation Report: Bharat Equity Intelligence Platform (AI-Powered Indian Stock Market Intelligence)

> **Primary Paradigm**: Hybrid AI. Deterministic analytics engines (no ML) + Supervised distributional forecasting (pooled LightGBM quantile regression with conformal calibration, gated by naive baselines) + Cross-sectional learning-to-rank (gated) + Grounded generative AI (fact-sheet-constrained LLM narrative with a deterministic citation gate) + Hybrid lexical/semantic retrieval + Lightweight NLP classifiers for filings and news
> **Problem Statement Ref**: [`BRD AI-Powered Indian Stock Market Intelligence Platform.pdf`](BRD%20AI-Powered%20Indian%20Stock%20Market%20Intelligence%20Platform.pdf) (v1.0, 11 Oct 2026, 155 pages)
> **Target Environment**: Python pipeline on GitHub Actions (`ubuntu-latest`, CPU only, 3 weekday runs + manual dispatch), persistent CSV store on a private `data` branch, file-based model registry (`models/model_registry.json`), Gmail SMTP delivery. No cloud account and no always-on server in v1.0.
> **Skill**: [`.agents/skills/ai-algorithm-selector/SKILL.md`](../../.agents/skills/ai-algorithm-selector/SKILL.md) · Template: [`.agents/skills/ai-algorithm-selector/templates/algorithm-recommendation-template.md`](../../.agents/skills/ai-algorithm-selector/templates/algorithm-recommendation-template.md)

Statements below follow the BRD's tagging where it matters: **[BRD]** = taken from the BRD with its section or requirement ID; **[A]** = assumption made in this report that must be confirmed; **[R]** = recommendation of this report.

---

## 1. Executive Summary

The platform's job is to give Indian retail and professional investors research on NIFTY 100 stocks (growing to NIFTY 500 and F&O names) where every number is traceable to a filing, a formula and a timestamp, and where forecasts are honest about uncertainty [BRD §1–3]. The defining design rule is that **only deterministic code and validated models produce numbers; the language model only explains them** [BRD §15, G-3, FR-060]. Most of the product is therefore not machine learning at all: ratios, technical indicators, DCF and multiples valuation, stop-loss and sizing, Black-Scholes-Merton Greeks, option payoffs and portfolio VaR are fixed formulas with golden tests [BRD §9–12, 10.9.1]. This report recommends ML only for the five places where it adds measurable value over formulas and rules.

**The recommended approach is a hybrid of five components.** (1) For 1/3/6/12-month statistical price ranges (FR-056), a **pooled cross-sectional LightGBM quantile-regression model on point-in-time features, calibrated with Conformalized Quantile Regression (CQR)**, evaluated against the BRD's mandatory naive baselines (B0 no-change, B1 drift random walk with EWMA/GARCH volatility, B2 market-beta). A regularised linear factor model is the close alternative and wins any tie under the BRD's "simplest model that passes the gate" rule [BRD §10.9]. (2) For the gated "which stocks deserve research" ranking (FR-183), **LightGBM LambdaRank on sector-neutral factor scores**, judged on rank IC and after-cost decile spread. (3) For the AI explanation layer, a **fact-sheet-constrained LLM** at temperature 0 with JSON-schema output, followed by a **deterministic citation gate** that drops any sentence whose numbers or named entities do not match an engine fact or a retrieved source span [FR-060, §15.2]. (4) For glossary search and filing retrieval, **hybrid BM25 + multilingual dense embeddings** with Hindi/Hinglish transliteration [FR-092]. (5) For filings and news, **rules first, then TF-IDF + logistic regression, with LLM span-verified extraction** only for governance flags [FR-025, FR-042, FR-043].

The honest expectation matters as much as the model choice. Return prediction for liquid large caps has very low signal-to-noise, so **it is likely that point forecasts will not beat the no-change baseline with Diebold-Mariano p < 0.05 for most segments**, and the publication gate will then show only the clearly labelled baselines plus fundamental scenarios, exactly as the BRD intends [BRD §10.6, BO-06]. Interval calibration (80% coverage inside 75–85%) is achievable with conformal methods even when median skill is absent. All components fit the GitHub Actions budget: the full T1 training set is about 250,000 stock-days [BRD §14.4.9], LightGBM trains in minutes on CPU, and inference for 100 stocks takes seconds. **Overall confidence: Medium** (High for the architecture, deterministic engines, retrieval and NLP choices; Low-to-Medium that any return-forecasting challenger passes the publication gate).

---

## 2. Business Problem Analysis

* **Business Objective**: Make company research on NSE/BSE stocks faster, traceable and honest about uncertainty, through six engines (fundamental, technical, market/macro, news/events, valuation/forecasting, risk/derivatives) delivered as an emailed HTML research report three times each weekday [BRD §1, §16.4].
* **Current Process**: Investors stitch together exchange filings, free ratio websites, broker apps, unverified social-media tips and videos; stops are chosen "by feel"; there is no record of reasoning and no feedback on whether past views were right [BRD §7.1].
* **Pain Points**: P1 scattered research (hours per stock); P2 unregistered tips with no stated assumptions; P3 indicators presented as buy/sell signals; P4 derivatives used without understanding payoff and expiry risk; P5 English-only jargon; P6 no public forecast-accuracy record [BRD §2].
* **Expected Outcome**: One cited report in minutes; explicit bull/base/bear scenarios with invalidation conditions instead of single targets; a forecast ledger compared against naive baselines; bilingual (English/Hindi) explanations [BRD §2 Opportunity].
* **Success Criteria**:
  * *Business KPIs*: BO-01 50% faster research vs public-source baseline; KPI-10 80% task completion; KPI-11 +20 pp terminology comprehension; KPI-17 98% scheduled-run success; KPI-21 99% emails submitted [BRD §3, §20].
  * *Integrity KPIs*: KPI-01 100% numeric claims cited; KPI-03 100% golden-test pass; NFR-041 zero unsupported numbers on the hallucination test set [BRD §17, §20].
  * *Predictive KPIs*: KPI-05 skill vs no-change > 0 with significance for any published segment; KPI-06 80%-interval coverage 75–85%; TST-FC-04 rank IC significant at 5% before rankings are published [BRD §10.6, §19.1].
* **Stakeholders**: Business sponsor; product manager; compliance officer (and RA principal officer if registered); external securities counsel; quantitative research lead (owns model risk and backtest sign-off); data engineering lead; engineering lead; QA lead; personas Asha (long-term investor), Rohan (swing/options trader), Meera (student), Vikram (analyst) [BRD §4].
* **Constraints**:
  * *Regulatory*: SEBI RA Regulations (amended 16 Dec 2024) and FAQs of 23 Jul 2025 treat named-stock forecasts, targets, stops and ranked lists as research services; AI-use disclosure required; until OD-01 (RA route) and OD-22 (recipients) close, named-stock forecasts go to the sponsor only [BRD §18, C-01, C-12].
  * *Data*: licensed vendor only, no scraping, no mock data in production; the licence must permit storage and (by this report's reading) **model training on derived data** [BRD §5.6, §14, OD-02].
  * *Compute*: GitHub-hosted CPU runners; incremental run p95 under 20 minutes, hard timeout 60 minutes; about 2,000 Actions minutes per month on GitHub Free for a private repository [BRD NFR-101, §15.5.4].
  * *Explainability*: every score, valuation and forecast must open an evidence inspector with inputs, formula, sources and model version (NFR-040, FR-062); no "buy/sell/target" labels [BRD §16.1].
  * *Reproducibility*: every prediction reproducible from recorded data checksums and model version (NFR-097, TST-GHA-09).
  * *Latency*: batch only in v1.0; no real-time serving requirement.

---

## 3. AI Suitability Assessment

The BRD already decides, correctly, that most capabilities must not use ML. This report agrees and maps every capability to the simplest adequate technique.

| Capability (BRD ref) | Recommended technique | ML needed? | Reason |
| :--- | :--- | :--- | :--- |
| Ratios, scorecard, peer percentiles (FR-020 to FR-026) | Deterministic formulas (Appendix A.2), percentile ranks | **No** | Defined accounting identities; must be reproducible to 4 d.p. (TST-CALC-01) |
| Technical indicators and summary states (FR-030 to FR-035) | Fixed formulas and rule set (Appendix A.4–A.6) | **No** | Must match TA-Lib within 1e-6; summary is a rule, not a prediction |
| Support/resistance zones (FR-032) | Deterministic swing-point clustering (A.5) | **No** | BRD requires determinism; DBSCAN-style clustering adds nothing auditable |
| Valuation (DCF, multiples, DDM, P/B-ROE) (FR-050 to FR-055) | Deterministic models with sensitivity grids | **No** | "No ML replaces valuation" [BRD §10.9.1] |
| Stops, sizing, R:R, VaR/ES (FR-070 to FR-076) | Closed-form formulas, historical simulation | **No** | Calculators over user inputs; regulatory boundary (C-02) |
| Greeks, IV, payoffs (FR-080 to FR-086) | BSM / Black-76, Newton-Raphson with bisection | **No** | Exactness tests (TST-DER-01/02) |
| Event "already priced in" and causation guard (FR-044, A.7) | Market-model event study (OLS) + significance test | **No (classical statistics)** | Rule fixed in A.7: |t_CAR| > 1.96 and no other material event |
| Data quality V1–V19 (§14.3) | Rule engine | **No** | Thresholds are explicit; an anomaly model would add unexplainable rejections |
| News confirmation status (FR-043) | Rule by source tier | **No** | Defined entirely by source tier [BRD §9.4] |
| **Horizon price distribution 1/3/6/12M (FR-056, FR-184)** | **Supervised quantile regression + conformal calibration** | **Yes, but gated** | Only a model can produce calibrated conditional intervals; must beat B0/B1 out of sample |
| **Volatility forecast for intervals and stops (B1, §11.2)** | **EWMA λ=0.94 vs GARCH(1,1)/GJR-GARCH** | **Yes (econometric)** | Volatility is forecastable; drives interval width and volatility-adjusted stops |
| **Stock ranking / daily research queue (FR-014, FR-183)** | **Factor scores + learning-to-rank** | **Yes, gated** | Cross-sectional ordering; FR-014 notability score stays rule-based (never expected return) |
| **AI narrative, bull/bear thesis, company overview (FR-060, §16.3)** | **Grounded LLM generation + deterministic citation gate** | **Yes (GenAI)** | Free-text summarisation of cited documents; numbers never generated by the LLM |
| **Glossary search and "ask about a term" (FR-092, FR-094)** | **Hybrid BM25 + multilingual embeddings; RAG restricted to glossary/methodology** | **Yes (retrieval)** | Hindi/Hinglish/transliterated queries defeat pure keyword search |
| **Filing classification, entity linking, governance flags (FR-042, FR-043, FR-025)** | **Rules → TF-IDF + LR → LLM span-verified extraction** | **Yes (NLP), selectively** | Unstructured filing text; ≥95% precision targets |

* **Why ML is recommended for the five "Yes" rows**: they involve conditional uncertainty estimates, cross-sectional ordering, or unstructured bilingual text, none of which a formula can express. Each has a measurable acceptance test in the BRD (TST-FC-02/03/04, TST-AI-01 to 05, FR-025/043/092 thresholds).
* **Why ML is NOT recommended elsewhere**: the BRD's integrity scoreboard (BO-03, KPI-03) demands 100% reproducibility against golden tests. Replacing formulas with learned approximations would make that impossible and would weaken the regulatory defence that "recommendations are corroborated by data and analysis" [BRD §18.1].
* **Default when a model fails**: the BRD's fallback is explicit and correct. If no challenger passes the gate, publish only the labelled naive baseline (B1 range) and the deterministic fundamental scenarios, with status `model_not_validated` [BRD §10.9.3].

---

## 4. Problem Classification

* **ML Task Category**: Multi-task hybrid:
  1. **Probabilistic time-series forecasting / quantile regression** of h-day log returns (h ≈ 21, 63, 126, 252 trading days) per stock: the core predictive task.
  2. **Conditional volatility forecasting** (econometric time series).
  3. **Learning-to-rank** across the stock universe per date (gated).
  4. **Retrieval-augmented, grounded text generation** (summarisation of filings and engine fact sheets).
  5. **NLP classification and information extraction**: filing category (multi-class), governance flag extraction (span extraction), entity linking (named-entity disambiguation to ISIN).
  6. **Semantic search** over a bilingual glossary.
* **Data Modality**: Structured time series (daily OHLCV, adjusted and total-return series), point-in-time tabular fundamentals (quarterly), event streams (corporate actions, announcements), unstructured text and PDFs (filings, annual reports, licensed news), bilingual editorial content (English/Hindi glossary).
* **Learning Paradigm**: Supervised learning (quantile regression, ranking, text classification) + classical econometrics (GARCH) + distribution-free calibration (split/rolling conformal) + Foundation-model generation via API with RAG (no fine-tuning) + pre-trained embeddings (transfer learning, no fine-tuning in MVP).
* **Execution Mode**: Offline batch. Inference runs inside each of the three weekday pipeline runs (09:00, 13:00, 16:00 IST) and on manual dispatch; training runs in a separate monthly or drift-triggered workflow outside the research slots [BRD FR-140, §10.9.4]. No online learning; a new daily candle never triggers retraining.
* **Classification Reasoning**: The BRD's forecast output is a **distribution** (median plus 50%/80% intervals), not a point or a direction, so the correct framing is quantile regression scored with pinball loss/CRPS and coverage, not classification of up/down moves. Ranking is evaluated cross-sectionally by rank IC, so it is a learning-to-rank problem, not per-stock regression. Narrative generation is constrained to restating engine facts, so it is RAG with a verifier rather than open generation or fine-tuning.

---

## 5. Data Assessment

### Data Type
* **Time series**: daily OHLCV for T1 (about 100 stocks), 10-year lookback; raw, split/bonus-adjusted and total-return series kept separate [BRD §14.4.1–14.4.2]. Intraday history is **not** stored in v1.0 (OD-25), so intraday models are out of scope.
* **Tabular point-in-time**: quarterly and annual statements (standalone and consolidated, as-reported and restated, with `filing_ts_utc`), shareholding and pledges, index membership with effective dates [BRD FR-020, FR-024, §6.1].
* **Events**: corporate actions, exchange announcements, macro releases with vintages (RBI, MoSPI, FBIL), derivatives contract masters.
* **Text**: exchange filings (PDF/XBRL), annual reports, investor presentations, licensed news headlines/abstracts (Phase 2), 300-term bilingual glossary.

### Data Quality

* **Dataset Size**: about 250,000 stock-days for T1 daily equity over 10 years (about 50 MB CSV) [BRD §14.4.9]; about 20 quarterly fundamentals × 100 companies × ~150 line items; NIFTY 500 in Phase 2 multiplies the cross-section by 5. Small by ML standards and far below anything that needs distributed training.
* **Features**: about 60–120 engineered numerical features per stock-date (technical, fundamental, factor, macro and regime features; see §9), all derived from the deterministic engines' outputs, plus sector as a categorical feature.
* **Label Availability**: Self-labelled. Targets are realised forward log returns at each horizon, available after the horizon matures. **Labels overlap heavily**: a 252-day target on consecutive days shares 251 days of path, so the effective number of independent observations per stock is roughly 10 years / horizon. For the 12-month horizon on 100 stocks that is on the order of 1,000 effectively independent observations [A]. This, not row count, is the binding constraint.
* **Missing Values**: Prices: low after validation (V1–V5). Fundamentals: moderate and structured: missing quarters, half-yearly cash-flow statements, IPOs with short history [BRD §6.3, §9.1]. The BRD forbids silent imputation (G-2, V2).
* **Class Imbalance**: Not applicable (regression and ranking). The analogue is **regime imbalance**: few crash periods (e.g., March 2020) in 10 years, so tail quantiles are poorly estimated.
* **Outliers**: Fat-tailed returns, circuit-limit days, event gaps, corporate-action artefacts (caught by V4/V8). Heavy-tailed targets argue for quantile loss and per-date winsorisation of features.
* **Historical Depth**: 10 years daily prices, 5–10 years fundamentals [BRD A-07]. The publication gate needs a **≥3-year final hold-out never used for tuning** [BRD §10.6], which leaves about 6–7 years for walk-forward development.
* **Survivorship and point-in-time**: delisted and merged stocks must stay in the backtest universe and index membership must be historical [BRD §6.1, §10.5]. Whether the chosen vendor supplies delisted history is an open risk (OD-02) [A].
* **Overall Data Quality**: **High for integrity** (validated, versioned, provenance on every row) but **Low for predictive signal**: low signal-to-noise, overlapping labels and a small effective sample. This is the main reason to prefer simple, regularised models and to expect many segments to fail the gate.

---

## 6. Recommended Learning Paradigm

* **Selected Paradigm**: **Hybrid AI with a deterministic core and gated ML at the edges**

  | Layer (BRD pillar) | Paradigm | Components |
  | :--- | :--- | :--- |
  | Calculation core (P3) | Deterministic | Ratios, indicators, valuation, risk, derivatives, event study |
  | Forecasting (P3) | Supervised quantile regression + conformal calibration + econometric volatility | Baselines B0/B1/B2, EWMA/GARCH, LightGBM-QR + CQR, Elastic Net QR |
  | Ranking (P3, gated) | Supervised learning-to-rank | Factor z-scores + LightGBM LambdaRank |
  | Interpretation (P4) | Foundation model via API, RAG, no fine-tuning | Fact-sheet prompting, structured output, citation gate, prohibited-language and causation filters |
  | Retrieval and NLP (P1/P4) | Transfer learning (frozen pre-trained encoders) + classical ML + rules | BM25 + multilingual embeddings, TF-IDF + LR, alias-dictionary entity linking |

* **Justification**:
  * **Supervised quantile regression** matches the BRD's output contract (median + 50%/80% intervals, pinball loss/CRPS for selection) [BRD §10.6, §10.9.3]. **Conformal calibration** turns any quantile model into one with finite-sample coverage guarantees under exchangeability and, with rolling recalibration, keeps 80% coverage inside the 75–85% band that NFR-043 monitors.
  * **A pooled cross-sectional model** (one model across all stocks, features normalised per date) is preferred over per-stock models because per-stock series give only tens of independent long-horizon observations. The BRD states the same preference [BRD §10.9.1 notes].
  * **RAG without fine-tuning** is correct because the LLM's job is restating verified facts and summarising cited documents, not learning new knowledge; fine-tuning would add cost and an unauditable artefact while the citation gate already enforces grounding [SKILL operating principle: RAG over training for knowledge retrieval].
* **Alternatives Considered**:
  * **Deep sequence models (LSTM, GRU, Temporal Fusion Transformer, PatchTST, DeepAR)**: evaluated in the validation track as the BRD requires (C-14, FR-180) but **not expected to pass**. About 100 series of daily returns with low signal-to-noise is far below the data regime where these models beat gradient boosting or linear models; they are harder to explain (NFR-040) and slower to train on CPU runners. Re-evaluate at NIFTY 500 scale in Phase 2.
  * **Reinforcement learning (portfolio or trade policies)**: rejected. Order execution, algorithmic trading and portfolio management are out of scope [BRD §5.2], and an RL policy would produce trading calls that are regulated research (REG-01).
  * **Unsupervised clustering / anomaly detection**: not needed for MVP. Peer sets come from the index provider's industry classification (FR-022), and data-quality checks are rules. Correlation clusters for portfolio risk (FR-076, Phase 2) can use hierarchical clustering on return correlations, a deterministic computation.
  * **LLM fine-tuning (LoRA/QLoRA)**: rejected for MVP. No labelled corpus exists, the citation gate gives stronger guarantees, and fine-tuning needs GPUs that the v1.0 architecture does not have.
  * **Financial-news sentiment scoring for forecasting features**: deferred. It requires licensed sentiment or news data (C-05, D-03, Phase 2) and adds look-ahead risk from imprecise timestamps.

---

## 7. Top Three Algorithms

The ranking below is for the core predictive task (FR-056 horizon distributions). The supporting components are specified in §7.4.

### Rank 1 (Recommended): Pooled LightGBM Quantile Regression + Conformalized Quantile Regression (CQR)
* **Model Category**: Gradient-boosted decision trees with quantile (pinball) loss, plus distribution-free conformal interval calibration.
* **Specific Implementation**: `lightgbm` (`objective="quantile"`, one model per quantile τ ∈ {0.10, 0.25, 0.50, 0.75, 0.90} per horizon; monotone constraints optional for momentum/volatility features) on **volatility-normalised forward log returns** (target = r_h / (σ̂_EWMA·√h)); intervals rescaled by the volatility forecast; then **split CQR** on the most recent calibration window inside each walk-forward fold, with **rolling recalibration** at each monthly retrain. Non-crossing enforced by sorting predicted quantiles. Shallow trees (`num_leaves` 7–31, `min_data_in_leaf` ≥ 200, strong `lambda_l2`, `feature_fraction` 0.5–0.8, early stopping on purged validation).
* **Why Recommended**:
  * *Business and data fit*: one pooled model learns from all ~100 (later ~500) stocks at once, handles native NaN for missing fundamentals without imputation (consistent with G-2), captures non-linear interactions such as momentum × volatility regime, and produces exactly the median + interval contract required by FR-184.
  * *Calibration and honesty*: CQR keeps the 80% band near nominal coverage even if the quantile model is mis-specified, directly serving BO-05 and NFR-043; normalising by volatility puts the hard part (volatility) on the econometric model where it is forecastable.
  * *Explainability and production readiness*: TreeSHAP gives per-forecast feature attributions for the evidence inspector (FR-062); models serialise to small text files that fit the CSV/Git store and the file-based registry (FR-181); training on ~250k rows takes minutes on a 2-vCPU runner.

### Rank 2 (Alternative): Regularised Linear Factor Model (Elastic Net / Linear Quantile Regression) + CQR
* **Model Category**: Penalised linear model on cross-sectionally standardised factor scores (value, quality, momentum 12-1, low volatility, size, earnings revisions where licensed, sector dummies), with linear quantile regression for the interval and the same conformal calibration.
* **Specific Implementation**: `scikit-learn` `ElasticNetCV` (purged time-series CV) for the median and `QuantileRegressor` (or `statsmodels` `QuantReg`) for the quantiles; features rank-gauss transformed per date and sector-neutralised.
* **Why Alternative**:
  * *When to switch*: if LightGBM's out-of-sample pinball loss is not significantly better (Diebold-Mariano on loss differentials) than this model's, **choose this model**. The BRD's tie rule favours the simpler model [§10.9], and in low signal-to-noise equity data linear factor models are often as good and more stable [A]. This is also the natural model for the 6/12-month horizons, where the BRD lists factor models and quantile regression with conformal calibration as candidates [§10.9.1].
  * *Trade-off vs Rank 1*: fully transparent coefficients (easiest for compliance and RA review, REG-04) and more robust under regime change, but cannot capture interactions or non-linear threshold effects.

### Rank 3 (Baseline, mandatory): Naive baselines B0/B1/B2 with EWMA or GARCH(1,1) volatility
* **Model Category**: Random walk (no-change), log-price random walk with drift = long-run ERP assumption, CAPM-style market-beta model; volatility from EWMA (λ = 0.94) or GARCH(1,1)/GJR-GARCH if it validates.
* **Specific Implementation**: closed form as specified in BRD §10.4, P_{lo,hi} = P_0·exp(μh ± z_α·σ·√h); `arch` package for GARCH estimation per stock with a pooled-parameter fallback.
* **Purpose**: These are the benchmarks every challenger must beat (TST-FC-02) and the **published fallback** when nothing passes. Their 80% interval coverage must itself be measured: unconditional normal intervals under-cover in fat-tailed periods, so apply the same conformal correction to B1 intervals. This often makes the calibrated baseline the best publishable product [A].

### 7.4 Supporting components (one recommended choice each)

| Task (BRD ref) | Recommended | Alternative / baseline | Acceptance test |
| :--- | :--- | :--- | :--- |
| Volatility forecast (§10.4, §11.2) | **EWMA λ=0.94** as default; promote **GJR-GARCH(1,1)** with Student-t errors only if QLIKE loss is lower out of sample | Rolling 20/60-day realised volatility | QLIKE / MSE on realised variance; interval coverage |
| Stock ranking (FR-183, gated) | **LightGBM LambdaRank** (`objective="lambdarank"`, query = date, relevance = forward-return quintile) on sector-neutral factor z-scores | Equal-weight composite factor score (value + quality + momentum + low-vol) | Rank IC > 0 with significance at 5%, after-cost decile spread, turnover, 2× cost sensitivity (TST-FC-04/05) |
| Daily research queue (FR-014) | **Deterministic notability score** (new results, estimate changes, abnormal volume z-score, event flags) | n/a | Rule tests; never ranked by expected return [BRD FR-014] |
| AI narrative and bull/bear thesis (FR-060, §16.3) | **API LLM, temperature 0, JSON-schema output** with sentence-level `fact_ids`/`source_ids`; prompt contains only the fact sheet and retrieved spans; **deterministic citation gate** (number/date/entity parser with unit normalisation, exact match); >20% failed sentences → regenerate once → template report | Template-only report (no LLM) | TST-AI-01 zero unsupported numbers on 500 adversarial fact sheets; TST-AI-02/03/04 |
| Model choice for the LLM (OD-12) | A mid-tier, low-latency API model with contractual no-training and acceptable data-residency terms; evaluate 2–3 providers on TST-AI-01 to 05 and choose the cheapest that passes | Smaller model for classification tasks | Pass rate, cost per report (KPI-15), latency within run budget |
| Glossary search and Q&A (FR-092, FR-094) | **Hybrid: BM25 (`rank_bm25`) + multilingual dense embeddings** (e.g., `intfloat/multilingual-e5-small` or `BAAI/bge-m3`, CPU, ONNX), reciprocal rank fusion; Hinglish/Devanagari normalisation via `indic-transliteration`; answers restricted to glossary and methodology pages | BM25 + alias table only | Top-3 hit rate ≥ 95% on 200 queries; ≥ 98% answers cite an entry; zero stock recommendations |
| Filing/document retrieval for company overview (§9.1) | Page-level chunking of annual reports and presentations, same hybrid retriever, optional cross-encoder reranker (`bge-reranker-v2-m3`) only if top-k precision is short | BM25 only | Citation resolves to the page span containing the fact (TST-AI-02) |
| Filing classification (FR-042) | **Map exchange-provided announcement categories by rule**; residual "general/others" items via **TF-IDF + Logistic Regression** | LLM zero-shot classification | Per-class precision on a labelled sample; 15-minute latency budget |
| News entity linking (FR-043, Phase 2) | **Alias dictionary from the security master** (ISIN, symbols, legal and short names, former names) + fuzzy matching (`rapidfuzz`) + context rules; unlinkable → not attached | Embedding similarity disambiguation | Precision ≥ 95% on labelled sample |
| Governance flags (FR-025) | **Rule/keyword detectors** (auditor resignation, qualification, penalties, rating actions) + **LLM extraction that must return a verbatim source span**, verified by exact string match against the filing text; low-confidence → human review queue | Rules only | Precision ≥ 95% on 200 labelled filings; every flag links to its paragraph |
| Prohibited language and causation guard (§15.2 rules 6, A.7) | **Lexicon + regex filters (English and Hindi)** on generated text; causal phrases allowed only when the A.7 event-study flag is true | Small TF-IDF + LR phrase classifier if lexicon recall is short | TST-AI-03 zero prohibited phrases; TST-AI-04 zero "caused" claims |

---

## 8. Algorithm Comparison Table

Scored for the core FR-056 forecasting task. The fourth column records the deep-learning candidates the BRD requires to be evaluated (C-14).

| Evaluation Dimension | Rank 3 Baseline (B1 drift + EWMA/GARCH, conformal-corrected) | Rank 1 Recommended (Pooled LightGBM-QR + CQR) | Rank 2 Alternative (Elastic Net / Linear QR factor model + CQR) | Evaluated only (LSTM / GRU / TFT / PatchTST) |
| :--- | :--- | :--- | :--- | :--- |
| **Business Fit** | High (always-available, honest fallback) | High (produces full FR-184 contract, explainable) | High (most defensible for RA review) | Low (no presumption of superiority; harder to defend) |
| **Data Suitability** | High (needs only prices) | High (handles NaN, mixed frequencies, ~250k rows) | High (robust with small effective sample) | Low (~100 noisy series; overfits) |
| **Expected Accuracy** [A] | Skill vs B0 ≈ 0 by construction; 80% coverage in band after conformal correction | Pinball-loss improvement vs B1 small (low single-digit %); rank IC ≈ 0.02–0.05 at 1–3M; may fail DM test in many segments | Similar to Rank 1 at 6–12M horizons; slightly worse at 1–3M if interactions matter | Unlikely to beat Rank 1 out of sample at T1 scale |
| **Interpretability** | Native (formula) | High (TreeSHAP per forecast) | Native (coefficients) | Low (attention/IG approximations only) |
| **Scalability** | High | High (NIFTY 500 / 2,000 stocks trivially) | High | Medium (CPU training time grows quickly) |
| **Training Time** (2-vCPU runner) | Seconds (GARCH per stock: about 1–2 min total) | Minutes (5 quantiles × 4 horizons × walk-forward folds) | Seconds to minutes | Tens of minutes to hours; may exceed 60-min job timeout |
| **Inference Latency** (100 stocks, batch) | < 1 s | < 2 s | < 1 s | Seconds |
| **Computational Cost** | $ | $ | $ | $$–$$$ (needs GPU, which GitHub-hosted standard runners do not provide) |
| **Hyperparameter Complexity** | Low (λ, GARCH order) | Medium (leaves, regularisation, early stopping; tune with Optuna under purged CV and record every trial) | Low (α, l1_ratio) | High |
| **Production Readiness** | High | High (mature library, small text artefacts, SHAP) | High | Medium |

**Selection rule [R]**, implementing BRD §10.9: per horizon and universe segment, compute mean pinball loss/CRPS on the purged walk-forward folds, then on the untouched ≥3-year hold-out. Publish the **simplest** model that (1) beats B0 with Diebold-Mariano p < 0.05 after False Discovery Rate correction across all variants tried, and (2) has 80% coverage in [75%, 85%] and 50% coverage in [45%, 55%] [TST-FC-02/03]. Otherwise publish the conformal-corrected B1 range labelled as naive, with status `model_not_validated`.

---

## 9. Feature Engineering Recommendations

All features are computed by the deterministic engines and the feature store (`processed/features/<FEATURE_SET_VERSION>/`) with point-in-time discipline. A feature for date *t* may use only data whose timestamp is ≤ the run's as-of time on *t* [BRD §10.5, FR-138].

1. **Missing Value Handling**: Do **not** impute fundamentals (BRD G-2, V2). Pass NaN to LightGBM (native missing-value branch) and add explicit `is_missing_<group>` and `quarters_of_history` indicators. For the linear model, use per-date cross-sectional median imputation **inside the training pipeline only**, plus the missing indicators, and record it in the model card. Stocks failing minimum-history rules (IPO under 2 quarters, under 252 bars) return `insufficient_data` rather than a forecast (FR-057).
2. **Encoding**: Sector/industry (index-provider classification, about 15–20 levels) as LightGBM native categorical; one-hot for the linear model. Market-cap bucket (AMFI) as ordinal. No target encoding (leak risk with overlapping labels).
3. **Scaling & Normalization**: Cross-sectional **rank-gauss (quantile-to-normal) transform per date** for all stock-level features, which removes level drift across years and makes features comparable across regimes. Optional sector neutralisation (subtract sector median per date) for factor features. Targets: volatility-normalised forward log returns.
4. **Feature Selection**: Start from a pre-registered, economically motivated list (below) to limit multiple testing; prune with grouped permutation importance and mean |SHAP| on purged validation folds; drop features whose importance sign flips across folds. Record every variant tried for the FDR correction [BRD §10.5].
5. **Feature Creation** (pre-registered families):
   * *Momentum and reversal*: 1M, 3M, 6M, 12-1M total returns; distance from 52-week high; RS vs NIFTY 50 and sector at 63/252 days (FR-033).
   * *Volatility and risk*: EWMA and GARCH σ̂, ATR%, 20/60/250-day realised vol, vol-of-vol, beta (2-year weekly, Blume-adjusted), max drawdown, gap frequency (FR-034).
   * *Technical states*: trend state, RSI(14), MACD histogram slope, Bollinger bandwidth percentile, volume z-score vs 20-day average (FR-031/035 outputs as numbers, not labels).
   * *Value*: earnings yield (1/PE), book yield, EV/EBITDA (non-financials only), FCF yield, dividend yield; P/B-ROE gap for financials.
   * *Quality*: ROE, ROCE, gross/EBITDA margin level and 4-quarter change, OCF/EBITDA (3-year), accruals, D/E; bank-specific NIM, GNPA, CASA for financials.
   * *Growth and trend*: TTM revenue/PAT growth, FR-023 trend label encoded as −1/0/+1, quarters since last results.
   * *Ownership*: promoter %, pledge % and quarterly changes, FPI/DII change (FR-024).
   * *Events*: days to next results or ex-date, recent confirmed corporate events (Tier-1 only), A.7 abnormal-return flags.
   * *Market regime and macro* (common to all stocks on a date): NIFTY 50 trend state, breadth (% of NIFTY 500 above 200-DMA), India VIX percentile where licensed, repo-rate change, 10-year G-sec yield change, INR/USD 3-month change. Use **release dates, not reference dates**, for macro values (vintage tracking, V18).
   * *Liquidity*: 20-day median traded value, Amihud illiquidity.
6. **Outlier Handling**: Per-date winsorisation of raw features at the 1st/99th percentile before rank-gauss; targets left unwinsorised for quantile models (quantile loss is robust) but winsorised at 1/99 for the Elastic Net median model. Quarantined bars (V3/V4) excluded from both features and labels.
7. **Class Balancing**: Not applicable. Instead, report all metrics **by regime** (trend up, trend down, high volatility), sector and period, as BRD §10.9.2 requires, so a model that works only in bull markets is visible.
8. **Data Augmentation**: **None** in training data (the BRD prohibits synthetic records in production datasets, §5.6). Block bootstrap is allowed **only in evaluation**, to put confidence intervals on skill scores and IC.
9. **Domain-Specific Processing**:
   * *Corporate actions*: features from split/bonus-adjusted series; return targets from total-return series; full-symbol feature rebuild on any new adjustment factor (FR-138).
   * *Labels*: forward log return from the close of *t* to the close of *t+h* on the exchange trading calendar; label timestamp = *t+h*; samples whose label window crosses a suspension or delisting use the delisting return where available, else drop with a logged reason (survivorship control).
   * *Text*: page-level chunking with page numbers kept for citations; Unicode NFC normalisation; Devanagari ↔ Latin transliteration aliases for glossary terms; no stop-word removal for embeddings.

---

## 10. Evaluation Metrics

* **Primary Optimization Metric (forecasting)**: **Mean pinball loss across τ ∈ {0.1, 0.25, 0.5, 0.75, 0.9}** (approximating CRPS) on volatility-normalised returns, per horizon. Selection and early stopping use this, not accuracy of direction.
* **Publication-gate metrics** [BRD §10.6, TST-FC-02/03]: skill score 1 − MAE_model/MAE_B0 on log price; **Diebold-Mariano test** vs B0 and B1 (HAC variance with lag = horizon − 1 because of overlapping forecasts; p < 0.05 after FDR correction); **empirical coverage** of 50% and 80% intervals with binomial confidence bands; PIT histogram.
* **Secondary Metrics**: RMSE/MAE of log price; directional hit rate (reported, never used alone); **information coefficient** (Spearman rank correlation of forecast vs realised return, per date, then averaged with Newey-West t-stat); interval width (sharpness at equal coverage); QLIKE for volatility models.
* **Ranking metrics** [TST-FC-04/05]: mean rank IC and IC information ratio; top-minus-bottom decile spread **after costs** (brokerage, STT, exchange charges, GST, stamp duty, SEBI fees from the versioned cost table + liquidity-bucket slippage); turnover; maximum drawdown; conclusions must hold at 2× costs.
* **GenAI / retrieval metrics**: unsupported-number count (target 0, TST-AI-01); citation validity rate (100% test, 99.5% weekly sample, TST-AI-02); prohibited-phrase count (0); causation-guard violations (0); glossary Top-3 hit rate ≥ 95%; grounding rate ≥ 98%; RAGAS-style faithfulness as a secondary diagnostic only, never as the gate (the gate is the deterministic citation check).
* **NLP metrics**: precision (primary, ≥ 95% for governance flags and entity linking), recall (secondary), per-class F1 for filing categories.
* **Cross-Validation Strategy**: **Purged and embargoed walk-forward (combinatorial purged CV where useful)** with expanding or 5-year rolling training windows; purge gap = horizon (no overlapping labels between train and test); embargo ≥ 5 trading days; a **final ≥ 3-year hold-out never touched for tuning**; universe and index membership as of each date; delisted stocks retained [BRD §10.5, TST-FC-01].
* **Hyperparameter Tuning Framework**: **Optuna** (TPE, ≤ 50 trials per horizon) on the purged folds only, with every trial logged to the selection report so the multiple-testing correction is honest. No tuning on the hold-out.

---

## 11. Production Architecture & MLOps

Designed for the v1.0 constraint of **no cloud account and no always-on server** [BRD §5.5, §15]. Everything below runs as Python libraries inside the GitHub Actions pipeline, with state in the private `data` branch.

* **Inference Mode**: **Batch**, in-process, inside the single pipeline entry point (`python -m research_platform.pipeline`) at steps 9–11 of BRD §15.5.3: load approved model versions from the registry → check feature freshness and alignment (FR-139) → predict → write `predictions/<date>/<run_id>.csv` with the FR-184 contract and status field. Models are loaded as files and called directly from Python; there is no model-serving component.
* **Training Mode**: **Offline**, in a separate monthly GitHub Actions workflow (or on a drift trigger), outside the 09:00/13:00/16:00 slots [BRD FR-140, §10.9.4]. The job reads the CSV store from the `data` branch, runs purged walk-forward + hold-out evaluation for every candidate, writes a selection report, and opens a pull request that updates the registry entry; promotion happens only when a reviewer merges it (FR-175, FR-181).
* **Feature Store**: The BRD's file-based feature store, `processed/features/<FEATURE_SET_VERSION>/<SYMBOL>.csv`, with incremental recompute from the earliest affected date minus the longest window (FR-138), committed to the private `data` branch.
* **Model Registry**: `models/model_registry.json` + `models/artifacts/<MODEL_ID>/<VERSION>/` (LightGBM text model, linear coefficients, conformal calibration residuals, feature list, SHAP background sample, artefact SHA-256) [BRD FR-181], versioned in Git; promotion is a reviewed commit (FR-175).
* **Experiment Tracking**: A committed selection-report CSV/JSON per training run, listing every candidate, fold, Optuna trial and metric (satisfies TST-GHA-10 and the multiple-testing record), stored next to the run record in the `data` branch.
* **Model Serving**: In-process Python (`lightgbm`, `scikit-learn`, `arch`). LLM calls through the chosen provider's SDK with retries, a per-run token budget (NFR-061) and caching of narratives per data snapshot.
* **CI/CD Pipeline**: **GitHub Actions**: unit and golden tests (TST-CALC, TST-DER, TST-RISK), leakage audit (TST-FC-01), hallucination/citation red-team suites (TST-AI-01 to 05) on every PR touching models or prompts; pinned action SHAs, least-privilege permissions, secret scanning (FR-171/172).
* **Monitoring & Drift Detection**:
  * *Calibration drift (primary)*: weekly rolling 80% coverage on matured forecasts; alert outside 70–90% (NFR-043).
  * *Skill drift*: monthly evaluation vs B0/B1 from the forecast ledger (FR-111, NFR-111).
  * *Feature drift*: PSI per feature on the cross-sectional distribution vs the training window (alert at PSI > 0.25); Evidently AI can render this as an HTML section of the run report if adopted as a library.
  * *GenAI quality*: weekly 5% sample of narratives for citation validity and prohibited language (OD-13, TST-AI-02).
  * *Operations*: run duration, Actions minutes, LLM spend per report, records reused vs downloaded (KPI-17 to KPI-23).
* **Deployment Strategy**: **Shadow (champion/challenger)**. A newly trained challenger writes forecasts to the ledger under a `shadow` flag for at least one evaluation cycle; only the approved champion's outputs appear in reports. Named-stock forecasts stay sponsor-only until OD-01/OD-22 close (REG-01, §18.6). A kill switch (config flag) disables the AI narrative and falls back to the template report (REG-15).
* **Retraining Strategy**: **Scheduled monthly** plus **drift-triggered** (coverage outside 70–90%, or PSI breach on more than 20% of top-20 features). Conformal calibration residuals refresh on each run's newest matured forecasts, so interval width adapts between retrains without changing model weights.

---

## 12. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **No challenger beats the naive baseline** (low signal-to-noise) | High | Medium | Expected outcome, not a failure: publish conformal-corrected B1 ranges + deterministic scenarios labelled as naive (BRD §10.6); report the result openly in the selection report; re-test at NIFTY 500 scale |
| **Backtest overfitting / multiple testing** (many variants, few independent samples) | High | High | Pre-registered feature families; Optuna trials logged; FDR/Bonferroni or deflated metrics; untouched ≥3-year hold-out; prefer Rank 2 on ties |
| **Look-ahead leakage** (fundamentals before filing time, restated values, revised macro, index membership) | Medium | High | Point-in-time joins on `filing_ts_utc` and release dates; historical constituents; purged/embargoed CV; TST-FC-01 leakage audit in CI |
| **Survivorship bias** (vendor lacks delisted history) | Medium | High | Make delisted/merged history a vendor RFP requirement (OD-02); if absent, flag every backtest as survivorship-biased and block publication |
| **Interval mis-calibration in crashes** (fat tails, regime shift) | Medium | High | Volatility-normalised targets; GJR-GARCH with Student-t; rolling conformal recalibration; regime-stratified coverage reports; NFR-043 alerting |
| **LLM states an unsupported number or causal claim** | Medium | High | Fact-sheet-only prompting, temperature 0, structured output with fact IDs, deterministic citation gate, causation and prohibited-language filters, template fallback, red-team suites TST-AI-01 to 04 |
| **Regulatory: forecasts or rankings read as research/trading calls** | High without RA route | Severe | REG-01 feature gates; sponsor-only recipients; "Statistical range / model_not_validated" labels; never "target", "buy" or "sell"; AI-use disclosure (REG-03) |
| **Data licence does not permit model training or derived outputs** | Medium | Severe | Add explicit derived-data and model-training rights to the OD-02 licence checklist; licence registry check before training (FR-143) |
| **Users over-rely on forecasts** | High | High | Show intervals, historical coverage and baseline comparison next to every range; confidence rates evidence, not profit (FR-063); invalidation conditions |
| **Concept drift** (SEBI F&O rule changes, rate cycles, index rebalances) | Medium | Medium | Monthly retrain, drift triggers, regime features, quarterly model-risk review by the quant lead |
| **Compute/time budget breach on Actions runners** | Low | Medium | Training in its own workflow; LightGBM/linear only on CPU; deep models confined to an offline research job with a timeout; NFR-101/110 monitoring |
| **LLM data residency / privacy** (A-06, NFR-036) | Low | Medium | No personal data in prompts (only public filings and engine outputs); provider with no-training terms (OD-12) |
| **Hindi retrieval quality** (transliteration, mixed script) | Medium | Low | Alias tables, transliteration normalisation, multilingual encoder, 200-query bilingual test set; BM25 fallback |

---

## 13. Implementation Roadmap

Aligned to the BRD's phases and gates [§22]. Durations are planning estimates [A]; ML work runs in parallel with the pipeline build and never blocks Phase 1 tools-mode delivery.

| Phase | Activities | Duration |
| :--- | :--- | :--- |
| **1. Business Understanding** | Confirm OD-01 (route), OD-07 (gate thresholds), OD-12 (LLM provider), OD-22 (recipients); sign off the metric definitions in §10 with the quant lead and compliance; pre-register feature families and horizons | 2 weeks (BRD Phase 0) |
| **2. Data Collection** | Vendor RFP includes delisted history, point-in-time fundamentals, index membership history and model-training rights (OD-02); initial 10-year download into the CSV store (FR-130); glossary and filing corpora | 4–6 weeks (Phase 0–1) |
| **3. Data Preparation** | V1–V19 validation, corporate-action adjustment and total-return series, trading calendar, point-in-time fundamentals with filing timestamps, survivorship-complete universe; leakage audit harness (TST-FC-01) | 3 weeks |
| **4. Feature Engineering** | Feature-set v1 from engine outputs; per-date rank-gauss; label builder with purging metadata; incremental recompute equivalence test (TST-GHA-08) | 3 weeks |
| **5. Model Selection** | Implement B0/B1/B2 + EWMA/GARCH baselines first and their conformal correction; then Elastic Net/linear QR; then LightGBM-QR; LSTM/GRU/TFT in an offline research job (C-14); LambdaRank for FR-183 | 3 weeks |
| **6. Training** | Purged walk-forward training for 4 horizons × 5 quantiles; conformal calibration; registry entries; monthly training workflow on Actions | 2 weeks |
| **7. Hyperparameter Tuning** | Optuna on purged folds with full trial logging; FDR correction across variants | 1–2 weeks |
| **8. Evaluation** | One-time ≥3-year hold-out evaluation; DM tests, coverage, IC, after-cost spreads, regime/sector breakdowns; selection report; quant lead + compliance sign-off per segment (gate G2 criterion) | 2 weeks |
| **9. Deployment** | Champion model into the research pipeline (internal beta, sponsor-only); AI narrative with citation gate and template fallback; hybrid glossary retrieval; filing classifiers; governance-flag extraction with review queue | 3 weeks (end of Phase 1) |
| **10. Monitoring** | Coverage/skill/PSI drift checks, GenAI sampling, cost and run-time KPIs in each run summary; shadow challenger in the ledger | 1 week setup, then continuous |
| **11. Continuous Improvement** | Monthly retrain and recalibration; re-evaluate deep models and LambdaRank at NIFTY 500 scale (Phase 2); add licensed news/sentiment features only after leakage review; public accuracy page only after 12 months of ledger and REG-09 (Phase 3) | Ongoing |

---

## 14. Final Recommendation

Build the platform as the BRD specifies: a **deterministic calculation core with ML used only where it is measurably better than a formula**. For the statistical price ranges, implement the **naive baselines with EWMA/GARCH volatility first**, then challenge them with a **pooled LightGBM quantile-regression model calibrated by CQR** (Rank 1) and a **regularised linear factor model** (Rank 2), and publish whichever is simplest among those that pass the Diebold-Mariano and coverage gate on an untouched ≥3-year hold-out. Otherwise publish the calibrated naive range labelled as such. Pair this with a **fact-sheet-constrained LLM behind a deterministic citation gate**, **hybrid BM25 + multilingual embedding retrieval** for the bilingual glossary and filings, and **rules-first NLP** for filings and governance flags. Everything runs as batch Python on GitHub Actions CPU runners with a file-based registry.

The expected business impact comes mainly from faster, fully cited, bilingual research and honest calibrated ranges (BO-01, BO-02, BO-05, BO-07), not from claims of predictive edge. Any predictive edge must be earned on the hold-out before it reaches a report, and must stay sponsor-only until OD-01 and OD-22 are closed.

---

## 15. Confidence Level

* **Confidence**: **Medium** overall.
  * **High** for the architecture split (deterministic core, gated ML, grounded GenAI), the retrieval and NLP choices, the evaluation protocol, and fit with the GitHub Actions/no-server constraints. These follow directly from explicit BRD requirements and mature, CPU-friendly libraries.
  * **High** that conformal methods can meet the calibration target (80% coverage in 75–85%).
  * **Low-to-Medium** that any return-forecasting or ranking challenger will pass the publication gate for T1 at 1–12-month horizons, given low signal-to-noise and about 1,000 effectively independent 12-month observations.
* **Reasoning**: The problem is well specified (acceptance tests, thresholds, output contract and fallbacks are all in the BRD), so the algorithm *choices* carry little uncertainty. The uncertainty is in the *outcome* of the predictive models, which the BRD handles correctly by making publication conditional on out-of-sample evidence.
* **Key Assumptions**:
  1. The licensed vendor (OD-02) provides point-in-time fundamentals, historical index membership and delisted-stock history, and the licence permits model training on derived data.
  2. Ten years of daily T1 data and 5–10 years of fundamentals are available (BRD A-07); a ≥3-year hold-out is affordable within that history.
  3. The chosen LLM provider (OD-12) offers no-training terms, deterministic decoding at temperature 0, and structured (JSON-schema) output.
  4. The quant lead and compliance accept the gate thresholds in BRD §10.6 (OD-07); stricter thresholds reduce the chance that any challenger is published.
  5. Expected-accuracy figures in §8 (rank IC ≈ 0.02–0.05, small pinball-loss gains) are planning assumptions from typical large-cap equity evidence, not measurements. They must be replaced by the platform's own selection report.
  6. Nothing in this report is investment advice, and no model output may be shared beyond the sponsor until the regulatory route is settled (BRD §18).
