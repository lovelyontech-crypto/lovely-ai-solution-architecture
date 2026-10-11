# CSV as the Database

The CSV files on the persistent store are the **system of record** (BRD §14.4). Treat them with database discipline: schemas, keys, transactions, indexes, migrations, backups. Any query engine (Polars, DuckDB) only **reads** them and can be rebuilt from them; nothing becomes a second store.

## 1. Table abstraction (repository pattern)

All reads and writes go through one module (`storage/csv_store.py`); no other code opens data CSVs directly.

```python
@dataclass(frozen=True, slots=True)
class TableSpec:
    dataset: str                         # e.g. "daily_equity_raw"
    schema_version: int
    columns: tuple[str, ...]             # fixed order = serialisation order
    dtypes: Mapping[str, pl.DataType]
    natural_key: tuple[str, ...]         # uniqueness constraint
    partition_by: Callable[[pl.DataFrame], Path]   # e.g. raw/daily/NSE/<SYMBOL>/<YYYY>.csv
    float_formats: Mapping[str, str]     # deterministic serialisation

class CsvTable:
    def read(self, *, symbols: Sequence[str] | None = None, start: date | None = None, end: date | None = None) -> pl.LazyFrame: ...
    def upsert(self, rows: pl.DataFrame, *, run: RunContext) -> UpsertResult: ...   # new / duplicate / revised counts
    def verify(self) -> list[IntegrityIssue]: ...                                     # checksum, schema, key uniqueness
```

## 2. Database guarantees and how CSV provides them

| Guarantee | Implementation |
|---|---|
| **Schema** | `TableSpec` + JSON schema file per version; validate with pandera on read and write; empty field = missing, never `0` |
| **Primary key / uniqueness** | `natural_key`; upsert deduplicates; `verify()` fails on duplicate keys |
| **Atomic transaction** | Write all changed partitions to `*.tmp` in the same directory → fsync → verify row count + SHA-256 → `os.replace` each → update `manifest.csv` last. If any step fails before the manifest update, readers still see the previous consistent version |
| **Multi-file commit** | A run's changes become durable together via one git commit to the `data` branch; the manifest is the commit point |
| **Isolation / concurrency** | Single writer per run (workflow concurrency group); an in-process lock file for local runs; workers never write |
| **Durability and backups** | Git history + backup tags before bulk changes; last N versions retained |
| **Indexes** | `manifest.csv` per file: coverage start/end, `last_confirmed_date`, row count, SHA-256, status. Gap detection uses the manifest, not full scans |
| **Audit / history** | Append-only logs (`download_log`, `data_quality_log`, `revisions_log`, run records); revisions write `revision + 1`, never edit in place |
| **Migrations** | `schema_version` per file; migration functions `vN → vN+1` are pure, tested, and run once under an operator dispatch with a backup tag |
| **Query** | Polars `scan_csv` with explicit `schema=`, predicate pushdown by partition path; optional DuckDB `read_csv(..., columns=...)` read-only for ad-hoc and golden SQL tests |

## 3. File format rules

- UTF-8 without BOM, comma-separated, header row, `\n` line endings, RFC 4180 quoting.
- Fixed column order from `TableSpec.columns`; rows sorted by natural key before writing.
- Dates `YYYY-MM-DD`; timestamps ISO 8601 UTC with `Z`; decimals with `.`; no thousands separators.
- Never write values starting with `= + - @` unquoted into user-facing CSV exports (formula injection); data CSVs are internal.
- Partition so routine writes touch only small files (symbol × year); warn at 25 MB per file.
- Read with explicit dtypes; never let the reader infer types from data.

## 4. Upsert algorithm

1. Validate incoming rows (schema + quality rules); rejected rows go to the quality log.
2. Load only the affected partitions.
3. Anti-join on the natural key → **new** rows. Inner-join → compare non-key columns: identical → **duplicate** (drop, count); different → **revision** resolved by source precedence, write `revision + 1`, log old/new.
4. Concatenate, sort by natural key, serialise with fixed formats.
5. Atomic replace; update manifest; return counts.

## 5. Tests

Round-trip (write → read → identical frame), byte-identical rewrite of unchanged data, duplicate and revision counts, crash between tmp write and rename leaves the old file valid, manifest checksum mismatch detected, migration up and verify.
