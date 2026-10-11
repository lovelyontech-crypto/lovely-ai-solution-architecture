# Production Edge-Case Catalogue

Use this list to attack every change under test. For each relevant category write down the expected behaviour and the test that proves it. Domain-specific additions belong in the project's `engineering-profile.md`.

## 1. Input values
- Empty, `None`, whitespace-only, missing field, extra unknown field
- Zero, negative, very large, `NaN`, `inf`, `-0.0`, precision loss, rounding direction (floor vs round half-even)
- Boundary values: exactly at a threshold, one below, one above; inclusive vs exclusive bounds
- Wrong type that coerces silently (`"1"` vs `1`, `True` as `1`)
- Unicode: non-Latin scripts (Devanagari), mixed scripts, combining characters, NFC vs NFD, emoji, right-to-left marks
- Very long strings, newlines and delimiters inside CSV fields, BOM at file start
- Case and whitespace differences in identifiers (`ABC` vs `abc ` vs `ABC.NS`)
- Duplicate keys, conflicting duplicates (same key, different values)

## 2. Time and calendars
- Time zones (UTC storage vs local display), DST in other markets, no DST in India
- Weekends, exchange holidays, special sessions (e.g. Muhurat), half days, unscheduled closures
- Run just before/after midnight UTC vs IST date boundaries; month/quarter/fiscal-year ends (April–March)
- Leap years, 29 Feb, end-of-month arithmetic
- Late or delayed schedules; clock skew between systems; timestamps in the future
- Incomplete current period (intraday candle not final, provisional close)
- Data published late, revised later, or restated with a new timestamp (point-in-time correctness)

## 3. Collections and data shape
- Empty collection, single element, very large collection (memory)
- Unsorted, out-of-order, gaps in sequences, overlapping ranges
- Lookback windows longer than available history (new listing)
- Schema drift: renamed, added, removed or reordered columns; changed units or scale
- Partial records; nested nulls; mixed types in one column

## 4. External dependencies
- Timeout, connection reset, DNS failure, TLS failure
- HTTP 4xx (401 expired token, 403 licence, 404 instrument removed, 429 rate limit with/without `Retry-After`), 5xx, 200 with error body
- Empty but successful response; truncated response; shorter history than already stored
- Pagination edge: last page, empty page, cursor reuse
- Duplicate or replayed responses; responses for the wrong symbol/date
- Provider schema change without notice; provider maintenance windows
- Credential expiry or rotation mid-run

## 5. State, storage and concurrency
- Process killed mid-write; disk full; read-only filesystem
- Corrupted file (checksum mismatch), missing file referenced by an index/manifest
- Two runs at once; a manual run during a scheduled run; retry of the same run ID
- Push/commit conflict; stale working copy; partial commit
- Re-running a completed job (idempotency: no duplicate rows, emails, ledger entries)
- Backup/restore round trip; migration of an older schema version

## 6. Domain: markets and finance (defaults for market-data projects)
- Corporate actions: split, bonus, rights, dividend, merger, demerger, symbol change, ISIN change, delisting, suspension
- Dual listing (NSE/BSE), different series, share classes
- Circuit limits, trading halts, illiquid stocks, zero-volume days
- Negative or zero denominators (EPS, equity), restated financials, missing quarters, half-yearly cash flow
- Lot size or expiry changes by circular; expiry on a holiday; weekly vs monthly expiry
- Options: price below intrinsic, IV not solvable, deep ITM/OTM, zero time to expiry
- Position sizing: stop on the wrong side of entry, stop equal to entry, quantity rounding to zero, short positions
- Survivorship and look-ahead bias in any historical computation

## 7. AI / ML components
- Insufficient training history; regime shift; label leakage; overlapping labels
- Model file missing, unapproved, or trained on a different feature-set version
- Feature misaligned to a different as-of date than the prediction
- LLM: invented numbers or citations, prohibited phrases, causal claims, prompt injection inside retrieved documents, truncated or invalid JSON, refusal, timeout, token budget exhausted
- Non-determinism: same input, different output across runs

## 8. Security and privacy
- Secrets in logs, exceptions, test snapshots, artefacts or commit history
- Injection through inputs (shell, path traversal, CSV formula injection `=cmd|...`)
- Personal data (emails) in logs or reports; recipients not on the approved list
- Permissions: read-only user attempting a write action

## 9. Operations
- First ever run (empty state); run after long downtime (large gap)
- Configuration missing, invalid, or valid-but-wrong (e.g. empty universe)
- Resource limits: job timeout, memory, monthly minutes/quota near limit
- Notification channel down (email fails after work succeeded) and the reverse
