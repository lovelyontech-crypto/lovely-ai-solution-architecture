# Developer Testing

The developer owns the first line of tests; the tester then verifies independently. Commands come from the project's `engineering-profile.md`.

## What the developer must deliver with every change

| Change type | Required tests |
|---|---|
| Formula, rule, threshold | Golden test against reviewed reference values at the profile's tolerance + property tests for invariants |
| Bug fix | A failing test that reproduces the bug, committed with the fix |
| New function/module | Unit tests for normal, boundary and error paths |
| Anything crossing a boundary (files, git, network, email, scheduler) | Component/integration test in a hermetic temp workspace |
| External adapter | Contract test against recorded real responses (secrets scrubbed), including error responses |

## Integration tests the developer writes

- Real local implementations: real files in `tmp_path`, real atomic-write code, a temporary bare git repository as `origin`, a local SMTP capture server.
- Recorded responses for third-party APIs (`respx`/`pytest-httpx`, cassettes); never hand-written "happy" payloads only.
- Fault injection for the failure paths the change introduces (timeout, 429, 5xx, killed process).
- Assert on observable outcomes: files and checksums, records written, commits, captured emails, log events.
- Live tests marked `@pytest.mark.live`; without credentials they are reported as **blocked**.

## Test code quality

- Arrange-Act-Assert; one behaviour per test; names state the behaviour.
- Deterministic: frozen time, fixed seeds, recordings; independent and parallel-safe.
- Fixtures synthetic and labelled, under `tests/` only.
