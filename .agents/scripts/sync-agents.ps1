# Installs the repository's agents and skills from .agents/ into Claude Code's folders.
#   .agents/agents/*.md     -> <target>/agents/
#   .agents/skills/<name>/  -> <target>/skills/<name>/
# Usage: .\.agents\scripts\sync-agents.ps1          # project scope: .\.claude (gitignored)
#        .\.agents\scripts\sync-agents.ps1 -User    # user scope: ~\.claude (all projects)
# .agents/ is the source of truth; edit there and re-run this script.
param([switch]$User)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$src = Join-Path $repoRoot '.agents'
if ($User) { $target = Join-Path $HOME '.claude' } else { $target = Join-Path $repoRoot '.claude' }

New-Item -ItemType Directory -Force (Join-Path $target 'agents') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $target 'skills') | Out-Null

Get-ChildItem (Join-Path $src 'agents') -Filter *.md | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $target 'agents') -Force
    Write-Output "agent  $($_.BaseName) -> $target\agents\"
}

Get-ChildItem (Join-Path $src 'skills') -Directory | ForEach-Object {
    $dest = Join-Path (Join-Path $target 'skills') $_.Name
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force -Confirm:$false }
    Copy-Item $_.FullName $dest -Recurse -Force
    Write-Output "skill  $($_.Name) -> $dest"
}
