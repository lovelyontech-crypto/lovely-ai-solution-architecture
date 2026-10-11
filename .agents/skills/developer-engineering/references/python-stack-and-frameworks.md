# Python Stack and Framework Selection

Modern, production-proven Python for batch data pipelines, analytics engines, ML inference and LLM features. Use the **right tool for each job and nothing more**: every dependency must earn its place (maintenance, licence, size, CPU-only runners). A project's `engineering-profile.md` may override a choice; never add a framework that needs infrastructure the project forbids (servers, databases, queues, clusters).

## 1. Toolchain

| Concern | Use | Why / rule |
|---|---|---|
| Python | 3.12 (`.python-version`) | Faster interpreter, better typing (`type` aliases, `@override`), stable on runners |
| Env + lock | **`uv`** (`uv venv`, `uv pip compile --generate-hashes`, `uv pip sync`) | 10–100× faster than pip; hash-locked `requirements.lock`; reproducible installs |
| Project layout | `src/`-less package `research_platform/` + `pyproject.toml` (PEP 621) | One config file for tools |
| Lint + format | **`ruff`** (lint rules `E,F,W,I,B,UP,SIM,C4,PTH,RUF,PL,N,S,DTZ,PD,NPY`) + `ruff format` | Replaces flake8/isort/black/pyupgrade/bandit-lite in one fast tool |
| Types | **`mypy --strict`** on core packages | Catches unit/None/shape bugs before runtime |
| Layering | **`import-linter`** contracts | Enforces pillar/layer directions |
| Pre-commit | `pre-commit` running ruff, mypy, secret scan | Same checks locally and in CI |

## 2. Libraries by job (project defaults)

| Job | Default | Use instead / in addition when | Do not use |
|---|---|---|---|
| Tabular transforms, CSV I/O, features | **Polars** (lazy API, `scan_csv`, expressions) | Hand a frame to libraries that need pandas via `.to_pandas()` only at that boundary | Row-by-row Python loops over frames; `DataFrame.apply` with Python lambdas |
| Statistical / econometric models | `statsmodels`, `arch` (GARCH), `scipy` | — | Re-implementing tested estimators |
| Library-boundary frames | `pandas` 2.x with `dtype_backend="pyarrow"` | Only where a library requires pandas | pandas as the main engine (keep one primary frame library) |
| Numerical kernels | `numpy`; **`numba`** `@njit` for tight loops that cannot vectorise (Wilder smoothing, swing-point clustering, IV root-finding over grids) | Profile first | Cython or C extensions |
| ML | `lightgbm`, `scikit-learn`, `optuna`, `shap` | Deep models only in the offline research job (`torch`, CPU) | Deep learning in the scheduled pipeline |
| Validation of records/config | **`pydantic` v2** models; **`pandera`** (Polars backend) for frame schemas | `jsonschema` for config files consumed by other tools | Hand-written `if` chains for schemas |
| HTTP | **`httpx`** (sync `Client` and `AsyncClient`, HTTP/2 optional) | — | `requests` in new code (no async, weaker timeouts) |
| Retries | **`tenacity`** (exponential backoff + jitter, `retry_if_exception_type`) | — | Ad-hoc `while True` loops |
| Async concurrency | `asyncio` with **`anyio`** task groups / `asyncio.TaskGroup` | — | Threads for I/O when async client exists |
| Rate limiting | `aiolimiter` (token bucket) or a small in-house limiter | — | `time.sleep` sprinkled in code |
| CLI entry points | **`typer`** | — | `argparse` boilerplate in many modules |
| Settings | **`pydantic-settings`** (env vars + `.env` for local only) | — | `os.environ[...]` scattered in code |
| Logging | **`structlog`** → JSON, with a masking processor | — | `print`; f-string logs without context |
| Templates / email HTML | `jinja2` (autoescape on) + `premailer` | — | String concatenation for HTML |
| Email | stdlib `smtplib` + `email.message.EmailMessage` (STARTTLS) | — | Third-party mail SaaS SDKs unless approved |
| LLM | Provider SDK behind an in-house `LLMClient` protocol; structured output validated by pydantic | — | Agent frameworks that hide prompts, add non-determinism or call tools autonomously |
| Retrieval | `rank-bm25`, `onnxruntime` with a multilingual encoder, `rapidfuzz`, `indic-transliteration` | — | Vector databases or hosted search |
| Optional analytics query layer | **`duckdb`** in-process, **read-only** over the CSV files | Ad-hoc screening queries, golden SQL references (FR-010 tests) | Writing to a DuckDB file as a second store |
| Testing | `pytest`, `hypothesis`, `pytest-xdist`, `respx`, `freezegun`, `aiosmtpd`, `pytest-cov` | `TA-Lib` as a test-only reference | Network in unit tests |

## 3. Modern Python idioms to use

- `from __future__ import annotations` not needed on 3.12; use `type Alias = ...`, `X | None`, `Self`, `@override`, `typing.Protocol` for adapters.
- Immutable value objects: `@dataclass(frozen=True, slots=True)` for hot paths, pydantic `BaseModel(frozen=True)` at boundaries.
- `enum.StrEnum` for statuses (`ok`, `partial`, `stale`, `insufficient_data`).
- `pathlib.Path` everywhere; `datetime` always timezone-aware (`datetime.now(UTC)` only in the injected clock).
- `match` statements for status handling; exhaustive with `assert_never`.
- Context managers for every resource (clients, files, SMTP); `contextlib.ExitStack` to compose.
- Generators/iterators and Polars lazy frames for large data; never load more than one symbol-year partition when you do not need to.
- `functools.cache` only on pure functions with hashable, bounded inputs.

## 4. Choosing a framework: decision rule

Adopt a library only if **all** are true: it removes meaningful code or risk; it is actively maintained with a compatible licence; it runs CPU-only in-process; it does not take over control flow in ways that break determinism; it is pinned and hash-locked. Record the choice and the rejected alternative in the PR.
