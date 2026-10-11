#!/usr/bin/env bash
# Create the orphan `data` branch that holds the persistent CSV store (BRD §14.4.9).
# Usage: ./bootstrap.sh <owner>/<repo>
set -euo pipefail

REPO="${1:?usage: bootstrap.sh <owner>/<repo>}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

git clone --quiet "git@github.com:${REPO}.git" "$WORK/repo"
cd "$WORK/repo"

if git ls-remote --exit-code --heads origin data >/dev/null; then
  echo "data branch already exists; nothing to do."
  exit 0
fi

git switch --orphan data
mkdir -p raw processed metadata/schemas checkpoints backups predictions reports runs
for d in raw processed metadata/schemas checkpoints backups predictions reports runs; do
  touch "$d/.gitkeep"
done
printf 'dataset,exchange,isin,symbol,frequency,adjustment,file_path,schema_version,coverage_start,coverage_end,last_confirmed_date,row_count,sha256,status,last_successful_update_utc,source,missing_ranges_count\n' \
  > metadata/manifest.csv
git add -A
git -c user.name=research-bot -c user.email=research-bot@users.noreply.github.com \
  commit --quiet -m "data: initialise empty persistent store"
git push --quiet origin data
echo "Created orphan data branch in ${REPO}."
