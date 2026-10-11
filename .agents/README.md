# `.agents/`: shared agents and skills for this repository

This folder is the **single source of truth** for the AI agents and skills used in this repository. It is committed to Git; tool-specific folders (such as `.claude/`, which is gitignored) are generated from it.

```
.agents/
├── agents/
│   ├── developer.md          # implements work items from implementation_plan.md, test-first
│   └── tester.md             # verifies acceptance criteria; never edits production code
├── skills/
│   ├── developer-engineering/  # developer only: clean code, edge-case design patterns,
│   │                           # developer tests, readiness self-check, profile template
│   ├── tester-engineering/     # tester only: edge-case catalogue, integration testing,
│   │                           # test-code standards, merge readiness, report template
│   ├── devops-engineer/        # DevOps only: GitHub Actions, repo-as-code, secrets,
│   │                           # data branch, operational edge cases, runbooks
│   ├── ai-algorithm-selector/
│   ├── ai-system-design-architect/
│   ├── ai-business-strategy-roadmap/
│   ├── ai-strategy-transformation-governance/
│   └── ai-ml-observability-architect/
└── scripts/
    ├── sync-agents.sh        # install into .claude/ (Git Bash, macOS, Linux)
    └── sync-agents.ps1       # install into .claude/ (PowerShell)
```

## Seniority and standards

All three roles work at staff / principal level (12+ years on large-scale production systems). They are **separate**: each has its own definition and its own skill, and no skill references another role's skill.

| Role | Definition | Own skill | What the skill holds | Does not do |
|---|---|---|---|---|
| Developer | `agents/developer.md` | `developer-engineering` | Clean-code standards, edge-case design patterns, developer-owned unit/golden/property/integration tests, readiness self-check, profile template | Sign off its own work; change CI/CD, secrets or repo settings |
| Tester | `agents/tester.md` | `tester-engineering` | Edge-case catalogue (attack list), integration-testing guide, test-code standards, merge-readiness checklist, test report template | Edit production code; set expectations from the developer's design |
| DevOps | skill only | `devops-engineer` | Workflow standards, GitHub Actions checklist, data-branch operations, operational edge cases, pipeline integration testing, runbook template | Edit application code or its tests |

Roles hand work to each other through their reports (developer → tester for verification, developer/tester → DevOps for pipeline changes).

## Customise per project

Each project gets an `engineering-profile.md` (template: `skills/developer-engineering/templates/engineering-profile-template.md`). Every role reads it; each role applies only the sections relevant to it. It sets the platform and **forbidden** infrastructure, commands, thresholds and tolerances, architecture rules, domain edge cases, test environments and blocked tests. The agents read it first and it overrides the defaults; the project's BRD and design still outrank it. Example: [`lab-ai-system-designs/intelligent-data-processing/engineering-profile.md`](../lab-ai-system-designs/intelligent-data-processing/engineering-profile.md).

## Install for Claude Code

Run once after cloning, and again after editing anything in `.agents/`:

```powershell
.\.agents\scripts\sync-agents.ps1          # this repository only  (.\.claude\)
.\.agents\scripts\sync-agents.ps1 -User    # every project on this machine (~\.claude\)
```

```bash
.agents/scripts/sync-agents.sh             # or: --user
```

Restart Claude Code (or open `/agents`) to pick up the agents.

## Use them

| What | How to invoke | Example |
|---|---|---|
| **developer** agent | Ask for it by name, or `@developer` | "Use the developer agent to implement sprint S0.2 (storage core) from `lab-ai-system-designs/intelligent-data-processing/implementation_plan.md`" |
| **tester** agent | Ask for it by name, or `@tester` | "Use the tester agent to verify FR-130 to FR-136 and Tests A–J for the storage core" |
| **devops-engineer** skill | `/devops-engineer`, or any request about workflows, secrets, branch protection | "/devops-engineer review `pipelines/research.yml` against the checklist" |

A typical loop for one work item: **developer** builds it → **tester** verifies it and reports pass / fail / blocked → **devops-engineer** for any workflow, secret or repository change → you review and merge.

Other assistants (Gemini CLI, Antigravity, Cursor) read `.agents/skills/` directly; the agent files are plain Markdown with YAML front matter and can be pasted or referenced as system instructions.

## Add a new agent or skill

- **Agent**: add `.agents/agents/<name>.md` with front matter `name`, `description` (when to use it), `tools`, `model`, then the instructions. Re-run the sync script.
- **Skill**: add `.agents/skills/<name>/SKILL.md` with front matter `name` and `description`, plus optional `references/` and `templates/`. Re-run the sync script.
- Keep paths repository-relative, and keep each agent's rules consistent with the project's BRD (for example, no infrastructure the design excludes).
