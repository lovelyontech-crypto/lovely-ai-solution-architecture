# Parallel Processing

Parallelise only where a measurement shows it pays, and **never at the cost of determinism or provider limits**. Pick the model by the kind of work.

## 1. Choose the model

| Work | Bound by | Use | Example in this project |
|---|---|---|---|
| Fetching many symbols/ranges from APIs | Network I/O | **`asyncio` + `httpx.AsyncClient`**, bounded by a semaphore and a token-bucket rate limiter | Incremental daily candles for 100–500 symbols |
| Per-symbol pure computations (indicators, ratios, adjusted series, features) | CPU, independent per symbol | **`concurrent.futures.ProcessPoolExecutor`** (spawn context) with chunked symbols | Recompute features for affected symbols |
| Column-wise transforms on a frame | CPU, vectorisable | **Polars** expressions (multi-threaded internally) — no extra pool needed | Rolling windows, ranks, joins |
| Tight numeric loops | CPU | `numba` `@njit` (optionally `parallel=True` with `prange`) | Wilder smoothing, IV solver over a strike grid |
| Model training | CPU | Library threads (`lightgbm num_threads`, `n_jobs`), one model at a time | Monthly training workflow |
| File writes, git, email, manifest updates | Shared state | **Sequential, single writer** | Persist step, commit, send |

## 2. Rules

1. **Never parallelise writes to shared state.** Workers return results; the parent merges, sorts and writes once.
2. **Do not nest pools.** If Polars, LightGBM or BLAS already use all cores, a process pool on top oversubscribes. Set `POLARS_MAX_THREADS`, `OMP_NUM_THREADS`, `num_threads` explicitly from config.
3. **Respect provider limits.** Concurrency (`max_in_flight`) and rate (`requests_per_second`) come from `config/platform.yaml` per provider; honour `Retry-After`.
4. **Deterministic results regardless of scheduling.** Collect results into a dict keyed by symbol, then iterate in sorted key order. Never depend on completion order.
5. **Workers are pure.** Pass paths/config, not open handles; workers read inputs, compute, return data. No logging to shared files from workers; return log events to the parent.
6. **Fail per item, not per batch.** Each task returns `Ok(result) | Err(reason)`; the parent records failures in the failed-range/quality log and continues.
7. **Bound memory.** Chunk symbols (e.g. 25 per task); use lazy frames; avoid pickling huge frames to workers (send paths instead).
8. **Budget-aware.** Default worker count = `min(cpu_count, config.max_workers)`; GitHub-hosted runners have few cores.

## 3. Patterns

**Async, rate-limited fetch (I/O-bound):**

```python
import asyncio
import httpx
from aiolimiter import AsyncLimiter

async def fetch_all(
    adapter: "AsyncProviderAdapter",
    requests: list["RangeRequest"],
    *,
    max_in_flight: int,
    per_second: float,
) -> dict[str, "FetchResult"]:
    limiter = AsyncLimiter(max_rate=per_second, time_period=1)
    gate = asyncio.Semaphore(max_in_flight)
    results: dict[str, FetchResult] = {}

    async def one(req: RangeRequest) -> None:
        async with gate, limiter:
            results[req.key] = await adapter.fetch(req)   # adapter handles timeout/retry, returns a status

    async with asyncio.TaskGroup() as tg:
        for req in requests:
            tg.create_task(one(req))
    return dict(sorted(results.items()))                    # deterministic order
```

**Process pool for per-symbol CPU work:**

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

def compute_features_for(symbols: list[str], inputs_dir: Path, feature_set: str) -> dict[str, FeatureResult]:
    ...  # pure: reads partitions, returns results; never writes shared files

def compute_all(symbols: list[str], *, inputs_dir: Path, feature_set: str, max_workers: int, chunk: int = 25) -> dict[str, FeatureResult]:
    chunks = [sorted(symbols)[i : i + chunk] for i in range(0, len(symbols), chunk)]
    ctx = mp.get_context("spawn")                          # same behaviour on Linux runners and Windows dev boxes
    merged: dict[str, FeatureResult] = {}
    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as pool:
        for part in pool.map(compute_features_for, chunks, [inputs_dir] * len(chunks), [feature_set] * len(chunks)):
            merged.update(part)
    return dict(sorted(merged.items()))
```

## 4. Tests required for any parallel code

- Same output (byte-identical CSV) with `max_workers=1` and `max_workers=N`.
- Same output across two runs with shuffled input order.
- One failing item does not lose other items' results; failure is recorded.
- Rate limiter never exceeds the configured rate (assert on recorded request timestamps with a fake clock).
