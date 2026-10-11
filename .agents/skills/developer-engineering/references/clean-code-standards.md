# Clean Code Standards (production defaults)

Defaults for Python services and pipelines; a project's `engineering-profile.md` may override. Each rule has a reason so reviewers can judge exceptions.

## 1. Structure and design

| Rule | Why |
|---|---|
| Functions do one thing; ≤ ~40 lines and ≤ 4 parameters (group the rest into a typed object) | Readable, testable units |
| Pure core, effects at the edges: computation takes data in and returns data out; I/O, clock, randomness and network are injected | Deterministic tests, reproducible outputs |
| Dependencies point inward (domain ← application ← adapters); enforce with import-linter contracts | Stops layer leaks that make change expensive |
| Composition over inheritance; protocols/ABCs only for real variation points (e.g. provider adapters) | Avoids deep hierarchies |
| No speculative generality: build for the current requirement plus known next step, not imagined ones | Less code to maintain |
| One implementation per business rule; shared by every caller (scheduled and manual runs alike) | No drift between duplicates |
| Configuration is data validated by a schema at start-up; no magic numbers in code (named constants with units, or config) | Change behaviour without code edits; reviewable |

## 2. Naming and readability

- Names state intent and unit: `timeout_s`, `price_inr`, `as_of_utc`, `risk_budget_inr`; avoid `data`, `tmp`, `obj`, `handle`.
- Booleans read as questions: `is_complete`, `has_restatement`.
- Comments explain **why** and cite the rule (`# FR-133: exclude incomplete sessions`); do not narrate what the code does.
- Docstrings on public functions: purpose, args with units, returns, raises, and the formula/requirement ID.
- Keep the file's existing style; no drive-by reformatting in feature PRs.

## 3. Types and data

- Full type hints; `mypy --strict` (or project equivalent) on core packages.
- Domain values are typed objects (`pydantic`/`dataclass(frozen=True)`), not dicts passed around.
- Money and prices: `Decimal` or integer minor units where exactness matters; floats only in statistical code with stated tolerance.
- Time: timezone-aware UTC internally; convert to local time only at presentation; trading dates are `date`, not `datetime`.
- Missing is explicit (`None` / a result type with a reason), never `0`, `""` or `NaN` silently standing in.
- Immutable by default; copy on write; never mutate arguments.

## 4. Errors

- Raise specific exception types defined per domain (`ProviderUnavailable`, `SchemaMismatch`); never bare `except:` or `except Exception: pass`.
- Catch only where you can add context or recover; re-raise with `raise ... from err`.
- Expected outcomes (no data, insufficient history) are return values, not exceptions.
- Error messages are actionable: what failed, which input, what to do next. No secrets or personal data in messages.

## 5. External calls and concurrency

- Every network call has a timeout, bounded retries with exponential backoff + jitter, and honours rate-limit headers.
- Retries only for idempotent operations or with idempotency keys.
- Shared mutable state behind a single owner; file writes via temp file + `fsync` + atomic rename.
- No unbounded loops, queues or caches; every cache has a size or TTL.

## 6. Logging and observability

- Structured JSON logs; one event per line; fields: `ts`, `level`, `event`, `run_id`, `component`, plus context.
- Levels: `ERROR` = needs action; `WARNING` = degraded but handled; `INFO` = lifecycle; `DEBUG` = off in production.
- Mask secrets, tokens and email addresses by a central filter; never log full payloads from third parties.
- Emit metrics for what the SLOs measure (duration, counts, failures, freshness).

## 7. Security

- Secrets only from the secret store/env; never in code, tests, fixtures, logs or exceptions.
- Validate and allow-list all external input; never build shell commands, SQL or paths from raw input.
- Pin dependencies with hashes; review new dependencies for licence, maintenance and size.

## 8. Testing (developer's own tests)

- Test-first for formulas, rules and bug fixes (the failing test reproduces the bug).
- Arrange-Act-Assert; one behaviour per test; test names state the behaviour (`test_stop_on_wrong_side_of_entry_is_rejected`).
- Deterministic: frozen time, fixed seeds, recorded external responses.
- Fixtures are synthetic and labelled as such; they live under `tests/`, never in production data paths.

## 9. Pull requests

- Small (aim < 400 changed lines), one purpose, requirement IDs in the title.
- Description: what, why, how verified (commands + results), risks, rollback.
- Green CI is necessary, not sufficient: the reviewer checks the edge-case list for the change.

## 10. Review checklist

- [ ] Behaviour matches the requirement and its acceptance criteria
- [ ] Edge cases from `edge-case-design-patterns.md` considered and tested or explicitly out of scope
- [ ] No hardcoded values that belong in config or data
- [ ] Errors are specific, actionable, and do not leak secrets
- [ ] External calls: timeout, retry, idempotency
- [ ] Writes are atomic; failure leaves prior state intact
- [ ] Logs/metrics added for new failure modes
- [ ] Tests are deterministic and test behaviour
- [ ] Naming, size and layering rules respected
