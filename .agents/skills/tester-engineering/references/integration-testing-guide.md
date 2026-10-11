# Integration Testing Guide

Unit tests prove a function; integration tests prove that components, files, processes and external systems work **together** under real conditions, including failure. A project's `engineering-profile.md` names its concrete commands, environments and credentials.

## 1. Test pyramid (default proportions)

| Level | Share | What it covers | External systems |
|---|---|---|---|
| Unit + property + golden | ~70% | Pure functions, formulas, rules | None |
| Component / contract | ~20% | One adapter or module against its contract; storage on a real temp filesystem | Recorded responses or local fakes |
| Integration | ~8% | Several modules end to end through real I/O: pipeline run on a temp repo/data dir | Real local services (git, filesystem, SMTP test server); recorded or sandbox APIs |
| End-to-end / live | ~2% | Real provider, real repository, real email account, real scheduler | Real, gated by credentials |

## 2. Principles

1. **Mock only at the true edge.** Inside the system use the real implementations (real files, real git, real serialisation). Replace only things you do not own (third-party APIs) and only with **recorded real responses** or a contract-faithful fake.
2. **Contract tests on both sides of every boundary.** Each provider adapter has a contract suite that runs against recordings in CI and against the live API on a schedule; when the live run fails, the recordings are stale.
3. **Hermetic and repeatable.** Each test creates its own temp workspace (data dir, git repo, config), seeds it, and cleans up. Frozen clock, fixed seeds. Tests can run in parallel.
4. **Test the failure paths as seriously as the happy path.** Inject faults at boundaries: timeouts, 429/5xx, partial responses, killed process mid-write, push conflicts, SMTP rejection.
5. **Assert on observable outcomes**: files on disk and their checksums, manifest/run-record contents, git commits, emails captured by the test SMTP server, log events. Not on internal calls.
6. **Idempotency and concurrency are integration properties**: run twice, run concurrently, re-run after failure; assert no duplicates and no corruption.
7. **Live tests are opt-in and honest.** Marked (`@pytest.mark.live`), skipped without credentials, and reported as **blocked** (not passed) when they cannot run.

## 3. Standard toolkit (Python defaults)

| Need | Tool / technique |
|---|---|
| HTTP recordings and fakes | `respx` / `pytest-httpx` for `httpx`; `vcrpy` cassettes with secrets scrubbed |
| Fault injection | Fake transport raising timeouts/resets; status-code sequences; `signal`/subprocess kill mid-write |
| Filesystem | `tmp_path`; real atomic-write code; checksum assertions |
| Git persistence | Temporary bare repo as `origin` + two clones to simulate concurrent runners and push conflicts |
| Email | Local SMTP capture (`aiosmtpd` test server) asserting subject, body sections, attachments, idempotency |
| Time | `freezegun` / injected clock; calendars with holidays and special sessions |
| Workflows | `actionlint`; `act` for local smoke runs where practical; real `workflow_dispatch` in a sandbox repo for live tests |
| Data invariants | `hypothesis` stateful tests for merge/dedupe/revision logic |
| Coverage of paths | `pytest-cov` with branch coverage on integration runs |

## 4. Scenario template (write one per acceptance criterion)

```
ID: <TST-xxx>            Requirement: <FR/NFR IDs>
Given:   <initial state: data files, manifest, config, clock, provider recording>
When:    <action: pipeline run / dispatch inputs / injected fault>
Then:    <observable outcomes: files, checksums, run record fields, commits, emails, logs>
And not: <what must not happen: duplicate rows, partial files, secrets in logs, stale report sent as current>
Level:   component | integration | live
```

## 5. Must-have integration scenarios for data pipelines

- First run on empty state → full initial load, validated, manifest complete
- Second run with no new data → zero historical requests, files byte-identical
- New data + back-filled gap + duplicates → only the gap fetched, no duplicate keys
- Upstream revision + corporate action → revision logged, derived series rebuilt, equals full rebuild
- Process killed mid-write → prior files intact; next run resumes from checkpoint
- Corrupted file → restored from backup or marked failed; never reported current
- Provider down → last valid data kept, datasets marked stale, labelled failure notice
- Two concurrent runs → consistent data; second waits or re-merges
- Re-run same run ID → no duplicate rows, predictions or emails
- Restart on a fresh runner/workspace → state read from persistent store, no re-download
- Email channel failure after successful processing → data still persisted, status recorded
- Invalid configuration or dispatch input → fails before any fetch or write

## 6. Exit criteria for an integration suite

- Every acceptance criterion in scope maps to at least one scenario
- All non-live scenarios run in CI on every PR in < 10 minutes (or the profile's budget)
- Live scenarios have run at least once against real systems, or are listed as blocked with the blocking ID
- No flaky tests: a test that fails intermittently is quarantined and fixed within the sprint, not retried until green
