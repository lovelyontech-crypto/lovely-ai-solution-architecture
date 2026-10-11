# Test Code Standards

| Rule | Why |
|---|---|
| Arrange-Act-Assert; one behaviour per test | Failures point at one cause |
| Name states the behaviour: `test_rerun_same_run_id_sends_no_second_email` | Readable report without opening code |
| Expected values come from requirements or reviewed references, not from running the code | Independence from the implementation |
| Deterministic: frozen clock, fixed seeds, recorded responses, no network unless `@pytest.mark.live` | Repeatable in CI |
| Hermetic: each test builds its own temp workspace and cleans up; no shared mutable state | Parallel-safe, order-independent |
| Fixtures synthetic, labelled "hypothetical", under `tests/` only; recordings scrubbed of secrets | Engineering principles; no leakage |
| Parametrise boundary tables instead of copy-pasting tests | Edge cases visible in one place |
| Assert on observable outcomes (files, checksums, records, commits, emails, logs), not internal calls | Tests survive refactors |
| Tolerances explicit and taken from the profile (`pytest.approx(rel=..., abs=...)`) | No hidden looseness |
| Golden data has provenance (who reviewed, source, date) next to it | Auditable references |
| No `sleep` for synchronisation; use events, polling with timeout, or injected clocks | No flakiness |
| Markers: `unit`, `golden`, `property`, `contract`, `integration`, `live` | Selective runs per profile commands |
