# Engineering Profile: <project name>

Customises the developer agent, tester agent and devops-engineer skill for this project. Place this file in the project folder (and at the root of the implementation repository). Anything not set here falls back to each role's own skill defaults: `developer-engineering`, `tester-engineering`, `devops-engineer`.

## 1. Sources of truth
| Document | Path |
|---|---|
| Requirements (BRD) | <path> |
| System design | <path> |
| Implementation plan | <path> |
| Algorithm / model decisions | <path> |

## 2. Platform constraints
- Runtime: <e.g. Python 3.12 on GitHub-hosted ubuntu-latest>
- Allowed infrastructure: <list>
- **Forbidden** infrastructure/tools (never propose or name): <list>
- Persistent state: <where and how>
- Budgets: <job timeout, monthly minutes, storage thresholds, cost limits>

## 3. Commands
| Purpose | Command |
|---|---|
| Install | <cmd> |
| Lint / format check | <cmd> |
| Type check | <cmd> |
| Unit + golden tests | <cmd> |
| Integration tests (non-live) | <cmd> |
| Live tests (need credentials) | <cmd> |
| Coverage | <cmd> |
| Static principle checks | <cmd> |

## 4. Quality thresholds
- Line coverage of core modules: <e.g. ≥ 80%>; golden coverage of formulas: <100%>
- Max function length / PR size: <defaults or override>
- Numeric tolerances: <e.g. ratios 4 d.p.; indicators 1e-6>
- CI time budget: <e.g. < 10 min>

## 5. Architecture rules
- Layers / pillars and allowed import directions: <...>
- Single entry points: <...>
- Naming conventions specific to this project: <...>

## 6. Domain edge cases (in addition to each skill's defaults)
- <case>: <expected behaviour> (<requirement ID>)

## 7. Test environments and credentials
| Environment | Purpose | Credentials (secret names only) | Status |
|---|---|---|---|

## 8. Gates and blockers
- Features gated until: <decision IDs>
- Tests that must be reported as blocked until: <decision / dependency IDs>

## 9. Waivers (loosened defaults)
| Default | Override | Reason | Approved by |
|---|---|---|---|
