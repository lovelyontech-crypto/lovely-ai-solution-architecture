---
name: developer-engineering
description: Staff-level software development skill used by the developer agent. Clean-code standards, edge-case design patterns for large-scale production systems, developer-owned unit and integration tests, production-readiness self-check, and per-project customisation via engineering-profile.md. Use when writing, refactoring or reviewing production code, or when creating a project's engineering profile.
---

# Purpose

How a staff engineer (12+ years on large-scale production systems) writes code in this repository. This skill belongs to the **developer** role only; testing sign-off and CI/CD changes are other roles' work.

# References

| Step | Reference |
|---|---|
| Load project customisation | the project's `engineering-profile.md` (template: [`templates/engineering-profile-template.md`](templates/engineering-profile-template.md)) |
| Pick the right Python tools and frameworks | [`references/python-stack-and-frameworks.md`](references/python-stack-and-frameworks.md) |
| Write code | [`references/clean-code-standards.md`](references/clean-code-standards.md) |
| Keep the flow deterministic | [`references/deterministic-pipeline.md`](references/deterministic-pipeline.md) |
| Parallelise where it pays | [`references/parallel-processing.md`](references/parallel-processing.md) |
| Store data in CSV as the database | [`references/csv-database-patterns.md`](references/csv-database-patterns.md) |
| Multiple data providers, multiple models, sessions | [`references/multi-provider-models-and-sessions.md`](references/multi-provider-models-and-sessions.md) |
| Design for failure | [`references/edge-case-design-patterns.md`](references/edge-case-design-patterns.md) |
| Write own tests (unit, golden, property, integration) | [`references/developer-testing.md`](references/developer-testing.md) |
| Self-check before handing to the tester | [`references/production-readiness-checklist.md`](references/production-readiness-checklist.md) |

# Customisation rules

- The project's `engineering-profile.md` overrides these defaults (language, commands, thresholds, forbidden infrastructure, domain edge cases). Missing → use defaults, say so, offer to create one from the template.
- Profiles may tighten defaults freely; loosening a safety default (secrets, data integrity, test honesty) needs a written reason in the profile's waiver table.
- The project's BRD and design documents outrank both.

# Principles

1. Correct first, then clear, then fast; optimise only with a measurement.
2. Validate at boundaries; trust types inside the core.
3. Every external call can fail, hang, lie or repeat: timeout, bounded retry with jitter, idempotency.
4. State changes are atomic and reversible.
5. Observable by default; no secrets in telemetry.
6. Tests prove behaviour; mocks only at true external edges.
7. "Done" means verified by a run, not believed.
8. Deterministic by construction: same inputs, code and config give byte-identical outputs.
9. CSV is the system of record; every read and write goes through the CSV table layer.
10. Parallelise I/O with async and CPU with processes only where measured, with a single writer and sorted results.
11. Providers and models sit behind protocols chosen by config; sessions are created per run and closed by it.
