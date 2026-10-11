# GitHub Actions Review Checklist

Use for every new or changed workflow. Each item is pass / fail / not applicable, with the line reference.

## Supply chain
- [ ] Every `uses:` pinned to a full 40-character commit SHA, version in a trailing comment
- [ ] Dependabot (or equivalent) configured to update pinned actions and dependencies
- [ ] Dependencies installed from a hash-locked file (`--require-hashes`)

## Permissions and secrets
- [ ] Top-level `permissions` set to `{}` or `contents: read`
- [ ] Write scopes granted per job, only where needed (e.g. the job that commits to `data`)
- [ ] Secrets referenced only as `secrets.NAME`; none printed, written to files, artefacts or summaries
- [ ] No `pull_request_target` running untrusted code with secrets
- [ ] Secret scanning and push protection enabled on the repository

## Inputs and injection
- [ ] `workflow_dispatch` / event fields reach shell only through `env:` variables
- [ ] Inputs validated in code against allow-lists (symbols, modes, horizons); destructive options need a reason input
- [ ] No `eval`, no unquoted variable expansion in `run:` blocks

## Reliability
- [ ] `timeout-minutes` on every job
- [ ] `concurrency` group on jobs that write shared state, `cancel-in-progress: false`
- [ ] Idempotent steps: re-running a run ID creates no duplicate rows, emails or commits
- [ ] Schedules in UTC with the local-time mapping commented; late-start handling present
- [ ] Failure path still writes a run record and job summary (`if: always()`)

## Persistence (data branch pattern)
- [ ] Commit only when files changed; run ID in commit message
- [ ] Fast-forward push with a single re-merge retry; otherwise no write and an alert
- [ ] Backup tag before full refresh or bulk rewrite
- [ ] Size thresholds checked each run

## Cost and observability
- [ ] Job durations and minutes tracked against the monthly allowance (alert at 70%)
- [ ] Structured logs with masking of secrets and email addresses
- [ ] Heavy jobs (training, full refresh) scheduled outside the business-critical slots
