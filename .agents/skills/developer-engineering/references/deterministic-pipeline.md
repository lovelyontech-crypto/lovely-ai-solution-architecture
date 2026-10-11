# Deterministic Pipeline Flow

Same inputs + same code + same config ⇒ **byte-identical outputs**. This is what makes runs reproducible (NFR-097), re-runs idempotent (FR-158) and scheduled and manual runs equivalent (FR-151). Only the LLM narrative is allowed to vary, and it is pinned by caching per snapshot and gated by deterministic checks.

## 1. Flow structure

- **One entry point, fixed step order.** The pipeline is an explicit ordered list of steps (BRD §15.5.3), not an event bus or an agent deciding what to run next.

```python
@dataclass(frozen=True, slots=True)
class Step:
    name: str
    run: Callable[[RunContext, StepInputs], StepOutputs]
    required: bool = True            # a failed required step stops later steps that depend on it

PIPELINE: tuple[Step, ...] = (
    Step("load_config", load_config),
    Step("load_state", load_state),
    Step("detect_gaps", detect_gaps),
    Step("fetch", fetch_missing),
    Step("validate_persist", validate_and_persist),
    Step("features", recompute_features),
    Step("models", load_approved_models),
    Step("analytics", run_engines),
    Step("predictions", write_predictions),
    Step("report", render_report),
    Step("deliver", send_email),
    Step("persist_git", commit_and_push),
)
```

- Each step is a function of `(RunContext, inputs) -> outputs`; outputs are typed and recorded in the run record with timings and status.
- Mode flags (`data_only`, `report_only`) select a **prefix or subset** of the same tuple; they never introduce a second implementation.

## 2. Sources of non-determinism and the fix

| Source | Fix |
|---|---|
| Wall clock (`datetime.now()`) inside logic | Inject `RunContext.clock`; capture `as_of_utc` once at run start; freeze in tests |
| Dict/set iteration, completion order of parallel tasks, filesystem listing order | Sort by natural key before every write and every aggregation; `sorted(Path.glob(...))` |
| Floating-point summation order | Sort inputs before reductions; use `math.fsum` / Polars deterministic aggregations; fixed rounding at serialisation |
| Random numbers (bootstrap, model training, Optuna) | Seeds from config, recorded in the run/model record; `numpy.random.default_rng(seed)`; `lightgbm deterministic=True, seed=...` |
| Thread counts affecting results | Fix `num_threads`; LightGBM `deterministic=True` + `force_row_wise=True` |
| Library upgrades | Hash-locked dependencies; versions recorded in each run record |
| CSV float formatting / column order | Fixed schema column order; fixed float format per column (e.g. prices 2–4 d.p. as received, ratios 6 d.p.); `\n` line endings; UTF-8 without BOM |
| Locale / timezone of the machine | Never use locale formatting in data; UTC internally; IST only in presentation |
| External data changing between retries | Snapshot ID = manifest checksums at the start of analytics; every output references it |
| LLM output | Temperature 0, structured output, prompt and model version recorded, **cache keyed by (snapshot ID, prompt version, model version)**; citation gate and template fallback are deterministic |

## 3. Run context

```python
@dataclass(frozen=True, slots=True)
class RunContext:
    run_id: str                      # business identity: workflow run id (not the attempt number)
    trigger: Literal["schedule", "workflow_dispatch"]
    as_of_utc: datetime              # captured once
    config: PlatformConfig           # validated, immutable
    data_dir: Path
    seed: int
    clock: Clock                     # injectable; frozen in tests
    log: BoundLogger                 # structlog bound with run_id
```

Everything a step needs comes from the context or its typed inputs; no globals, no module-level state.

## 4. Proof (tests)

- Run the pipeline twice on the same fixture workspace → identical files (compare SHA-256 of every output).
- Scheduled vs dispatch trigger with the same inputs → identical outputs except the trigger field.
- Re-run of the same `run_id` → no new rows, predictions or emails.
- `max_workers=1` vs `N` → identical outputs.
