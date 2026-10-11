#!/usr/bin/env bash
# Installs the repository's agents and skills from .agents/ into Claude Code's folders.
#   .agents/agents/*.md     -> <target>/agents/
#   .agents/skills/<name>/  -> <target>/skills/<name>/
# Usage: .agents/scripts/sync-agents.sh            # project scope: ./.claude (gitignored)
#        .agents/scripts/sync-agents.sh --user     # user scope: ~/.claude (all projects)
# .agents/ is the source of truth; edit there and re-run this script.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
src="$repo_root/.agents"

if [[ "${1:-}" == "--user" ]]; then
  target="$HOME/.claude"
else
  target="$repo_root/.claude"
fi

mkdir -p "$target/agents" "$target/skills"

for f in "$src"/agents/*.md; do
  cp -f "$f" "$target/agents/"
  echo "agent  $(basename "$f" .md) -> $target/agents/"
done

for d in "$src"/skills/*/; do
  name="$(basename "$d")"
  rm -rf "${target:?}/skills/$name"
  cp -R "$d" "$target/skills/$name"
  echo "skill  $name -> $target/skills/$name"
done
