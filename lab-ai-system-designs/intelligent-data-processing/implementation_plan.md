# Bharat Equity Intelligence Platform: Engineering Implementation Plan

**Author**: @lovely
**Version**: 1.0
**Date**: 11 Oct 2026
**Status**: Draft. Code, unit tests and workflows can start now; production runs, integration tests and model training are blocked until OD-01, OD-02, OD-22, OD-28 and D-11 close (BRD §23)
**Inputs**: [`BRD AI-Powered Indian Stock Market Intelligence Platform.pdf`](BRD%20AI-Powered%20Indian%20Stock%20Market%20Intelligence%20Platform.pdf) (v1.0) · [`algorithm-recommendation.md`](algorithm-recommendation.md) · consistent with [`system_design.md`](system_design.md), [`pipelines/`](pipelines/), [`terraform/`](terraform/), [`config/platform.example.yaml`](config/platform.example.yaml)

Tags: **[BRD]** = taken from the BRD with its ID; **[ALG]** = from the algorithm recommendation; **[A]** = planning assumption to confirm; **[D]** = decision made in this plan that the engineering lead may change.

> **Deployment constraint.** v1.0 is one Python pipeline on GitHub Actions, a persistent CSV store on the private `data` branch, a file-based model registry and Gmail SMTP delivery. No always-on server and no hosted infrastructure of any kind (BRD §5.5, §15). Every work package below stays inside that environment.

---

## 1. Summary

The plan delivers the BRD's Phase 1 **Pipeline MVP** (gate G1) in **8 weeks of foundations + 16 weeks of build = 24 weeks** with a squad of about six, and prepares the forecasting evidence needed for **G2** (research live) in Phase 2.

Build order follows one rule: **the data spine first, numbers second, words last.**

1. **Spine (weeks 1–10)**: repository, config, contracts, persistent CSV store with incremental updates (FR-130 to FR-141, Tests A–J), provider adapters, the 14-step pipeline and the Actions workflows. Nothing else is trustworthy until this passes.
2. **Deterministic engines (weeks 9–18)**: fundamentals, technicals, market/events, valuation, risk and derivatives, each with golden tests at 100% (BO-03).
3. **Report, delivery and AI layer (weeks 15–20)**: fact sheet, LLM narrative behind the citation gate, 14-section HTML report, Gmail delivery.
4. **Forecasting (weeks 13–24, parallel quant track)**: naive baselines B0/B1/B2 with EWMA/GARCH and conformal correction ship in the MVP; LightGBM quantile regression + CQR and the Elastic Net factor model are built and evaluated, but published only if they pass the gate on the ≥3-year hold-out [ALG §7, §8].

What will **not** be claimed: no test is reported as passed until it has run against real code, and any test that needs the real provider, repository or Gmail account is reported as **blocked**, not passed (BRD §5.6 principle 7, §19.4).

---

## 2. Scope

| In scope (Phase 1, MVP) | Built but gated (internal / sponsor-only) | Out of scope for this plan |
|---|---|---|
| T1 = NIFTY 100, EOD + delayed snapshot (OD-04) | Named-stock scenarios FR-055, horizon forecasts FR-056 | Interactive web interface, accounts, public API (OD-21, Phase 4) |
| CSV store on `data` branch, incremental updates, Tests A–J | Stock ranking FR-183, research queue FR-014 | Order execution, broker integration, portfolio management (§5.2) |
| Pipeline: 3 weekday runs + dispatch, run records, data commits | Public accuracy page FR-112 (REG-09) | Intraday history in Git (OD-25) |
| Fundamental scorecard, technical summary, valuation ranges, insufficient-data cards | Research approval workflow FR-121 (needed before G2) | News feed, option chains (Phase 2) |
| Risk calculators over configured assumptions, index option payoffs and Greeks | | Stock F&O, portfolio risk, ETFs (Phase 3) |
| AI narrative + citation gate, glossary EN/HI, disclosures, AI-use label | | |
| HTML report + CSV summary via Gmail, failure notices | | |
| Baselines B0/B1/B2 + conformal intervals, forecast ledger, model registry, training workflow | | |

---

## 3. Engineering principles and how each is enforced

The BRD's mandatory principles (§5.6) become automated checks, not review comments.

| Principle (BRD §5.6) | Enforcement in code and CI |
|---|---|
| 1. No hardcoded prices, metrics, emails, credentials, lot sizes | `TST-PRIN-01` static scan in `ci.yml` (regex + AST rules for numeric literals in engine modules, email patterns, key patterns); config-only constants loaded through the JSON schema (FR-170); lot sizes read only from the contract master (TST-DER-04) |
| 2. No mock data in production; fixtures only outside `data/` | Fixtures live in `tests/fixtures/`; the mock provider class is importable only under `tests/`; production config schema rejects provider type `mock`; CI fails if any file under `data/` matches a fixture hash |
| 3. No placeholder shown as finished | Feature flags (`compliance/flags.py`) with states `off`, `internal`, `sponsor_only`, `public`; report sections render "unavailable: <reason>" when a flag is off (FR-165) |
| 4. No full download on routine runs; no runner disk as storage | `TST-HIST-B`, `TST-HIST-J`; pipeline refuses to start if `data/` is not a checkout of the `data` branch (FR-131) |
| 5. No prediction from invalid data; no unsupported accuracy claims | `FR-139` freshness/alignment check before inference; forecast contract status `insufficient_data` / `model_not_validated` (FR-184); prohibited-language filter (TST-AI-03) |
| 6. No bypassing the six pillars | Package layout mirrors P1–P6; an import-linter contract forbids, for example, `genai` importing `ingestion`, or `analytics` importing `delivery` |
| 7. No claim that something works until verified | Test status table (BRD §19.5) generated from CI results into `docs/test_status.md`; blocked tests are marked `blocked` with the blocking OD/D ID |
| 8. Fixed formulas allowed when explicit, tested, versioned | Every formula has an ID matching BRD Appendix A (e.g. `A.2.ROE`), a docstring citing it, and a golden test |

---

## 4. Repository and code structure

Two branches in one private repository (OD-28, A-09): code on `main`, state on the orphan `data` branch (created by [`terraform/bootstrap.sh`](terraform/bootstrap.sh)). The model registry lives on `main` so promotion is a reviewed PR [system_design §3; deviation from BRD §14.4.1 still to be confirmed by the engineering lead].

```
main
├── .github/workflows/        research.yml, model-training.yml, ci.yml   (from pipelines/)
├── .github/CODEOWNERS        workflows → engineering; models/ → quant lead; prompts/, config/ → compliance
├── config/
│   ├── platform.yaml         providers, universe, schedule, horizons, risk defaults, flags (FR-170)
│   ├── platform.schema.json
│   ├── cost_table.csv        STT, stamp duty, GST, SEBI fees, slippage buckets (versioned, §10.5)
│   └── macro/                rbi_rates.csv, fbil_usdinr.csv (reviewed PRs, §14.2 fallback)
├── models/                   model_registry.json, artifacts/<MODEL_ID>/<VERSION>/ (FR-181)
├── prompts/                  versioned prompt templates (compliance-owned)
├── glossary/                 300 terms EN/HI, YAML per term (FR-090)
├── research_platform/        Python package (below)
├── tests/                    unit, golden, property, history (A–J), ai_safety, fixtures/
└── docs/                     methodology pages, model cards, test_status.md, runbooks

data   (orphan branch, bot-written)
└── raw/ processed/ metadata/ predictions/ reports/ runs/ checkpoints/ backups/  (BRD §14.4.1, year-partitioned per §14.4.9)
```

### 4.1 Python package by pillar

| Pillar | Module | Responsibility | Key FRs |
|---|---|---|---|
| P1 | `ingestion/base.py` | `fetch(dataset, symbols, start, end) -> FetchResult(records, provenance, status)`; statuses `ok/partial/rate_limited/auth_failed/unavailable/invalid_response` | FR-142 |
| P1 | `ingestion/http.py` | `httpx` client, 30 s timeout, 5 retries with exponential backoff + jitter, `Retry-After`, run-wide rate limiter | §14.4.6 |
| P1 | `ingestion/providers/{upstox,vendor,mospi,files}.py` | Adapters; `vendor` is a configurable slot until OD-02; `files` reads reviewed macro CSVs | FR-143, §13 of system design |
| P1 | `ingestion/licence.py` | Refuses any dataset whose provider has `licence_confirmed: false` | FR-143, FR-125 |
| P2 | `storage/csv_store.py` | Typed read/write; temp file → fsync → checksum → `os.replace` | FR-131, NFR-095 |
| P2 | `storage/manifest.py`, `storage/schemas/` | Manifest rows, SHA-256, schema versions, statuses | FR-132, NFR-093 |
| P2 | `storage/calendar.py`, `storage/gaps.py` | Trading calendar; expected minus stored dates + failed ranges + 5-day look-back | FR-133, FR-159 |
| P2 | `storage/merge.py`, `storage/revisions.py` | Natural-key merge, dedupe, precedence (exchange > primary > secondary), revision rows | FR-134, FR-135 |
| P2 | `storage/corporate_actions.py` | Cumulative adjustment factors (A.1), split/bonus and total-return series | FR-002 |
| P2 | `quality/rules.py` | V1–V19 as pure functions returning `RuleResult` rows for `data_quality_log.csv` | §14.3 |
| P2 | `storage/security_master.py` | ISIN-keyed master, symbol history, review queue for conflicts | FR-001, FR-004 |
| P3 | `analytics/fundamentals/` | Statement normalisation, ratios (A.2), peers, trend rule (A.3), scorecard | FR-020 to FR-026 |
| P3 | `analytics/technicals/` | SMA/EMA/RSI/MACD/ATR/Bollinger/OBV (A.4), S/R zones (A.5), summary states (A.6), RS, drawdown | FR-030 to FR-035 |
| P3 | `analytics/market/`, `analytics/events/` | Market overview, breadth, sector rotation, macro panel, event calendar, event study (A.7) | FR-040 to FR-046 |
| P3 | `analytics/valuation/` | Method selector (§10.2), DCF + 5×5 grid, multiples, DDM, P/B-ROE, fair-value range, scenarios, invalidation conditions, insufficient-data card | FR-050 to FR-058 |
| P3 | `analytics/risk/` | Stop methods (§11.2), sizing (§11.3), R:R, gap/slippage, suitability checks | FR-070 to FR-075 |
| P3 | `analytics/derivatives/` | Contract master, BSM/Black-76, IV solver, payoff builder, futures basis | FR-080 to FR-087 |
| P3 | `features/` | Feature-set registry with versions; incremental recompute back by longest window | FR-138 |
| P3 | `models/` | Baselines, volatility, quantile LightGBM, linear QR, conformal, ranking, evaluation (DM, coverage, IC), selection, registry loader | FR-056, FR-180 to FR-184 |
| P2/P3 | `ledger/` | Append-only forecast ledger with SHA-256 hash chain | FR-110, FR-111 |
| P4 | `nlp/` | Filing classifier, entity linker, governance-flag extractor | FR-025, FR-042, FR-043 |
| P4 | `retrieval/` | BM25, multilingual embeddings (ONNX), reciprocal rank fusion, transliteration | FR-092, FR-094 |
| P4 | `genai/` | Fact-sheet builder, LLM client, citation gate, prohibited-language + causation filters, template fallback | FR-060, §15.2 |
| P4 | `reporting/` | 14-section Jinja2 HTML report, CSV summary, disclosures, AI-use label | FR-064, FR-120, FR-165 |
| P5 | `orchestration/pipeline.py` | The single entry point running the 14 steps of §15.5.3 | FR-152 |
| P5 | `orchestration/{inputs,session_state,run_record,git_persist}.py` | Dispatch-input validation, session labels, run records, fast-forward push with one re-merge | FR-151, FR-153 to FR-158 |
| P5 | `delivery/` | Gmail SMTP, idempotency send log, failure notice, recipient allow-list | FR-160 to FR-164 |
| P6 | `config/`, `observability/`, `compliance/` | Schema loader, JSON logs with masking, job summary, metrics, feature flags, disclosure versions | FR-170 to FR-176, REG-01, REG-03 |

**Workflow entry points.** The workflows in [`pipelines/`](pipelines/) call these modules, which must exist with exactly these names (thin CLI wrappers over the packages above):

| Command in workflow | Workflow | Wraps |
|---|---|---|
| `research_platform.pipeline` | `research.yml` | `orchestration/pipeline.py` |
| `research_platform.providers.preflight` | `research.yml` | `ingestion/providers/*` health and licence checks |
| `research_platform.persist.remerge`, `research_platform.persist.mark_not_persisted` | `research.yml` | `orchestration/git_persist.py` |
| `research_platform.observability.job_summary` | `research.yml` | `observability/` |
| `research_platform.checks.principles` | `ci.yml` | TST-PRIN-01 scan (§3) |
| `research_platform.models.leakage_audit`, `.select`, `.gate` | `model-training.yml` | `models/` evaluation and selection |

### 4.2 Technology stack [D]

All versions pinned and hash-locked in `requirements.lock` (generated with `uv pip compile --generate-hashes`).

| Concern | Choice | Note |
|---|---|---|
| Runtime | Python 3.12 on `ubuntu-latest` | `.python-version` |
| Env and lock | `uv` (`uv pip compile --generate-hashes`) | Fast, reproducible, hash-locked installs |
| Data | **Polars** (lazy CSV scans, multi-threaded expressions) as the primary frame engine; `pandas` 2.x (pyarrow dtypes) only at library boundaries (`statsmodels`, `arch`); `numpy`, `numba` for loops that cannot vectorise | CSV stays the only store; optional in-process read-only `duckdb` for ad-hoc and golden SQL tests (FR-010) |
| Contracts and config | `pydantic` v2, `pydantic-settings`, `pandera` (Polars frame schemas), `jsonschema` | |
| HTTP and retries | `httpx` (sync + async, one session per provider per run), `tenacity`, `aiolimiter` | Async fetch with per-provider concurrency and rate limits from config |
| Parallelism | `asyncio` for I/O-bound fetches; `ProcessPoolExecutor` (spawn) for per-symbol CPU work; single writer for all CSV and git writes | Byte-identical output vs sequential run is a CI test |
| CLI and logs | `typer` entry points, `structlog` JSON with masking | |
| Statistics and ML | `scipy`, `statsmodels`, `arch`, `scikit-learn`, `lightgbm`, `optuna`, `shap` | [ALG §7, §10] |
| Retrieval and NLP | `rank-bm25`, `onnxruntime` + a multilingual e5/bge encoder exported to ONNX, `indic-transliteration`, `rapidfuzz` | [ALG §7.4] |
| Reporting | `jinja2`, `premailer` (inline CSS for email clients) | |
| Testing | `pytest`, `hypothesis`, `pytest-cov`, `TA-Lib` (test-only reference for TST-CALC-02), `freezegun` | |
| Quality | `ruff`, `mypy --strict` on `analytics/`, `storage/`, `models/`, `import-linter` | |

---

## 5. Team and ownership

| Role | FTE [A] | Owns | BRD owner mapping |
|---|---|---|---|
| Engineering lead / platform engineer | 1 | Repo, workflows, orchestration (P5), config/security/observability (P6), code review | Engineering lead (§4) |
| Data engineers | 2 | Ingestion (P1), CSV store, quality rules, corporate actions, security master (P2), Tests A–J | Data engineering lead |
| Quant / ML engineer | 1.5 | Engines in P3, features, baselines and challengers, evaluation, model registry | Quantitative research lead |
| AI engineer | 1 | Fact sheet, LLM client, citation gate, filters, retrieval, NLP, report narrative | Research head |
| QA engineer | 1 | Golden datasets with two-analyst review, AI red-team sets, test-status table | QA lead |
| Compliance (part-time) | 0.25 | Disclosures, prompts review, recipient list, flag sign-off | Compliance officer |
| Bilingual finance editor (contract) | 0.5 | 300 glossary terms EN/HI (D-08) | Content |

---

## 6. Phase and sprint plan

Two-week sprints. Week numbers count from plan start. Each sprint lists deliverables, the FRs they close, and its **exit test**. Items that need an open decision are marked ⛔ with the blocker.

### 6.1 Phase 0: Foundations (weeks 1–8), gate G0

Business track (sponsor, counsel, data lead): close OD-01, OD-02 (RFP must cover storage in a private repo, access from GitHub-hosted runners, delisted history, point-in-time fundamentals, historical index membership, **model-training rights on derived data** [ALG §12]), OD-03, OD-22, OD-28, D-11; user research baselines for BO-01.

Engineering track runs in parallel and depends only on OD-28 (a repository).

| Sprint | Weeks | Deliverables | FRs / tests | Exit test |
|---|---|---|---|---|
| **S0.1 Repo and skeleton** | 1–2 | ⛔OD-28. Apply `terraform/` (private repo, protection, CODEOWNERS) and `bootstrap.sh` (orphan `data` branch); package skeleton per §4.1; `ci.yml` (lint, types, import contracts, coverage gate); `platform.schema.json` + loader; JSON logger with secret and email masking; feature-flag module; contracts from BRD §15.4 as pydantic models | FR-170 to FR-173, FR-176 | CI green on an empty skeleton; invalid config stops before any fetch (schema test); TST-SEC-05 checklist done |
| **S0.2 Storage core** | 3–4 | `csv_store` atomic write; manifest with SHA-256 and status; schemas v1 for every §14.4.2 dataset; trading-calendar model; gap detector; natural-key merge + dedupe; revisions log; failed-range queue; checkpoints; backups (keep last 7) | FR-130 to FR-136 (logic), NFR-093 to NFR-095 | Tests B, C, D, E, J pass against the **recording mock provider** under `tests/` |
| **S0.3 Ingestion** | 5–6 | Adapter base, HTTP client with retries/rate limits, licence check, provenance fields on every row; Upstox adapter (instrument master, daily candles, quotes, holidays) behind `licence_confirmed`; `files` adapter for RBI/FBIL CSVs; vendor slot with contract tests only | FR-142 to FR-144 | Contract tests per adapter; failure injection shows no writes on error; dataset without licence entry is never fetched |
| **S0.4 Golden datasets and formula library** | 7–8 | QA + two analysts build golden spreadsheets: 30 companies × 15 ratios, 50 indicator series, 40 corporate-action events, strategy payoffs (App. C), stop/sizing cases (§11.5); formula library for A.1–A.8 written test-first | TST-CALC-01/02, TST-DATA-03, TST-DER-01/02, TST-RISK-01 (harness) | Golden files reviewed and committed under `tests/golden/`; formulas pass where inputs are hypothetical (App. B/C values reproduce) |

**G0 exit** (BRD §22.3): OD-01, OD-02, OD-03 closed, licence signed. Engineering adds: storage core and adapters merged with Tests B–E, J green on the mock provider.

### 6.2 Phase 1: Pipeline MVP (weeks 9–24), gate G1

| Sprint | Weeks | Deliverables | FRs / tests | Exit test |
|---|---|---|---|---|
| **S1 Initial load and security master** | 9–10 | ⛔OD-02 for corporate actions and index constituents. Security master keyed by ISIN with symbol history; resumable initial 10-year download committing checkpoints across jobs until the manifest is complete; corporate-action factors and adjusted/total-return series; coverage and status flags (§6.3 rules); V1–V19 wired into the write path | FR-001, FR-002, FR-004, FR-130, FR-131, FR-135 | Test A on 20 symbols (mock) and one real-provider run; TST-DATA-03 on 40 events; size measured against A-11 |
| **S2 Orchestration and persistence** | 11–12 | `pipeline.py` with all 14 steps (steps 9–13 stubbed to "unavailable" until later sprints); `research.yml` with dispatch inputs validated in code; session-state labels; holiday handling; run records; `git_persist` fast-forward push with one re-merge; full-refresh safeguards with backup tag; job summary | FR-150 to FR-159, FR-173 | TST-GHA-01, 03, 04, 05, 06, 07 green; Test G (restart = fresh runner) and Test I green |
| **S3 Fundamentals** | 13–14 | ⛔OD-02 fundamentals vendor. Point-in-time statements (as-reported + restated by `filing_ts_utc`); ratio engine (A.2) with "not meaningful" handling; peer sets (≥5, widen to sector, bank-specific metrics); trend rule (A.3); ownership; scorecard by percentile, pillar "incomplete" rule, no verdict (OD-10) | FR-020 to FR-024, FR-026 | TST-CALC-01 100% to 4 d.p.; 100 sampled line items match filings; V13–V16 active |
| **S4 Technicals, market and events** | 15–16 | Indicator engine; S/R zones; RS (63/252 vs NIFTY 50 and sector); volatility/drawdown/gap stats; technical summary states with rule text; market overview, breadth, sector rotation; macro panel with release-date vintages; filing classification (exchange categories by rule + TF-IDF/LR residual) and event calendar; event study A.7 flag | FR-030 to FR-035, FR-040 to FR-042, FR-045 | TST-CALC-02 within 1e-6 vs TA-Lib; no "buy"/"sell" in summary output; calendar matches official sources for a sampled month |
| **S5 Valuation, risk and derivatives** | 17–18 | Method selector with exclusion reasons; DCF with 5×5 grid and terminal-growth rule; peer and own-history multiples; P/B-ROE; fair-value range as interquartile span of midpoints; scenarios + measurable invalidation conditions (flag `sponsor_only`); insufficient-data card; confidence rubric (§10.7); stop methods, sizing with caps and lot rounding, R:R, gap/slippage, suitability checks; contract master (no hardcoded lot sizes), BSM/Black-76, IV solver, payoff builder for the §12.5 library, derivatives disclosure text | FR-050 to FR-058, FR-063, FR-070 to FR-075, FR-080, FR-082, FR-083, FR-087 | TST-RISK-01, TST-DER-01/02/04 100%; TST-AI-05 (300 missing-data cases return the card); App. B/C examples reproduce |
| **S6 Report, AI layer and delivery** | 19–20 | ⛔OD-12 LLM provider, ⛔D-11 Gmail. Fact-sheet builder (IDs per fact, derived comparisons computed by engines); LLM client at temperature 0 with JSON-schema output and per-run token cap; citation gate (number/date/percentage/entity parser with unit normalisation, exact match); >20% failed sentences → regenerate once → template report; prohibited-language and causation filters EN/HI; 14-section HTML report + CSV summary; disclosures and AI-use label; Gmail SMTP with idempotency key, `submitted`/`smtp_error` only; failure notices; recipient allow-list | FR-060 to FR-062, FR-120, FR-160 to FR-165, REG-01, REG-03 | TST-AI-01 (zero unsupported numbers on 500 adversarial fact sheets), TST-AI-02/03/04; TST-RPT-01; TST-MAIL-01 to 04 |
| **S7 Forecast baselines, ledger, registry, glossary** | 21–22 | B0/B1/B2 with EWMA (λ = 0.94) and GJR-GARCH(1,1)-t candidate; conformal correction of B1 intervals; forecast contract writer; ledger with hash chain; accuracy evaluation job; registry loader refusing unapproved models; `model-training.yml` producing a selection report and a registry PR; glossary content load + hybrid BM25/embedding search with transliteration; contextual term tagging in the report | FR-056 (baselines), FR-110, FR-111, FR-139, FR-140, FR-181, FR-184, FR-090 to FR-092 | Test H; TST-GHA-09, TST-GHA-10; ledger records cannot be edited (tested); glossary top-3 hit rate ≥ 95% on 200 queries |
| **S8 Hardening and G1 readiness** | 23–24 | Observe all three slots for 5 weekdays (TST-GHA-02); measure NFR-101 run time, NFR-104 storage growth, NFR-107 API calls, NFR-110 minutes; security tests; restore drill; runbooks (failure email, token expiry, full refresh, restore from tag); test-status table regenerated from CI | NFR-100 to NFR-111, TST-SEC-03/04/05, TST-PRIN-01 | All Phase 1 Must FRs pass or are explicitly blocked with an OD/D ID; G1 evidence pack assembled |

**G1 exit** (BRD §19.2 gate 2): acceptance gate 1 (all Must FRs; TST-CALC, TST-DATA, TST-AI, TST-SEC, TST-REG green; Tests A–J green) plus usability, accessibility of the HTML report, and counsel's opinion on the tools-mode boundary. Named-stock forecasts remain `sponsor_only` until OD-01 and OD-22 close.

### 6.3 Parallel quant track: challengers (weeks 13–24), feeds G2

Runs on the quant engineer's time in an offline job, never inside the research slots, and never blocks G1 [ALG §13].

| Weeks | Work | Output |
|---|---|---|
| 13–14 | ⛔OD-02 (needs delisted history, PIT fundamentals, historical index membership). Label builder (forward log returns on the trading calendar, label timestamp t+h, delisting handling); feature set v1 from engine outputs (pre-registered families, [ALG §9]); per-date rank-gauss; leakage audit harness | TST-FC-01 harness; `features/v1` |
| 15–16 | Purged + embargoed walk-forward splitter (purge = horizon, embargo ≥ 5 days); hold-out of the final ≥3 years locked by a checksum file so it cannot be read during tuning | Reusable evaluation library |
| 17–18 | Elastic Net median + linear quantile regression with CQR (Rank 2) | Candidate results per horizon |
| 19–20 | Pooled LightGBM quantile regression (τ = 0.10, 0.25, 0.50, 0.75, 0.90; vol-normalised target; shallow trees) + split CQR with rolling recalibration; Optuna ≤ 50 trials per horizon on purged folds, every trial logged | Candidate results; SHAP background sample |
| 21–22 | Offline research job for LSTM/GRU/TFT as required by C-14 (time-boxed, CPU, own workflow timeout); LambdaRank on sector-neutral factor z-scores for FR-183 | Recorded as evaluated; not expected to pass [ALG §6] |
| 23–24 | One-time hold-out evaluation: Diebold-Mariano (HAC, lag = h − 1) vs B0/B1 with FDR correction, 50%/80% coverage, IC, after-cost decile spreads at 1× and 2× costs, breakdowns by regime/sector/period | Selection report for quant lead + compliance sign-off (G2 input) |

**Selection rule** [ALG §8]: per horizon and segment, publish the **simplest** model that beats B0 with DM p < 0.05 after FDR and has coverage 80% in [75%, 85%] and 50% in [45%, 55%]; otherwise publish the conformal-corrected B1 range labelled naive with status `model_not_validated`. The expected outcome is that many segments fall back to the baseline; that is a valid result, not a failure.

### 6.4 Phases 2–4 (outline)

| Phase | Engineering scope | Gate |
|---|---|---|
| 2 Research live (16 weeks, est.) | Research approval workflow FR-121 (PR-based approval with approver ID in the run record); shadow → champion for any passing challenger; NIFTY 500 universe (re-test deep models and LambdaRank at that scale); licensed news (FR-043, FR-044) with entity linker; option chains, OI, PCR with caveats (FR-081, FR-085); governance flags with span-verified LLM extraction and human review queue (FR-025); drift monitoring (coverage 70–90%, PSI) live | G2: RA registration, gate 3, validated segments only |
| 3 Expansion (24 weeks, est.) | Stock F&O, margin only if risk files licensed (FR-084), portfolio risk/VaR/ES (FR-076), ETFs, BSE-only stocks, accuracy page (REG-09); storage migration decision at the 500 MB warning (OD-24) | G3: gate 4 |
| 4 Later options | Web interface with a server-side trigger token (OD-21), IA review, broker read-only sync | Business case and legal review |

---

## 7. Implementation detail for the critical components

### 7.1 Persistent CSV store (P2): the spine

- **Write path**: validate → stage → merge on natural key → write `<file>.tmp` in the same directory → `fsync` → verify row count and SHA-256 → `os.replace` → update manifest → append log rows. The manifest is never updated before the rename succeeds (FR-132, NFR-095).
- **Partitioning**: `raw/daily/<EXCH>/<SYMBOL>/<YYYY>.csv`, so a routine run rewrites one small file per symbol (§14.4.9). Warn at 25 MB per file and 500 MB packed `data` branch.
- **Gap detection**: `expected = calendar.sessions(coverage_start, provider_latest) - stored_dates`; add `failed_ranges.csv`; add 5-day look-back; exclude incomplete sessions (`is_complete = false`). Missing calendar → stop the update and warn (FR-133).
- **Revisions**: never edit a raw row in place; write `revision + 1`, log old/new value, source and precedence rule (FR-135).
- **Proof**: Tests A–J run in CI against the recording mock on 20 symbols across NSE and BSE, and once against the real provider when OD-02 closes (BRD §19.3).

### 7.2 Orchestration and Git persistence (P5)

- One entry point, `python -m research_platform.pipeline --trigger <event>`; scheduled and manual runs differ only in validated inputs (FR-151, FR-152).
- Step 13 (email) runs before step 14 (push), so a push conflict never blocks delivery; a failed push after send is recorded as `data_not_persisted` and the next run re-merges (§15.5.3).
- Push algorithm: `git fetch data` → if base is still tip, fast-forward push; else re-read changed files, re-merge once, retry; else exit without writing and alert (FR-154).
- Idempotency: run ID + report hash key the send log and the ledger writes, so re-runs create no duplicate rows, predictions or emails (FR-158, FR-163).

### 7.3 Deterministic engines (P3)

- Pure functions over typed frames; each returns `value`, `unit`, `period`, `basis`, `formula_id`, `source_ids`, `calc_version`, or a structured `InsufficientData(missing_fields, next_data_date)` (G-1, G-2, FR-057).
- No imputation of fundamentals; prices forward-filled only for display of non-trading days, labelled (V2).
- Every output carries a fact ID so the fact sheet, evidence inspector data (FR-062) and citation gate share one identity.

### 7.4 Forecasting (P3)

- Baselines first and always computed: B0 no-change; B1 drift = versioned ERP assumption with EWMA σ (GARCH only if it wins on QLIKE out of sample); B2 beta × index B1 [ALG §7.4].
- Conformal correction on the newest matured forecasts each run, so interval width adapts between monthly retrains [ALG §11].
- Contract per BRD §10.9.3 written to `predictions/<date>/<run_id>.csv`, with manifest checksums and `last_confirmed_date` of every input (FR-139, NFR-097).
- Registry entry: model ID, version, task, horizon, training window, feature-set version, validation report path, approval, artefact SHA-256 (FR-181). Unapproved → refuse and mark `model_not_validated`.

### 7.5 AI layer (P4)

| Step | Implementation | Test |
|---|---|---|
| Fact sheet | JSON of engine outputs with IDs, units, periods; derived comparisons precomputed | Schema test |
| Retrieval | Page-level chunks of annual reports/presentations with page numbers; hybrid BM25 + embeddings; only for company overview and thesis | TST-AI-02 |
| Generation | Temperature 0, JSON schema: `[{sentence, fact_ids[], source_ids[]}]`; no personal data in prompts (NFR-036); narrative cached per snapshot ID | Token cap test |
| Citation gate | Parse every number, date, percentage, named entity; exact match after unit normalisation to a fact or a retrieved span; drop failures; >20% fail → regenerate once → template report | TST-AI-01 |
| Filters | Prohibited lexicon EN/HI ("guaranteed", "sure-shot", "will reach", "buy now", "multibagger", Hindi equivalents); "caused" never; "likely contributed" only if the A.7 flag is true | TST-AI-03, TST-AI-04 |
| Labels | Fact / Interpretation / Assumption / Scenario tag per statement; AI-use disclosure per report | TST-REG-01 |
| Kill switch | Config flag disables the narrative and uses the template report (REG-15) | Flag test |

The LLM provider is chosen under OD-12 by running TST-AI-01 to 05 against two or three candidates and picking the cheapest that passes [ALG §7.4]. Until then, the report runs in template-only mode, which is a complete, compliant output.

---

## 8. Testing strategy and CI gates

| Layer | Runs | Contents | Blocks merge? |
|---|---|---|---|
| Unit + property | Every PR | `hypothesis` for ratio sign rules, sizing caps, payoff symmetry, merge idempotency | Yes |
| Golden | Every PR | TST-CALC-01/02, TST-DATA-03, TST-DER-01/02, TST-RISK-01 at 100% | Yes |
| Historical store | Every PR | Tests A–J on the recording mock, 20 symbols | Yes |
| AI safety | PRs touching `genai/`, `prompts/`, `models/` | TST-AI-01 to 05 on **recorded** LLM responses (deterministic in CI); live-provider run nightly once OD-12 closes | Yes (recorded); nightly reports only |
| Leakage audit | PRs touching `features/`, `models/` | TST-FC-01 | Yes |
| Engineering principles | Every PR | TST-PRIN-01 scan, import contracts, secret scan, fixture-hash check on `data/` | Yes |
| Coverage | Every PR | ≥ 80% line coverage of core modules, 100% golden coverage of formulas (NFR-109) | Yes |
| Integration | After unblock | Real provider (OD-02), real repo, real Gmail (D-11): TST-GHA-01 to 10, TST-MAIL-01 to 04 | Reported `blocked` until unblocked |
| Model evaluation | Monthly workflow | TST-FC-02 to 05, TST-GHA-10 | Registry PR cannot merge without the selection report |

---

## 9. Configuration and secrets

| Name | Kind | Set by | Used by |
|---|---|---|---|
| `UPSTOX_ANALYTICS_TOKEN` | Secret | Sponsor (`gh secret set`) | Upstox adapter (sponsor-only use, after written terms confirmation) |
| `UPSTOX_TOKEN_ISSUED_ON` | Variable | Terraform | Preflight expiry warning (30 days) |
| `MARKET_DATA_API_KEY`, `FUNDAMENTALS_API_KEY` | Secret | After OD-02 | Vendor adapter |
| `MOSPI_USERNAME`, `MOSPI_PASSWORD` | Secret | Operator | MoSPI adapter |
| `LLM_API_KEY` | Secret | After OD-12 | `genai/llm_client.py` |
| `GMAIL_SENDER`, `GMAIL_APP_PASSWORD` | Secret | Sponsor (D-11) | `delivery/` |
| `REPORT_RECIPIENT` | Secret (OD-27 default) | Compliance-approved list (OD-22) | `delivery/` |

Secrets are never in Terraform state, code, logs, CSVs, reports or run records; rotation every 90 days (§15.7). Config changes go through PR with compliance as code owner.

---

## 10. Milestones and decision deadlines

| Week | Milestone | Decisions needed **by** this week |
|---|---|---|
| 1 | Repository live | OD-28 (repository), OD-23 (private) |
| 4 | Storage core green on mock | — |
| 8 | **G0** | OD-01, OD-02 (licence signed, incl. storage, runner access, training rights), OD-03 |
| 10 | Initial load complete on real data | A-13 confirmed (vendor reachable from runners) |
| 12 | Scheduled runs live (data only) | OD-27 |
| 18 | Engines complete | OD-07 (gate thresholds), OD-08 (ERP and terminal growth policy), OD-10 |
| 19 | Report + email | OD-12 (LLM provider), D-11 (Gmail App Password), OD-22 (recipients), OD-26 fallback if App Password unavailable |
| 24 | **G1** | Counsel opinion on tools-mode boundary |
| 24 | Selection report ready for G2 review | OD-07 confirmed after first validation run |

---

## 11. Delivery risks

| Risk | Effect on plan | Mitigation |
|---|---|---|
| OD-02 slips | S1, S3 and the quant track stall | Build against the recording mock and contract tests; Upstox covers prices and calendar for sponsor-only runs; fundamentals sections render "unavailable" until the vendor lands |
| Vendor blocks GitHub runner IPs (R-19) | Production fetches impossible | Confirm in RFP; a self-hosted runner is new infrastructure and needs approval, so escalate rather than add it |
| Initial download exceeds one job's time budget | Long first load | Resumable chunks with committed checkpoints across jobs; reports blocked until the manifest is complete (§14.4.9) |
| Run time exceeds 20 min p95 or minutes budget | NFR-101/110 breach | Cache per snapshot, incremental features, narrative caching, training kept out of slots; measured in S8 |
| No challenger passes the gate | No model-based forecasts at G2 | Planned outcome: calibrated B1 ranges + deterministic scenarios ship labelled naive |
| Golden dataset review takes longer than S0.4 | Engine sprints lack acceptance data | Start golden set with Appendix B/C hypothetical cases; QA owns schedule from week 1 |
| Hindi glossary not ready (D-08) | Report glossary links missing | Editor contracted in week 1; English fallback with marker (FR-005) |
| `data` branch growth | Storage thresholds hit early | Year partitioning, no intraday history, size alerts each run (NFR-104) |

---

## 12. Definition of done (every work item)

1. Code merged to `main` through a reviewed PR with the right code owner.
2. Unit, golden and property tests written first where a formula exists; all CI gates green.
3. Requirement IDs in the PR title and in docstrings; traceability updated in `docs/traceability.csv`.
4. No hardcoded market values, addresses or credentials (TST-PRIN-01).
5. Outputs carry source ID, timestamp and calculation version (G-1) or a structured insufficient-data result (G-2).
6. Runbook or methodology page updated when behaviour visible to the sponsor changes.
7. Integration tests that cannot run are recorded as `blocked` with the blocking ID, never as passed.

---

## 13. Traceability summary

| Plan section | BRD | Algorithm recommendation |
|---|---|---|
| §6.1 S0.2, §7.1 | §14.4, FR-130 to FR-141, NFR-090 to NFR-097, Tests A–J | §11 feature store |
| §6.1 S0.3 | §14.5, FR-142 to FR-144 | — |
| §6.2 S2, §7.2 | §15.5, FR-150 to FR-159 | §11 inference mode |
| §6.2 S3–S5, §7.3 | §9–12, FR-020 to FR-087, App. A | §3 (no-ML capabilities) |
| §6.2 S6, §7.5 | §15.2, FR-060 to FR-064, FR-160 to FR-165, REG-03 | §7.4 narrative, citation gate, filters |
| §6.2 S7, §6.3, §7.4 | §10.4 to §10.9, FR-056, FR-110, FR-111, FR-180 to FR-184 | §7 Ranks 1–3, §8 selection rule, §9 features, §10 metrics, §11 MLOps |
| §6.2 S7 glossary | §13, FR-090 to FR-092 | §7.4 hybrid retrieval |
| §6.4 Phase 2 NLP | FR-025, FR-043 | §7.4 entity linking, governance flags |
| §8 | §19 | §10 cross-validation |
| §11 | §21, §23 | §12 |
