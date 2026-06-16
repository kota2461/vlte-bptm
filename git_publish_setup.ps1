# VLTE-BPTM - local git setup for publishing
# Run from Windows PowerShell, inside the project folder.
#   cd "D:\Thought State Register"
#   powershell -ExecutionPolicy Bypass -File .\git_publish_setup.ps1
#
# This script does LOCAL prep only (cleanup + init + first commit).
# It does NOT push anywhere. Push + Zenn linking steps are in SETUP_GITHUB.md.

$ErrorActionPreference = "Stop"
Set-Location "D:\Thought State Register"

Write-Host "==> Cleaning up stray files left by the sandbox..." -ForegroundColor Cyan
foreach ($f in @(".git", "__b", "__unlink_test")) {
    if (Test-Path $f) {
        Remove-Item -Recurse -Force $f
        Write-Host "    removed $f"
    }
}

Write-Host "==> Initializing git repository..." -ForegroundColor Cyan
git init -b main
git config user.name  "kota2461"
git config user.email "kot9786@gmail.com"

Write-Host "==> Staging files (.gitignore controls what is included)..." -ForegroundColor Cyan
git add -A

Write-Host "==> Files staged:" -ForegroundColor Cyan
(git diff --cached --name-only | Measure-Object).Count

Write-Host "==> Sanity check - archive folders included (should be ONLY first-model-frozen):" -ForegroundColor Cyan
git diff --cached --name-only | Select-String '^archive/' |
    ForEach-Object { ($_ -replace '^(archive/[^/]+)/.*$', '$1') } | Sort-Object -Unique

Write-Host "==> Sanity check - any logs/db/pycache leaked in? (should be empty):" -ForegroundColor Cyan
git diff --cached --name-only | Select-String '\.(log|db)$|__pycache__|egg-info'

Write-Host "==> Creating first commit..." -ForegroundColor Cyan
git commit -m "Archive VLTE-BPTM v0.3 first frozen model + Zenn article (alpha)"

Write-Host ""
Write-Host "Local repo is ready. Next: create the GitHub repo and push - see SETUP_GITHUB.md" -ForegroundColor Green
