# Engineering Profile: Bharat Equity Intelligence Platform

Customises the `developer` and `tester` agents and the `devops-engineer` skill for this project. Defaults not set here come from each role's own skill: `developer-engineering`, `tester-engineering`, `devops-engineer` (under `.agents/skills/`). Copy this file to the root of the implementation repository when it is created (OD-28).

## 1. Sources of truth
| Document | Path |
|---|---|
| Requirements (BRD v1.0) | [`BRD AI-Powered Indian Stock Market Intelligence Platform.pdf`](BRD%20AI-Powered%20Indian%20Stock%20Market%20Intelligence%20Platform.pdf) |
| System design | [`system_design.md`](system_design.md) |
| Implementation plan | [`implementation_plan.md`](implementation_plan.md) |
| Algorithm / model decisions | [`algorithm-recommendation.md`](algorithm-recommendation.md) |
| Workflows, config, repo-as-code | [`pipelines/`](pipelines/), [`config/platform.example.yaml`](config/platform.example.yaml), [`terraform/`](terraform/) |

## 2. Platform constraints
- Runtime: Python 3.12 on GitHub-hosted `ubuntu-latest` (CPU only).
- Allowed: private GitHub repository, GitHub Actions (schedule + `workflow_dispatch`), orphan `data` branch as the persistent CSV store, GitHub secrets/variables, Terraform `integrations/github` provider, external HTTPS APIs listed in `config/platform.yaml`, Gmail SMTP.
- **Forbidden** (never propose or name as options): any cloud account or hosted infrastructure, always-on servers, container platforms, hosted ML platforms, model-serving or feature-store products, hosted experiment trackers (BRD §5.5, §15). New infrastructure needs documented approval.
- Persistent state: `data` branch only; never runner disk.
- Budgets: research job timeout 60 min, p95 < 20 min (NFR-101); training job 120 min; CI < 10 min; Actions minutes alert at 70% of plan (NFR-110); file warn 25 MB, `data` branch warn 500 MB, migrate at 1 GB only with approval (§14.4.9).

## 3. Commands
| Purpose | Command |
|---|---|
| Install | `uv pip sync requirements.lock` (CI: `pip install --require-hashes -r requirements.lock`) |
| Determinism check | `pytest -q -m determinism` (two runs and 1 vs N workers give byte-identical outputs) |
| Lint / format check | `ruff check . && ruff format --check .` |
| Type check | `mypy --strict research_platform/analytics research_platform/storage research_platform/models` |
| Import layering | `lint-imports` |
| Unit + golden | `pytest -q tests/unit tests/golden` |
| Historical store Tests A–J | `pytest -q tests/history` |
| Integration (non-live) | `pytest -q -m "integration and not live"` |
| Live (needs secrets) | `pytest -q -m live` |
| Coverage | `pytest --cov=research_platform --cov-branch --cov-fail-under=80` |
| Principle checks | `python -m research_platform.checks.principles` |
| Workflow lint | `actionlint .github/workflows/*.yml` |

## 4. Quality thresholds
- ≥ 80% line coverage of core modules; 100% golden coverage of formulas (NFR-109).
- Tolerances: ratios 4 d.p. (TST-CALC-01); indicators, Greeks, IV 1e-6 (TST-CALC-02, TST-DER-02); corporate-action adjusted prices 0.01% (TST-DATA-03); DCF 0.1% (FR-051).
- Calculation, citation, entitlement or disclosure test failures block release (BRD §19).

## 5. Architecture rules
- **Data store**: CSV on the `data` branch is the only database; all access via `storage/csv_store.py` table specs (natural keys, upsert, atomic multi-file commit, manifest as index). Polars/DuckDB only read and are rebuildable.
- **Frameworks**: Polars primary, pandas only at library boundaries; httpx + tenacity + aiolimiter; pydantic/pandera validation; typer CLIs; structlog. No web frameworks, task queues, ORMs or database servers in v1.0.
- **Parallelism**: async fetch bounded by each provider's `max_in_flight` and `requests_per_second` in `config/platform.yaml`; process pool for per-symbol engines/features (`max_workers` from config, threads of Polars/LightGBM pinned); single writer.
- **Determinism**: fixed step tuple (BRD §15.5.3); `RunContext` with `as_of_utc`, seed and clock captured once; sorted keys before every write; fixed CSV float formats; LLM narrative cached by (snapshot ID, prompt version, model version).
- **Sessions**: one httpx session per provider per run; token sessions refresh before expiry (MoSPI 30-minute token; Upstox token expiry preflight); one SMTP session per run.
- **Multi-provider / multi-model**: providers routed by `dataset_routing` with licence gate and logged fallback; forecasters and LLM clients behind protocols, chosen by registry/config, champion + shadow.
- Pillars P1 ingestion → P2 storage/quality → P3 analytics/models → P4 reporting/AI → P5 orchestration; P6 config/security/observability cross-cutting. `genai` must not import `ingestion`; `analytics` must not import `delivery` (implementation plan §4.1).
- One entry point: `python -m research_platform.pipeline`; workflow entry points per implementation plan §4.1.
- Only deterministic engines and approved models produce numbers; the LLM restates fact-sheet entries behind the citation gate (G-3, FR-060).
- Labels never "buy", "sell" or "target" alone (§16.1).

## 6. Domain edge cases (in addition to the catalogue)
- Morning run before 09:15 IST open → previous completed session only (C-10, NFR-100).
- 13:00 run → intraday snapshot labelled incomplete; 16:00 → provisional unless final close confirmed (FR-153).
- Exchange holiday or Muhurat session → "market closed" note or skip; no false gaps (FR-159).
- Corporate action announced after a run → full symbol rebuild of adjusted series and features (FR-135, FR-138).
- Restated financials → new row with its own filing timestamp; original kept for point-in-time (§14.4.5).
- Provider returns shorter history than stored → treat as incomplete, never replace (§14.4.6).
- Lot size or expiry change → read from contract master only; zero hardcoded constants (TST-DER-04).
- Stop on wrong side of entry, quantity rounding to zero, short positions (FR-070, FR-071).
- IV not solvable, price below intrinsic → "IV not computable" (FR-082).
- Fewer than 2 valuation methods eligible → single-method range with warning; none → insufficient-data card (FR-054, FR-057).
- LLM >20% sentences failing the citation gate → regenerate once → template report (§15.2).
- Upstox Analytics Token within 30 days of expiry → warning; expired → labelled failure email (system design §13.2).
- Recipient not on the compliance allow-list → email step fails with a clear message (FR-164, OD-22).

## 7. Test environments and credentials
| Environment | Purpose | Credentials (secret names only) | Status |
|---|---|---|---|
| Local / CI (hermetic) | Unit, golden, Tests A–J, non-live integration with recordings, temp bare git origin, test SMTP | none | Available once code exists |
| Sandbox private repo | Workflow dispatch, concurrency, idempotency tests | dummy secrets | Blocked by OD-28 |
| Live provider | Real-provider run of Tests A–J, contract refresh | `UPSTOX_ANALYTICS_TOKEN`, `MARKET_DATA_API_KEY`, `FUNDAMENTALS_API_KEY` | Blocked by OD-02 (and Upstox terms confirmation) |
| Live email | TST-MAIL-01 to 04 | `GMAIL_SENDER`, `GMAIL_APP_PASSWORD`, `REPORT_RECIPIENT` | Blocked by D-11 |
| Live LLM | Nightly TST-AI suites | `LLM_API_KEY` | Blocked by OD-12 |

## 8. Gates and blockers
- Gated features (`sponsor_only` or off): FR-014, FR-055, FR-056 publication, FR-112, FR-183 until OD-01, OD-22 (REG-01).
- Report as **blocked**, never passed, until the listed dependency closes (see §7).

## 9. Waivers (loosened defaults)
| Default | Override | Reason | Approved by |
|---|---|---|---|
| Model registry under `data/models/` (BRD §14.4.1) | `models/` on `main` | Reviewed promotion (FR-175, FR-181) | Pending engineering lead |
