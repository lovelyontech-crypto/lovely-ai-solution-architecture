# Runbook: <event name>

| Field | Value |
|---|---|
| Owner | <role> |
| Severity | <low / medium / high> |
| Related requirements | <FR / NFR / R IDs> |
| Last tested | <date or "not yet tested"> |

## Symptoms
- How the event shows up (failure email subject, job summary text, alert, metric).

## Impact
- What users or data are affected; what is safe (e.g. "stored CSVs are untouched").

## Diagnose
1. `gh run view <run-id> --log-failed`
2. Check `runs/<run_id>.json` on the `data` branch for the failing step.
3. <project-specific checks>

## Resolve
1. <step>
2. <step>
3. Re-run: `gh workflow run <workflow>.yml -f <inputs>`

## Verify
- <what proves it is fixed: run record status, test, report received>

## Prevent
- <follow-up change, alert or test to add>
