# Multiple Providers, Multiple Models, and Sessions

## 1. Multiple data providers

One contract, many adapters (FR-142). Analytics never knows which provider supplied a row; provenance on every row says so.

```python
class ProviderAdapter(Protocol):
    name: str
    def capabilities(self) -> frozenset[Dataset]: ...
    def fetch(self, req: RangeRequest, *, session: ProviderSession) -> FetchResult: ...   # status, records, provenance
```

- **Routing from config**, not code: `dataset_routing` in `config/platform.yaml` maps each dataset to an ordered list of providers (primary, secondary).
- **Licence gate first**: a provider without `licence_confirmed: true` for the dataset is skipped and recorded (FR-143).
- **Fallback** only to the next configured provider for the same dataset, and only on `unavailable / rate_limited / auth_failed`, never on `invalid_response` silently; the fallback is logged and visible in the report.
- **Precedence on conflict**: exchange official > licensed primary > secondary; a lower-precedence source never overwrites a higher one (§14.4.5).
- **Contract tests per adapter** against recorded responses, plus a scheduled live check that refreshes recordings.
- Adding a provider = new adapter module + config entry + contract tests. No change to analytics.

## 2. Multiple models

**ML models (forecasting, ranking)**
- A registry (`models/model_registry.json`) lists every model with task, horizon, version, feature-set version, training window, approval and artefact checksum.
- A `ModelSpec` → loader factory maps model type to implementation (`baseline_b1`, `elastic_net_qr`, `lightgbm_qr`, `lambdarank`). All implement one protocol:

```python
class Forecaster(Protocol):
    model_id: str
    version: str
    def predict(self, features: pl.DataFrame, *, horizon: Horizon) -> ForecastFrame: ...   # median + quantiles + status
```
- Champion per (task, horizon, segment); challengers run in **shadow** and write to the ledger with a shadow flag.
- Load refuses: unapproved, checksum mismatch, or feature-set version different from the current features.

**LLM providers/models**
- An `LLMClient` protocol with one method returning a validated pydantic object; provider SDKs live behind it.

```python
class LLMClient(Protocol):
    provider: str
    model: str
    def generate(self, prompt: Prompt, *, schema: type[T], max_tokens: int) -> LLMResult[T]: ...
```
- Model chosen per task in config (narrative vs classification can use different models); temperature 0; prompt version + model recorded per output.
- Fallback order: same provider retry → configured secondary model → **template report** (deterministic). Never fall back to a model that has not passed the AI-safety suite.
- Token budget per run enforced by the client; cache keyed by (snapshot ID, prompt version, model version).

## 3. Sessions: where they are required

| Session | Why | Pattern |
|---|---|---|
| **HTTP session per provider** | Connection pooling, keep-alive, shared auth headers, consistent timeouts | One `httpx.Client`/`AsyncClient` per provider per run, created in a context manager, with base URL, default headers, `timeout=httpx.Timeout(30, connect=10)`, limits; closed at run end |
| **Token sessions with expiry** | Some APIs issue short-lived tokens (e.g. a login returning a 30-minute token); others have long-lived tokens with an expiry date | `ProviderSession` holds token + `expires_at`; refreshes **before** expiry under a lock; on 401 refresh once then fail as `auth_failed`; preflight warns before long-lived token expiry |
| **SMTP session** | Avoid reconnecting per message; STARTTLS once | `with smtplib.SMTP(host, 587, timeout=30) as s: s.starttls(context=ssl.create_default_context()); s.login(...)`; send all messages for the run, then close |
| **Run session (context)** | Every step must see the same run ID, as-of time, config, snapshot and logger | Immutable `RunContext` created once at start and passed explicitly (see deterministic-pipeline.md) |
| **LLM session** | Rate limits and token budget across calls in one run | One client instance per run tracking tokens used and cache hits |

Rules: sessions are never global or module-level; they are created by the run and passed in; secrets come from settings, never logged; every session is closed in `finally`/context managers; tests use fake sessions with the same interface.

```python
class ProviderSession:
    def __init__(self, client: httpx.Client, auth: TokenProvider, clock: Clock) -> None: ...
    def get(self, path: str, **params: str) -> httpx.Response:
        self._ensure_token()                    # refresh if expires within the safety margin
        resp = self._client.get(path, params=params, headers=self._auth_header())
        if resp.status_code == 401 and self._refresh_once():
            resp = self._client.get(path, params=params, headers=self._auth_header())
        return resp
```
