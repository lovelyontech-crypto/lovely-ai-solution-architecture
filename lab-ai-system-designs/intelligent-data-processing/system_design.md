# Bharat Equity Intelligence Platform: AI System Design Document

**Author**: @lovely
**Version**: 1.0
**Date**: 11 Oct 2026
**Status**: Draft (implementation blocked by OD-01, OD-02, OD-22, OD-28 per BRD §23)
**Pattern**: Hybrid: deterministic analytics core + gated predictive ML + grounded generative AI (fact-sheet RAG with citation gate)
**Skill Compliance**: `ai-system-design-architect` (12-section standard), adapted to the BRD's no-cloud deployment
**Inputs**: [`BRD AI-Powered Indian Stock Market Intelligence Platform.pdf`](BRD%20AI-Powered%20Indian%20Stock%20Market%20Intelligence%20Platform.pdf) (v1.0) · [`algorithm-recommendation.md`](algorithm-recommendation.md)

**Deliverables in this folder**

| File | Content |
|---|---|
| `system_design.md` | This document |
| [`system_architecture.drawio`](system_architecture.drawio) | 10-page architecture diagram (one page per view in §7) |
| [`generate_drawio.py`](generate_drawio.py) | Regenerates the diagram: `python generate_drawio.py` |
| [`pipelines/`](pipelines/) | `research.yml`, `model-training.yml`, `ci.yml` (GitHub Actions) |
| [`terraform/`](terraform/) | Repository-as-code with the GitHub provider + `bootstrap.sh` for the `data` branch |
| [`config/platform.example.yaml`](config/platform.example.yaml) | **Provider and endpoint registry** the scheduled runs read: base URLs, paths, auth secret names, licence flags, dataset routing (§13) |

> **Deployment constraint (BRD §5.5, §15, change log).** v1.0 runs as a Python pipeline on **GitHub Actions** with a **private Git `data` branch** as the persistent store and **Gmail SMTP** for delivery. There is **no cloud account, no Kubernetes, no VPC and no always-on server**. The skill's cloud-oriented sections (infrastructure topology, Terraform, multi-region failover) are therefore expressed in GitHub terms. No cloud resources appear anywhere in this design.

---

## 1. AI Problem Classification

- **Domain Category**: Predictive AI (probabilistic price-range forecasting, cross-sectional ranking) + Generative AI (grounded research narrative) + Knowledge Retrieval (bilingual glossary and filing search) + Document Intelligence (filing classification, governance-flag extraction).
- **AI Archetype**: Batch research pipeline with a deterministic calculation core; ML and LLM components are bounded, gated and replaceable by deterministic fallbacks.
- **Problem Statement Summary**: Indian investors can get prices for free but not research that is current, sourced, explained and honest about uncertainty [BRD §2]. The platform researches NIFTY 100 stocks (NIFTY 500 and F&O later) through six engines (fundamental, technical, market/macro, news/events, valuation/forecasting, risk/derivatives) and emails a 14-section cited HTML report three times each weekday [BRD §1, §16.4]. The governing rule is **"only deterministic code and validated models produce numbers; the LLM only explains them"** (G-3, FR-060). Named-stock forecasts, stops and rankings are SEBI-regulated research, so they stay sponsor-only until the regulatory route (OD-01) and recipient list (OD-22) are decided [BRD §18].

---

## 2. Architecture Pattern Selection & Rationale

- **Selected Pattern**: **Six-pillar batch pipeline (BRD §15) = Deterministic engines + Gated Predictive ML + Fact-sheet RAG with a deterministic citation gate**. No autonomous agents.
- **Pattern Comparison & Rationale**:

| Option | Assessment | Decision |
|---|---|---|
| Pure LLM prompting ("ask the model about the stock") | LLM would produce numbers and causal claims it cannot cite; violates G-3, FR-060 and SEBI's "corroborated by data" rule | **Rejected** |
| AI agent with tool calling | Non-deterministic step order; FR-152 requires one implementation per business function, identical for scheduled and manual runs; more hallucination surface | **Rejected** |
| Fine-tuned LLM | No labelled corpus; GPUs unavailable on standard runners; the citation gate gives stronger guarantees than fine-tuning | **Rejected** |
| Deep-learning forecasters (LSTM/GRU/TFT) as primary | ~100 noisy series; low expected out-of-sample skill; evaluated only, per C-14 | **Evaluated, not primary** |
| **Deterministic core + gated ML + fact-sheet RAG** | Every number reproducible (BO-03); ML published only after passing the out-of-sample gate (BO-06); LLM restricted to restating facts with per-sentence citations (BO-02) | **Selected** |

Model choices come from [`algorithm-recommendation.md`](algorithm-recommendation.md): EWMA/GARCH baselines → pooled LightGBM quantile regression + CQR (or Elastic Net factor model on ties) for FR-056; LightGBM LambdaRank for the gated ranking; hybrid BM25 + multilingual embeddings for retrieval; rules + TF-IDF/LR + span-verified LLM extraction for filings.

---

## 3. Architecture Reasoning

| Concern | Choice | Reason |
|---|---|---|
| **Compute** | GitHub-hosted `ubuntu-latest` runners (CPU) | Sponsor-mandated; about 250k stock-days for T1 is small; LightGBM, linear models and GARCH train in minutes on CPU; run p95 < 20 min (NFR-101) |
| **Orchestration** | GitHub Actions `schedule` + `workflow_dispatch`, one Python entry point | Three IST slots and manual runs share one pipeline (FR-150 to FR-152); `concurrency: research-data` prevents overlapping writes (FR-154) |
| **Persistent storage** | CSV files on an orphan `data` branch of a private repository | Runners are ephemeral; Git gives versioning, backups (tags), atomic history and audit for free (§14.4.9); system of record is CSV by sponsor decision |
| **Model registry** | `models/model_registry.json` + artefacts on **`main`**, changed only by reviewed PR | FR-175/FR-181 require reviewed promotion; bot commits to `data` cannot be reviewed. *Deviation from BRD §14.4.1, which places `models/` under `data/`; to be confirmed by the engineering lead* |
| **Model engine (ML)** | `lightgbm`, `scikit-learn`, `arch`, `statsmodels` in-process | No serving component needed for batch inference over ~100 stocks |
| **Model engine (LLM)** | External LLM API chosen under OD-12 (no-training terms, temperature 0, JSON-schema output) | One bounded call per report section; cheapest model that passes TST-AI-01 to 05 |
| **Retrieval** | `rank_bm25` + multilingual sentence embeddings (CPU, ONNX), indexes stored as files | 300 glossary terms and T1 filings fit in memory; no vector database needed |
| **Live market data** | **Upstox Developer API over REST** (`https://api.upstox.com/v2`, `/v3`) with a 1-year read-only Analytics Token, for v1.0 sponsor-only use; licensed vendor slots for corporate actions, index constituents and fundamentals (OD-02) | The only verified option found that an unattended scheduler can call: no daily login and no static IP for market-data APIs. Full registry in §13 |
| **MCP** | **Not used by the scheduled pipeline.** Optional MoSPI MCP (`https://mcp.mospi.gov.in/`) for macro, disabled by default | Scheduled runs need deterministic REST calls with fixed parameters; broker MCP servers need an interactive login (§13.3) |
| **Delivery** | Gmail SMTP (`smtp.gmail.com:587`, STARTTLS, App Password) | Sponsor-mandated; Gmail API with OAuth as fallback (OD-26) |
| **Security & guardrails** | GitHub secrets, branch protection, CODEOWNERS, secret scanning, citation gate, prohibited-language and causation filters, REG-01 feature flags | All controls available without additional infrastructure (§15.7) |

---

## 4. AI System Context & Boundary Table

| Context Attribute | Specification |
|---|---|
| **Target Users** | v1.0: sponsor as sole report recipient (C-12, OD-22); operators and quant lead as repository collaborators. Later: Asha, Rohan, Meera, Vikram personas via a Phase 4 web interface (OD-21) |
| **Input Sources** | Upstox REST API `https://api.upstox.com` (daily candles, quotes, holidays) and instrument master `https://assets.upstox.com/.../complete.json.gz`; licensed vendor for corporate actions, index constituents and fundamentals (OD-02); MoSPI `https://api.mospi.gov.in`; RBI/FBIL rates as reviewed CSV files; licensed news (Phase 2); in-house glossary. See §13 |
| **Output Interfaces** | HTML report (14 sections) + CSV summary by Gmail; failure notice email; GitHub job summary; files on the `data` branch (predictions, reports, run records) |
| **Inference Type** | Batch, 3 scheduled weekday runs (09:00, 13:00, 16:00 IST) + manual dispatch; monthly / drift-triggered training workflow |
| **Universe & Scale** | T1 = NIFTY 100 (~100 stocks), 10 years daily, 5–10 years fundamentals; data branch growth < 50 MB/month (NFR-104) |
| **Target Platform** | GitHub (private repository, Actions, secrets) + external SaaS APIs. **No cloud account** |
| **SLA & Latency Target** | 98% scheduled runs succeed (NFR-102); run p95 < 20 min, timeout 60 min (NFR-101); 99% report emails submitted within 5 min of report generation (NFR-108) |
| **Regulatory boundary** | Named-stock fair values, scenarios, forecasts, rankings and suggested stops: sponsor-only until OD-01 + counsel opinion (REG-01) |

---

## 5. Architecture Component Inventory (8 Enterprise Layers)

Mapped to the BRD's six pillars (P1–P6).

1. **User Layer**: Sponsor (report recipient, Gmail inbox); operator (runs dispatch and full refresh); quant lead (approves model PRs); compliance (owns recipient allow-list, disclosures, prompts). Phase 4: web interface (OD-21).
2. **Application Layer (P4, P5)**: 14-section HTML report renderer + CSV summary (FR-165); email composer with idempotency key (FR-163); failure-notice composer (FR-161); glossary EN/HI (FR-090 to FR-094).
3. **API / Integration Layer (P1)**: provider adapter contract `fetch(dataset, symbols, start, end) -> records, provenance, status` (FR-142); licence and capability check (FR-143); provenance capture (FR-144); retry with exponential backoff and jitter, rate-limit handling; trading-calendar loader.
4. **AI / ML Layer (P3, P4)**:
   - *Deterministic engines*: fundamental (FR-020 to FR-026), technical (FR-030 to FR-036), valuation (FR-050 to FR-058), risk (FR-070 to FR-076), derivatives (FR-080 to FR-087), event study / causation guard (A.7).
   - *Forecasting*: baselines B0/B1/B2 with EWMA/GARCH volatility; LightGBM quantile regression + CQR (challenger); Elastic Net factor model (tie-break); LambdaRank ranking (gated).
   - *GenAI*: fact-sheet builder, hybrid retriever, LLM narrative (temperature 0, JSON schema), citation gate, prohibited-language and causation filters, template fallback.
   - *NLP*: filing classifier (rules + TF-IDF/LR), entity linker (security-master aliases + fuzzy match), governance-flag extractor (rules + span-verified LLM).
5. **Data Layer (P2)**: persistent CSV store on `data` branch (`raw/`, `processed/adjusted`, `processed/features/<version>`, `metadata/`, `predictions/`, `reports/`, `runs/`, `checkpoints/`, `backups/`); manifest with SHA-256 and status; quality, download and revisions logs; forecast ledger with hash chain (FR-110); file-based retrieval indexes.
6. **Security Layer (P6)**: GitHub Actions secrets; least-privilege `permissions`; actions pinned to SHAs; branch protection + CODEOWNERS; secret scanning with push protection; Dependabot; masked logs; dispatch input allow-lists; REG-01 feature flags; recipient allow-list; AI-use disclosure.
7. **Infrastructure Layer**: GitHub private repository (`main` for code, `data` for state); GitHub-hosted runners; concurrency groups; external HTTPS APIs (data vendors, LLM) and SMTP. Nothing else.
8. **Operations & Observability Layer (P6)**: structured JSON logs; `metadata/run_log.csv` and `runs/<run_id>.json`; GitHub job summary; report §2 (freshness) and §14 (data quality); monthly evaluation report; drift checks (coverage 70–90%, PSI); Actions usage and LLM token tracking.

---

## 6. Interaction Flow & Request Lifecycle

**A. Scheduled research run (09:00 / 13:00 / 16:00 IST; manual dispatch is identical)**

1. **Trigger**: cron fires on `main` (UTC `30 3`, `30 7`, `30 10` Mon–Fri). The run records its actual start time; a late start beyond the configured tolerance is labelled (FR-150, R-14).
2. **Checkout**: code from `main`; `data` branch into `data/`; Python with hash-locked dependencies.
3. **Config**: `config/platform.yaml` validated against its JSON schema; invalid config stops the run before any fetch (FR-170).
4. **Load state**: manifest read; every file's checksum and schema version verified (NFR-093).
5. **Gap detection**: expected trading dates (exchange calendar) minus stored dates, plus `failed_ranges.csv`, plus a 5-day look-back and new corporate actions (FR-133).
6. **Fetch (P1)**: a preflight step first checks each enabled provider in `config/platform.yaml` (instrument master download, `GET /v2/market/holidays`, token-expiry date, `licence_confirmed`). Then only missing ranges are requested, e.g. `GET https://api.upstox.com/v3/historical-candle/{instrument_key}/days/1/{to_date}/{from_date}`, plus `GET /v3/market-quote/quotes` (≤500 keys per call) for the 13:00 and 16:00 snapshots. Provenance on every row. Provider failure → keep last valid data, mark datasets stale (§14.5). Endpoints per dataset: §13.
7. **Validate and persist (P2)**: V1–V19; merge on natural key; revisions by precedence; temp-file write → fsync → checksum → atomic rename; manifest updated only after success (FR-134 to FR-136).
8. **Features**: recompute only affected symbols/dates back by the longest window; full rebuild after a corporate action (FR-138).
9. **Models**: load approved versions from the registry; refuse unapproved models (FR-181).
10. **Analytics (P3)**: deterministic engines; forecasts with status `available`, `insufficient_data` or `model_not_validated` (FR-184); session-state labels (completed / incomplete / provisional, FR-153).
11. **Predictions**: `predictions/<date>/<run_id>.csv` + ledger entries with model version and manifest checksums (FR-110, FR-139).
12. **Report (P4)**: fact sheet → retrieval → LLM draft (narrative cached per snapshot) → citation gate → language filters → HTML + CSV. More than 20% failed sentences → regenerate once → template report (§15.2).
13. **Deliver (P5)**: idempotency check, then SMTP submit; status `submitted` or `smtp_error`. On a failed run, a labelled failure email; a stale report is never sent as current (FR-160 to FR-163).
14. **Persist**: commit changed files to `data` with the run ID; on push conflict re-read, re-merge once and retry; otherwise mark `data_not_persisted` and alert; write the job summary (FR-154 to FR-156).

**B. Monthly / drift-triggered training**: checkout → leakage audit → purged walk-forward evaluation of all candidates (Optuna trials logged) → ≥3-year hold-out → Diebold-Mariano with FDR + coverage gate → PR updating the registry → quant lead + compliance approval → shadow for one cycle → champion.

**C. Full refresh (operator)**: dispatch with `full_refresh: true` and a reason → backup tag on `data` → re-download → compare → swap → audited (FR-137, FR-157).

---

## 7. The 10 Architecture Views

Each view is a page in [`system_architecture.drawio`](system_architecture.drawio). Summaries and text renderings follow.

### 1. Logical Architecture View (page 1)
Six pillars as colour-coded columns: P5 triggers → P1 ingestion → P2 storage & DQ (with CSV store cylinder) → P3 analytics & models (with registry) → P4 research & reporting → P5 delivery; external services column; P6 and model-governance bars across the bottom.

```
 Triggers ──► P1 Ingestion ──► P2 Storage & DQ ──► P3 Analytics ──► P4 Reporting ──► P5 Delivery ──► Sponsor inbox
 (cron x3,     adapters,         CSV store,          engines,           fact sheet,       Gmail SMTP,
  dispatch)    licence check     V1–V19, features    baselines, LGBM    LLM + citation    commit data
                    ▲                  ▲                   ▲              gate
              vendor APIs         data branch         model registry      LLM API
 ───────────── P6 config · secrets · least privilege · logs · audit (spans all pillars) ─────────────
```

### 2. Infrastructure View (page 2): GitHub, not cloud
Private repository boundary containing `main` (code, workflows, config, model registry*), `data` (orphan branch with `raw/`, `processed/`, `metadata/`, `checkpoints/`, `backups/`, `predictions/`, `reports/`, `runs/`, backup tags), Actions runners (concurrency, timeouts, minutes budget) and settings (secrets, protection, scanning). External SaaS column: market-data vendor, fundamentals vendor, filings feed, official macro, news (Phase 2), LLM API, Gmail SMTP, recipient inbox. Edges labelled HTTPS fetch, SMTP STARTTLS, checkout/commit.
*Registry location per §3.*

### 3. Security Architecture View (page 3)
Four quadrants: **Identity & access** (write access = dispatch, branch protection, CODEOWNERS, least-privilege token, pinned actions); **Policy & compliance** (REG-01 gates, recipient allow-list, AI-use disclosure, licence registry, no buy/sell/target labels, prohibited language); **Audit** (ledger hash chain, run records, revisions log, reviewed model commits, citation IDs, 5-year retention); **Threat** (secret scanning, Dependabot, masked logs, input allow-lists, retrieved text treated as data, secret rotation). Governance bar = job summary + report §14.

### 4. Observability View (page 4)
Rows: **Collection** (JSON logs, run/download/quality logs, token usage, ledger) → **Visualisation** (job summary, report §2/§14, monthly evaluation, Actions usage, selection report) → **Alerting** (failure email, stale banner, coverage outside 70–90%, PSI > 0.25, minutes ≥ 70%, data branch ≥ 500 MB) → **Operations** (idempotent re-run, full refresh, restore tag, model rollback by revert, secret rotation, monthly restore drill).

### 5. MLOps / LLMOps CI/CD View (page 5)
Source (PR + CODEOWNERS) → CI (lint, golden tests, leakage audit, AI red-team, secret scan) → Training (purged walk-forward, Optuna, CQR) → Evaluation gate (pinball/CRPS, DM + FDR, coverage) → Registry PR (quant lead approval, artefact hash) → Shadow → Champion, with a dashed drift → retrain loop. Research data pipeline shown underneath.

### 6. Data Lineage & Privacy View (page 6)
Vendor record → raw row (revision) → adjusted series (ca_version) → feature row (feature_set_version) → prediction (model version + manifest checksums) → fact-sheet entry (fact_id) → narrative sentence (fact_ids/source_ids) → report (report_id, snapshot_id) → email (idempotency key). Privacy sidebar: only personal data is recipient addresses (secrets, masked); no personal data in prompts; licensed data private; CSVs never downloadable; DPDP readiness.

### 7. Resilience & Fallback View (page 7)
Five fallback chains: market data (primary → retry → secondary vendor if licensed → last valid + stale label → failure email); LLM (draft → citation gate → regenerate once → template report → kill switch); scheduling (cron → late flag → missed-slot alert → manual dispatch); persistence (push → re-merge → `data_not_persisted` → restore tag → single-file repair); email (SMTP → retry → `smtp_error` → job summary → Gmail API OAuth per OD-26).

### 8. Pipeline Orchestration View (page 8; replaces "multi-agent")
The 14 deterministic steps of BRD §15.5.3 as a DAG; engines called as Python modules; state lives in the `data` branch. **No autonomous agents and no LLM tool calling**: the BRD requires one implementation per function (FR-152) and forbids LLM-produced numbers (G-3).

### 9. FinOps View (page 9)
Decision flow: new data? (no → zero historical requests) → narrative cached for snapshot? (yes → $0 LLM) → task type (classification → rules/TF-IDF at $0; narrative → mid-tier LLM; over budget → template). Cost levers and budget alerts listed in §12.

### 10. AI Governance, Safety & HITL View (page 10)
Three gated flows with decision diamonds: **forecast models** (DM test → coverage → PR review → shadow → champion; failure → labelled naive range); **narratives** (citation match → >20% dropped? → regenerate → template; weekly 5% human sample); **governance flags** (verbatim span + confidence → shown, else human review queue) and the **OD-01/OD-22 route gate** (sponsor-only vs public research).

---

## 8. Draw.io Multi-Page XML File

- **File**: [`system_architecture.drawio`](system_architecture.drawio), 10 pages, generated by [`generate_drawio.py`](generate_drawio.py).
- **Quality checklist status**:

| Check | Status |
|---|---|
| Bold page title on every page | Done |
| Storage as `shape=cylinder3` | Done |
| Container + colour header badge + white `shadow=1` cards | Done |
| Labelled major edges (`edgeLabel` children, `connectable="0"`) | Done |
| Unique IDs per page; every `source`/`target`/`parent` resolves | Verified by script (all 10 pages pass) |
| Well-formed XML | Verified by XML parser |
| 15+ components per page | Done (24–67 vertices per page) |
| Cloud provider icons and network group shapes | **Not applicable**: no cloud infrastructure in v1.0 |
| Draw.io MCP preview (`open_drawio_xml`) | **Not run**: the draw.io MCP server is not available in this session; open the file in diagrams.net to review layout |

---

## 9. Infrastructure Architecture Specifications

| Component | Specification |
|---|---|
| Repository | Private (A-09, OD-23); `main` protected (PR review, CODEOWNERS, status check `test`, linear history); `data` orphan branch, no force-push or deletion |
| Runners | GitHub-hosted `ubuntu-latest`; `research` job timeout 60 min, `model-training` 120 min, `ci` 30 min |
| Concurrency | `research-data` group, `cancel-in-progress: false`; training in its own group |
| Storage growth | Daily files partitioned by year; no intraday history in Git (OD-25); warn at 25 MB per file, 500 MB packed `data` branch; migrate at 1 GB only with approval (OD-24) |
| Network | Outbound HTTPS to licensed APIs and LLM API; SMTP 587 STARTTLS to Gmail. A13: vendor must accept calls from GitHub-hosted runner IPs; a self-hosted runner would be new infrastructure needing approval (R-19) |
| Budget | 3 runs × ~22 weekdays = ~66 runs/month; at p95 < 20 min that is ≤ ~1,320 minutes, inside the 2,000 included minutes for a private repo on GitHub Free [BRD §15.5.4]; manual and training runs must fit the remainder or the plan is upgraded |
| Secrets | `UPSTOX_ANALYTICS_TOKEN`, `MOSPI_USERNAME`, `MOSPI_PASSWORD`, `LLM_API_KEY`, `GMAIL_SENDER`, `GMAIL_APP_PASSWORD`, `REPORT_RECIPIENT` (secret per OD-27 default); `MARKET_DATA_API_KEY`, `FUNDAMENTALS_API_KEY` once the vendor is chosen. Variable `UPSTOX_TOKEN_ISSUED_ON` drives the token-expiry alert |
| Outbound endpoints | `api.upstox.com` and `assets.upstox.com` (HTTPS 443), `api.mospi.gov.in` (HTTPS 443), LLM provider (OD-12), `smtp.gmail.com:587`. Full list in §13 |

---

## 10. Infrastructure as Code (repository-as-code)

The skill asks for Terraform. Because v1.0 has no cloud resources, [`terraform/`](terraform/) uses only the **`integrations/github`** provider to codify the repository:

- `main.tf`: private repository (`auto_init`, secret scanning + push protection, Dependabot alerts, squash-only merges); branch protection for `main` (reviews, code owners, required `test` check) and `data` (no force-push or deletion); Actions variables; `.github/CODEOWNERS` routing workflows to engineering, `models/` to the quant lead, `prompts/` and `config/` to compliance.
- `variables.tf` / `outputs.tf`: owner, repository name, reviewers, owners, non-secret variables; next-step instructions.
- `bootstrap.sh`: creates the orphan `data` branch with the §14.4.1 directory skeleton and an empty manifest (Terraform cannot create orphan branches).
- **Secrets are intentionally not in Terraform**: state files would hold plaintext values. Set them with `gh secret set`.
- **Not validated here**: Terraform is not installed in this environment; run `terraform init && terraform validate` before use.

---

## 11. MLOps / LLMOps CI/CD Pipeline

Copy [`pipelines/`](pipelines/) into `.github/workflows/` of the platform repository and replace version tags with commit SHAs (FR-172).

| Workflow | Trigger | What it does | BRD refs |
|---|---|---|---|
| [`research.yml`](pipelines/research.yml) | 3 weekday crons + `workflow_dispatch` (scope, symbols, mode, horizons, format, full_refresh + reason) | Runs the 14-step pipeline; inputs passed via env (no shell interpolation); commits `data` with fast-forward + one re-merge; writes job summary | FR-150 to FR-165, §15.5 |
| [`model-training.yml`](pipelines/model-training.yml) | Monthly (2nd, 02:00 IST) + manual with trigger reason | Leakage audit → candidate selection (purged walk-forward, ≥3-year hold-out) → publication gate → PR to update the registry | FR-140, FR-180 to FR-182, §10.9 |
| [`ci.yml`](pipelines/ci.yml) | PR to `main` | Lint/type check; golden calc tests; historical-store tests A–J with a recording mock provider; AI safety suites on recorded responses; engineering-principles scan; ≥80% coverage | §19, NFR-109, TST-PRIN-01 |

The YAML files parse cleanly; they reference `research_platform.*` modules that do not exist yet (the code is not written, BRD §19.5).

---

## 12. Operational & FinOps Model

- **Service levels** (proposals, unmeasured): 98% scheduled-run success (NFR-102); run p95 < 20 min (NFR-101); 99% report emails submitted (NFR-108); 100% run records including failures (NFR-106); morning report uses the previous completed session, evening report labels prices provisional unless final (NFR-100).
- **Recovery and backup**: Git history is the backup of every committed file; dated backup tags before any full refresh or bulk revision; last 7 CSV versions retained, restore drill monthly (NFR-094); a failed run leaves data intact and the next run recovers automatically in ≥95% of cases (NFR-103). There is no multi-region failover because there is no hosted service. GitHub outage → missed slots are reported and re-run by manual dispatch.
- **Model operations**: monthly retraining or drift trigger (coverage outside 70–90%, PSI > 0.25 on more than 20% of top features); conformal residuals refreshed every run; shadow before champion; rollback = `git revert` of the registry commit.
- **Cost model**:

| Cost | Driver | Control |
|---|---|---|
| GitHub Actions minutes | ~66 research runs + 1 training run + CI per month | Alert at 70% of included minutes (NFR-110); training outside slots; no deep models in CI |
| Market and fundamentals data | Vendor quote (OD-02) | Fetch only missing ranges (NFR-091); API calls < 70% of quota (NFR-107) |
| LLM tokens | Narrative sections × runs | Narrative cached per data snapshot; fact sheet only in prompt; rules/TF-IDF for classification; daily token cap with template fallback (NFR-061) |
| Storage | `data` branch growth | Year-partitioned files, no intraday history, thresholds in §14.4.9 |

Cost per completed run is reported in every run (KPI-23); the budget is set after OD-02 and OD-03.
- **Governance**: REG-01 feature flags off for anything public; recipients limited to the compliance-approved list (OD-22); every model, prompt, schema and config change is a reviewed commit with a changelog entry (FR-175); regulatory watch reviewed monthly (R-07).
- **Open decisions affecting this design**: OD-01 (route), OD-02 (vendor; must allow storage in a private repo, access from GitHub runners and model training), OD-12 (LLM provider), OD-22 (recipients), OD-24 (storage migration path), OD-26 (Gmail API fallback), OD-28 (repository). The `models/` location on `main` (§3) also needs confirmation.

---

## 13. Live Data Source, Endpoint & MCP Registry

This section answers *where each scheduled run gets its live data from*. The pipeline never hardcodes a URL: every run reads [`config/platform.yaml`](config/platform.example.yaml) (FR-170), resolves each dataset to a provider through `dataset_routing`, and reads that provider's credential from the GitHub secret named in the config. Endpoints below were checked against the providers' own documentation on 11 Oct 2026, except where marked unverified.

### 13.1 Endpoint registry (what the GitHub scheduler calls)

| Dataset (BRD ref) | Provider | Method + URL | Auth (GitHub secret) | Called in slot | Status |
|---|---|---|---|---|---|
| Security master, index keys, F&O lot sizes and expiries (FR-001, FR-080) | Upstox instrument master (CDN) | `GET https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz` | None (public CDN file, refreshed ~06:00 IST) | Every run (cached per day) | Verified. Excludes delisted and expired instruments, so the platform keeps its own history |
| Daily OHLCV, stocks and indices (FR-130, FR-133) | Upstox REST | `GET https://api.upstox.com/v3/historical-candle/{instrument_key}/days/1/{to_date}/{from_date}` | `Authorization: Bearer ${UPSTOX_ANALYTICS_TOKEN}` | Initial load once; then missing ranges + 5-day look-back each run | Verified. Daily history from Jan 2000; at most 1 decade per request, so the 10-year initial load is 1 call per instrument |
| Intraday / provisional snapshot (OD-25, FR-153) | Upstox REST | `GET https://api.upstox.com/v3/market-quote/quotes?instrument_key=…` (≤ 500 keys per call) | Same token | 13:00 (incomplete session), 16:00 (provisional close) | Verified |
| Trading calendar (FR-133, FR-159) | Upstox REST | `GET https://api.upstox.com/v2/market/holidays` (optional `/{YYYY-MM-DD}`) | Same token | Every run | Verified. A Muhurat-session inconsistency has been reported, so cross-check against the exchange holiday circular |
| Corporate actions, index constituents with effective dates (FR-002, §6.1) | Licensed vendor | `base_url` in config, set after the RFP | `MARKET_DATA_API_KEY` | Every run | **Blocked by OD-02.** Upstox has no verified endpoint for this |
| Point-in-time fundamentals, shareholding (FR-020, FR-024) | Fundamentals vendor | `base_url` in config | `FUNDAMENTALS_API_KEY` | 09:00 run | **Blocked by OD-02.** Upstox lists a "Fundamentals" category, but its endpoint paths are unverified |
| CPI, IIP, GDP (FR-041) | MoSPI REST | Base `https://api.mospi.gov.in`; `POST /api/login` returns a token valid 30 minutes; data paths per the [CPI API User Manual](https://api.mospi.gov.in/API/CPI%20API%20User%20Manual.pdf) | `MOSPI_USERNAME`, `MOSPI_PASSWORD` | 09:00 run, on release dates | Base URL and auth verified; check the portal terms. Without a token, only 10 records are returned |
| Repo rate, 10Y G-sec, 91-day T-bill (§9.3, §12.3) | RBI DBIE `https://data.rbi.org.in` | No documented API found. Operator updates `config/macro/rbi_rates.csv` by reviewed PR | n/a | Read every run | BRD fallback "manual entry with second-person check" (§14.2) |
| USD/INR reference rate | FBIL `https://www.fbil.org.in` | No documented API found. `config/macro/fbil_usdinr.csv` by reviewed PR (published ~13:00 IST weekdays) | n/a | Read every run | Same fallback |
| News (FR-043) | Licensed news vendor | `base_url` in config | `NEWS_API_KEY` | Phase 2 | Not in v1.0; no scraping (C-05) |
| AI narrative (FR-060) | LLM provider | `base_url` in config | `LLM_API_KEY` | 09:00, 13:00, 16:00 | Provider decided under OD-12 |
| Report email (FR-160) | Gmail | `smtp.gmail.com:587`, STARTTLS | `GMAIL_SENDER`, `GMAIL_APP_PASSWORD`, `REPORT_RECIPIENT` | End of each run | Verified (§15.6) |

### 13.2 Why Upstox for v1.0, and its limits

- **Works unattended.** The Upstox Analytics Token is generated once in Developer Apps → Analytics, is valid for **1 year**, is **read-only (GET only)**, and is free. Market Quote, Historical Data, Option Chain and Market Information APIs need **no static IP**. GitHub-hosted runners have no fixed IP and no human present at 09:00, so a daily-login or IP-allow-listed API would fail every scheduled run (BRD A-13, R-19).
- **Licence boundary.** Broker API data is for the account holder's own use (BRD §14.5). It is acceptable **only while reports go to the sponsor alone** (OD-22, §18.6) and after written confirmation of Upstox's terms. `licence_confirmed: false` in the config blocks production fetches until then (FR-143). Any wider distribution needs the licensed vendor (OD-02), which plugs into the same adapter interface (FR-142).
- **Token lifecycle.** Store the generation date in the Actions variable `UPSTOX_TOKEN_ISSUED_ON`. The preflight step warns 30 days before expiry and fails the run with a labelled failure email after expiry. Only one Analytics Token can exist per account, so regenerating it invalidates the old one.
- **Gaps Upstox does not fill (verified so far):** corporate-action ratios and ex-dates, historical index constituents, point-in-time fundamentals, and delisted-stock history. These are mandatory for the forecasting backtests (§10.5), so model training stays blocked until OD-02 is closed. Deterministic reports on current data can run before that.

### 13.3 MCP: what is and is not used

| MCP server | URL | Used by the scheduler? | Reason |
|---|---|---|---|
| Zerodha Kite MCP (official, hosted) | `https://mcp.kite.trade/mcp` | **No** | Authentication is an interactive Kite login with two-factor authentication through the AI client, so no unattended GitHub run can complete it. It also gives GTT order capability, which the platform must never have (§5.2). Suitable only for the sponsor's own interactive research in an AI assistant |
| MoSPI eSankhyiki MCP | `https://mcp.mospi.gov.in/` (tools: `list_datasets` → `get_indicators` → `get_metadata` → `get_data`) | **Optional, off by default** (`providers.mospi_mcp.enabled: false`) | It could supply CPI/IIP/GDP over streamable HTTP. The REST API is preferred because the BRD needs fixed, reproducible requests (FR-139, NFR-097). Enable it only after its auth and terms are checked |
| Community Upstox / Dhan MCP servers | various third-party hosts | **No** | Not operated by the broker; sending the broker token to a third-party host breaks the secrets policy (§15.7, R-17) |

**Design rule:** scheduled runs call REST endpoints directly from the provider adapters (FR-142). MCP belongs to interactive AI tooling, not to the deterministic pipeline, and an LLM never chooses which data to fetch (G-3).

### 13.4 Sources used for this registry

- Upstox Analytics Token: https://upstox.com/developer/api-documentation/analytics-token/
- Upstox API overview (base URL, auth header): https://upstox.com/developer/api-documentation/api-overview/
- Upstox historical candle v3: https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/
- Upstox full market quote v3: https://upstox.com/developer/api-documentation/get-full-market-quote-v3
- Upstox market holidays: https://upstox.com/developer/api-documentation/get-market-holidays/
- Upstox instruments: https://upstox.com/developer/api-documentation/instruments
- Zerodha Kite MCP: https://support.zerodha.com/category/trading-and-markets/general-kite/others-kite/articles/connect-zerodha-ai-assistant
- MoSPI CPI API manual: https://api.mospi.gov.in/API/CPI%20API%20User%20Manual.pdf
- MoSPI MCP listing: https://glama.ai/mcp/servers/nso-india/esankhyiki-mcp
- RBI DBIE URL change: https://website.rbi.org.in/web/rbi/-/press-releases/reserve-bank-s-database-on-indian-economy-portal-change-in-url
