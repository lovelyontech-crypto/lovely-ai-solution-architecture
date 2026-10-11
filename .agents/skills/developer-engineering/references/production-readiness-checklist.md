# Production Readiness Checklist

A change ships when every applicable item is checked or explicitly waived with a reason and owner.

## Correctness
- [ ] Acceptance criteria met; requirement IDs traced to tests
- [ ] Edge cases from `edge-case-design-patterns.md` covered or documented as out of scope
- [ ] Golden/property tests for every formula and rule
- [ ] Integration scenarios pass; live scenarios passed or listed as blocked

## Resilience
- [ ] Timeouts, bounded retries with jitter, rate-limit handling on every external call
- [ ] Idempotent re-runs; atomic writes; backups before bulk changes
- [ ] Degraded mode defined (stale labels, template fallback, failure notice) and tested
- [ ] Concurrency control for shared state

## Observability
- [ ] Structured logs with run/correlation ID; secrets and personal data masked
- [ ] Metrics for SLOs (duration, success rate, freshness, cost) emitted
- [ ] Run record written on success and failure
- [ ] Alerts with a runbook link for each new failure mode

## Security
- [ ] No secrets in code, logs, fixtures, artefacts or history (scanner clean)
- [ ] Inputs validated and allow-listed; no injection paths
- [ ] Least-privilege permissions; dependencies pinned with hashes

## Operability
- [ ] Configuration documented and schema-validated
- [ ] Runbooks updated (diagnose, resolve, verify, prevent)
- [ ] Rollback is one step (revert commit / restore tag) and was rehearsed for risky changes
- [ ] Capacity and cost within budget (run time, quota, storage growth)

## Compliance and product
- [ ] Gated features remain off unless their gate is closed
- [ ] Required disclosures and labels present in outputs
- [ ] No infrastructure or tools outside what the design allows
