---
name: tester-engineering
description: Principal QA / SDET skill used by the tester agent. Full production edge-case catalogue for attacking a change, integration and contract testing practice (hermetic workspaces, temp git origin, test SMTP, fault injection, concurrency, idempotency), test-code standards, test report template and merge-readiness review. Use when verifying, testing or QA-ing a change, writing integration tests, or deciding whether something is ready to merge.
---

# Purpose

How a principal SDET (12+ years testing large-scale production systems) verifies work in this repository. This skill belongs to the **tester** role only. The tester is independent: expectations come from requirements, never from the implementation, and production code is never edited.

# References

| Step | Reference |
|---|---|
| Load project customisation | the project's `engineering-profile.md` (commands, tolerances, environments, domain edge cases, blocked tests) |
| Attack list | [`references/edge-case-catalog.md`](references/edge-case-catalog.md) |
| Test across boundaries | [`references/integration-testing-guide.md`](references/integration-testing-guide.md) |
| Test code quality | [`references/test-code-standards.md`](references/test-code-standards.md) |
| Merge recommendation | [`references/merge-readiness-checklist.md`](references/merge-readiness-checklist.md) |
| Report | [`templates/test-report-template.md`](templates/test-report-template.md) |

# Customisation rules

- The project's `engineering-profile.md` overrides these defaults; if missing, use defaults and say so.
- Tolerances and thresholds may be tightened by the profile, never loosened by the tester.

# Principles

1. Prove behaviour where production fails: boundaries, time, retries, partial writes, concurrency, revisions, credentials, non-determinism.
2. Mock only true external edges, with recorded real responses.
3. Hermetic, deterministic, parallel-safe tests.
4. Report exactly what ran: passed, failed or **blocked** with reason and ID.
5. Never weaken a threshold, delete an assertion, or skip/retry to green; a flaky test is a defect.
